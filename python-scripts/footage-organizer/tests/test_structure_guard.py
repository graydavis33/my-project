"""Structure guard — detect + auto-repair a canonical top-level folder that got
moved INSIDE another (e.g. 05_FOOTAGE_LIBRARY/01_ORGANIZED)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cli_index as cli


def _mk(p):
    p.mkdir(parents=True, exist_ok=True)


def test_find_misnested_detects_nested_canonical(tmp_path):
    lib = tmp_path / "Sai"
    _mk(lib / "05_FOOTAGE_LIBRARY" / "01_ORGANIZED" / "2026-06-10")
    found = cli._find_misnested(lib)
    names = [n.name for n, _ in found]
    assert "01_ORGANIZED" in names


def test_find_misnested_clean_when_proper(tmp_path):
    lib = tmp_path / "Sai"
    for d in ("00_TEMPLATES", "01_ORGANIZED", "05_FOOTAGE_LIBRARY"):
        _mk(lib / d)
    _mk(lib / "05_FOOTAGE_LIBRARY" / "b-roll")  # freeform child, NOT canonical
    assert cli._find_misnested(lib) == []


def test_repair_moves_back_when_target_clear(tmp_path):
    lib = tmp_path / "Sai"
    _mk(lib / "05_FOOTAGE_LIBRARY" / "01_ORGANIZED" / "day")
    (lib / "05_FOOTAGE_LIBRARY" / "01_ORGANIZED" / "day" / "c.mp4").write_bytes(b"x")
    repaired, warnings = cli._repair_structure(lib)
    assert repaired == ["01_ORGANIZED"]
    assert warnings == []
    assert (lib / "01_ORGANIZED" / "day" / "c.mp4").exists()
    assert not (lib / "05_FOOTAGE_LIBRARY" / "01_ORGANIZED").exists()


def test_repair_warns_when_target_exists(tmp_path):
    lib = tmp_path / "Sai"
    _mk(lib / "05_FOOTAGE_LIBRARY" / "01_ORGANIZED")
    _mk(lib / "01_ORGANIZED")  # top-level already there → cannot auto-move
    repaired, warnings = cli._repair_structure(lib)
    assert repaired == []
    assert warnings and "already exists" in warnings[0]
    assert (lib / "05_FOOTAGE_LIBRARY" / "01_ORGANIZED").exists()  # left untouched
