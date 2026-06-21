import subprocess
import numpy as np
from scipy.io import wavfile

def _rms(a, sr, t, win=0.06):
    s = a[int(t*sr):int((t+win)*sr)]; return float(np.sqrt(np.mean(s**2))) if len(s) else 0.0

def check_no_clips(lav_wav, synced_outs):
    sr, a = wavfile.read(str(lav_wav)); a = a.astype(np.float32)
    out = []
    for t in synced_outs:
        inside, after = _rms(a, sr, t-0.06), _rms(a, sr, t)
        out.append({"t": t, "inside": inside, "after": after,
                    "ok": not (inside > 700 and after > 700)})
    return out

def decode_clean(path):
    r = subprocess.run(["ffmpeg","-v","error","-i",str(path),"-f","null","-"],
                       capture_output=True, text=True)
    return r.returncode == 0 and not r.stderr.strip()

def _dur(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=nk=1:nw=1",str(path)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())

def same_length(a, b, tol=0.05):
    return abs(_dur(a) - _dur(b)) <= tol

def audio_md5(path):
    r = subprocess.run(["ffmpeg","-v","error","-i",str(path),"-map","0:a",
        "-ar","48000","-ac","1","-f","md5","-"], capture_output=True, text=True, check=True)
    return r.stdout.strip()

def gate(a_cut, b_cut, lav_wav, synced_outs):
    clips = check_no_clips(lav_wav, synced_outs)
    res = {"clips": clips, "a_decode": decode_clean(a_cut), "b_decode": decode_clean(b_cut),
           "length_match": same_length(a_cut, b_cut),
           "audio_match": audio_md5(a_cut) == audio_md5(b_cut)}
    res["passed"] = (all(c["ok"] for c in clips) and res["a_decode"] and res["b_decode"]
                     and res["length_match"] and res["audio_match"])
    return res
