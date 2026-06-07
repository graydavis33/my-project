"""Sync + trim paired A/B interview cams to their common overlapping window.

For each (A, B) clip pair:
  1. Extract mono audio from both.
  2. Cross-correlate to find the A->B offset (reuses sync.compute_offset).
  3. Compute the time window where BOTH cameras were rolling.
  4. ffmpeg-trim + re-encode each cam to that window, keeping each cam's
     NATIVE framerate (A stays 23.976, B stays 25 — they are NOT locked
     to each other; they get conformed on the Premiere timeline).

Output naming matches the already-done Pair 1:
  Pair{N}_A_{Aname}_synced.mp4 / Pair{N}_B_{Bname}_synced.mp4

Usage:
  python sync_trim_pairs.py --verify        # print intended trims, write nothing
  python sync_trim_pairs.py --pairs 2-6     # encode pairs 2 through 6
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from sync import compute_offset

EP = Path("/Volumes/Footage 1/Sai/01_ORGANIZED/Longfrom Doc/Ep 1")
A_DIR = EP / "A-cam Ep 1 Doc Int"
B_DIR = EP / "B-Cam Ep 1 Doc Int"
OUT_DIR = EP / "Synced_Trimmed Int"

# Sequential 1:1 pairing (A-cam clip <-> B-cam clip, in capture order)
PAIRS = [
    ("C2608", "MVI_5034"),
    ("C2609", "MVI_5035"),
    ("C2610", "MVI_5036"),
    ("C2611", "MVI_5037"),
    ("C2612", "MVI_5038"),
    ("C2613", "MVI_5039"),
]


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def extract_wav(src: Path, dst: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "48000",
         "-f", "wav", str(dst)],
        check=True, capture_output=True,
    )


def overlap_window(dur_a: float, dur_b: float, offset: float):
    """offset = tB - tA. Returns (a_start, length, b_start) in seconds.

    B's t=0 sits at A-time (-offset). Overlap is the intersection of
    A's span [0,dur_a] and B's span (in A-time) [-offset, dur_b-offset].
    """
    start_a = max(0.0, -offset)
    end_a = min(dur_a, dur_b - offset)
    length = end_a - start_a
    start_b = start_a + offset  # convert A-time start to B-time
    return start_a, length, start_b


def encode_segment(src: Path, start: float, length: float, dst: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{start:.4f}", "-i", str(src),
         "-t", f"{length:.4f}",
         "-c:v", "libx264", "-preset", "fast", "-crf", "20",
         "-c:a", "aac", "-b:a", "192k", str(dst)],
        check=True,
    )


def process(pair_idx: int, a_name: str, b_name: str, verify: bool) -> None:
    a_src = A_DIR / f"{a_name}.MP4"
    b_src = B_DIR / f"{b_name}.MP4"
    dur_a, dur_b = duration(a_src), duration(b_src)

    with tempfile.TemporaryDirectory() as td:
        a_wav, b_wav = Path(td) / "a.wav", Path(td) / "b.wav"
        extract_wav(a_src, a_wav)
        extract_wav(b_src, b_wav)
        offset = compute_offset(a_wav, b_wav, window_s=60.0)

    a_start, length, b_start = overlap_window(dur_a, dur_b, offset)
    print(f"Pair{pair_idx}: offset={offset:+.3f}s  overlap={length:.3f}s  "
          f"A[{a_start:.3f}..{a_start+length:.3f}]  B[{b_start:.3f}..{b_start+length:.3f}]")

    if verify:
        return

    OUT_DIR.mkdir(exist_ok=True)
    a_out = OUT_DIR / f"Pair{pair_idx}_A_{a_name}_synced.mp4"
    b_out = OUT_DIR / f"Pair{pair_idx}_B_{b_name}_synced.mp4"
    encode_segment(a_src, a_start, length, a_out)
    encode_segment(b_src, b_start, length, b_out)
    print(f"  -> wrote {a_out.name} + {b_out.name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="print intended trims for ALL pairs, write nothing")
    ap.add_argument("--pairs", default="2-6",
                    help="inclusive range to encode, e.g. 2-6 or 3-3")
    args = ap.parse_args()

    if args.verify:
        for i, (a, b) in enumerate(PAIRS, start=1):
            process(i, a, b, verify=True)
        return

    lo, hi = (int(x) for x in args.pairs.split("-"))
    for i in range(lo, hi + 1):
        a, b = PAIRS[i - 1]
        process(i, a, b, verify=False)


if __name__ == "__main__":
    main()
