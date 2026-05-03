"""
find_visuals.py — pair sai-linkedin visual_ideas with footage-library frames.

Usage:
    python find_visuals.py "/Volumes/Footage/Sai/08_AI_EDITS/linkedin/<draft-folder>"

Reads linkedin/visual_ideas.txt, samples candidate clips from the SQLite footage
index, scores them with Claude Haiku Vision, and extracts the winning HQ JPG
per idea into linkedin/visuals/.

Frames only, not full MP4s.
"""

import argparse
import base64
import json
import os
import random
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

FOOTAGE_ROOT = Path("/Volumes/Footage/Sai")
INDEX_DB = FOOTAGE_ROOT / ".footage-index.sqlite"
MODEL = "claude-haiku-4-5-20251001"

CANDIDATES_PER_IDEA = 8
THUMB_WIDTH = 512


def map_idea_to_categories(idea: str) -> list[str]:
    """Heuristic: map idea text to plausible candidate categories."""
    t = idea.lower()
    cats = set()
    if any(k in t for k in ["meditat", "cross-legged", "eyes closed", "still", "quiet", "calm"]):
        cats.update(["candid-people", "misc", "action-sport-fitness", "interview-solo"])
    if any(k in t for k in ["phone", "timer", "screen", "watch", "stopwatch", "clock"]):
        cats.update(["insert-product", "insert-hands", "screens-and-text", "insert-detail"])
    if any(k in t for k in ["desk", "notebook", "laptop", "office", "workspace", "meeting"]):
        cats.update(["interview-solo", "establishing-interior", "insert-hands", "insert-detail"])
    if any(k in t for k in ["morning", "light", "routine", "wake", "early"]):
        cats.update(["establishing-interior", "candid-people", "walk-and-talk", "misc"])
    if any(k in t for k in ["room", "interior", "home", "bedroom", "kitchen"]):
        cats.update(["establishing-interior", "misc"])
    if not cats:
        cats.update(["misc", "interview-solo", "establishing-interior", "candid-people"])
    return list(cats)


def sample_candidates(idea: str, n: int) -> list[dict]:
    cats = map_idea_to_categories(idea)
    placeholders = ",".join("?" * len(cats))
    conn = sqlite3.connect(INDEX_DB)
    rows = conn.execute(
        f"SELECT path, category, duration_s FROM clips WHERE category IN ({placeholders}) AND duration_s > 1.5",
        cats,
    ).fetchall()
    conn.close()
    random.shuffle(rows)
    return [{"path": r[0], "category": r[1], "duration": r[2]} for r in rows[:n]]


def extract_thumb(clip_path: Path, out_path: Path, width: int = THUMB_WIDTH) -> bool:
    """Extract a mid-frame JPG thumbnail."""
    try:
        duration = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(clip_path)
        ]).decode().strip())
    except Exception:
        return False
    mid = duration / 2
    try:
        subprocess.run([
            "ffmpeg", "-y", "-ss", f"{mid:.2f}", "-i", str(clip_path),
            "-frames:v", "1", "-vf", f"scale={width}:-2", "-q:v", "4",
            str(out_path)
        ], check=True, capture_output=True)
        return out_path.exists()
    except subprocess.CalledProcessError:
        return False


def extract_hq_frame(clip_path: Path, out_path: Path) -> bool:
    """Extract a hi-res mid-frame JPG (no scaling)."""
    try:
        duration = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(clip_path)
        ]).decode().strip())
    except Exception:
        return False
    mid = duration / 2
    try:
        subprocess.run([
            "ffmpeg", "-y", "-ss", f"{mid:.2f}", "-i", str(clip_path),
            "-frames:v", "1", "-q:v", "2", str(out_path)
        ], check=True, capture_output=True)
        return out_path.exists()
    except subprocess.CalledProcessError:
        return False


def b64_image(path: Path) -> dict:
    data = base64.standard_b64encode(path.read_bytes()).decode()
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/jpeg", "data": data},
    }


def score_candidates(client: Anthropic, idea: str, candidates: list[dict], thumb_dir: Path) -> list[dict]:
    """Send all candidate thumbs in one Haiku call, get JSON scores 0-10."""
    content = []
    valid = []
    for i, c in enumerate(candidates):
        thumb = thumb_dir / f"cand_{i}.jpg"
        if extract_thumb(FOOTAGE_ROOT / c["path"], thumb):
            content.append({"type": "text", "text": f"Candidate {i}:"})
            content.append(b64_image(thumb))
            valid.append(c)

    if not valid:
        return []

    content.append({
        "type": "text",
        "text": (
            f'Score each candidate frame 0-10 for how well it visually represents this concept:\n\n'
            f'"{idea}"\n\n'
            f'10 = perfect match, 5 = somewhat related, 0 = unrelated. '
            f'Return ONLY a JSON array of objects with keys "i" (candidate index) and "score" (0-10) and "reason" (one short sentence). '
            f'No commentary, no markdown.'
        ),
    })

    resp = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": content}],
    )
    raw = resp.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    try:
        scores = json.loads(raw)
    except json.JSONDecodeError:
        print(f"  [warn] Haiku returned non-JSON: {raw[:200]}")
        return []

    for s in scores:
        if 0 <= s["i"] < len(valid):
            valid[s["i"]]["score"] = s["score"]
            valid[s["i"]]["reason"] = s.get("reason", "")
    return [v for v in valid if "score" in v]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", help="Path to draft folder containing linkedin/visual_ideas.txt")
    args = parser.parse_args()

    folder = Path(args.folder)
    ideas_path = folder / "linkedin" / "visual_ideas.txt"
    if not ideas_path.exists():
        sys.exit(f"Not found: {ideas_path}")

    ideas = [
        re.sub(r"^[-*\d.\s]+", "", line).strip()
        for line in ideas_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    print(f"[find_visuals] {len(ideas)} ideas loaded")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY missing")
    client = Anthropic(api_key=api_key)

    out_dir = folder / "linkedin" / "visuals"
    out_dir.mkdir(parents=True, exist_ok=True)
    thumb_dir = Path("/tmp/sai-find-visuals")
    thumb_dir.mkdir(exist_ok=True)

    manifest = []
    for idx, idea in enumerate(ideas, 1):
        print(f"\n[idea {idx}] {idea}")
        candidates = sample_candidates(idea, CANDIDATES_PER_IDEA)
        print(f"  sampled {len(candidates)} candidates from {set(c['category'] for c in candidates)}")
        if not candidates:
            continue

        scored = score_candidates(client, idea, candidates, thumb_dir)
        scored.sort(key=lambda x: x["score"], reverse=True)
        if not scored:
            print(f"  no scores returned")
            continue

        winner = scored[0]
        print(f"  winner: {winner['path']} (score {winner['score']}/10) — {winner.get('reason','')}")

        clip_path = FOOTAGE_ROOT / winner["path"]
        out_jpg = out_dir / f"idea{idx}_score{winner['score']}_{Path(winner['path']).stem}.jpg"
        if extract_hq_frame(clip_path, out_jpg):
            print(f"  saved: {out_jpg.name}")
            manifest.append({
                "idea_index": idx,
                "idea": idea,
                "winner_clip": winner["path"],
                "score": winner["score"],
                "reason": winner.get("reason", ""),
                "output_jpg": out_jpg.name,
                "runner_ups": [{"clip": s["path"], "score": s["score"]} for s in scored[1:4]],
            })

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n[done] {len(manifest)} visuals saved to {out_dir}")


if __name__ == "__main__":
    main()
