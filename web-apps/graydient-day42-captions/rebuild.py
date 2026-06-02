"""Regenerate index.html from captions.json.

Edit captions.json to tweak any chunk's text, timing, or is_aroll classification.
Run `python rebuild.py` to apply changes. HyperFrames preview hot-reloads.

For continuous auto-rebuild on save, run `python watch.py` instead.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).parent
CAPTIONS_PATH = ROOT / "captions.json"
INDEX_PATH = ROOT / "index.html"


def main() -> int:
    if not CAPTIONS_PATH.exists():
        print(f"ERROR: {CAPTIONS_PATH} not found")
        return 1

    data = json.loads(CAPTIONS_PATH.read_text(encoding="utf-8"))
    dur = float(data["video_duration"])
    hook = data["hook"]
    body = data["body_chunks"]
    hook_end = float(hook["end_time"])

    # Hook word spans (with keyword styling)
    hook_spans = ""
    for i, w in enumerate(hook["words"]):
        cls = "kw" if w["is_keyword"] else "rw"
        # safely escape any HTML special chars
        display = (w["display"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        hook_spans += f'<span class="hw {cls}" id="hw{i}">{display}</span>'

    # Body chunks split into two layered containers
    aroll_html = ""
    broll_html = ""
    for i, c in enumerate(body):
        safe = c["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if c.get("is_aroll"):
            aroll_html += f'<div class="bc bc-aroll" id="bc{i}">{safe}</div>'
        else:
            broll_html += f'<div class="bc bc-broll" id="bc{i}">{safe}</div>'

    # GSAP tweens — hook (per-word typewriter)
    hook_tweens = []
    for i, w in enumerate(hook["words"]):
        hook_tweens.append(f'  tl.set("#hw{i}", {{opacity:0, y:14}}, 0);')
        hook_tweens.append(f'  tl.to("#hw{i}", {{opacity:1, y:0, duration:0.20, ease:"power2.out"}}, {float(w["start"]):.3f});')
    hook_tweens.append(f'  tl.to(".hook-block", {{opacity:0, y:-12, duration:0.30, ease:"power2.in"}}, {hook_end:.3f});')
    hook_tweens.append(f'  tl.set(".hook-block", {{visibility:"hidden"}}, {hook_end + 0.30:.3f});')

    # GSAP tweens — body
    body_tweens = []
    for i, c in enumerate(body):
        s = float(c["start"]); e = float(c["end"])
        body_tweens.append(f'  tl.set("#bc{i}", {{opacity:0, y:18, visibility:"hidden"}}, 0);')
        body_tweens.append(f'  tl.set("#bc{i}", {{visibility:"visible"}}, {s:.3f});')
        body_tweens.append(f'  tl.to("#bc{i}", {{opacity:1, y:0, duration:0.18, ease:"power3.out"}}, {s:.3f});')
        next_start = float(body[i+1]["start"]) if i + 1 < len(body) else dur
        fade_out_at = min(e + 0.05, next_start - 0.10)
        if fade_out_at > s + 0.20:
            body_tweens.append(f'  tl.to("#bc{i}", {{opacity:0, duration:0.15, ease:"power2.in"}}, {fade_out_at:.3f});')

    hook_tw = "\n".join(hook_tweens)
    body_tw = "\n".join(body_tweens)

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <link rel="preconnect" href="https://fonts.googleapis.com" crossorigin="anonymous" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link href="https://fonts.googleapis.com/css2?family=Anton&family=Montserrat:wght@600;700&display=swap" rel="stylesheet" crossorigin="anonymous" />
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <style>
    @font-face {{
      font-family: 'Anton';
      font-style: normal;
      font-weight: 400;
      src: url('https://fonts.gstatic.com/s/anton/v25/1Ptgg87LROyAm0K08i4gS7lu.woff2') format('woff2');
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{
      margin: 0; width: 1080px; height: 1920px;
      overflow: hidden; background: #000;
    }}
    #day42-captions {{
      position: relative;
      width: 1080px; height: 1920px;
      background: #000;
      overflow: hidden;
      font-family: 'Montserrat', sans-serif;
    }}
    .video-wrap {{
      position: absolute; inset: 0;
      width: 1080px; height: 1920px;
      overflow: hidden;
    }}
    .video-wrap video {{
      width: 100%; height: 100%; object-fit: cover;
    }}
    .hook-block {{
      position: absolute;
      top: 370px;
      left: 90px; right: 90px;
      width: 900px;
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      align-items: baseline;
      gap: 0 14px;
      row-gap: 14px;
      z-index: 10;
      text-align: center;
      color: #ffffff;
      filter: drop-shadow(0 3px 8px rgba(0,0,0,0.55));
    }}
    .hw {{ display: inline-block; line-height: 1.05; }}
    .hw.rw {{
      font-family: 'Montserrat', sans-serif;
      font-weight: 600; font-size: 64px;
      color: #ffffff;
    }}
    .hw.kw {{
      font-family: 'Anton', 'Montserrat', sans-serif;
      font-weight: 400; font-size: 78px;
      color: #FFD60A;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .body-block-aroll, .body-block-broll {{
      position: absolute;
      left: 90px; right: 90px;
      width: 900px;
      z-index: 10;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .body-block-aroll {{ top: 320px; height: 240px; }}
    .body-block-broll {{ top: 880px; height: 280px; }}
    .bc {{
      position: absolute;
      width: 100%;
      font-family: 'Montserrat', sans-serif;
      font-weight: 600; font-size: 62px;
      line-height: 1.18;
      color: #ffffff;
      text-align: center;
      filter: drop-shadow(0 3px 7px rgba(0,0,0,0.6));
    }}
  </style>
</head>
<body>
  <div id="day42-captions" data-composition-id="day42-captions" data-start="0" data-duration="{dur}" data-track-index="0" data-width="1080" data-height="1920">
    <div class="video-wrap">
      <video id="day42-video"
             data-start="0" data-duration="{dur}" data-track-index="1"
             src="assets/day42_final.mp4"
             muted playsinline></video>
    </div>
    <audio id="day42-audio"
           data-start="0" data-duration="{dur}" data-track-index="2"
           src="assets/day42_final.m4a"
           data-volume="1" preload="auto"></audio>

    <div class="hook-block">{hook_spans}</div>
    <div class="body-block-aroll">{aroll_html}</div>
    <div class="body-block-broll">{broll_html}</div>
  </div>

  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
{hook_tw}
{body_tw}
    window.__timelines["day42-captions"] = tl;
  </script>
</body>
</html>
"""
    INDEX_PATH.write_text(html, encoding="utf-8")
    n_aroll = sum(1 for c in body if c.get("is_aroll"))
    n_broll = len(body) - n_aroll
    print(f"Rebuilt index.html: hook={len(hook['words'])}w, body={len(body)} chunks ({n_aroll} A-roll, {n_broll} B-roll)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
