import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import render


def test_segment_timing_basic():
    seg = {"in": 27.22, "out": 31.18, "tail": None}
    b_media, dur, a_media, fallback = render._segment_timing(seg, offset=9.3232)
    assert abs(b_media - 27.12) < 1e-6          # in - 0.10 head
    assert abs(dur - ((31.18 + 0.25) - 27.12)) < 1e-6  # (out + tail) - b_media
    assert abs(a_media - (27.12 - 9.3232)) < 1e-6
    assert fallback is False


def test_segment_timing_tail_override():
    seg = {"in": 92.0, "out": 94.26, "tail": 0.80}
    b_media, dur, _, _ = render._segment_timing(seg, offset=9.3232)
    assert abs(b_media - 91.9) < 1e-6
    assert abs(dur - ((94.26 + 0.80) - 91.9)) < 1e-6  # tail override respected


def test_segment_timing_hook_fallback():
    # in < offset => a_media negative => A reel falls back to B
    seg = {"in": 5.0, "out": 8.0, "tail": None}
    b_media, dur, a_media, fallback = render._segment_timing(seg, offset=9.3232)
    assert a_media < 0
    assert fallback is True


def test_segment_timing_clamps_b_media_at_zero():
    seg = {"in": 0.05, "out": 1.0, "tail": None}
    b_media, dur, _, _ = render._segment_timing(seg, offset=1.0)
    assert b_media == 0.0
    assert abs(dur - (1.0 + 0.25)) < 1e-6


def test_caption_remap_shifts_to_cut_timeline():
    offset = 9.3232
    segments = [
        {"in": 13.84, "out": 16.42, "tail": None},
        {"in": 27.22, "out": 31.18, "tail": None},
    ]
    words = [
        {"start": 14.0, "end": 14.5, "word": "hello"},   # inside seg 0
        {"start": 20.0, "end": 20.5, "word": "gap"},      # between segs => dropped
        {"start": 28.0, "end": 28.5, "word": "world"},    # inside seg 1
    ]
    out = render._caption_remap(words, segments, offset)
    assert [w["word"] for w in out] == ["hello", "world"]
    # first kept word: cum=0, b_media = 13.84-0.10 = 13.74 => 14.0 - 13.74 = 0.26
    assert abs(out[0]["start"] - 0.26) < 1e-3
    # second word lands after seg0's duration, all positive + monotonic
    assert out[1]["start"] > out[0]["end"]


def test_caption_remap_excludes_partial_words():
    segments = [{"in": 10.0, "out": 12.0, "tail": None}]
    words = [
        {"start": 9.5, "end": 10.5, "word": "straddle_in"},   # starts before in
        {"start": 11.5, "end": 12.5, "word": "straddle_out"}, # ends after out
        {"start": 10.5, "end": 11.0, "word": "keep"},
    ]
    out = render._caption_remap(words, segments, offset=0.0)
    assert [w["word"] for w in out] == ["keep"]


def test_deliverable_folder_naming():
    p = render._deliverable_folder(Path("/lib"), 3, 13, "The Real Lever Is You")
    assert p.name == "B3_V13 - The Real Lever Is You"
    assert p.parent.name == "Batch_03"
    assert p.parts[-3:] == ("shorts", "Batch_03", "B3_V13 - The Real Lever Is You")


def test_deliverable_folder_vid_zero_padded():
    p = render._deliverable_folder(Path("/lib"), 3, 4, "Money")
    assert p.name == "B3_V04 - Money"
