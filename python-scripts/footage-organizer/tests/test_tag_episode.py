# tests/test_tag_episode.py
import os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cli_index as cli
import index
from index import ClipRecord

def test_category_from_path_episode_folder():
    lib = Path("/Sai")
    clip = lib / "01_ORGANIZED" / "ep2 doc" / "2026-06-10" / "C1.MP4"
    assert cli._category_from_path(clip, lib) == "ep2 doc"

def test_query_by_episode_category_excludes_broll(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    def rec(p, cat):
        return ClipRecord(path=p, category=cat, format="long-form",
                          filmed_date="2026-06-10", upload_date="", duration_s=3.0,
                          width=1920, height=1080, codec="", sha1=p)
    index.upsert(db, rec("01_ORGANIZED/ep2 doc/2026-06-10/C1.MP4", "ep2 doc"))
    index.upsert(db, rec("05_FOOTAGE_LIBRARY/b-roll/W07/C9.MP4", "b-roll"))
    got = [r.path for r in index.query(db, category="ep2 doc")]
    assert got == ["01_ORGANIZED/ep2 doc/2026-06-10/C1.MP4"]
