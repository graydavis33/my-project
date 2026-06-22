import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orchestrate import _build_segments_json, _words_for_range, _read_title


WORDS = [
    {"word": "What's", "start": 13.8, "end": 14.0},
    {"word": "the", "start": 14.0, "end": 14.1},
    {"word": "real", "start": 14.1, "end": 14.4},
    {"word": "lever?", "start": 14.4, "end": 16.2},
    {"word": "The", "start": 27.2, "end": 27.4},
    {"word": "lever", "start": 27.4, "end": 27.8},
    {"word": "is", "start": 27.8, "end": 28.0},
    {"word": "you.", "start": 28.0, "end": 31.0},
]

# (seg_in, seg_out, next_word_start, hard_cap)
SEEDED = [
    (13.8, 16.42, 27.2, 27.18),
    (27.2, 31.18, 0, 31.18),
]

TRANSCRIPT = [
    {"start": 13.8, "end": 16.2, "text": "What's the real lever?"},
    {"start": 27.2, "end": 31.0, "text": "The lever is you."},
]


def test_words_for_range():
    assert _words_for_range(WORDS, 13.8, 16.42) == "What's the real lever?"
    assert _words_for_range(WORDS, 27.2, 31.18) == "The lever is you."


def test_schema_keys():
    d = _build_segments_json(3, 13, "The real lever is you", -5.4321, 7.2,
                             "01_ORGANIZED/Batch_03/Vid_13/A-cam/a.MP4",
                             "01_ORGANIZED/Batch_03/Vid_13/B-cam/b.MP4",
                             SEEDED, WORDS, TRANSCRIPT)
    for k in ("batch_n", "vid_n", "title", "offset", "offset_dominance",
              "a_src", "b_src", "fps", "segments", "dropped", "transcript"):
        assert k in d, f"missing key {k}"
    assert d["batch_n"] == 3 and d["vid_n"] == 13
    assert d["title"] == "The real lever is you"
    assert d["offset"] == -5.4321
    assert d["offset_dominance"] == 7.2
    assert d["fps"] == "24000/1001"
    assert d["a_src"].startswith("01_ORGANIZED")
    assert d["dropped"] == []


def test_segment_shape_and_text():
    d = _build_segments_json(3, 13, "T", 0.0, 5.0, "a", "b",
                             SEEDED, WORDS, TRANSCRIPT)
    assert len(d["segments"]) == 2
    for seg in d["segments"]:
        assert set(seg.keys()) == {"in", "out", "text", "tag", "tail"}
        assert isinstance(seg["in"], float)
        assert isinstance(seg["out"], float)
        assert seg["tail"] is None
    # text populated from words
    assert d["segments"][0]["text"] == "What's the real lever?"
    assert d["segments"][1]["text"] == "The lever is you."


def test_first_segment_question_tag():
    d = _build_segments_json(3, 13, "T", 0.0, 5.0, "a", "b",
                             SEEDED, WORDS, TRANSCRIPT)
    assert d["segments"][0]["tag"] == "HOOK — your question"
    assert d["segments"][1]["tag"] == ""


def test_first_segment_no_tag_when_not_question():
    words = [
        {"word": "The", "start": 0.0, "end": 0.2},
        {"word": "lever.", "start": 0.2, "end": 1.0},
    ]
    seeded = [(0.0, 1.2, 0, 1.2)]
    d = _build_segments_json(3, 13, "T", 0.0, 5.0, "a", "b",
                             seeded, words, [])
    assert d["segments"][0]["tag"] == ""


def test_transcript_carried():
    d = _build_segments_json(3, 13, "T", 0.0, 5.0, "a", "b",
                             SEEDED, WORDS, TRANSCRIPT)
    assert d["transcript"] == TRANSCRIPT


def test_read_title(tmp_path):
    vid = tmp_path / "Vid_13"
    vid.mkdir()
    assert _read_title(vid, 13) == "Video 13"
    (vid / "_INFO.txt").write_text("The real lever is you\nsecond line\n", encoding="utf-8")
    assert _read_title(vid, 13) == "The real lever is you"
