"""Incremental _reindex: unchanged files skip the probe entirely; new/changed
files are probed; deleted files are pruned. probe_media is faked so no ffprobe
is needed — the fingerprint logic is what's under test."""
import time
from pathlib import Path

import cli_index
import index


FAKE_PROBE = {
    "width": 1920, "height": 1080, "duration_s": 5.0,
    "filmed_date": "2026-07-01", "orientation": "horizontal",
}


def _make_library(tmp_path):
    lib = tmp_path / "library"
    week = lib / "05_FOOTAGE_LIBRARY" / "b-roll" / "W13_Jul-06-12"
    week.mkdir(parents=True)
    (week / "C0001.MP4").write_bytes(b"a" * 100)
    (week / "C0002.MP4").write_bytes(b"b" * 100)
    return lib, week


def _counting_probe(counter):
    def probe(filepath):
        counter.append(filepath)
        return dict(FAKE_PROBE)
    return probe


def test_second_scan_probes_nothing(tmp_path, monkeypatch):
    lib, week = _make_library(tmp_path)
    db = tmp_path / "idx.sqlite"
    calls = []
    monkeypatch.setattr(cli_index, "probe_media", _counting_probe(calls))

    added, skipped, removed = cli_index._reindex(lib, db)
    assert (added, skipped, removed) == (2, 0, 0)
    assert len(calls) == 2

    added, skipped, removed = cli_index._reindex(lib, db)
    assert (added, skipped, removed) == (0, 0, 0)
    assert len(calls) == 2  # no re-probe of unchanged files


def test_changed_file_reprobes_only_that_file(tmp_path, monkeypatch):
    lib, week = _make_library(tmp_path)
    db = tmp_path / "idx.sqlite"
    calls = []
    monkeypatch.setattr(cli_index, "probe_media", _counting_probe(calls))

    cli_index._reindex(lib, db)
    calls.clear()

    changed = week / "C0001.MP4"
    changed.write_bytes(b"a" * 200)  # new size ⇒ new fingerprint

    added, skipped, removed = cli_index._reindex(lib, db)
    assert added == 1
    assert [Path(c).name for c in calls] == ["C0001.MP4"]


def test_deleted_file_is_pruned_without_probing(tmp_path, monkeypatch):
    lib, week = _make_library(tmp_path)
    db = tmp_path / "idx.sqlite"
    calls = []
    monkeypatch.setattr(cli_index, "probe_media", _counting_probe(calls))

    cli_index._reindex(lib, db)
    calls.clear()

    (week / "C0002.MP4").unlink()
    added, skipped, removed = cli_index._reindex(lib, db)
    assert (added, removed) == (0, 1)
    assert calls == []
    assert [r.path for r in index.query(db)] == [
        "05_FOOTAGE_LIBRARY/b-roll/W13_Jul-06-12/C0001.MP4"
    ]


def test_reindex_fills_fingerprint_and_batch_fields(tmp_path, monkeypatch):
    lib, _ = _make_library(tmp_path)
    batch_dir = lib / "01_ORGANIZED" / "Batch_03" / "Vid_09"
    batch_dir.mkdir(parents=True)
    (batch_dir / "C0100.MP4").write_bytes(b"c" * 300)
    db = tmp_path / "idx.sqlite"
    monkeypatch.setattr(cli_index, "probe_media", lambda fp: dict(FAKE_PROBE))

    cli_index._reindex(lib, db)

    rec = index.get(db, "01_ORGANIZED/Batch_03/Vid_09/C0100.MP4")
    assert (rec.batch_num, rec.vid_num) == (3, 9)
    assert rec.size_bytes == 300
    assert rec.mtime is not None


def test_pre_v5_rows_reprobe_once_then_skip(tmp_path, monkeypatch):
    """Rows without a fingerprint (NULL size/mtime) re-probe on the first run
    under the new code, then skip like any other unchanged row."""
    lib, week = _make_library(tmp_path)
    db = tmp_path / "idx.sqlite"
    calls = []
    monkeypatch.setattr(cli_index, "probe_media", _counting_probe(calls))

    # Simulate an old-code row: no size/mtime.
    index.init(db)
    index.upsert(db, index.ClipRecord(
        path="05_FOOTAGE_LIBRARY/b-roll/W13_Jul-06-12/C0001.MP4",
        category="b-roll", format="long-form",
        filmed_date="2026-07-01", upload_date="2026-07-01",
        duration_s=5.0, width=1920, height=1080, codec="", sha1="old",
    ))

    added, _, _ = cli_index._reindex(lib, db)
    assert added == 2  # both files probed (one legacy row, one brand-new file)

    calls.clear()
    added, _, _ = cli_index._reindex(lib, db)
    assert added == 0
    assert calls == []
