"""Tests for the v3 Phase 4 `promote` command — move a finished project between
stages (ACTIVE → DELIVERED → ARCHIVE). Pure file ops, no ffprobe/index."""
from datetime import date
from pathlib import Path

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli_index import (
    _find_stage_item, _infer_format, _promote_item, _DEFAULT_FROM,
)
from config import FOLDER_PROJECTS, FOLDER_DELIVERED, FOLDER_ARCHIVE
from week_utils import week_label_for

WEEK = date(2026, 6, 15)          # W10_Jun-15-21
WEEK_LABEL = week_label_for(WEEK)


def _make_project(parent: Path, name: str, files=("final.mp4",)) -> Path:
    proj = parent / name
    proj.mkdir(parents=True, exist_ok=True)
    for f in files:
        (proj / f).write_bytes(b"x")
    return proj


def _make_file(parent: Path, name: str) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    f = parent / name
    f.write_bytes(b"x")
    return f


# ---- _find_stage_item -----------------------------------------------------

def test_find_project_folder(tmp_path):
    root = tmp_path / FOLDER_PROJECTS
    _make_project(root / "shorts", "My Edit")
    found = _find_stage_item(root, "My Edit")
    assert found == [root / "shorts" / "My Edit"]


def test_find_loose_file(tmp_path):
    root = tmp_path / FOLDER_PROJECTS
    _make_file(root / "longform", "Ep 1 Final.mp4")
    found = _find_stage_item(root, "Ep 1 Final.mp4")
    assert found == [root / "longform" / "Ep 1 Final.mp4"]


def test_find_does_not_descend_into_matched_dir(tmp_path):
    root = tmp_path / FOLDER_PROJECTS
    proj = _make_project(root / "shorts", "Proj")
    # a nested file also named "Proj" must NOT be returned (dir was pruned)
    (proj / "Proj").write_bytes(b"x")
    found = _find_stage_item(root, "Proj")
    assert found == [root / "shorts" / "Proj"]


def test_find_ambiguous_returns_all(tmp_path):
    root = tmp_path / FOLDER_PROJECTS
    _make_project(root / "shorts", "Dup")
    _make_project(root / "longform", "Dup")
    assert len(_find_stage_item(root, "Dup")) == 2


# ---- _infer_format --------------------------------------------------------

def test_infer_format_from_bucket(tmp_path):
    root = tmp_path / FOLDER_PROJECTS
    p = root / "shorts" / "X"
    assert _infer_format(p, root) == "shorts"


def test_infer_format_none_outside_bucket(tmp_path):
    root = tmp_path / FOLDER_PROJECTS
    p = root / "affirmations" / "C1.MP4"   # legacy named folder, not a format bucket
    assert _infer_format(p, root) is None


# ---- _promote_item --------------------------------------------------------

def test_promote_active_to_delivered_infers_format(tmp_path):
    _make_project(tmp_path / FOLDER_PROJECTS / "shorts", "My Edit")
    result = _promote_item(tmp_path, "My Edit", "active", "delivered", None, WEEK)
    dest = tmp_path / FOLDER_DELIVERED / "shorts" / WEEK_LABEL / "My Edit"
    assert dest.is_dir()
    assert (dest / "final.mp4").exists()
    # original is gone (moved, not copied)
    assert not (tmp_path / FOLDER_PROJECTS / "shorts" / "My Edit").exists()
    assert result["format"] == "shorts"


def test_promote_delivered_to_archive(tmp_path):
    _make_project(tmp_path / FOLDER_DELIVERED / "longform", "Old Ep")
    _promote_item(tmp_path, "Old Ep", "delivered", "archive", None, WEEK)
    assert (tmp_path / FOLDER_ARCHIVE / "longform" / WEEK_LABEL / "Old Ep").is_dir()


def test_promote_no_week_places_loose(tmp_path):
    _make_file(tmp_path / FOLDER_PROJECTS / "shorts", "clip.mp4")
    _promote_item(tmp_path, "clip.mp4", "active", "delivered", None, None)
    assert (tmp_path / FOLDER_DELIVERED / "shorts" / "clip.mp4").exists()


def test_promote_explicit_format_for_legacy_folder(tmp_path):
    # item lives outside a format bucket → format can't be inferred → caller passes it
    _make_project(tmp_path / FOLDER_PROJECTS, "affirmations")
    _promote_item(tmp_path, "affirmations", "active", "delivered", "shorts", WEEK)
    assert (tmp_path / FOLDER_DELIVERED / "shorts" / WEEK_LABEL / "affirmations").is_dir()


def test_promote_not_found_raises(tmp_path):
    (tmp_path / FOLDER_PROJECTS).mkdir(parents=True)
    try:
        _promote_item(tmp_path, "ghost", "active", "delivered", "shorts", WEEK)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "not found" in str(e)


def test_promote_ambiguous_raises(tmp_path):
    _make_project(tmp_path / FOLDER_PROJECTS / "shorts", "Dup")
    _make_project(tmp_path / FOLDER_PROJECTS / "longform", "Dup")
    try:
        _promote_item(tmp_path, "Dup", "active", "delivered", None, WEEK)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "ambiguous" in str(e)


def test_promote_refuses_overwrite(tmp_path):
    _make_project(tmp_path / FOLDER_PROJECTS / "shorts", "Edit", files=("a.mp4",))
    # a project with the same name already sits in the destination
    _make_project(tmp_path / FOLDER_DELIVERED / "shorts" / WEEK_LABEL, "Edit", files=("b.mp4",))
    try:
        _promote_item(tmp_path, "Edit", "active", "delivered", None, WEEK)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "already exists" in str(e)
    # source untouched — nothing lost
    assert (tmp_path / FOLDER_PROJECTS / "shorts" / "Edit" / "a.mp4").exists()


def test_promote_unknown_format_raises(tmp_path):
    _make_project(tmp_path / FOLDER_PROJECTS, "weirdname")  # no bucket, no --format
    try:
        _promote_item(tmp_path, "weirdname", "active", "delivered", None, WEEK)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "format" in str(e)


def test_promote_same_stage_raises(tmp_path):
    _make_project(tmp_path / FOLDER_DELIVERED / "shorts", "X")
    try:
        _promote_item(tmp_path, "X", "delivered", "delivered", None, WEEK)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "same" in str(e)


def test_default_from_mapping():
    assert _DEFAULT_FROM["delivered"] == "active"
    assert _DEFAULT_FROM["archive"] == "delivered"
