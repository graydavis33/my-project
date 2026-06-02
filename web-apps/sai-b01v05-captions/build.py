"""Build a captions-ONLY layer (chroma green, no background video) for overlay
in Premiere. One layer. Follows the brand caption standard."""
from __future__ import annotations
import json, sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

HERE = Path(__file__).parent
DUR = 28.70
MAX_WORDS = 3
PAUSE_BREAK = 0.30
PROPER_NOUNS = set()  # add lowercase names here if any

raw = json.loads((HERE / "words.json").read_text(encoding="utf-8"))
words = []
for w in raw:
    tok = w["word"].strip()
    if tok.startswith("-") and words:
        words[-1]["word"] += tok; words[-1]["end"] = float(w["end"])
    else:
        words.append({"word": tok, "start": float(w["start"]), "end": float(w["end"])})

def style_word(tok):
    core = tok.strip('.,!?;:"“”()')
    low = core.lower()
    if low == "i" or low.startswith("i'") or low in PROPER_NOUNS:
        return low[0].upper() + low[1:]
    return low

def ends_sentence(tok): return tok.rstrip('"\'').endswith((".", "!", "?"))

groups, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    gap = (words[i+1]["start"] - w["end"]) if i+1 < len(words) else 999
    if len(cur) >= MAX_WORDS or ends_sentence(w["word"]) or gap >= PAUSE_BREAK:
        groups.append(cur); cur = []
if cur: groups.append(cur)

records = []
for gi, g in enumerate(groups):
    text = " ".join(style_word(x["word"]) for x in g).strip()
    start = float(g[0]["start"])
    end = float(groups[gi+1][0]["start"]) if gi+1 < len(groups) else min(DUR, float(g[-1]["end"]) + 0.5)
    records.append({"text": text, "start": round(start, 3), "end": round(end, 3)})

groups_json = json.dumps(records, ensure_ascii=False)
print(f"{len(words)} words -> {len(records)} groups")

HTML = '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: #00FF00; font-family: "Montserrat", system-ui, sans-serif; }
      .scene { position: relative; width: 100%; height: 100%; }
      #cap-layer { position: absolute; left: 0; right: 0; top: 900px; text-align: center; }
      .cap { position: absolute; left: 0; right: 0; top: 0; display: flex; justify-content: center; }
      .cap .txt {
        display: inline-block;
        font-family: "Montserrat", system-ui, sans-serif;
        font-weight: 600;
        font-size: 52px;
        line-height: 1.1;
        color: #FFFFFF;
        white-space: nowrap;
        letter-spacing: 0.005em;
        padding: 0 36px;
        text-shadow: 0 3px 10px rgba(0,0,0,0.9), 0 0 3px rgba(0,0,0,0.95);
        will-change: transform, opacity;
      }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="__DUR__" data-width="1080" data-height="1920">
      <div id="scene" class="scene clip" data-start="0" data-duration="__DUR__" data-track-index="1">
        <div id="cap-layer"></div>
      </div>
    </div>
    <script>
      (function () {
        var GROUPS = __GROUPS__;
        var layer = document.getElementById("cap-layer");
        var fit = (window.__hyperframes && window.__hyperframes.fitTextFontSize) ? window.__hyperframes.fitTextFontSize : null;
        GROUPS.forEach(function (g, i) {
          var cap = document.createElement("div"); cap.className = "cap"; cap.id = "cg-" + i;
          var txt = document.createElement("span"); txt.className = "txt"; txt.textContent = g.text;
          if (fit) { var r = fit(g.text, { fontFamily: "Montserrat", fontWeight: 600, maxWidth: 920, baseFontSize: 52, minFontSize: 34, step: 2 }); txt.style.fontSize = r.fontSize + "px"; }
          cap.appendChild(txt); layer.appendChild(cap);
        });
        window.__timelines = window.__timelines || {};
        var tl = gsap.timeline({ paused: true });
        GROUPS.forEach(function (g, i) {
          var el = document.getElementById("cg-" + i);
          gsap.set(el, { opacity: 0, scale: 0.92, transformOrigin: "50% 50%" });
          tl.to(el, { opacity: 1, scale: 1, duration: 0.13, ease: "back.out(1.6)" }, g.start);
          tl.set(el, { opacity: 0, visibility: "hidden" }, g.end);
        });
        window.__timelines["main"] = tl;
      })();
    </script>
  </body>
</html>
'''
HTML = HTML.replace("__GROUPS__", groups_json).replace("__DUR__", str(DUR))
(HERE / "index.html").write_text(HTML, encoding="utf-8")
print("wrote index.html")
