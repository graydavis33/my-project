"""Feature 1 — TRUE display-orientation column in the index. Migration is
non-destructive, and query(orientation=...) filters on the new column (NOT the
width×height-derived `format`, which lies for Sony 1920x1080 + 90° flag).
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import index
from index import ClipRecord


def _rec(path, orientation=None, **over):
    base = dict(
        path=path, category="b-roll", format="long-form",
        filmed_date="2026-05-12", upload_date="2026-05-13",
        duration_s=3.0, width=1920, height=1080, codec="", sha1=path,
        orientation=orientation,
    )
    base.update(over)
    return ClipRecord(**base)


def test_fresh_init_has_orientation_column(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    cols = {r[1] for r in sqlite3.connect(db).execute("PRAGMA table_info(clips)")}
    assert "orientation" in cols


def test_migration_adds_orientation_to_old_db(tmp_path):
    db = tmp_path / "old.sqlite"
    # Pre-orientation DB: has the v4 tag columns but NOT orientation.
    with sqlite3.connect(db) as c:
        c.execute("""CREATE TABLE clips (
            path TEXT PRIMARY KEY, category TEXT NOT NULL, format TEXT NOT NULL,
            filmed_date TEXT NOT NULL, upload_date TEXT NOT NULL, duration_s REAL NOT NULL,
            width INTEGER NOT NULL, height INTEGER NOT NULL, codec TEXT NOT NULL,
            sha1 TEXT NOT NULL, batch_num INTEGER, vid_num INTEGER,
            emotion TEXT, action TEXT, location TEXT, objects TEXT)""")
        c.execute("INSERT INTO clips (path,category,format,filmed_date,upload_date,"
                  "duration_s,width,height,codec,sha1) VALUES "
                  "('p/C1.MP4','b-roll','long-form','2026-05-12','2026-05-13',3.0,1920,1080,'','h')")

    index.init(db)  # runs _migrate

    cols = {r[1] for r in sqlite3.connect(db).execute("PRAGMA table_info(clips)")}
    assert "orientation" in cols
    # no data loss; legacy row's orientation is NULL until re-indexed
    rows = index.query(db, category="b-roll")
    assert len(rows) == 1
    assert rows[0].orientation is None


def test_query_filters_on_orientation(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    index.upsert(db, _rec("b-roll/W05/H1.MP4", orientation="horizontal"))
    index.upsert(db, _rec("b-roll/W05/H2.MP4", orientation="horizontal"))
    index.upsert(db, _rec("b-roll/W05/V1.MP4", orientation="vertical"))
    index.upsert(db, _rec("b-roll/W05/N1.MP4", orientation=None))

    horiz = {r.path for r in index.query(db, orientation="horizontal")}
    assert horiz == {"b-roll/W05/H1.MP4", "b-roll/W05/H2.MP4"}

    vert = {r.path for r in index.query(db, orientation="vertical")}
    assert vert == {"b-roll/W05/V1.MP4"}


def test_orientation_overwritten_on_rescan_not_coalesced(tmp_path):
    # Unlike tags, orientation is ffprobe-derived → a rescan overwrites it.
    db = tmp_path / "i.sqlite"
    index.init(db)
    index.upsert(db, _rec("b-roll/W05/C1.MP4", orientation="vertical"))
    index.upsert(db, _rec("b-roll/W05/C1.MP4", orientation="horizontal"))
    assert index.query(db, category="b-roll")[0].orientation == "horizontal"
