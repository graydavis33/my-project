"""
CLI for the v2 index + pull layer. Kept separate from main.py so the existing
organize/archive flow is untouched.

Commands:
  index         — scan the library, upsert every clip into SQLite
  pull          — filter index → hardlink results into 07_QUERY_PULLS/<slug>/
  batch         — file a shoot into 01_ORGANIZED/Batch_NN/Vid_MM/ then re-index
  promote       — move a finished project ACTIVE→DELIVERED→ARCHIVE
  ship          — post-delivery cleanup: archive the edit project + file the footage
  create-week   — backfill a past/future week's folder scaffold
  pull-cleanup  — delete query-pull folders after the edit ships
"""
import argparse
import hashlib
import os
import re
import shutil
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Force UTF-8 — Windows console hits cp1252 by default.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from config import (
    CATEGORIES, CLIENT_ROOTS, VIDEO_EXTENSIONS, INDEX_DB_NAME, PULL_FOLDER_NAME,
    INDEX_SCAN_ROOTS, FORMAT_LONG_FORM, FORMAT_SHORT_FORM,
    FOLDER_FOOTAGE_LIB, FOLDER_ORGANIZED, FOLDER_QUERY_PULLS,
    FOLDER_PROJECTS, FOLDER_DELIVERED, FOLDER_ARCHIVE, FOLDER_BATCHES,
    FOLDER_DRAFTS, FOLDER_BROLL, FOLDER_VERTICAL, FOLDER_INBOX,
    VISION_TAG_MODEL, VISION_TAG_COST_PER_CLIP,
)

PROJECT_FORMAT_BUCKETS = ["longform", "linkedin", "shorts"]
from extractor import (get_resolution, get_duration, get_shoot_date,
                       extract_frames, get_display_orientation)
from week_utils import week_label_for, current_week_label
import index
import pull as pull_mod


def _library(client: str) -> Path:
    root = CLIENT_ROOTS.get(client, "")
    if not root:
        print(f"Error: {client.upper()}_LIBRARY_ROOT not set in .env")
        sys.exit(1)
    lib = Path(root)
    if not lib.exists():
        print(f"Error: {client.upper()}_LIBRARY_ROOT does not exist on disk: {lib}")
        print("  (drive not mounted? path typo in .env?)")
        sys.exit(1)
    return lib


def _db(client: str) -> Path:
    return _library(client) / INDEX_DB_NAME


def _check_legacy_db(db_path: Path) -> None:
    """If the DB has legacy absolute paths, wipe + warn. The next index build
    will repopulate with relative paths. Safe to run on an empty DB.

    This is symmetrical: whichever machine (Mac or Windows) runs first after the
    relative-path migration triggers the wipe; subsequent runs on either machine
    see relative paths and short-circuit.
    """
    if not db_path.exists():
        return
    if not index.has_legacy_paths(db_path):
        return
    print(f"\n  ! Detected legacy absolute-path index at {db_path}")
    print(f"  ! Wiping clips table and rebuilding with relative paths.")
    print(f"  ! (This is safe — clip files on disk are untouched.)\n")
    index.wipe_clips(db_path)


_PREMIERE_DIR_PREFIXES = ("Adobe Premiere Pro",)


def _walk_videos(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune Premiere project subdirs — they generate .mp4 preview renders
        # that are NOT real footage. Skip names like "Adobe Premiere Pro Video
        # Previews/" and any "*.PRV" sidecar dirs.
        # Also prune underscore-prefixed helper folders (_INBOX raw drop, _TO_SORT
        # holding area) — those hold un-categorized footage and must stay out of
        # the searchable index (same convention ensure_week uses to skip them).
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(_PREMIERE_DIR_PREFIXES)
            and not d.endswith(".PRV")
            and not d.startswith("_")
        ]
        for name in filenames:
            # Mac on exFAT sprinkles `._<name>` AppleDouble sidecars + `.DS_Store`.
            # These are not real footage — skip even if extension matches.
            if name.startswith("._") or name == ".DS_Store":
                continue
            if Path(name).suffix in VIDEO_EXTENSIONS:
                yield Path(dirpath) / name


def _category_from_path(filepath: Path, library: Path) -> str:
    """Infer category from the folder it lives in. Accepts both shapes:
      FOOTAGE_LIBRARY/{category}/{week_or_date}/clip.mp4
      ORGANIZED/{category}/{date}/clip.mp4
    Freeform (v3): ANY folder name under FOOTAGE_LIBRARY or ORGANIZED is its own
    category — not just the fixed 17 — so Gray's own folders index correctly.
    """
    rel = filepath.relative_to(library).parts
    if len(rel) >= 4 and rel[0] in (FOLDER_FOOTAGE_LIB, FOLDER_ORGANIZED):
        return rel[1]
    return "misc"


_BATCH_RE = re.compile(r"^Batch_(\d+)$")
_VID_RE = re.compile(r"^Vid_(\d+)$")


def _batch_vid_from_path(filepath: Path, library: Path):
    """Derive (batch_num, vid_num) from an adjacent Batch_NN/Vid_MM folder pair
    anywhere in the clip's path. Folders are the source of truth, so a plain
    re-index re-derives these — same pattern as _category_from_path.
    Returns (None, None) when the clip isn't under a batch/vid folder."""
    parts = filepath.relative_to(library).parts
    for i in range(len(parts) - 1):
        bm = _BATCH_RE.match(parts[i])
        vm = _VID_RE.match(parts[i + 1])
        if bm and vm:
            return int(bm.group(1)), int(vm.group(1))
    return None, None


def _format_from_resolution(w: int, h: int) -> str:
    return FORMAT_SHORT_FORM if h > w else FORMAT_LONG_FORM


def _sha1_head(filepath: Path, n_bytes: int = 1_048_576) -> str:
    """Hash first 1 MB + filesize — fast pseudo-fingerprint, sufficient for dedup of identical clips.
    Filesize is mixed in because two distinct clips can share the same intro card (first MB)
    but they cannot share the same total length."""
    h = hashlib.sha1()
    h.update(str(filepath.stat().st_size).encode())
    with open(filepath, "rb") as f:
        h.update(f.read(n_bytes))
    return h.hexdigest()


def _reindex(library: Path, db_path: Path) -> tuple[int, int, int]:
    """Scan the library into the SQLite index, then prune rows whose files are
    gone. Returns (added, skipped, removed). Shared by `index` and `batch` (which
    re-indexes after moving clips so the new Batch_NN/Vid_MM clips get tagged)."""
    index.init(db_path)
    _check_legacy_db(db_path)

    added = 0
    skipped = 0
    for sub in INDEX_SCAN_ROOTS:
        root = library / sub
        if not root.exists():
            continue
        for clip in _walk_videos(root):
            try:
                w, h = get_resolution(str(clip))
                duration = get_duration(str(clip))
                filmed = get_shoot_date(str(clip))
            except Exception as e:
                print(f"  [skip] {clip.name}: {e}")
                skipped += 1
                continue

            upload = datetime.fromtimestamp(clip.stat().st_mtime).strftime("%Y-%m-%d")
            rel_path = clip.relative_to(library).as_posix()
            batch_num, vid_num = _batch_vid_from_path(clip, library)
            rec = index.ClipRecord(
                path=rel_path,
                category=_category_from_path(clip, library),
                format=_format_from_resolution(w, h),
                filmed_date=filmed,
                upload_date=upload,
                duration_s=duration,
                width=w,
                height=h,
                codec="",  # codec is optional — leave empty unless needed
                sha1=_sha1_head(clip),
                batch_num=batch_num,
                vid_num=vid_num,
            )
            index.upsert(db_path, rec)
            added += 1

    removed = index.remove_missing(db_path, library_root=library)
    return added, skipped, removed


def cmd_index(args):
    client = args.client
    library = _library(client)
    _autocreate_week(library)
    db_path = _db(client)
    added, skipped, removed = _reindex(library, db_path)
    print(f"\n  Indexed {added} clip(s), skipped {skipped}, removed {removed} missing")
    print(f"  DB: {db_path}\n")


