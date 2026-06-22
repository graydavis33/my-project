"""Render stage: read Cut/SEGMENTS.json (written by prep), build parallel A/B
ProRes reels (frame-locked), a watch preview, remapped caption words, and export
the H.264 deliverable.

Ported from D:/Sai/01_ORGANIZED/Batch_03/Vid_13/_cut_preview.py. Editorial math is
factored into pure helpers (_segment_timing, _caption_remap, _deliverable_folder)
so it can be tested without ffmpeg.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import config

HEAD_DEFAULT = 0.10
TAIL_DEFAULT = 0.25
VF = "scale=1920:1080,setsar=1"
# ProRes 422 per-segment masters (config.PRORES422 = profile 3) + pcm audio for seam-clean concat-copy
PRORES = [*config.PRORES422, "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]


# --- pure editorial helpers (tested without ffmpeg) ------------------------

def _segment_timing(seg: dict, offset: float, head_default=HEAD_DEFAULT, tail_default=TAIL_DEFAULT):
    """Return (b_media, dur, a_media, a_fallback) for one segment.

    b_media = max(0, in - head); dur = (out + tail) - b_media;
    a_media = b_media - offset. If a_media < 0 the A reel falls back to B-cam.
    """
    head = head_default
    tail = seg.get("tail")
    tail = tail_default if tail is None else tail
    b_in, b_out = seg["in"], seg["out"]
    b_media = max(0.0, b_in - head)
    dur = (b_out + tail) - b_media
    a_media = b_media - offset
    return b_media, dur, a_media, a_media < 0


def _caption_remap(words: list, segments: list, offset: float,
                   head_default=HEAD_DEFAULT, tail_default=TAIL_DEFAULT) -> list:
    """Remap caption words (B-cam source times) onto the cut timeline.

    Keeps only words fully inside a segment's [in, out]; shifts to cumulative time.
    """
    out, cum = [], 0.0
    for seg in segments:
        b_media, dur, _, _ = _segment_timing(seg, offset, head_default, tail_default)
        for w in words:
            if w["start"] >= seg["in"] and w["end"] <= seg["out"]:
                out.append({
                    "start": round(cum + (w["start"] - b_media), 3),
                    "end": round(cum + (w["end"] - b_media), 3),
                    "word": w["word"],
                })
        cum += dur
    return out


def _deliverable_folder(library_root: Path, batch_n: int, vid_n: int, title: str) -> Path:
    """08_AI_EDITS/shorts/Batch_NN/B{N}_V{MM} - {title}/ (batch unpadded, vid zero-padded)."""
    return (Path(library_root) / "08_AI_EDITS" / "shorts" / f"Batch_{batch_n:02d}"
            / f"B{batch_n}_V{vid_n:02d} - {title}")


# --- ffmpeg helpers --------------------------------------------------------

def _run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def _b_segment(b_src: Path, b_media: float, dur: float, dst: Path):
    _run(["ffmpeg", "-y", "-ss", f"{b_media:.4f}", "-i", str(b_src), "-t", f"{dur:.4f}",
          "-vf", VF, "-r", config.FPS, *PRORES, str(dst)])


def _a_segment(a_src: Path, b_src: Path, a_media: float, b_media: float, dur: float, dst: Path):
    # A-cam VIDEO + B-cam AUDIO
    _run(["ffmpeg", "-y", "-ss", f"{a_media:.4f}", "-i", str(a_src),
          "-ss", f"{b_media:.4f}", "-i", str(b_src),
          "-map", "0:v:0", "-map", "1:a:0", "-t", f"{dur:.4f}",
          "-vf", VF, "-r", config.FPS, *PRORES, str(dst)])


def _concat(segs: list, dst: Path, td: Path):
    lst = td / "list.txt"
    lst.write_text("".join(f"file '{s.as_posix()}'\n" for s in segs))
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(dst)])


def _h264(src: Path, dst: Path, crf: int, preset: str, audio_kbps: str):
    _run(["ffmpeg", "-y", "-i", str(src), "-c:v", "libx264", "-crf", str(crf),
          "-preset", preset, "-pix_fmt", "yuv420p", "-r", config.FPS,
          "-c:a", "aac", "-b:a", audio_kbps, str(dst)])


# --- main render -----------------------------------------------------------

def render(batch_n: int, vid_n: int):
    """Load Cut/SEGMENTS.json for the batch/vid, build reels, export deliverable."""
    lib = config.library_root()
    cut_dir = lib / f"01_ORGANIZED/Batch_{batch_n:02d}/Vid_{vid_n:02d}/Cut"
    seg_json = cut_dir / "SEGMENTS.json"
    if not seg_json.exists():
        raise RuntimeError(f"No SEGMENTS.json at {seg_json} (run prep first)")

    data = json.loads(seg_json.read_text(encoding="utf-8"))
    title = data["title"]
    offset = data["offset"]
    a_src = lib / data["a_src"]
    b_src = lib / data["b_src"]
    segments = data["segments"]
    transcript = data.get("transcript", [])

    a_reel = cut_dir / f"{title} - A-cam.mov"
    b_reel = cut_dir / f"{title} - B-cam.mov"
    preview = cut_dir / f"{title} - PREVIEW.mp4"

    print(f"\n{'='*60}\nRENDER  Batch {batch_n} Vid {vid_n} — {title}\n{'='*60}")
    print(f"offset {offset:+.4f}s | {len(segments)} segments")

    plan = []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        a_segs, b_segs, cum = [], [], 0.0
        for i, seg in enumerate(segments):
            b_media, dur, a_media, a_fallback = _segment_timing(seg, offset)
            a_dst, b_dst = td / f"a{i:02d}.mov", td / f"b{i:02d}.mov"
            _b_segment(b_src, b_media, dur, b_dst)
            if a_fallback:
                _run(["ffmpeg", "-y", "-i", str(b_dst), "-c", "copy", str(a_dst)])
            else:
                _a_segment(a_src, b_src, a_media, b_media, dur, a_dst)
            a_segs.append(a_dst); b_segs.append(b_dst)
            plan.append(f"range {i:02d}: B {b_media:7.2f}->{seg['out']:7.2f} ({dur:5.2f}s)"
                        f" -> cut {cum:6.2f}-{cum+dur:6.2f}"
                        + ("  [A=B fallback]" if a_fallback else ""))
            cum += dur

        _concat(a_segs, a_reel, td)
        _concat(b_segs, b_reel, td)
        _h264(b_reel, preview, crf=20, preset="fast", audio_kbps="192k")

    # caption words remapped to cut timeline
    cut_words = _caption_remap(transcript, segments, offset)
    (cut_dir / "cut_words.json").write_text(
        json.dumps(cut_words, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\n".join(plan))
    print(f"\nTOTAL: {cum:.2f}s | {len(cut_words)} caption words")

    # --- export deliverable ---
    deliver = _deliverable_folder(lib, batch_n, vid_n, title)
    angles = deliver / "ANGLES"
    angles.mkdir(parents=True, exist_ok=True)
    a_out = angles / f"B{batch_n}_V{vid_n:02d}_A-cam.mp4"
    b_out = angles / f"B{batch_n}_V{vid_n:02d}_B-cam.mp4"
    _h264(a_reel, a_out, crf=18, preset="slow", audio_kbps="192k")
    _h264(b_reel, b_out, crf=18, preset="slow", audio_kbps="192k")

    info = [f"{title}", f"Batch {batch_n} Video {vid_n}", "",
            f"Sync offset (tB - tA): {offset:+.4f}s   A-time = B-time - offset", "",
            "Segments (B-cam time -> cut time):", *plan, "",
            f"TOTAL: {cum:.2f}s across {len(segments)} ranges"]
    if data.get("dropped"):
        info += ["", "Dropped:"] + [f"  - {d}" for d in data["dropped"]]
    (deliver / "_INFO.txt").write_text("\n".join(info) + "\n", encoding="utf-8")

    print(f"\n✓ Deliverable: {deliver}")
    print(f"  ProRes masters kept in: {cut_dir}")
    return deliver


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser("Render batch video from Cut/SEGMENTS.json")
    p.add_argument("--batch", type=int, required=True)
    p.add_argument("--video", type=int, required=True)
    args = p.parse_args()
    render(args.batch, args.video)
