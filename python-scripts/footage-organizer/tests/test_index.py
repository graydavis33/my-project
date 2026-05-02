from pathlib import Path
import index


def test_index_round_trip(tmp_path):
    db = tmp_path / "idx.sqlite"
    index.init(db)

    rec = index.ClipRecord(
        path="05_FOOTAGE_LIBRARY/interview-solo/W01_Apr-15-19/clip.mp4",
        category="interview-solo",
        format="short-form",
        filmed_date="2026-04-16",
        upload_date="2026-04-17",
        duration_s=12.34,
        width=1080,
        height=1920,
        codec="hevc",
        sha1="abc123",
    )
    index.upsert(db, rec)

    rows = index.query(db, format="short-form", filmed_date="2026-04-16")
    assert len(rows) == 1
    assert rows[0].path == "05_FOOTAGE_LIBRARY/interview-solo/W01_Apr-15-19/clip.mp4"
    assert rows[0].category == "interview-solo"


def test_index_upsert_is_idempotent(tmp_path):
    db = tmp_path / "idx.sqlite"
    index.init(db)
    rec = index.ClipRecord(
        path="05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/y.mp4",
        category="misc", format="long-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1920, height=1080, codec="h264", sha1="x",
    )
    index.upsert(db, rec)
    index.upsert(db, rec)
    assert len(index.query(db)) == 1


def test_index_query_filters(tmp_path):
    db = tmp_path / "idx.sqlite"
    index.init(db)
    for i, (cat, fmt, fdate) in enumerate([
        ("interview-solo", "short-form", "2026-04-16"),
        ("interview-solo", "long-form",  "2026-04-16"),
        ("insert-hands",   "short-form", "2026-04-15"),
    ]):
        index.upsert(db, index.ClipRecord(
            path=f"05_FOOTAGE_LIBRARY/{cat}/W01_Apr-15-19/{i}.mp4",
            category=cat, format=fmt,
            filmed_date=fdate, upload_date=fdate,
            duration_s=1.0, width=1, height=1, codec="x", sha1=str(i),
        ))

    assert len(index.query(db, format="short-form")) == 2
    assert len(index.query(db, category="interview-solo")) == 2
    assert len(index.query(db, filmed_date="2026-04-16")) == 2
    assert len(index.query(db, category="interview-solo", format="short-form")) == 1


def test_remove_missing_resolves_against_library(tmp_path):
    """remove_missing now takes library_root and joins before checking existence."""
    db = tmp_path / "idx.sqlite"; index.init(db)
    library = tmp_path / "library"
    real_dir = library / "05_FOOTAGE_LIBRARY" / "misc" / "W01_Apr-15-19"
    real_dir.mkdir(parents=True)
    real_file = real_dir / "real.mp4"; real_file.write_bytes(b"x")

    index.upsert(db, index.ClipRecord(
        path="05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/real.mp4",
        category="misc", format="long-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1920, height=1080, codec="h264", sha1="r",
    ))
    index.upsert(db, index.ClipRecord(
        path="05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/ghost.mp4",
        category="misc", format="long-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1920, height=1080, codec="h264", sha1="g",
    ))

    removed = index.remove_missing(db, library_root=library)
    assert removed == 1
    rows = index.query(db)
    assert len(rows) == 1
    assert rows[0].path.endswith("real.mp4")


def test_has_legacy_paths_detects_absolute(tmp_path):
    """has_legacy_paths returns True if any stored path is absolute."""
    db = tmp_path / "idx.sqlite"; index.init(db)
    # Insert one legacy-format absolute path directly (simulating pre-migration DB)
    import sqlite3
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO clips VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("/Volumes/Footage/Sai/05_FOOTAGE_LIBRARY/misc/x.mp4",
             "misc", "long-form", "2026-04-16", "2026-04-16",
             1.0, 1920, 1080, "h264", "abc"),
        )
    assert index.has_legacy_paths(db) is True


def test_has_legacy_paths_false_when_all_relative(tmp_path):
    db = tmp_path / "idx.sqlite"; index.init(db)
    index.upsert(db, index.ClipRecord(
        path="05_FOOTAGE_LIBRARY/misc/x.mp4",
        category="misc", format="long-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1920, height=1080, codec="h264", sha1="abc",
    ))
    assert index.has_legacy_paths(db) is False


def test_has_legacy_paths_false_on_empty_db(tmp_path):
    db = tmp_path / "idx.sqlite"; index.init(db)
    assert index.has_legacy_paths(db) is False


def test_wipe_clips_drops_all_rows(tmp_path):
    db = tmp_path / "idx.sqlite"; index.init(db)
    index.upsert(db, index.ClipRecord(
        path="x.mp4", category="misc", format="long-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1, height=1, codec="x", sha1="x",
    ))
    assert len(index.query(db)) == 1
    index.wipe_clips(db)
    assert len(index.query(db)) == 0