def cmd_pull(args):
    client = args.client
    library = _library(client)
    _autocreate_week(library)
    db_path = _db(client)
    if not db_path.exists():
        print(f"Error: index not built yet. Run: python cli_index.py --client {client} index")
        sys.exit(1)

    _check_legacy_db(db_path)

    _slugify = lambda s: s.strip().lower().replace(" ", "-")
    slug_parts = []
    if args.filmed_date: slug_parts.append(args.filmed_date)
    if args.category:    slug_parts.append(args.category)
    if args.orientation: slug_parts.append(args.orientation)
    if args.emotion:     slug_parts.append(_slugify(args.emotion))
    if args.action:      slug_parts.append(_slugify(args.action))
    if args.location:    slug_parts.append(_slugify(args.location))
    if args.object:      slug_parts.append(_slugify(args.object))
    slug = "-".join(slug_parts) or "all"
    out = library / PULL_FOLDER_NAME / slug

    fmt_map = {"vertical": FORMAT_SHORT_FORM, "horizontal": FORMAT_LONG_FORM}
    fmt = fmt_map.get(args.orientation) if args.orientation else None

    subfolder_fn = None
    if args.by_week:
        def by_week(record):
            if not record.filmed_date:
                return "unknown-week"
            try:
                return week_label_for(date.fromisoformat(record.filmed_date))
            except (ValueError, TypeError):
                return "unknown-week"
        subfolder_fn = by_week

    result = pull_mod.pull(
        db_path, out,
        library_root=library,
        category=args.category,
        format=fmt,
        filmed_date=args.filmed_date,
        filmed_after=args.filmed_after,
        filmed_before=args.filmed_before,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        emotion=args.emotion,
        action=args.action,
        location=args.location,
        object=args.object,
        subfolder_fn=subfolder_fn,
    )

    if result.count == 0:
        print(f"\n  Pull → {result.folder}")
        print(f"  Linked 0 clip(s). Run 'index' first if this is unexpected.\n")
    else:
        print(f"\n  Pull → {result.folder}")
        print(f"  Linked {result.count} clip(s); fallback copies: {result.fallback_copies}\n")


def ensure_week(library: Path, target: date) -> tuple[int, int]:
    """Create `target`'s week folders across:
      - 05_FOOTAGE_LIBRARY/{b-roll,vertical}/<W##>/  (the v4 footage buckets)
      - 02_ACTIVE_PROJECTS/<format>/<W##>/            (3 format buckets)
      - 03_DELIVERED/<format>/<W##>/                  (3 format buckets)
      - 04_ARCHIVE/<format>/<W##>/                    (3 format buckets)
    Idempotent — folders that already exist are skipped. Returns (created, skipped).

    Single source of truth for both the manual `create-week` command and the
    lazy auto-creation that every command runs first, so Gray never has to
    remember to scaffold a week by hand."""
    label = week_label_for(target)
    lib_root = library / FOLDER_FOOTAGE_LIB

    # v4: seed only the b-roll + vertical buckets — the old 17 categories were
    # flattened away in the v4 consolidation, so don't recreate them. Plus any
    # freeform folder already on disk (skip underscore-prefixed helpers).
    freeform = []
    if lib_root.is_dir():
        freeform = [p.name for p in lib_root.iterdir()
                    if p.is_dir() and not p.name.startswith("_")]
    categories = sorted({FOLDER_BROLL, FOLDER_VERTICAL} | set(freeform))

    targets = []
    # Footage library: weekly subfolder per bucket (b-roll, vertical, freeform)
    for category in categories:
        targets.append(lib_root / category / label)
    # _BATCHES parent — batch interview originals are filed by Batch_NN/Vid_MM
    # (via ship), NOT by week, so just guarantee the parent folder exists.
    targets.append(lib_root / FOLDER_BATCHES)
    # Project folders: one per format bucket per top-level
    for top in (FOLDER_PROJECTS, FOLDER_DELIVERED, FOLDER_ARCHIVE):
        for fmt in PROJECT_FORMAT_BUCKETS:
            targets.append(library / top / fmt / label)

    created = 0
    skipped = 0
    for path in targets:
        if path.exists():
            skipped += 1
            continue
        path.mkdir(parents=True)
        created += 1
    return created, skipped


def _autocreate_week(library: Path) -> None:
    """Lazy week creation — every command calls this first so the current
    week's folders always exist. Quiet unless it actually creates something."""
    created, _ = ensure_week(library, date.today())
    if created:
        print(f"  + Lazy-created {created} folder(s) for week {current_week_label()}")


def cmd_create_week(args):
    """Create the current (or specified) week's folders. Manual backfill — every
    other command auto-scaffolds the current week via ensure_week, so this is
    only needed to pre-create a past or future week on demand."""
    library = _library(args.client)
    target = date.fromisoformat(args.week) if args.week else date.today()
    label = week_label_for(target)

    created, skipped = ensure_week(library, target)

    print(f"\n  Week {label} ({args.client.upper()})")
    print(f"  Created {created} folder(s), skipped {skipped} existing")
    print(f"  Spans: FOOTAGE_LIBRARY ({FOLDER_BROLL} + {FOLDER_VERTICAL} + freeform) + ACTIVE/DELIVERED/ARCHIVE ({len(PROJECT_FORMAT_BUCKETS)} formats × 3 = {len(PROJECT_FORMAT_BUCKETS) * 3})")
    print(f"  Library: {library}\n")


def cmd_pull_cleanup(args):
    """List query-pull folders, prompt per-folder keep/delete.
    With --older-than N: delete pulls N+ days old non-interactively."""
    library = _library(args.client)
    pulls_root = library / FOLDER_QUERY_PULLS
    if not pulls_root.is_dir():
        print(f"\n  No {FOLDER_QUERY_PULLS}/ folder yet. Nothing to clean.\n")
        return

    folders = sorted(p for p in pulls_root.iterdir() if p.is_dir())
    if not folders:
        print(f"\n  {FOLDER_QUERY_PULLS}/ is empty.\n")
        return

    today = date.today()
    deleted = 0
    print(f"\n  Pull cleanup ({args.client.upper()})")
    print(f"  Root: {pulls_root}\n")

    for folder in folders:
        mtime = date.fromtimestamp(folder.stat().st_mtime)
        age_days = (today - mtime).days
        clip_count = sum(1 for _ in folder.rglob("*") if _.is_file())

        if args.older_than is not None:
            if age_days >= args.older_than:
                shutil.rmtree(folder)
                deleted += 1
                print(f"    deleted {folder.name} ({clip_count} files, {age_days}d old)")
            continue

        ans = input(f"  Delete {folder.name}? ({clip_count} files, {age_days}d old) [y/N]: ").strip().lower()
        if ans == "y":
            shutil.rmtree(folder)
            deleted += 1
            print(f"    deleted {folder.name}")

    print(f"\n  Done. Deleted {deleted} of {len(folders)} folder(s).\n")


def cmd_drafts_cleanup(args):
    """Delete review-staging items in 03_DELIVERED/drafts/ untouched for N+ days.
    Same rule as the query-pull sweep — anything (videos AND project files) idle
    7+ days is removed, no exceptions. Handles loose files and subfolders (the
    query-pull sweep only does folders). Dotfiles (.DS_Store, ._*) are ignored."""
    library = _library(args.client)
    drafts_root = library / FOLDER_DELIVERED / FOLDER_DRAFTS
    if not drafts_root.is_dir():
        print(f"\n  No {FOLDER_DELIVERED}/{FOLDER_DRAFTS}/ folder yet. Nothing to clean.\n")
        return

    items = sorted(p for p in drafts_root.iterdir() if not p.name.startswith("."))
    if not items:
        print(f"\n  {FOLDER_DELIVERED}/{FOLDER_DRAFTS}/ is empty.\n")
        return

    def _remove(p: Path):
        shutil.rmtree(p) if p.is_dir() else p.unlink()

    today = date.today()
    deleted = 0
    print(f"\n  Drafts cleanup ({args.client.upper()})")
    print(f"  Root: {drafts_root}\n")

    for item in items:
        age_days = (today - date.fromtimestamp(item.stat().st_mtime)).days

        if args.older_than is not None:
            if age_days >= args.older_than:
                _remove(item)
                deleted += 1
                print(f"    deleted {item.name} ({age_days}d old)")
            continue

        ans = input(f"  Delete {item.name}? ({age_days}d old) [y/N]: ").strip().lower()
        if ans == "y":
            _remove(item)
            deleted += 1
            print(f"    deleted {item.name}")

    print(f"\n  Done. Deleted {deleted} of {len(items)} item(s).\n")


