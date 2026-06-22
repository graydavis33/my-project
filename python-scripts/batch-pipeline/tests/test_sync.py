import sys, numpy as np
from pathlib import Path
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sync

def test_known_offset(tmp_path):
    sr = 48000; rng = np.random.default_rng(0)
    base = rng.standard_normal(sr*10).astype(np.float32)
    lag = int(2.0*sr)                     # B starts 2s "after" -> B leads A by 2s of content
    a = base[lag:]; b = base[:-lag]
    wavfile.write(tmp_path/"a.wav", sr, a)
    wavfile.write(tmp_path/"b.wav", sr, b)
    off = sync.compute_offset(tmp_path/"a.wav", tmp_path/"b.wav")
    assert abs(off - 2.0) < 0.01


def test_verify_offset_known_delay(tmp_path):
    sr = 8000; rng = np.random.default_rng(42)
    dur = 12.0
    n = int(dur * sr)
    # A speech-band burst placed at a known spot, on a quiet noise floor.
    t = np.arange(int(1.5 * sr)) / sr
    burst = (0.8 * np.sin(2 * np.pi * 800 * t * (1 + 0.5 * t))
             + 0.4 * np.sin(2 * np.pi * 1800 * t)).astype(np.float64)

    a = (0.02 * rng.standard_normal(n)).astype(np.float64)
    b = (0.02 * rng.standard_normal(n)).astype(np.float64)
    a_pos = int(3.0 * sr)
    delay = 1.7                      # B's copy of the event lands 1.7s later
    b_pos = a_pos + int(delay * sr)
    a[a_pos:a_pos + len(burst)] += burst
    b[b_pos:b_pos + len(burst)] += burst

    wavfile.write(tmp_path/"a.wav", sr, a.astype(np.float32))
    wavfile.write(tmp_path/"b.wav", sr, b.astype(np.float32))

    res = sync.verify_offset(tmp_path/"a.wav", tmp_path/"b.wav")
    # B event is later -> tB - tA is positive (B's t=0 is earlier in real time,
    # so the shared event sits at a larger B index): lag = b_pos - a_pos.
    assert abs(res["offset"] - delay) < 0.01
    assert res["dominance"] > 3
    assert len(res["candidates"]) == 5
