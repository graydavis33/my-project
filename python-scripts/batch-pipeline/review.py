"""HyperFrames trim-review comp builder.

Ports web-apps/hyperframes/sai-b3v13-trim-review/build_review.py into a reusable
pipeline function. Given a list of kept sentence segments (B-cam source times) and
a 720p B-cam proxy, writes an index.html HyperFrames comp where each segment is a
sequenced video+audio clip pulled from the proxy via data-media-start, placed
back-to-back, with a read-along lower-third caption.
"""
import subprocess
from pathlib import Path

HEAD, TAIL = 0.10, 0.25
W, H = 1280, 720


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def make_proxy(bcam_video: Path, out_proxy: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(bcam_video),
         "-vf", "scale=1280:720", "-c:v", "libx264", "-crf", "23",
         "-preset", "veryfast", "-c:a", "aac", "-b:a", "160k", str(out_proxy)],
        check=True,
    )


def build_review(segments: list, proxy_filename: str, out_dir: Path,
                  head: float = 0.10, tail: float = 0.25) -> Path:
    out_dir = Path(out_dir)
    clips, caps = [], []
    cum_ms = 0
    for i, seg in enumerate(segments):
        sin = seg["in"]
        sout = seg["out"]
        text = seg["text"]
        tag = seg.get("tag", "")
        seg_tail = seg.get("tail")
        seg_tail = tail if seg_tail is None else seg_tail
        media_in = max(0.0, sin - head)
        dur_ms = round(((sout + seg_tail) - media_in) * 1000)
        start = cum_ms / 1000
        dur = (dur_ms - 3) / 1000
        clips.append(
            f'  <video id="v{i}" src="{proxy_filename}" muted playsinline '
            f'data-start="{start:.3f}" data-duration="{dur:.3f}" data-media-start="{media_in:.3f}" data-track-index="0"></video>\n'
            f'  <audio id="a{i}" src="{proxy_filename}" '
            f'data-start="{start:.3f}" data-duration="{dur:.3f}" data-media-start="{media_in:.3f}" data-volume="1" data-track-index="1"></audio>'
        )
        tagline = f'<span class="tag">{esc(tag)}</span>' if tag else ""
        caps.append(
            f'  <div id="cap{i}" class="clip cap" data-start="{start:.3f}" data-duration="{dur:.3f}" data-track-index="2">'
            f'{tagline}<span class="txt">{esc(text)}</span><span class="seg">{i+1} / {len(segments)}</span></div>')
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
    out_path = out_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path
