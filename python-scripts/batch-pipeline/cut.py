import json, subprocess, tempfile
from pathlib import Path
import numpy as np
from scipy.io import wavfile
import clipguard, config

HEAD, TAIL = 0.10, 0.25

def plan(words, ranges, audio, sr):
    keep, caps, cum, synced_outs = [], [], 0.0, []
    for (sin, sout, head, tail) in ranges:
        head = HEAD if head is None else head
        lo = sin - head
        nxt = next((w["start"] for w in words if w["start"] >= sout - 1e-6), None)
        hi = clipguard.snap_out(audio, sr, sout, nxt)
        dur = hi - lo
        for w in [w for w in words if w["start"] < sout and w["end"] > sin]:
            caps.append({"start": round(cum + (w["start"]-lo), 3),
                         "end": round(cum + (w["end"]-lo), 3), "word": w["word"]})
        keep.append((lo, dur)); synced_outs.append(hi); cum += dur
    return keep, caps, cum, synced_outs

def _extract(video_src, lav_wav, start, dur, dst):
    subprocess.run(["ffmpeg","-y","-ss",f"{start:.4f}","-i",str(video_src),
        "-ss",f"{start:.4f}","-i",str(lav_wav),"-t",f"{dur:.4f}",
        "-map","0:v","-map","1:a","-r",config.FPS,"-vsync","cfr",*config.PRORES422,
        "-c:a","aac","-b:a","256k","-ar","48000",str(dst)], check=True, capture_output=True)

def _concat(parts, dst):
    lf = dst.parent / (dst.stem + "_list.txt")
    lf.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts))
    subprocess.run(["ffmpeg","-y","-fflags","+genpts","-f","concat","-safe","0","-i",str(lf),
        "-r",config.FPS,*config.PRORES422,"-c:a","aac","-b:a","256k","-ar","48000",
        "-movflags","+faststart",str(dst)], check=True, capture_output=True)
    lf.unlink()

def build_cut(synced_a, synced_b, lav_wav, words, ranges, out_dir, vid_tag):
    out_dir.mkdir(parents=True, exist_ok=True)
    sr, audio = wavfile.read(str(lav_wav)); audio = audio.astype(np.float32)
    keep, caps, total, synced_outs = plan(words, ranges, audio, sr)
    (out_dir/"caption_words.json").write_text(json.dumps(caps, indent=1), encoding="utf-8")
    res = {"caption_words": out_dir/"caption_words.json", "total_s": total, "synced_outs": synced_outs}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for cam, src in (("A", synced_a), ("B", synced_b)):
            parts = []
            for i,(lo,dur) in enumerate(keep):
                p = td/f"{cam}_{i:02d}.mov"; _extract(src, lav_wav, lo, dur, p); parts.append(p)
            dst = out_dir/f"{vid_tag}_{cam}-cam_CUT.mov"; _concat(parts, dst); res[cam.lower()] = dst
    return res
