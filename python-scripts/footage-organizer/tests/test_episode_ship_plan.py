# tests/test_episode_ship_plan.py
import os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cli_index as cli

def _touch(p): p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b"x")

def test_footage_to_library_and_project_archived(tmp_path):
    lib = tmp_path / "Sai"
    epf = lib / "01_ORGANIZED" / "ep2 doc"
    for n in ("A.MP4", "B.MP4", "V.MP4"):
        _touch(epf / "2026-05-26" / n)
    proj = lib / "02_ACTIVE_PROJECTS" / "longform" / "W07_May-25-31" / "ep2 doc"
    _touch(proj / "edit.prproj")
    orient = lambda p: ("vertical", True) if p.name == "V.MP4" else ("horizontal", False)
    week = lambda p: "W07_May-25-31"
    moves, warnings = cli._episode_ship_plan(lib, "ep2 doc", orient_fn=orient, week_fn=week)
    dests = {s.name: d.as_posix() for s, d in moves}
    assert "05_FOOTAGE_LIBRARY/b-roll/W07_May-25-31/A.MP4" in dests["A.MP4"]
    assert "05_FOOTAGE_LIBRARY/b-roll/W07_May-25-31/B.MP4" in dests["B.MP4"]
    assert "05_FOOTAGE_LIBRARY/vertical/W07_May-25-31/V.MP4" in dests["V.MP4"]
    assert any(s.name == "ep2 doc" and "04_ARCHIVE/longform/" in d.as_posix()
               for s, d in moves)
    assert warnings == []

def test_custom_footage_root(tmp_path):
    lib = tmp_path / "Sai"
    custom = lib / "01_ORGANIZED" / "my-doc-week"
    _touch(custom / "A.MP4")
    moves, warnings = cli._episode_ship_plan(
        lib, "Ep", footage_root=custom,
        orient_fn=lambda p: ("horizontal", False), week_fn=lambda p: "W07")
    assert moves[0][1].as_posix().endswith("05_FOOTAGE_LIBRARY/b-roll/W07/A.MP4")

def test_missing_footage_warns_not_crashes(tmp_path):
    lib = tmp_path / "Sai"
    proj = lib / "02_ACTIVE_PROJECTS" / "longform" / "W07" / "Ep"
    _touch(proj / "edit.prproj")
    moves, warnings = cli._episode_ship_plan(
        lib, "Ep", orient_fn=lambda p: ("horizontal", False), week_fn=lambda p: "W07")
    assert any("no footage" in w.lower() for w in warnings)

def test_no_project_warns(tmp_path):
    lib = tmp_path / "Sai"
    _touch(lib / "01_ORGANIZED" / "Ep" / "2026-05-26" / "A.MP4")
    moves, warnings = cli._episode_ship_plan(
        lib, "Ep", orient_fn=lambda p: ("horizontal", False), week_fn=lambda p: "W07")
    assert any("no active project" in w.lower() for w in warnings)
    assert any(s.name == "A.MP4" for s, d in moves)  # footage still planned
