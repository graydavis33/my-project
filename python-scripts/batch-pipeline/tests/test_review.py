import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from review import build_review, HEAD, TAIL


SEGMENTS = [
    {"in": 13.84, "out": 16.42, "text": "What's the real lever everyone is ignoring?", "tag": "HOOK"},
    {"in": 27.22, "out": 31.18, "text": "The real lever is you & how you feel."},
    {"in": 92.00, "out": 94.26, "text": "every other lever will pull itself.", "tail": 0.80},
]


def test_build_review_writes_index(tmp_path):
    out = build_review(SEGMENTS, "bcam.mp4", tmp_path)
    assert out == tmp_path / "index.html"
    assert out.exists()


def test_block_counts_and_content(tmp_path):
    out = build_review(SEGMENTS, "bcam.mp4", tmp_path)
    html = out.read_text(encoding="utf-8")

    # one <video per segment
    assert html.count("<video ") == len(SEGMENTS)
    # one caption .cap block per segment
    assert html.count('class="clip cap"') == len(SEGMENTS)

    # read-along text + tag present (& escaped)
    assert "What&#x27;s the real lever everyone is ignoring?" in html or \
           "What's the real lever everyone is ignoring?" in html
    assert "The real lever is you &amp; how you feel." in html
    assert "HOOK" in html
    assert "1 / 3" in html and "3 / 3" in html


def test_duration_math_and_total(tmp_path):
    out = build_review(SEGMENTS, "bcam.mp4", tmp_path)
    html = out.read_text(encoding="utf-8")

    cum_ms = 0
    expected_durs = []
    for seg in SEGMENTS:
        seg_tail = seg.get("tail")
        seg_tail = TAIL if seg_tail is None else seg_tail
        media_in = max(0.0, seg["in"] - HEAD)
        dur_ms = round(((seg["out"] + seg_tail) - media_in) * 1000)
        dur = (dur_ms - 3) / 1000  # 3ms sub-frame guard
        expected_durs.append(f'data-duration="{dur:.3f}"')
        cum_ms += dur_ms

    for d in expected_durs:
        assert d in html

    total = cum_ms / 1000
    assert f'data-duration="{total:.3f}"' in html  # root div total
