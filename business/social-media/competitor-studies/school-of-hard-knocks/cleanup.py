"""Dedupe + correctly rank-number the reels folder.

The two yt-dlp runs (initial + resume) both used --autonumber-start 1, so when
some downloads failed in run 1 and got retried in run 2, the rank prefixes
diverged from the urls.txt order. This rebuilds correct rank prefixes from
labels.csv (reel_id is the source of truth) and deletes duplicates + .part files.
"""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REELS = ROOT / "reels"

reel_to_rank = {}
with open(ROOT / "labels.csv") as f:
    for row in csv.DictReader(f):
        reel_to_rank[row["reel_id"]] = int(row["rank"])

removed = 0
renamed = 0
ok = 0
unknown = []

for f in sorted(REELS.iterdir()):
    name = f.name
    if not f.is_file():
        continue
    if name.endswith(".part") or ".part" in name:
        f.unlink()
        removed += 1
        continue
    if not name.endswith(".mp4"):
        continue

    m = re.match(r"^(\d+)-(.+)\.mp4$", name)
    if not m:
        continue
    reel_id = m.group(2)
    correct_rank = reel_to_rank.get(reel_id)
    if correct_rank is None:
        unknown.append(name)
        continue

    correct_name = f"{correct_rank:02d}-{reel_id}.mp4"
    if name == correct_name:
        ok += 1
        continue

    correct_path = REELS / correct_name
    if correct_path.exists():
        f.unlink()
        removed += 1
    else:
        f.rename(correct_path)
        renamed += 1

print(f"Already correct: {ok}")
print(f"Renamed: {renamed}")
print(f"Removed (duplicates + partials): {removed}")
if unknown:
    print(f"Unknown reel_ids (not in labels.csv): {unknown}")

final = sorted(p.name for p in REELS.glob("*.mp4"))
print(f"\nFinal count: {len(final)} mp4 files")
print(f"Expected: {len(reel_to_rank)}")
missing_ranks = [r for r, _ in sorted([(rk, rid) for rid, rk in reel_to_rank.items()])
                 if not (REELS / f"{r:02d}-{[rid for rid,rrk in reel_to_rank.items() if rrk==r][0]}.mp4").exists()]
if missing_ranks:
    print(f"Missing ranks: {missing_ranks}")
