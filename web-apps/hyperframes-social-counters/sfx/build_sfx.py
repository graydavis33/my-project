"""
Build per-platform sound effects for the HyperFrames social counters.

Three SFX components per track, timed to the GSAP timeline:
  - 0.10s : logo entrance whoosh / pop
  - 0.40s : counter glyph click
  - 0.60s..3.00s : tick sequence eased to power2.out (fast -> slow)
  - 3.00s : landing ding (platform-flavored)

Output: 4.00s stereo WAV at 48 kHz in renders/, plus copies to
D:/Sai/06_ASSETS/Visual Effects/Social Counters/ to match the MP4 destination.
"""

import sys
import shutil
import math
from pathlib import Path

import numpy as np
from scipy.io import wavfile

sys.stdout.reconfigure(encoding="utf-8")

SR = 48000
DURATION = 4.0
N = int(SR * DURATION)
HERE = Path(__file__).resolve().parent
RENDERS = HERE.parent / "renders"
SAI_DEST = Path("D:/Sai/06_ASSETS/Sound Effects/Social Counters")
RENDERS.mkdir(parents=True, exist_ok=True)


def empty_stereo() -> np.ndarray:
    return np.zeros((N, 2), dtype=np.float32)


def add_mono(buf: np.ndarray, mono: np.ndarray, start: float, pan: float = 0.0, gain: float = 1.0):
    """Mix a mono signal into the stereo buffer at 'start' seconds. pan in [-1,1]."""
    i0 = int(start * SR)
    i1 = min(i0 + mono.shape[0], N)
    if i0 >= N:
        return
    seg = mono[: i1 - i0] * gain
    l_gain = math.cos((pan + 1) * math.pi / 4)
    r_gain = math.sin((pan + 1) * math.pi / 4)
    buf[i0:i1, 0] += seg * l_gain
    buf[i0:i1, 1] += seg * r_gain


def env_exp(n: int, attack: float = 0.005, decay: float = 0.12) -> np.ndarray:
    t = np.arange(n) / SR
    atk = np.clip(t / max(attack, 1e-6), 0, 1)
    dec = np.exp(-(np.maximum(t - attack, 0)) / max(decay, 1e-6))
    return (atk * dec).astype(np.float32)


def sine(freq: float, n: int, phase: float = 0.0) -> np.ndarray:
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * freq * t + phase).astype(np.float32)


def sweep(f0: float, f1: float, n: int) -> np.ndarray:
    t = np.arange(n) / SR
    k = (f1 - f0) / (n / SR)
    phase = 2 * np.pi * (f0 * t + 0.5 * k * t * t)
    return np.sin(phase).astype(np.float32)


def noise(n: int) -> np.ndarray:
    rng = np.random.default_rng(seed=42)
    return rng.standard_normal(n).astype(np.float32)


def lp_one_pole(x: np.ndarray, cutoff: float) -> np.ndarray:
    """Simple one-pole lowpass, in-place safe."""
    a = math.exp(-2 * math.pi * cutoff / SR)
    y = np.empty_like(x)
    prev = 0.0
    for i, v in enumerate(x):
        prev = (1 - a) * v + a * prev
        y[i] = prev
    return y


def hp_one_pole(x: np.ndarray, cutoff: float) -> np.ndarray:
    return x - lp_one_pole(x, cutoff)


# --- elemental SFX builders ---


def whoosh(dur: float = 0.35, f0: float = 200, f1: float = 1800, color: str = "bright") -> np.ndarray:
    n = int(dur * SR)
    swp = sweep(f0, f1, n)
    nz = noise(n)
    if color == "warm":
        nz = lp_one_pole(nz, 3500)
    elif color == "bold":
        nz = lp_one_pole(nz, 2200)
    else:  # bright
        nz = hp_one_pole(nz, 800)
        nz = lp_one_pole(nz, 6000)
    env = env_exp(n, attack=0.01, decay=dur * 0.35)
    return (0.55 * swp + 0.45 * nz) * env


def click(freq: float = 1400, dur: float = 0.06) -> np.ndarray:
    n = int(dur * SR)
    s = sine(freq, n) + 0.5 * sine(freq * 2.01, n)
    env = env_exp(n, attack=0.001, decay=0.04)
    return (s * env).astype(np.float32)


def tick(freq: float, dur: float = 0.012) -> np.ndarray:
    """Digital UI beep — fixed high-freq sine, tight envelope, no pitch drift.

    Reads like a calculator key / stock ticker / Geiger counter, not a wood block.
    """
    n = int(dur * SR)
    t = np.arange(n) / SR
    # Pure fixed-frequency sine — no glide, no harmonics that add melody
    tone = np.sin(2 * np.pi * freq * t).astype(np.float32)
    # 0.4 ms hard noise transient for the "press" sensation
    trans_n = int(0.0004 * SR)
    rng = np.random.default_rng(seed=int(freq) & 0xFFFF)
    transient = rng.standard_normal(trans_n).astype(np.float32)
    transient *= np.linspace(1.0, 0.0, trans_n)
    out = tone.copy()
    out[:trans_n] += transient * 0.6
    # Very tight envelope — 0.3 ms attack, 6 ms decay
    env = env_exp(n, attack=0.0003, decay=0.006)
    return (out * env).astype(np.float32)


