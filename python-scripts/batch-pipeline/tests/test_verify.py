import sys, numpy as np
from pathlib import Path
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify

def test_clip_detection(tmp_path):
    sr = 48000; a = np.zeros(int(5*sr), dtype=np.float32)
    rng = np.random.default_rng(0)
    a[int(1.0*sr):int(1.5*sr)] = 20000*rng.standard_normal(int(0.5*sr))  # word 1.0-1.5
    wav = tmp_path/"lav.wav"; wavfile.write(wav, sr, a)
    # cut-out at 1.25 = mid-word (clip); at 1.80 = silence (clean)
    res = verify.check_no_clips(wav, [1.25, 1.80])
    assert res[0]["ok"] is False and res[1]["ok"] is True
