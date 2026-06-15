"""
CLI for the v2 index + pull layer. Kept separate from main.py so the existing
organize/archive flow is untouched.

Commands:
  index         — scan the library, upsert every clip into SQLite
  pull          — filter index → hardlink results into 07_QUERY_PULLS/<slug>/
  batch         — file a shoot into 01_ORGANIZED/Batch_NN/Vid_MM/ then re-index
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
    FOLDER_PROJECTS, FOLDER_DELIVERED, FOLDER_ARCHIVE,
)

PROJECT_FORMAT_BUCKETS = ["episodes", "linkedin", "shorts"]
from extractor import get_resolution, get_duration, get_shoot_date
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
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(_PREMIERE_DIR_PREFIXES) and not d.endswith(".PRV")
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

    slug_parts = []
    if args.filmed_date: slug_parts.append(args.filmed_date)
    if args.category:    slug_parts.append(args.category)
    if args.orientation: slug_parts.append(args.orientation)
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
      - 05_FOOTAGE_LIBRARY/<category>/<W##>/   (17 categories)
      - 02_ACTIVE_PROJECTS/<format>/<W##>/      (3 format buckets)
      - 03_DELIVERED/<format>/<W##>/            (3 format buckets)
      - 04_ARCHIVE/<format>/<W##>/              (3 format buckets)
    Idempotent — folders that already exist are skipped. Returns (created, skipped).

    Single source of truth for both the manual `create-week` command and the
    lazy auto-creation that every command runs first, so Gray never has to
    remember to scaffold a week by hand."""
    label = week_label_for(target)
    lib_root = library / FOLDER_FOOTAGE_LIB

    # Seed the 17 standard categories, PLUS any freeform folders Gray already
    # made on disk (v3) so his own folders get weekly subfolders too. Skip
    # underscore-prefixed helpers like _TO_SORT — those aren't categories.
    freeform = []
    if lib_root.is_dir():
        freeform = [p.name for p in lib_root.iterdir()
                    if p.is_dir() and not p.name.startswith("_")]
    categories = sorted(set(CATEGORIES) | set(freeform))

    targets = []
    # Footage library: one folder per category (standard + freeform)
    for category in categories:
        targets.append(lib_root / category / label)
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
    print(f"  Spans: FOOTAGE_LIBRARY ({len(CATEGORIES)} categories) + ACTIVE/DELIVERED/ARCHIVE ({len(PROJECT_FORMAT_BUCKETS)} formats × 3 = {len(PROJECT_FORMAT_BUCKETS) * 3})")
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

    db_path = _db(client)
    added, skipped, removed = _reindex(library, db_path)
    print(f"\n  Re-indexed: {added} clip(s), skipped {skipped}, removed {removed} missing")
    print(f"  DB: {db_path}\n")


def main():
    ap = argparse.ArgumentParser(description="Footage index + pull (v2)")
    ap.add_argument("--client", "-c", required=True, choices=list(CLIENT_ROOTS.keys()))
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("index", help="Scan library and refresh the SQLite index").set_defaults(func=cmd_index)

    p = sub.add_parser("pull", help="Filter index → output folder under 08_QUERY_PULLS/")
    p.add_argument("--category")
    p.add_argument("--orientation", choices=["vertical", "horizontal"])
    p.add_argument("--filmed-date", help="YYYY-MM-DD")
    p.add_argument("--filmed-after", help="YYYY-MM-DD")
    p.add_argument("--filmed-before", help="YYYY-MM-DD")
    p.add_argument("--min-duration", type=float)
    p.add_argument("--max-duration", type=float)
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

    cw = sub.add_parser("create-week", help="Create this week's folder under every category in FOOTAGE_LIBRARY")
    cw.add_argument("--week", help="YYYY-MM-DD; defaults to today")
    cw.set_defaults(func=cmd_create_week)

    pc = sub.add_parser("pull-cleanup", help="Delete query-pull folders after the edit ships")
    pc.add_argument("--older-than", type=int, help="Auto-delete pulls N+ days old (no prompts)")
    pc.set_defaults(func=cmd_pull_cleanup)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
