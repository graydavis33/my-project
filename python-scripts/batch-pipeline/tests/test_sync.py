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
