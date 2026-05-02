"""
CLI for the v2 index + pull layer. Kept separate from main.py so the existing
organize/archive flow is untouched.

Commands:
  index   — scan the library, upsert every clip into SQLite
  pull    — filter index → hardlink results into _pulls/<slug>/
"""
import argparse
import hashlib
import os
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
)
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
    The `rel[1] in CATEGORIES` guard means new W##_MMM-DD-DD week folders parse correctly.
    """
    rel = filepath.relative_to(library).parts
    if len(rel) >= 4 and rel[0] in (FOLDER_FOOTAGE_LIB, FOLDER_ORGANIZED) and rel[1] in CATEGORIES:
        return rel[1]
    return "misc"


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


def cmd_index(args):
    client = args.client
    library = _library(client)
    db_path = _db(client)
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
            )
            index.upsert(db_path, rec)
            added += 1

    removed = index.remove_missing(db_path, library_root=library)
    print(f"\n  Indexed {added} clip(s), skipped {skipped}, removed {removed} missing")
    print(f"  DB: {db_path}\n")


def cmd_pull(args):
    client = args.client
    library = _library(client)
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
    )

    if result.count == 0:
        print(f"\n  Pull → {result.folder}")
        print(f"  Linked 0 clip(s). Run 'index' first if this is unexpected.\n")
    else:
        print(f"\n  Pull → {result.folder}")
        print(f"  Linked {result.count} clip(s); fallback copies: {result.fallback_copies}\n")


def cmd_create_week(args):
    """Create the current (or specified) week's folder under every category in FOOTAGE_LIBRARY.
    Idempotent — folders that already exist are skipped."""
    library = _library(args.client)
    footage_lib = library / FOLDER_FOOTAGE_LIB
    target = date.fromisoformat(args.week) if args.week else date.today()
    label = week_label_for(target)

    created = 0
    skipped = 0
    for category in CATEGORIES:
        path = footage_lib / category / label
        if path.exists():
            skipped += 1
            continue
        path.mkdir(parents=True)
        created += 1

    print(f"\n  Week {label} ({args.client.upper()})")
    print(f"  Created {created} folder(s), skipped {skipped} existing")
    print(f"  Library: {footage_lib}\n")


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
    p.set_defaults(func=cmd_pull)

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