def _expand_clip_segment(seg: str) -> list[str]:
    """Expand one map segment into clip IDs (uppercased):
      'C2493'          -> ['C2493']
      'C2493-C2495'    -> ['C2493', 'C2494', 'C2495']
    Range endpoints share a letter prefix; the low endpoint's digit width sets
    the zero-padding (so C0008-C0011 stays 4-wide)."""
    seg = seg.strip().upper()
    if "-" not in seg:
        return [seg]
    lo, hi = (s.strip() for s in seg.split("-", 1))
    m_lo, m_hi = re.match(r"^([A-Z]*)(\d+)$", lo), re.match(r"^([A-Z]*)(\d+)$", hi)
    if not (m_lo and m_hi):
        raise ValueError(f"bad clip range '{seg}' (expected e.g. C2493-C2495)")
    prefix, width = m_lo.group(1), len(m_lo.group(2))
    start, end = int(m_lo.group(2)), int(m_hi.group(2))
    if end < start:
        raise ValueError(f"range '{seg}' ends before it starts")
    return [f"{prefix}{n:0{width}d}" for n in range(start, end + 1)]


def _parse_map(map_str: str) -> dict:
    """Parse the --map string into {vid_num: [clip_id, ...]}.
      '1:C2493-C2495 2:C2496,C2498' -> {1: ['C2493','C2494','C2495'], 2: ['C2496','C2498']}"""
    mapping: dict[int, list[str]] = {}
    for token in map_str.split():
        if ":" not in token:
            raise ValueError(f"bad map token '{token}' (expected VID:CLIPS, e.g. 1:C2493-C2495)")
        vid_str, clips_str = token.split(":", 1)
        vid = int(vid_str)
        for seg in clips_str.split(","):
            if seg.strip():
                mapping.setdefault(vid, []).extend(_expand_clip_segment(seg))
    return mapping


def _matching_files(source: Path, clip_id: str) -> list[Path]:
    """Files in `source` (non-recursive) belonging to clip_id: exact stem match,
    or stem starting with clip_id followed by a non-digit (Sony sidecars like
    C2493M01.XML, C2493.WAV). The non-digit guard stops C249 matching C2493.
    Skips AppleDouble (`._*`) + .DS_Store."""
    cid = clip_id.upper()
    out = []
    for f in source.iterdir():
        if not f.is_file() or f.name.startswith("._") or f.name == ".DS_Store":
            continue
        stem = f.stem.upper()
        if stem == cid:
            out.append(f)
        elif stem.startswith(cid) and not stem[len(cid):len(cid) + 1].isdigit():
            out.append(f)
    return out


def _file_batch(source: Path, batch_root: Path, mapping: dict) -> dict:
    """Move mapped clip files from `source` into `batch_root/Vid_MM/`. Pure file
    ops, no indexing (so it's unit-testable without ffprobe). Returns a summary:
      {moved, not_found:[(vid,cid)], unmapped:[name], per_vid:{vid:[name]}}.
    A clip already present in its Vid folder is left as-is (idempotent re-run)."""
    moved = 0
    not_found = []
    per_vid: dict[int, list[str]] = {}
    for vid in sorted(mapping):
        vid_folder = batch_root / f"Vid_{vid:02d}"
        vid_folder.mkdir(parents=True, exist_ok=True)
        per_vid[vid] = []
        for cid in mapping[vid]:
            files = _matching_files(source, cid)
            if not files:
                not_found.append((vid, cid))
                continue
            for f in files:
                dest = vid_folder / f.name
                if not dest.exists():
                    shutil.move(str(f), str(dest))
                    moved += 1
                per_vid[vid].append(f.name)
    unmapped = sorted(
        f.name for f in source.iterdir()
        if f.is_file() and not f.name.startswith("._") and f.name != ".DS_Store"
        and f.suffix in VIDEO_EXTENSIONS
    )
    return {"moved": moved, "not_found": not_found, "unmapped": unmapped, "per_vid": per_vid}


def cmd_batch(args):
    """File a batch shoot into 01_ORGANIZED/Batch_NN/Vid_MM/ then re-index.
    One command = one whole stage: ensure the week, make the folders, move the
    mapped clips, re-index (tags batch_num/vid_num), report anything unmapped."""
    client = args.client
    library = _library(client)
    _autocreate_week(library)

    source = Path(args.source)
    if not source.is_absolute():
        source = library / args.source
    if not source.is_dir():
        print(f"Error: --from folder not found: {source}")
        sys.exit(1)

    try:
        mapping = _parse_map(args.map)
    except ValueError as e:
        print(f"Error parsing --map: {e}")
        sys.exit(1)

    batch_label = f"Batch_{args.num:02d}"
    batch_root = library / FOLDER_ORGANIZED / batch_label

    print(f"\n  Batch {args.num} ← {source}")
    print(f"  → {batch_root}\n")

    result = _file_batch(source, batch_root, mapping)
    for vid in sorted(result["per_vid"]):
        names = result["per_vid"][vid]
        print(f"    Vid_{vid:02d} ← {len(names)} file(s): {', '.join(names) or '(none)'}")

    print(f"\n  Moved {result['moved']} file(s) into {batch_label}.")
    if result["not_found"]:
        print(f"  ! {len(result['not_found'])} mapped clip(s) had no file in source:")
        for vid, cid in result["not_found"]:
            print(f"      Vid_{vid:02d}: {cid}")
    if result["unmapped"]:
        print(f"  ! {len(result['unmapped'])} video file(s) in source were NOT mapped (left in place):")
        for name in result["unmapped"]:
            print(f"      {name}")

    # Move-and-clear: once everything's filed into Batch_NN/Vid_MM, drop the now-empty
    # source (e.g. the _INBOX/<date>/ drop folder) so the inbox doesn't linger empty.
    if source.is_dir() and not any(source.iterdir()):
        source.rmdir()
        print(f"  Cleared empty source folder: {source}")

    db_path = _db(client)
    added, skipped, removed = _reindex(library, db_path)
    print(f"\n  Re-indexed: {added} clip(s), skipped {skipped}, removed {removed} missing")
    print(f"  DB: {db_path}\n")


# ---- v4: consolidate all category folders into b-roll/<week>/ --------------
# Flattens the 17 content categories (+ freeform folders) into a single
# 05_FOOTAGE_LIBRARY/b-roll/<week>/ home. Findability moves to index tags, not
# folders. Each clip keeps its ORIGINAL week (read from the source week folder,
# else derived from filmed date) so no dates are lost. Plan-first + pure moves.

_WEEK_RE = re.compile(r"^W\d+_")
# Clips with no week folder AND no readable filmed-date land here so they're still
# consolidated + taggable (Gray's choice). Re-file by hand later if a date surfaces.
UNKNOWN_WEEK = "unknown-week"


def _week_from_path(filepath: Path, library: Path):
    """Return the W##_MMM-DD-DD week label from anywhere in the clip's path, or
    None if it isn't under a week folder. Pure — this is the common case (existing
    b-roll already lives in week folders), so it needs no ffprobe."""
    for part in filepath.relative_to(library).parts:
        if _WEEK_RE.match(part):
            return part
    return None


def _resolve_week(filepath: Path, library: Path):
    """Target week for a clip: its source week folder if present, else derived
    from the clip's filmed date (ffprobe). None when neither is available — the
    caller leaves those clips in place and reports them."""
    week = _week_from_path(filepath, library)
    if week:
        return week
    try:
        return week_label_for(date.fromisoformat(get_shoot_date(str(filepath))))
    except Exception:
        return None


