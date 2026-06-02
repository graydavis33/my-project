"""
NBA arena buzzer beater — procedural synthesis.

Anatomy:
  0.00 - 0.30s : silence (lead-in)
  0.30 - 0.38s : 80ms attack ramp on the horn
  0.38 - 2.10s : sustained horn body
  2.10 - 2.80s : 700ms exponential decay to silence (the "die-off")
  2.80 - 3.10s : silence (tail)

Synthesis recipe (the "electric horn" character):
  - Three detuned square voices at 220 / 222 / 224 Hz -> thick "beating" thickness
  - Light saw layer at the fundamental + octave -> bright top edge
  - Sine harmonics at 3x and 5x -> the "wail"
  - 4 Hz / +-0.3% vibrato -> arena PA system wobble
  - tanh soft-clip -> "blown out / overdriven" PA character
  - 3 delayed taps (35 / 67 / 110 ms) -> rough arena reverb

Output:
  D:/Sai/06_ASSETS/SFX/buzzer-beater.wav  (48 kHz stereo, normalized to ~-1 dBFS)
  D:/Sai/06_ASSETS/SFX/buzzer-beater.mp3  (320k VBR for quick use)
"""

import sys
import subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile

sys.stdout.reconfigure(encoding="utf-8")

SR = 48000
INTRO = 0.30
BODY = 1.80
DECAY = 0.70
OUTRO = 0.30
TOTAL = INTRO + BODY + DECAY + OUTRO

OUT_DIR = Path("D:/Sai/06_ASSETS/SFX")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def build_buzzer() -> np.ndarray:
    n = int((BODY + DECAY) * SR)
    t = np.arange(n) / SR

    # Slow vibrato — real arena horns have a tiny pitch wobble
    vib = 1.0 + 0.003 * np.sin(2 * np.pi * 4.0 * t)
    phase220 = 2 * np.pi * 220.0 * t * vib
    phase222 = 2 * np.pi * 222.0 * t * vib
    phase224 = 2 * np.pi * 224.0 * t * vib

    # Three detuned square voices -> thick beating
    sq1 = 0.36 * np.sign(np.sin(phase220))
    sq2 = 0.36 * np.sign(np.sin(phase222))
    sq3 = 0.22 * np.sign(np.sin(phase224))

    # Saw layer for top-end brightness
    def saw(freq):
        x = freq * t * vib
        return 2 * (x - np.floor(0.5 + x))

    sw1 = 0.10 * saw(220.0)
    sw2 = 0.07 * saw(440.0)

    # Sine harmonics — adds the "wail"
    h3 = 0.09 * np.sin(2 * np.pi * 660.0 * t)
    h5 = 0.05 * np.sin(2 * np.pi * 1100.0 * t)
    h7 = 0.02 * np.sin(2 * np.pi * 1540.0 * t)

    sig = sq1 + sq2 + sq3 + sw1 + sw2 + h3 + h5 + h7

    # Envelope: attack ramp + sustain + exponential decay
    attack_n = int(0.08 * SR)
    body_n = int(BODY * SR) - attack_n
    decay_n = int(DECAY * SR)
    env = np.ones(n, dtype=np.float32)
    env[:attack_n] = np.linspace(0.0, 1.0, attack_n) ** 1.5  # slight curve in
    decay_start = attack_n + body_n
    tau = DECAY / 4.0  # e^-4 ~ 0.018 by end of decay
    env[decay_start:] = np.exp(-(np.arange(decay_n) / SR) / tau)
    sig = (sig * env).astype(np.float32)

    # Soft clip — that "blown PA" overdriven character
    sig = np.tanh(sig * 1.45) / np.tanh(1.45)
    return sig


def add_reverb(x: np.ndarray) -> np.ndarray:
    taps = [(int(0.035 * SR), 0.22), (int(0.067 * SR), 0.14), (int(0.110 * SR), 0.08)]
    out = x.copy()
    for d, g in taps:
        tail = np.zeros_like(x)
        tail[d:] = x[:-d] * g
        out += tail
    return out


def assemble() -> np.ndarray:
    mono = add_reverb(build_buzzer())
    total_n = int(TOTAL * SR)
    buf = np.zeros((total_n, 2), dtype=np.float32)
    start_n = int(INTRO * SR)
    end_n = start_n + mono.shape[0]
    # Slight stereo width: tiny L/R gain offset (true mono content, perceived width via reverb)
    buf[start_n:end_n, 0] = mono * 0.97
    buf[start_n:end_n, 1] = mono * 1.00
    # Normalize to -1 dBFS peak
    peak = float(np.max(np.abs(buf)))
    if peak > 0:
        buf *= 0.89 / peak
    return buf


def write_wav(buf: np.ndarray, path: Path):
    int16 = (np.clip(buf, -1.0, 1.0) * 32767).astype(np.int16)
    wavfile.write(path, SR, int16)
    print(f"  wrote {path}  ({path.stat().st_size / 1024:.1f} KB, {TOTAL:.2f}s)")


def write_mp3(wav_path: Path, mp3_path: Path):
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path),
         "-c:a", "libmp3lame", "-q:a", "2", str(mp3_path)],
        check=True,
    )
    print(f"  wrote {mp3_path}  ({mp3_path.stat().st_size / 1024:.1f} KB)")


def main():
    print("Building NBA buzzer beater...")
    buf = assemble()
    wav = OUT_DIR / "buzzer-beater.wav"
    mp3 = OUT_DIR / "buzzer-beater.mp3"
    write_wav(buf, wav)
    write_mp3(wav, mp3)
    print("Done.")


if __name__ == "__main__":
    main()
