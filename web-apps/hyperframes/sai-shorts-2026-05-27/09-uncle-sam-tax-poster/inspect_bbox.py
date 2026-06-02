"""Inspect non-transparent pixel bounding box + sample alpha along rows
to figure out where head ends and body/arm begin."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from PIL import Image
from pathlib import Path

img = Image.open(Path(__file__).parent / "assets" / "uncle-sam-4x.png").convert("RGBA")
W, H = img.size
a = img.split()[-1].load()

# Find overall bbox of non-transparent content
bbox = img.getbbox()
print(f"Image size:    {W}x{H}")
print(f"Content bbox:  {bbox}  (left, top, right, bottom)")
print(f"Content size:  {bbox[2]-bbox[0]} x {bbox[3]-bbox[1]}")

# Sample alpha-coverage horizontally at key y-levels — tells us where the figure
# is widest (shoulders) and where it narrows (neck, beard tip).
print("\nHoriz pixel-coverage by Y row (number of opaque px, 0-1304):")
step = 40
for y in range(440, 1430, step):
    count = sum(1 for x in range(W) if a[x, y] > 32)
    bar = "#" * (count // 16)
    # also find leftmost+rightmost x with content for this row
    xs = [x for x in range(W) if a[x, y] > 32]
    if xs:
        left = xs[0]
        right = xs[-1]
        print(f"  y={y:5d}  count={count:4d}  L={left:4d}  R={right:4d}  W={right-left:4d}  {bar}")
    else:
        print(f"  y={y:5d}  empty")
