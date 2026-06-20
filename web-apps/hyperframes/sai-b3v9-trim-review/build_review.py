"""Vid_09 'Structure Frees Creativity' HyperFrames trim-review composition.

Each kept sentence becomes a sequenced video+audio clip pulled from the 720p B-cam
proxy via data-media-start, placed back-to-back, with a lower-third read-along so
Gray can verify CONTENT + COMPLETENESS + ORDER while scrubbing. REVIEW tool only.

Edit SEGMENTS and re-run. Timecodes are MVI_5046_v09.MP4 (B-cam) time.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
HEAD, TAIL = 0.10, 0.25
W, H = 1280, 720

# src proxy, source-in, source-out, read-along text, tag, head-pad, tail-pad
SEGMENTS = [
    ("bcam.mp4", 7.78, 10.74, "Why does more structure make you creative, not less?", "HOOK — your question", None, None),
    ("bcam.mp4", 38.06, 42.10, "What I learned through time is that structure and creativity aren't polar opposites.", "", None, None),
    ("bcam.mp4", 43.04, 44.80, "They actually feed into one another.", "", None, None),
    ("bcam.mp4", 48.16, 52.36, "If you're really creative and have no structure, you'll probably be a one-hit wonder.", "", None, None),
    ("bcam.mp4", 54.60, 59.20, "And if you have a lot of structure and no creativity, you won't be unique and authentic.", "", None, None),
    ("bcam.mp4", 67.88, 72.52, "And so the way that you strike that perfect balance is by adding structure to your creativity.", "", None, None),
    ("bcam.mp4", 74.66, 78.74, "Which basically means, what do you do once you actually come up with an idea?", "", None, None),
    ("bcam.mp4", 81.34, 84.40, "The idea and coming up with it is the creative part.", "", None, None),
    ("bcam.mp4", 85.34, 87.18, "Everything else should be a system.", "", None, None),
    ("bcam.mp4", 92.68, 98.48, "You should come up with a framework or something that you follow every single time, in order to go from idea to actual execution.", "", None, None),
    # tail=0.80: Whisper marks "implemented." end early; let it ring out
    ("bcam.mp4", 100.70, 107.70, "That way you know that you can just crank out ideas and that they actually get implemented.", "", None, 0.80),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    clips, caps = [], []
    cum_ms = 0
    for i, (src, sin, sout, text, tag, head, tail) in enumerate(SEGMENTS):
        head = HEAD if head is None else head
        tail = TAIL if tail is None else tail
        media_in = max(0.0, sin - head)
        dur_ms = round(((sout + tail) - media_in) * 1000)
        start = cum_ms / 1000
        dur = (dur_ms - 3) / 1000  # 3ms sub-frame guard
        clips.append(
            f'  <video id="v{i}" src="{src}" muted playsinline '
            f'data-start="{start:.3f}" data-duration="{dur:.3f}" data-media-start="{media_in:.3f}" data-track-index="0"></video>\n'
            f'  <audio id="a{i}" src="{src}" '
            f'data-start="{start:.3f}" data-duration="{dur:.3f}" data-media-start="{media_in:.3f}" data-volume="1" data-track-index="1"></audio>'
        )
        tagline = f'<span class="tag">{esc(tag)}</span>' if tag else ""
        caps.append(
            f'  <div id="cap{i}" class="clip cap" data-start="{start:.3f}" data-duration="{dur:.3f}" data-track-index="2">'
            f'{tagline}<span class="txt">{esc(text)}</span><span class="seg">{i+1} / {len(SEGMENTS)}</span></div>')
        cum_ms += dur_ms

    total = cum_ms / 1000
    html = f'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  #root {{ position: relative; width: {W}px; height: {H}px; background: #000; overflow: hidden; font-family: 'Montserrat', sans-serif; }}
  #root video {{ position: absolute; top: 0; left: 0; width: {W}px; height: {H}px; object-fit: cover; z-index: 1; }}
  #root .cap {{ position: absolute; left: 0; right: 0; bottom: 54px; text-align: center; padding: 0 90px; z-index: 5; }}
  #root .cap .txt {{ display: inline-block; color: #fff; font-size: 30px; font-weight: 600; line-height: 1.3;
            text-shadow: 0 4px 14px rgba(0,0,0,.85); background: rgba(0,0,0,.34); padding: 10px 20px; border-radius: 10px; }}
  #root .cap .tag {{ display: block; color: #F28129; font-size: 18px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; margin-bottom: 10px; text-shadow: 0 2px 8px rgba(0,0,0,.9); }}
  #root .cap .seg {{ position: absolute; top: -2px; right: 24px; color: rgba(255,255,255,.55); font-size: 16px; font-weight: 600; }}
</style>
</head>
<body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-start="0" data-duration="{total:.3f}">
{chr(10).join(clips)}
{chr(10).join(caps)}
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <script>
  window.__timelines = window.__timelines || {{}};
  window.__timelines["root"] = gsap.timeline({{ paused: true }});
  </script>
</div>
</body>
</html>
'''
    (HERE / "index.html").write_text(html, encoding="utf-8")
    print(f"wrote index.html  |  {len(SEGMENTS)} segments  |  total {total:.2f}s")
    json.dump([{"i": i, "src": s[0], "in": s[1], "out": s[2], "text": s[3]} for i, s in enumerate(SEGMENTS)],
              open(HERE / "segments.json", "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
