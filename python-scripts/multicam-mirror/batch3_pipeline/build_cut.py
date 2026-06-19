#!/usr/bin/env python3
"""Batch 3 Vid 2 cut v2 — includes Gray's question (from B-cam) + longer tails.

Word sources (all converted to SYNCED time = A-cam C2741 full time):
  - QUESTION words: B-cam transcript (clear there; faint on A-cam), B_orig - 3.8946
  - ANSWER words:   A-cam synced transcript (already synced)
SEGMENTS are in synced time. Both cams have footage for every range (full-source
synced pair), so the same ranges are cut from each and stay locked.

Fix vs v1: TAIL 0.30 (was 0.10) so trailing words ring out instead of clipping.
"""
import json
import glob
import subprocess
import tempfile
from pathlib import Path

VID = Path("/Volumes/Footage/Sai/01_ORGANIZED/Batch_03/Vid_02")
SYNC = VID / "Synced"
A_SRC = SYNC / "Vid_02_A-cam_synced.mp4"
B_SRC = SYNC / "Vid_02_B-cam_synced.mp4"
A_WORDS = SYNC / "Vid_02_A-cam_synced.json"
OUT = VID / "Cut"
B_OFFSET = 3.8946   # synced = B_orig - this

LEAD = 0.08
TAIL = 0.30
PAUSE_S = 0.50
FPS = "24000/1001"

# selection in SYNCED time (in, out). Builder trims to actual word bounds.
SEGMENTS = [
    (6.30, 9.10),    # Q1  What did making 10,000 ads teach you?           (B-cam)
    (11.80, 13.20),  # Q2  That you can't learn making 10?                 (B-cam)
    (18.50, 31.60),  # A1  hardest part ... every unit as good as the last
    (35.70, 38.80),  # A2a "a lot of times what ends up happening is you scale,"
    (43.40, 47.00),  # A2b "The product or service ... worse and worse"  (CLEAN 2nd take, rings out)
    (49.60, 54.90),  # A3  the difference is building systems ... delivers
    (57.90, 61.10),  # A4  one ad just as good as if you made 10,000
    (66.40, 71.30),  # A5  when you aim that one unit and scale it
    (77.60, 80.90),  # A6  closer: build really big, ensure nothing breaks
]
HANDLE_OVERRIDE = {8: (LEAD, 0.35)}  # closer rings out


def load_answer_words():
    d = json.loads(A_WORDS.read_text())
    out = []
    for s in d["segments"]:
        for w in s.get("words", []):
            t = w["word"].strip()
            if t and w["end"] > w["start"]:
                out.append({"start": float(w["start"]), "end": float(w["end"]), "word": t})
    return out


def load_question_words():
    """B-cam question words -> synced. Keep take 1 + the 'That you can't...' part,
    drop the duplicate take 2."""
    f = glob.glob("/tmp/v2q/*.json")[0]
    d = json.loads(Path(f).read_text())
    keep_borig = [(10.30, 13.26), (15.78, 17.34)]  # take1 of Q + the follow-up
    out = []
    for s in d["segments"]:
        for w in s.get("words", []):
            if w["end"] <= w["start"]:
                continue
            if any(lo - 0.01 <= w["start"] < hi for lo, hi in keep_borig):
                out.append({"start": w["start"] - B_OFFSET, "end": w["end"] - B_OFFSET,
                            "word": w["word"].strip()})
    return out


def words_in(words, lo, hi):
    return [w for w in words if w["start"] < hi and w["end"] > lo]


def build(words):
    ranges = []
    for seg_idx, (lo, hi) in enumerate(SEGMENTS):
        sw = words_in(words, lo, hi)
        if not sw:
            continue
        cur = [sw[0]]
        for w in sw[1:]:
            if w["start"] - cur[-1]["end"] > PAUSE_S:
                ranges.append((seg_idx, cur)); cur = [w]
            else:
                cur.append(w)
        ranges.append((seg_idx, cur))
    keep = []
    for seg_idx, grp in ranges:
        lead, tail = HANDLE_OVERRIDE.get(seg_idx, (LEAD, TAIL))
        keep.append({"lo": max(0.0, grp[0]["start"] - lead), "hi": grp[-1]["end"] + tail, "words": grp})
    return keep


def ff_extract(src, start, dur, dst):
    subprocess.run(["ffmpeg", "-y", "-ss", f"{start:.4f}", "-i", str(src), "-t", f"{dur:.4f}",
                    "-r", FPS, "-vsync", "cfr", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", str(dst)],
                   check=True, capture_output=True)


def concat(parts, dst):
    # Re-encode the stitched segments into ONE clean continuous stream with fresh,
    # monotonic timestamps. Stream-copy concat leaves per-segment timestamps that make
    # QuickTime stall at a boundary; re-encoding (+genpts, uniform CFR) fixes that.
    lf = dst.parent / (dst.stem + "_list.txt")
    lf.write_text("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-fflags", "+genpts", "-f", "concat", "-safe", "0", "-i", str(lf),
                    "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-r", "24000/1001", "-video_track_timescale", "24000",
                    "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart",
                    str(dst)], check=True, capture_output=True)
    lf.unlink()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    words = sorted(load_question_words() + load_answer_words(), key=lambda w: w["start"])
    keep = build(words)
    cap, plan, cum = [], [], 0.0
    for i, r in enumerate(keep):
        dur = r["hi"] - r["lo"]
        plan.append(f"range {i:02d}: synced {r['lo']:7.3f}-{r['hi']:7.3f} ({dur:5.2f}s) -> cut {cum:6.3f}-{cum+dur:6.3f} | "
                    + " ".join(w["word"] for w in r["words"]))
        for w in r["words"]:
            cap.append({"start": round(cum + (w["start"] - r["lo"]), 3),
                        "end": round(cum + (w["end"] - r["lo"]), 3), "word": w["word"]})
        cum += dur
    plan.append(f"\nTOTAL: {cum:.2f}s across {len(keep)} ranges")
    (OUT / "cut_plan.txt").write_text("\n".join(plan))
    (OUT / "caption_words.json").write_text(json.dumps(cap, indent=1))
    print("\n".join(plan))
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for cam, src in (("A", A_SRC), ("B", B_SRC)):
            parts = []
            for i, r in enumerate(keep):
                p = td / f"{cam}_{i:02d}.mp4"
                ff_extract(src, r["lo"], r["hi"] - r["lo"], p)
                parts.append(p)
            dst = OUT / f"Vid_02_{cam}-cam_CUT.mp4"
            concat(parts, dst)
            print(f"wrote {dst}")


if __name__ == "__main__":
    main()
