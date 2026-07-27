#!/usr/bin/env python3
"""
render_thumb.py — branded Instagram reel cover / grid thumbnail for Sai.

Takes a video + timestamp (or a still frame) + a title, and renders a
1080x1920 (9:16) cover PNG whose title sits inside the CENTER 3:4 region,
so it looks right both as the full reel cover and as the profile-grid tile.

Brand (LOCKED, from business/sai-karra/editor-onboarding/03-brand-template-spec.md):
  - Montserrat ExtraBold headers, lowercase except I/names
  - White text, accent word(s) in Trendify orange #F28129 (max ~20%)
  - Soft drop shadow (same recipe as sai-captions)

Usage:
  python3 render_thumb.py --video short.mp4 --time 12.5 --title "the client\nemail that\nchanged everything" --accent client --out cover.png
  python3 render_thumb.py --frame frame.jpg --title "..." --out cover.png

  --time      seconds into the video to grab the frame
  --title     use \n for manual line breaks; auto-wraps if none given
  --accent    word(s) to color orange (case-insensitive, optional)
  --pos       vertical anchor of the text block inside the grid-safe zone:
              top | center | bottom  (default: top)
  --no-scrim  disable the dark gradient band behind the text
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FONT_PATH = HERE.parent / "sai-captions" / "fonts" / "Montserrat.ttf"

W, H = 1080, 1920
# Instagram grid shows the center 3:4 crop of a 9:16 cover.
GRID_TOP, GRID_BOTTOM = 240, 1680       # 1080x1440 center region
SAFE_MARGIN_X = 70                       # side margin inside the tile
ORANGE = (242, 129, 41)                  # #F28129
WHITE = (255, 255, 255)
SHADOW_OFFSET = (5, 6)
SHADOW_BLUR = 6

FONT_SIZE = 92                           # brand header spec: 72-92px ExtraBold
MIN_FONT_SIZE = 64
LINE_SPACING = 1.16

# words kept capitalized despite lowercase styling (brand: lowercase except I/names)
NAMES = {"i", "sai", "sharran", "srivatsaa", "trendify", "ai", "ceo", "cmo", "roi"}
CAP = {"i": "I", "sai": "Sai", "sharran": "Sharran", "srivatsaa": "Srivatsaa",
       "trendify": "Trendify", "ai": "AI", "ceo": "CEO", "cmo": "CMO", "roi": "ROI"}


def load_font(size):
    font = ImageFont.truetype(str(FONT_PATH), size)
    try:
        font.set_variation_by_name("ExtraBold")
    except Exception:
        pass
    return font


def brand_case(text):
    words = text.split(" ")
    out = []
    for w in words:
        bare = re.sub(r"[^\w']", "", w).lower()
        out.append(w.replace(re.sub(r"[^\w']", "", w), CAP[bare]) if bare in CAP else w.lower())
    return " ".join(out)


def grab_frame(video, seconds):
    tmp = Path(tempfile.mkstemp(suffix=".png")[1])
    cmd = ["ffmpeg", "-y", "-ss", str(seconds), "-i", str(video),
           "-frames:v", "1", "-q:v", "2", str(tmp)]
    subprocess.run(cmd, check=True, capture_output=True)
    return tmp


def fit_canvas(img, cx=0.5):
    """Scale + crop any frame to 1080x1920. cx = horizontal focus (0=left, 1=right)."""
    img = img.convert("RGB")
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    x = min(max(round(img.width * cx - W / 2), 0), img.width - W)
    y = (img.height - H) // 2
    return img.crop((x, y, x + W, y + H))


def wrap_lines(title, font, max_width, draw):
    if "\\n" in title or "\n" in title:
        return [l.strip() for l in title.replace("\\n", "\n").split("\n") if l.strip()]
    words, lines, cur = title.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render(frame_img, title, accent=None, pos="top", bg="scrim", out="cover.png", cx=0.5):
    base = fit_canvas(frame_img, cx)
    max_width = W - 2 * SAFE_MARGIN_X

    # pick a font size where no line overflows and the block fits the safe zone
    size = FONT_SIZE
    dummy = ImageDraw.Draw(base)
    while size >= MIN_FONT_SIZE:
        font = load_font(size)
        lines = wrap_lines(title, font, max_width, dummy)
        line_h = round(size * LINE_SPACING)
        block_h = line_h * len(lines)
        widths = [dummy.textlength(l, font=font) for l in lines]
        if max(widths) <= max_width and block_h <= (GRID_BOTTOM - GRID_TOP) * 0.6:
            break
        size -= 4
    lines = [brand_case(l) for l in lines]

    anchors = {
        "top": GRID_TOP + 90,
        "center": GRID_TOP + ((GRID_BOTTOM - GRID_TOP) - block_h) // 2,
        "bottom": GRID_BOTTOM - block_h - 110,
    }
    y0 = anchors[pos]

    # dark gradient band behind the text for legibility on any footage
    if bg == "scrim":
        band = Image.new("L", (1, H), 0)
        pad = 80
        for y in range(H):
            d = min(abs(y - (y0 - pad)), abs(y - (y0 + block_h + pad)))
            if y0 - pad <= y <= y0 + block_h + pad:
                band.putpixel((0, y), 150)
            elif d < 120:
                band.putpixel((0, y), round(150 * (1 - d / 120)))
        band = band.resize((W, H))
        black = Image.new("RGB", (W, H), (10, 10, 10))
        base = Image.composite(black, base, band.point(lambda v: v))

    # solid rounded label behind each line (like the "Growth Tactics" pill style)
    if bg == "pill":
        base = base.convert("RGBA")
        pill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        line_h_p = round(size * LINE_SPACING)
        pad_x, pad_y = 36, 14
        for i, line in enumerate(lines):
            lw = dummy.textlength(line, font=font)
            x0p = (W - lw) / 2 - pad_x
            y0p = y0 + i * line_h_p - pad_y
            pd.rounded_rectangle([x0p, y0p, x0p + lw + 2 * pad_x, y0p + size + 2 * pad_y],
                                 radius=26, fill=(20, 20, 20, 235))
        base.alpha_composite(pill)
        base = base.convert("RGB")

    # shadow layer then text layer (sai-captions recipe)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt)

    accents = {a.strip().lower() for a in (accent or "").split(",") if a.strip()}
    line_h = round(size * LINE_SPACING)
    for i, line in enumerate(lines):
        y = y0 + i * line_h
        x = (W - td.textlength(line, font=font)) // 2
        sd.text((x + SHADOW_OFFSET[0], y + SHADOW_OFFSET[1]), line, font=font, fill=(0, 0, 0, 220))
        # draw the full line once (exact centering), then overdraw accent words
        td.text((x, y), line, font=font, fill=WHITE)
        words = line.split(" ")
        for j, word in enumerate(words):
            bare = re.sub(r"[^\w']", "", word).lower()
            if bare in accents:
                prefix = " ".join(words[:j])
                off = td.textlength(prefix + " ", font=font) if prefix else 0
                td.text((x + off, y), word, font=font, fill=ORANGE)

    shadow = shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
    base = base.convert("RGBA")
    base.alpha_composite(shadow)
    base.alpha_composite(txt)
    base.convert("RGB").save(out, quality=95)
    return out


def main():
    p = argparse.ArgumentParser()
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--video")
    src.add_argument("--frame")
    p.add_argument("--time", type=float, default=0.0)
    p.add_argument("--title", required=True)
    p.add_argument("--accent", default=None, help="comma-separated words to color orange")
    p.add_argument("--pos", choices=["top", "center", "bottom"], default="top")
    p.add_argument("--no-scrim", action="store_true")
    p.add_argument("--bg", choices=["scrim", "none", "pill"], default="scrim")
    p.add_argument("--cx", type=float, default=0.5, help="horizontal crop focus 0-1")
    p.add_argument("--out", default="cover.png")
    a = p.parse_args()

    if a.video:
        tmp = grab_frame(a.video, a.time)
        img = Image.open(tmp)
    else:
        img = Image.open(a.frame)

    bg = "none" if a.no_scrim else a.bg
    out = render(img, a.title, accent=a.accent, pos=a.pos, bg=bg, out=a.out, cx=a.cx)
    print(f"saved {out}")


if __name__ == "__main__":
    sys.exit(main())
