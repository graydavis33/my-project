"""EP2 Interview C2749+MVI_5050 trim-review (HyperFrames). B-cam (MVI_5048) time."""
from pathlib import Path
HERE=Path(__file__).resolve().parent; HEAD,TAIL=0.10,0.30; W,H=1280,720
SEGMENTS=[
 ("bcam.mp4",55.82,60.04,"Typically, a lot of stresses in life can be solved with a simple system.","",None,None),
 ("bcam.mp4",62.00,66.42,"And a system is something that works continuously — every day, every week, every month,","",None,None),
 ("bcam.mp4",68.74,74.26,"without you having to think about it. I'll give you an example. If you're really stressed out","",None,None),
 ("bcam.mp4",74.26,79.14,"every week because you don't have enough clean clothes to wear,","",None,None),
 ("bcam.mp4",79.14,82.38,"and everything else is just in the laundry,","",None,None),
 ("bcam.mp4",83.24,87.98,"you'd set up a simple system where every Saturday you go do your laundry,","",None,None),
 ("bcam.mp4",88.08,94.06,"fold your clothes so you have fresh clothes for the rest of the week. Maybe an alarm","",None,None),
 ("bcam.mp4",94.06,100.22,"goes off at 11 a.m. on Saturdays that reminds you to do it. And then another alarm","",None,None),
 ("bcam.mp4",100.22,105.04,"goes off at 12 p.m. that reminds you to take your","",None,None),
 ("bcam.mp4",105.04,109.38,"clothes from the washer to the dryer. And then another at 1 p.m. that tells you to take","",None,None),
 ("bcam.mp4",109.38,114.42,"your clothes out of the dryer. And you do this every single Saturday — and that's a simple","",None,None),
 ("bcam.mp4",114.42,120.76,"system. And so in the same realm, for me in business, there were a lot of simple stresses","",None,None),
 ("bcam.mp4",120.76,122.54,"that would come up over and over again,","",None,None),
 ("bcam.mp4",123.20,125.20,"that I just didn't care enough about,","",None,None),
 ("bcam.mp4",125.20,127.62,"because I wanted to focus on what I thought mattered more.","",None,None),
 ("bcam.mp4",128.56,130.86,"When in reality, I had to focus on","",None,None),
 ("bcam.mp4",130.86,133.78,"how I could turn every single little thing into a system.","",None,None),
 ("bcam.mp4",135.58,137.16,"Everything that stresses me out","",None,None),
 ("bcam.mp4",137.16,139.76,"can be a system that no longer stresses me out.","",None,None),
 ("bcam.mp4",140.58,142.76,"And that was kind of the huge epiphany I had today,","",None,None),
 ("bcam.mp4",142.80,145.28,"starting with building a system for how we build systems.","",None,0.80),
 ("bcam.mp4",189.94,192.72,"You drifted from systems for a couple of weeks.","QUESTION",None,None),
 ("bcam.mp4",197.02,201.38,"I shifted away from working on systems for a couple of weeks, because I tried to get cute.","",None,0.60),
 ("bcam.mp4",208.12,210.98,"Fundamentally, business is about doing the simple things at scale —","",None,None),
 ("bcam.mp4",211.86,215.82,"the boring stuff no one usually wants to do, i.e. building systems.","",None,0.80),
 ("bcam.mp4",225.38,230.40,"I got pulled away from it because I tried to get fancy. I thought I'd reached a level in","",None,None),
 ("bcam.mp4",230.40,231.96,"which systems no longer serve me.","",None,None),
 ("bcam.mp4",232.66,234.14,"It was my ego.","",None,0.50),
 ("bcam.mp4",235.58,238.74,"And I got pulled back through a hard, humbling lesson","",None,None),
 ("bcam.mp4",240.30,242.28,"when multiple systems were breaking,","",None,None),
 ("bcam.mp4",242.28,243.98,"and I just felt really stressed out.","",None,0.80),
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
