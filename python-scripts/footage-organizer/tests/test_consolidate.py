"""consolidate-broll flattens every category folder into 05_FOOTAGE_LIBRARY/b-roll/<week>/
while preserving each clip's ORIGINAL week. Pure file logic (no ffprobe) is unit-tested:
week-from-path, the move plan (exclusions, sidecars, collisions, unknown-week), and the
collision-safe executor.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cli_index
from config import FOLDER_FOOTAGE_LIB, FOLDER_BROLL


def _mk(p: Path, body=b"x"):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(body)
    return p


def _lib(tmp_path):
    return tmp_path  # library root; FOOTAGE_LIBRARY lives under it


# ── _week_from_path ─────────────────────────────────────────────────────────

def test_week_from_path_reads_week_folder(tmp_path):
    clip = tmp_path / FOLDER_FOOTAGE_LIB / "interview-solo" / "W05_May-11-17" / "C1.MP4"
    assert cli_index._week_from_path(clip, tmp_path) == "W05_May-11-17"


def test_week_from_path_none_when_no_week_folder(tmp_path):
    clip = tmp_path / FOLDER_FOOTAGE_LIB / "old-broll" / "C2.MP4"
    assert cli_index._week_from_path(clip, tmp_path) is None


# ── _plan_consolidation ─────────────────────────────────────────────────────

def test_plan_preserves_original_weeks(tmp_path):
    lib = tmp_path / FOLDER_FOOTAGE_LIB
    _mk(lib / "interview-solo" / "W05_May-11-17" / "C1.MP4")
    _mk(lib / "insert-hands" / "W10_Jun-15-21" / "C2.MP4")

    moves, per_week, unknown, collisions = cli_index._plan_consolidation(tmp_path)

    dests = {dest.relative_to(tmp_path).as_posix() for _src, dest in moves}
    assert f"{FOLDER_FOOTAGE_LIB}/{FOLDER_BROLL}/W05_May-11-17/C1.MP4" in dests
    assert f"{FOLDER_FOOTAGE_LIB}/{FOLDER_BROLL}/W10_Jun-15-21/C2.MP4" in dests
    assert per_week == {"W05_May-11-17": 1, "W10_Jun-15-21": 1}
    assert unknown == [] and collisions == []


def test_plan_excludes_broll_and_underscore_helpers(tmp_path):
    lib = tmp_path / FOLDER_FOOTAGE_LIB
    _mk(lib / FOLDER_BROLL / "W05_May-11-17" / "already.MP4")     # destination — skip
    _mk(lib / "_BATCHES" / "Batch_02" / "Vid_01" / "C9.MP4")     # helper — skip
    _mk(lib / "_TO_SORT" / "loose.MP4")                          # helper — skip
    keep = _mk(lib / "crowd-group" / "W05_May-11-17" / "C3.MP4") # real — move

    moves, per_week, _unknown, _coll = cli_index._plan_consolidation(tmp_path)

    srcs = {src.resolve() for src, _dest in moves}
    assert keep.resolve() in srcs
    assert len(moves) == 1  # only the crowd-group clip


def test_plan_groups_sidecars_with_clip(tmp_path):
    lib = tmp_path / FOLDER_FOOTAGE_LIB
    wk = lib / "interview-duo" / "W05_May-11-17"
    _mk(wk / "C4.MP4")
    _mk(wk / "C4M01.XML")   # sidecar — moves with C4
    _mk(wk / "C40.MP4")     # different clip — must NOT be grabbed as C4's sidecar

    moves, _pw, _u, _c = cli_index._plan_consolidation(tmp_path)
    names = sorted(dest.name for _src, dest in moves)
    assert names == ["C4.MP4", "C40.MP4", "C4M01.XML"]


def test_plan_flags_collisions(tmp_path):
    lib = tmp_path / FOLDER_FOOTAGE_LIB
    # Same filename in two categories, same week → second collides at the b-roll dest
    _mk(lib / "insert-detail" / "W05_May-11-17" / "C5.MP4")
    _mk(lib / "environment-detail" / "W05_May-11-17" / "C5.MP4")

    moves, _pw, _u, collisions = cli_index._plan_consolidation(tmp_path)
    assert len(moves) == 1       # only the first wins the dest
    assert len(collisions) == 1  # the second is reported, not silently dropped


def test_plan_unknown_week_routes_to_unknown_bucket(tmp_path, monkeypatch):
    lib = tmp_path / FOLDER_FOOTAGE_LIB
    _mk(lib / "candid-people" / "C6.MP4")  # no week folder
    # ffprobe fallback fails → clip still consolidates into b-roll/unknown-week/
    monkeypatch.setattr(cli_index, "get_shoot_date", lambda p: (_ for _ in ()).throw(Exception("no date")))

    moves, per_week, unknown, _c = cli_index._plan_consolidation(tmp_path)
    assert len(moves) == 1
    dest = moves[0][1].relative_to(tmp_path).as_posix()
    assert dest == f"{FOLDER_FOOTAGE_LIB}/{FOLDER_BROLL}/{cli_index.UNKNOWN_WEEK}/C6.MP4"
    assert unknown == [f"{FOLDER_FOOTAGE_LIB}/candid-people/C6.MP4"]
    assert per_week.get(cli_index.UNKNOWN_WEEK) == 1


def test_plan_unknown_week_falls_back_to_filmed_date(tmp_path, monkeypatch):
    lib = tmp_path / FOLDER_FOOTAGE_LIB
    _mk(lib / "candid-people" / "C7.MP4")  # no week folder
    monkeypatch.setattr(cli_index, "get_shoot_date", lambda p: "2026-05-12")

    moves, per_week, unknown, _c = cli_index._plan_consolidation(tmp_path)
    assert unknown == []
    assert per_week == {"W05_May-11-17": 1}
    dest = moves[0][1].relative_to(tmp_path).as_posix()
    assert dest == f"{FOLDER_FOOTAGE_LIB}/{FOLDER_BROLL}/W05_May-11-17/C7.MP4"


# ── _execute_consolidation ──────────────────────────────────────────────────

def test_execute_moves_files(tmp_path):
    src = _mk(tmp_path / "src" / "C8.MP4")
    dest = tmp_path / FOLDER_FOOTAGE_LIB / FOLDER_BROLL / "W05_May-11-17" / "C8.MP4"

    moved = cli_index._execute_consolidation([(src, dest)])
    assert moved == 1
    assert dest.exists() and not src.exists()


def test_execute_never_overwrites(tmp_path):
    src = _mk(tmp_path / "src" / "C9.MP4", b"new")
    dest = _mk(tmp_path / "dst" / "C9.MP4", b"original")

    moved = cli_index._execute_consolidation([(src, dest)])
    assert moved == 0
    assert dest.read_bytes() == b"original"  # untouched
    assert src.exists()                       # source left in place too


def test_prune_empty_dirs_keeps_broll_and_helpers(tmp_path):
    lib = tmp_path / FOLDER_FOOTAGE_LIB
    (lib / "interview-solo" / "W05_May-11-17").mkdir(parents=True)  # now empty
    (lib / FOLDER_BROLL / "W05_May-11-17").mkdir(parents=True)      # empty but kept
    (lib / "_TO_SORT").mkdir(parents=True)                          # empty but kept

    cli_index._prune_empty_dirs(lib, keep=FOLDER_BROLL)

    assert not (lib / "interview-solo").exists()        # emptied category pruned
    assert (lib / FOLDER_BROLL / "W05_May-11-17").exists()  # b-roll kept
    assert (lib / "_TO_SORT").exists()                  # helper kept
