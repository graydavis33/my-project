"""EP2 Interview C2750+MVI_5051 trim-review (HyperFrames). B-cam (MVI_5048) time."""
from pathlib import Path
HERE=Path(__file__).resolve().parent; HEAD,TAIL=0.10,0.30; W,H=1280,720
SEGMENTS=[
 ("bcam.mp4",30.00,39.00,"This week I built systems that actually helped move things forward. We","",0.0,None),
 ("bcam.mp4",39.00,42.18,"built an editing workflow where historically creators were responsible","",None,None),
 ("bcam.mp4",42.18,47.34,"for filming and editing content. Now we have the optionality to add editors into","",None,None),
 ("bcam.mp4",47.34,52.66,"the workflow if we need more sophisticated edits. And through building","",None,None),
 ("bcam.mp4",52.66,56.56,"that system, I was able to understand how to build a system for systems.","",None,0.80),
 ("bcam.mp4",62.00,66.44,"Through every step of building the editor workflow, I identified","",None,None),
 ("bcam.mp4",66.44,71.50,"everything that went into it and thought about how I could turn that into a","",None,None),
 ("bcam.mp4",71.50,74.56,"system in and of itself. And so we mapped it out","",None,None),
 ("bcam.mp4",75.70,82.44,"into Asana. Our operations team built a process for it, and now every project","",None,None),
 ("bcam.mp4",82.44,85.44,"follows the same system, similar to how we did with the editor workflow.","",None,0.80),
 ("bcam.mp4",92.64,97.04,"You're handing off the onboarding calls you used to run yourself. Why was that scary,","QUESTION",None,None),
 ("bcam.mp4",97.04,99.48,"and why did delegating to Madison feel like a nightmare?","QUESTION",None,None),
 ("bcam.mp4",102.06,106.36,"I used to run all the onboarding calls here at Trendify until we hired a creator lead.","",None,None),
 ("bcam.mp4",106.36,110.82,"And now she's responsible for running the onboarding call with new creators.","",None,None),
 ("bcam.mp4",111.84,118.30,"And it was so stressful, because I feel like I need to be in control and the face of everything related to people.","",None,None),
 ("bcam.mp4",119.02,122.42,"I want to meet people. I want to be a part of people's onboarding journey.","",None,None),
 ("bcam.mp4",125.30,130.64,"And I realized it was just my ego and need for control holding me back from delegating.","",None,0.60),
 ("bcam.mp4",130.94,133.56,"Because those calls would take up a lot of time on my calendar.","",None,None),
 ("bcam.mp4",134.94,138.26,"And so I handed it off, and the onboarding call actually went really good.","",None,None),
 ("bcam.mp4",138.72,143.66,"And I felt good about handing things off as time goes on, as long as I find the right people to do it.","",None,0.80),
 ("bcam.mp4",152.14,154.88,"Why is an agency uniquely hard to build?","QUESTION",None,None),
 ("bcam.mp4",159.80,163.10,"The thing about agencies is that they're really hard to build,","",None,None),
 ("bcam.mp4",163.84,168.82,"and even harder to scale, because you're just trying to scale humans.","",None,0.60),
 ("bcam.mp4",172.26,176.86,"But I really like that, because I think my superpower is working with people,","",None,None),
 ("bcam.mp4",177.74,182.40,"eyeing out who to hire, and building a really fun culture.","",None,0.70),
 ("bcam.mp4",183.50,186.92,"But if you make one system change — it could be the smallest thing ever —","",None,None),
 ("bcam.mp4",187.08,189.92,"there have to be eight different departments that get notified of it.","",None,None),
 ("bcam.mp4",189.92,195.56,"And you have to make sure it gets implemented, and the tech gets implemented, and all the SOPs get changed.","",None,None),
 ("bcam.mp4",197.00,202.72,"Now imagine doing this across 10 people. Now 100 people. In the future, 1,000 people.","",None,None),
 ("bcam.mp4",203.10,206.00,"That's why agencies are uniquely difficult to build,","",None,None),
 ("bcam.mp4",206.10,210.70,"but also the most rewarding if you can do it right — because no one else wants to.","",None,0.80),
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
