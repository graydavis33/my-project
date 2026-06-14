"""
story-arc-board/server.py

Local web server for the long-form story-arc board.

Folder-scoped by design: you point it at ONE specific footage folder
(the week's raw long-form / A-roll). It scans that folder for video files,
generates a thumbnail per clip, and serves them as draggable cards.
It NEVER pulls arbitrary clips from the whole footage library.

The SQLite footage index is used ONLY to enrich metadata (filmed_date)
for clips that already live under the library root and are indexed.
If the drive/index isn't mounted, scanning still works via ffprobe.

Run:
    cd web-apps/story-arc-board
    python server.py                 # serves http://localhost:4500
    python server.py --port 4600
"""

import hashlib
import json
import os
import socketserver
import subprocess
import sqlite3
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
THUMB_DIR = os.path.join(HERE, ".thumbs")
BOARD_DIR = os.path.join(HERE, "boards")
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}

# Library root + index (read-only enrichment). Drive may be unmounted — that's fine.
LIBRARY_ROOT = os.environ.get("SAI_LIBRARY_ROOT", "D:/Sai")
INDEX_DB = os.path.join(LIBRARY_ROOT, ".footage-index.sqlite")

os.makedirs(THUMB_DIR, exist_ok=True)
os.makedirs(BOARD_DIR, exist_ok=True)


def clip_id(path: str) -> str:
    return hashlib.sha1(path.encode("utf-8")).hexdigest()[:16]


def ffprobe_meta(path: str):
    """Return (duration_s, width, height) via ffprobe. Best-effort."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height:format=duration",
             "-of", "json", path],
            capture_output=True, text=True, check=True,
        ).stdout
        data = json.loads(out)
        st = (data.get("streams") or [{}])[0]
        dur = float(data.get("format", {}).get("duration", 0) or 0)
        return dur, int(st.get("width", 0) or 0), int(st.get("height", 0) or 0)
    except Exception:
        return 0.0, 0, 0


def index_lookup():
    """Return {posix_rel_path: filmed_date} from the footage index, or {} if unreachable."""
    if not os.path.exists(INDEX_DB):
        return {}
    try:
        con = sqlite3.connect(f"file:{INDEX_DB}?mode=ro", uri=True)
        rows = con.execute("SELECT path, filmed_date FROM clips").fetchall()
        con.close()
        return {r[0]: r[1] for r in rows}
    except Exception:
        return {}


def scan_folder(folder: str, recursive: bool):
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        return {"error": f"Not a folder: {folder}"}

    idx = index_lookup()
    root_abs = os.path.abspath(LIBRARY_ROOT)
    clips = []

    if recursive:
        walker = (os.path.join(d, f) for d, _, fs in os.walk(folder) for f in fs)
    else:
        walker = (os.path.join(folder, f) for f in os.listdir(folder))

    for p in walker:
        if not os.path.isfile(p):
            continue
        name = os.path.basename(p)
        if name.startswith("._") or os.path.splitext(name)[1].lower() not in VIDEO_EXTS:
            continue
        dur, w, h = ffprobe_meta(p)
        filmed = ""
        try:
            rel = os.path.relpath(os.path.abspath(p), root_abs).replace("\\", "/")
            if not rel.startswith(".."):
                filmed = idx.get(rel, "")
        except ValueError:
            pass
        clips.append({
            "id": clip_id(os.path.abspath(p)),
            "path": os.path.abspath(p),
            "name": name,
            "duration": round(dur, 1),
            "width": w,
            "height": h,
            "vertical": h > w if (w and h) else False,
            "filmed_date": filmed,
        })

    clips.sort(key=lambda c: (c["filmed_date"], c["name"]))
    return {"folder": folder, "indexed": bool(idx), "count": len(clips), "clips": clips}


def make_thumb(path: str) -> str:
    """Generate (and cache) a JPEG thumbnail at the clip midpoint. Returns thumb path or ''."""
    tid = clip_id(os.path.abspath(path))
    out = os.path.join(THUMB_DIR, f"{tid}.jpg")
    if os.path.exists(out):
        return out
    if not os.path.isfile(path):
        return ""
    dur, _, _ = ffprobe_meta(path)
    seek = max(0.0, dur * 0.5)
    try:
        subprocess.run(
            ["ffmpeg", "-ss", f"{seek:.3f}", "-i", path, "-frames:v", "1",
             "-vf", "scale=320:-1", "-q:v", "4", "-y", out],
            check=True, capture_output=True,
        )
        return out if os.path.exists(out) else ""
    except Exception:
        return ""


def slugify(name: str) -> str:
    keep = "".join(c if c.isalnum() or c in " -_" else "" for c in name).strip()
    return ("-".join(keep.split()) or "board").lower()[:60]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, fname, ctype):
        fp = os.path.join(HERE, fname)
        if not os.path.exists(fp):
            self._send(404, {"error": "not found"})
            return
        with open(fp, "rb") as f:
            self._send(200, f.read(), ctype)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        route = u.path

        if route == "/":
            self._file("index.html", "text/html; charset=utf-8")
        elif route == "/app.js":
            self._file("app.js", "application/javascript")
        elif route == "/style.css":
            self._file("style.css", "text/css")
        elif route == "/api/scan":
            folder = (q.get("folder") or [""])[0]
            recursive = (q.get("recursive") or ["0"])[0] == "1"
            if not folder:
                self._send(400, {"error": "folder required"})
                return
            self._send(200, scan_folder(folder, recursive))
        elif route == "/api/thumb":
            path = (q.get("path") or [""])[0]
            thumb = make_thumb(path)
            if not thumb:
                self._send(404, {"error": "no thumb"})
                return
            with open(thumb, "rb") as f:
                self._send(200, f.read(), "image/jpeg")
        elif route == "/api/boards":
            names = [f[:-5] for f in os.listdir(BOARD_DIR) if f.endswith(".json")]
            self._send(200, {"boards": sorted(names)})
        elif route == "/api/board":
            name = slugify((q.get("name") or [""])[0])
            fp = os.path.join(BOARD_DIR, f"{name}.json")
            if not os.path.exists(fp):
                self._send(404, {"error": "no such board"})
                return
            with open(fp, encoding="utf-8") as f:
                self._send(200, f.read())
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        if u.path != "/api/board":
            self._send(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length))
        except Exception:
            self._send(400, {"error": "bad json"})
            return
        name = slugify(data.get("name", ""))
        fp = os.path.join(BOARD_DIR, f"{name}.json")
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self._send(200, {"ok": True, "name": name})


def main():
    port = 4500
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])

    class Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
        daemon_threads = True

    print(f"Story-Arc Board -> http://localhost:{port}")
    print(f"Library root (enrichment): {LIBRARY_ROOT}  (index {'found' if os.path.exists(INDEX_DB) else 'NOT mounted'})")
    with Server(("127.0.0.1", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nbye")


if __name__ == "__main__":
    main()
