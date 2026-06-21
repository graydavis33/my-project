"""v4 — split-vertical: vertical clips move out of b-roll/ into vertical/<week>/
(weeks preserved), horizontal stays, rotation-flipped clips are flagged for review,
undetermined orientation is left in place. Orientation detection is stubbed (no ffprobe).
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


def _broll(tmp_path):
    return tmp_path / FOLDER_FOOTAGE_LIB / FOLDER_BROLL


def test_vertical_moves_horizontal_stays(tmp_path):
    b = _broll(tmp_path)
    _mk(b / "W05_May-11-17" / "V1.MP4")   # vertical
    _mk(b / "W05_May-11-17" / "H1.MP4")   # horizontal
    orient = {"V1.MP4": ("vertical", False), "H1.MP4": ("horizontal", False)}
    fn = lambda p: orient[Path(p).name]

    moves, counts, flipped, unknown, coll = cli_index._orientation_plan(tmp_path, orient_fn=fn)

    assert counts == {"horizontal": 1, "vertical": 1}
    dest = moves[0][1].relative_to(tmp_path).as_posix()
    assert dest == f"{FOLDER_FOOTAGE_LIB}/{FOLDER_VERTICAL}/W05_May-11-17/V1.MP4"
    assert flipped == [] and unknown == [] and coll == []


def test_rotation_flipped_is_flagged(tmp_path):
    b = _broll(tmp_path)
    _mk(b / "W10_Jun-15-21" / "C9.MP4")  # displays vertical only because of a rotate flag
    fn = lambda p: ("vertical", True)

    moves, counts, flipped, unknown, _c = cli_index._orientation_plan(tmp_path, orient_fn=fn)
    assert counts["vertical"] == 1
    assert flipped == [f"{FOLDER_FOOTAGE_LIB}/{FOLDER_BROLL}/W10_Jun-15-21/C9.MP4"]
    assert len(moves) == 1  # still planned for the move


def test_unknown_orientation_left_in_place(tmp_path):
    b = _broll(tmp_path)
    _mk(b / "W05_May-11-17" / "weird.MP4")
    fn = lambda p: ("unknown", False)

    moves, counts, _f, unknown, _c = cli_index._orientation_plan(tmp_path, orient_fn=fn)
    assert moves == []
    assert counts == {"horizontal": 0, "vertical": 0}
    assert unknown == [f"{FOLDER_FOOTAGE_LIB}/{FOLDER_BROLL}/W05_May-11-17/weird.MP4"]


def test_vertical_sidecars_move_together(tmp_path):
    b = _broll(tmp_path) / "W05_May-11-17"
    _mk(b / "C4.MP4")
    _mk(b / "C4M01.XML")   # sidecar moves with C4
    _mk(b / "C40.MP4")     # different clip — not C4's sidecar
    orient = {"C4.MP4": ("vertical", False), "C40.MP4": ("horizontal", False)}
    fn = lambda p: orient[Path(p).name]

    moves, counts, _f, _u, _c = cli_index._orientation_plan(tmp_path, orient_fn=fn)
    names = sorted(dest.name for _src, dest in moves)
    assert names == ["C4.MP4", "C4M01.XML"]   # C40 stays (horizontal)
    assert counts == {"horizontal": 1, "vertical": 1}


def test_week_preserved_including_unknown_week(tmp_path):
    b = _broll(tmp_path)
    _mk(b / "unknown-week" / "U1.MP4")
    fn = lambda p: ("vertical", False)

    moves, _c, _f, _u, _co = cli_index._orientation_plan(tmp_path, orient_fn=fn)
    dest = moves[0][1].relative_to(tmp_path).as_posix()
    assert dest == f"{FOLDER_FOOTAGE_LIB}/{FOLDER_VERTICAL}/unknown-week/U1.MP4"
