"""
Auto Footage Organizer
Analyzes raw video files visually using Claude AI and organizes them
into subfolders by content type.

Usage:
  python main.py /path/to/footage/
  python main.py /path/to/footage/ --output ~/Desktop/shoot-march19/
  python main.py /path/to/footage/ --move

Requires:
  - ANTHROPIC_API_KEY in .env
  - ffmpeg + ffprobe installed (https://ffmpeg.org/download.html)
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from usage_logger import log_run

from config import CATEGORIES, VIDEO_EXTENSIONS, FOOTAGE_INBOX, FORMAT_LONG_FORM, FORMAT_SHORT_FORM, FORMAT_OTHER, LONGFORM_WIDTH, LONGFORM_HEIGHT
from extractor import ffmpeg_available, get_duration, get_resolution, extract_frames
from analyzer import classify_video
from organizer import organize_file
from cache import get_cached, store_cached


def parse_args():
    parser = argparse.ArgumentParser(
        description="Organize raw footage by visual content using Claude AI."
    )
    parser.add_argument(
        "input_folder",
        nargs="?",
        default=None,
        help="Path to footage folder (default: FOOTAGE_INBOX from .env)"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output folder (default: input_folder/organized/)"
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move files instead of copying (default: copy)"
    )
    return parser.parse_args()


def find_videos(folder: str) -> list[str]:
    """Return sorted list of video file paths in folder (non-recursive)."""
    files = []
    for name in os.listdir(folder):
        ext = os.path.splitext(name)[1]
        if ext in VIDEO_EXTENSIONS:
            files.append(os.path.join(folder, name))
    return sorted(files)


def run(input_folder: str, output_dir: str, move: bool):
    log_run("footage-organizer")

    print(f"\n{'=' * 60}")
    print(f"  Auto Footage Organizer")
    print(f"{'=' * 60}")
    print(f"  Input:  {input_folder}")
    print(f"  Output: {output_dir}")
    print(f"  Mode:   {'MOVE' if move else 'COPY'}")
    print()

    videos = find_videos(input_folder)
    if not videos:
        print("  No .mp4 or .mov files found in that folder.")
        sys.exit(0)

    print(f"  Found {len(videos)} video file(s)\n")

    results = []   # (filename, format_type, category, dest_path, from_cache)
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

        # --- Cache check ---
        cached_category = get_cached(filepath)
        if cached_category:
            print(f"         (cached) -> {cached_category}")
            dest = organize_file(filepath, output_dir, format_type, cached_category, move=move)
            results.append((filename, format_type, cached_category, dest, True))
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
        dest = organize_file(filepath, output_dir, format_type, category, move=move)
        results.append((filename, format_type, category, dest, False))

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

    # Group by format, then category
    from collections import defaultdict
    breakdown = defaultdict(lambda: defaultdict(int))
    for _, format_type, category, _, _ in results:
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

    input_folder = args.input_folder or FOOTAGE_INBOX

    if not input_folder:
        print("\n  Error: No input folder specified.")
        print("  Set FOOTAGE_INBOX in your .env file, or pass a folder path as an argument.")
        print(r"  Example .env entry:  FOOTAGE_INBOX=C:\Users\Gray Davis\Desktop\Footage Inbox")
        sys.exit(1)

    if not os.path.isdir(input_folder):
        print(f"\n  Error: '{input_folder}' is not a valid folder.")
        sys.exit(1)

    if not ffmpeg_available():
        print("\n  Error: ffmpeg and ffprobe are required but not found.")
        print("  Install from: https://ffmpeg.org/download.html")
        print("  Then make sure ffmpeg is in your system PATH.\n")
        sys.exit(1)

    output_dir = args.output or os.path.join(input_folder, "organized")
    os.makedirs(output_dir, exist_ok=True)

    run(input_folder, output_dir, move=args.move)
