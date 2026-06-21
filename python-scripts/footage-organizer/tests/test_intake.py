"""v4 intake — route a new dump into b-roll/<week>/ (horizontal) or vertical/<week>/
(vertical) by orientation + filmed date. Orientation and week are stubbed (no ffprobe).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cli_index
from config import FOLDER_FOOTAGE_LIB, FOLDER_BROLL, FOLDER_VERTICAL


def _mk(p: Path, body=b"x"):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(body)
    return p


def test_routes_by_orientation_into_week_folders(tmp_path):
    src = tmp_path / "_INBOX" / "2026-05-12"
    _mk(src / "H1.MP4")   # horizontal
    _mk(src / "V1.MP4")   # vertical
    orient = {"H1.MP4": ("horizontal", False), "V1.MP4": ("vertical", True)}
    fn = lambda p: orient[Path(p).name]
    wk = lambda p: "W05_May-11-17"

    moves, counts, by_week, unknown, coll = cli_index._intake_plan(
        src, tmp_path, "W05_May-11-17", orient_fn=fn, week_fn=wk)

    dests = {dest.relative_to(tmp_path).as_posix() for _s, dest in moves}
    assert f"{FOLDER_FOOTAGE_LIB}/{FOLDER_BROLL}/W05_May-11-17/H1.MP4" in dests
    assert f"{FOLDER_FOOTAGE_LIB}/{FOLDER_VERTICAL}/W05_May-11-17/V1.MP4" in dests
    assert counts == {"horizontal": 1, "vertical": 1}
    assert unknown == [] and coll == []


def test_week_from_filmed_date_per_clip(tmp_path):
    src = tmp_path / "card"
    _mk(src / "A.MP4")
    _mk(src / "B.MP4")
    weeks = {"A.MP4": "W01_Apr-15-19", "B.MP4": "W05_May-11-17"}
    moves, _c, by_week, _u, _co = cli_index._intake_plan(
        src, tmp_path, "W10_Jun-15-21",
        orient_fn=lambda p: ("horizontal", False),
        week_fn=lambda p: weeks[Path(p).name])

    dests = {dest.relative_to(tmp_path).as_posix() for _s, dest in moves}
    assert f"{FOLDER_FOOTAGE_LIB}/{FOLDER_BROLL}/W01_Apr-15-19/A.MP4" in dests
    assert f"{FOLDER_FOOTAGE_LIB}/{FOLDER_BROLL}/W05_May-11-17/B.MP4" in dests
    assert set(by_week) == {"W01_Apr-15-19", "W05_May-11-17"}


def test_falls_back_to_default_week(tmp_path):
    src = tmp_path / "card"
    _mk(src / "A.MP4")
    moves, _c, _bw, _u, _co = cli_index._intake_plan(
        src, tmp_path, "W10_Jun-15-21",
        orient_fn=lambda p: ("horizontal", False),
        week_fn=lambda p: None)  # no readable filmed date
    dest = moves[0][1].relative_to(tmp_path).as_posix()
    assert dest == f"{FOLDER_FOOTAGE_LIB}/{FOLDER_BROLL}/W10_Jun-15-21/A.MP4"


def test_unknown_orientation_left_in_source(tmp_path):
    src = tmp_path / "card"
    _mk(src / "weird.MP4")
    moves, counts, _bw, unknown, _co = cli_index._intake_plan(
        src, tmp_path, "W10_Jun-15-21",
        orient_fn=lambda p: ("unknown", False), week_fn=lambda p: "W10_Jun-15-21")
    assert moves == []
    assert counts == {"horizontal": 0, "vertical": 0}
    assert unknown == ["weird.MP4"]


def test_sidecars_follow_clip(tmp_path):
    src = tmp_path / "card"
    _mk(src / "C4.MP4")
    _mk(src / "C4M01.XML")
    _mk(src / "C40.MP4")
    orient = {"C4.MP4": ("horizontal", False), "C40.MP4": ("vertical", False)}
    moves, _c, _bw, _u, _co = cli_index._intake_plan(
        src, tmp_path, "W05_May-11-17",
        orient_fn=lambda p: orient[Path(p).name], week_fn=lambda p: "W05_May-11-17")
    names = {dest.relative_to(tmp_path).as_posix() for _s, dest in moves}
    assert f"{FOLDER_FOOTAGE_LIB}/{FOLDER_BROLL}/W05_May-11-17/C4.MP4" in names
    assert f"{FOLDER_FOOTAGE_LIB}/{FOLDER_BROLL}/W05_May-11-17/C4M01.XML" in names   # sidecar with C4
    assert f"{FOLDER_FOOTAGE_LIB}/{FOLDER_VERTICAL}/W05_May-11-17/C40.MP4" in names  # separate clip, vertical
