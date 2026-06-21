#!/usr/bin/env python3
"""Local b-roll review dashboard (v4).

Phase 3.5 — a verification view: plays each tagged b-roll clip in the browser
with its Vision tags (emotion · action · location + objects) shown as the title,
so Gray can cross-reference accuracy before committing to the full tagging pass.
Phase 4 will add in-place editing + bulk-apply on top of this same server.

Run:  python tagger/server.py --client sai [--limit N] [--all] [--port 4600]
Then open the printed http://localhost:<port> URL.
"""
import argparse
import http.server
import json
import os
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import index
from config import (CLIENT_ROOTS, INDEX_DB_NAME, FOLDER_BROLL, FOLDER_FOOTAGE_LIB,
                    VIDEO_EXTENSIONS)
from extractor import get_display_orientation

LIBRARY = Path(".")
DB = Path(".")
SHOW_ALL = False
LIMIT = None
VERTICAL_N = None  # when set, show the first N detected-vertical b-roll clips instead
_THUMB_DIR = Path(tempfile.gettempdir()) / "broll-review-thumbs"


def _vertical_sample(n: int):
    """First n b-roll clips that detect as vertical — for confirming the split
    before parking them. Title shows the orientation, video plays so you can see it."""
    broll = LIBRARY / FOLDER_FOOTAGE_LIB / FOLDER_BROLL
    out = []
    for clip in sorted(broll.rglob("*")):
        if len(out) >= n:
            break
        if not clip.is_file() or clip.suffix not in VIDEO_EXTENSIONS or clip.name.startswith("._"):
            continue
        orientation, flipped = get_display_orientation(str(clip))
        if orientation != "vertical":
            continue
        rel = clip.relative_to(LIBRARY).as_posix()
        week = next((p for p in rel.split("/") if p.startswith("W") or p == "unknown-week"), "")
        out.append({
            "path": rel, "name": clip.name,
            "emotion": "VERTICAL",
            "action": "rotation-flag" if flipped else "native-portrait",
            "location": week, "objects": [],
        })
    return out


def _clips():
    if VERTICAL_N:
        return _vertical_sample(VERTICAL_N)
    recs = index.query(DB, category=FOLDER_BROLL)
    if not SHOW_ALL:
        recs = [r for r in recs if (r.emotion or r.action or r.location or r.objects)]
    if LIMIT:
        recs = recs[:LIMIT]
    return [{
        "path": r.path,
        "name": Path(r.path).name,
        "emotion": r.emotion or "",
        "action": r.action or "",
        "location": r.location or "",
        "objects": index.unpack_objects(r.objects),
    } for r in recs]


def _safe_clip_path(rel: str):
    """Resolve a request path to a real file, confined to the b-roll library
    (05_FOOTAGE_LIBRARY/b-roll/). Blocks path traversal outside that subtree."""
    broll = (LIBRARY / FOLDER_FOOTAGE_LIB / FOLDER_BROLL).resolve()
    target = (LIBRARY / rel).resolve()
    if broll not in target.parents or not target.is_file():
        return None
    return target


def _thumb(target: Path) -> Path:
    _THUMB_DIR.mkdir(parents=True, exist_ok=True)
    out = _THUMB_DIR / (str(abs(hash(str(target)))) + ".jpg")
    if not out.exists():
        subprocess.run(["ffmpeg", "-ss", "1", "-i", str(target), "-frames:v", "1",
                        "-vf", "scale=480:-1", "-q:v", "4", "-y", str(out)],
                       capture_output=True)
    return out


