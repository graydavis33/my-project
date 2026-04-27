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
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8 — Windows console hits cp1252 by default.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from config import (
    CLIENT_ROOTS, VIDEO_EXTENSIONS, INDEX_DB_NAME, PULL_FOLDER_NAME,
    INDEX_SCAN_ROOTS, FORMAT_LONG_FORM, FORMAT_SHORT_FORM,
    FOLDER_FOOTAGE_LIB, FOLDER_ORGANIZED,
)
from extractor import get_resolution, get_duration, get_shoot_date
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


def _walk_videos(root: Path):
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if Path(name).suffix in VIDEO_EXTENSIONS:
                yield Path(dirpath) / name


def _category_from_path(filepath: Path, library: Path) -> str:
    """Infer category from the folder it lives in: .../{category}/{date}/clip.mp4
    or .../organized/{date}/{format}/{category}/clip.mp4."""
    rel = filepath.relative_to(library).parts
    # FOOTAGE_LIBRARY/{category}/{date}/clip.mp4   → rel[1] is category
    # ORGANIZED/{date}/{format}/{category}/clip.mp4 → rel[3] is category
    if len(rel) >= 4 and rel[0] == FOLDER_FOOTAGE_LIB:
        return rel[1]
    if len(rel) >= 5 and rel[0] == FOLDER_ORGANIZED:
        return rel[3]
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
            rec = index.ClipRecord(
                path=str(clip),
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

    removed = index.remove_missing(db_path)
    print(f"\n  Indexed {added} clip(s), skipped {skipped}, removed {removed} missing")
    print(f"  DB: {db_path}\n")


def cmd_pull(args):
    client = args.client
    library = _library(client)
    db_path = _db(client)
    if not db_path.exists():
        print(f"Error: index not built yet. Run: python cli_index.py --client {client} index")
        sys.exit(1)

    slug_parts = []
    if args.filmed_date: slug_parts.append(args.filmed_date)
    if args.category:    slug_parts.append(args.category)
    if args.orientation: slug_parts.append(args.orientation)
    slug = "-".join(slug_parts) or "all"
    out = library / PULL_FOLDER_NAME / slug

    fmt_map = {"vertical": FORMAT_SHORT_FORM, "horizontal": FORMAT_LONG_FORM}
    fmt = fmt_map.get(args.orientation) if args.orientation else None

    result = pull_mod.pull(
        db_path,
        out,
        category=args.category,
        format=fmt,
        filmed_date=args.filmed_date,
        filmed_after=args.filmed_after,
        filmed_before=args.filmed_before,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
    )

    if result.count == 0:
        print(f"\n  No clips matched.")
        return

    print(f"\n  Pulled {result.count} clip(s) → {result.folder}")
    if result.fallback_copies:
        print(f"  ({result.fallback_copies} fell back to copy — likely cross-drive)")
    print(f"\n  Drag this folder into Premiere:")
    print(f"  {result.folder}\n")


def main():
    ap = argparse.ArgumentParser(description="Footage index + pull (v2)")
    ap.add_argument("--client", "-c", required=True, choices=list(CLIENT_ROOTS.keys()))
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("index", help="Scan library and refresh the SQLite index").set_defaults(func=cmd_index)

    p = sub.add_parser("pull", help="Filter index → hardlink folder")
    p.add_argument("--category")
    p.add_argument("--orientation", choices=["vertical", "horizontal"])
    p.add_argument("--filmed-date", help="YYYY-MM-DD")
    p.add_argument("--filmed-after", help="YYYY-MM-DD")
    p.add_argument("--filmed-before", help="YYYY-MM-DD")
    p.add_argument("--min-duration", type=float)
    p.add_argument("--max-duration", type=float)
    p.set_defaults(func=cmd_pull)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
