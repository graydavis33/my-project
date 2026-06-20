import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import clipguard

def _env(sr, segments):  # segments: list of (start, end, amp)
    a = np.zeros(int(8*sr), dtype=np.float32)
    rng = np.random.default_rng(0)
    for s, e, amp in segments:
        n = int((e-s)*sr); a[int(s*sr):int(s*sr)+n] = amp*rng.standard_normal(n)
    return a

def test_rings_out_then_cuts_in_the_dip():
    sr = 48000
    # word marked end at 1.00, but energy rings to 1.20; dip 1.20-1.30; loud breath 1.30-1.45
    a = _env(sr, [(0.0,1.20,0.3),(1.30,1.45,0.6)])
    out = clipguard.snap_out(a, sr, sout=1.00, next_word_start=None)
    assert 1.18 < out < 1.31   # cut in the dip, not mid-ring, not into the breath

def test_never_passes_next_word():
    sr = 48000
    a = _env(sr, [(0.0,1.05,0.3),(1.10,1.40,0.4)])
    out = clipguard.snap_out(a, sr, sout=1.00, next_word_start=1.10)
    assert out <= 1.08

def test_rms_window_does_not_spill_past_hard_cap():
    # Regression: without the fix, a candidate at t near hard_cap reads
    # audio[t : t+0.06], spilling PAST hard_cap into the next word's onset.
    # If the next-word onset is very quiet, that candidate gets a lower RMS
    # than any candidate whose window is fully inside [sout, hard_cap], so
    # snap_out returns a value at/near hard_cap even though there's a genuine
    # louder-but-still-quieter-than-pre-dip region INSIDE the legal window.
    #
    # Concrete setup (sr=48000):
    #   sout=1.00, next_word_start=1.30  →  hard_cap = 1.28
    #   Audio layout:
    #     1.00-1.16  loud ring  (amp 0.8)
    #     1.16-1.28  medium hiss (amp 0.15) — this IS the quietest legal zone
    #     1.28-1.60  near-silence (amp 0.001) — OUTSIDE hard_cap, next-word onset
    #
    #   Without fix: candidate at t=1.22 reads [1.22, 1.28] + spills into
    #     [1.28, 1.28]  → but that's fine. Candidate at t=1.26 reads [1.26,1.32]
    #     which includes 2 frames of near-silence → its RMS drops below the
    #     medium-hiss candidates → snap_out returns 1.26 (near hard_cap).
    #     More precisely, any candidate t where t+0.06 > 1.28 pulls in the
    #     near-zero audio and appears artificially quiet.
    #   With fix: window clamped at hard_cap=1.28 for all candidates; the medium
    #     hiss is uniformly the quietest zone found in the legal range; the first
    #     candidate that enters it (t=1.16) wins → result << hard_cap.
    sr = 48000
    a = np.zeros(int(8*sr), dtype=np.float32)
    rng = np.random.default_rng(42)
    # loud ring
    n = int(0.16*sr); a[int(1.00*sr):int(1.00*sr)+n] = 0.8*rng.standard_normal(n)
    # medium hiss (quietest inside legal window)
    n = int(0.12*sr); a[int(1.16*sr):int(1.16*sr)+n] = 0.15*rng.standard_normal(n)
    # near-silence OUTSIDE hard_cap (next-word onset)
    n = int(0.32*sr); a[int(1.28*sr):int(1.28*sr)+n] = 0.001*rng.standard_normal(n)

    hard_cap = 1.28  # = 1.30 - 0.02
    out = clipguard.snap_out(a, sr, sout=1.00, next_word_start=1.30)

    # Without fix: candidates at 1.22/1.24/1.26 spill into near-silence past
    # hard_cap and get artificially low RMS → snap_out returns 1.28 (== hard_cap).
    # With fix: windows clamped at hard_cap; the hiss zone [1.16-1.28] is the
    # genuine minimum, best candidate lands at 1.24 (well below hard_cap 1.28).
    # Use 1.25 as the ceiling (midpoint between 1.24 and 1.28) to stay robust
    # to float accumulation while clearly separating the two outcomes.
    assert out < 1.25, (
        f"snap_out returned {out:.4f}, expected < 1.25; "
        "RMS window likely spilled past hard_cap, pulling selection to boundary"
    )
