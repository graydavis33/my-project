"""EP2 Interview C2747+MVI_5048 trim-review (HyperFrames). B-cam (MVI_5048) time."""
from pathlib import Path
HERE=Path(__file__).resolve().parent; HEAD,TAIL=0.10,0.30; W,H=1280,720
SEGMENTS=[
 ("bcam.mp4",17.18,22.34,"Last week, the plan was to finally turn the ads back on and launch the site.","QUESTION",None,None),
 ("bcam.mp4",22.52,27.88,"What actually happened, and where does the launch stand right now?","QUESTION",None,None),
 ("bcam.mp4",28.88,31.86,"We were supposed to launch ads three weeks ago.","",None,None),
 ("bcam.mp4",34.46,39.34,"But what had happened is I was too focused on other things that required my attention.","",None,None),
 ("bcam.mp4",41.38,48.36,"And to me, product, culture, and customer experience always come first.","",None,None),
 ("bcam.mp4",49.40,55.00,"And so we had to postpone the launch of our ads because of that.","",None,None),
 ("bcam.mp4",55.00,60.44,"And now we are probably going to start running out tomorrow, which is really exciting.","",None,None),
 ("bcam.mp4",76.06,81.56,"Why did it slip by two? And how do you actually feel about it slipping?","QUESTION",None,None),
 ("bcam.mp4",83.08,85.20,"I don't care that it slipped because it's marketing.","",None,None),
 ("bcam.mp4",85.48,87.56,"I only care when product stuff slips.","",None,None),
 ("bcam.mp4",89.60,91.32,"Because marketing is just getting new clients.","",None,None),
 ("bcam.mp4",91.40,93.84,"It's not like if I don't turn on marketing, anyone's suffering.","",None,None),
 ("bcam.mp4",95.72,99.84,"But if there's something that goes wrong with the team or the product or customer experience, people suffer.","",None,None),
 ("bcam.mp4",100.80,102.70,"And so that is always utmost priority.","",None,None),
 ("bcam.mp4",103.50,105.40,"So I don't really care that we postpone marketing.","",None,None),
 ("bcam.mp4",105.58,106.78,"Like, who cares?","",None,None),
 ("bcam.mp4",122.14,131.94,"Instead, this week, I decided to focus on building a system for how we build systems.","",None,None),
 ("bcam.mp4",133.22,136.02,"Since we ship so many new systems every week,","",None,None),
 ("bcam.mp4",139.46,142.36,"it's really important that we have a system for how we build and ship systems.","",None,None),
 ("bcam.mp4",145.24,149.04,"And so when we make product updates, I don't have to worry about everything being in my brain.","",None,None),
 ("bcam.mp4",149.16,152.98,"Instead, everyone knows what's going on because it's documented like an actual system.","",None,0.80),
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
    for i,(src,sin,sout,text,tag,head,tail) in enumerate(_merge(SEGMENTS)):
        head=HEAD if head is None else head; tail=TAIL if tail is None else tail
        mi=max(0.0,sin-head); dms=round(((sout+tail)-mi)*1000); start=cum/1000; dur=(dms-3)/1000
        clips.append(f'  <video id="v{i}" src="{src}" muted playsinline data-start="{start:.3f}" data-duration="{dur:.3f}" data-media-start="{mi:.3f}" data-track-index="0"></video>\n  <audio id="a{i}" src="{src}" data-start="{start:.3f}" data-duration="{dur:.3f}" data-media-start="{mi:.3f}" data-volume="1" data-track-index="1"></audio>')
        tl=f'<span class="tag">{esc(tag)}</span>' if tag else ""
        caps.append(f'  <div id="cap{i}" class="clip cap" data-start="{start:.3f}" data-duration="{dur:.3f}" data-track-index="2">{tl}<span class="txt">{esc(text)}</span><span class="seg">{i+1} / {len(SEGMENTS)}</span></div>')
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
    print(f"wrote index.html | {len(SEGMENTS)} segments | total {total:.2f}s")
main()
