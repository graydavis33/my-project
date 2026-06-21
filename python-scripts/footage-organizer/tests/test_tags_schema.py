"""v4 Phase 2 — b-roll tag columns in the index. The migration is non-destructive,
a plain re-index never wipes tags (COALESCE), and pull-by-tag filters work
(including pipe-wrapped object matching with no substring collisions).
"""
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import index
from index import ClipRecord


def _rec(path, **tags):
    """Minimal ClipRecord with the required scan fields + optional tag overrides."""
    base = dict(
        path=path, category="b-roll", format="long-form",
        filmed_date="2026-05-12", upload_date="2026-05-13",
        duration_s=3.0, width=1920, height=1080, codec="", sha1="abc",
    )
    base.update(tags)
    return ClipRecord(**base)


def test_fresh_init_has_tag_columns(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    cols = {r[1] for r in sqlite3.connect(db).execute("PRAGMA table_info(clips)")}
    assert {"emotion", "action", "location", "objects"} <= cols


def test_migration_adds_tag_columns_to_old_db(tmp_path):
    db = tmp_path / "old.sqlite"
    # Simulate a pre-v4 DB: clips table without the tag columns.
    with sqlite3.connect(db) as c:
        c.execute("""CREATE TABLE clips (
            path TEXT PRIMARY KEY, category TEXT NOT NULL, format TEXT NOT NULL,
            filmed_date TEXT NOT NULL, upload_date TEXT NOT NULL, duration_s REAL NOT NULL,
            width INTEGER NOT NULL, height INTEGER NOT NULL, codec TEXT NOT NULL,
            sha1 TEXT NOT NULL, batch_num INTEGER, vid_num INTEGER)""")
        c.execute("INSERT INTO clips VALUES ('p/C1.MP4','b-roll','long-form','2026-05-12','2026-05-13',3.0,1920,1080,'','h',NULL,NULL)")

    index.init(db)  # runs _migrate

    cols = {r[1] for r in sqlite3.connect(db).execute("PRAGMA table_info(clips)")}
    assert {"emotion", "action", "location", "objects"} <= cols
    # existing row survives the migration
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM clips").fetchone()[0] == 1


def test_upsert_and_query_tags_roundtrip(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    index.upsert(db, _rec("b-roll/W05/C1.MP4", emotion="stoic", action="walking",
                          location="times square", objects=index.pack_objects(["coffee cup", "laptop"])))

    got = index.query(db, emotion="stoic")[0]
    assert got.action == "walking" and got.location == "times square"
    assert index.unpack_objects(got.objects) == ["coffee cup", "laptop"]


def test_reindex_never_wipes_tags(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    # 1) tag the clip
    index.upsert(db, _rec("b-roll/W05/C1.MP4", emotion="stoic", location="office"))
    # 2) a plain re-index re-upserts the SAME path with NO tags (all None)
    index.upsert(db, _rec("b-roll/W05/C1.MP4"))

    got = index.query(db, category="b-roll")[0]
    assert got.emotion == "stoic"   # preserved across rescan
    assert got.location == "office"


def test_explicit_value_still_updates_tag(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    index.upsert(db, _rec("b-roll/W05/C1.MP4", emotion="happy"))
    index.upsert(db, _rec("b-roll/W05/C1.MP4", emotion="stoic"))  # explicit re-tag
    assert index.query(db, category="b-roll")[0].emotion == "stoic"


def test_object_filter_no_substring_collision(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    index.upsert(db, _rec("b-roll/W05/A.MP4", objects=index.pack_objects(["coffee cup"])))
    index.upsert(db, _rec("b-roll/W05/B.MP4", objects=index.pack_objects(["cup"])))

    assert {r.path for r in index.query(db, object="cup")} == {"b-roll/W05/B.MP4"}
    assert {r.path for r in index.query(db, object="coffee cup")} == {"b-roll/W05/A.MP4"}


def test_tag_filters_and_combine(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    index.upsert(db, _rec("b-roll/W05/A.MP4", emotion="stoic", location="times square"))
    index.upsert(db, _rec("b-roll/W05/B.MP4", emotion="stoic", location="office"))

    hits = index.query(db, emotion="stoic", location="times square")
    assert {r.path for r in hits} == {"b-roll/W05/A.MP4"}


def test_pack_unpack_objects():
    assert index.pack_objects([]) is None
    assert index.pack_objects(["a", "b"]) == "|a|b|"
    assert index.unpack_objects(None) == []
    assert index.unpack_objects("|a|b|") == ["a", "b"]
