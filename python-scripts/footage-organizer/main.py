"""
Auto Footage Organizer
Analyzes raw video files visually using Claude AI and organizes them
into the client's 02_ORGANIZED/ folder, split by format and date.

Usage:
  # Sort Sai's footage (point at the date folder you dumped to)
  python main.py --client sai 01_RAW_INCOMING/2026-04-16/

  # Sort your own footage
  python main.py --client graydient 01_RAW_INCOMING/

  # Move instead of copy
  python main.py --client sai 01_RAW_INCOMING/2026-04-16/ --move

Requires:
  - ANTHROPIC_API_KEY in .env
  - SAI_LIBRARY_ROOT and/or GRAYDIENT_LIBRARY_ROOT in .env
  - ffmpeg + ffprobe installed (https://ffmpeg.org/download.html)
"""
import argparse
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from usage_logger import log_run

from config import (
    CATEGORIES, VIDEO_EXTENSIONS, CLIENT_ROOTS,
    FORMAT_LONG_FORM, FORMAT_SHORT_FORM, FORMAT_OTHER,
    LONGFORM_WIDTH, LONGFORM_HEIGHT,
)
from extractor import ffmpeg_available, get_shoot_date, get_duration, get_resolution, extract_frames
from analyzer import classify_video
from organizer import organize_file
from cache import get_cached, store_cached


def parse_args():
    parser = argparse.ArgumentParser(
        description="Organize raw footage by format + date + content type using Claude AI."
    )
    parser.add_argument(
        "--client", "-c",
        required=True,
        choices=list(CLIENT_ROOTS.keys()),
        help="Which client's library to sort into (sai or graydient)"
    )
    parser.add_argument(
        "input_folder",
        nargs="?",
        default=None,
        help="Path to footage folder. Absolute, or relative to the client's library root."
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move files instead of copying (default: copy)"
    )
    return parser.parse_args()


def resolve_input_folder(client: str, input_arg: str) -> str:
    """
    Resolve the input folder path.
    If input_arg is absolute, use it directly.
    If relative, resolve it against the client library root.
    """
    library_root = CLIENT_ROOTS.get(client, "")
    if not library_root:
        print(f"\n  Error: {client.upper()}_LIBRARY_ROOT is not set in your .env file.")
        print(f"  Add it like: SAI_LIBRARY_ROOT=/Volumes/MySSD/Sai")
        sys.exit(1)

    if not input_arg:
        # Default to 01_RAW_INCOMING/ inside the library
        return os.path.join(library_root, "01_RAW_INCOMING")

    if os.path.isabs(input_arg):
        return input_arg

    # Relative path — resolve from library root
    return os.path.join(library_root, input_arg)


def get_output_dir(client: str) -> str:
    library_root = CLIENT_ROOTS[client]
    return os.path.join(library_root, "02_ORGANIZED")


def find_videos(folder: str) -> list[str]:
    """Return sorted list of video file paths — searches recursively."""
    files = []
    for root, _, filenames in os.walk(folder):
        for name in filenames:
            ext = os.path.splitext(name)[1]
            if ext in VIDEO_EXTENSIONS:
                files.append(os.path.join(root, name))
    return sorted(files)


