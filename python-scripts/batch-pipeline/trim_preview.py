#!/usr/bin/env python
"""Trim synced A/B cam videos to selected ranges and output for preview.

Usage:
    python trim_preview.py --config <path/to/config.json>

Output: trimmed MOVs at the same location as synced videos, with a preview HTML.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def trim_video_ranges(video_path: Path, ranges: list, out_path: Path) -> None:
    """Trim video to multiple ranges and concatenate."""
    # Build ffmpeg filter for concat
    # Each range is [start, end, ...]
    segments = []
    concat_filter = ""

    for i, (seg_start, seg_end) in enumerate([(r[0], r[1]) for r in ranges]):
        duration = seg_end - seg_start
        # Use trim + setpts to extract and reset timestamps
        concat_filter += f"[0:v]trim=start={seg_start}:end={seg_end},setpts=PTS-STARTPTS[v{i}]; "
        concat_filter += f"[0:a]atrim=start={seg_start}:end={seg_end},asetpts=PTS-STARTPTS[a{i}]; "

    # Concat all segments
    v_inputs = "".join([f"[v{i}]" for i in range(len(ranges))])
    a_inputs = "".join([f"[a{i}]" for i in range(len(ranges))])
    concat_filter += f"{v_inputs}concat=n={len(ranges)}:v=1:a=0[vout]; "
    concat_filter += f"{a_inputs}concat=n={len(ranges)}:v=0:a=1[aout]"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-filter_complex", concat_filter,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "prores_ks", "-profile:v", "3",
        "-c:a", "aac",
        str(out_path)
    ]

    print(f"  Trimming {video_path.name}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[:200]}")
        raise RuntimeError(f"ffmpeg trim failed: {result.stderr}")
    print(f"  ✓ Trimmed: {out_path.name}")


def trim_to_preview(config_path: Path):
    """Trim A/B cam videos to ranges and prepare for preview."""
    config_dict = json.loads(config_path.read_text())
    ranges = config_dict["ranges"]
    batch_n = config_dict["batch_n"]
    vid_n = config_dict["vid_n"]
    title = config_dict.get("title", f"B{batch_n}V{vid_n:02d}")

    # Videos are in the same folder as config.json
    synced_folder = config_path.parent
    synced_a = synced_folder / f"B{batch_n}_V{vid_n:02d}_A-cam_SYNCED.mov"
    synced_b = synced_folder / f"B{batch_n}_V{vid_n:02d}_B-cam_SYNCED.mov"

    print(f"\n{'='*60}")
    print(f"TRIM PREVIEW — {title}")
    print(f"{'='*60}")
    print(f"\nSource A-cam: {synced_a.name}")
    print(f"Source B-cam: {synced_b.name}")
    print(f"Ranges: {len(ranges)} segments → ~{sum(r[1]-r[0] for r in ranges):.1f}s total")

    # Output folder (same as synced folder)
    trim_folder = synced_a.parent / "trimmed"
    trim_folder.mkdir(exist_ok=True)

    trimmed_a = trim_folder / f"{synced_a.stem}_trimmed.mov"
    trimmed_b = trim_folder / f"{synced_b.stem}_trimmed.mov"

    print(f"\nTrimming videos...")
    trim_video_ranges(synced_a, ranges, trimmed_a)
    trim_video_ranges(synced_b, ranges, trimmed_b)

    print(f"\n{'='*60}")
    print(f"✓ Trimmed files ready for preview:")
    print(f"  A-cam: {trimmed_a}")
    print(f"  B-cam: {trimmed_b}")
    print(f"{'='*60}\n")

    return trimmed_a, trimmed_b


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser("Trim videos to selected ranges for preview")
    p.add_argument("--config", type=Path, required=True)
    args = p.parse_args()

    trim_to_preview(args.config)
