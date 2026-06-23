"""EP2 Interview C2752+MVI_5053 trim-review (HyperFrames). B-cam (MVI_5048) time."""
from pathlib import Path
HERE=Path(__file__).resolve().parent; HEAD,TAIL=0.10,0.30; W,H=1280,720
SEGMENTS=[
 ("bcam.mp4",24.80,31.28,"We haven't launched ads yet — what I'm waiting for is our new website to get up and running: trendify.com.","",None,0.50),
 ("bcam.mp4",33.08,39.64,"And once that goes up, we'll set up a landing page that looks similar, so when we run ads, people go to the new site.","",None,None),
 ("bcam.mp4",42.06,48.84,"So we're probably going live today or tomorrow with the website — give or take a day until the ads go up too.","",None,0.60),
 ("bcam.mp4",68.20,71.04,"What's the one thing you're most afraid of as you try to grow?","QUESTION",None,None),
 ("bcam.mp4",74.36,80.68,"The one thing I'm most afraid of, as I'm trying to grow, is a fear I've had from the last time we grew.","",None,0.50),
 ("bcam.mp4",86.70,92.40,"Imagine you're walking down a road, and that road has a huge pothole in it.","",None,None),
 ("bcam.mp4",93.20,96.80,"A few years ago, you fell in it, and you broke all of your bones.","",None,None),
 ("bcam.mp4",96.86,97.78,"You broke your heart.","",None,None),
 ("bcam.mp4",97.82,102.52,"You broke pretty much everything you held close to you, because you weren't paying attention.","",None,0.50),
 ("bcam.mp4",103.80,106.82,"And for the first time in years, you're walking down that road again.","",None,None),
 ("bcam.mp4",107.44,109.42,"You're probably going to be scared for the same reason.","",None,None),
 ("bcam.mp4",110.64,112.04,"And that's how I feel right now.","",None,0.60),
 ("bcam.mp4",112.92,119.70,"So what I'm afraid of going wrong is not giving customers and our product the attention it truly deserves.","",None,None),
 ("bcam.mp4",121.54,130.26,"I just want to make sure people — including our team — have a great time, either working at Trendify or getting our services.","",None,None),
 ("bcam.mp4",131.06,141.62,"So the thing I'm being more cognizant of is being aware that I need to spend all my time focusing on the thing that got us here,","",None,None),
 ("bcam.mp4",142.04,146.16,"and not getting distracted with marketing or the glitz and glamour of making more money.","",None,0.80),
]
def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
MERGE_GAP=0.5  # merge adjacent segments with a tiny gap (continuous speech) -> no micro-cut, no overlap-stutter
def _merge(segs):
    out=[list(segs[0])]
    for s in segs[1:]:
        prev=out[-1]
        if s[0]==prev[0] and (s[1]-prev[2])<MERGE_GAP:
            prev[2]=s[2]; prev[3]=(prev[3]+" "+s[3]).strip(); prev[6]=s[6]
        else:
            out.append(list(s))
    return [tuple(x) for x in out]
def main():
    clips,caps,cum=[],[],0
    MERGED=_merge(SEGMENTS); NSEG=len(MERGED)
    for i,(src,sin,sout,text,tag,head,tail) in enumerate(MERGED):
        head=HEAD if head is None else head; tail=TAIL if tail is None else tail
        mi=max(0.0,sin-head); dms=round(((sout+tail)-mi)*1000); start=cum/1000; dur=(dms-3)/1000
        clips.append(f'  <video id="v{i}" src="{src}" muted playsinline data-start="{start:.3f}" data-duration="{dur:.3f}" data-media-start="{mi:.3f}" data-track-index="0"></video>\n  <audio id="a{i}" src="{src}" data-start="{start:.3f}" data-duration="{dur:.3f}" data-media-start="{mi:.3f}" data-volume="1" data-track-index="1"></audio>')
        tl=f'<span class="tag">{esc(tag)}</span>' if tag else ""
        caps.append(f'  <div id="cap{i}" class="clip cap" data-start="{start:.3f}" data-duration="{dur:.3f}" data-track-index="2">{tl}<span class="txt">{esc(text)}</span><span class="seg">{i+1} / {NSEG}</span></div>')
        cum+=dms
    total=cum/1000
    html=f'''<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
#root{{position:relative;width:{W}px;height:{H}px;background:#000;overflow:hidden;font-family:'Montserrat',sans-serif}}
#root video{{position:absolute;top:0;left:0;width:{W}px;height:{H}px;object-fit:cover;z-index:1}}
#root .cap{{position:absolute;left:0;right:0;bottom:54px;text-align:center;padding:0 90px;z-index:5}}
#root .cap .txt{{display:inline-block;color:#fff;font-size:28px;font-weight:600;line-height:1.3;text-shadow:0 4px 14px rgba(0,0,0,.85);background:rgba(0,0,0,.34);padding:10px 20px;border-radius:10px}}
#root .cap .tag{{display:block;color:#F28129;font-size:18px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;margin-bottom:10px;text-shadow:0 2px 8px rgba(0,0,0,.9)}}
#root .cap .seg{{position:absolute;top:-2px;right:24px;color:rgba(255,255,255,.55);font-size:16px;font-weight:600}}
</style></head><body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-start="0" data-duration="{total:.3f}">
{chr(10).join(clips)}
{chr(10).join(caps)}
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>window.__timelines=window.__timelines||{{}};window.__timelines["root"]=gsap.timeline({{paused:true}});</script>
</div></body></html>'''
    (HERE/"index.html").write_text(html,encoding="utf-8")
    print(f"wrote index.html | {NSEG} segments (merged from {len(SEGMENTS)}) | total {total:.2f}s")
main()
