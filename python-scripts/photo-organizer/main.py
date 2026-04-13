"""
Photo Organizer — One-Time Use Script
--------------------------------------
Groups ~1,800 photos by GPS location, removes blurry ones,
keeps the top 20% per location, and sorts them into two output folders:

  output/organized/[Location Name]/   ← your best photos
  output/rejected/[Location Name]/    ← everything else (just in case)

Usage:
  python main.py /path/to/your/photos
  python main.py /path/to/your/photos --output ~/Desktop/sorted-photos
  python main.py /path/to/your/photos --top 30   (keep top 30% instead of 20%)

No API keys needed. Runs entirely on your computer.
"""

import argparse
import math
import os
import shutil
import sys

from config import (
    PHOTO_EXTENSIONS, BLUR_THRESHOLD, TOP_PERCENT,
    ORGANIZED_FOLDER, REJECTED_FOLDER, GEOCODE_CACHE_FILE,
)
from extractor import find_photos, get_gps_coords
from scorer import is_blurry, quality_score
from locator import build_location_groups


# ── Helpers ───────────────────────────────────────────────────────────────────

def progress(current: int, total: int, label: str = ""):
    bar_len = 40
    filled = int(bar_len * current / total)
    bar = "█" * filled + "░" * (bar_len - filled)
    pct = current / total * 100
    print(f"\r  [{bar}] {pct:5.1f}%  {label[:50]:<50}", end="", flush=True)
    if current == total:
        print()


def copy_file(src: str, dest_folder: str):
    os.makedirs(dest_folder, exist_ok=True)
    dest = os.path.join(dest_folder, os.path.basename(src))
    # Avoid overwriting if two photos have the same filename
    if os.path.exists(dest):
        base, ext = os.path.splitext(os.path.basename(src))
        i = 1
        while os.path.exists(dest):
            dest = os.path.join(dest_folder, f"{base}_{i}{ext}")
            i += 1
    shutil.copy2(src, dest)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Organize photos by location, keep top 20%.")
    parser.add_argument("input_folder", help="Folder containing your photos")
    parser.add_argument("--output", "-o", default=None,
                        help="Where to save results (default: input_folder/output/)")
    parser.add_argument("--top", type=float, default=None,
                        help="Percent to keep per location, e.g. 30 = top 30%% (default: 20)")
    args = parser.parse_args()

    input_folder = os.path.expanduser(args.input_folder)
    if not os.path.isdir(input_folder):
        print(f"ERROR: Folder not found: {input_folder}")
        sys.exit(1)

    output_folder = args.output or os.path.join(input_folder, "output")
    output_folder = os.path.expanduser(output_folder)

    top_percent = (args.top / 100.0) if args.top else TOP_PERCENT
    cache_path  = os.path.join(output_folder, GEOCODE_CACHE_FILE)
    os.makedirs(output_folder, exist_ok=True)

    print(f"\n Photo Organizer")
    print(f"  Input:   {input_folder}")
    print(f"  Output:  {output_folder}")
    print(f"  Keeping: top {int(top_percent * 100)}% per location\n")

    # ── Step 1: Find all photos ───────────────────────────────────────────────
    print("Step 1/4  Scanning for photos...")
    all_photos = find_photos(input_folder, PHOTO_EXTENSIONS)

    # Exclude anything already inside the output folder
    all_photos = [p for p in all_photos if not p.startswith(output_folder)]

    total = len(all_photos)
    print(f"  Found {total} photos\n")
    if total == 0:
        print("No photos found. Check the folder path and try again.")
        sys.exit(0)

    # ── Step 2: Blur detection + quality scoring ──────────────────────────────
    print("Step 2/4  Checking quality (blur, exposure, contrast)...")
    photo_scores:  dict[str, float] = {}   # path → quality score (non-blurry only)
    blurry_photos: list[str]        = []
    gps_map:       dict[str, tuple] = {}   # path → (lat, lon)
    no_gps:        list[str]        = []

    for i, path in enumerate(all_photos):
        progress(i + 1, total, os.path.basename(path))

        blurry, blur_val = is_blurry(path)
        if blurry:
            blurry_photos.append(path)
            continue

        score = quality_score(path, blur_val)
        photo_scores[path] = score

        coords = get_gps_coords(path)
        if coords:
            gps_map[path] = coords
        else:
            no_gps.append(path)

    sharp_count = len(photo_scores)
    print(f"\n  Blurry (rejected automatically): {len(blurry_photos)}")
    print(f"  Sharp photos to evaluate:         {sharp_count}\n")

    # ── Step 3: Group by location ─────────────────────────────────────────────
    print("Step 3/4  Grouping by location (may take a few minutes for geocoding)...")

    def geo_progress(current, total_clusters, label):
        progress(current, total_clusters, label)

    location_groups = build_location_groups(
        photo_coords={p: c for p, c in gps_map.items() if p in photo_scores},
        no_gps_photos=[p for p in no_gps if p in photo_scores],
        cache_path=cache_path,
        progress_callback=geo_progress,
    )

    print(f"\n  Found {len(location_groups)} location group(s)\n")

    # ── Step 4: Select top % per location and copy files ─────────────────────
    print("Step 4/4  Selecting top photos and copying to output folders...")

    organized_count = 0
    rejected_count  = 0

    # Copy blurry photos to rejected
    for path in blurry_photos:
        dest = os.path.join(output_folder, REJECTED_FOLDER, "Blurry")
        copy_file(path, dest)
        rejected_count += 1

    # Process each location group
    for location, paths in location_groups.items():
        # Sort by quality score, best first
        paths_sorted = sorted(paths, key=lambda p: photo_scores.get(p, 0), reverse=True)

        # How many to keep: top X% of ALL photos at this location (including ones
        # already removed as blurry), but at least 1 if there's anything left
        keep_count = max(1, math.ceil(len(paths_sorted) * top_percent))
        # Make sure we don't keep more than we have
        keep_count = min(keep_count, len(paths_sorted))

        for i, path in enumerate(paths_sorted):
            if i < keep_count:
                dest = os.path.join(output_folder, ORGANIZED_FOLDER, location)
                organized_count += 1
            else:
                dest = os.path.join(output_folder, REJECTED_FOLDER, location)
                rejected_count += 1
            copy_file(path, dest)
            progress(organized_count + rejected_count - len(blurry_photos),
                     sharp_count, os.path.basename(path))

    print(f"\n\n Done!\n")
    print(f"  Kept (organized):  {organized_count} photos  →  {output_folder}/{ORGANIZED_FOLDER}/")
    print(f"  Rejected:          {rejected_count} photos  →  {output_folder}/{REJECTED_FOLDER}/")
    print(f"    ↳ Blurry:        {len(blurry_photos)}")
    print(f"    ↳ Lower quality: {rejected_count - len(blurry_photos)}")
    print(f"\n  Your originals were NOT moved or deleted. Everything is a copy.\n")

    # ── Print location breakdown ──────────────────────────────────────────────
    print("  Location breakdown:")
    for location, paths in sorted(location_groups.items(), key=lambda x: -len(x[1])):
        total_loc  = len(paths)
        kept       = max(1, math.ceil(total_loc * top_percent))
        kept       = min(kept, total_loc)
        print(f"    {location:<40}  kept {kept:>4} of {total_loc}")


if __name__ == "__main__":
    main()
