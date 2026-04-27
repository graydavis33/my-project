"""Audio-offset detection via scipy cross-correlation.

Returns the seconds you must add to an A-cam timestamp to get the
equivalent B-cam timestamp. If B started rolling 2.0s after A, the
returned offset is -2.0 (B's t=0 is 2s after A's t=0, so an A-cam
event at t=5 maps to B-cam t=3).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import correlate


def compute_offset(a_wav: Path, b_wav: Path, window_s: float = 30.0) -> float:
    sr_a, a = wavfile.read(str(a_wav))
    sr_b, b = wavfile.read(str(b_wav))

    if sr_a != sr_b:
        raise ValueError(f"Sample rate mismatch: A={sr_a} B={sr_b}")

    if a.ndim > 1:
        a = a.mean(axis=1)
    if b.ndim > 1:
        b = b.mean(axis=1)

    n = int(window_s * sr_a)
    a = a[:n].astype(np.float32)
    b = b[:n].astype(np.float32)

    a -= a.mean()
    b -= b.mean()

    corr = correlate(b, a, mode="full", method="fft")
    lag_samples = int(np.argmax(corr)) - (len(a) - 1)
    offset_s = -lag_samples / sr_a
    return offset_s


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python sync.py <a.wav> <b.wav>")
        sys.exit(2)
    print(f"{compute_offset(Path(sys.argv[1]), Path(sys.argv[2])):+.4f}")