_PAGE = """<!doctype html><html><head><meta charset="utf-8">
<title>B-roll tag review</title>
<style>
  body{background:#111;color:#eee;font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:24px}
  h1{font-size:18px;font-weight:600;margin:0 0 4px}
  .sub{color:#888;font-size:13px;margin-bottom:20px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:20px}
  .card{background:#1b1b1b;border:1px solid #2a2a2a;border-radius:10px;overflow:hidden}
  video{width:100%;display:block;background:#000;aspect-ratio:16/9;object-fit:contain}
  .meta{padding:12px 14px}
  .title{font-size:15px;font-weight:600;margin-bottom:6px}
  .title .em{color:#ff9b3d}.title .ac{color:#5ec8ff}.title .lo{color:#9be36a}
  .name{color:#777;font-size:12px;margin-bottom:8px}
  .objs{display:flex;flex-wrap:wrap;gap:5px}
  .chip{background:#262626;border:1px solid #333;border-radius:999px;padding:2px 9px;font-size:11px;color:#bbb}
</style></head><body>
<h1>B-roll tag review</h1>
<div class="sub" id="sub">loading…</div>
<div class="grid" id="grid"></div>
<script>
fetch('/api/clips').then(r=>r.json()).then(clips=>{
  document.getElementById('sub').textContent =
    clips.length + ' tagged clip(s) — title is emotion · action · location; play to cross-reference';
  const g=document.getElementById('grid');
  for(const c of clips){
    const enc=encodeURIComponent(c.path);
    const objs=c.objects.map(o=>`<span class="chip">${o}</span>`).join('');
    const title=[c.emotion?`<span class="em">${c.emotion}</span>`:'',
                 c.action?`<span class="ac">${c.action}</span>`:'',
                 c.location?`<span class="lo">${c.location}</span>`:'']
                .filter(Boolean).join(' &middot; ') || '(no tags)';
    g.insertAdjacentHTML('beforeend',
      `<div class="card">
         <video controls preload="metadata" poster="/thumb?path=${enc}">
           <source src="/video?path=${enc}">
         </video>
         <div class="meta">
           <div class="title">${title}</div>
           <div class="name">${c.name}</div>
           <div class="objs">${objs}</div>
         </div>
       </div>`);
  }
});
</script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def _q(self):
        return urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

    def do_GET(self):
        route = urllib.parse.urlparse(self.path).path
        if route == "/":
            body = _PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif route == "/api/clips":
            body = json.dumps(_clips()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif route == "/thumb":
            self._send_file(self._thumb_path(), "image/jpeg", allow_range=False)
        elif route == "/video":
            rel = (self._q().get("path") or [""])[0]
            target = _safe_clip_path(rel)
            if not target:
                self.send_error(404); return
            self._send_file(target, "video/mp4", allow_range=True)
        else:
            self.send_error(404)

    def _thumb_path(self):
        rel = (self._q().get("path") or [""])[0]
        target = _safe_clip_path(rel)
        return _thumb(target) if target else None

    def _send_file(self, target, content_type, allow_range):
        if not target or not Path(target).is_file():
            self.send_error(404); return
        size = os.path.getsize(target)
        rng = self.headers.get("Range") if allow_range else None
        if rng and rng.startswith("bytes="):
            start_s, _, end_s = rng[6:].partition("-")
            start = int(start_s) if start_s else 0
            end = int(end_s) if end_s else size - 1
            end = min(end, size - 1)
            length = end - start + 1
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            start, length = 0, size
            self.send_response(200)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        with open(target, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(1 << 20, remaining))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    break
                remaining -= len(chunk)


def main():
    global LIBRARY, DB, SHOW_ALL, LIMIT, VERTICAL_N
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", default="sai")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--all", action="store_true", help="Show all b-roll clips, not just tagged ones")
    ap.add_argument("--vertical", type=int, metavar="N", help="Show the first N detected-vertical b-roll clips (orientation-split confirmation)")
    ap.add_argument("--port", type=int, default=4600)
    args = ap.parse_args()

    root = CLIENT_ROOTS.get(args.client, "")
    if not root or not Path(root).exists():
        print(f"Error: {args.client.upper()}_LIBRARY_ROOT not set or missing")
        sys.exit(1)
    LIBRARY = Path(root)
    DB = LIBRARY / INDEX_DB_NAME
    SHOW_ALL = args.all
    LIMIT = args.limit
    VERTICAL_N = args.vertical

    n = len(_clips())
    print(f"\n  B-roll tag review — {n} clip(s)")
    print(f"  Open:  http://localhost:{args.port}\n  Ctrl-C to stop.\n")
    http.server.ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
