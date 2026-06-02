"""Fetch top videos + thumbnails from a list of YouTube channels via yt-dlp.

Outputs:
  data/creators.json      -- {creator_slug: [{id, title, views, thumb_path, url}, ...]}
  thumbnails/<slug>_<rank>.jpg

Designed to be re-run; existing JPGs are not redownloaded.
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
THUMBS = ROOT / "thumbnails"
DATA = ROOT / "data"
THUMBS.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)

# (slug, display_name, channel_url, n_videos)
CREATORS = [
    ("hormozi",     "Alex Hormozi",      "https://www.youtube.com/@AlexHormozi/videos", 5),
    ("gadzhi",      "Iman Gadzhi",       "https://www.youtube.com/@ImanGadzhi/videos", 5),
    ("morgan",      "Charlie Morgan",    "https://www.youtube.com/@charliemorganbusiness/videos", 5),
    ("welch",       "Jordan Welch",      "https://www.youtube.com/@JordanWelch/videos", 5),
    ("malinowski",  "Brett Malinowski",  "https://www.youtube.com/@TheBrettWay/videos", 5),
    ("mylett",      "Ed Mylett",         "https://www.youtube.com/@EdMylettShow/videos", 5),
    ("sharran",     "Sharran Srivatsaa", "https://www.youtube.com/@sharran/videos", 5),
    ("kagan",       "Noah Kagan",        "https://www.youtube.com/@noahkagan/videos", 5),
    ("koe",         "Dan Koe",           "https://www.youtube.com/@DanKoeTalks/videos", 5),
    ("doac",        "Diary of a CEO",    "https://www.youtube.com/@TheDiaryOfACEO/videos", 5),
    ("abdaal",      "Ali Abdaal",        "https://www.youtube.com/@aliabdaal/videos", 5),
    ("sahil",       "Sahil Bloom",       "https://www.youtube.com/@sahil_bloom/videos", 5),
    ("codie",       "Codie Sanchez",     "https://www.youtube.com/@CodieSanchezCT/videos", 5),
    ("leila",       "Leila Hormozi",     "https://www.youtube.com/@LeilaHormozi/videos", 5),
]

YT_DLP = "yt-dlp"


def fetch_creator(slug: str, url: str, n: int):
    """Use yt-dlp --flat-playlist to grab top N videos, sorted by views via 'popular' tab."""
    # Try popular tab first for top-by-views ordering
    popular_url = url.replace("/videos", "/videos?view=0&sort=p&flow=grid")
    cmd = [
        YT_DLP,
        "--flat-playlist",
        "--dump-json",
        "--playlist-end", str(n),
        "-I", f"1:{n}",
        popular_url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, encoding="utf-8")
        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        if not lines:
            print(f"  [{slug}] popular tab empty, falling back to /videos")
            cmd[-1] = url
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, encoding="utf-8")
            lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        out = []
        for line in lines:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            vid = d.get("id")
            if not vid:
                continue
            out.append({
                "id": vid,
                "title": d.get("title", ""),
                "views": d.get("view_count") or 0,
                "url": f"https://www.youtube.com/watch?v={vid}",
            })
        return out
    except Exception as e:
        print(f"  [{slug}] ERROR: {e}")
        return []


def download_thumb(video_id: str, dest: Path):
    if dest.exists() and dest.stat().st_size > 1000:
        return True
    # Try maxres first, then hqdefault
    for variant in ("maxresdefault.jpg", "hqdefault.jpg"):
        thumb_url = f"https://i.ytimg.com/vi/{video_id}/{variant}"
        try:
            req = Request(thumb_url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=20) as r:
                data = r.read()
                if len(data) > 1000:
                    dest.write_bytes(data)
                    return True
        except Exception:
            continue
    return False


def main():
    all_data = {}
    for slug, name, url, n in CREATORS:
        print(f"Fetching {name}...")
        videos = fetch_creator(slug, url, n)
        if not videos:
            print(f"  [{slug}] NO VIDEOS FOUND")
            all_data[slug] = {"name": name, "videos": []}
            continue
        # Sort by views desc when populated
        videos.sort(key=lambda v: v["views"] or 0, reverse=True)
        for i, v in enumerate(videos[:n], 1):
            thumb_path = THUMBS / f"{slug}_{i}.jpg"
            ok = download_thumb(v["id"], thumb_path)
            v["thumb"] = f"thumbnails/{thumb_path.name}" if ok else None
            v["rank"] = i
            print(f"    {i}. {v['title'][:60]:60s} | {v['views']:>12,} | {'OK' if ok else 'MISS'}")
        all_data[slug] = {"name": name, "videos": videos[:n]}
        time.sleep(0.4)

    out = DATA / "creators.json"
    out.write_text(json.dumps(all_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
