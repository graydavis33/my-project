#!/usr/bin/env python3
"""
grid_preview.py — mock up how covers will look on the Instagram profile grid.

Takes cover images (9:16 or any size), center-crops each to the 3:4 grid tile,
and lays them out in IG's 3-column grid so Gray/Sai can approve the look
before touching the real profile.

Usage:
  python3 grid_preview.py cover1.png cover2.png cover3.png ... --out grid.jpg
  # order = top-left → right, row by row (IG shows newest first)
"""

import argparse

from PIL import Image

TILE_W, TILE_H = 360, 480            # 3:4 tile
GAP = 4
BG = (26, 26, 26)                    # brand #1A1A1A
COLS = 3


def to_tile(path):
    img = Image.open(path).convert("RGB")
    scale = max(TILE_W / img.width, TILE_H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    x = (img.width - TILE_W) // 2
    y = (img.height - TILE_H) // 2
    return img.crop((x, y, x + TILE_W, y + TILE_H))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("covers", nargs="+")
    p.add_argument("--out", default="grid_preview.jpg")
    a = p.parse_args()

    rows = (len(a.covers) + COLS - 1) // COLS
    canvas = Image.new("RGB", (COLS * TILE_W + (COLS - 1) * GAP,
                               rows * TILE_H + (rows - 1) * GAP), BG)
    for i, path in enumerate(a.covers):
        r, c = divmod(i, COLS)
        canvas.paste(to_tile(path), (c * (TILE_W + GAP), r * (TILE_H + GAP)))
    canvas.save(a.out, quality=92)
    print(f"saved {a.out}")


if __name__ == "__main__":
    main()
