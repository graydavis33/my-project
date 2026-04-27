from pathlib import Path
import index


def test_index_round_trip(tmp_path):
    db = tmp_path / "idx.sqlite"
    index.init(db)

    rec = index.ClipRecord(
        path=str(tmp_path / "clip.mp4"),
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
    assert rows[0].category == "interview-solo"


def test_index_upsert_is_idempotent(tmp_path):
    db = tmp_path / "idx.sqlite"
    index.init(db)
    rec = index.ClipRecord(
        path="/x/y.mp4", category="misc", format="long-form",
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
            path=f"/x/{i}.mp4", category=cat, format=fmt,
            filmed_date=fdate, upload_date=fdate,
            duration_s=1.0, width=1, height=1, codec="x", sha1=str(i),
        ))

    assert len(index.query(db, format="short-form")) == 2
    assert len(index.query(db, category="interview-solo")) == 2
    assert len(index.query(db, filmed_date="2026-04-16")) == 2
    assert len(index.query(db, category="interview-solo", format="short-form")) == 1
