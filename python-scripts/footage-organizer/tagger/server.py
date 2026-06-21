#!/usr/bin/env python3
"""Local b-roll tagging dashboard (v4, Phase 4).

A browser editor for the b-roll tags:
  - thumbnail grid + full-clip video scrubbing (lazy-loaded so 200+ clips are fine)
  - inline edit of emotion / action / location (autocomplete) + objects (chips)
  - shift-select multiple clips → bulk-apply a tag
  - type a new value → it's remembered in tagger/vocab.json and autocompletes next time
Writes go straight to the SQLite index (index.update_tags).

Run:  python tagger/server.py --client sai [--vertical N] [--port 4600]
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
                    VIDEO_EXTENSIONS, EMOTION_TAGS, ACTION_TAGS)
from extractor import get_display_orientation

LIBRARY = Path(".")
DB = Path(".")
VERTICAL_N = None
_THUMB_DIR = Path(tempfile.gettempdir()) / "broll-review-thumbs"
VOCAB_FILE = Path(__file__).resolve().parent / "vocab.json"
_TAG_FIELDS = ("emotion", "action", "location")


# ── vocabulary (seed + vocab.json + live index values) ──────────────────────

def _load_vocab_file() -> dict:
    if VOCAB_FILE.exists():
        try:
            return json.loads(VOCAB_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _vocab() -> dict:
    base = {"emotion": set(EMOTION_TAGS), "action": set(ACTION_TAGS),
            "location": set(), "object": set()}
    filev = _load_vocab_file()
    dist = index.distinct_tag_values(DB)
    for k in base:
        base[k] |= set(filev.get(k, [])) | set(dist.get(k, []))
    return {k: sorted(v) for k, v in base.items()}


def _remember_vocab(field: str, value: str):
    """Persist a newly-typed tag value so it autocompletes next session."""
    value = (value or "").strip()
    if not value or field not in ("emotion", "action", "location", "object"):
        return
    filev = _load_vocab_file()
    lst = filev.setdefault(field, [])
    if value not in lst:
        lst.append(value)
        VOCAB_FILE.write_text(json.dumps(filev, indent=2), encoding="utf-8")


# ── clip listing ────────────────────────────────────────────────────────────

def _clip_dict(r):
    week = next((p for p in r.path.split("/") if p.startswith("W") or p == "unknown-week"), "")
    return {"path": r.path, "name": Path(r.path).name,
            "emotion": r.emotion or "", "action": r.action or "",
            "location": r.location or "", "objects": index.unpack_objects(r.objects),
            "week": week}


def _vertical_sample(n: int):
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
        out.append({"path": rel, "name": clip.name, "emotion": "VERTICAL",
                    "action": "rotation-flag" if flipped else "native-portrait",
                    "location": week, "objects": [], "week": week})
    return out


def _clips():
    if VERTICAL_N:
        return _vertical_sample(VERTICAL_N)
    recs = index.query(DB, category=FOLDER_BROLL)
    return [_clip_dict(r) for r in recs]


# ── files ────────────────────────────────────────────────────────────────────

def _safe_clip_path(rel: str):
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


_PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<title>B-roll tagger</title>
<style>
  body{background:#111;color:#eee;font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:0 24px 80px}
  header{position:sticky;top:0;background:#111;padding:18px 0 10px;z-index:10;border-bottom:1px solid #222}
  h1{font-size:17px;font-weight:600;margin:0}
  .sub{color:#888;font-size:12px;margin-top:3px}
  .bulk{margin-top:10px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;opacity:.4;pointer-events:none}
  .bulk.on{opacity:1;pointer-events:auto}
  .bulk select,.bulk input,.bulk button{background:#1e1e1e;color:#eee;border:1px solid #333;border-radius:6px;padding:5px 8px;font-size:13px}
  .bulk button{background:#2a5;border-color:#2a5;cursor:pointer;font-weight:600}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:18px;margin-top:18px}
  .card{background:#1b1b1b;border:1px solid #2a2a2a;border-radius:10px;overflow:hidden;position:relative}
  .card.sel{border-color:#5ec8ff;box-shadow:0 0 0 2px #5ec8ff55}
  .pick{position:absolute;top:8px;left:8px;width:20px;height:20px;z-index:3;cursor:pointer}
  video{width:100%;display:block;background:#000;aspect-ratio:16/9;object-fit:contain}
  .meta{padding:10px 12px}
  .name{color:#777;font-size:11px;margin-bottom:8px}
  .row{display:flex;align-items:center;gap:6px;margin:5px 0}
  .row label{width:60px;color:#999;font-size:11px;text-transform:uppercase;letter-spacing:.04em}
  .row input{flex:1;background:#161616;color:#eee;border:1px solid #2e2e2e;border-radius:5px;padding:4px 7px;font-size:13px}
  .row input.em{color:#ff9b3d}.row input.ac{color:#5ec8ff}.row input.lo{color:#9be36a}
  .objs{display:flex;flex-wrap:wrap;gap:5px;margin-top:6px}
  .chip{background:#262626;border:1px solid #333;border-radius:999px;padding:2px 8px;font-size:11px;color:#ccc;display:flex;gap:5px;align-items:center}
  .chip b{cursor:pointer;color:#e66}
  .objs input{background:#161616;color:#eee;border:1px solid #2e2e2e;border-radius:999px;padding:2px 8px;font-size:11px;width:90px}
  .saved{position:absolute;top:8px;right:10px;color:#2a5;font-size:11px;opacity:0;transition:opacity .2s}
  .saved.show{opacity:1}
</style></head><body>
<header>
  <h1>B-roll tagger</h1>
  <div class="sub" id="sub">loading…</div>
  <div class="bulk" id="bulk">
    <span id="selcount">0 selected</span>
    <select id="bfield"><option value="emotion">emotion</option><option value="action">action</option><option value="location">location</option><option value="object">+ object</option></select>
    <input id="bval" list="dl-emotion" placeholder="value…">
    <button id="bapply">Apply to selected</button>
    <button id="bclear" style="background:#333;border-color:#333">clear selection</button>
  </div>
</header>
<datalist id="dl-emotion"></datalist><datalist id="dl-action"></datalist>
<datalist id="dl-location"></datalist><datalist id="dl-object"></datalist>
<div class="grid" id="grid"></div>
<script>
let CLIPS=[], VOCAB={}, sel=new Set(), lastIdx=null;

function fillDatalist(id, arr){const d=document.getElementById(id);d.innerHTML=arr.map(v=>`<option value="${v.replace(/"/g,'&quot;')}">`).join('');}
function refreshVocab(){return fetch('/api/vocab').then(r=>r.json()).then(v=>{VOCAB=v;
  fillDatalist('dl-emotion',v.emotion);fillDatalist('dl-action',v.action);
  fillDatalist('dl-location',v.location);fillDatalist('dl-object',v.object);});}

function save(body){return fetch('/api/tag',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(r=>r.json());}
function flash(card){const s=card.querySelector('.saved');s.classList.add('show');setTimeout(()=>s.classList.remove('show'),700);}

function objChips(c){
  return c.objects.map(o=>`<span class="chip">${o}<b data-o="${o.replace(/"/g,'&quot;')}">×</b></span>`).join('')
    + `<input class="objadd" list="dl-object" placeholder="+ object">`;
}

function render(){
  const g=document.getElementById('grid');g.innerHTML='';
  CLIPS.forEach((c,i)=>{
    const div=document.createElement('div');div.className='card'+(sel.has(c.path)?' sel':'');div.dataset.i=i;
    div.innerHTML=`<input type="checkbox" class="pick" ${sel.has(c.path)?'checked':''}>
      <span class="saved">saved</span>
      <video controls preload="none" data-src="/video?path=${encodeURIComponent(c.path)}" data-poster="/thumb?path=${encodeURIComponent(c.path)}"></video>
      <div class="meta">
        <div class="name">${c.name} · ${c.week}</div>
        <div class="row"><label>emotion</label><input class="em f" data-f="emotion" list="dl-emotion" value="${c.emotion}"></div>
        <div class="row"><label>action</label><input class="ac f" data-f="action" list="dl-action" value="${c.action}"></div>
        <div class="row"><label>location</label><input class="lo f" data-f="location" list="dl-location" value="${c.location}"></div>
        <div class="objs">${objChips(c)}</div>
      </div>`;
    g.appendChild(div);
  });
  io_observe();
}

// lazy-load video src + poster only when a card scrolls into view
let io;
function io_observe(){
  io = io || new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){const v=e.target.querySelector('video');
    if(v&&!v.src){v.poster=v.dataset.poster;v.src=v.dataset.src;}io.unobserve(e.target);}});},{rootMargin:'300px'});
  document.querySelectorAll('.card').forEach(c=>io.observe(c));
}

function setSelCount(){const n=sel.size;document.getElementById('selcount').textContent=n+' selected';
  document.getElementById('bulk').classList.toggle('on',n>0);}

document.getElementById('grid').addEventListener('change',e=>{
  const card=e.target.closest('.card'); if(!card) return; const c=CLIPS[+card.dataset.i];
  if(e.target.classList.contains('pick')){
    const i=+card.dataset.i;
    if(e.target.checked) sel.add(c.path); else sel.delete(c.path);
    card.classList.toggle('sel',e.target.checked); lastIdx=i; setSelCount(); return;
  }
  if(e.target.classList.contains('f')){
    const f=e.target.dataset.f, val=e.target.value.trim();
    c[f]=val; save({paths:[c.path],set:{[f]:val}}).then(()=>{flash(card);refreshVocab();});
  }
});

// shift-click range select on checkboxes
document.getElementById('grid').addEventListener('click',e=>{
  if(e.target.classList.contains('pick') && e.shiftKey && lastIdx!==null){
    const i=+e.target.closest('.card').dataset.i, [a,b]=[Math.min(i,lastIdx),Math.max(i,lastIdx)];
    for(let k=a;k<=b;k++){sel.add(CLIPS[k].path);}
    render(); setSelCount();
  }
});

// object add (enter) + remove (×)
document.getElementById('grid').addEventListener('keydown',e=>{
  if(e.target.classList.contains('objadd') && e.key==='Enter'){
    const card=e.target.closest('.card'), c=CLIPS[+card.dataset.i], val=e.target.value.trim();
    if(!val) return;
    save({paths:[c.path],add_object:val}).then(()=>{if(!c.objects.includes(val))c.objects.push(val);render();refreshVocab();});
  }
});
document.getElementById('grid').addEventListener('click',e=>{
  if(e.target.tagName==='B' && e.target.dataset.o!==undefined){
    const card=e.target.closest('.card'), c=CLIPS[+card.dataset.i], val=e.target.dataset.o;
    save({paths:[c.path],remove_object:val}).then(()=>{c.objects=c.objects.filter(o=>o!==val);render();});
  }
});

// bulk apply
document.getElementById('bfield').addEventListener('change',e=>{
  document.getElementById('bval').setAttribute('list','dl-'+(e.target.value==='object'?'object':e.target.value));});
document.getElementById('bapply').addEventListener('click',()=>{
  const f=document.getElementById('bfield').value, val=document.getElementById('bval').value.trim();
  const paths=[...sel]; if(!paths.length||!val) return;
  const body = f==='object' ? {paths,add_object:val} : {paths,set:{[f]:val}};
  save(body).then(()=>{
    CLIPS.forEach(c=>{if(sel.has(c.path)){ if(f==='object'){if(!c.objects.includes(val))c.objects.push(val);} else c[f]=val; }});
    render(); refreshVocab(); document.getElementById('bval').value='';
  });
});
document.getElementById('bclear').addEventListener('click',()=>{sel.clear();render();setSelCount();});

Promise.all([fetch('/api/clips').then(r=>r.json()), refreshVocab()]).then(([clips])=>{
  CLIPS=clips;
  document.getElementById('sub').textContent=clips.length+' b-roll clips — edit inline; check + shift-click to multi-select, then bulk-apply';
  render();
});
</script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _q(self):
        return urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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
            self._json(_clips())
        elif route == "/api/vocab":
            self._json(_vocab())
        elif route == "/thumb":
            target = _safe_clip_path((self._q().get("path") or [""])[0])
            self._send_file(_thumb(target) if target else None, "image/jpeg", allow_range=False)
        elif route == "/video":
            target = _safe_clip_path((self._q().get("path") or [""])[0])
            self._send_file(target, "video/mp4", allow_range=True)
        else:
            self.send_error(404)

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/api/tag":
            self.send_error(404); return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self._json({"error": "bad json"}, 400); return
        if VERTICAL_N:  # read-only orientation-review mode
            self._json({"error": "read-only"}, 403); return

        paths = data.get("paths") or []
        sets = data.get("set") or {}
        add_object = (data.get("add_object") or "").strip()
        remove_object = (data.get("remove_object") or "").strip()

        for path in paths:
            kwargs = {f: sets[f] for f in _TAG_FIELDS if f in sets}
            if "objects" in sets:
                kwargs["objects"] = index.pack_objects(sets["objects"])
            if kwargs:
                index.update_tags(DB, path, **kwargs)
            if add_object or remove_object:
                rec = index.get(DB, path)
                objs = index.unpack_objects(rec.objects) if rec else []
                if add_object and add_object not in objs:
                    objs.append(add_object)
                if remove_object and remove_object in objs:
                    objs.remove(remove_object)
                index.update_tags(DB, path, objects=index.pack_objects(objs))

        for f in _TAG_FIELDS:
            if sets.get(f):
                _remember_vocab(f, sets[f])
        for o in (sets.get("objects") or []):
            _remember_vocab("object", o)
        if add_object:
            _remember_vocab("object", add_object)

        self._json({"ok": True})

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
    global LIBRARY, DB, VERTICAL_N
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", default="sai")
    ap.add_argument("--vertical", type=int, metavar="N", help="Read-only: show first N detected-vertical clips (orientation check)")
    ap.add_argument("--port", type=int, default=4600)
    args = ap.parse_args()

    root = CLIENT_ROOTS.get(args.client, "")
    if not root or not Path(root).exists():
        print(f"Error: {args.client.upper()}_LIBRARY_ROOT not set or missing")
        sys.exit(1)
    LIBRARY = Path(root)
    DB = LIBRARY / INDEX_DB_NAME
    VERTICAL_N = args.vertical

    mode = f"vertical-review ({args.vertical})" if args.vertical else "edit"
    print(f"\n  B-roll tagger [{mode}] — {len(_clips())} clip(s)")
    print(f"  Open:  http://localhost:{args.port}\n  Ctrl-C to stop.\n")
    http.server.ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
