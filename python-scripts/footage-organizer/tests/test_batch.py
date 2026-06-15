"""Tests for the v3 `batch` command — file a shoot into Batch_NN/Vid_MM/ + tag
the index with batch_num/vid_num. Pure helpers are unit-tested directly so the
move/parse logic is covered without needing ffprobe on real video."""
import sqlite3
from pathlib import Path

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import index
from cli_index import (
    _expand_clip_segment, _parse_map, _matching_files, _file_batch,
    _batch_vid_from_path,
)

LIB = Path("/lib")


def _touch(folder: Path, name: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    f = folder / name
    f.write_bytes(b"fake video bytes")
    return f


# ---- clip-range expansion -------------------------------------------------

def test_expand_single_clip():
    assert _expand_clip_segment("C2493") == ["C2493"]


def test_expand_range_inclusive():
    assert _expand_clip_segment("C2493-C2495") == ["C2493", "C2494", "C2495"]


def test_expand_range_preserves_zero_padding():
    assert _expand_clip_segment("C0008-C0011") == ["C0008", "C0009", "C0010", "C0011"]


def test_expand_lowercases_to_upper():
    assert _expand_clip_segment("c2493") == ["C2493"]


def test_expand_reversed_range_raises():
    try:
        _expand_clip_segment("C2495-C2493")
        assert False, "expected ValueError"
    except ValueError:
        pass


# ---- --map parsing --------------------------------------------------------

def test_parse_map_basic():
    assert _parse_map("1:C2493-C2495 2:C2496-C2498") == {
        1: ["C2493", "C2494", "C2495"],
        2: ["C2496", "C2497", "C2498"],
    }


def test_parse_map_comma_list_and_single():
    assert _parse_map("1:C2493,C2495 2:C2500") == {
        1: ["C2493", "C2495"],
        2: ["C2500"],
    }


def test_parse_map_bad_token_raises():
    try:
        _parse_map("1-C2493")  # missing colon
        assert False, "expected ValueError"
    except ValueError:
        pass


# ---- batch/vid derivation from path --------------------------------------

def test_batch_vid_from_organized_path():
    clip = LIB / "01_ORGANIZED" / "Batch_02" / "Vid_01" / "C2493.MP4"
    assert _batch_vid_from_path(clip, LIB) == (2, 1)


def test_batch_vid_from_nested_path():
    clip = LIB / "02_ACTIVE_PROJECTS" / "shorts" / "Batch_10" / "Vid_03" / "x.mp4"
    assert _batch_vid_from_path(clip, LIB) == (10, 3)


def test_batch_vid_none_for_non_batch_path():
    clip = LIB / "05_FOOTAGE_LIBRARY" / "interview-solo" / "W01_Apr-15-19" / "c.mp4"
    assert _batch_vid_from_path(clip, LIB) == (None, None)


# ---- file matching --------------------------------------------------------

def test_matching_files_exact_and_sidecar(tmp_path):
    src = tmp_path / "src"
    _touch(src, "C2493.MP4")
    _touch(src, "C2493M01.XML")   # Sony sidecar — non-digit after the id
    _touch(src, "C2493.WAV")
    names = sorted(f.name for f in _matching_files(src, "C2493"))
    assert names == ["C2493.MP4", "C2493.WAV", "C2493M01.XML"]


def test_matching_files_non_digit_guard(tmp_path):
    # C249 must NOT match C2493 (next char is a digit)
    src = tmp_path / "src"
    _touch(src, "C2493.MP4")
    assert _matching_files(src, "C249") == []


def test_matching_files_skips_appledouble(tmp_path):
    src = tmp_path / "src"
    _touch(src, "._C2493.MP4")
    assert _matching_files(src, "C2493") == []


# ---- the move stage -------------------------------------------------------

def test_file_batch_moves_into_vid_folders(tmp_path):
    src = tmp_path / "01_ORGANIZED" / "2026-06-07"
    for n in ("C2493", "C2494", "C2495", "C2496"):
        _touch(src, f"{n}.MP4")
    batch_root = tmp_path / "01_ORGANIZED" / "Batch_02"

    result = _file_batch(src, batch_root, {1: ["C2493", "C2494", "C2495"]})

    assert result["moved"] == 3
    assert (batch_root / "Vid_01" / "C2493.MP4").exists()
    assert (batch_root / "Vid_01" / "C2495.MP4").exists()
    # The clip not in the map is left in the source and flagged as unmapped
    assert (src / "C2496.MP4").exists()
    assert result["unmapped"] == ["C2496.MP4"]
    assert result["not_found"] == []


def test_file_batch_reports_not_found(tmp_path):
    src = tmp_path / "src"
    _touch(src, "C2493.MP4")
    batch_root = tmp_path / "Batch_02"
    result = _file_batch(src, batch_root, {1: ["C2493", "C9999"]})
    assert result["moved"] == 1
    assert result["not_found"] == [(1, "C9999")]


def test_file_batch_is_idempotent(tmp_path):
    src = tmp_path / "src"
    _touch(src, "C2493.MP4")
    batch_root = tmp_path / "Batch_02"
    _file_batch(src, batch_root, {1: ["C2493"]})
    # Re-running with the file already moved must not error or double-move
    result = _file_batch(src, batch_root, {1: ["C2493"]})
    assert result["moved"] == 0
    assert (batch_root / "Vid_01" / "C2493.MP4").exists()


# ---- index stores + filters batch_num/vid_num -----------------------------

def test_index_round_trips_batch_vid(tmp_path):
    db = tmp_path / "idx.sqlite"
    index.init(db)
    index.upsert(db, index.ClipRecord(
        path="01_ORGANIZED/Batch_02/Vid_01/C2493.MP4",
        category="Batch_02", format="short-form",
        filmed_date="2026-06-07", upload_date="2026-06-07",
        duration_s=1.0, width=1080, height=1920, codec="", sha1="a",
        batch_num=2, vid_num=1,
    ))
    rows = index.query(db, batch_num=2)
    assert len(rows) == 1
    assert rows[0].batch_num == 2 and rows[0].vid_num == 1
    assert index.query(db, batch_num=2, vid_num=2) == []


def test_index_batch_columns_default_null(tmp_path):
    db = tmp_path / "idx.sqlite"
    index.init(db)
    index.upsert(db, index.ClipRecord(
        path="05_FOOTAGE_LIBRARY/misc/x.mp4",
        category="misc", format="long-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1, height=1, codec="x", sha1="x",
    ))
    assert index.query(db)[0].batch_num is None


def test_init_migrates_old_ten_column_db(tmp_path):
    """A DB built by the pre-batch code (10 columns) must gain batch_num/vid_num
    on the next init() — non-destructively, preserving existing rows."""
    db = tmp_path / "old.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute(
            "CREATE TABLE clips (path TEXT PRIMARY KEY, category TEXT, format TEXT, "
            "filmed_date TEXT, upload_date TEXT, duration_s REAL, width INTEGER, "
            "height INTEGER, codec TEXT, sha1 TEXT)"
        )
        conn.execute(
            "INSERT INTO clips (path, category, format, filmed_date, upload_date, "
            "duration_s, width, height, codec, sha1) VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("05_FOOTAGE_LIBRARY/misc/x.mp4", "misc", "long-form",
             "2026-04-16", "2026-04-16", 1.0, 1, 1, "x", "x"),
        )

    index.init(db)  # should ALTER TABLE ADD COLUMN batch_num, vid_num

    cols = {r[1] for r in sqlite3.connect(db).execute("PRAGMA table_info(clips)").fetchall()}
    assert "batch_num" in cols and "vid_num" in cols
    rows = index.query(db)
    assert len(rows) == 1 and rows[0].batch_num is None and rows[0].vid_num is None