def _clip_group(clip: Path) -> list[Path]:
    """The clip plus any sidecars sharing its stem in the same folder (Sony
    C####M01.XML, C####.WAV). Non-digit guard stops C249 grabbing C2493's files."""
    cid = clip.stem.upper()
    group = [clip]
    for f in clip.parent.iterdir():
        if f == clip or not f.is_file():
            continue
        if f.name.startswith("._") or f.name == ".DS_Store":
            continue
        stem = f.stem.upper()
        if stem == cid or (stem.startswith(cid) and not stem[len(cid):len(cid) + 1].isdigit()):
            group.append(f)
    return group


def _plan_consolidation(library: Path):
    """Build the move plan: every clip under FOOTAGE_LIBRARY/<category>/ (except
    b-roll itself and _-prefixed helpers) → b-roll/<week>/. Returns
    (moves, per_week, unknown, collisions):
      moves      — list of (src_file, dest_file) for clips + sidecars
      per_week   — {week_label: clip_count}
      unknown    — [rel_path] clips with no resolvable week (left in place)
      collisions — [(src_rel, dest_rel)] dest already taken (skipped)"""
    lib_root = library / FOLDER_FOOTAGE_LIB
    moves, collisions, unknown = [], [], []
    per_week: dict[str, int] = {}
    seen_dest = set()
    processed = set()
    if not lib_root.is_dir():
        return moves, per_week, unknown, collisions

    for category_dir in sorted(lib_root.iterdir()):
        if not category_dir.is_dir():
            continue
        if category_dir.name == FOLDER_BROLL or category_dir.name.startswith("_"):
            continue
        for clip in _walk_videos(category_dir):
            if clip in processed:
                continue
            week = _resolve_week(clip, library)
            if not week:
                # No week folder, no readable filmed-date → still consolidate into
                # b-roll/unknown-week/ (reported below so Gray can re-file later).
                unknown.append(clip.relative_to(library).as_posix())
                week = UNKNOWN_WEEK
            dest_dir = lib_root / FOLDER_BROLL / week
            for f in _clip_group(clip):
                processed.add(f)
                dest = dest_dir / f.name
                if dest.exists() or dest.as_posix() in seen_dest:
                    collisions.append((f.relative_to(library).as_posix(),
                                       dest.relative_to(library).as_posix()))
                    continue
                seen_dest.add(dest.as_posix())
                moves.append((f, dest))
            per_week[week] = per_week.get(week, 0) + 1
    return moves, per_week, unknown, collisions


def _execute_consolidation(moves) -> int:
    """Perform the planned moves. Never overwrites (dest-exists is skipped — the
    plan already flagged it as a collision). Returns the count actually moved."""
    moved = 0
    for src, dest in moves:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            continue
        shutil.move(str(src), str(dest))
        moved += 1
    return moved


def _prune_empty_dirs(root: Path, keep: str) -> None:
    """Remove now-empty folders under root, bottom-up. Never touches root itself,
    the `keep` subtree (b-roll), or _-prefixed helpers."""
    for dirpath, _dirnames, _files in os.walk(root, topdown=False):
        d = Path(dirpath)
        if d == root:
            continue
        rel = d.relative_to(root).parts
        if rel and (rel[0] == keep or rel[0].startswith("_")):
            continue
        try:
            if not any(d.iterdir()):
                d.rmdir()
        except OSError:
            pass


def cmd_consolidate_broll(args):
    """Flatten every category folder into b-roll/<week>/, weeks preserved.
    Plan-first: shows the full move plan and moves nothing until you confirm."""
    client = args.client
    library = _library(client)
    moves, per_week, unknown, collisions = _plan_consolidation(library)

    print(f"\n  Consolidate → {FOLDER_FOOTAGE_LIB}/{FOLDER_BROLL}/<week>/  ({client.upper()})")
    if per_week:
        print(f"\n  Clips per week (kept in their original week):")
        for week in sorted(per_week):
            print(f"    {week}: {per_week[week]} clip(s)")
    total_files = len(moves)
    total_clips = sum(per_week.values())
    print(f"\n  Plan: move {total_clips} clip(s) ({total_files} file(s) incl. sidecars).")
    if unknown:
        print(f"  ! {len(unknown)} clip(s) have no readable date → b-roll/{UNKNOWN_WEEK}/ (re-file later):")
        for p in unknown[:20]:
            print(f"      {p}")
        if len(unknown) > 20:
            print(f"      … +{len(unknown) - 20} more")
    if collisions:
        print(f"  ! {len(collisions)} file(s) would collide at the destination — SKIPPED:")
        for src, dest in collisions[:20]:
            print(f"      {src} -> {dest}")
        if len(collisions) > 20:
            print(f"      … +{len(collisions) - 20} more")

    if not moves:
        print("\n  Nothing to move.\n")
        return

    if not args.yes:
        ans = input("\n  Proceed with the move? [y/N]: ").strip().lower()
        if ans != "y":
            print("  Aborted — nothing moved.\n")
            return

    moved = _execute_consolidation(moves)
    _prune_empty_dirs(library / FOLDER_FOOTAGE_LIB, keep=FOLDER_BROLL)
    print(f"\n  Moved {moved} file(s) into {FOLDER_BROLL}/.")

    db_path = _db(client)
    added, skipped, removed = _reindex(library, db_path)
    print(f"  Re-indexed: {added} clip(s), skipped {skipped}, removed {removed} missing")
    print(f"  DB: {db_path}\n")


# ---- v4: split vertical clips out of b-roll/ -------------------------------
# All current filming is horizontal, so horizontal = reusable b-roll (tagged).
# Vertical = legacy short-form, parked in vertical/<week>/ (never tagged).
# Orientation is rotation-aware (Sony 1920x1080 + rotate flag = display-vertical).

def _orientation_plan(library: Path, orient_fn=None):
    """Plan moving every VERTICAL clip in b-roll/ → vertical/<same-week>/.
    orient_fn(path) -> (orientation, flipped); defaults to ffprobe. Returns
    (moves, counts, flipped, unknown, collisions):
      moves      — (src, dest) for vertical clips + sidecars
      counts     — {"horizontal": n, "vertical": n}
      flipped    — [rel_path] vertical-by-rotation-flag (worth a human spot-check)
      unknown    — [rel_path] orientation undetermined (left in place)
      collisions — [(src_rel, dest_rel)] dest taken (skipped)"""
    orient_fn = orient_fn or (lambda p: get_display_orientation(str(p)))
    broll_root = library / FOLDER_FOOTAGE_LIB / FOLDER_BROLL
    moves, flipped, unknown, collisions = [], [], [], []
    counts = {"horizontal": 0, "vertical": 0}
    seen, processed = set(), set()
    if not broll_root.is_dir():
        return moves, counts, flipped, unknown, collisions

    for clip in _walk_videos(broll_root):
        if clip in processed:
            continue
        orientation, was_flipped = orient_fn(clip)
        if orientation == "horizontal":
            counts["horizontal"] += 1
            for f in _clip_group(clip):
                processed.add(f)
            continue
        if orientation not in ("vertical",):  # unknown / square → leave + report
            unknown.append(clip.relative_to(library).as_posix())
            for f in _clip_group(clip):
                processed.add(f)
            continue
        # vertical → vertical/<same week>/
        week = _week_from_path(clip, library) or UNKNOWN_WEEK
        dest_dir = library / FOLDER_FOOTAGE_LIB / FOLDER_VERTICAL / week
        for f in _clip_group(clip):
            processed.add(f)
            dest = dest_dir / f.name
            if dest.exists() or dest.as_posix() in seen:
                collisions.append((f.relative_to(library).as_posix(),
                                   dest.relative_to(library).as_posix()))
                continue
            seen.add(dest.as_posix())
            moves.append((f, dest))
        counts["vertical"] += 1
        if was_flipped:
            flipped.append(clip.relative_to(library).as_posix())
    return moves, counts, flipped, unknown, collisions


