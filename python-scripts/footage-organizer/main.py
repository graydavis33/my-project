"""
Auto Footage Organizer
Analyzes raw video using Claude AI and organizes by format + content type.

Folder structure (inside each client's library root):
  00_TEMPLATES/                        ← LUTs, title cards, Premiere templates
  01_RAW_INCOMING/YYYY-MM-DD/          ← dump card here each shoot day
  02_ORGANIZED/YYYY-MM-DD/             ← AI-sorted output (long-form/ or short-form/ → category/)
  03_PROJECTS/                         ← active editing projects (you manage this manually)
  04_DELIVERED/                        ← finished published exports
  05_ARCHIVE/                          ← old/retired projects
  06_BROLL_LIBRARY/category/           ← global reusable footage library, no dates
  07_ASSETS/                           ← brand assets, fonts, music, SFX

Usage:
  # First-time setup — create all folders
  python main.py --client sai --setup
  python main.py --client graydient --setup

  # Organize today's RAW footage
  python main.py --client sai
  python main.py --client graydient

  # Organize a specific date
  python main.py --client sai --date 2026-04-15

  # Move instead of copy (saves disk space — use when you're sure)
  python main.py --client sai --move

  # Archive unused clips from a date → global ARCHIVE/
  # Run this after you've pulled your selects into PROJECTS/
  python main.py --client sai --archive 2026-04-16
"""
import argparse
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from usage_logger import log_run

from config import (
    CLIENT_ROOTS, VIDEO_EXTENSIONS,
    FOLDER_TEMPLATES, FOLDER_RAW, FOLDER_ORGANIZED, FOLDER_PROJECTS,
    FOLDER_DELIVERED, FOLDER_ARCHIVE, FOLDER_BROLL_LIB, FOLDER_ASSETS,
    CATEGORIES,
    FORMAT_LONG_FORM, FORMAT_SHORT_FORM,
)
from extractor import ffmpeg_available, get_duration, get_resolution, extract_frames
from analyzer import classify_video
from organizer import organize_file, archive_file
from cache import get_cached, store_cached


def parse_args():
    parser = argparse.ArgumentParser(
        description="Organize raw footage by format + content type using Claude AI."
    )
    parser.add_argument(
        "--client", "-c",
        required=True,
        choices=list(CLIENT_ROOTS.keys()),
        help="Which client library to use: sai or graydient"
    )
    parser.add_argument(
        "--date", "-d",
        default=None,
        help="Date to process (YYYY-MM-DD). Defaults to today."
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move files instead of copying (default: copy)"
    )
    parser.add_argument(
        "--archive",
        metavar="DATE",
        help="Move organized clips from ORGANIZED/DATE/ into global ARCHIVE/. "
             "Run after pulling selects into PROJECTS/."
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Create full folder structure for this client (run once on first use)"
    )
    return parser.parse_args()


def get_library(client):
    root = CLIENT_ROOTS.get(client, "")
    if not root:
        print(f"\n  Error: {client.upper()}_LIBRARY_ROOT is not set in your .env file.")
        print(f"  Add it like: SAI_LIBRARY_ROOT=/Volumes/SSD/Sai")
        sys.exit(1)
    return root


