"""EP2 Interview C2748+MVI_5049 trim-review (HyperFrames). B-cam (MVI_5048) time."""
from pathlib import Path
HERE=Path(__file__).resolve().parent; HEAD,TAIL=0.10,0.30; W,H=1280,720
SEGMENTS=[
 ("bcam.mp4",15.60,17.72,"Yeah, it's something I'm actively trying to work on.","",None,None),
 ("bcam.mp4",18.52,23.46,"I don't want to tie my identity and self-worth to how much I get accomplished on any given day.","",None,None),
 ("bcam.mp4",23.46,28.12,"And it's hard, because I know that if I focus and I'm productive, I can","",None,None),
 ("bcam.mp4",29.22,35.32,"move things forward — whether it's business, content, or one day, I don't know, helping","",None,None),
 ("bcam.mp4",35.32,42.50,"change the world. And it almost makes you feel like, unless you're working or utilizing","",None,None),
 ("bcam.mp4",42.50,49.48,"the gift that the universe, God, gave you — you're not worth anything.","",None,0.70),
 ("bcam.mp4",51.78,58.26,"And so I'm trying to root my self-worth and identity in things beyond just my productivity.","",None,None),
 ("bcam.mp4",66.10,69.28,"Which is difficult, because I love working so much.","",None,0.70),
 ("bcam.mp4",109.12,112.02,"My bad day starts from when I don't get enough sleep.","",None,None),
 ("bcam.mp4",112.72,115.26,"If I don't get enough sleep, I have a terrible day.","",None,None),
 ("bcam.mp4",115.34,117.02,"It doesn't matter what happens that day.","",None,None),
 ("bcam.mp4",118.70,122.14,"And usually I have incredible days when I get enough sleep.","",None,None),
 ("bcam.mp4",125.52,127.50,"And when I get things done in the morning","",None,None),
 ("bcam.mp4",127.50,129.72,"before I have my deep work block in the afternoon.","",None,None),
 ("bcam.mp4",134.28,140.64,"And I have bad days when I eat oily food, don't stick to my diet, or miss a workout.","",None,None),
 ("bcam.mp4",146.06,148.80,"And my great days come from meditating in the morning.","",None,0.80),
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