def cmd_split_vertical(args):
    """Move vertical clips out of b-roll/ into vertical/<week>/ (parked, untagged).
    Plan-first — shows counts + the rotation-flipped clips to spot-check, and moves
    nothing until you confirm. Horizontal clips stay in b-roll/ for tagging."""
    client = args.client
    library = _library(client)
    moves, counts, flipped, unknown, collisions = _orientation_plan(library)

    print(f"\n  Split vertical out of {FOLDER_BROLL}/  ({client.upper()})")
    print(f"  Horizontal (stay as b-roll): {counts['horizontal']}")
    print(f"  Vertical (→ {FOLDER_VERTICAL}/<week>/, untagged): {counts['vertical']}")
    if flipped:
        print(f"\n  ({len(flipped)} of the vertical clips are stored-landscape + a rotation flag —")
        print(f"   normal for Sony vertical; detection is rotation-aware. Sample a few if unsure.)")
    if unknown:
        print(f"  ! {len(unknown)} clip(s) had undetermined orientation — LEFT IN b-roll:")
        for p in unknown[:20]:
            print(f"      {p}")
    if collisions:
        print(f"  ! {len(collisions)} file(s) collide at the destination — SKIPPED:")
        for src, dest in collisions[:20]:
            print(f"      {src} -> {dest}")

    if not moves:
        print("\n  No vertical clips to move.\n")
        return

    if not args.yes:
        ans = input("\n  Move the vertical clips? [y/N]: ").strip().lower()
        if ans != "y":
            print("  Aborted — nothing moved.\n")
            return

    moved = _execute_consolidation(moves)
    print(f"\n  Moved {moved} file(s) into {FOLDER_VERTICAL}/.")

    db_path = _db(client)
    added, skipped, removed = _reindex(library, db_path)
    print(f"  Re-indexed: {added} clip(s), skipped {skipped}, removed {removed} missing")
    print(f"  DB: {db_path}\n")


# ---- v4: intake a new dump → b-roll/<week> | vertical/<week> ----------------
# Ongoing intake (the loop after a shoot): route each new clip into the right
# week folder by orientation + filmed date. Horizontal → b-roll (tag next),
# vertical → vertical (parked). Weeks come from each clip's filmed date, so a
# multi-day card lands in the correct weeks.

def _filmed_week(clip: Path):
    """Week label from the clip's filmed date (ffprobe). None if undeterminable."""
    try:
        return week_label_for(date.fromisoformat(get_shoot_date(str(clip))))
    except Exception:
        return None


def _intake_plan(source: Path, library: Path, default_week: str,
                 orient_fn=None, week_fn=None):
    """Plan routing every clip in `source` into b-roll/<week>/ (horizontal) or
    vertical/<week>/ (vertical). Week = clip's filmed date, else default_week.
    Returns (moves, counts, by_week, unknown, collisions)."""
    orient_fn = orient_fn or (lambda p: get_display_orientation(str(p)))
    week_fn = week_fn or _filmed_week
    moves, unknown, collisions = [], [], []
    counts = {"horizontal": 0, "vertical": 0}
    by_week: dict[str, dict] = {}
    seen, processed = set(), set()

    for clip in _walk_videos(source):
        if clip in processed:
            continue
        group = _clip_group(clip)
        for f in group:
            processed.add(f)
        orientation, _flip = orient_fn(clip)
        bucket = (FOLDER_BROLL if orientation == "horizontal"
                  else FOLDER_VERTICAL if orientation == "vertical" else None)
        if bucket is None:
            unknown.append(clip.relative_to(source).as_posix() if source in clip.parents else clip.name)
            continue
        week = week_fn(clip) or default_week
        dest_dir = library / FOLDER_FOOTAGE_LIB / bucket / week
        for f in group:
            dest = dest_dir / f.name
            if dest.exists() or dest.as_posix() in seen:
                collisions.append((f.name, dest.relative_to(library).as_posix()))
                continue
            seen.add(dest.as_posix())
            moves.append((f, dest))
        key = "horizontal" if bucket == FOLDER_BROLL else "vertical"
        counts[key] += 1
        by_week.setdefault(week, {"horizontal": 0, "vertical": 0})[key] += 1
    return moves, counts, by_week, unknown, collisions


def cmd_intake(args):
    """Route a new footage dump into the weekly b-roll/vertical folders.
    Plan-first; then run `tag` to tag the new horizontal clips."""
    client = args.client
    library = _library(client)
    _autocreate_week(library)

    if args.source:
        source = Path(args.source)
        if not source.is_absolute():
            source = library / args.source
    else:
        date_str = args.date or date.today().isoformat()
        source = library / FOLDER_ORGANIZED / FOLDER_INBOX / date_str
    if not source.is_dir():
        print(f"Error: intake source not found: {source}")
        sys.exit(1)

    default_week = week_label_for(date.fromisoformat(args.date)) if args.date else current_week_label()
    moves, counts, by_week, unknown, collisions = _intake_plan(source, library, default_week)

    print(f"\n  Intake ← {source}  ({client.upper()})")
    print(f"  Horizontal → {FOLDER_BROLL}/: {counts['horizontal']}    Vertical → {FOLDER_VERTICAL}/: {counts['vertical']}")
    if by_week:
        print(f"\n  By week:")
        for wk in sorted(by_week):
            b = by_week[wk]
            print(f"    {wk}: {b['horizontal']} horizontal, {b['vertical']} vertical")
    if unknown:
        print(f"  ! {len(unknown)} clip(s) had undetermined orientation — LEFT in source:")
        for p in unknown[:20]:
            print(f"      {p}")
    if collisions:
        print(f"  ! {len(collisions)} file(s) collide at the destination — SKIPPED:")
        for name, dest in collisions[:20]:
            print(f"      {name} -> {dest}")

    if not moves:
        print("\n  Nothing to intake.\n")
        return

    if not args.yes:
        ans = input("\n  Route these clips? [y/N]: ").strip().lower()
        if ans != "y":
            print("  Aborted — nothing moved.\n")
            return

    moved = _execute_consolidation(moves)
    if source.is_dir() and not any(source.iterdir()):
        source.rmdir()
        print(f"\n  Cleared empty source: {source}")
    else:
        print()

    db_path = _db(client)
    added, skipped, removed = _reindex(library, db_path)
    print(f"  Moved {moved} file(s). Re-indexed: {added} clip(s), skipped {skipped}, removed {removed} missing")

    if args.tag and counts["horizontal"]:
        todo = [c for c in index.query(db_path, category=FOLDER_BROLL) if _is_untagged(c)]
        per_clip = VISION_TAG_COST_PER_CLIP.get(args.tag_model, 0.015)
        print(f"\n  Auto-tag: {len(todo)} untagged b-roll clip(s)  "
              f"Model: {args.tag_model}  Est. cost: ~${len(todo) * per_clip:.2f}")
        go = args.yes or input("  Proceed with the paid Vision run? [y/N]: ").strip().lower() == "y"
        if go and todo:
            tagged, cache_hits, failed = _run_tagging(library, db_path, todo, args.tag_model)
            print(f"\n  Tagged {tagged} clip(s) ({cache_hits} from cache, {failed} skipped).")
        elif not go:
            print(f"  Skipped tagging — run later: python cli_index.py --client {client} tag")
    elif counts["horizontal"]:
        print(f"  Next: tag the {counts['horizontal']} new horizontal clip(s) → python cli_index.py --client {client} tag")
    print(f"  DB: {db_path}\n")


# ---- v4 Phase 3: AI Vision tagging of b-roll -------------------------------

def _apply_tags_to_record(rec, tags: dict):
    """Write a Vision tag dict onto a ClipRecord. Defensive: emotion/action are
    forced None unless a person is present (so a stray model value can't slip in).
    objects are pipe-packed. Pure — unit-testable without the API."""
    person = bool(tags.get("person_present"))
    rec.emotion = (tags.get("emotion") or None) if person else None
    rec.action = (tags.get("action") or None) if person else None
    rec.location = tags.get("location") or None
    rec.objects = index.pack_objects(tags.get("objects") or [])
    return rec


def _is_untagged(rec) -> bool:
    return not (rec.emotion or rec.action or rec.location or rec.objects)


