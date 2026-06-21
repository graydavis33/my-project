"""v4 Phase 4 — the dashboard write layer in index.py: get(), update_tags()
(set/clear/leave-unchanged), and distinct_tag_values() for autocomplete.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import index
from index import ClipRecord


def _seed(db, path="b-roll/W05/C1.MP4", **tags):
    index.init(db)
    base = dict(path=path, category="b-roll", format="long-form",
                filmed_date="2026-05-12", upload_date="2026-05-13",
                duration_s=3.0, width=1920, height=1080, codec="", sha1=path)
    base.update(tags)
    index.upsert(db, ClipRecord(**base))


def test_get_returns_record_or_none(tmp_path):
    db = tmp_path / "i.sqlite"
    _seed(db, emotion="focused")
    assert index.get(db, "b-roll/W05/C1.MP4").emotion == "focused"
    assert index.get(db, "nope.MP4") is None


def test_update_tags_sets_only_provided(tmp_path):
    db = tmp_path / "i.sqlite"
    _seed(db, emotion="happy", location="office")
    index.update_tags(db, "b-roll/W05/C1.MP4", location="cafe")  # only location
    r = index.get(db, "b-roll/W05/C1.MP4")
    assert r.location == "cafe"
    assert r.emotion == "happy"  # untouched


def test_update_tags_empty_string_clears(tmp_path):
    db = tmp_path / "i.sqlite"
    _seed(db, emotion="happy")
    index.update_tags(db, "b-roll/W05/C1.MP4", emotion="")
    assert index.get(db, "b-roll/W05/C1.MP4").emotion == ""


def test_update_tags_objects_roundtrip(tmp_path):
    db = tmp_path / "i.sqlite"
    _seed(db)
    index.update_tags(db, "b-roll/W05/C1.MP4", objects=index.pack_objects(["mic", "laptop"]))
    assert index.unpack_objects(index.get(db, "b-roll/W05/C1.MP4").objects) == ["mic", "laptop"]


def test_relocate_repoints_path_and_category(tmp_path):
    db = tmp_path / "i.sqlite"
    _seed(db, path="05_FOOTAGE_LIBRARY/b-roll/W05/C1.MP4", emotion="happy")
    n = index.relocate(db, "05_FOOTAGE_LIBRARY/b-roll/W05/C1.MP4",
                       "05_FOOTAGE_LIBRARY/vertical/W05/C1.MP4", "vertical")
    assert n == 1
    assert index.get(db, "05_FOOTAGE_LIBRARY/b-roll/W05/C1.MP4") is None
    moved = index.get(db, "05_FOOTAGE_LIBRARY/vertical/W05/C1.MP4")
    assert moved is not None and moved.category == "vertical"


def test_remove_deletes_row(tmp_path):
    db = tmp_path / "i.sqlite"
    _seed(db, path="b-roll/W05/C1.MP4")
    assert index.get(db, "b-roll/W05/C1.MP4") is not None
    assert index.remove(db, "b-roll/W05/C1.MP4") == 1
    assert index.get(db, "b-roll/W05/C1.MP4") is None
    assert index.remove(db, "b-roll/W05/C1.MP4") == 0  # already gone


def test_distinct_tag_values(tmp_path):
    db = tmp_path / "i.sqlite"
    _seed(db, path="b-roll/W05/A.MP4", emotion="focused", location="office",
          objects=index.pack_objects(["laptop", "mic"]))
    index.upsert(db, ClipRecord(path="b-roll/W05/B.MP4", category="b-roll", format="long-form",
                                filmed_date="2026-05-12", upload_date="2026-05-13", duration_s=3.0,
                                width=1920, height=1080, codec="", sha1="B",
                                emotion="happy", location="office",
                                objects=index.pack_objects(["laptop", "plant"])))
    d = index.distinct_tag_values(db)
    assert d["emotion"] == ["focused", "happy"]
    assert d["location"] == ["office"]
    assert d["object"] == ["laptop", "mic", "plant"]