def setup_structure(library, client):
    dirs = [
        os.path.join(library, FOLDER_TEMPLATES),
        os.path.join(library, FOLDER_RAW),
        os.path.join(library, FOLDER_ORGANIZED),
        os.path.join(library, FOLDER_PROJECTS, "episodes"),
        os.path.join(library, FOLDER_PROJECTS, "shorts"),
        os.path.join(library, FOLDER_PROJECTS, "linkedin"),
        os.path.join(library, FOLDER_DELIVERED, "episodes"),
        os.path.join(library, FOLDER_DELIVERED, "shorts"),
        os.path.join(library, FOLDER_DELIVERED, "linkedin"),
        os.path.join(library, FOLDER_ARCHIVE),
        os.path.join(library, FOLDER_ASSETS, "fonts"),
        os.path.join(library, FOLDER_ASSETS, "music"),
        os.path.join(library, FOLDER_ASSETS, "sfx"),
        os.path.join(library, FOLDER_ASSETS, "brand"),
    ]
    for cat in CATEGORIES:
        dirs.append(os.path.join(library, FOLDER_BROLL_LIB, cat))

    for path in dirs:
        os.makedirs(path, exist_ok=True)

    print(f"\n  {'=' * 56}")
    print(f"  Footage Organizer — {client.upper()} — Setup Complete")
    print(f"  {'=' * 56}")
    print(f"  Library: {library}")
    print()
    print(f"  Folders created:")
    print(f"    {FOLDER_TEMPLATES}/    ← LUTs, Premiere templates, title cards")
    print(f"    {FOLDER_RAW}/  ← dump card footage here each day (dated)")
    print(f"    {FOLDER_ORGANIZED}/   ← AI-sorted output (dated)")
    print(f"    {FOLDER_PROJECTS}/    ← active edits")
    print(f"    {FOLDER_DELIVERED}/   ← finished published exports")
    print(f"    {FOLDER_ARCHIVE}/     ← old/retired projects")
    print(f"    {FOLDER_BROLL_LIB}/  ← {len(CATEGORIES)} category folders for reusable footage")
    print(f"    {FOLDER_ASSETS}/      ← brand assets, fonts, music, SFX")
    print()
    print(f"  Next step: copy today's card into {FOLDER_RAW}/{date.today().strftime('%Y-%m-%d')}/")
    print(f"  Then run:  python main.py --client {client}\n")


def find_videos(folder):
    files = []
    for root, _, filenames in os.walk(folder):
        for name in filenames:
            if os.path.splitext(name)[1] in VIDEO_EXTENSIONS:
                files.append(os.path.join(root, name))
    return sorted(files)


def detect_format(filepath):
    width, height = get_resolution(filepath)
    if height > width:
        fmt = FORMAT_SHORT_FORM
    else:
        fmt = FORMAT_LONG_FORM
    return fmt, width, height


def run_organize(client, date_str, move):
    log_run("footage-organizer")
    library = get_library(client)

    raw_folder   = os.path.join(library, FOLDER_RAW, date_str)
    organized_dir = os.path.join(library, FOLDER_ORGANIZED)

    if not os.path.isdir(raw_folder):
        print(f"\n  Error: RAW folder not found: {raw_folder}")
        print(f"  Dump your card footage there first, then re-run.")
        print(f"  Expected path: {FOLDER_RAW}/{date_str}/")
        sys.exit(1)

    print(f"\n  {'=' * 56}")
    print(f"  Footage Organizer — {client.upper()} — {date_str}")
    print(f"  {'=' * 56}")
    print(f"  Input:  {raw_folder}")
    print(f"  Output: {organized_dir}/{date_str}/")
    print(f"  Mode:   {'MOVE' if move else 'COPY (originals stay in RAW/)'}")
    print()

    videos = find_videos(raw_folder)
    if not videos:
        print(f"  No .mp4 or .mov files found in {raw_folder}")
        sys.exit(0)

    print(f"  Found {len(videos)} video file(s)\n")

    results = []
    skipped = []

    for i, filepath in enumerate(videos, 1):
        filename = os.path.basename(filepath)
        print(f"  [{i}/{len(videos)}] {filename}")

        try:
            fmt, w, h = detect_format(filepath)
            print(f"         {w}x{h} → {fmt}")
        except Exception as e:
            print(f"         [skip] Could not read resolution: {e}")
            skipped.append(filename)
            continue

        cached = get_cached(filepath)
        if cached:
            print(f"         (cached) → {cached}")
            dest = organize_file(filepath, organized_dir, fmt, date_str, cached, move=move)
            results.append((filename, fmt, cached, dest, True))
            continue

        try:
            duration = get_duration(filepath)
            frames_b64 = extract_frames(filepath, duration)
        except Exception as e:
            print(f"         [skip] Frame extraction failed: {e}")
            skipped.append(filename)
            continue

        try:
            category = classify_video(frames_b64, filename)
        except Exception as e:
            print(f"         [skip] Claude API error: {e}")
            skipped.append(filename)
            continue

        print(f"         → {category}")
        store_cached(filepath, category)
        dest = organize_file(filepath, organized_dir, fmt, date_str, category, move=move)
        results.append((filename, fmt, category, dest, False))

    _print_organize_summary(results, skipped, organized_dir, date_str, move, client)


