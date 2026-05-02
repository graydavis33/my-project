from pathlib import Path
import index, pull


def _seed(db, tmp_path, n=3, **overrides):
    src = tmp_path / "src"; src.mkdir()
    for i in range(n):
        f = src / f"clip_{i}.mp4"
        f.write_bytes(b"fake video bytes")
        index.upsert(db, index.ClipRecord(
            path=str(f),
            category=overrides.get("category", "interview-solo"),
            format=overrides.get("format", "short-form"),
            filmed_date=overrides.get("filmed_date", "2026-04-16"),
            upload_date=overrides.get("upload_date", "2026-04-17"),
            duration_s=10.0, width=1080, height=1920, codec="hevc",
            sha1=f"sha-{i}",
        ))


def test_pull_creates_hardlinks(tmp_path):
    db = tmp_path / "idx.sqlite"; index.init(db)
    _seed(db, tmp_path)
    out = tmp_path / "_pulls" / "test"

    result = pull.pull(db, out, format="short-form", filmed_date="2026-04-16")

    assert result.count == 3
    assert out.is_dir()
    pulled = sorted(out.iterdir())
    assert len(pulled) == 3
    # Hardlinks share inode on same volume
    src0 = Path(result.records[0].path)
    assert pulled[0].stat().st_ino == src0.stat().st_ino


def test_pull_skips_dupes_by_sha1(tmp_path):
    db = tmp_path / "idx.sqlite"; index.init(db)
    src = tmp_path / "src"; src.mkdir()
    f1 = src / "a.mp4"; f1.write_bytes(b"x")
    f2 = src / "b.mp4"; f2.write_bytes(b"x")
    for f in (f1, f2):
        index.upsert(db, index.ClipRecord(
            path=str(f), category="misc", format="short-form",
            filmed_date="2026-04-16", upload_date="2026-04-16",
            duration_s=1.0, width=1, height=1, codec="x", sha1="SAME",
        ))
    out = tmp_path / "_pulls" / "dedup"
    result = pull.pull(db, out, dedup_by_sha1=True)
    assert result.count == 1


def test_pull_empty_result(tmp_path):
    db = tmp_path / "idx.sqlite"; index.init(db)
    out = tmp_path / "_pulls" / "nothing"
    result = pull.pull(db, out, category="interview-duo")
    assert result.count == 0
    # Empty result should NOT create the folder
    assert not out.exists()


def test_pull_count_reflects_actually_linked_not_matched(tmp_path):
    """If a source file is missing on disk, PullResult.count should NOT include it."""
    db = tmp_path / "idx.sqlite"; index.init(db)
    src = tmp_path / "src"; src.mkdir()

    # Two clips: one exists on disk, one is a ghost row
    real = src / "real.mp4"; real.write_bytes(b"x")
    ghost_path = str(src / "ghost.mp4")  # never created

    index.upsert(db, index.ClipRecord(
        path=str(real), category="misc", format="short-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1, height=1, codec="x", sha1="real-sha",
    ))
    index.upsert(db, index.ClipRecord(
        path=ghost_path, category="misc", format="short-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1, height=1, codec="x", sha1="ghost-sha",
    ))

    out = tmp_path / "_pulls" / "missing-src"
    result = pull.pull(db, out, filmed_date="2026-04-16")

    assert result.count == 1, f"Expected 1 (only real file linked), got {result.count}"
    assert len(list(out.iterdir())) == 1
