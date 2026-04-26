"""Generate icon PNGs for the Trendify props doc.

Each icon is a solid silhouette in Trendify orange (#F28129) on a transparent
background, rendered at 1024x1024 via 4x supersampling for clean edges.
"""
import os
import math
from PIL import Image, ImageDraw

ORANGE = (242, 129, 41, 255)
TRANSPARENT = (0, 0, 0, 0)

OUT_SIZE = 1024
DRAW_SIZE = 4096

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, 'icons')
os.makedirs(OUT_DIR, exist_ok=True)


def new_canvas():
    img = Image.new('RGBA', (DRAW_SIZE, DRAW_SIZE), TRANSPARENT)
    return img, ImageDraw.Draw(img)


def save(img, name):
    out = img.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)
    path = os.path.join(OUT_DIR, f'{name}.png')
    out.save(path)
    print(f'  saved {name}.png')


CX = DRAW_SIZE // 2
CY = DRAW_SIZE // 2


def icon_pin():
    """01 - HOW WE GOT HERE - map pin"""
    img, d = new_canvas()
    radius = 750
    head_cy = CY - 350
    d.ellipse([CX - radius, head_cy - radius, CX + radius, head_cy + radius], fill=ORANGE)
    triangle = [
        (CX - radius * 0.92, head_cy + radius * 0.4),
        (CX + radius * 0.92, head_cy + radius * 0.4),
        (CX, head_cy + radius * 2.5),
    ]
    d.polygon(triangle, fill=ORANGE)
    # Inner hole (transparent)
    inner_r = int(radius // 2.5)
    d.ellipse([CX - inner_r, head_cy - inner_r, CX + inner_r, head_cy + inner_r], fill=TRANSPARENT)
    save(img, '01-how-we-got-here')


def icon_bolt():
    """02 - WHAT WE DO - lightning bolt"""
    img, d = new_canvas()
    pts = [
        (CX + 200, CY - 1600),
        (CX - 800, CY - 100),
        (CX - 100, CY - 100),
        (CX - 500, CY + 1600),
        (CX + 800, CY + 100),
        (CX + 100, CY + 100),
        (CX + 700, CY - 1000),
    ]
    d.polygon(pts, fill=ORANGE)
    save(img, '02-what-we-do')


def icon_eye():
    """03 - TRENDIFY VISION - eye"""
    img, d = new_canvas()
    width = 2400
    height = 1100
    n = 80
    pts = []
    for i in range(n + 1):
        t = i / n
        x = CX - width / 2 + t * width
        y = -height / 2 * math.sin(math.pi * t)
        pts.append((x, CY + y))
    for i in range(n, -1, -1):
        t = i / n
        x = CX - width / 2 + t * width
        y = height / 2 * math.sin(math.pi * t)
        pts.append((x, CY + y))
    d.polygon(pts, fill=ORANGE)
    # Pupil hole + inner dot
    pupil_r = 380
    d.ellipse([CX - pupil_r, CY - pupil_r, CX + pupil_r, CY + pupil_r], fill=TRANSPARENT)
    dot_r = 220
    d.ellipse([CX - dot_r, CY - dot_r, CX + dot_r, CY + dot_r], fill=ORANGE)
    save(img, '03-trendify-vision')


def icon_chat():
    """04 - HOW WE COMMUNICATE - chat bubble with three dots"""
    img, d = new_canvas()
    box = [CX - 1500, CY - 1100, CX + 1500, CY + 500]
    d.rounded_rectangle(box, radius=320, fill=ORANGE)
    # Tail pointing down-left
    tail = [
        (CX - 900, CY + 500 - 30),
        (CX - 1100, CY + 1250),
        (CX - 300, CY + 500 - 30),
    ]
    d.polygon(tail, fill=ORANGE)
    # Three dots
    dot_r = 150
    for off in [-700, 0, 700]:
        d.ellipse(
            [CX + off - dot_r, CY - 200 - dot_r,
             CX + off + dot_r, CY - 200 + dot_r],
            fill=TRANSPARENT,
        )
    save(img, '04-how-we-communicate')


def icon_wrench():
    """05 - TOOLS THAT WE USE - double-end wrench, rotated 45 degrees"""
    # Draw horizontally, then rotate the whole image
    img = Image.new('RGBA', (DRAW_SIZE, DRAW_SIZE), TRANSPARENT)
    d = ImageDraw.Draw(img)

    # Handle (horizontal)
    handle_left = CX - 1300
    handle_right = CX + 1300
    handle_top = CY - 160
    handle_bottom = CY + 160
    d.rounded_rectangle([handle_left, handle_top, handle_right, handle_bottom],
                        radius=140, fill=ORANGE)

    # Right head: closed-loop (box-end) wrench
    rh_cx = handle_right + 200
    rh_r = 540
    d.ellipse([rh_cx - rh_r, CY - rh_r, rh_cx + rh_r, CY + rh_r], fill=ORANGE)
    # Hex hole in right head
    rh_inner = 280
    d.ellipse([rh_cx - rh_inner, CY - rh_inner, rh_cx + rh_inner, CY + rh_inner],
              fill=TRANSPARENT)

    # Left head: open-end wrench
    lh_cx = handle_left - 200
    lh_r = 540
    d.ellipse([lh_cx - lh_r, CY - lh_r, lh_cx + lh_r, CY + lh_r], fill=ORANGE)
    # Square jaw cutout opening to the left
    jaw_w = 700
    jaw_h = 380
    d.rectangle([lh_cx - jaw_w, CY - jaw_h // 2, lh_cx, CY + jaw_h // 2],
                fill=TRANSPARENT)
    # Small inner cutout to give it depth
    inner_r = 130
    d.ellipse([lh_cx - inner_r, CY - inner_r, lh_cx + inner_r, CY + inner_r],
              fill=TRANSPARENT)

    # Rotate -45 degrees and save
    img = img.rotate(-45, resample=Image.BICUBIC)
    out = img.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)
    path = os.path.join(OUT_DIR, '05-tools-that-we-use.png')
    out.save(path)
    print('  saved 05-tools-that-we-use.png')


def icon_broom():
    """06 - HOUSEKEEPING - broom"""
    img, d = new_canvas()
    handle_top = CY - 1700
    handle_bottom = CY + 200
    handle_w = 90
    d.rectangle([CX - handle_w, handle_top, CX + handle_w, handle_bottom], fill=ORANGE)
    # Binding band
    band_top = handle_bottom
    band_bottom = handle_bottom + 220
    band_w = 700
    d.rectangle([CX - band_w, band_top, CX + band_w, band_bottom], fill=ORANGE)
    # Bristles (trapezoid)
    bristles_top = band_bottom
    bristles_bottom = bristles_top + 1300
    flare_w = 1100
    bristles = [
        (CX - band_w, bristles_top),
        (CX + band_w, bristles_top),
        (CX + flare_w, bristles_bottom),
        (CX - flare_w, bristles_bottom),
    ]
    d.polygon(bristles, fill=ORANGE)
    # Bristle separator lines (transparent slits)
    slit_w = 50
    n_slits = 6
    for i in range(1, n_slits):
        t = i / n_slits
        # Slit goes from top of bristles to bottom, fanning out with the trapezoid
        x_top = (CX - band_w) + (2 * band_w) * t
        x_bot = (CX - flare_w) + (2 * flare_w) * t
        slit = [
            (x_top - slit_w, bristles_top),
            (x_top + slit_w, bristles_top),
            (x_bot + slit_w * 1.5, bristles_bottom),
            (x_bot - slit_w * 1.5, bristles_bottom),
        ]
        d.polygon(slit, fill=TRANSPARENT)
    save(img, '06-housekeeping')


def icon_padlock():
    """07 - KEEP THINGS SAFE - padlock"""
    img, d = new_canvas()
    body_top = CY - 200
    body_bottom = CY + 1400
    body_w = 1150
    d.rounded_rectangle([CX - body_w, body_top, CX + body_w, body_bottom],
                        radius=200, fill=ORANGE)
    # Shackle: outer U
    shackle_outer = 850
    shackle_inner = 620
    shackle_cy_top = body_top - 50
    # Outer arc top
    d.pieslice(
        [CX - shackle_outer, shackle_cy_top - shackle_outer,
         CX + shackle_outer, shackle_cy_top + shackle_outer],
        180, 360, fill=ORANGE,
    )
    # Outer legs
    d.rectangle(
        [CX - shackle_outer, shackle_cy_top, CX + shackle_outer, body_top + 100],
        fill=ORANGE,
    )
    # Inner cutout: arc + legs (transparent)
    d.pieslice(
        [CX - shackle_inner, shackle_cy_top - shackle_inner,
         CX + shackle_inner, shackle_cy_top + shackle_inner],
        180, 360, fill=TRANSPARENT,
    )
    d.rectangle(
        [CX - shackle_inner, shackle_cy_top, CX + shackle_inner, body_top + 200],
        fill=TRANSPARENT,
    )
    # Re-fill body top edge so the inner cutout doesn't punch into the body
    d.rounded_rectangle([CX - body_w, body_top, CX + body_w, body_top + 200],
                        radius=200, fill=ORANGE)
    # Keyhole
    kh_cy = (body_top + body_bottom) // 2 - 100
    kh_r = 170
    d.ellipse([CX - kh_r, kh_cy - kh_r, CX + kh_r, kh_cy + kh_r], fill=TRANSPARENT)
    # Keyhole tail (trapezoid)
    tail = [
        (CX - 90, kh_cy + 50),
        (CX + 90, kh_cy + 50),
        (CX + 160, kh_cy + 480),
        (CX - 160, kh_cy + 480),
    ]
    d.polygon(tail, fill=TRANSPARENT)
    save(img, '07-keep-things-safe')


def icon_key():
    """08 - KEY TERMS TO KNOW - key"""
    img, d = new_canvas()
    head_cx = CX - 1000
    head_cy = CY
    head_r = 650
    d.ellipse([head_cx - head_r, head_cy - head_r,
               head_cx + head_r, head_cy + head_r], fill=ORANGE)
    # Hole in head
    hole_r = 280
    d.ellipse([head_cx - hole_r, head_cy - hole_r,
               head_cx + hole_r, head_cy + hole_r], fill=TRANSPARENT)
    # Shaft going right
    shaft_top = CY - 130
    shaft_bottom = CY + 130
    shaft_end = CX + 1500
    d.rectangle([head_cx + head_r - 50, shaft_top, shaft_end, shaft_bottom], fill=ORANGE)
    # Teeth (two downward notches near right end)
    d.rectangle([CX + 700, shaft_bottom, CX + 900, shaft_bottom + 280], fill=ORANGE)
    d.rectangle([CX + 1150, shaft_bottom, CX + 1350, shaft_bottom + 380], fill=ORANGE)
    save(img, '08-key-terms-to-know')


def icon_heart():
    """09 - CORE VALUES - heart (parametric curve for smooth shape)"""
    img, d = new_canvas()
    pts = []
    n = 240
    scale = 115
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        x = 16 * (math.sin(t) ** 3)
        y = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        pts.append((CX + x * scale, CY + y * scale))
    d.polygon(pts, fill=ORANGE)
    save(img, '09-core-values')


def main():
    print('Generating Trendify props icons...')
    icon_pin()
    icon_bolt()
    icon_eye()
    icon_chat()
    icon_wrench()
    icon_broom()
    icon_padlock()
    icon_key()
    icon_heart()
    print(f'\nDone. {len(os.listdir(OUT_DIR))} icons in {OUT_DIR}')


if __name__ == '__main__':
    main()
