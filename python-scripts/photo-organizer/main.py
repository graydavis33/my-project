"""
Photo Organizer — One-Time Use Script
--------------------------------------
Analyzes ~1,800 Canon RAW (CR3) photos visually using Claude Haiku,
groups them by location/scene, removes blurry ones, and keeps the top 20%
per location.

Output folders:
  output/organized/[Location]/   ← your best photos
  output/rejected/[Location]/    ← everything else (review if needed)

Usage:
  python3 main.py /path/to/your/photos
  python3 main.py /path/to/your/photos --output ~/Desktop/sorted
  python3 main.py /path/to/your/photos --top 30    (keep top 30% instead)

Requires ANTHROPIC_API_KEY in a .env file in this folder.
"""

import argparse
import math
import os
import shutil
import sys

from dotenv import load_dotenv

from config import (
    PHOTO_EXTENSIONS,
    BLUR_THRESHOLD,
    TOP_PERCENT,
    ORGANIZED_FOLDER,
    REJECTED_FOLDER,
    VISION_CACHE_FILE,
)
from extractor import find_photos
from scorer import is_blurry, quality_score
from locator import build_location_groups


# ── Helpers ───────────────────────────────────────────────────────────────────

def progress(current: int, total: int, label: str = ""):
    bar_len = 40
    filled = int(bar_len * current / total) if total else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    pct = (current / total * 100) if total else 0
    print(f"\r  [{bar}] {pct:5.1f}%  {label[:50]:<50}", end="", flush=True)
    if current == total:
        print()


def copy_file(src: str, dest_folder: str):
    os.makedirs(dest_folder, exist_ok=True)
    dest = os.path.join(dest_folder, os.path.basename(src))
    if os.path.exists(dest):
        base, ext = os.path.splitext(os.path.basename(src))
        i = 1
        while os.path.exists(dest):
            dest = os.path.join(dest_folder, f"{base}_{i}{ext}")
            i += 1
    shutil.copy2(src, dest)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nERROR: ANTHROPIC_API_KEY not found.")
        print("Create a .env file in this folder with:")
        print("  ANTHROPIC_API_KEY=your-key-here\n")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Organize photos by visual location, keep top 20%.")
    parser.add_argument("input_folder", help="Folder containing your photos")
    parser.add_argument("--output", "-o", default=None,
                        help="Where to save results (default: input_folder/output/)")
    parser.add_argument("--top", type=float, default=None,
                        help="Percent to keep per location, e.g. 30 keeps top 30%% (default: 20)")
    args = parser.parse_args()

    input_folder = os.path.expanduser(args.input_folder)
    if not os.path.isdir(input_folder):
        print(f"\nERROR: Folder not found: {input_folder}\n")
        sys.exit(1)

    output_folder = os.path.expanduser(args.output) if args.output else os.path.join(input_folder, "output")
    top_percent   = (args.top / 100.0) if args.top else TOP_PERCENT
    cache_path    = os.path.join(output_folder, VISION_CACHE_FILE)
    os.makedirs(output_folder, exist_ok=True)

    print(f"\n Photo Organizer")
    print(f"  Input:   {input_folder}")
    print(f"  Output:  {output_folder}")
    print(f"  Keeping: top {int(top_percent * 100)}% per location\n")

    # ── Step 1: Find photos ───────────────────────────────────────────────────
    print("Step 1/4  Scanning for photos...")
    all_photos = find_photos(input_folder, PHOTO_EXTENSIONS)
    all_photos = [p for p in all_photos if not p.startswith(output_folder)]
    total = len(all_photos)
    print(f"  Found {total} photos\n")

    if total == 0:
        print("No photos found. Check the folder path and try again.")
        sys.exit(0)

    # ── Step 2: Blur detection + quality scoring ──────────────────────────────
    print("Step 2/4  Checking sharpness and quality (runs locally, no API cost)...")
    photo_scores:  dict = {}   # path → float score
    blurry_photos: list = []
    sharp_photos:  list = []

    for i, path in enumerate(all_photos):
        progress(i + 1, total, os.path.basename(path))
        blurry, blur_val = is_blurry(path)
        if blurry:
            blurry_photos.append(path)
        else:
            score = quality_score(path, blur_val)
            photo_scores[path] = score
            sharp_photos.append(path)

    print(f"\n  Blurry (auto-rejected): {len(blurry_photos)}")
    print(f"  Sharp photos to sort:   {len(sharp_photos)}\n")

    # ── Step 3: Visual location grouping via Claude Haiku ─────────────────────
    print("Step 3/4  Identifying locations visually using Claude Haiku...")
    print(f"  (Analyzing {len(sharp_photos)} photos — results cached so re-runs are free)\n")

    def geo_progress(current, total_photos, label):
        progress(current, total_photos, label)

    location_groups = build_location_groups(
        photo_paths=sharp_photos,
        cache_path=cache_path,
        api_key=api_key,
        progress_callback=geo_progress,
    )

    print(f"\n  Found {len(location_groups)} location group(s)\n")

    # ── Step 4: Select top % and copy files ───────────────────────────────────
    print("Step 4/4  Selecting top photos and copying to output folders...")

    organized_count = 0
    rejected_count  = 0

    # Copy blurry → rejected/Blurry
    for path in blurry_photos:
        copy_file(path, os.path.join(output_folder, REJECTED_FOLDER, "Blurry"))
        rejected_count += 1

    # Per-location selection
    all_ops = sum(len(p) for p in location_groups.values())
    done = 0

    for location, paths in location_groups.items():
        paths_sorted = sorted(paths, key=lambda p: photo_scores.get(p, 0), reverse=True)
        keep_count   = max(1, math.ceil(len(paths_sorted) * top_percent))
        keep_count   = min(keep_count, len(paths_sorted))

        for i, path in enumerate(paths_sorted):
            if i < keep_count:
                copy_file(path, os.path.join(output_folder, ORGANIZED_FOLDER))
                organized_count += 1
            else:
                copy_file(path, os.path.join(output_folder, REJECTED_FOLDER, location))
                rejected_count += 1
            done += 1
            progress(done, all_ops, os.path.basename(path))

    print(f"\n\n Done!\n")
    print(f"  Kept (organized):  {organized_count}  →  output/{ORGANIZED_FOLDER}/")
    print(f"  Rejected:          {rejected_count}  →  output/{REJECTED_FOLDER}/")
    print(f"    Blurry:          {len(blurry_photos)}")
    print(f"    Lower quality:   {rejected_count - len(blurry_photos)}")
    print(f"\n  Your originals were NOT moved or deleted.\n")

    print("  Location breakdown:")
    for location, paths in sorted(location_groups.items(), key=lambda x: -len(x[1])):
        kept = max(1, math.ceil(len(paths) * top_percent))
        kept = min(kept, len(paths))
        print(f"    {location:<40}  kept {kept:>3} of {len(paths)}")


if __name__ == "__main__":
    main()