def get_week_monday(date_str: str) -> str:
    """Given 'YYYY-MM-DD', return 'week-of-YYYY-MM-DD' for the Monday of that week."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    monday = dt - timedelta(days=dt.weekday())
    return f"week-of-{monday.strftime('%Y-%m-%d')}"


def build_date_path(format_type: str, shoot_date: str) -> str:
    """
    Build the date subfolder path within 02_ORGANIZED/format_type/.

    long-form:  "2026-04-16"
    short-form: "week-of-2026-04-14/2026-04-16"
    other:      "2026-04-16"
    """
    if format_type == FORMAT_SHORT_FORM:
        week = get_week_monday(shoot_date)
        return os.path.join(week, shoot_date)
    return shoot_date


def run(client: str, input_folder: str, output_dir: str, move: bool):
    log_run("footage-organizer")

    print(f"\n{'=' * 60}")
    print(f"  Auto Footage Organizer")
    print(f"{'=' * 60}")
    print(f"  Client: {client}")
    print(f"  Input:  {input_folder}")
    print(f"  Output: {output_dir}")
    print(f"  Mode:   {'MOVE' if move else 'COPY'}")
    print()

    videos = find_videos(input_folder)
    if not videos:
        print("  No .mp4 or .mov files found in that folder.")
        sys.exit(0)

    print(f"  Found {len(videos)} video file(s)\n")

    results = []   # (filename, format_type, shoot_date, category, dest_path, from_cache)
    skipped = []   # filenames that failed

    for i, filepath in enumerate(videos, 1):
        filename = os.path.basename(filepath)
        print(f"  [{i}/{len(videos)}] {filename}")

        # --- Detect format from resolution (free — no API call) ---
        try:
            width, height = get_resolution(filepath)
            if height > width:
                format_type = FORMAT_SHORT_FORM
            elif width >= LONGFORM_WIDTH and height >= LONGFORM_HEIGHT:
                format_type = FORMAT_LONG_FORM
            else:
                format_type = FORMAT_OTHER
            print(f"         {width}x{height} -> {format_type}")
        except Exception as e:
            print(f"         [skip] Could not read resolution: {e}")
            skipped.append(filename)
            continue

        # --- Read shoot date from camera metadata ---
        try:
            shoot_date = get_shoot_date(filepath)
            date_path = build_date_path(format_type, shoot_date)
            print(f"         date: {shoot_date}  path: {format_type}/{date_path}")
        except Exception as e:
            print(f"         [skip] Could not read shoot date: {e}")
            skipped.append(filename)
            continue

        # --- Cache check ---
        cached_category = get_cached(filepath)
        if cached_category:
            print(f"         (cached) -> {cached_category}")
            dest = organize_file(filepath, output_dir, format_type, date_path, cached_category, move=move)
            results.append((filename, format_type, shoot_date, cached_category, dest, True))
            continue

        # --- Extract frames ---
        try:
            duration = get_duration(filepath)
            frames_b64 = extract_frames(filepath, duration)
        except Exception as e:
            print(f"         [skip] Frame extraction failed: {e}")
            skipped.append(filename)
            continue

        # --- Classify with Claude ---
        try:
            category = classify_video(frames_b64, filename)
        except Exception as e:
            print(f"         [skip] Claude API error: {e}")
            skipped.append(filename)
            continue

        print(f"         -> {category}")
        store_cached(filepath, category)
        dest = organize_file(filepath, output_dir, format_type, date_path, category, move=move)
        results.append((filename, format_type, shoot_date, category, dest, False))

    _print_summary(results, skipped, output_dir, move)


def _print_summary(results, skipped, output_dir, move):
    print(f"\n{'=' * 60}")
    print(f"  DONE")
    print(f"{'=' * 60}\n")

    action = "Moved" if move else "Copied"
    total = len(results)
    cached_count = sum(1 for *_, from_cache in results if from_cache)
    new_count = total - cached_count

    print(f"  {action} {total} file(s)  ({new_count} analyzed, {cached_count} from cache)\n")

    from collections import defaultdict
    # breakdown[format_type][category] = count
    breakdown = defaultdict(lambda: defaultdict(int))
    for _, format_type, _, category, _, _ in results:
        breakdown[format_type][category] += 1

    for fmt in [FORMAT_LONG_FORM, FORMAT_SHORT_FORM, FORMAT_OTHER]:
        if fmt not in breakdown:
            continue
        fmt_total = sum(breakdown[fmt].values())
        print(f"  {fmt}  ({fmt_total} file(s)):")
        for category in CATEGORIES:
            count = breakdown[fmt].get(category, 0)
            if count > 0:
                bar = "#" * count
                print(f"    {category:<22} {bar}  ({count})")

    if skipped:
        print(f"\n  Skipped {len(skipped)} file(s):")
        for name in skipped:
            print(f"    - {name}")

    estimated_cost = new_count * 0.003
    print(f"\n  Estimated API cost this run: ~${estimated_cost:.3f}")
    print(f"  Output: {output_dir}\n")


if __name__ == "__main__":
    args = parse_args()

    input_folder = resolve_input_folder(args.client, args.input_folder)

    if not os.path.isdir(input_folder):
        print(f"\n  Error: '{input_folder}' is not a valid folder.")
        sys.exit(1)

    if not ffmpeg_available():
        print("\n  Error: ffmpeg and ffprobe are required but not found.")
        print("  Install from: https://ffmpeg.org/download.html")
        print("  Then make sure ffmpeg is in your system PATH.\n")
        sys.exit(1)

    output_dir = get_output_dir(args.client)
    os.makedirs(output_dir, exist_ok=True)

    run(args.client, input_folder, output_dir, move=args.move)
