"""
One-time migration: project folders adopt W##_MMM-DD-DD weekly buckets.

Rules:
  - Range folders ("Apr 20 – Apr 26") with content → rename to W## form
  - Range folders empty → delete
  - All Adobe Premiere cache subdirs → delete (regenerable)
  - macOS ._* junk → delete
  - Active loose files (top level) → archive/<format>/W##_*/  (per Gray: all published)
  - Delivered loose files (top level) → delivered/<format>/W##_*/  (stay in delivered)
  - Active range folders with content → migrate to archive
  - 04_ARCHIVE/2026-04-27-schedule-v6/ → archive/shorts/W03_Apr-27-May-3/
  - Empty legacy archive long-form/, short-form/ buckets → delete

Date parsing for loose top-level files:
  YYYY-MM-DD prefix → MM-DD prefix (assumes 2026) → file mtime
"""
import argparse
import os
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

from config import CLIENT_ROOTS, FOLDER_PROJECTS, FOLDER_DELIVERED, FOLDER_ARCHIVE
from week_utils import week_label_for, PROJECT_START

DATE_PREFIX = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
SHORT_DATE_PREFIX = re.compile(r"^(\d{2})-(\d{2})")
RANGE_FULL = re.compile(
    r"^([A-Z][a-z]{2}) (\d{1,2})\s*[–\-]\s*([A-Z][a-z]{2})? ?(\d{1,2})( (\d{4}))?$"
)
ADOBE_CACHE_DIRS = {
    "Adobe Premiere Pro Audio Previews",
    "Adobe Premiere Pro Auto-Save",
    "Adobe Premiere Pro Video Previews",
}
SHARED_RESOURCE_DIRS = {"Motion Array Assets", "Motion Graphics Template Media"}
FORMAT_BUCKETS = ["episodes", "linkedin", "shorts"]
# Capitalized legacy project folders Gray asked to leave untouched (Q2 Option A)
LEGACY_PROJECT_DIRS = {"Longform", "Shortform", "Paid Ads", "Onboarding"}
MONTH_NUM = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
             "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
ASSUMED_YEAR = 2026


def parse_args():
    p = argparse.ArgumentParser(description="Migrate project folders to W## weekly buckets.")
    p.add_argument("--client", "-c", required=True, choices=list(CLIENT_ROOTS.keys()))
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def date_from_name(name: str) -> date | None:
    m = DATE_PREFIX.match(name)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = SHORT_DATE_PREFIX.match(name)
    if m:
        try:
            return date(ASSUMED_YEAR, int(m.group(1)), int(m.group(2)))
        except ValueError:
            return None
    return None


def date_from_mtime(path: Path) -> date:
    return date.fromtimestamp(path.stat().st_mtime)


def resolve_loose_date(path: Path) -> tuple[date, str]:
    d = date_from_name(path.name)
    if d:
        return d, "name"
    return date_from_mtime(path), "mtime"


def parse_range_start(name: str) -> date | None:
    """Parse 'Apr 20 – Apr 26' → start date (2026-04-20). Trailing year overrides ASSUMED_YEAR."""
    m = RANGE_FULL.match(name)
    if not m:
        return None
    start_mon = m.group(1)
    start_day = int(m.group(2))
    year = int(m.group(6)) if m.group(6) else ASSUMED_YEAR
    if start_mon not in MONTH_NUM:
        return None
    try:
        return date(year, MONTH_NUM[start_mon], start_day)
    except ValueError:
        return None


def merge_dir_into(src: Path, dst: Path):
    """Move children of src into dst (which exists or will be created), then rmdir src.
    For collisions, append _2, _3, ..."""
    dst.mkdir(parents=True, exist_ok=True)
    for child in list(src.iterdir()):
        target = dst / child.name
        if target.exists():
            stem, ext = (child.stem, child.suffix) if child.is_file() else (child.name, "")
            counter = 2
            while (dst / f"{stem}_{counter}{ext}").exists():
                counter += 1
            target = dst / f"{stem}_{counter}{ext}"
        shutil.move(str(child), str(target))
    if not any(src.iterdir()):
        src.rmdir()


