"""multicam-mirror: apply a video-use EDL's A-cam cuts to a parallel B-cam.

Usage:
    python main.py <a_cam.mp4> <b_cam.mp4> <edl.json> [--out-dir DIR]

Produces <out-dir>/final_b.mp4 — a B-cam reel cut at the same moments
A-cam was cut in the EDL, after computing the audio offset between the
two takes via scipy cross-correlation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import sync
import render

# Force UTF-8 stdout on Windows so the +/- offset arrow doesn't crash cp1252.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mirror a video-use EDL onto a parallel B-cam.")
    p.add_argument("a_cam", type=Path, help="A-cam source file (the one video-use cut)")
    p.add_argument("b_cam", type=Path, help="B-cam source file (parallel angle)")
    p.add_argument("edl", type=Path, help="video-use edl.json")
    p.add_argument("--out-dir", type=Path, default=Path("./multicam_out"),
                   help="Output directory (default: ./multicam_out)")
    p.add_argument("--window", type=float, default=30.0,
                   help="Seconds of audio to use for sync correlation (default: 30)")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    for path in (args.a_cam, args.b_cam, args.edl):
        if not path.exists():
            print(f"ERROR: not found: {path}")
            return 1

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    edl = json.loads(args.edl.read_text(encoding="utf-8"))
    ranges = edl.get("ranges", [])
    if not ranges:
        print("ERROR: EDL has no ranges")
        return 1

    sources = set(r["source"] for r in ranges)
    if len(sources) > 1:
        print(f"ERROR: EDL references multiple sources {sorted(sources)}.")
        print("       multicam-mirror v1 only supports single-A-cam EDLs.")
        return 1

    print(f"[1/4] Extracting mono audio from A-cam and B-cam ...")
    a_wav = out_dir / "a.wav"
    b_wav = out_dir / "b.wav"
    render.extract_audio_mono(args.a_cam, a_wav)
    render.extract_audio_mono(args.b_cam, b_wav)

    print(f"[2/4] Computing audio offset (window={args.window}s) ...")
    offset = sync.compute_offset(a_wav, b_wav, window_s=args.window)
    print(f"      A->B offset: {offset:+.4f}s "
          f"({'B is later' if offset < 0 else 'B is earlier'} than A)")

    b_duration = render.get_duration(args.b_cam)

    print(f"[3/4] Extracting {len(ranges)} B-cam segment(s) ...")
    segments: list[Path] = []
    for i, r in enumerate(ranges):
        b_start = r["start"] + offset
        b_end = r["end"] + offset
        if b_start < 0 or b_end > b_duration:
            print(f"      WARN: segment {i} out of B-cam range "
                  f"[{b_start:.2f}, {b_end:.2f}] vs B duration {b_duration:.2f}")
            b_start = max(0.0, b_start)
            b_end = min(b_duration, b_end)
            if b_end <= b_start:
                print(f"      SKIP: segment {i} fully outside B-cam")
                continue
        seg_path = out_dir / "segments" / f"seg_{i:03d}.mp4"
        render.extract_segment(args.b_cam, b_start, b_end, seg_path)
        segments.append(seg_path)
        print(f"      seg {i:03d}: A[{r['start']:.2f}-{r['end']:.2f}] -> B[{b_start:.2f}-{b_end:.2f}]")

    if not segments:
        print("ERROR: no usable segments after offset shift")
        return 1

    print(f"[4/4] Concatenating into final_b.mp4 ...")
    final = out_dir / "final_b.mp4"
    render.concat_segments(segments, final)

    print(f"\nDone. {final}  ({len(segments)} segments)")
    print(f"Drop final_a.mp4 + final_b.mp4 onto a Premiere/Resolve timeline as parallel tracks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
