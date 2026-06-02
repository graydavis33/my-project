"""Segment the upscaled, bg-removed Uncle Sam into 3 layered PNGs:
   - body.png: torso + lower body, head & arm regions removed
   - head.png: head + hat, rest transparent
   - arm.png:  pointing arm + hand + finger, rest transparent

All output PNGs share the same 1304x1712 canvas so they can be stacked
absolutely in HyperFrames without manual positioning offsets.
"""
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "assets" / "uncle-sam-4x.png"

img = Image.open(SRC).convert("RGBA")
W, H = img.size
print(f"Source: {W}x{H}")

# === Bounding boxes for each part (in 4x coordinate space) ===
# Tuned by inspect_bbox.py — figure content bbox is (277,442,1018,1427)
# Head: hat top → chin/upper-beard, before shoulders kick in at y~920
HEAD_BOX = (260, 430, 820, 940)
# Forearm + hand + pointing finger only (upper arm stays in body).
# Pivots at the ELBOW (~x=460, y=1180) so forearm swings like a puppet joint
# without disturbing the bowtie or upper coat.
ARM_BOX = (260, 1120, 740, 1430)

FEATHER_PX = 24   # softer feather for cleaner seams


def make_mask(box, feather=FEATHER_PX):
    """White-fill rect inside box, soft black outside; gaussian-blurred edges."""
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.rectangle(box, fill=255)
    if feather > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=feather))
    return mask


def apply_alpha_mask(rgba, mask):
    """Multiply rgba's alpha by mask (L mode). Returns new RGBA."""
    out = rgba.copy()
    r, g, b, a = out.split()
    # multiply existing alpha by mask
    a_arr = a.load()
    m_arr = mask.load()
    new_a = Image.new("L", rgba.size, 0)
    new_a_arr = new_a.load()
    for y in range(H):
        for x in range(W):
            new_a_arr[x, y] = (a_arr[x, y] * m_arr[x, y]) // 255
    return Image.merge("RGBA", (r, g, b, new_a))


def invert_mask(mask):
    """Invert L mode mask: 255 -> 0, 0 -> 255."""
    return Image.eval(mask, lambda v: 255 - v)


# === HEAD layer: keep head box, transparent outside ===
head_mask = make_mask(HEAD_BOX)
head_layer = apply_alpha_mask(img, head_mask)
head_layer.save(HERE / "assets" / "uncle-sam-head.png", "PNG")
print(f"Saved head.png  (box {HEAD_BOX})")

# === ARM layer: keep arm box, transparent outside ===
arm_mask = make_mask(ARM_BOX)
arm_layer = apply_alpha_mask(img, arm_mask)
arm_layer.save(HERE / "assets" / "uncle-sam-arm.png", "PNG")
print(f"Saved arm.png   (box {ARM_BOX})")

# === BODY layer: full image MINUS head AND arm regions ===
# Create a "keep" mask: starts fully white (keep everything), then subtract
# head and arm bounding boxes (so those areas become transparent in body).
body_mask = Image.new("L", (W, H), 255)
head_punch = make_mask(HEAD_BOX, feather=FEATHER_PX)
arm_punch = make_mask(ARM_BOX, feather=FEATHER_PX)
# body_mask = body_mask * (255 - head_punch)/255 * (255 - arm_punch)/255
hm = head_punch.load()
am = arm_punch.load()
bm = body_mask.load()
for y in range(H):
    for x in range(W):
        cur = bm[x, y]
        cur = (cur * (255 - hm[x, y])) // 255
        cur = (cur * (255 - am[x, y])) // 255
        bm[x, y] = cur
body_layer = apply_alpha_mask(img, body_mask)
body_layer.save(HERE / "assets" / "uncle-sam-body.png", "PNG")
print(f"Saved body.png  (head + arm regions punched)")

print("\nDone.")
