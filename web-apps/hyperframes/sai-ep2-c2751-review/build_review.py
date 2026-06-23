"""EP2 Interview C2751+MVI_5052 trim-review (HyperFrames). B-cam (MVI_5048) time."""
from pathlib import Path
HERE=Path(__file__).resolve().parent; HEAD,TAIL=0.10,0.30; W,H=1280,720
SEGMENTS=[
 ("bcam.mp4",27.16,29.72,"You said building an agency is just people,","QUESTION",None,None),
 ("bcam.mp4",30.00,32.36,"and that you love it — where does that come from?","QUESTION",None,None),
 ("bcam.mp4",41.10,44.90,"At the end of the day, building a company — specifically an agency — is just people.","",None,0.60),
 ("bcam.mp4",50.62,52.96,"And I don't know why I love that so much,","",None,None),
 ("bcam.mp4",54.90,57.84,"but I think nature is so cool, in the sense that","",None,None),
 ("bcam.mp4",57.84,62.64,"we have people similar to us in this world","",None,None),
 ("bcam.mp4",62.64,67.50,"that could share the same sense of purpose and passion toward building something.","",None,0.50),
 ("bcam.mp4",68.30,73.14,"It's like you're coming together and building something that's a culmination of everyone.","",None,None),
 ("bcam.mp4",74.10,76.16,"And that, to me, is just so exciting.","",None,0.50),
 ("bcam.mp4",79.00,85.02,"And maybe it was my lack of going to school and being around people for a lot of my life that makes me want to do this.","",None,None),
 ("bcam.mp4",86.66,95.24,"Man, I love working with high-agency people that are good — people that share a similar purpose and passion for building things.","",None,0.60),
 ("bcam.mp4",99.36,101.96,"Tell me about UGA — the semester of college.","QUESTION",None,None),
 ("bcam.mp4",104.72,108.76,"So I went to college for one semester before dropping out.","",None,None),
 ("bcam.mp4",111.46,113.48,"University of Georgia. Go Dawgs.","",None,0.50),
 ("bcam.mp4",119.28,124.66,"And I thought it would be the most exhilarating experience of my life, because I was finally able to be around people.","",None,None),
 ("bcam.mp4",125.46,127.50,"For context, I did all of my high school online.","",None,None),
 ("bcam.mp4",128.84,133.62,"But when I went there, I noticed really quickly that my joy came from working all day long.","",None,None),
 ("bcam.mp4",135.72,139.74,"And most freshmen in college don't share that same experience — rightfully so.","",None,None),
 ("bcam.mp4",142.54,145.44,"And I felt like I didn't find what I was looking for.","",None,None),
 ("bcam.mp4",145.46,151.52,"And after reflecting on it, I realized I want to be around people who also love doing the same things as me.","",None,0.60),
 ("bcam.mp4",154.50,159.04,"And not being able to get that in college makes me want, even more than ever,","",None,None),
 ("bcam.mp4",159.10,166.36,"to have an in-person office where I'm around people, building together toward one bigger vision.","",None,None),
 ("bcam.mp4",167.68,168.80,"That's really exciting.","",None,0.60),
 ("bcam.mp4",192.54,196.08,"You surprised Craig with a new laptop this week. What was that instinct?","QUESTION",None,None),
 ("bcam.mp4",200.76,209.78,"So my creative director behind the camera right now — I surprised him with a laptop, because he had a really crappy one before.","",None,None),
 ("bcam.mp4",210.34,214.60,"And I could sense his frustration with it as time went on.","",None,None),
 ("bcam.mp4",214.70,222.24,"And I wanted to ensure he had everything he needed to have a great experience working.","",None,None),
 ("bcam.mp4",224.66,232.52,"And not to mention his level of agency and shared passion for the work we do together — I thought he really deserved it.","",None,None),
 ("bcam.mp4",232.56,236.14,"So I ordered it and surprised him, which was a lot of fun.","",None,0.60),
 ("bcam.mp4",248.02,252.34,"So why do I make these videos, even though I have absolutely nothing for you to buy?","QUESTION",None,None),
 ("bcam.mp4",255.96,262.34,"I could give a logical answer — that I want to help people out, or attract awesome talent to our company.","",None,None),
 ("bcam.mp4",262.34,272.26,"But more than that, I just feel drawn to it. So I'm taking it day by day. But yeah — I have nothing to sell you, and I probably never will.","",None,0.80),
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
