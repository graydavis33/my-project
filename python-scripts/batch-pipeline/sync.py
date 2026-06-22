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
from scipy.signal import butter, correlate, fftconvolve, resample_poly, sosfiltfilt


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
    # correlate(b, a) peaks at lag D where b[n] = a[n-D], i.e. D = (tB - tA)*sr.
    # The contract (see module docstring) is offset = tB - tA = lag/sr, so that
    # an A-cam timestamp maps to B via A + offset. Do NOT negate here — negating
    # flips the sign and lands every mirrored B segment at A - offset (off by 2x).
    offset_s = lag_samples / sr_a
    return offset_s


def _load_mono_8k(wav_path: Path) -> np.ndarray:
    """Read a WAV, mix to mono, resample to 8000Hz only if needed."""
    sr, x = wavfile.read(str(wav_path))
    x = x.astype(np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    if sr != _VERIFY_SR:
        x = resample_poly(x, _VERIFY_SR, sr)
    return x


_VERIFY_SR = 8000


def verify_offset(a_wav: Path, b_wav: Path) -> dict:
    """Sharper offset detection via bandpassed full-clip cross-correlation.

    Ports the proven manual recipe (_verify_offset.py): bandpass both clips to
    speech (300-3000Hz), normalize, full xcorr, and rank the top candidate lags.
    The correct lag dominates the runner-up when sync is real.

    Returns:
        offset:     float, tB - tA in seconds (same contract as compute_offset)
        peak:       float, normalized correlation peak of the winning lag
        dominance:  float, winner_peak / next_distinct_candidate_peak
        candidates: list of (lag_s, peak) for the top 5 distinct lags
    """
    a = _load_mono_8k(a_wav)
    b = _load_mono_8k(b_wav)

    sos = butter(4, [300 / (_VERIFY_SR / 2), 3000 / (_VERIFY_SR / 2)],
                 btype="band", output="sos")
    a = sosfiltfilt(sos, a)
    b = sosfiltfilt(sos, b)
    a = (a - a.mean()) / (a.std() + 1e-9)
    b = (b - b.mean()) / (b.std() + 1e-9)

    # fftconvolve(b, a[::-1]) peaks at lag D where b[n] = a[n-D], i.e.
    # D = (tB - tA)*sr. offset = tB - tA = lag/sr. Do NOT negate (see the
    # 2x sign-error warning in compute_offset above).
    corr = fftconvolve(b, a[::-1], mode="full")
    norm = np.sqrt((a ** 2).sum() * (b ** 2).sum())
    lags = (np.arange(len(corr)) - (len(a) - 1)) / _VERIFY_SR
    order = np.argsort(corr)[::-1]

    candidates: list[tuple[float, float]] = []
    for idx in order:
        lag_s = float(lags[idx])
        if any(abs(lag_s - s) < 1.0 for s, _ in candidates):
            continue
        candidates.append((lag_s, float(corr[idx] / norm)))
        if len(candidates) >= 5:
            break

    winner_lag, winner_peak = candidates[0]
    runner_up_peak = candidates[1][1] if len(candidates) > 1 else 1e-9
    dominance = winner_peak / (runner_up_peak if runner_up_peak != 0 else 1e-9)

    return {
        "offset": winner_lag,
        "peak": winner_peak,
        "dominance": dominance,
        "candidates": candidates,
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python sync.py <a.wav> <b.wav>")
        sys.exit(2)
    print(f"{compute_offset(Path(sys.argv[1]), Path(sys.argv[2])):+.4f}")
