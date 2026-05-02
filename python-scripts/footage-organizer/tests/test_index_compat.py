"""Cross-machine compatibility tests — simulate the same DB being read from
two different library roots (e.g. /Volumes/Footage/Sai vs D:/Sai)."""
from pathlib import Path
import sqlite3
import index, pull


def _make_clip(library: Path, rel: str) -> Path:
    """Create a real file at <library>/<rel> and return its Path."""
    full = library / rel
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_bytes(b"fake video bytes")
    return full


def test_same_db_resolves_under_two_different_library_roots(tmp_path):
    """The same SQLite DB (with relative paths) must work when the library root
    changes between machines. Simulates the user's actual flow: build index on
    Mac at /tmp/mac_lib, then read it back as if mounted at /tmp/win_lib."""
    mac_lib = tmp_path / "mac_lib"
    win_lib = tmp_path / "win_lib"
    mac_lib.mkdir()
    win_lib.mkdir()

    rel = "05_FOOTAGE_LIBRARY/interview-solo/W01_Apr-15-19/clip.mp4"

    # Step 1: Mac creates the file + DB at mac_lib
    _make_clip(mac_lib, rel)
    db = tmp_path / "shared.sqlite"
    index.init(db)
    index.upsert(db, index.ClipRecord(
        path=rel, category="interview-solo", format="short-form",
        filmed_date="2026-04-16", upload_date="2026-04-17",
        duration_s=10.0, width=1080, height=1920, codec="hevc", sha1="abc",
    ))

    # Step 2: Windows mounts the SAME drive at a different path. Recreate the
    # file at win_lib and read the DB through that root.
    _make_clip(win_lib, rel)

    rows = index.query(db, format="short-form")
    assert len(rows) == 1
    assert rows[0].path == rel  # path is relative — no machine-specific prefix

    # Existence check via Windows root works
    removed = index.remove_missing(db, library_root=win_lib)
    assert removed == 0  # file exists under win_lib

    # Pull via Windows root works
    out = win_lib / "07_QUERY_PULLS" / "x"
    result = pull.pull(db, out, library_root=win_lib, filmed_date="2026-04-16")
    assert result.count == 1
    assert (out / "clip.mp4").exists()


def test_legacy_absolute_path_db_is_detected(tmp_path):
    """A DB built before the migration (absolute Mac paths) must be flagged as legacy."""
    db = tmp_path / "legacy.sqlite"; index.init(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO clips VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("/Volumes/Footage/Sai/05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/x.mp4",
             "misc", "long-form", "2026-04-16", "2026-04-16",
             1.0, 1920, 1080, "h264", "abc"),
        )
    assert index.has_legacy_paths(db) is True


def test_legacy_windows_absolute_path_db_is_detected(tmp_path):
    """Same legacy detection for absolute Windows paths (drive letter)."""
    db = tmp_path / "legacy.sqlite"; index.init(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO clips VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("D:/Sai/05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/x.mp4",
             "misc", "long-form", "2026-04-16", "2026-04-16",
             1.0, 1920, 1080, "h264", "abc"),
        )
    assert index.has_legacy_paths(db) is True


def test_wipe_clips_then_reindex_produces_relative_paths(tmp_path):
    """Full migration round-trip: legacy DB → wipe → upsert with relative path."""
    db = tmp_path / "idx.sqlite"; index.init(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO clips VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("/Volumes/Footage/Sai/05_FOOTAGE_LIBRARY/misc/x.mp4",
             "misc", "long-form", "2026-04-16", "2026-04-16",
             1.0, 1920, 1080, "h264", "abc"),
        )
    assert index.has_legacy_paths(db) is True

    index.wipe_clips(db)
    assert len(index.query(db)) == 0
    assert index.has_legacy_paths(db) is False

    index.upsert(db, index.ClipRecord(
        path="05_FOOTAGE_LIBRARY/misc/x.mp4",
        category="misc", format="long-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1920, height=1080, codec="h264", sha1="abc",
    ))
    assert index.has_legacy_paths(db) is False
