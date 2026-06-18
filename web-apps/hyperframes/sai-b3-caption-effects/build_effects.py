"""Generate 3 caption-effect test comps (same words, different animation).

Brand: Montserrat SemiBold, lowercase, no punctuation, white + orange #F28129,
strong drop shadow, lower-third. Each effect runs over the same 6s bg clip so
Gray can compare the ANIMATION directly. Winner gets rebuilt as a full alpha
ProRes caption layer.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORANGE = "#F28129"
W, H, TOTAL = 1920, 1080, 6.0
# (line text, keyword shown in orange)
LINES = [("business is spiritual", "spiritual"),
         ("align your values", "values"),
         ("money follows you", "money")]
S = [0.0, 2.0, 4.0]   # each line shows for 2s


def words_html(i, text, kw):
    spans = ""
    for j, w in enumerate(text.split()):
        cls = "w kw" if w == kw else "w"
        spans += f'<span class="{cls}" id="l{i}w{j}">{w}</span> '
    return spans


def lines_html(with_bar=False):
    out = ""
    for i, (text, kw) in enumerate(LINES):
        bar = '<span class="bar"></span>' if with_bar else ""
        out += f'  <div class="capline" id="line{i}">{words_html(i, text, kw)}{bar}</div>\n'
    return out


def show_hide():
    """Hard-cut visibility per brand no-flicker rule (no fade between lines)."""
    js = ""
    for i in range(len(LINES)):
        js += f'  tl.set("#line{i}", {{opacity: 1}}, {S[i]});\n'
        if i + 1 < len(LINES):
            js += f'  tl.set("#line{i}", {{opacity: 0}}, {S[i+1]});\n'
    return js


def fx_karaoke():
    js = show_hide()
    for i, (text, kw) in enumerate(LINES):
        for j, w in enumerate(text.split()):
            t = round(S[i] + 0.15 + j * 0.17, 3)
            rest = ORANGE if w == kw else "#ffffff"
            js += f'  tl.from("#l{i}w{j}", {{opacity: 0, y: 12, duration: 0.22, ease: "power2.out"}}, {t});\n'
            js += f'  tl.fromTo("#l{i}w{j}", {{color: "{ORANGE}"}}, {{color: "{rest}", duration: 0.40, ease: "power1.out"}}, {t});\n'
    return js


def fx_slam():
    js = show_hide()
    for i in range(len(LINES)):
        t = round(S[i] + 0.10, 3)
        js += (f'  tl.from("#line{i} .w", {{scale: 2.3, opacity: 0, rotation: -5, '
               f'transformOrigin: "50% 50%", duration: 0.34, stagger: 0.13, ease: "back.out(2)"}}, {t});\n')
    return js


def fx_slide():
    js = show_hide()
    for i in range(len(LINES)):
        t = round(S[i] + 0.10, 3)
        js += (f'  tl.from("#line{i} .w", {{yPercent: 130, opacity: 0, '
               f'duration: 0.42, stagger: 0.08, ease: "power3.out"}}, {t});\n')
        js += (f'  tl.from("#line{i} .bar", {{scaleX: 0, transformOrigin: "0% 50%", '
               f'duration: 0.5, ease: "power2.out"}}, {round(t + 0.08, 3)});\n')
    return js


EFFECTS = {
    "fx1-karaoke": (False, fx_karaoke, "word-by-word reveal with an orange highlight flash"),
    "fx2-slam":    (False, fx_slam,    "each word slams in big with a bouncy overshoot"),
    "fx3-slide":   (True,  fx_slide,   "words slide up smoothly + an orange underline wipes in"),
}


def build(name, with_bar, fx, _desc):
    html = f'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  #root {{ position: relative; width: {W}px; height: {H}px; background: #000; overflow: hidden; font-family: 'Montserrat', sans-serif; }}
  #root video {{ position: absolute; inset: 0; width: {W}px; height: {H}px; object-fit: cover; z-index: 1; }}
  .capline {{ position: absolute; left: 0; right: 0; bottom: 120px; text-align: center; opacity: 0; z-index: 5; }}
  .w {{ display: inline-block; font-weight: 600; font-size: 66px; color: #fff; margin: 0 7px;
        text-shadow: 0 3px 10px rgba(0,0,0,.9), 0 0 3px rgba(0,0,0,.95); }}
  .kw {{ color: {ORANGE}; }}
  .bar {{ display: block; height: 7px; width: 240px; background: {ORANGE}; margin: 14px auto 0; border-radius: 4px;
          box-shadow: 0 2px 8px rgba(0,0,0,.6); }}
</style>
</head>
<body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-start="0" data-duration="{TOTAL}">
  <video src="bg.mp4" muted playsinline data-start="0" data-duration="{TOTAL}" data-track-index="0"></video>
{lines_html(with_bar)}
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <script>
  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{ paused: true }});
{fx()}
  window.__timelines["root"] = tl;
  </script>
</div>
</body>
</html>
'''
    (HERE / f"{name}.html").write_text(html, encoding="utf-8")
    print(f"wrote {name}.html")


if __name__ == "__main__":
    for name, (bar, fx, desc) in EFFECTS.items():
        build(name, bar, fx, desc)
