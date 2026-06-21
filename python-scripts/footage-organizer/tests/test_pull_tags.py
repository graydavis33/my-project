"""v4 Phase 5 — pull by tag. `pull` forwards tag filters to index.query and builds
the output folder with only the matching clips. Uses a real temp index + temp files.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import index
import pull as pull_mod
from index import ClipRecord


def _seed(lib: Path, db: Path, specs):
    """specs: list of (name, kwargs). Creates the file + index row. sha1=name so
    dedup-by-sha1 doesn't collapse distinct clips."""
    index.init(db)
    for name, kw in specs:
        rel = f"05_FOOTAGE_LIBRARY/b-roll/W05_May-11-17/{name}.MP4"
        f = lib / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b"x")
        rec = ClipRecord(path=rel, category="b-roll", format="long-form",
                         filmed_date="2026-05-12", upload_date="2026-05-13",
                         duration_s=3.0, width=1920, height=1080, codec="", sha1=name, **kw)
        index.upsert(db, rec)


def test_pull_by_emotion(tmp_path):
    db = tmp_path / ".idx.sqlite"
    _seed(tmp_path, db, [
        ("A", dict(emotion="focused", location="office")),
        ("B", dict(emotion="happy", location="office")),
        ("C", dict(emotion="focused", location="cafe")),
    ])
    res = pull_mod.pull(db, tmp_path / "out", library_root=tmp_path, emotion="focused")
    assert res.count == 2
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == ["A.MP4", "C.MP4"]


def test_pull_combined_emotion_and_location(tmp_path):
    db = tmp_path / ".idx.sqlite"
    _seed(tmp_path, db, [
        ("A", dict(emotion="focused", location="office")),
        ("C", dict(emotion="focused", location="cafe")),
    ])
    res = pull_mod.pull(db, tmp_path / "out", library_root=tmp_path,
                        emotion="focused", location="office")
    assert res.count == 1
    assert [p.name for p in (tmp_path / "out").iterdir()] == ["A.MP4"]


def test_pull_by_object_no_substring_collision(tmp_path):
    db = tmp_path / ".idx.sqlite"
    _seed(tmp_path, db, [
        ("A", dict(objects=index.pack_objects(["coffee cup"]))),
        ("B", dict(objects=index.pack_objects(["cup"]))),
    ])
    res = pull_mod.pull(db, tmp_path / "out", library_root=tmp_path, object="cup")
    assert [p.name for p in (tmp_path / "out").iterdir()] == ["B.MP4"]


def test_pull_no_match_is_empty(tmp_path):
    db = tmp_path / ".idx.sqlite"
    _seed(tmp_path, db, [("A", dict(emotion="focused"))])
    res = pull_mod.pull(db, tmp_path / "out", library_root=tmp_path, emotion="angry")
    assert res.count == 0
