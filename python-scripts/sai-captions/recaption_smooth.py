#!/usr/bin/env python3
"""Re-caption a Sai clip in house style with a SMOOTH ease-in fade (no flicker).

Cross-platform. Lives next to caption.py and imports it as a sibling (no hardcoded
repo path), and auto-selects the transcription engine:
  - Mac / Apple Silicon -> mlx-whisper large-v3 (free, local)
  - Windows / CUDA       -> openai-whisper large-v3 on the GPU
Whichever Whisper is installed gets used; no per-machine edits.

Supersedes the Windows-only copy that used to live at
`<footage>/.../Batch 2/_b2_edit/recaption_smooth.py`.

Each card fades IN cleanly (opacity 0->100, ease-out, + subtle slide-up). NO crossfade
overlap between cards (the source of the flicker). Cards are timed to the ACTUAL spoken
word times (they clear in pauses) so what's on screen matches what he's saying.

Usage:
    python recaption_smooth.py "<src video or audio>" --out "<dest>.mov" [--preview]
"""
import argparse, subprocess, sys, tempfile, types
from pathlib import Path
from PIL import Image

# import the canonical house style (Montserrat SemiBold 72, lowercase-except-I, drop
# shadow) from the sibling caption.py. Stub faster_whisper so its module-level import
# never fails — we supply our own transcribe() and never touch caption's WhisperModel.
sys.modules["faster_whisper"] = types.ModuleType("faster_whisper")
sys.modules["faster_whisper"].WhisperModel = object
sys.path.insert(0, str(Path(__file__).resolve().parent))
import caption as cap  # noqa: E402

W, H = 1080, 1920

# animation
FADE_IN  = 0.16   # s, ease-out fade + slide
FADE_OUT = 0.12   # s, only when a pause follows
SLIDE    = 12     # px upward travel during fade-in
TAIL     = 0.10   # s, hold after the last word before clearing (paused cards)
PAUSE    = 0.30   # s, gap-after >= this => fade the card out and clear (else hold to next)


def ease_out(t):  # cubic
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
    return 1 - (1 - t) ** 3


def media_dur(path):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                       capture_output=True, text=True, check=True)
    return float(o.stdout.strip())


def video_fps(path):
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=r_frame_rate", "-of",
                        "default=noprint_wrappers=1:nokey=1", str(path)],
                       capture_output=True, text=True)
    s = o.stdout.strip()
    if "/" in s:
        n, d = s.split("/"); return float(n) / float(d) if float(d) else 30.0
    return float(s) if s else 30.0


def transcribe(src):
    """Word-level transcript as [(text, start, end)]. Engine auto-selected by platform."""
    work = Path(tempfile.mkdtemp(prefix="recap-asr-"))
    wav = work / "a.wav"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", str(src), "-ac", "1", "-ar", "16000", str(wav)], check=True)
    try:
        import mlx_whisper          # Mac / Apple Silicon
        print("  mlx-whisper large-v3 ...")
        res = mlx_whisper.transcribe(str(wav),
                                     path_or_hf_repo="mlx-community/whisper-large-v3-mlx",
                                     language="en", word_timestamps=True)
        segs = res["segments"]
    except ImportError:
        import whisper             # Windows / CUDA
        print("  whisper large-v3 (cuda) ...")
        model = whisper.load_model("large-v3", device="cuda")
        res = model.transcribe(str(wav), language="en", word_timestamps=True)
        segs = res["segments"]
    words = []
    for seg in segs:
        for w in seg.get("words", []):
            t = w["word"].strip()
            if t:
                words.append((t, float(w["start"]), float(w["end"])))
    return words


def build(src, out, preview=False):
    fps = video_fps(src) if str(src).lower().endswith((".mp4", ".mov")) else 24.0
    total = media_dur(src)
    words = transcribe(src)
    cards = cap.group_words(words)
    print(f"  {len(words)} words -> {len(cards)} cards, {fps:.3f}fps, {total:.2f}s")

    work = Path(tempfile.mkdtemp(prefix="recap-smooth-"))
    pngs = cap.render_all_cards(cards, work)
    imgs = [Image.open(p).convert("RGBA") for p, _, _ in pngs]
    alphas = [im.split()[3] for im in imgs]

    # per-card display timing from ACTUAL word times
    info = []
    for i, (cw, _, _) in enumerate(cards):
        info.append({"appear": cw[0][1], "wend": cw[-1][2]})
    for i in range(len(info)):
        nxt = info[i + 1]["appear"] if i + 1 < len(info) else total
        gap = nxt - info[i]["wend"]
        if gap >= PAUSE:
            info[i]["end"] = min(info[i]["wend"] + TAIL, nxt - 0.02)
            info[i]["fade_out"] = True
        else:
            info[i]["end"] = nxt           # hold to next; next HARD-CUTS in (no dip)
            info[i]["fade_out"] = False
    # fade IN only over a blank screen (start, or after a pause where the prev card
    # faded out). Back-to-back cards in continuous speech HARD-CUT at full opacity.
    for i in range(len(info)):
        info[i]["fade_in"] = (i == 0) or info[i - 1]["fade_out"]

    fdir = work / "frames"; fdir.mkdir()
    blank = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nframes = int(round(total * fps))
    for fi in range(nframes):
        t = fi / fps
        k = -1
        for idx, d in enumerate(info):
            if d["appear"] <= t < d["end"]:
                k = idx; break
        if k < 0:
            blank.save(fdir / f"f_{fi:05d}.png"); continue
        d = info[k]
        if d["fade_in"]:
            o_in = ease_out((t - d["appear"]) / FADE_IN)
        else:
            o_in = 1.0                     # hard-cut in at full opacity
        o = o_in
        if d["fade_out"] and t > d["end"] - FADE_OUT:
            o = min(o, ease_out((d["end"] - t) / FADE_OUT))
        yoff = int(round(SLIDE * (1 - o_in)))
        if o >= 0.999 and yoff == 0:
            imgs[k].save(fdir / f"f_{fi:05d}.png"); continue
        canvas = blank.copy()
        card = imgs[k].copy()
        card.putalpha(alphas[k].point(lambda p, o=o: int(p * o)))
        canvas.alpha_composite(card, (0, yoff))
        canvas.save(fdir / f"f_{fi:05d}.png")

    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-framerate", f"{fps}", "-i", str(fdir / "f_%05d.png"),
                    "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                    str(out)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  caption layer -> {out}")

    if preview and str(src).lower().endswith((".mp4", ".mov")):
        pv = out.with_name(out.stem + " - PREVIEW.mp4")
        subprocess.run(["ffmpeg", "-y", "-i", str(src), "-i", str(out),
                        "-filter_complex", "[0:v][1:v]overlay=format=auto",
                        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                        "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
                        str(pv)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  watchable preview -> {pv}")


def main():
    ap = argparse.ArgumentParser(description="Re-caption a Sai short with the SMOOTH no-flicker style.")
    ap.add_argument("src")
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    build(a.src, a.out, a.preview)


if __name__ == "__main__":
    main()
