"""Re-render the 2026-04-30 long-form dual-cam edit with new padding.

Reads existing artifacts (claude_keep.json + words.json + sync.json), re-snaps
each pick to Whisper word boundaries with configurable head/tail padding, then
extracts + concats parallel A-cam and B-cam reels.

Defaults: head_pad=0ms (start exactly at first-word onset), tail_pad=400ms
(let the last word finish + a touch of breath before the cut).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(r"D:/Sai/A-Roll Long Lessons I learned from growing a business")
EDIT = ROOT / "edit"
A_CAM = ROOT / "C2313.MP4"
B_CAM = ROOT / "b-roll long .MP4"
OUT_DIR = Path(r"D:/Sai/AI Edits/2026-04-30/long-form-v2")

HEAD_PAD = 0.000   # seconds added before first-word onset
TAIL_PAD = 0.400   # seconds added after last-word offset
FADE = 0.030       # audio crossfade at cut points

SLOP = 0.05  # tolerance when matching Claude's pick window to word timestamps


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FFMPEG STDERR:", r.stderr[-1500:])
        raise SystemExit(f"ffmpeg failed: {' '.join(cmd[:4])} ...")


def snap_to_words(pick_start: float, pick_end: float, words: list[dict]) -> tuple[float, float] | None:
    first = next((w for w in words if w["start"] >= pick_start - SLOP), None)
    if first is None:
        return None
    last = None
    for w in words:
        if w["end"] <= pick_end + SLOP:
            last = w
    if last is None or last["end"] <= first["start"]:
        return None
    return first["start"], last["end"]


def main() -> int:
    keep = json.loads((EDIT / "claude_keep.json").read_text(encoding="utf-8"))["keep"]
    words = json.loads((EDIT / "words.json").read_text(encoding="utf-8"))
    sync = json.loads((EDIT / "sync.json").read_text(encoding="utf-8"))
    offset = sync["offset_seconds"]
    a_dur = sync["a_duration"]
    b_dur = sync["b_duration"]

    print(f"Picks: {len(keep)}  |  A->B offset: {offset:+.4f}s  |  head={HEAD_PAD*1000:.0f}ms tail={TAIL_PAD*1000:.0f}ms")

    segs_a = OUT_DIR / "segs_a"
    segs_b = OUT_DIR / "segs_b"
    segs_a.mkdir(parents=True, exist_ok=True)
    segs_b.mkdir(parents=True, exist_ok=True)

    snapped: list[tuple[float, float]] = []
    for i, pick in enumerate(keep):
        snap = snap_to_words(pick["start"], pick["end"], words)
        if snap is None:
            print(f"  WARN pick {i:03d}: no word match in [{pick['start']:.2f}, {pick['end']:.2f}] — skipping")
            continue
        snapped.append(snap)

    padded: list[tuple[float, float]] = []
    for i, (ws, we) in enumerate(snapped):
        s = max(0.0, ws - HEAD_PAD)
        e = we + TAIL_PAD
        if i + 1 < len(snapped):
            next_ws = snapped[i + 1][0]
            if e > next_ws - 0.020:
                e = max(we, next_ws - 0.020)
        e = min(e, a_dur)
        b_start = s + offset
        b_end = e + offset
        if b_start < 0 or b_end > b_dur:
            print(f"  WARN seg {i:03d}: B out of range [{b_start:.2f}, {b_end:.2f}] vs {b_dur:.2f}")
            if b_start < 0:
                shift = -b_start
                b_start = 0.0
                s = s + shift
            if b_end > b_dur:
                shift = b_end - b_dur
                b_end = b_dur
                e = e - shift
            if b_end <= b_start or e <= s:
                print(f"  SKIP seg {i:03d}: B fully outside")
                continue
        padded.append((s, e, b_start, b_end))

    print(f"Rendering {len(padded)} segments...")
    concat_a = OUT_DIR / "concat_A.txt"
    concat_b = OUT_DIR / "concat_B.txt"
    a_lines: list[str] = []
    b_lines: list[str] = []

    for i, (a_s, a_e, b_s, b_e) in enumerate(padded):
        a_seg = segs_a / f"seg_{i:03d}.mp4"
        b_seg = segs_b / f"seg_{i:03d}.mp4"
        dur_a = a_e - a_s
        dur_b = b_e - b_s
        afade = (
            f"afade=t=in:st=0:d={FADE},"
            f"afade=t=out:st={max(0.0, dur_a - FADE):.3f}:d={FADE}"
        )
        afade_b = (
            f"afade=t=in:st=0:d={FADE},"
            f"afade=t=out:st={max(0.0, dur_b - FADE):.3f}:d={FADE}"
        )
        fast_a = max(0.0, a_s - 5.0)
        fast_b = max(0.0, b_s - 5.0)
        run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", f"{fast_a:.3f}", "-i", str(A_CAM),
            "-ss", f"{a_s - fast_a:.3f}", "-t", f"{dur_a:.3f}",
            "-r", "24000/1001",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-af", afade,
            "-pix_fmt", "yuv420p",
            str(a_seg),
        ])
        run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", f"{fast_b:.3f}", "-i", str(B_CAM),
            "-ss", f"{b_s - fast_b:.3f}", "-t", f"{dur_b:.3f}",
            "-r", "24000/1001",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-af", afade_b,
            "-pix_fmt", "yuv420p",
            str(b_seg),
        ])
        a_lines.append(f"file '{a_seg.as_posix()}'")
        b_lines.append(f"file '{b_seg.as_posix()}'")
        print(f"  seg {i:03d}: A[{a_s:7.2f}-{a_e:7.2f}] dur={dur_a:5.2f}  B[{b_s:7.2f}-{b_e:7.2f}]")

    concat_a.write_text("\n".join(a_lines) + "\n", encoding="utf-8")
    concat_b.write_text("\n".join(b_lines) + "\n", encoding="utf-8")

    print("Concatenating final_Aroll.mp4 + final_Broll.mp4 ...")
    run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_a),
        "-c", "copy",
        str(OUT_DIR / "final_Aroll.mp4"),
    ])
    run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_b),
        "-c", "copy",
        str(OUT_DIR / "final_Broll.mp4"),
    ])

    total = sum(e - s for s, e, _, _ in padded)
    print(f"\nDone. {len(padded)} segments, {total:.2f}s total")
    print(f"  {OUT_DIR / 'final_Aroll.mp4'}")
    print(f"  {OUT_DIR / 'final_Broll.mp4'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