def main():
    args = parse_args()
    library = Path(CLIENT_ROOTS.get(args.client, ""))
    if not library.exists():
        print(f"Error: library root for {args.client} not found at {library}")
        sys.exit(1)

    active   = library / FOLDER_PROJECTS
    delivered = library / FOLDER_DELIVERED
    archive  = library / FOLDER_ARCHIVE
    DRY = args.dry_run

    print(f"\n  {'=' * 64}")
    print(f"  Migrate project folders → W## weekly ({args.client.upper()})")
    print(f"  {'=' * 64}")
    print(f"  Mode:  {'DRY RUN' if DRY else 'EXECUTE'}\n")

    actions = []

    def plan(kind, src, dst, reason):
        actions.append((kind, src, dst, reason))

    def in_legacy_folder(path: Path) -> bool:
        """True if path is inside a capitalized legacy project folder we leave alone."""
        for part in path.parts:
            if part in LEGACY_PROJECT_DIRS:
                return True
        return False

    # ── 1. Adobe cache: delete everywhere under active/delivered/archive ────
    #    EXCEPT inside capitalized legacy project folders (Gray's Q2 Option A)
    for top in (active, delivered, archive):
        for cache_dir in top.rglob("*"):
            if cache_dir.is_dir() and cache_dir.name in ADOBE_CACHE_DIRS:
                if in_legacy_folder(cache_dir):
                    continue
                plan("DEL", cache_dir, None, "Adobe regenerable cache")

    # ── 2. macOS junk ───────────────────────────────────────────────────────
    for top in (active, delivered, archive):
        for junk in top.rglob("._*"):
            if in_legacy_folder(junk):
                continue
            plan("DEL", junk, None, "macOS junk")

    # ── 3. Range folders: rename to W## form, with merge ────────────────────
    # active range → archive (Gray: all published)
    # delivered range → delivered (stay)
    # archive range → archive (stay)
    range_targets = [
        (active, archive, "active range → archive"),
        (delivered, delivered, "delivered range → delivered W##"),
        (archive, archive, "archive range → archive W##"),
    ]
    for source_root, dest_root, label in range_targets:
        for fmt_dir in source_root.iterdir() if source_root.is_dir() else []:
            if not fmt_dir.is_dir() or fmt_dir.name not in FORMAT_BUCKETS + ["long-form", "short-form"]:
                continue
            for child in list(fmt_dir.iterdir()):
                if not child.is_dir():
                    continue
                start_d = parse_range_start(child.name)
                if start_d is None:
                    continue
                # Empty range → delete
                # Need to look past Adobe cache + ._junk that we plan to delete
                non_garbage = [
                    c for c in child.iterdir()
                    if c.name not in ADOBE_CACHE_DIRS and not c.name.startswith("._")
                ]
                if not non_garbage:
                    plan("DEL_RECURSIVE", child, None, "empty (post-cache-purge) broken-sort stub")
                    continue
                # Rename / merge to W## form
                if start_d < PROJECT_START:
                    plan("DEL_OR_MANUAL", child, None,
                         f"range starts {start_d} — before project start {PROJECT_START}, decide manually")
                    continue
                target_fmt = "shorts" if fmt_dir.name in ("shorts", "short-form") else \
                             ("episodes" if fmt_dir.name in ("episodes", "long-form") else fmt_dir.name)
                week = week_label_for(start_d)
                dst = dest_root / target_fmt / week
                plan("MERGE_INTO", child, dst, label)

    # ── 4. Active loose top-level → archive (per Gray, all published) ──────
    for fmt in FORMAT_BUCKETS + ["long-form", "short-form"]:
        src_root = active / fmt
        if not src_root.is_dir():
            continue
        # Index .prproj for sidecar matching
        prproj_dates = {}
        for c in src_root.iterdir():
            if c.suffix == ".prproj":
                d = date_from_name(c.name) or date_from_mtime(c)
                prproj_dates[c.stem] = d

        for child in sorted(src_root.iterdir()):
            if child.name.startswith("._") or child.name in ADOBE_CACHE_DIRS:
                continue  # already planned for delete
            if RANGE_FULL.match(child.name) and child.is_dir():
                continue  # handled in step 3
            if child.is_dir() and child.name in SHARED_RESOURCE_DIRS:
                target_fmt = "shorts" if fmt in ("shorts", "short-form") else fmt
                plan("MOVE", child, archive / target_fmt / "_shared" / child.name, "shared paid resource")
                continue

            d = None
            reason = ""
            for stem, sd in prproj_dates.items():
                if child.name != stem + ".prproj" and (
                    child.stem.startswith(stem) or child.name.startswith(stem)
                ):
                    d = sd
                    reason = f"sidecar of {stem}.prproj"
                    break
            if d is None:
                d, src = resolve_loose_date(child)
                reason = f"date from {src}"

            if d < PROJECT_START:
                plan("DEL_OR_MANUAL", child, None,
                     f"date {d} before project start; decide manually")
                continue
            week = week_label_for(d)
            target_fmt = "shorts" if fmt in ("shorts", "short-form") else \
                         ("episodes" if fmt in ("episodes", "long-form") else fmt)
            plan("MOVE", child, archive / target_fmt / week / child.name, reason)

    # ── 5. Delivered loose top-level → delivered/<fmt>/W##/ ─────────────────
    for fmt in FORMAT_BUCKETS:
        src_root = delivered / fmt
        if not src_root.is_dir():
            continue
        for child in sorted(src_root.iterdir()):
            if child.name.startswith("._") or child.name in ADOBE_CACHE_DIRS:
                continue
            if RANGE_FULL.match(child.name) and child.is_dir():
                continue
            if child.is_dir() and child.name.startswith("W") and "_" in child.name:
                continue  # already W## form
            d, src = resolve_loose_date(child)
            if d < PROJECT_START:
                plan("DEL_OR_MANUAL", child, None,
                     f"date {d} before project start; decide manually")
                continue
            week = week_label_for(d)
            plan("MOVE", child, src_root / week / child.name, f"date from {src}")

    # ── 6. Archive: legacy 2026-04-27-schedule-v6/ → shorts/W03 ─────────────
    legacy = archive / "2026-04-27-schedule-v6"
    if legacy.is_dir():
        plan("MOVE", legacy, archive / "shorts" / week_label_for(date(2026, 4, 27)) / "2026-04-27-schedule-v6",
             "previously-relocated Premiere project")

    # ── 7. Archive: delete empty legacy lowercase format buckets ────────────
    for legacy_fmt in ("long-form", "short-form"):
        legacy_dir = archive / legacy_fmt
        if legacy_dir.is_dir():
            plan("DEL_IF_EMPTY", legacy_dir, None, "legacy empty format bucket")

    # ── Deduplicate (rglob can find Adobe cache as both top-level and nested) ──
    seen = set()
    deduped = []
    for kind, src, dst, reason in actions:
        key = (kind, str(src), str(dst) if dst else None)
        if key in seen:
            continue
        seen.add(key)
        deduped.append((kind, src, dst, reason))
    actions = deduped

    # ── Print plan ───────────────────────────────────────────────────────────
    n_move = sum(1 for a in actions if a[0] in ("MOVE", "MERGE_INTO"))
    n_del = sum(1 for a in actions if a[0].startswith("DEL"))
    print(f"  Planned MOVE/MERGE: {n_move}")
    print(f"  Planned DELETE/SKIP: {n_del}\n")

    for kind, src, dst, reason in actions:
        rel_src = src.relative_to(library)
        if dst is not None:
            rel_dst = dst.relative_to(library)
            print(f"  {kind:14}  {rel_src}")
            print(f"  {' ':14}  → {rel_dst}  ({reason})")
        else:
            print(f"  {kind:14}  {rel_src}  ({reason})")

    if DRY:
        print(f"\n  DRY RUN complete. Re-run without --dry-run to execute.\n")
        return

    # ── Execute ──────────────────────────────────────────────────────────────
    moved = deleted = manual = 0
    for kind, src, dst, reason in actions:
        try:
            if kind == "MOVE":
                if not src.exists():
                    continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    print(f"  SKIP  destination exists: {dst}")
                    continue
                shutil.move(str(src), str(dst))
                moved += 1
            elif kind == "MERGE_INTO":
                if not src.exists():
                    continue
                merge_dir_into(src, dst)
                moved += 1
            elif kind == "DEL":
                if not src.exists():
                    continue
                if src.is_dir():
                    shutil.rmtree(src)
                else:
                    src.unlink()
                deleted += 1
            elif kind == "DEL_RECURSIVE":
                if src.exists():
                    shutil.rmtree(src)
                    deleted += 1
            elif kind == "DEL_IF_EMPTY":
                if src.is_dir() and not any(src.iterdir()):
                    src.rmdir()
                    deleted += 1
            elif kind == "DEL_OR_MANUAL":
                manual += 1
                print(f"  MANUAL  {src.relative_to(library)} ({reason})")
        except Exception as e:
            print(f"  ERROR on {kind} {src}: {e}")

    # Ensure new format buckets exist in archive
    for fmt in FORMAT_BUCKETS:
        (archive / fmt).mkdir(exist_ok=True)

    print(f"\n  Done. Moved/merged {moved}, deleted {deleted}, left for manual review {manual}.\n")


if __name__ == "__main__":
    main()