def _run_tagging(library, db_path, todo, model, retag=False):
    """Vision-tag a list of ClipRecords → write tags to the index. Shared by the
    `tag` command and intake's `--tag`. Returns (tagged, cache_hits, failed)."""
    import analyzer
    from cache import get_cached_tags, store_cached_tags

    tagged = failed = cache_hits = 0
    for c in todo:
        abspath = str(library / c.path)
        name = Path(c.path).name
        cached = None if retag else get_cached_tags(abspath)
        if cached is not None:
            tags = cached
            cache_hits += 1
        else:
            try:
                dur = get_duration(abspath)
                frames = extract_frames(abspath, dur)
                tags = analyzer.tag_video(frames, name, model)
                store_cached_tags(abspath, tags)
            except Exception as e:
                print(f"    [skip] {name}: {e}")
                failed += 1
                continue
        _apply_tags_to_record(c, tags)
        index.upsert(db_path, c)
        tagged += 1
        print(f"    {name}: emotion={c.emotion} action={c.action} "
              f"location={c.location} objects={index.unpack_objects(c.objects)}")
    return tagged, cache_hits, failed


def cmd_tag(args):
    """Vision-tag b-roll clips → emotion/action/location/objects in the index.
    Plan-first (shows count + est cost), caches by file hash, COALESCE-upsert so
    re-runs never wipe tags. Default model Opus 4.8; --limit N for a sample run."""
    client_name = args.client
    library = _library(client_name)
    db_path = _db(client_name)
    if not db_path.exists():
        print(f"Error: index not built yet. Run: python cli_index.py --client {client_name} index")
        sys.exit(1)
    _check_legacy_db(db_path)

    if args.episode:
        # freshly-organized episode footage may not be indexed yet — refresh first
        _reindex(library, db_path)
        target_category = args.episode
    else:
        target_category = FOLDER_BROLL
    clips = index.query(db_path, category=target_category)
    todo = clips if args.retag else [c for c in clips if _is_untagged(c)]
    if args.limit:
        todo = todo[:args.limit]

    per_clip = VISION_TAG_COST_PER_CLIP.get(args.model, 0.015)
    est = len(todo) * per_clip
    print(f"\n  Vision-tag {target_category} ({client_name.upper()})")
    print(f"  Model: {args.model}   Clips to tag: {len(todo)}   Est. cost: ~${est:.2f}")
    if args.retag:
        print(f"  (--retag: re-tagging already-tagged clips too)")

    if not todo:
        print(f"  Nothing to tag — all {target_category} clips already tagged.\n")
        return

    if not args.yes:
        ans = input("\n  Proceed with the paid Vision run? [y/N]: ").strip().lower()
        if ans != "y":
            print("  Aborted — no API calls made.\n")
            return

    tagged, cache_hits, failed = _run_tagging(library, db_path, todo, args.model, args.retag)
    print(f"\n  Tagged {tagged} clip(s) ({cache_hits} from cache, {failed} skipped).")
    print(f"  DB: {db_path}\n")


# ---- stage transitions (v3 Phase 4): ACTIVE → DELIVERED → ARCHIVE ----------
# Project stages (02/03/04) are NOT in the index (INDEX_SCAN_ROOTS is 01 + 05),
# so these are pure, safe file moves — no ffprobe, no index rebuild.

_STAGE_DIRS = {
    "active": FOLDER_PROJECTS,
    "delivered": FOLDER_DELIVERED,
    "archive": FOLDER_ARCHIVE,
}
# The natural next stage, so `--to delivered` implies `--from active`, etc.
_DEFAULT_FROM = {"delivered": "active", "archive": "delivered"}


def _find_stage_item(stage_root: Path, name: str) -> list:
    """Find file/dir entries named exactly `name` anywhere under stage_root.
    Does NOT descend into a matched directory (so a project folder is returned
    whole, not also its children). Skips AppleDouble sidecars."""
    matches = []
    for dirpath, dirnames, filenames in os.walk(stage_root):
        d = Path(dirpath)
        if name in dirnames:
            matches.append(d / name)
        # prune the matched dir + AppleDouble so we don't walk into them
        dirnames[:] = [n for n in dirnames if n != name and not n.startswith("._")]
        for n in filenames:
            if n == name and not n.startswith("._"):
                matches.append(d / n)
    return matches


def _infer_format(path: Path, stage_root: Path):
    """If the item sits inside a format bucket (longform/linkedin/shorts), return
    that bucket name; otherwise None (caller must then require --format)."""
    rel = path.relative_to(stage_root).parts
    if rel and rel[0] in PROJECT_FORMAT_BUCKETS:
        return rel[0]
    return None


def _promote_item(library: Path, name: str, from_stage: str, to_stage: str,
                  fmt, week_target) -> dict:
    """Move a finished project (file or folder) named `name` from one stage to the
    next, into <to_stage>/<format>/<week?>/. Pure file op. Never overwrites.
    Raises ValueError on not-found / ambiguous / unknown-format / dest-exists."""
    if from_stage == to_stage:
        raise ValueError("source and destination stage are the same")

    src_root = library / _STAGE_DIRS[from_stage]
    if not src_root.is_dir():
        raise ValueError(f"{from_stage} stage folder doesn't exist: {src_root}")

    found = _find_stage_item(src_root, name)
    if not found:
        raise ValueError(f"'{name}' not found anywhere under {from_stage} ({src_root})")
    if len(found) > 1:
        listing = "\n".join(f"      {p.relative_to(library).as_posix()}" for p in found)
        raise ValueError(
            f"'{name}' is ambiguous in {from_stage} ({len(found)} matches):\n{listing}\n"
            f"      Rename one so it's unique, or move it by hand."
        )
    src = found[0]

    fmt = fmt or _infer_format(src, src_root)
    if not fmt:
        raise ValueError(f"can't infer the format of '{name}' — pass "
                         f"--format {'|'.join(PROJECT_FORMAT_BUCKETS)}")

    dest_dir = library / _STAGE_DIRS[to_stage] / fmt
    if week_target is not None:
        dest_dir = dest_dir / week_label_for(week_target)
    dest = dest_dir / name
    if dest.exists():
        raise ValueError(f"destination already exists, refusing to overwrite: "
                         f"{dest.relative_to(library).as_posix()}")

    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    return {
        "src": src.relative_to(library).as_posix(),
        "dest": dest.relative_to(library).as_posix(),
        "format": fmt,
    }


def cmd_promote(args):
    """Move a finished project ACTIVE→DELIVERED→ARCHIVE so the stage move can't be
    forgotten. Finds the item by name in the source stage, infers its format, and
    files it into the destination stage's format/week folder."""
    library = _library(args.client)
    to_stage = args.to
    from_stage = args.from_stage or _DEFAULT_FROM[to_stage]

    if args.no_week:
        week_target = None
    elif args.week:
        week_target = date.fromisoformat(args.week)
    else:
        week_target = date.today()

    try:
        result = _promote_item(library, args.item, from_stage, to_stage,
                               args.format, week_target)
    except ValueError as e:
        print(f"\n  Error: {e}\n")
        sys.exit(1)

    print(f"\n  Promoted ({from_stage} → {to_stage}, {result['format']}):")
    print(f"    {result['src']}")
    print(f"    → {result['dest']}\n")


# ---- ship: post-delivery cleanup (v3.1) -----------------------------------
# When a finished video lands in 03_DELIVERED, archive its edit project AND file
# its raw footage into the library — in ONE reviewed step. Builds a plan first;
# nothing moves until confirmed. Reuses promote's find/infer helpers. The
# (moves, warnings) split lets a future folder-watcher reuse _ship_plan headless.

