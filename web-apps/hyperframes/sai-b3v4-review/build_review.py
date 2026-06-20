"""Generate the HyperFrames trim-review composition for Batch 3 Vid 4
("Money reflects who you are").

Each kept sentence becomes a sequenced video+audio clip pulled straight from the
720p B-cam proxy (bcam.mp4) via data-media-start, placed back-to-back. A
lower-third read-along shows the sentence text so Gray can verify CONTENT +
COMPLETENESS + ORDER, not just hear it. REVIEW tool only — final render uses the
lav-mic camera's audio.

All timecodes are B-cam SYNCED time (B-cam synced == B-cam original, offset 0).
Sai answers TWICE; Take 1 was rejected on camera. This is Take 2 (the redo).
Edit SEGMENTS and re-run. One number per cut point — no re-render needed.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
HEAD, TAIL = 0.10, 0.25
W, H = 1280, 720

# src proxy, source-in, source-out, read-along text, tag, head-pad, tail-pad (None = default)
SEGMENTS = [
    ("bcam.mp4", 14.30, 18.88, "How has your relationship with money changed?", "HOOK — your question", None, None),
    ("bcam.mp4", 188.16, 190.96, "Money is, at the end of the day, just a reflection of you.", "", None, None),
    ("bcam.mp4", 191.86, 195.08, "People will say money is money — regardless of how you make it.", "", None, None),
    ("bcam.mp4", 196.60, 207.42, "But I found in my life that when I act out of my values and out of my ethics, money will come — but it never stays.", "", None, None),
    # 2nd "but when..." take (drops the doubled false start at 210.3-212.9); tiny tail so the held "the" after "me," is not grabbed
    ("bcam.mp4", 212.90, 217.10, "But when I'm deeply aligned with my values and act in a way that's authentic to me,", "", None, 0.05),
    # the SECOND "the money actually sticks" flows straight into "and weirdly..." -> one clean clip, no internal cut
    ("bcam.mp4", 221.56, 224.78, "the money actually sticks — and weirdly, I make more of it.", "", 0.08, None),
    ("bcam.mp4", 233.32, 237.18, "So before, it was: how do I chase money? How do I make a ton of money?", "", None, None),
    ("bcam.mp4", 238.22, 242.40, "Now it's: how do I show up as the person who's capable of making money?", "", None, None),
    # closer rings out -> longer tail
    ("bcam.mp4", 243.16, 245.88, "And that simple frame shift has changed everything for me.", "", None, 0.40),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    clips, caps = [], []
    cum_ms = 0  # integer milliseconds -> no float drift, exact touch boundaries
    for i, (src, sin, sout, text, tag, head, tail) in enumerate(SEGMENTS):
        head = HEAD if head is None else head
        tail = TAIL if tail is None else tail
        media_in = max(0.0, sin - head)
        dur_ms = round(((sout + tail) - media_in) * 1000)
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
