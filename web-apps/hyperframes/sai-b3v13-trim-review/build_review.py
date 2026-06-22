"""Vid_13 'The Real Lever Is You' HyperFrames trim-review comp. B-cam (MVI_5046_v13) time."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
HEAD, TAIL = 0.10, 0.25
W, H = 1280, 720

SEGMENTS = [
    ("bcam.mp4", 13.84, 16.42, "What's the real lever everyone else is ignoring?", "HOOK — your question", None, None),
    ("bcam.mp4", 27.22, 31.18, "The real lever is you, and how you feel about yourself.", "", None, None),
    ("bcam.mp4", 42.00, 45.64, "At the end of the day, everything that you build comes from you.", "", None, None),
    ("bcam.mp4", 47.68, 52.28, "And if you're fully aligned, then everything that you produce will also be aligned.", "", None, None),
    ("bcam.mp4", 82.50, 86.74, "And if you're just able to show up as the most aligned version of yourself every day to work,", "", None, None),
    ("bcam.mp4", 92.00, 94.26, "every other lever will pull itself automatically.", "", None, 0.80),
    ("bcam.mp4", 102.86, 105.80, "So I think you should start asking questions like, why do I not feel good today?", "", None, None),
    ("bcam.mp4", 106.78, 109.02, "Why am I scared today? Why am I sad today?", "", None, None),
    ("bcam.mp4", 110.68, 114.38, "Instead of asking what course should I take, what book should I read.", "", None, None),
    ("bcam.mp4", 115.66, 122.60, "Because once you solve the former, you'll realize that you don't need anything else.", "", None, 0.80),
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
        dur = (dur_ms - 3) / 1000
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


if __name__ == "__main__":
    main()