def ding(freqs, dur: float = 1.1, decay: float = 0.7) -> np.ndarray:
    n = int(dur * SR)
    out = np.zeros(n, dtype=np.float32)
    env = env_exp(n, attack=0.004, decay=decay)
    for i, f in enumerate(freqs):
        # Slight per-partial detune adds shimmer
        detune = 1.0 + 0.0008 * (i - len(freqs) / 2)
        out += sine(f * detune, n) * (0.9 ** i)
    out *= env
    # Light "bloom" via short delay
    delay_n = int(0.018 * SR)
    bloom = np.zeros_like(out)
    bloom[delay_n:] = out[:-delay_n] * 0.35
    return (out + bloom).astype(np.float32)


# --- time mapping for the counter tick sequence ---
# GSAP power2.out: progress(t) = 1 - (1-t)^2, t in [0,1]
# We want ticks evenly spaced in PROGRESS so they feel synced to the counter.
# Invert: t = 1 - sqrt(1 - progress).


def tick_times(start: float, dur: float, n_ticks: int) -> list:
    times = []
    for i in range(1, n_ticks + 1):
        p = i / n_ticks
        local = 1 - math.sqrt(1 - p)
        times.append(start + dur * local)
    return times


# --- per-platform patches ---


def build_tiktok() -> np.ndarray:
    buf = empty_stereo()
    # Stereo logo entrance: cyan-back left, magenta-front right
    cyan = whoosh(0.28, 350, 2200, color="bright")
    mag = whoosh(0.28, 280, 1900, color="bright")
    add_mono(buf, cyan, start=0.10, pan=-0.5, gain=0.55)
    add_mono(buf, mag, start=0.12, pan=0.5, gain=0.55)
    # Count glyph click
    add_mono(buf, click(1500, 0.07), start=0.40, pan=0.0, gain=0.55)
    # Ticks — fixed 4200 Hz UI beep, dead-center (no pan jitter)
    for i, t in enumerate(tick_times(0.60, 2.40, 24)):
        add_mono(buf, tick(4200, 0.012), start=t, pan=0.0, gain=0.45)
    return buf


def build_instagram() -> np.ndarray:
    buf = empty_stereo()
    # Warm gradient whoosh
    w = whoosh(0.45, 220, 1400, color="warm")
    add_mono(buf, w, start=0.10, pan=-0.15, gain=0.55)
    w2 = whoosh(0.35, 320, 1100, color="warm")
    add_mono(buf, w2, start=0.18, pan=0.20, gain=0.40)
    # Count glyph — softer pop
    add_mono(buf, click(900, 0.09), start=0.40, pan=0.0, gain=0.45)
    # Ticks — fixed 3600 Hz UI beep, softer level
    for i, t in enumerate(tick_times(0.60, 2.40, 20)):
        add_mono(buf, tick(3600, 0.012), start=t, pan=0.0, gain=0.38)
    return buf


def build_youtube() -> np.ndarray:
    buf = empty_stereo()
    # Bold red-flash whoosh — punchier, lower sweep
    w = whoosh(0.32, 180, 1500, color="bold")
    add_mono(buf, w, start=0.10, pan=0.0, gain=0.65)
    # A small sub-thump on the logo hit
    add_mono(buf, sine(110, int(0.20 * SR)) * env_exp(int(0.20 * SR), 0.005, 0.15), start=0.10, pan=0.0, gain=0.30)
    # Count glyph click — bold
    add_mono(buf, click(1100, 0.08), start=0.40, pan=0.0, gain=0.55)
    # Ticks — fixed 3900 Hz UI beep, dead-center
    for i, t in enumerate(tick_times(0.60, 2.40, 22)):
        add_mono(buf, tick(3900, 0.012), start=t, pan=0.0, gain=0.42)
    return buf


def write_wav(name: str, buf: np.ndarray):
    # Normalize to -3 dBFS peak
    peak = float(np.max(np.abs(buf)))
    if peak > 0:
        buf = buf * (0.707 / peak)
    int16 = np.clip(buf, -1.0, 1.0)
    int16 = (int16 * 32767).astype(np.int16)
    out = RENDERS / name
    wavfile.write(out, SR, int16)
    print(f"  wrote {out}  ({out.stat().st_size / 1024:.1f} KB)")
    if SAI_DEST.exists():
        dest = SAI_DEST / name
        shutil.copy2(out, dest)
        print(f"  copied -> {dest}")
    return out


def main():
    print("Building social counter SFX...")
    write_wav("TikTok-Counter-SFX.wav", build_tiktok())
    write_wav("Instagram-Counter-SFX.wav", build_instagram())
    write_wav("YouTube-Counter-SFX.wav", build_youtube())
    print("Done.")


if __name__ == "__main__":
    main()
