"""
Pre-process whatever reels are already downloaded, in parallel with the ongoing
yt-dlp batch. Idempotent — re-running picks up newly-completed reels.

Skips report generation (analyze.py does that once all 43 are ready).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze import (
    reel_files,
    transcribe_reel,
    extract_frames,
    analyze_frames,
    detect_cuts,
    TRANSCRIPTS,
    FRAMES,
    CUTS,
)

for d in (TRANSCRIPTS, FRAMES, CUTS):
    d.mkdir(exist_ok=True)

reels = list(reel_files())
print(f"Pre-processing {len(reels)} reels currently on disk...")

for rank, reel_id, mp4 in reels:
    transcribe_reel(rank, reel_id, mp4)
    extract_frames(rank, reel_id, mp4)
    analyze_frames(rank, reel_id)
    detect_cuts(rank, reel_id, mp4)
    print(f"  done {rank:02d} {reel_id}")

print(f"\nPre-processing complete on {len(reels)} reels.")
