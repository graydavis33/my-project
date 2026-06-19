"""The index walker must skip underscore-prefixed helper folders so un-categorized
or archived footage never lands in the searchable b-roll index:
  _INBOX   — raw drop, not yet sorted
  _TO_SORT — manual holding area
  _BATCHES — finished batch interview originals (own filing system)
"""
from pathlib import Path

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli_index import _walk_videos


def _mk(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x")
    return p


def test_walk_skips_inbox_and_to_sort(tmp_path):
    organized = tmp_path / "01_ORGANIZED"
    _mk(organized / "_INBOX" / "2026-06-19" / "raw.MP4")
    _mk(organized / "_TO_SORT" / "loose.MP4")
    kept = _mk(organized / "interview-solo" / "2026-06-18" / "C1.MP4")

    found = set(_walk_videos(organized))
    assert kept in found
    assert not any("_INBOX" in p.parts or "_TO_SORT" in p.parts for p in found)


def test_walk_skips_batches_archive(tmp_path):
    lib = tmp_path / "05_FOOTAGE_LIBRARY"
    _mk(lib / "_BATCHES" / "Batch_02" / "Vid_01" / "C2493.MP4")
    broll = _mk(lib / "nyc-street" / "W10_Jun-15-21" / "C2700.MP4")

    found = set(_walk_videos(lib))
    assert broll in found
    assert not any("_BATCHES" in p.parts for p in found)
