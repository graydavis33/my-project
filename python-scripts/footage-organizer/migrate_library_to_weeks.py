"""
One-time migration: convert FOOTAGE_LIBRARY from old shape to W##_MMM-DD-DD.

Before:
  06_FOOTAGE_LIBRARY/<category>/Apr 16 – Apr 19/         (empty stubs — alphabetical sort, broken)
  06_FOOTAGE_LIBRARY/<category>/2026-04-17/clip.MP4      (legacy daily folders — actual clips)

After:
  06_FOOTAGE_LIBRARY/<category>/W01_Apr-15-19/clip.MP4   (weekly folders, project-relative)

The script:
  - Deletes any subfolder under <category>/ named with the broken alphabetical pattern
    (e.g. "Apr 16 – Apr 19", "Aug 3 – Aug 9") IF it is empty.
  - For each subfolder named YYYY-MM-DD: computes the W## label and moves clips
    into <category>/<W##>/<filename>. Sony XML sidecars follow their MP4 partners.
  - Pre/post MP4 count check.
  - Dry-run mode.

Usage:
  python migrate_library_to_weeks.py --client sai --dry-run
  python migrate_library_to_weeks.py --client sai
"""

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from config import CLIENT_ROOTS, VIDEO_EXTENSIONS, FOLDER_FOOTAGE_LIB, CATEGORIES
from week_utils import week_label_for

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# "Apr 16 – Apr 19", "Aug 3 – Aug 9", "Apr 27 – May 3" — note the en-dash AND hyphen variants
RANGE_RE = re.compile(r"^[A-Z][a-z]{2} \d{1,2}\s*[–\-]\s*[A-Z][a-z]{2}? ?\d{1,2}$")


def parse_args():
    p = argparse.ArgumentParser(description="Migrate FOOTAGE_LIBRARY to W##_MMM-DD-DD week folders.")
    p.add_argument("--client", "-c", required=True, choices=list(CLIENT_ROOTS.keys()))
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def find_xml_sidecars(date_dir: Path, mp4_path: Path):
    """Sony pairs C####.MP4 with C####M01.XML. Look in the SAME folder as the MP4
    (legacy daily folders kept everything together)."""
    stem = mp4_path.stem
    out = []
    for c in [date_dir / f"{stem}M01.XML", date_dir / f"{stem}.XML"]:
        if c.exists():
            out.append(c)
    return out


def count_mp4s(root: Path):
    if not root.is_dir():
        return 0
    return sum(1 for p in root.rglob("*") if p.is_file() and p.suffix in VIDEO_EXTENSIONS)


def main():
    args = parse_args()
    library = Path(CLIENT_ROOTS.get(args.client, ""))
    if not library.exists():
        print(f"Error: library root for {args.client} not found at {library}")
        sys.exit(1)

    footage_lib = library / FOLDER_FOOTAGE_LIB
    if not footage_lib.is_dir():
        print(f"Error: {footage_lib} does not exist")
        sys.exit(1)

    print(f"\n  {'=' * 64}")
    print(f"  Migrate FOOTAGE_LIBRARY → W##_MMM-DD-DD ({args.client.upper()})")
    print(f"  {'=' * 64}")
    print(f"  Library:  {footage_lib}")
    print(f"  Mode:     {'DRY RUN (no changes)' if args.dry_run else 'EXECUTE (real moves)'}\n")

    pre_count = count_mp4s(footage_lib)
    print(f"  Pre-migration MP4 count: {pre_count}\n")

    moves = []         # (src_mp4, dst_mp4, [sidecars...])
    empty_stubs = []   # paths to delete (empty range-named folders)
    occupied_stubs = []  # range-named folders that contain files (would block delete)

    for category_dir in sorted(footage_lib.iterdir()):
        if not category_dir.is_dir():
            continue
        for sub in sorted(category_dir.iterdir()):
            if not sub.is_dir():
                continue
            if RANGE_RE.match(sub.name):
                # Range-named stub (Apr 16 – Apr 19 etc.) — should be empty
                contents = list(sub.iterdir())
                if not contents:
                    empty_stubs.append(sub)
                else:
                    occupied_stubs.append((sub, len(contents)))
                continue
            if DATE_RE.match(sub.name):
                # Legacy daily folder — clips need to move
                shoot_date = date.fromisoformat(sub.name)
                week_label = week_label_for(shoot_date)
                dst_dir = category_dir / week_label
                for clip in sorted(sub.iterdir()):
                    if not clip.is_file():
                        continue
                    if clip.suffix in VIDEO_EXTENSIONS:
                        sidecars = find_xml_sidecars(sub, clip)
                        moves.append((clip, dst_dir / clip.name, sidecars, dst_dir))

    # Report
    print(f"  Empty range-named stubs to delete:    {len(empty_stubs)}")
    print(f"  Range-named stubs with content (BAD): {len(occupied_stubs)}")
    print(f"  Clips to move (legacy day → week):    {len(moves)}\n")

    if occupied_stubs:
        print("  ABORT: range-named folders are not empty. Investigate manually:")
        for stub, n in occupied_stubs:
            print(f"    {stub.relative_to(footage_lib.parent)} — {n} item(s)")
        sys.exit(1)

    # Show planned moves
    for clip, dst, sidecars, _ in moves[:10]:
        rel_src = clip.relative_to(footage_lib.parent)
        rel_dst = dst.relative_to(footage_lib.parent)
        print(f"  PLAN  {rel_src}  →  {rel_dst}")
        for sc in sidecars:
            print(f"        + sidecar {sc.name}")
    if len(moves) > 10:
        print(f"  ... and {len(moves) - 10} more")
    print()

    # Show planned deletions sample
    for stub in empty_stubs[:5]:
        print(f"  DEL   {stub.relative_to(footage_lib.parent)}")
    if len(empty_stubs) > 5:
        print(f"  ... and {len(empty_stubs) - 5} more empty stubs")
    print()

    if args.dry_run:
        print(f"  DRY RUN complete. Re-run without --dry-run to execute.\n")
        sys.exit(0)

    # Execute moves first (so we don't delete a folder that still has stuff)
    for clip, dst, sidecars, dst_dir in moves:
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(clip), str(dst))
        for sc in sidecars:
            shutil.move(str(sc), str(dst_dir / sc.name))

    # Now prune the legacy day folders (they should be empty after moves)
    for clip, dst, sidecars, dst_dir in moves:
        old_dir = clip.parent
        if old_dir.is_dir() and not any(old_dir.iterdir()):
            old_dir.rmdir()

    # Delete empty range-named stubs
    deleted_stubs = 0
    for stub in empty_stubs:
        try:
            stub.rmdir()
            deleted_stubs += 1
        except OSError:
            pass

    post_count = count_mp4s(footage_lib)
    print(f"\n  Post-migration MP4 count: {post_count}")
    print(f"  Deleted {deleted_stubs} empty stub folder(s)")

    if post_count != pre_count:
        print(f"\n  ERROR: MP4 count changed during migration! ({pre_count} → {post_count})")
        sys.exit(2)

    print(f"\n  Migration verified: {pre_count} clip(s) preserved.")
    print(f"  Next: python cli_index.py --client {args.client} index\n")


if __name__ == "__main__":
    main()
