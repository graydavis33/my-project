"""Caption stage: render an alpha ProRes 4444 .mov with house-style caption cards.

Ported from D:/Sai/01_ORGANIZED/Batch_03/Vid_04/_caption_v04.py.
All rendering math (TOP_MARGIN, shadow blur, gaussian, overlay-enable timing,
prores_ks 4444 export) preserved identically; style values and ffmpeg args now
come from config.
"""
import json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import config

# --- resolved style values -------------------------------------------------
_S = config.CAPTION_STYLE
FONT_SIZE    = _S["font_size"]
TOP_MARGIN   = _S["top_margin"]
MAX_WORDS    = _S["max_words"]
TEXT_COLOR   = _S["text_color"]
SHADOW_COLOR = _S["shadow_color"]
SHADOW_OFFSET = _S["shadow_offset"]
SHADOW_BLUR  = _S["shadow_blur"]
PRESERVE_CASE = _S["preserve_case"]
PUNCT        = _S["punct"]

# grouping constants not in config — kept here to preserve behavior exactly
MAX_DUR    = 1.6
MIN_DUR    = 0.35
PAUSE_BREAK = 0.45

FONT_VARIATION = "SemiBold"
VIDEO_W, VIDEO_H = 1920, 1080


# ---------------------------------------------------------------------------

def clean(word: str) -> str:
    """Strip punctuation and apply preserve-case map; lowercase everything else."""
    c = word.strip(PUNCT)
    return PRESERVE_CASE.get(c.lower(), c.lower())


def group(words: list) -> list:
    """Group word dicts into caption cards of ≤ MAX_WORDS words.

    Returns list of (card_words, start, end) tuples.
    """
    cards, cur = [], []
    for w in words:
        if not cur:
            cur.append(w); continue
        gap = w["start"] - cur[-1]["end"]
        if len(cur) >= MAX_WORDS or (w["end"] - cur[0]["start"]) > MAX_DUR or gap > PAUSE_BREAK:
            cards.append(cur); cur = [w]
        else:
            cur.append(w)
    if cur:
        cards.append(cur)
    fixed = []
    for i, c in enumerate(cards):
        s, e = c[0]["start"], c[-1]["end"]
        if e - s < MIN_DUR:
            e = s + MIN_DUR
        if i + 1 < len(cards):
            e = min(e, cards[i + 1][0]["start"])
        fixed.append((c, s, e))
    return fixed


def _render_card(text: str, png: Path, font) -> None:
    """Draw one caption card as a transparent RGBA PNG."""
    img    = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    sd     = ImageDraw.Draw(shadow)
    tl     = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    td     = ImageDraw.Draw(tl)
    bbox   = font.getbbox(text)
    lw     = bbox[2] - bbox[0]
    x      = (VIDEO_W - lw) // 2 - bbox[0]
    sd.text((x + SHADOW_OFFSET[0], TOP_MARGIN + SHADOW_OFFSET[1]), text, font=font, fill=SHADOW_COLOR)
    td.text((x, TOP_MARGIN), text, font=font, fill=TEXT_COLOR)
    shadow = shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
    img.alpha_composite(shadow)
    img.alpha_composite(tl)
    img.save(png, "PNG")


def _duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nk=1:nw=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def render(caption_words: Path, ref_video: Path, out_mov: Path) -> Path:
    """Render caption_words.json against ref_video into out_mov (ProRes 4444 alpha).

    Parameters
    ----------
    caption_words : Path
        JSON file with word-timing dicts: [{word, start, end}, ...].
    ref_video : Path
        Reference video — used only to get total duration.
    out_mov : Path
        Destination .mov (ProRes 4444 yuva444p10le, transparent).

    Returns
    -------
    Path
        out_mov after successful encode.
    """
    words = json.loads(Path(caption_words).read_text(encoding="utf-8"))
    cards = group(words)
    dur   = _duration(ref_video)
    print(f"{len(words)} words -> {len(cards)} cards over {dur:.2f}s")

    font = ImageFont.truetype(str(config.font_path()), FONT_SIZE)
    try:
        font.set_variation_by_name(FONT_VARIATION)
    except Exception:
        pass

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        pngs = []
        for i, (card, s, e) in enumerate(cards):
            text = " ".join(clean(w["word"]) for w in card if clean(w["word"]))
            p = td / f"c{i:03d}.png"
            _render_card(text, p, font)
            pngs.append((p, s, e))

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i",
            f"color=c=black@0.0:s={VIDEO_W}x{VIDEO_H}:r={config.FPS}:d={dur:.3f},format=rgba",
        ]
        for p, _, _ in pngs:
            cmd += ["-loop", "1", "-i", str(p)]

        parts, prev = [], "0:v"
        for i, (_, s, e) in enumerate(pngs, start=1):
            nxt = f"v{i}"
            parts.append(
                f"[{prev}][{i}:v]overlay=0:0:enable='between(t,{s:.3f},{e:.3f})'[{nxt}]"
            )
            prev = nxt

        cmd += [
            "-filter_complex", ";".join(parts),
            "-map", f"[{prev}]",
            "-t", f"{dur:.3f}",
            *config.PRORES4444,
            str(out_mov),
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    print(f"wrote {out_mov}")
    return Path(out_mov)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Render alpha caption .mov")
    p.add_argument("caption_words", type=Path, help="caption_words.json")
    p.add_argument("ref_video",     type=Path, help="reference cut for duration")
    p.add_argument("out_mov",       type=Path, help="output .mov path")
    args = p.parse_args()
    render(args.caption_words, args.ref_video, args.out_mov)
