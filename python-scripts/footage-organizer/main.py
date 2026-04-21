"""
Auto Footage Organizer
Analyzes raw video using Claude AI and organizes by format + content type.

Folder structure (inside each client's library root):
  00_TEMPLATES/                        ← LUTs, title cards, Premiere templates
  01_RAW_INCOMING/YYYY-MM-DD/          ← dump card here each shoot day
  02_ORGANIZED/YYYY-MM-DD/             ← AI-sorted output (long-form/ or short-form/ → category/)
  03_ACTIVE_PROJECTS/                  ← active editing projects by format → week
  04_DELIVERED/                        ← finished published exports by format → week
  05_ARCHIVE/                          ← Premiere files by long-form/short-form → week
  06_FOOTAGE_LIBRARY/category/week/    ← reusable footage library
  07_ASSETS/                           ← brand assets, fonts, music, SFX

Usage:
  # First-time setup — create all folders
  python main.py --client sai --setup

  # Organize today's RAW footage (moves files, deletes RAW folder after)
  python main.py --client sai

  # Organize a specific date
  python main.py --client sai --date 2026-04-15

  # Keep originals in RAW (copy instead of move)
  python main.py --client sai --copy

  # Archive an organized date → 06_FOOTAGE_LIBRARY/{category}/{date}/
  # Run after you've pulled your selects into ACTIVE_PROJECTS/. Deletes ORGANIZED/{date}/.
  python main.py --client sai --archive 2026-04-16
"""
import argparse
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import date

# Windows default console encoding (cp1252) can't render the arrows / em-dashes used
# in this script's output. Force UTF-8 on stdout/stderr so prints don't crash.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from usage_logger import log_run

from config import (
    CLIENT_ROOTS, VIDEO_EXTENSIONS,
    FOLDER_TEMPLATES, FOLDER_RAW, FOLDER_ORGANIZED, FOLDER_PROJECTS,
    FOLDER_DELIVERED, FOLDER_ARCHIVE, FOLDER_FOOTAGE_LIB, FOLDER_ASSETS,
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
        help="Folder name to process (YYYY-MM-DD or any label like 'old-broll'). Defaults to today."
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of moving (default: move and delete RAW folder)"
    )
    parser.add_argument(
        "--archive",
        metavar="DATE",
        help="Move clips from ORGANIZED/DATE/ into FOOTAGE_LIBRARY/{category}/{date}/. "
             "Run after pulling your selects into ACTIVE_PROJECTS/."
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Create full folder structure for this client (run once on first use)"
    )
    return parser.parse_args()


def check_cache_synced():
    """Warn if the remote has newer .cache.json not yet pulled. Prevents the
    2026-04-16 misc/ bug — running archive on Windows without pulling the Mac's
    cache updates caused all 40 clips to fall back to misc/.

    Read-only: runs `git fetch` only, never pulls or modifies anything.
    Silently skips if git is unavailable or no upstream is configured.
    """
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    cache_rel = "python-scripts/footage-organizer/.cache.json"
    try:
        subprocess.run(
            ["git", "fetch", "--quiet"],
            cwd=repo_root, check=True, timeout=20,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        result = subprocess.run(
            ["git", "log", "--oneline", "HEAD..@{u}", "--", cache_rel],
            cwd=repo_root, capture_output=True, text=True, timeout=10,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return
    if result.returncode != 0 or not result.stdout.strip():
        return

    print("\n  " + "=" * 56)
    print("  WARNING: Remote has newer .cache.json not yet pulled")
    print("  " + "=" * 56)
    print("  Running now risks re-categorizing clips and losing cache hits")
    print("  (this is what caused the 2026-04-16 misc/ incident).")
    print()
    print("  Incoming commits touching .cache.json:")
    for line in result.stdout.strip().split("\n"):
        print(f"    {line}")
    print()
    print("  Recommended: abort, run `git pull`, then re-run this command.")
    print()
    try:
        answer = input("  Continue anyway? [y/N]: ").strip().lower()
    except EOFError:
        answer = ""
    if answer != "y":
        print("  Aborted — run `git pull` and try again.\n")
        sys.exit(0)
    print()


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
        os.path.join(library, FOLDER_ARCHIVE, "long-form"),
        os.path.join(library, FOLDER_ARCHIVE, "short-form"),
        os.path.join(library, FOLDER_ASSETS, "fonts"),
        os.path.join(library, FOLDER_ASSETS, "music"),
        os.path.join(library, FOLDER_ASSETS, "sfx"),
        os.path.join(library, FOLDER_ASSETS, "brand"),
    ]
    for cat in CATEGORIES:
        dirs.append(os.path.join(library, FOLDER_FOOTAGE_LIB, cat))

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
    print(f"    {FOLDER_FOOTAGE_LIB}/  ← {len(CATEGORIES)} category folders, each with week subfolders")
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
    print(f"  Mode:   {'COPY (originals stay in RAW/)' if not move else 'MOVE (RAW folder deleted after)'}")
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

    real_skips = [s for s in skipped if not s.startswith("._")]
    if not real_skips:
        shutil.rmtree(raw_folder)
        print(f"  Deleted RAW folder: {raw_folder}\n")


def run_archive(client, date_str):
    library = get_library(client)
    organized_date = os.path.join(library, FOLDER_ORGANIZED, date_str)
    footage_lib    = os.path.join(library, FOLDER_FOOTAGE_LIB)

    if not os.path.isdir(organized_date):
        print(f"\n  Error: No organized folder found: {organized_date}")
        print(f"  Run the organizer first: python main.py --client {client} --date {date_str}")
        sys.exit(1)

    print(f"\n  {'=' * 56}")
    print(f"  Archive to Footage Library — {client.upper()} — {date_str}")
    print(f"  {'=' * 56}")
    print(f"  From: {organized_date}")
    print(f"  To:   {FOLDER_FOOTAGE_LIB}/{{category}}/{date_str}/")
    print()

    videos = find_videos(organized_date)
    if not videos:
        print("  No videos found.")
        sys.exit(0)

    moved = 0
    by_category = defaultdict(int)

    for filepath in videos:
        cached_cat = get_cached(filepath)
        category = cached_cat if cached_cat else "misc"
        archive_file(filepath, footage_lib, os.path.join(category, date_str), move=True)
        by_category[category] += 1
        moved += 1
        print(f"  {os.path.basename(filepath)} → {category}/{date_str}/")

    shutil.rmtree(organized_date)
    print(f"\n  Moved {moved} clip(s) into {FOLDER_FOOTAGE_LIB}/  ({date_str})")
    for cat, count in sorted(by_category.items()):
        print(f"    {cat:<26} {count} file(s)")
    print(f"\n  Deleted organized folder: {organized_date}\n")



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
    print(f"    1. Pull selects from {FOLDER_ORGANIZED}/{date_str}/ into {FOLDER_PROJECTS}/ for editing")
    print(f"    2. Archive to Footage Library (deletes ORGANIZED/{date_str}/):")
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

    check_cache_synced()

    if args.archive:
        run_archive(args.client, args.archive)
    else:
        date_str = args.date or date.today().strftime("%Y-%m-%d")
        run_organize(args.client, date_str, move=not args.copy)
