import base64, html, io
from pathlib import Path
from PIL import Image

BASE = Path(__file__).parent
FONT = Path("C:/Users/Gray Davis/my-project/python-scripts/sai-captions/fonts/Montserrat.ttf")

def b64_font(p):
    return base64.b64encode(p.read_bytes()).decode()

def b64_img(p, w=1040):
    im = Image.open(p).convert("RGB")
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=86)
    return base64.b64encode(buf.getvalue()).decode()

def caption_html(txt):
    out = []
    for line in txt.rstrip("\n").split("\n"):
        if line.strip() == "":
            out.append('<div class="sp"></div>')
        else:
            out.append(f"<div>{html.escape(line)}</div>")
    return "\n".join(out)

posts = [
    dict(id="36", tag="Story / lesson", lane="Lane 2 — text + still",
         cap=(BASE/"36-dropped-out/caption.txt").read_text(encoding="utf-8"),
         img=b64_img(BASE/"36-dropped-out/LINKEDIN-IMAGE.jpg"),
         src="Raw clip C2208 (Central Park) — no captions, no graphics",
         window="Tue-Thu, 8-10am ET"),
    dict(id="11", tag="Raw / gear", lane="Lane 2 — text + still",
         cap=(BASE/"11-3-purchases/caption.txt").read_text(encoding="utf-8"),
         img=b64_img(BASE/"11-3-purchases/LINKEDIN-IMAGE.jpg"),
         src="Raw clip C2782 (productivity shoot) — no captions, no graphics",
         window="Weekday, 8-11am ET"),
]

font_b64 = b64_font(FONT)

cards = ""
for p in posts:
    cards += f"""
    <article class="card">
      <div class="head">
        <div class="avatar">SK</div>
        <div class="who">
          <div class="name">Sai Karra</div>
          <div class="role">Founder, Trendify</div>
        </div>
        <div class="draft">DRAFT</div>
      </div>
      <div class="cap">{caption_html(p['cap'])}</div>
      <figure class="shot"><img alt="Paired image for post {p['id']}" src="data:image/jpeg;base64,{p['img']}"></figure>
      <div class="meta">
        <span class="pill">{html.escape(p['tag'])}</span>
        <dl>
          <div><dt>Format</dt><dd>{html.escape(p['lane'])}</dd></div>
          <div><dt>Image source</dt><dd>{html.escape(p['src'])}</dd></div>
          <div><dt>Suggested window</dt><dd>{html.escape(p['window'])}</dd></div>
        </dl>
      </div>
    </article>"""

doc = f"""<title>LinkedIn Draft Review — Sai Karra</title>
<style>
@font-face{{font-family:'Montserrat';src:url(data:font/ttf;base64,{font_b64}) format('truetype');font-weight:100 900;font-display:swap}}
:root{{
  --bg:#f6f4f1;--surface:#ffffff;--ink:#1a1a1a;--muted:#6b6560;--line:#e8e3dc;
  --accent:#F28129;--accent-ink:#b85e13;--shadow:0 1px 2px rgba(26,20,12,.05),0 8px 24px rgba(26,20,12,.06);
}}
@media (prefers-color-scheme:dark){{:root{{
  --bg:#141312;--surface:#1f1c1a;--ink:#f3f0ec;--muted:#a99e93;--line:#302b27;
  --accent:#F28129;--accent-ink:#f8a35a;--shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
}}}}
:root[data-theme="light"]{{
  --bg:#f6f4f1;--surface:#ffffff;--ink:#1a1a1a;--muted:#6b6560;--line:#e8e3dc;
  --accent:#F28129;--accent-ink:#b85e13;--shadow:0 1px 2px rgba(26,20,12,.05),0 8px 24px rgba(26,20,12,.06);
}}
:root[data-theme="dark"]{{
  --bg:#141312;--surface:#1f1c1a;--ink:#f3f0ec;--muted:#a99e93;--line:#302b27;
  --accent:#F28129;--accent-ink:#f8a35a;--shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased;line-height:1.5}}
.wrap{{max-width:1120px;margin:0 auto;padding:40px 24px 64px}}
header{{border-bottom:1px solid var(--line);padding-bottom:22px;margin-bottom:30px}}
.eyebrow{{font-family:'Montserrat';font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  font-size:11px;color:var(--accent-ink);margin:0 0 10px}}
h1{{font-family:'Montserrat';font-weight:800;font-size:clamp(26px,4vw,38px);margin:0;letter-spacing:-.01em;text-wrap:balance}}
.lede{{color:var(--muted);margin:12px 0 0;max-width:60ch;font-size:15px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:26px;align-items:start}}
.card{{background:var(--surface);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);overflow:hidden}}
.head{{display:flex;align-items:center;gap:12px;padding:18px 20px 12px}}
.avatar{{width:44px;height:44px;border-radius:50%;flex:none;display:grid;place-items:center;
  background:var(--accent);color:#fff;font-family:'Montserrat';font-weight:800;font-size:15px;letter-spacing:.02em}}
.who{{flex:1;min-width:0}}
.name{{font-family:'Montserrat';font-weight:700;font-size:15px}}
.role{{color:var(--muted);font-size:13px}}
.draft{{font-family:'Montserrat';font-weight:700;font-size:10px;letter-spacing:.12em;color:var(--accent-ink);
  border:1px solid var(--accent);border-radius:999px;padding:4px 10px}}
.cap{{padding:4px 20px 16px;font-size:15px;color:var(--ink)}}
.cap .sp{{height:12px}}
.shot{{margin:0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}
.shot img{{display:block;width:100%;height:auto}}
.meta{{padding:16px 20px 20px}}
.pill{{display:inline-block;font-family:'Montserrat';font-weight:700;font-size:11px;letter-spacing:.06em;
  text-transform:uppercase;color:var(--accent-ink);background:color-mix(in srgb,var(--accent) 14%,transparent);
  border-radius:6px;padding:4px 9px;margin-bottom:12px}}
dl{{margin:0;display:grid;gap:8px}}
dl>div{{display:grid;grid-template-columns:120px 1fr;gap:10px;font-size:13px}}
dt{{color:var(--muted)}}
dd{{margin:0;color:var(--ink)}}
footer{{margin-top:34px;color:var(--muted);font-size:12.5px;border-top:1px solid var(--line);padding-top:18px}}
</style>
<div class="wrap">
  <header>
    <p class="eyebrow">Graydient Media &middot; IG &rarr; LinkedIn repurpose</p>
    <h1>LinkedIn Draft Review</h1>
    <p class="lede">Two test posts for Sai's LinkedIn, repurposed from posted reels. Captions are in Sai's voice; images are raw frames from the actual footage &mdash; no burned captions, no graphics, nothing AI-edited. Nothing is posted yet. Note any changes and they get folded back into the drafting.</p>
  </header>
  <div class="grid">{cards}
  </div>
  <footer>Drafts generated {Path(__file__).stat().st_mtime and ''}2026-08-05. Preview only &mdash; posting happens manually on the scheduled day.</footer>
</div>
"""

out = BASE/"PREVIEW.html"
out.write_text(doc, encoding="utf-8")
print("wrote", out, f"({len(doc)//1024} KB)")
