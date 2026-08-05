import base64, html, io
from pathlib import Path
from PIL import Image

BASE = Path(__file__).parent
FONT = Path("C:/Users/Gray Davis/my-project/python-scripts/sai-captions/fonts/Montserrat.ttf")

def bfont(): return base64.b64encode(FONT.read_bytes()).decode()
def bimg(p, w=680):
    im = Image.open(p).convert("RGB")
    if im.width > w: im = im.resize((w, round(im.height*w/im.width)))
    b = io.BytesIO(); im.save(b, "JPEG", quality=84)
    return base64.b64encode(b.getvalue()).decode()
def cap(t):
    return "\n".join('<div class="sp"></div>' if l.strip()=="" else f"<div>{html.escape(l)}</div>" for l in t.strip("\n").split("\n"))

# ---- caption versions (from the iteration history) ----
PUR_V1 = """Three purchases that actually changed how I work and sleep.

1. Monitor light
I've always struggled to find something that lit up my face without being a pain to set up.
This one plugs directly into my monitor.
Click the power button. Done.
Perfect lighting every time.

2. Whiteboard
Something about putting a marker down on a physical surface just does more for me than a to-do app.
You write it down. You look at it.
And when you cross something out, it actually feels like you got something done.
I use it constantly.

3. Eye mask
I paid a ridiculous amount of money for this thing.
Worth every penny.
Too much light in the room? Slap it on.
Traveling through New York City where it never actually gets dark? Slap it on.
Pitch black. Sleep like a baby.

What's one purchase you've made that actually moved the needle?"""

PUR_NOW = (BASE/"11-3-purchases/caption.txt").read_text(encoding="utf-8")

DROP_V1 = """I dropped out of college, did four years of high school online, and gave up my entire social life to build a business.

If I could go back, I would not do it the same way.

When you first start, the opportunities feel endless.

And they are.

But that same feeling convinces you that you can shortcut the path.

That success is months away, not years.

So even if you're winning on paper - everything still feels miserable.

Because the timeline in your head is wrong.

So here's what I did:

I stopped thinking in weeks.
I stopped thinking in months.

Now I try to think in 3, 5, 10-year windows.

When you zoom out that far, the bad days stop feeling like you're doomed.
The slow months stop feeling like failure.
The whole thing just feels different.

I'd only go back and do it all again if I could tell my younger self one thing:

It's going to take way longer than you think.

That's the whole point.

What would you go back and tell yourself?"""

DROP_NOW = (BASE/"36-dropped-out/caption.txt").read_text(encoding="utf-8")

img_candid = bimg(BASE/"11-3-purchases/LINKEDIN-IMAGE.jpg")
img_trip   = bimg(BASE/"11-3-purchases/LINKEDIN-IMAGE-triptych.jpg")
img_pen    = bimg(BASE/"11-3-purchases/LINKEDIN-IMAGE-pen.jpg")
img_drop   = bimg(BASE/"36-dropped-out/LINKEDIN-IMAGE.jpg")

def img_card(title, badge, b64, note):
    bcls = "cur" if badge=="CURRENT" else "old"
    return f"""<figure class="opt"><figcaption><span class="v {bcls}">{badge}</span> {html.escape(title)}</figcaption>
      <img alt="{html.escape(title)}" src="data:image/jpeg;base64,{b64}"><p class="note">{html.escape(note)}</p></figure>"""

def cap_card(title, badge, text):
    bcls = "cur" if badge=="CURRENT" else "old"
    n = len(text)
    return f"""<figure class="opt cap-opt"><figcaption><span class="v {bcls}">{badge}</span> {html.escape(title)} <span class="len">{n} chars</span></figcaption>
      <div class="cap">{cap(text)}</div></figure>"""

