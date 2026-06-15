from datetime import date

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli_index import ensure_week
from config import CATEGORIES

# 17 footage-library categories + (ACTIVE/DELIVERED/ARCHIVE) × 3 format buckets
WEEK_FOLDER_COUNT = len(CATEGORIES) + 9


def test_ensure_week_creates_full_week_scaffold(tmp_path):
    created, skipped = ensure_week(tmp_path, date(2026, 4, 21))  # W02
    assert created == WEEK_FOLDER_COUNT
    assert skipped == 0
    assert (tmp_path / "05_FOOTAGE_LIBRARY" / "interview-solo" / "W02_Apr-20-26").is_dir()
    assert (tmp_path / "02_ACTIVE_PROJECTS" / "shorts" / "W02_Apr-20-26").is_dir()
    assert (tmp_path / "04_ARCHIVE" / "episodes" / "W02_Apr-20-26").is_dir()


def test_ensure_week_is_idempotent(tmp_path):
    ensure_week(tmp_path, date(2026, 4, 21))
    created, skipped = ensure_week(tmp_path, date(2026, 4, 21))
    assert created == 0
    assert skipped == WEEK_FOLDER_COUNT


def test_ensure_week_includes_freeform_folders(tmp_path):
    # Gray made his own library folder; it should get a weekly subfolder too
    (tmp_path / "05_FOOTAGE_LIBRARY" / "nyc-street").mkdir(parents=True)
    ensure_week(tmp_path, date(2026, 4, 21))  # W02
    assert (tmp_path / "05_FOOTAGE_LIBRARY" / "nyc-street" / "W02_Apr-20-26").is_dir()


def test_ensure_week_skips_underscore_helper_folders(tmp_path):
    # _TO_SORT is a holding folder, not a category — no weekly subfolder
    (tmp_path / "05_FOOTAGE_LIBRARY" / "_TO_SORT").mkdir(parents=True)
    ensure_week(tmp_path, date(2026, 4, 21))
    assert not (tmp_path / "05_FOOTAGE_LIBRARY" / "_TO_SORT" / "W02_Apr-20-26").exists()