def monday_of_week(date_str):
    """
    Given 'YYYY-MM-DD', return the Monday of that ISO week as 'YYYY-MM-DD'.
    Used to bucket archived B-roll by week shot.
    """
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    monday = d - timedelta(days=d.weekday())
    return monday.strftime("%Y-%m-%d")


def run_archive(client, date_str):
    library = get_library(client)
    organized_date = os.path.join(library, FOLDER_ORGANIZED, date_str)
    broll_dir      = os.path.join(library, FOLDER_BROLL_LIB)
    week           = monday_of_week(date_str)

    if not os.path.isdir(organized_date):
        print(f"\n  Error: No organized folder found: {organized_date}")
        print(f"  Run the organizer first: python main.py --client {client} --date {date_str}")
        sys.exit(1)

    print(f"\n  {'=' * 56}")
    print(f"  Send to B-Roll Library — {client.upper()} — {date_str}")
    print(f"  {'=' * 56}")
    print(f"  From: {organized_date}")
    print(f"  To:   {broll_dir}/{{category}}/{week}/   (week of {week})")
    print()

    videos = find_videos(organized_date)
    if not videos:
        print("  No videos found.")
        sys.exit(0)

    moved = 0
    by_category = defaultdict(int)

    for filepath in videos:
        cached_cat = get_cached(filepath)
        category = cached_cat if cached_cat else "miscellaneous"
        archive_file(filepath, broll_dir, os.path.join(category, week), move=True)
        by_category[category] += 1
        moved += 1
        print(f"  {os.path.basename(filepath)} → {FOLDER_BROLL_LIB}/{category}/{week}/")

    print(f"\n  Moved {moved} file(s) into {FOLDER_BROLL_LIB}/  (week of {week})")
    for cat, count in sorted(by_category.items()):
        print(f"    {cat:<26} {count} file(s)")
    print()


def _print_organize_summary(results, skipped, organized_dir, date_str, move, client):
    print(f"\n  {'=' * 56}")
    print(f"  DONE")
    print(f"  {'=' * 56}\n")

    action = "Moved" if move else "Copied"
    total = len(results)
    cached_count = sum(1 for *_, fc in results if fc)
    new_count = total - cached_count

    print(f"  {action} {total} file(s)  ({new_count} analyzed by Claude, {cached_count} from cache)\n")

    breakdown = defaultdict(lambda: defaultdict(int))
    for _, fmt, cat, _, _ in results:
        breakdown[fmt][cat] += 1

    for fmt in [FORMAT_LONG_FORM, FORMAT_SHORT_FORM]:
        if fmt not in breakdown:
            continue
        fmt_total = sum(breakdown[fmt].values())
        print(f"  {fmt}  ({fmt_total} file(s)):")
        for cat in CATEGORIES:
            count = breakdown[fmt].get(cat, 0)
            if count > 0:
                bar = "#" * count
                print(f"    {cat:<26} {bar}  ({count})")
        print()

    if skipped:
        print(f"  Skipped {len(skipped)} file(s):")
        for name in skipped:
            print(f"    - {name}")
        print()

    estimated_cost = new_count * 0.003
    print(f"  Estimated API cost this run: ~${estimated_cost:.3f}")
    print(f"  Output: {organized_dir}/{date_str}/")
    print()
    print(f"  Next steps:")
    print(f"    1. Pull selects into {FOLDER_PROJECTS}/ for editing")
    print(f"    2. Send unused clips to the B-Roll Library:")
    print(f"       python main.py --client {client} --archive {date_str}")
    print()


if __name__ == "__main__":
    args = parse_args()
    library = get_library(args.client)

    if args.setup:
        setup_structure(library, args.client)
        sys.exit(0)

    if not ffmpeg_available():
        print("\n  Error: ffmpeg and ffprobe are required but not found in PATH.")
        print("  Install: https://ffmpeg.org/download.html\n")
        sys.exit(1)

    if args.archive:
        run_archive(args.client, args.archive)
    else:
        date_str = args.date or date.today().strftime("%Y-%m-%d")
        run_organize(args.client, date_str, args.move)
