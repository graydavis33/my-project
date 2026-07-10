"""pull --batch/--vid: batch_num/vid_num filters flow through index.query into
pull, whole-batch pulls group into Vid_MM subfolders, and batch_summary feeds
list-batches."""
from pathlib import Path

import index
import pull as pull_mod


def _seed(tmp_path):
    lib = tmp_path / "library"
    db = tmp_path / "idx.sqlite"
    index.init(db)
    clips = [
        ("01_ORGANIZED/Batch_03/Vid_09/C0001.MP4", 3, 9),
        ("01_ORGANIZED/Batch_03/Vid_09/C0002.MP4", 3, 9),
        ("01_ORGANIZED/Batch_03/Vid_10/C0003.MP4", 3, 10),
        ("01_ORGANIZED/Batch_04/Vid_01/C0004.MP4", 4, 1),
        ("05_FOOTAGE_LIBRARY/b-roll/W13_Jul-06-12/C0005.MP4", None, None),
    ]
    for i, (rel, batch, vid) in enumerate(clips):
        src = lib / rel
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_bytes(bytes([65 + i]) * 50)
        index.upsert(db, index.ClipRecord(
            path=rel, category="misc", format="long-form",
            filmed_date="2026-06-19", upload_date="2026-06-19",
            duration_s=30.0, width=1920, height=1080, codec="",
            sha1=f"sha{i}", batch_num=batch, vid_num=vid,
        ))
    return lib, db


def test_query_filters_by_batch_and_vid(tmp_path):
    _, db = _seed(tmp_path)
    assert len(index.query(db, batch_num=3)) == 3
    assert len(index.query(db, batch_num=3, vid_num=9)) == 2
    assert len(index.query(db, batch_num=4)) == 1


def test_pull_whole_batch(tmp_path):
    lib, db = _seed(tmp_path)
    out = tmp_path / "pull-out"
    result = pull_mod.pull(db, out, library_root=lib, batch_num=3)
    assert result.count == 3
    names = {p.name for p in out.rglob("*.MP4")}
    assert names == {"C0001.MP4", "C0002.MP4", "C0003.MP4"}


def test_pull_batch_groups_by_vid_subfolder(tmp_path):
    lib, db = _seed(tmp_path)
    out = tmp_path / "pull-out"

    def by_vid(record):  # mirrors cmd_pull's whole-batch grouping
        return f"Vid_{record.vid_num:02d}" if record.vid_num else "unassigned"

    pull_mod.pull(db, out, library_root=lib, batch_num=3, subfolder_fn=by_vid)
    assert sorted(p.name for p in out.iterdir() if p.is_dir()) == ["Vid_09", "Vid_10"]
    assert len(list((out / "Vid_09").glob("*.MP4"))) == 2
    assert len(list((out / "Vid_10").glob("*.MP4"))) == 1


def test_batch_summary(tmp_path):
    _, db = _seed(tmp_path)
    rows = index.batch_summary(db)
    assert [(r[0], r[1], r[2]) for r in rows] == [(3, 9, 2), (3, 10, 1), (4, 1, 1)]
    assert rows[0][4] == 60.0  # total duration of Vid_09
