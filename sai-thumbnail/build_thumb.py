"""Build 3-panel Sai thumbnail with glass-pane dividers."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance
from rembg import remove, new_session

HERE = Path(__file__).parent
W, H = 1920, 1080
PANEL_W = W // 3  # 640
DIVIDER_X = [PANEL_W, PANEL_W * 2]  # 640, 1280


def fit_panel(img: Image.Image, target_w: int, target_h: int, focus_x: float = 0.5, focus_y: float = 0.5) -> Image.Image:
    """Scale + center-crop image to target panel size, biased to focus point (0-1)."""
    sw, sh = img.size
    src_ratio = sw / sh
    tgt_ratio = target_w / target_h
    if src_ratio > tgt_ratio:
        # source wider — scale by height
        new_h = target_h
        new_w = int(sh * (target_h / sh) * src_ratio)
        # actually: scale image so height = target_h
        scale = target_h / sh
        new_w = int(sw * scale)
        new_h = target_h
    else:
        # source taller — scale by width
        scale = target_w / sw
        new_w = target_w
        new_h = int(sh * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    # Crop around focus
    left = int((new_w - target_w) * focus_x)
    top = int((new_h - target_h) * focus_y)
    left = max(0, min(left, new_w - target_w))
    top = max(0, min(top, new_h - target_h))
    return img.crop((left, top, left + target_w, top + target_h))


def make_glass_edge_hint(panel_h: int, width: int = 4) -> Image.Image:
    """Whisper of glass edge — single faint white highlight, no shadow band."""
    g = Image.new("RGBA", (width, panel_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    for i in range(width):
        a = int(70 * (1 - abs(i - width / 2) / (width / 2)))
        d.line([(i, 0), (i, panel_h)], fill=(255, 255, 255, a), width=1)
    return g


def feather_edge(img: Image.Image, side: str, feather_w: int, fg_mask: Image.Image | None = None) -> Image.Image:
    """Apply alpha gradient on left/right edge so the image bleeds into neighbor.
    If fg_mask provided (L mode, same size as img, 255=foreground), those pixels stay opaque.
    """
    img = img.convert("RGBA")
    mask = Image.new("L", img.size, 255)
    md = ImageDraw.Draw(mask)
    if side == "left":
        for x in range(feather_w):
            a = int(255 * (x / feather_w))
            md.line([(x, 0), (x, img.height)], fill=a)
    elif side == "right":
        for x in range(feather_w):
            a = int(255 * (x / feather_w))
            md.line([(img.width - 1 - x, 0), (img.width - 1 - x, img.height)], fill=a)
    elif side == "both":
        for x in range(feather_w):
            a = int(255 * (x / feather_w))
            md.line([(x, 0), (x, img.height)], fill=a)
            md.line([(img.width - 1 - x, 0), (img.width - 1 - x, img.height)], fill=a)
    # If we have a foreground mask, lift the feather alpha back to 255 wherever it's foreground
    if fg_mask is not None:
        # Compose: out_alpha = max(feather_alpha, fg_mask)
        from PIL import ImageChops
        mask = ImageChops.lighter(mask, fg_mask)
    img.putalpha(mask)
    return img


def get_fg_mask(img: Image.Image, session, soften: int = 4) -> Image.Image:
    """Run rembg → return an L-mode alpha mask same size as img (255=foreground)."""
    rgba = remove(img, session=session, alpha_matting=False)
    mask = rgba.split()[-1]
    if soften:
        mask = mask.filter(ImageFilter.GaussianBlur(soften))
    return mask


def detect_white_table(img: Image.Image, y_start_frac: float = 0.55) -> Image.Image:
    """Detect bright white surface in the lower portion of an image (the coffee table).
    Returns an L-mode mask.
    """
    import numpy as np
    arr = np.array(img.convert("RGB"))
    h, w, _ = arr.shape
    y_start = int(h * y_start_frac)
    mask = np.zeros((h, w), dtype=np.uint8)
    region = arr[y_start:, :, :]
    # bright + desaturated white-ish
    r, g, b = region[..., 0], region[..., 1], region[..., 2]
    bright = (r > 200) & (g > 200) & (b > 200)
    sat_range = (np.max(region, axis=-1).astype(int) - np.min(region, axis=-1).astype(int)) < 40
    white = (bright & sat_range).astype(np.uint8) * 255
    mask[y_start:, :] = white
    table_mask = Image.fromarray(mask, "L")
    # Soften edges
    table_mask = table_mask.filter(ImageFilter.MaxFilter(7))  # dilate slightly
    table_mask = table_mask.filter(ImageFilter.GaussianBlur(8))
    return table_mask


def apply_refraction(panel: Image.Image, side: str) -> Image.Image:
    """Slight horizontal pixel shift near the glass edge to simulate refraction.
    side='right' shifts pixels in the rightmost ~80px band; 'left' the leftmost.
    """
    p = panel.copy()
    band_w = 80
    if side == "right":
        band = p.crop((p.width - band_w, 0, p.width, p.height))
        # Shift band slightly inward by warping
        shifted = Image.new("RGB", band.size, (0, 0, 0))
        shifted.paste(band.resize((band_w - 4, band.height), Image.LANCZOS), (2, 0))
        # Blur very slightly
        shifted = shifted.filter(ImageFilter.GaussianBlur(0.6))
        p.paste(shifted, (p.width - band_w, 0))
    elif side == "left":
        band = p.crop((0, 0, band_w, p.height))
        shifted = Image.new("RGB", band.size, (0, 0, 0))
        shifted.paste(band.resize((band_w - 4, band.height), Image.LANCZOS), (2, 0))
        shifted = shifted.filter(ImageFilter.GaussianBlur(0.6))
        p.paste(shifted, (0, 0))
    elif side == "both":
        p = apply_refraction(p, "left")
        p = apply_refraction(p, "right")
    return p


def color_unify(img: Image.Image) -> Image.Image:
    """Subtle pass: lift saturation slightly + tiny contrast bump for cohesion."""
    img = ImageEnhance.Color(img).enhance(1.05)
    img = ImageEnhance.Contrast(img).enhance(1.04)
    return img


def main():
    # Load
    p1 = Image.open(HERE / "src_1_whiteboard.jpg").convert("RGB")
    p2 = Image.open(HERE / "src_2_coffee.jpg").convert("RGB")
    p3 = Image.open(HERE / "src_3_lola.jpg").convert("RGB")

    # Each panel is OVERSIZED beyond its slot so it can bleed into the neighbor.
    BLEED = 140  # px of overlap into adjacent panel
    FEATHER = 200  # px feathering zone (gentle blend)
    # Less feather on panel 2's right side so Sai's left shoulder bleed is reduced
    FEATHER_P2_RIGHT = 90

    # Panel 1: 640 + 140 wider (only right bleeds), placed at x=0
    panel1 = fit_panel(p1, PANEL_W + BLEED, H, focus_x=0.42, focus_y=0.5)
    # Panel 2: 640 + 2*140 (both sides bleed), placed centered around 960
    panel2 = fit_panel(p2, PANEL_W + 2 * BLEED, H, focus_x=0.5, focus_y=0.42)
    # Panel 3: 640 + 140 (only left bleeds), placed at x=1280-140
    panel3 = fit_panel(p3, PANEL_W + BLEED, H, focus_x=0.55, focus_y=0.5)

    # Color cohesion
    panel1 = color_unify(panel1)
    panel2 = color_unify(panel2)
    panel3 = color_unify(panel3)

    # Build whiteboard-only mask for panel 1:
    # combined (Sai + whiteboard) MINUS human-only (Sai) = just the whiteboard
    print("Running rembg combined on panel 1...")
    sess_general = new_session("u2net")
    mask1_combined = get_fg_mask(panel1, sess_general, soften=2)
    print("Running rembg human-seg on panel 1...")
    sess_human = new_session("u2net_human_seg")
    mask1_human = get_fg_mask(panel1, sess_human, soften=2)
    # Sai in panel 2 (coffee shot) — rotoscope him so his body doesn't bleed into LOLA
    print("Running rembg human-seg on panel 2...")
    mask2_human_raw = get_fg_mask(panel2, sess_human, soften=0)
    # Hard threshold + dilate to cover the underlying soft fringe, then 1px edge soften
    mask2_human = mask2_human_raw.point(lambda v: 255 if v > 100 else 0)
    mask2_human = mask2_human.filter(ImageFilter.MaxFilter(5))  # dilate ~2px
    mask2_human = mask2_human.filter(ImageFilter.GaussianBlur(1.0))
    mask2_human.save(HERE / "debug_mask2_human.png")
    # Whiteboard = combined - human (dilate human aggressively so we don't leave a halo around him)
    from PIL import ImageChops
    import numpy as np
    mask1_human_dilated = mask1_human.filter(ImageFilter.MaxFilter(31))
    whiteboard_mask = ImageChops.subtract(mask1_combined, mask1_human_dilated)
    whiteboard_mask = whiteboard_mask.point(lambda v: 255 if v > 120 else 0)

    # Restrict to the whiteboard easel's actual region — upper right diagonal band only.
    # Excludes: chair/pants (lower-left), TV cabinet (lower-right under whiteboard).
    w_arr = np.array(whiteboard_mask)
    h_, w_ = w_arr.shape
    yy, xx = np.indices((h_, w_))
    keep = (xx > 0.35 * w_) & (yy < 0.62 * h_)
    w_arr[~keep] = 0

    # Make the INTERIOR fully solid (no see-through blotches from semi-transparent pixels).
    # Erode → that's the "core" → set to 255. Outside core but inside original → soft edge only.
    whiteboard_mask_solid = Image.fromarray(w_arr, "L")
    core = whiteboard_mask_solid.filter(ImageFilter.MinFilter(7))  # erode 3px
    core_arr = np.array(core)
    w_arr = np.where(core_arr > 0, 255, w_arr).astype(np.uint8)

    # Fade the right edge slightly (where bottom-right corner was rough)
    fade_right_px = 40
    for x in range(fade_right_px):
        scale = x / fade_right_px
        col = w_ - 1 - x
        w_arr[:, col] = (w_arr[:, col].astype(float) * scale).astype(np.uint8)

    whiteboard_mask = Image.fromarray(w_arr, "L")
    # Light overall edge softening (1px only — avoid soft fall-off in interior)
    whiteboard_mask = whiteboard_mask.filter(ImageFilter.GaussianBlur(1))
    whiteboard_mask.save(HERE / "debug_whiteboard_mask.png")

    # Feather the edges normally — Sai bleeds into neighbors like the rest of the scene
    panel1_feathered = feather_edge(panel1, "right", FEATHER)
    panel2_feathered = feather_edge(panel2, "left", FEATHER)
    panel2_feathered = feather_edge(panel2_feathered, "right", FEATHER_P2_RIGHT)
    panel3_feathered = feather_edge(panel3, "left", FEATHER)

    # Lift panel2's alpha to 255 wherever Sai is, so he stays fully opaque even in the feather zone.
    # This kills the halo: no double-compositing, no underlying soft edge to show around Sai.
    p2_alpha = panel2_feathered.split()[-1]
    new_alpha = ImageChops.lighter(p2_alpha, mask2_human)
    panel2_feathered.putalpha(new_alpha)

    # Composite: paste panel1, then panel2 over it, then panel3 over both
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    canvas.alpha_composite(panel1_feathered, (0, 0))
    canvas.alpha_composite(panel2_feathered, (PANEL_W - BLEED, 0))
    canvas.alpha_composite(panel3_feathered, (PANEL_W * 2 - BLEED, 0))

    # Top layer 1: whiteboard easel (rotoscoped from panel 1)
    panel1_whiteboard = Image.new("RGBA", panel1.size, (0, 0, 0, 0))
    panel1_whiteboard.paste(panel1.convert("RGBA"), (0, 0), whiteboard_mask)
    # Blur the TOP portion of the whiteboard layer with a HORIZONTAL motion blur,
    # then fade alpha so the top dissolves into the panel evenly across the width.
    top_blur_h = 220  # height of blur region from top
    top_region = panel1_whiteboard.crop((0, 0, panel1_whiteboard.width, top_blur_h))
    # Horizontal-dominant blur: large x-radius, small y-radius
    blurred_top = top_region.filter(ImageFilter.GaussianBlur(radius=18))
    # Add horizontal motion smear by averaging shifted copies
    smeared = Image.new("RGBA", top_region.size, (0, 0, 0, 0))
    for dx in range(-30, 31, 10):
        shifted = Image.new("RGBA", top_region.size, (0, 0, 0, 0))
        shifted.paste(blurred_top, (dx, 0), blurred_top)
        smeared = Image.alpha_composite(smeared, shifted)
    # Apply vertical alpha gradient (gentle, full top_blur_h height)
    grad = Image.new("L", top_region.size, 0)
    g_arr = np.array(grad)
    for y in range(top_blur_h):
        g_arr[y, :] = int(255 * (y / top_blur_h) ** 1.5)
    grad = Image.fromarray(g_arr, "L")
    # Multiply smeared alpha by gradient
    smeared_alpha = smeared.split()[-1]
    from PIL import ImageChops
    new_alpha = ImageChops.multiply(smeared_alpha, grad)
    smeared.putalpha(new_alpha)
    # Replace top region of whiteboard layer with smeared version
    panel1_whiteboard.paste(smeared, (0, 0), smeared)
    canvas.alpha_composite(panel1_whiteboard, (0, 0))

    # No top-layer sharp Sai — he's already at 255 alpha in the underlying panel2 (above).
    # Single layer = no halo / drop-shadow.

    # Whisper of glass edge at each seam
    edge = make_glass_edge_hint(H, width=3)
    canvas.alpha_composite(edge, (PANEL_W - 1, 0))
    canvas.alpha_composite(edge, (PANEL_W * 2 - 1, 0))

    out = canvas.convert("RGB")
    out_path = HERE / "thumbnail.jpg"
    out.save(out_path, "JPEG", quality=95)
    print(f"Saved -> {out_path}")
    print(f"Size: {out.size}")


if __name__ == "__main__":
    main()
