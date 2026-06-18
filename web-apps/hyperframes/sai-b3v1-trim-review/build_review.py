"""Generate a HyperFrames trim-review composition.

Each kept sentence becomes a sequenced video+audio clip pulled straight from a
proxy via data-media-start, placed back-to-back. A lower-third read-along shows
the sentence text so Gray can verify CONTENT + COMPLETENESS + ORDER, not just
hear it. This is a REVIEW tool (B-cam proxy, 720p) — final render uses A-cam
Rode audio for the answer + B-cam audio for the question.

Edit SEGMENTS and re-run. One number per cut point — no re-render needed.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
HEAD, TAIL = 0.10, 0.25
W, H = 1280, 720

# src proxy, source-in, source-out, read-along text
# (B-cam / MVI_5041 timecodes; bcam.mp4 is the 720p proxy)
SEGMENTS = [
    ("bcam.mp4", 26.60, 30.36, "What do you believe about business that almost everyone disagrees with?", "HOOK — your question"),
    ("bcam.mp4", 67.44, 69.44, "I think business is spiritual.", ""),
    ("bcam.mp4", 73.10, 78.36, "You learn more about yourself through building something authentically than you learn through anything else.", ""),
    ("bcam.mp4", 110.88, 115.30, "And in that same sense, the more you align yourself deeply with your morals and ethics,", ""),
    ("bcam.mp4", 118.16, 123.32, "you'll interestingly find that opportunities start to find you.", ""),
    ("bcam.mp4", 142.68, 146.48, "The universe starts bringing the right people into your orbit.", ""),
    ("bcam.mp4", 149.66, 152.00, "And as a result, you start to make more money.", ""),
    ("bcam.mp4", 156.16, 161.10, "So I'd say, the more aligned you are with your values and ethics, the more money you make in business.", ""),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    clips, caps = [], []
    cum_ms = 0  # integer milliseconds -> no float drift, exact touch boundaries
    for i, (src, sin, sout, text, tag) in enumerate(SEGMENTS):
        media_in = max(0.0, sin - HEAD)
        dur_ms = round(((sout + TAIL) - media_in) * 1000)
        start = cum_ms / 1000
        dur = (dur_ms - 3) / 1000  # 3ms sub-frame guard so float end never overlaps next start
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