def _ship_plan(library: Path, video: str, project_name, footage_path,
               category, fmt, week_target):
    """Build the post-delivery cleanup plan for `video`. Returns (moves, warnings):
    moves = [{what, src(Path), dest(Path)}], warnings = [str]. Moves nothing.
    Raises ValueError on an ambiguous project or a destination that already exists."""
    moves, warnings = [], []

    # sanity: is there actually a delivered item by this name? (soft — names vary)
    delivered_root = library / FOLDER_DELIVERED
    if delivered_root.is_dir():
        hit = [p for p in delivered_root.rglob("*") if p.name == video or p.stem == video]
        if not hit:
            warnings.append(f"no item named '{video}' found in {FOLDER_DELIVERED} "
                            f"(double-check the name)")

    # 1) edit project (02_ACTIVE_PROJECTS) → 04_ARCHIVE
    active_root = library / FOLDER_PROJECTS
    pname = project_name or video
    found = _find_stage_item(active_root, pname) if active_root.is_dir() else []
    if len(found) > 1:
        listing = ", ".join(p.relative_to(library).as_posix() for p in found)
        raise ValueError(f"project '{pname}' is ambiguous in active projects: {listing}. "
                         f"Pass --project \"exact name\".")
    if found:
        src = found[0]
        pfmt = fmt or _infer_format(src, active_root) or "shorts"
        dest_dir = library / FOLDER_ARCHIVE / pfmt
        if week_target is not None:
            dest_dir = dest_dir / week_label_for(week_target)
        moves.append({"what": "edit project → archive", "src": src, "dest": dest_dir / src.name})
    else:
        warnings.append(f"no active project matched '{pname}' — skipping the project archive "
                        f"(pass --project to point at it)")

    # 2) raw footage (01_ORGANIZED) → 05_FOOTAGE_LIBRARY
    # Two filing systems on purpose:
    #   - batch interview originals → 05_FOOTAGE_LIBRARY/_BATCHES/Batch_NN/Vid_MM/
    #     (by batch/vid, NO week, index-skipped — its own system, kept off b-roll search)
    #   - loose b-roll shoots (--footage) → 05_FOOTAGE_LIBRARY/<category>/<week>/<folder>
    fsrc = None
    batch_dest = None
    if footage_path:
        p = Path(footage_path)
        fsrc = p if p.is_absolute() else library / footage_path
    else:
        m = re.search(r"[Bb]atch[\s_]*0*(\d+).*?[Vv]id[\s_]*0*(\d+)", video)
        if m:
            bn, vn = int(m.group(1)), int(m.group(2))
            guess = library / FOLDER_ORGANIZED / f"Batch_{bn:02d}" / f"Vid_{vn:02d}"
            if guess.is_dir():
                fsrc = guess
                batch_dest = (library / FOLDER_FOOTAGE_LIB / FOLDER_BATCHES
                              / f"Batch_{bn:02d}" / f"Vid_{vn:02d}")
    if fsrc and fsrc.exists():
        if batch_dest is not None:
            dest = batch_dest
        else:
            cat = category or video
            dest_dir = library / FOLDER_FOOTAGE_LIB / cat
            if week_target is not None:
                dest_dir = dest_dir / week_label_for(week_target)
            dest = dest_dir / fsrc.name
        moves.append({"what": "raw footage → library", "src": fsrc, "dest": dest})
    else:
        warnings.append("couldn't locate the raw footage — pass --footage <folder> to include it "
                        "(skipping the footage move)")

    for mv in moves:
        if mv["dest"].exists():
            raise ValueError(f"destination already exists, refusing to overwrite: "
                             f"{mv['dest'].relative_to(library).as_posix()}")
    return moves, warnings


def _episode_ship_plan(library, episode, footage_root=None, orient_fn=None, week_fn=None):
    """Finalize a delivered documentary episode. Move ALL its footage →
    b-roll/<week> (horizontal) or vertical/<week> (vertical), and archive the
    Premiere project → 04_ARCHIVE/longform/<week>/<episode>/. Returns
    (moves, warnings). footage_root defaults to 01_ORGANIZED/<episode>/.
    NOTE: moves are (src, dest) tuples — execute via _execute_consolidation, not _execute_ship."""
    orient_fn = orient_fn or (lambda p: get_display_orientation(str(p)))
    week_fn = week_fn or _filmed_week
    moves, warnings, seen, processed = [], [], set(), set()

    ep_root = Path(footage_root) if footage_root else (
        library / FOLDER_ORGANIZED / episode)
    footage = list(_walk_videos(ep_root)) if ep_root.is_dir() else []
    if not footage:
        warnings.append(f"no footage found under {ep_root}")

    archive_week = None
    for clip in footage:
        if clip in processed:
            continue
        group = _clip_group(clip)
        for f in group:
            processed.add(f)
        orientation, _flip = orient_fn(clip)
        bucket = (FOLDER_BROLL if orientation == "horizontal"
                  else FOLDER_VERTICAL if orientation == "vertical" else None)
        if bucket is None:
            warnings.append(f"undetermined orientation, left in source: {clip.name}")
            continue
        week = week_fn(clip) or current_week_label()
        archive_week = archive_week or week
        dest_dir = library / FOLDER_FOOTAGE_LIB / bucket / week
        for f in group:
            dest = dest_dir / f.name
            if dest.exists() or dest.as_posix() in seen:
                warnings.append(f"collision skipped: {f.name} -> {dest.relative_to(library).as_posix()}")
                continue
            seen.add(dest.as_posix())
            moves.append((f, dest))

    matches = _find_stage_item(library / FOLDER_PROJECTS, episode)
    if not matches:
        warnings.append(f"no active project named '{episode}' to archive")
    elif len(matches) > 1:
        warnings.append(f"multiple projects named '{episode}' — archive by hand: "
                        + ", ".join(str(m) for m in matches))
    else:
        wk = archive_week or current_week_label()
        dest = library / FOLDER_ARCHIVE / "longform" / wk / episode
        if dest.exists():
            warnings.append(f"archive destination already exists: {dest.relative_to(library).as_posix()}")
        else:
            moves.append((matches[0], dest))
    return moves, warnings


def _execute_ship(moves) -> None:
    for mv in moves:
        mv["dest"].parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(mv["src"]), str(mv["dest"]))


def _cmd_ship_episode(args, client):
    library = _library(client)
    footage_root = None
    if args.footage:
        footage_root = Path(args.footage)
        if not footage_root.is_absolute():
            footage_root = library / args.footage
    moves, warnings = _episode_ship_plan(library, args.episode, footage_root=footage_root)

    print(f"\n  Finalize episode: {args.episode}  ({client.upper()})")
    print(f"  Plan — {len(moves)} move(s):")
    for s, d in moves[:60]:
        print(f"    {s.name}  ->  {d.relative_to(library).as_posix()}")
    if len(moves) > 60:
        print(f"    … +{len(moves) - 60} more")
    for w in warnings:
        print(f"  ! {w}")
    if not moves:
        print("\n  Nothing to finalize.\n"); return
    if not args.yes and input("\n  Execute this finalize? [y/N]: ").strip().lower() != "y":
        print("  Aborted — nothing moved.\n"); return

    _execute_consolidation(moves)
    ep_root = footage_root or (library / FOLDER_ORGANIZED / args.episode)
    if ep_root.is_dir():
        _prune_empty_dirs(ep_root, keep="")
    db_path = _db(client)
    added, skipped, removed = _reindex(library, db_path)
    print(f"\n  Re-indexed: {added}, skipped {skipped}, removed {removed} missing")

    todo = [c for c in index.query(db_path, category=FOLDER_BROLL) if _is_untagged(c)]
    per_clip = VISION_TAG_COST_PER_CLIP.get(args.tag_model, 0.015)
    print(f"  Auto-tag {len(todo)} new b-roll clip(s)  Model: {args.tag_model}  Est. ~${len(todo) * per_clip:.2f}")
    if todo and (args.yes or input("  Proceed with the paid Vision run? [y/N]: ").strip().lower() == "y"):
        tagged, cache_hits, failed = _run_tagging(library, db_path, todo, args.tag_model)
        print(f"  Tagged {tagged} clip(s) ({cache_hits} from cache, {failed} skipped).")
    print(f"  Episode finalized. DB: {db_path}\n")


