"""
One-time migration script — April 2026 restructure:
  1. Flatten Footage Library: remove unused/used split, move clips up to category level
  2. Rename 03_PROJECTS → 03_ACTIVE_PROJECTS
  3. Add 52 weeks of placeholder folders (Apr 16 2026 start) to:
       - 06_FOOTAGE_LIBRARY/{category}/
       - 04_DELIVERED/shorts|linkedin|episodes/
       - 05_ARCHIVE/long-form|short-form/
       - 03_ACTIVE_PROJECTS/shorts|linkedin|episodes/
"""

import os
import shutil
from datetime import date, timedelta

LIBRARY = "/Volumes/Footage/Sai"

CATEGORIES = [
    "interview-solo", "interview-duo", "walk-and-talk",
    "candid-people", "reaction-listening", "crowd-group",
    "insert-hands", "insert-product", "insert-food-drink", "insert-detail",
    "screens-and-text",
    "establishing-exterior", "establishing-interior", "environment-detail",
    "action-sport-fitness", "transit-vehicles",
    "misc",
]


def week_label(start: date, end: date) -> str:
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    s = f"{months[start.month - 1]} {start.day}"
    e = f"{months[end.month - 1]} {end.day}"
    if end.year != 2026:
        e += f" {end.year}"
    return f"{s} – {e}"


def build_weeks(num_weeks=52):
    weeks = []
    # Week 1: Apr 16 (Thu) – Apr 19 (Sat)
    w1_start = date(2026, 4, 16)
    w1_end = date(2026, 4, 19)
    weeks.append(week_label(w1_start, w1_end))
    # Remaining weeks: Sun–Sat
    sunday = date(2026, 4, 20)
    for _ in range(num_weeks - 1):
        saturday = sunday + timedelta(days=6)
        weeks.append(week_label(sunday, saturday))
        sunday += timedelta(days=7)
    return weeks


def makedirs(path):
    os.makedirs(path, exist_ok=True)


def step1_flatten_footage_library():
    print("\n── Step 1: Flatten Footage Library ──")
    footage_lib = os.path.join(LIBRARY, "06_FOOTAGE_LIBRARY")
    unused_root = os.path.join(footage_lib, "unused")
    used_root = os.path.join(footage_lib, "used")

    # Move clips from unused/{category}/{date}/ → {category}/{date}/
    if os.path.isdir(unused_root):
        for category in os.listdir(unused_root):
            cat_src = os.path.join(unused_root, category)
            if not os.path.isdir(cat_src):
                continue
            cat_dst = os.path.join(footage_lib, category)
            makedirs(cat_dst)
            for date_folder in os.listdir(cat_src):
                date_src = os.path.join(cat_src, date_folder)
                date_dst = os.path.join(cat_dst, date_folder)
                if os.path.isdir(date_src):
                    if os.path.exists(date_dst):
                        # Merge — move individual files
                        for f in os.listdir(date_src):
                            shutil.move(os.path.join(date_src, f), os.path.join(date_dst, f))
                        os.rmdir(date_src)
                    else:
                        shutil.move(date_src, date_dst)
                    print(f"  Moved {category}/{date_folder}/")
        shutil.rmtree(unused_root)
        print(f"  Deleted unused/")

    # used/ folders are all empty — just delete
    if os.path.isdir(used_root):
        shutil.rmtree(used_root)
        print(f"  Deleted used/")


def step2_rename_projects():
    print("\n── Step 2: Rename 03_PROJECTS → 03_ACTIVE_PROJECTS ──")
    src = os.path.join(LIBRARY, "03_PROJECTS")
    dst = os.path.join(LIBRARY, "03_ACTIVE_PROJECTS")
    if os.path.isdir(src) and not os.path.exists(dst):
        os.rename(src, dst)
        print(f"  Renamed 03_PROJECTS → 03_ACTIVE_PROJECTS")
    elif os.path.isdir(dst):
        print(f"  Already renamed, skipping")
    else:
        print(f"  03_PROJECTS not found, skipping")


def step3_create_week_folders(weeks):
    print("\n── Step 3: Create week placeholder folders ──")

    footage_lib = os.path.join(LIBRARY, "06_FOOTAGE_LIBRARY")
    delivered = os.path.join(LIBRARY, "04_DELIVERED")
    archive = os.path.join(LIBRARY, "05_ARCHIVE")
    projects = os.path.join(LIBRARY, "03_ACTIVE_PROJECTS")

    # Footage Library — week folders inside each category
    for cat in CATEGORIES:
        for week in weeks:
            makedirs(os.path.join(footage_lib, cat, week))
    print(f"  Footage Library: {len(CATEGORIES)} categories × {len(weeks)} weeks")

    # Delivered — week folders inside shorts/linkedin/episodes
    for fmt in ["shorts", "linkedin", "episodes"]:
        for week in weeks:
            makedirs(os.path.join(delivered, fmt, week))
    print(f"  Delivered: 3 formats × {len(weeks)} weeks")

    # Archive — new long-form/short-form with week folders (old folders untouched)
    for fmt in ["long-form", "short-form"]:
        for week in weeks:
            makedirs(os.path.join(archive, fmt, week))
    print(f"  Archive: long-form + short-form × {len(weeks)} weeks")

    # Active Projects — week folders inside shorts/linkedin/episodes
    for fmt in ["shorts", "linkedin", "episodes"]:
        for week in weeks:
            makedirs(os.path.join(projects, fmt, week))
    print(f"  Active Projects: 3 formats × {len(weeks)} weeks")


if __name__ == "__main__":
    weeks = build_weeks(52)
    print(f"Weeks: {weeks[0]}  →  {weeks[-1]}  ({len(weeks)} total)\n")

    step1_flatten_footage_library()
    step2_rename_projects()
    step3_create_week_folders(weeks)

    print("\n✓ Migration complete.")
