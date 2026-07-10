"""
One-time migration: flatten 02_ORGANIZED layout.

Before:  02_ORGANIZED/<date>/<format>/<category>/clip.MP4
After:   02_ORGANIZED/<category>/<date>/clip.MP4

Same shape as 06_FOOTAGE_LIBRARY. Format folders disappear; format remains
queryable in the SQLite index. Sony XML sidecars (C####M01.XML at the date
top level) follow their MP4 partners into <category>/<date>/.

The script:
  - Walks 02_ORGANIZED/<YYYY-MM-DD>/<short-form|long-form>/<category>/*.MP4
  - Moves each clip to 02_ORGANIZED/<category>/<date>/<filename>
  - Matches & moves any XML sidecar at <date>/<stem>M01.XML alongside the MP4
  - Prunes empty <format>/<category>/ and <format>/ subtrees
  - Leaves <date>/ folders alone if they still contain anything else
    (Premiere projects, unmatched sidecars, etc.)
  - Pre/post MP4 count check — aborts with non-zero exit if mismatch

Dry run:  python migrate_to_flat_structure.py --client sai --dry-run
Execute:  python migrate_to_flat_structure.py --client sai
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from config import CLIENT_ROOTS, VIDEO_EXTENSIONS, FOLDER_ORGANIZED, FORMAT_LONG_FORM, FORMAT_SHORT_FORM

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FORMAT_DIRS = {FORMAT_LONG_FORM, FORMAT_SHORT_FORM}


def parse_args():
    p = argparse.ArgumentParser(description="Flatten 02_ORGANIZED into <category>/<date>/ shape.")
    p.add_argument("--client", "-c", required=True, choices=list(CLIENT_ROOTS.keys()))
    p.add_argument("--dry-run", action="store_true", help="Print planned moves without executing.")
    return p.parse_args()


def find_xml_sidecar(date_dir: Path, mp4_path: Path):
    """Sony pairs C####.MP4 with C####M01.XML at the date top level.
    Match by stem prefix: C2089.MP4 -> C2089M01.XML, C2089M01.MP4 -> C2089M01.XML."""
    stem = mp4_path.stem
    candidates = [date_dir / f"{stem}M01.XML", date_dir / f"{stem}.XML"]
    for c in candidates:
        if c.exists():
            return c
    return None


def collect_planned_moves(organized_dir: Path):
    """Returns list of (src_mp4, dst_mp4, src_xml_or_None, dst_xml_or_None)."""
    moves = []
    if not organized_dir.is_dir():
        return moves

    for date_dir in sorted(organized_dir.iterdir()):
        if not date_dir.is_dir() or not DATE_RE.match(date_dir.name):
            continue
        date_str = date_dir.name

        for fmt_dir in sorted(date_dir.iterdir()):
            if not fmt_dir.is_dir() or fmt_dir.name not in FORMAT_DIRS:
                continue

            for cat_dir in sorted(fmt_dir.iterdir()):
                if not cat_dir.is_dir():
                    continue
                category = cat_dir.name

                for clip in sorted(cat_dir.iterdir()):
                    if not clip.is_file() or clip.suffix not in VIDEO_EXTENSIONS:
                        continue
                    dst_clip = organized_dir / category / date_str / clip.name
                    src_xml = find_xml_sidecar(date_dir, clip)
                    dst_xml = (organized_dir / category / date_str / src_xml.name) if src_xml else None
                    moves.append((clip, dst_clip, src_xml, dst_xml))
    return moves


def count_mp4s(root: Path):
    if not root.is_dir():
        return 0
    return sum(1 for p in root.rglob("*") if p.is_file() and p.suffix in VIDEO_EXTENSIONS)


def execute_moves(moves, dry_run: bool):
    for src_clip, dst_clip, src_xml, dst_xml in moves:
        rel = src_clip.relative_to(src_clip.parents[3])  # readable label
        if dry_run:
            print(f"  PLAN  {rel}  ->  {dst_clip.relative_to(dst_clip.parents[2])}")
            if src_xml:
                print(f"        + sidecar {src_xml.name}")
            continue
        dst_clip.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_clip), str(dst_clip))
        if src_xml and dst_xml:
            shutil.move(str(src_xml), str(dst_xml))


def prune_empty_format_subtrees(organized_dir: Path, dry_run: bool):
    """After moves, remove now-empty <date>/<format>/<category>/ and <date>/<format>/.
    Stop at <date>/ — those may hold Premiere projects, XML stragglers, etc."""
    pruned = 0
    for date_dir in sorted(organized_dir.iterdir()):
        if not date_dir.is_dir() or not DATE_RE.match(date_dir.name):
            continue
        for fmt_dir in list(date_dir.iterdir()):
            if not fmt_dir.is_dir() or fmt_dir.name not in FORMAT_DIRS:
                continue
            # Drill into category subdirs first
            for cat_dir in list(fmt_dir.iterdir()):
                if cat_dir.is_dir() and not any(cat_dir.iterdir()):
                    if dry_run:
                        print(f"  PRUNE {cat_dir.relative_to(organized_dir.parent)}")
                    else:
                        cat_dir.rmdir()
                    pruned += 1
            # Then prune the format dir if it's now empty
            if fmt_dir.is_dir() and not any(fmt_dir.iterdir()):
                if dry_run:
                    print(f"  PRUNE {fmt_dir.relative_to(organized_dir.parent)}")
                else:
                    fmt_dir.rmdir()
                pruned += 1
    return pruned


def main():
    args = parse_args()
    library = Path(CLIENT_ROOTS.get(args.client, ""))
    if not library.exists():
        print(f"Error: library root for {args.client} not found at {library}")
        sys.exit(1)

    organized = library / FOLDER_ORGANIZED
    if not organized.is_dir():
        print(f"Error: {organized} does not exist")
        sys.exit(1)

    print(f"\n  {'=' * 56}")
    print(f"  Migrate ORGANIZED -> <category>/<date>/  ({args.client.upper()})")
    print(f"  {'=' * 56}")
    print(f"  Library:  {library}")
    print(f"  Target:   {organized}")
    print(f"  Mode:     {'DRY RUN (no changes)' if args.dry_run else 'EXECUTE (real moves)'}\n")

    pre_count = count_mp4s(organized)
    moves = collect_planned_moves(organized)
    print(f"  Pre-migration MP4 count under {FOLDER_ORGANIZED}/: {pre_count}")
    print(f"  Planned MP4 moves: {len(moves)}\n")

    if not moves:
        print("  Nothing to migrate. Exiting cleanly.\n")
        sys.exit(0)

    execute_moves(moves, args.dry_run)

    pruned = prune_empty_format_subtrees(organized, args.dry_run)
    print(f"\n  Pruned {pruned} empty subdir(s)")

    if args.dry_run:
        print(f"\n  DRY RUN complete. Re-run without --dry-run to execute.\n")
        sys.exit(0)

    post_count = count_mp4s(organized)
    print(f"\n  Post-migration MP4 count under {FOLDER_ORGANIZED}/: {post_count}")

    if post_count != pre_count:
        print(f"\n  ERROR: MP4 count changed during migration! ({pre_count} -> {post_count})")
        print(f"  Files may have been lost. Investigate before re-indexing.")
        sys.exit(2)

    print(f"\n  Migration verified: {pre_count} clip(s) preserved.\n")
    print(f"  Next:  python cli_index.py --client {args.client} index\n")


if __name__ == "__main__":
    main()