def cmd_ship(args):
    """Post-delivery cleanup: archive the edit project + file the footage, after
    showing the plan. Nothing moves until confirmed (or --yes)."""
    if getattr(args, "episode", None):
        return _cmd_ship_episode(args, args.client)
    if not getattr(args, "video", None):
        print("\n  Error: --video is required (or use --episode for a documentary episode)\n")
        sys.exit(1)
    library = _library(args.client)
    if args.no_week:
        week_target = None
    elif args.week:
        week_target = date.fromisoformat(args.week)
    else:
        week_target = date.today()

    try:
        moves, warnings = _ship_plan(library, args.video, args.project, args.footage,
                                     args.category, args.format, week_target)
    except ValueError as e:
        print(f"\n  Error: {e}\n")
        sys.exit(1)

    print(f"\n  Ship cleanup for: {args.video}")
    for w in warnings:
        print(f"  ! {w}")
    if not moves:
        print("\n  Nothing to move — check the name, or pass --project / --footage.\n")
        return

    print("\n  Planned moves (nothing has moved yet):")
    for mv in moves:
        print(f"    • {mv['what']}")
        print(f"        {mv['src'].relative_to(library).as_posix()}")
        print(f"        → {mv['dest'].relative_to(library).as_posix()}")

    if not args.yes:
        ans = input("\n  Proceed with these moves? [y/N]: ").strip().lower()
        if ans != "y":
            print("  Cancelled — nothing moved.\n")
            return

    _execute_ship(moves)
    print(f"\n  Done — moved {len(moves)} item(s).")
    db_path = _db(args.client)
    added, skipped, removed = _reindex(library, db_path)
    print(f"  Re-indexed: {added} clip(s), skipped {skipped}, removed {removed} missing\n")


def main():
    ap = argparse.ArgumentParser(description="Footage index + pull (v2)")
    ap.add_argument("--client", "-c", required=True, choices=list(CLIENT_ROOTS.keys()))
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("index", help="Scan library and refresh the SQLite index").set_defaults(func=cmd_index)

    p = sub.add_parser("pull", help="Filter index → output folder under 07_QUERY_PULLS/")
    p.add_argument("--category")
    p.add_argument("--orientation", choices=["vertical", "horizontal"])
    p.add_argument("--filmed-date", help="YYYY-MM-DD")
    p.add_argument("--filmed-after", help="YYYY-MM-DD")
    p.add_argument("--filmed-before", help="YYYY-MM-DD")
    p.add_argument("--min-duration", type=float)
    p.add_argument("--max-duration", type=float)
    p.add_argument("--emotion", help="b-roll tag (exact), e.g. focused")
    p.add_argument("--action", help="b-roll tag (exact), e.g. walking")
    p.add_argument("--location", help="b-roll tag (exact), e.g. \"times square\"")
    p.add_argument("--object", help="b-roll object tag (contains), e.g. \"coffee cup\"")
    p.add_argument("--by-week", action="store_true",
                   help="Group results into W##_MMM-DD-DD subfolders by filmed date")
    p.set_defaults(func=cmd_pull)

    b = sub.add_parser("batch", help="File a batch shoot into 01_ORGANIZED/Batch_NN/Vid_MM/ and re-index")
    b.add_argument("--num", type=int, required=True, help="Batch number, e.g. 2")
    b.add_argument("--from", dest="source", required=True,
                   help="Source folder holding the shoot's clips (relative to the library root, or absolute)")
    b.add_argument("--map", required=True,
                   help='Vid→clips map, e.g. "1:C2493-C2495 2:C2496-C2498 3:C2500"')
    b.set_defaults(func=cmd_batch)

    pr = sub.add_parser("promote", help="Move a finished project ACTIVE→DELIVERED→ARCHIVE into the right format/week folder")
    pr.add_argument("--item", required=True, help="Exact name of the file or folder to move")
    pr.add_argument("--to", required=True, choices=["delivered", "archive"], help="Destination stage")
    pr.add_argument("--from", dest="from_stage", choices=["active", "delivered"],
                    help="Source stage (default: active→delivered, delivered→archive)")
    pr.add_argument("--format", choices=PROJECT_FORMAT_BUCKETS,
                    help="Format bucket (inferred from the item's location if omitted)")
    pr.add_argument("--week", help="YYYY-MM-DD destination week folder (default: current week)")
    pr.add_argument("--no-week", action="store_true",
                    help="Place directly under the format bucket, not a week folder")
    pr.set_defaults(func=cmd_promote)

    sh = sub.add_parser("ship", help="After delivery: archive the edit project + file the footage into the library (shows a plan first)")
    sh.add_argument("--video", help="Name of the delivered video (the file you dropped in 03_DELIVERED)")
    sh.add_argument("--episode", help="Finalize a documentary episode: footage → library + auto-tag, project → archive")
    sh.add_argument("--project", help="Override: exact active-project name to archive")
    sh.add_argument("--footage", help="Override: footage folder to file into the library (relative or absolute)")
    sh.add_argument("--tag-model", default=VISION_TAG_MODEL, help=f"Vision model for the auto-tag pass (default {VISION_TAG_MODEL})")
    sh.add_argument("--category", help="Library sub-folder for the footage (default: the video name)")
    sh.add_argument("--format", choices=PROJECT_FORMAT_BUCKETS,
                    help="Format bucket for the archived project (inferred if omitted)")
    sh.add_argument("--week", help="YYYY-MM-DD destination week (default: current week)")
    sh.add_argument("--no-week", action="store_true", help="Place directly under the bucket, not a week folder")
    sh.add_argument("--yes", "-y", action="store_true", help="Skip the confirmation prompt")
    sh.set_defaults(func=cmd_ship)

    cw = sub.add_parser("create-week", help="Create this week's folder under every category in FOOTAGE_LIBRARY")
    cw.add_argument("--week", help="YYYY-MM-DD; defaults to today")
    cw.set_defaults(func=cmd_create_week)

    pc = sub.add_parser("pull-cleanup", help="Delete query-pull folders after the edit ships")
    pc.add_argument("--older-than", type=int, help="Auto-delete pulls N+ days old (no prompts)")
    pc.set_defaults(func=cmd_pull_cleanup)

    dc = sub.add_parser("drafts-cleanup", help="Delete review drafts in 03_DELIVERED/drafts/ untouched N+ days (never deletes project files)")
    dc.add_argument("--older-than", type=int, help="Auto-delete drafts N+ days old (no prompts)")
    dc.set_defaults(func=cmd_drafts_cleanup)

    cb = sub.add_parser("consolidate-broll", help="Flatten all category folders into 05_FOOTAGE_LIBRARY/b-roll/<week>/ (original weeks preserved); plan-first")
    cb.add_argument("--yes", "-y", action="store_true", help="Skip the confirmation prompt")
    cb.set_defaults(func=cmd_consolidate_broll)

    ik = sub.add_parser("intake", help="Route a new footage dump → b-roll/<week>/ (horizontal) or vertical/<week>/ (vertical) by orientation + filmed date; plan-first")
    ik.add_argument("--from", dest="source", help="Folder to intake (relative to library or absolute). Default: 01_ORGANIZED/_INBOX/<date>/")
    ik.add_argument("--date", help="YYYY-MM-DD: default inbox date + fallback week for clips with no readable filmed date")
    ik.add_argument("--tag", action="store_true", help="After filing, AI Vision-tag the new horizontal b-roll clips in one go")
    ik.add_argument("--tag-model", default=VISION_TAG_MODEL, help=f"Vision model for --tag (default {VISION_TAG_MODEL})")
    ik.add_argument("--yes", "-y", action="store_true", help="Skip the confirmation prompt")
    ik.set_defaults(func=cmd_intake)

    sv = sub.add_parser("split-vertical", help="Move vertical clips out of b-roll/ into vertical/<week>/ (parked, untagged); plan-first, rotation-aware")
    sv.add_argument("--yes", "-y", action="store_true", help="Skip the confirmation prompt")
    sv.set_defaults(func=cmd_split_vertical)

    tg = sub.add_parser("tag", help="AI Vision-tag b-roll clips → emotion/action/location/objects in the index")
    tg.add_argument("--model", default=VISION_TAG_MODEL, help=f"Vision model (default {VISION_TAG_MODEL}; pass claude-haiku-4-5 for cheap incremental runs)")
    tg.add_argument("--limit", type=int, help="Only tag the first N untagged clips (sample run)")
    tg.add_argument("--retag", action="store_true", help="Re-tag even already-tagged clips")
    tg.add_argument("--yes", "-y", action="store_true", help="Skip the cost-confirmation prompt")
    tg.add_argument("--episode", help="Tag a documentary episode's footage in place (01_ORGANIZED/<episode>/) so it's pull-able as b-roll before the episode ships. Default tags the b-roll library.")
    tg.set_defaults(func=cmd_tag)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
