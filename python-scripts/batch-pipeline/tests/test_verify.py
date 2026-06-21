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

def test_clip_detection_float32_wav(tmp_path):
    """Float32 WAV (±1.0 scale, amplitude ~0.5) must still detect a mid-word cut as clipped.

    Without the float-scale guard, every RMS would be ~0.01-0.35, never exceed
    the 700 threshold, and the gate would silently pass — a false negative.
    With the guard, the array is scaled to int16 magnitude before the RMS check.
    """
    sr = 48000
    a = np.zeros(int(5 * sr), dtype=np.float32)
    rng = np.random.default_rng(42)
    # Amplitude ~0.5 in ±1.0 float scale — equivalent to ~16000 in int16 scale
    # Clip to ±1.0 so max(abs) stays within the float-WAV normalized range.
    # standard_normal has outliers beyond ±2σ, so multiply then clip keeps the
    # array in ±1.0 while still producing RMS well above the scaled threshold.
    noise = (0.5 * rng.standard_normal(int(0.5 * sr))).astype(np.float32)
    a[int(1.0 * sr):int(1.5 * sr)] = np.clip(noise, -1.0, 1.0)
    wav = tmp_path / "lav_float32.wav"
    wavfile.write(wav, sr, a)  # scipy writes float32 as a float WAV
    # cut at 1.25 = mid-word → should be detected as clipped (ok=False)
    # cut at 1.80 = silence → should be clean (ok=True)
    res = verify.check_no_clips(wav, [1.25, 1.80])
    assert res[0]["ok"] is False, "float32 wav: mid-word cut must be flagged as clipped"
    assert res[1]["ok"] is True, "float32 wav: silence cut must be clean"