doc = f"""<title>LinkedIn Drafts — Version Compare</title>
<style>
@font-face{{font-family:'Montserrat';src:url(data:font/ttf;base64,{bfont()}) format('truetype');font-weight:100 900}}
:root{{--bg:#f6f4f1;--surface:#fff;--ink:#1a1a1a;--muted:#6b6560;--line:#e8e3dc;--accent:#F28129;--accent-ink:#b85e13;--old:#8a827a;--shadow:0 1px 2px rgba(26,20,12,.05),0 8px 22px rgba(26,20,12,.06)}}
@media(prefers-color-scheme:dark){{:root{{--bg:#141312;--surface:#1f1c1a;--ink:#f3f0ec;--muted:#a99e93;--line:#302b27;--accent:#F28129;--accent-ink:#f8a35a;--old:#8a807655;--shadow:0 1px 2px rgba(0,0,0,.3),0 10px 28px rgba(0,0,0,.35)}}}}
:root[data-theme="light"]{{--bg:#f6f4f1;--surface:#fff;--ink:#1a1a1a;--muted:#6b6560;--line:#e8e3dc;--accent-ink:#b85e13}}
:root[data-theme="dark"]{{--bg:#141312;--surface:#1f1c1a;--ink:#f3f0ec;--muted:#a99e93;--line:#302b27;--accent-ink:#f8a35a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;line-height:1.5;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1160px;margin:0 auto;padding:40px 24px 70px}}
.eyebrow{{font-family:'Montserrat';font-weight:700;letter-spacing:.14em;text-transform:uppercase;font-size:11px;color:var(--accent-ink);margin:0 0 8px}}
h1{{font-family:'Montserrat';font-weight:800;font-size:clamp(24px,3.6vw,34px);margin:0}}
.lede{{color:var(--muted);margin:10px 0 0;max-width:62ch;font-size:15px}}
h2{{font-family:'Montserrat';font-weight:800;font-size:19px;margin:44px 0 4px;border-top:1px solid var(--line);padding-top:26px}}
.sub{{color:var(--muted);font-size:13px;margin:0 0 18px}}
.row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;align-items:start}}
.opt{{margin:0;background:var(--surface);border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:var(--shadow)}}
figcaption{{font-family:'Montserrat';font-weight:600;font-size:13px;padding:12px 14px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
.v{{font-family:'Montserrat';font-weight:800;font-size:10px;letter-spacing:.08em;padding:3px 8px;border-radius:999px}}
.v.cur{{color:#fff;background:var(--accent)}}
.v.old{{color:var(--muted);border:1px solid var(--line)}}
.len{{margin-left:auto;color:var(--muted);font-weight:500;font-size:11px}}
.opt img{{display:block;width:100%;height:auto;border-top:1px solid var(--line)}}
.note{{margin:0;padding:10px 14px;font-size:12.5px;color:var(--muted)}}
.cap{{padding:6px 16px 16px;font-size:14.5px}}
.cap .sp{{height:11px}}
.cap-opt figcaption{{border-bottom:1px solid var(--line)}}
</style>
<div class="wrap">
  <p class="eyebrow">Graydient Media &middot; draft iteration</p>
  <h1>LinkedIn Drafts &mdash; Version Compare</h1>
  <p class="lede">Every version of the two test posts side by side, oldest to current. The orange <b>CURRENT</b> tag marks what's live in the main preview now. The live preview page also has a version picker if you want to see full past layouts.</p>

  <h2>3 Purchases &mdash; image options</h2>
  <p class="sub">Same post, three image directions.</p>
  <div class="row">
    {img_card("Candid single frame", "V1", img_candid, "Raw frame of Sai talking in his room. Clean but the products aren't the subject.")}
    {img_card("Triptych (light / whiteboard / mask)", "V2", img_trip, "Rule-of-thirds, one object per panel. You didn't like this one.")}
    {img_card("Pen insert, full horizontal", "CURRENT", img_pen, "Full 1920x1080, no crop, no motion blur. The current pick.")}
  </div>

  <h2>3 Purchases &mdash; caption versions</h2>
  <p class="sub">From the first engine draft to the current numbered, tightened version.</p>
  <div class="row">
    {cap_card("First draft (long)", "V1", PUR_V1)}
    {cap_card("Numbered + tightened", "CURRENT", PUR_NOW)}
  </div>

  <h2>Dropped out of college</h2>
  <p class="sub">Image unchanged (you liked it). Caption went from long to tight.</p>
  <div class="row">
    {img_card("Central Park frame", "CURRENT", img_drop, "Raw frame C2208, unchanged across versions.")}
    {cap_card("First draft (long)", "V1", DROP_V1)}
    {cap_card("Tightened", "CURRENT", DROP_NOW)}
  </div>
</div>
"""
out = BASE/"COMPARE.html"
out.write_text(doc, encoding="utf-8")
print("wrote", out, f"({len(doc)//1024} KB)")
