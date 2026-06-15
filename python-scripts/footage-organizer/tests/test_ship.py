"""Tests for the v3.1 `ship` command — post-delivery cleanup: archive the edit
project + file the raw footage into the library, as one reviewed plan. The plan
builder is pure (no moves) so it's fully unit-testable; _execute_ship does the moves."""
from datetime import date
from pathlib import Path

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli_index import _ship_plan, _execute_ship
from config import (
    FOLDER_PROJECTS, FOLDER_DELIVERED, FOLDER_ARCHIVE, FOLDER_ORGANIZED,
    FOLDER_FOOTAGE_LIB,
)
from week_utils import week_label_for

WEEK = date(2026, 6, 15)            # W10_Jun-15-21
WK = week_label_for(WEEK)
VIDEO = "Batch 2 Vid 1 - 10 Truths About Ads"


def _mkfile(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x")
    return p


def _full_setup(tmp):
    """A delivered file + matching active project + batch footage on disk."""
    _mkfile(tmp / FOLDER_DELIVERED / "shorts" / f"{VIDEO}.mp4")
    (tmp / FOLDER_PROJECTS / "shorts" / VIDEO).mkdir(parents=True)
    _mkfile(tmp / FOLDER_PROJECTS / "shorts" / VIDEO / "edit.prproj")
    _mkfile(tmp / FOLDER_ORGANIZED / "Batch_02" / "Vid_01" / "C2493.MP4")


def test_plan_finds_project_and_batch_footage(tmp_path):
    _full_setup(tmp_path)
    moves, warnings = _ship_plan(tmp_path, VIDEO, None, None, None, None, WEEK)
    whats = [m["what"] for m in moves]
    assert "edit project → archive" in whats
    assert "raw footage → library" in whats

    proj = next(m for m in moves if m["what"].startswith("edit project"))
    assert proj["dest"] == tmp_path / FOLDER_ARCHIVE / "shorts" / WK / VIDEO

    foot = next(m for m in moves if m["what"].startswith("raw footage"))
    # footage folder (Vid_01) filed under a library folder named after the video
    assert foot["dest"] == tmp_path / FOLDER_FOOTAGE_LIB / VIDEO / WK / "Vid_01"


def test_batch_vid_parsed_from_video_name(tmp_path):
    # only the footage exists — confirm "Batch 2 Vid 1 …" maps to Batch_02/Vid_01
    _mkfile(tmp_path / FOLDER_ORGANIZED / "Batch_02" / "Vid_01" / "C1.MP4")
    moves, _ = _ship_plan(tmp_path, VIDEO, None, None, None, None, WEEK)
    foot = [m for m in moves if m["what"].startswith("raw footage")]
    assert len(foot) == 1
    assert foot[0]["src"] == tmp_path / FOLDER_ORGANIZED / "Batch_02" / "Vid_01"


def test_explicit_footage_and_category(tmp_path):
    _mkfile(tmp_path / FOLDER_ORGANIZED / "loose-shoot" / "C1.MP4")
    moves, _ = _ship_plan(tmp_path, "Some Video", None,
                          "01_ORGANIZED/loose-shoot", "interviews", None, WEEK)
    foot = [m for m in moves if m["what"].startswith("raw footage")][0]
    assert foot["src"] == tmp_path / FOLDER_ORGANIZED / "loose-shoot"
    assert foot["dest"] == tmp_path / FOLDER_FOOTAGE_LIB / "interviews" / WK / "loose-shoot"


def test_missing_project_warns_and_continues(tmp_path):
    # footage present, no active project → footage-only plan + a warning
    _mkfile(tmp_path / FOLDER_ORGANIZED / "Batch_02" / "Vid_01" / "C1.MP4")
    moves, warnings = _ship_plan(tmp_path, VIDEO, None, None, None, None, WEEK)
    assert [m["what"] for m in moves] == ["raw footage → library"]
    assert any("no active project matched" in w for w in warnings)


def test_missing_footage_warns(tmp_path):
    (tmp_path / FOLDER_PROJECTS / "shorts" / VIDEO).mkdir(parents=True)
    moves, warnings = _ship_plan(tmp_path, VIDEO, None, None, None, None, WEEK)
    assert [m["what"] for m in moves] == ["edit project → archive"]
    assert any("couldn't locate the raw footage" in w for w in warnings)


def test_ambiguous_project_raises(tmp_path):
    (tmp_path / FOLDER_PROJECTS / "shorts" / VIDEO).mkdir(parents=True)
    (tmp_path / FOLDER_PROJECTS / "episodes" / VIDEO).mkdir(parents=True)
    try:
        _ship_plan(tmp_path, VIDEO, None, None, None, None, WEEK)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "ambiguous" in str(e)


def test_refuses_overwrite(tmp_path):
    _full_setup(tmp_path)
    # archive destination already taken
    (tmp_path / FOLDER_ARCHIVE / "shorts" / WK / VIDEO).mkdir(parents=True)
    try:
        _ship_plan(tmp_path, VIDEO, None, None, None, None, WEEK)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "already exists" in str(e)


def test_execute_moves_everything(tmp_path):
    _full_setup(tmp_path)
    moves, _ = _ship_plan(tmp_path, VIDEO, None, None, None, None, WEEK)
    _execute_ship(moves)
    # project archived
    assert (tmp_path / FOLDER_ARCHIVE / "shorts" / WK / VIDEO / "edit.prproj").exists()
    assert not (tmp_path / FOLDER_PROJECTS / "shorts" / VIDEO).exists()
    # footage filed
    assert (tmp_path / FOLDER_FOOTAGE_LIB / VIDEO / WK / "Vid_01" / "C2493.MP4").exists()
    assert not (tmp_path / FOLDER_ORGANIZED / "Batch_02" / "Vid_01").exists()


def test_no_week_places_loose(tmp_path):
    _mkfile(tmp_path / FOLDER_ORGANIZED / "Batch_02" / "Vid_01" / "C1.MP4")
    moves, _ = _ship_plan(tmp_path, VIDEO, None, None, None, None, None)
    foot = [m for m in moves if m["what"].startswith("raw footage")][0]
    assert foot["dest"] == tmp_path / FOLDER_FOOTAGE_LIB / VIDEO / "Vid_01"
