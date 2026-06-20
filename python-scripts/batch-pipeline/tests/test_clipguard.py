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
