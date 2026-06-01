import sys
sys.stdout.reconfigure(encoding="utf-8")

import math
import random
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

# =============================================================================
# Tweak these to change the look
# =============================================================================
WIDTH = 1920
HEIGHT = 1080
FPS = 60
DURATION_SECONDS = 1.5
PARTICLE_COUNT = 200

# Where the burst originates (defaults to center — behind a centered logo)
EMIT_X = WIDTH / 2
EMIT_Y = HEIGHT / 2

# Physics
BURST_SPEED_MIN = 18
BURST_SPEED_MAX = 40
UPWARD_BIAS = 8          # initial upward kick (pixels/frame)
GRAVITY = 0.8            # downward acceleration per frame
AIR_DRAG = 0.99          # velocity multiplier per frame (< 1 slows particles)

# Particle shape
PARTICLE_WIDTH_RANGE = (14, 28)
PARTICLE_HEIGHT_RANGE = (7, 14)
ROTATION_SPEED_RANGE = (-20, 20)

# Classic confetti palette
COLORS = [
    (255, 59, 59),     # red
    (255, 193, 59),    # gold
    (59, 193, 255),    # blue
    (59, 255, 115),    # green
    (255, 105, 180),   # pink
    (255, 140, 0),     # orange
    (147, 112, 219),   # purple
    (255, 255, 255),   # white
]

OUTPUT_DIR = Path(__file__).parent / "output" / "confetti_burst_frames"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MOV_PATH = OUTPUT_DIR.parent / "confetti_burst.mov"


class Particle:
    def __init__(self):
        self.x = EMIT_X
        self.y = EMIT_Y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(BURST_SPEED_MIN, BURST_SPEED_MAX)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - UPWARD_BIAS
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(*ROTATION_SPEED_RANGE)
        self.color = random.choice(COLORS)
        self.w = random.randint(*PARTICLE_WIDTH_RANGE)
        self.h = random.randint(*PARTICLE_HEIGHT_RANGE)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += GRAVITY
        self.vx *= AIR_DRAG
        self.vy *= AIR_DRAG
        self.rotation += self.rotation_speed


def render():
    total_frames = int(FPS * DURATION_SECONDS)
    particles = [Particle() for _ in range(PARTICLE_COUNT)]
    fade_start = int(total_frames * 0.70)

    print(f"Rendering {total_frames} frames at {WIDTH}x{HEIGHT} ({PARTICLE_COUNT} particles)...")

    for frame in range(total_frames):
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))

        if frame >= fade_start:
            alpha_mult = 1.0 - (frame - fade_start) / (total_frames - fade_start)
        else:
            alpha_mult = 1.0

        for p in particles:
            pad = max(p.w, p.h) + 4
            tile = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
            td = ImageDraw.Draw(tile)
            cx, cy = pad, pad
            alpha = int(255 * alpha_mult)
            td.rectangle(
                [cx - p.w / 2, cy - p.h / 2, cx + p.w / 2, cy + p.h / 2],
                fill=(*p.color, alpha),
            )
            tile = tile.rotate(p.rotation, resample=Image.BILINEAR)
            img.paste(tile, (int(p.x - pad), int(p.y - pad)), tile)

        img.save(OUTPUT_DIR / f"frame_{frame:04d}.png")

        for p in particles:
            p.update()

        if (frame + 1) % 15 == 0 or frame == total_frames - 1:
            print(f"  frame {frame+1}/{total_frames}")

    print(f"\nPNG sequence saved to: {OUTPUT_DIR}")

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(OUTPUT_DIR / "frame_%04d.png"),
        "-c:v", "prores_ks",
        "-profile:v", "4444",
        "-pix_fmt", "yuva444p10le",
        str(MOV_PATH),
    ]
    print("\nConverting to ProRes 4444 (.mov with alpha channel)...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"\nDone. Drop this into Premiere:\n  {MOV_PATH}")
    except FileNotFoundError:
        print("\nffmpeg not found. Run manually:")
        print("  " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
    except subprocess.CalledProcessError as e:
        print(f"\nffmpeg failed:\n{e.stderr}")


if __name__ == "__main__":
    render()
