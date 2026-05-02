from pathlib import Path
import index, pull


def _seed(db, library, n=3, **overrides):
    """Seed n clips at <library>/05_FOOTAGE_LIBRARY/<category>/W01_Apr-15-19/clip_*.mp4
    and insert matching index rows with RELATIVE paths."""
    cat = overrides.get("category", "interview-solo")
    week = "W01_Apr-15-19"
    src_dir = library / "05_FOOTAGE_LIBRARY" / cat / week
    src_dir.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        rel = f"05_FOOTAGE_LIBRARY/{cat}/{week}/clip_{i}.mp4"
        f = library / rel
        f.write_bytes(b"fake video bytes")
        index.upsert(db, index.ClipRecord(
            path=rel,
            category=cat,
            format=overrides.get("format", "short-form"),
            filmed_date=overrides.get("filmed_date", "2026-04-16"),
            upload_date=overrides.get("upload_date", "2026-04-17"),
            duration_s=10.0, width=1080, height=1920, codec="hevc",
            sha1=f"sha-{i}",
        ))


def test_pull_creates_hardlinks(tmp_path):
    library = tmp_path / "library"; library.mkdir()
    db = library / "idx.sqlite"; index.init(db)
    _seed(db, library)
    out = library / "07_QUERY_PULLS" / "test"

    result = pull.pull(db, out, library_root=library, format="short-form", filmed_date="2026-04-16")

    assert result.count == 3
    assert out.is_dir()
    pulled = sorted(out.iterdir())
    assert len(pulled) == 3
    # Hardlinks share inode on same volume
    src0 = library / result.records[0].path
    assert pulled[0].stat().st_ino == src0.stat().st_ino


def test_pull_skips_dupes_by_sha1(tmp_path):
    library = tmp_path / "library"; library.mkdir()
    db = library / "idx.sqlite"; index.init(db)
    src_dir = library / "05_FOOTAGE_LIBRARY" / "misc" / "W01_Apr-15-19"
    src_dir.mkdir(parents=True)
    for name in ("a.mp4", "b.mp4"):
        rel = f"05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/{name}"
        (library / rel).write_bytes(b"x")
        index.upsert(db, index.ClipRecord(
            path=rel, category="misc", format="short-form",
            filmed_date="2026-04-16", upload_date="2026-04-16",
            duration_s=1.0, width=1, height=1, codec="x", sha1="SAME",
        ))
    out = library / "07_QUERY_PULLS" / "dedup"
    result = pull.pull(db, out, library_root=library, dedup_by_sha1=True)
    assert result.count == 1


def test_pull_empty_result(tmp_path):
    library = tmp_path / "library"; library.mkdir()
    db = library / "idx.sqlite"; index.init(db)
    out = library / "07_QUERY_PULLS" / "nothing"
    result = pull.pull(db, out, library_root=library, category="interview-duo")
    assert result.count == 0
    # Empty result should NOT create the folder
    assert not out.exists()


def test_pull_count_reflects_actually_linked_not_matched(tmp_path):
    """If a source file is missing on disk, PullResult.count should NOT include it."""
    library = tmp_path / "library"; library.mkdir()
    db = library / "idx.sqlite"; index.init(db)
    src_dir = library / "05_FOOTAGE_LIBRARY" / "misc" / "W01_Apr-15-19"
    src_dir.mkdir(parents=True)

    # Two clips: one exists on disk, one is a ghost row
    real_rel = "05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/real.mp4"
    ghost_rel = "05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/ghost.mp4"
    (library / real_rel).write_bytes(b"x")  # ghost intentionally not created

    index.upsert(db, index.ClipRecord(
        path=real_rel, category="misc", format="short-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1, height=1, codec="x", sha1="real-sha",
    ))
    index.upsert(db, index.ClipRecord(
        path=ghost_rel, category="misc", format="short-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1, height=1, codec="x", sha1="ghost-sha",
    ))

    out = library / "07_QUERY_PULLS" / "missing-src"
    result = pull.pull(db, out, library_root=library, filmed_date="2026-04-16")

    assert result.count == 1, f"Expected 1 (only real file linked), got {result.count}"
    assert len(list(out.iterdir())) == 1
