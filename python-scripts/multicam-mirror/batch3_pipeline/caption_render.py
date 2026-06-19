#!/usr/bin/env python3
"""Render a LANDSCAPE (1920x1080) alpha caption .mov for B3 Vid 1.

Reuses Sai's house caption style (Montserrat SemiBold, white, soft drop shadow,
2-3 words per card) but in 16:9 lower-third, driven by the exact word timings
from the cut (caption_words.json) — no transcription, so nothing gets clipped.

Output is ProRes 4444 with a real alpha channel -> composite over the multicam.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FONT_PATH = Path.home() / "Desktop/my-project/python-scripts/sai-captions/fonts/Montserrat.ttf"
FONT_VARIATION = "SemiBold"

VIDTAG = sys.argv[1] if len(sys.argv) > 1 else "Vid_01"
CUT = Path(f"/Volumes/Footage/Sai/01_ORGANIZED/Batch_03/{VIDTAG}/Cut")
WORDS = CUT / "caption_words.json"
REF_VIDEO = CUT / f"{VIDTAG}_A-cam_CUT.mp4"
OUT = CUT / f"{VIDTAG}_captions.mov"

VIDEO_W, VIDEO_H = 1920, 1080
FONT_SIZE = 60
TOP_MARGIN = 858          # y of top of the text -> lower third
TEXT_COLOR = (255, 255, 255, 255)
SHADOW_COLOR = (0, 0, 0, 165)
SHADOW_OFFSET = (0, 5)
SHADOW_BLUR = 6
FPS = "24000/1001"

PRESERVE_CASE = {"i": "I", "i'm": "I'm", "i've": "I've", "i'll": "I'll", "i'd": "I'd",
                 "sai": "Sai", "sai's": "Sai's"}
PUNCT = ".,!?;:\"()[]{}—–-…"
MAX_WORDS = 3
MAX_DUR = 1.6
MIN_DUR = 0.35
PAUSE_BREAK = 0.45


def clean(word):
    c = word.strip(PUNCT)
    return PRESERVE_CASE.get(c.lower(), c.lower())


def group(words):
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


def render_card(text, png, font):
    img = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    tl = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tl)
    bbox = font.getbbox(text)
    lw = bbox[2] - bbox[0]
    x = (VIDEO_W - lw) // 2 - bbox[0]
    sd.text((x + SHADOW_OFFSET[0], TOP_MARGIN + SHADOW_OFFSET[1]), text, font=font, fill=SHADOW_COLOR)
    td.text((x, TOP_MARGIN), text, font=font, fill=TEXT_COLOR)
    shadow = shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
    img.alpha_composite(shadow)
    img.alpha_composite(tl)
    img.save(png, "PNG")


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nk=1:nw=1", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def main():
    words = json.loads(WORDS.read_text())
    cards = group(words)
    dur = duration(REF_VIDEO)
    print(f"{len(words)} words -> {len(cards)} cards over {dur:.2f}s")

    font = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)
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
            render_card(text, p, font)
            pngs.append((p, s, e))

        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i",
               f"color=c=black@0.0:s={VIDEO_W}x{VIDEO_H}:r={FPS}:d={dur:.3f},format=rgba"]
        for p, _, _ in pngs:
            cmd += ["-loop", "1", "-i", str(p)]
        parts, prev = [], "0:v"
        for i, (_, s, e) in enumerate(pngs, start=1):
            nxt = f"v{i}"
            parts.append(f"[{prev}][{i}:v]overlay=0:0:enable='between(t,{s:.3f},{e:.3f})'[{nxt}]")
            prev = nxt
        cmd += ["-filter_complex", ";".join(parts), "-map", f"[{prev}]",
                "-t", f"{dur:.3f}", "-c:v", "prores_ks", "-profile:v", "4444",
                "-pix_fmt", "yuva444p10le", str(OUT)]
        subprocess.run(cmd, check=True, capture_output=True)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
