"""Generate the 4 small lower-third step title cards for Vid 6 (locked Sai title-card style:
rounded dark bar + orange number badge + white summary, slide-up + fade, transparent/alpha).
Writes step-N/index.html for each."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    (1, "Review what went wrong"),
    (2, "Implement the changes"),
    (3, "Reorder it chronologically"),
    (4, "Simplify — cut the rest"),
    (5, "Creators fill out a feedback form"),
]

TPL = r"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1080, height=1920">
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden;
        background: transparent; font-family: "Montserrat", system-ui, sans-serif; }
      .scene { position: relative; width: 100%; height: 100%; overflow: hidden; }

      /* small lower-third card */
      .card { position: absolute; left: 150px; top: 1500px; width: 780px; height: 168px;
        border-radius: 26px; display: flex; align-items: center; gap: 26px; padding: 0 30px;
        opacity: 0; will-change: transform, opacity;
        background: linear-gradient(120deg, #2C2825 0%, #211D1A 60%, #181513 100%);
        box-shadow: inset 0 2px 5px rgba(255,255,255,0.07), 0 16px 34px rgba(0,0,0,0.5); }

      /* orange number badge */
      .badge { flex: 0 0 auto; width: 108px; height: 108px; border-radius: 22px;
        display: flex; align-items: center; justify-content: center; opacity: 0;
        will-change: transform, opacity;
        background: linear-gradient(150deg, #FFC68A 0%, #F28129 55%, #D66416 100%);
        border: 2px solid #fff; box-shadow: 0 0 22px rgba(242,129,41,0.5), 0 8px 18px rgba(0,0,0,0.32); }
      .badge span { font-weight: 900; font-size: 64px; color: #fff; letter-spacing: -0.02em;
        text-shadow: 0 3px 8px rgba(0,0,0,0.35); font-variant-numeric: tabular-nums; }

      .text { display: flex; flex-direction: column; gap: 4px; }
      .kick { font-weight: 800; font-size: 24px; letter-spacing: 0.14em; color: #F28129;
        text-transform: uppercase; opacity: 0; will-change: transform, opacity; }
      .label { font-weight: 800; font-size: 46px; color: #fff; letter-spacing: -0.01em; line-height: 1.05;
        max-width: 540px; opacity: 0; will-change: transform, opacity;
        text-shadow: 0 3px 10px rgba(0,0,0,0.4); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="3" data-width="1080" data-height="1920">
      <div id="scene" class="scene clip" data-start="0" data-duration="3" data-track-index="1">
        <div id="card" class="card">
          <div id="badge" class="badge"><span>__NUM__</span></div>
          <div class="text">
            <div id="kick" class="kick">Step __NUM__</div>
            <div id="label" class="label">__LABEL__</div>
          </div>
        </div>
      </div>
    </div>
    <script>
      (function () {
        window.__timelines = window.__timelines || {};
        const tl = gsap.timeline({ paused: true });
        // card slides up + fades in (no exit — the Premiere cut ends it)
        tl.fromTo("#card", { opacity: 0, y: 46 }, { opacity: 1, y: 0, duration: 0.55, ease: "power3.out", immediateRender: false }, 0.1);
        tl.fromTo("#badge", { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.7)", immediateRender: false }, 0.28);
        tl.fromTo("#kick", { opacity: 0, x: -14 }, { opacity: 1, x: 0, duration: 0.4, ease: "power2.out", immediateRender: false }, 0.42);
        tl.fromTo("#label", { opacity: 0, x: -14 }, { opacity: 1, x: 0, duration: 0.45, ease: "power2.out", immediateRender: false }, 0.5);
        window.__timelines["main"] = tl;
      })();
    </script>
  </body>
</html>
"""

for num, label in STEPS:
    d = os.path.join(HERE, f"step-{num}")
    os.makedirs(d, exist_ok=True)
    html = TPL.replace("__NUM__", str(num)).replace("__LABEL__", label)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html)
    print("wrote", f"step-{num}/index.html")
