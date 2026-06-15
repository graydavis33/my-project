"""Tests for the delivered-folder watcher's pure 'brain' — detecting new exports,
debouncing until the file stops growing, and the seen-state. The Slack handshake
is live-only (tested with `watch_delivered.py --self-test`)."""
from pathlib import Path

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from watch_delivered import (
    _delivered_videos, _stable_new_items, _load_seen, _save_seen,
)


def _vid(root: Path, rel: str, data=b"x"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p


def test_delivered_videos_finds_only_videos(tmp_path):
    _vid(tmp_path, "shorts/A.mp4")
    _vid(tmp_path, "shorts/B.MOV")
    _vid(tmp_path, "shorts/notes.txt")       # not a video
    _vid(tmp_path, "shorts/._A.mp4")          # AppleDouble
    found = _delivered_videos(tmp_path)
    assert found == {"shorts/A.mp4", "shorts/B.MOV"}


def test_new_file_ready_only_after_it_stops_growing(tmp_path):
    _vid(tmp_path, "shorts/Export.mp4", b"12345")
    seen, sizes = set(), {}
    # first scan: brand-new file, size just recorded → not ready yet
    assert _stable_new_items(tmp_path, seen, sizes) == []
    # second scan, unchanged size → ready
    assert _stable_new_items(tmp_path, seen, sizes) == ["shorts/Export.mp4"]


def test_growing_file_is_not_ready(tmp_path):
    f = _vid(tmp_path, "shorts/Export.mp4", b"12345")
    seen, sizes = set(), {}
    _stable_new_items(tmp_path, seen, sizes)        # record initial size
    f.write_bytes(b"1234567890")                    # still exporting → grew
    assert _stable_new_items(tmp_path, seen, sizes) == []   # not stable
    assert _stable_new_items(tmp_path, seen, sizes) == ["shorts/Export.mp4"]  # now stable


def test_already_seen_items_are_ignored(tmp_path):
    _vid(tmp_path, "shorts/Old.mp4")
    seen = {"shorts/Old.mp4"}                        # baselined / already handled
    sizes = {}
    assert _stable_new_items(tmp_path, seen, sizes) == []
    assert _stable_new_items(tmp_path, seen, sizes) == []


def test_seen_state_round_trip(tmp_path):
    state = tmp_path / ".ship-watch-state.json"
    assert _load_seen(state) == set()
    _save_seen(state, {"shorts/A.mp4", "shorts/B.mp4"})
    assert _load_seen(state) == {"shorts/A.mp4", "shorts/B.mp4"}
