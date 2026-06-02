"""Re-run fetch for only the 3 creators that came back empty initially.

Merges into existing creators.json without re-fetching the others.
"""
import json, subprocess, time
from pathlib import Path
from urllib.request import urlopen, Request
import sys
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
THUMBS = ROOT / "thumbnails"
DATA = ROOT / "data"

TARGETS = [
    ("mylett", "Ed Mylett",   "https://www.youtube.com/@EdMylettShow/videos", 5),
    ("koe",    "Dan Koe",     "https://www.youtube.com/@DanKoeTalks/videos", 5),
    ("sahil",  "Sahil Bloom", "https://www.youtube.com/@sahil_bloom/videos", 5),
]

def fetch(url, n):
    popular = url.replace("/videos", "/videos?view=0&sort=p&flow=grid")
    for u in (popular, url):
        cmd = ["yt-dlp", "--flat-playlist", "--dump-json", "-I", f"1:{n}", u]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, encoding="utf-8")
        lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
        if lines:
            out = []
            for line in lines:
                try:
                    d = json.loads(line)
                except: continue
                if d.get("id"):
                    out.append({
                        "id": d["id"],
                        "title": d.get("title",""),
                        "views": d.get("view_count") or 0,
                        "url": f"https://www.youtube.com/watch?v={d['id']}",
                    })
            if out: return out
    return []

def dl_thumb(vid, dest):
    if dest.exists() and dest.stat().st_size > 1000:
        return True
    for v in ("maxresdefault.jpg", "hqdefault.jpg"):
        try:
            req = Request(f"https://i.ytimg.com/vi/{vid}/{v}", headers={"User-Agent":"Mozilla/5.0"})
            with urlopen(req, timeout=20) as r:
                data = r.read()
                if len(data) > 1000:
                    dest.write_bytes(data); return True
        except: continue
    return False

# Load existing
path = DATA / "creators.json"
data = json.loads(path.read_text(encoding="utf-8"))

# Strip Sai
data.pop("sai", None)
for f in THUMBS.glob("sai_*.jpg"):
    f.unlink()

for slug, name, url, n in TARGETS:
    print(f"Fetching {name}...")
    videos = fetch(url, n)
    if not videos:
        print(f"  STILL EMPTY")
        continue
    for i, v in enumerate(videos[:n], 1):
        # Remove stale jpg if exists
        dest = THUMBS / f"{slug}_{i}.jpg"
        if dest.exists(): dest.unlink()
        ok = dl_thumb(v["id"], dest)
        v["thumb"] = f"thumbnails/{dest.name}" if ok else None
        v["rank"] = i
        print(f"  {i}. {v['title'][:60]:60s} | {'OK' if ok else 'MISS'}")
    data[slug] = {"name": name, "videos": videos[:n]}
    time.sleep(0.3)

path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("Done")
