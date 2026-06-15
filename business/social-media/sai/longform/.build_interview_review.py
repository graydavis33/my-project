"""Generate a self-contained, EDITABLE HTML review page from an episode's
interview-questions .md (the weekly A-roll questions for Sai).

Reusable every week:  python .build_interview_review.py ep2/EP2-INTERVIEW-QUESTIONS.md

Parses '## Block X — Title', a 'Feeds: ...' line, and '- [★] question' items.
Sai can edit each question, toggle ★ must-have, Keep/Cut, add a note, and add
new questions — all saved in his browser; 'Copy final script' exports the kept set.
No server, no deps — just open the .html."""
import json, re, sys, html, os

SRC = sys.argv[1] if len(sys.argv) > 1 else "ep2/EP2-INTERVIEW-QUESTIONS.md"
HERE = os.path.dirname(os.path.abspath(__file__))
src_path = SRC if os.path.isabs(SRC) else os.path.join(HERE, SRC)
out_path = os.path.splitext(src_path)[0] + "-review.html"

text = open(src_path, encoding="utf-8").read()
parts = re.split(r"\n## ", text)
intro = parts[0]
tm = re.search(r"^#\s*(.+)", intro)
page_title = tm.group(1).strip() if tm else "Interview Questions"
# strip the leading "# title" line, keep the rest of the intro as a blurb
blurb = "\n".join(l for l in intro.split("\n")[1:] if l.strip())

blocks = []
for b in parts[1:]:
    lines = b.split("\n")
    head = lines[0].strip()
    bm = re.match(r"Block\s+(\S+)\s*[—-]\s*(.+)", head)
    letter = bm.group(1) if bm else ""
    btitle = (bm.group(2) if bm else head).strip()
    feeds = ""
    qs = []
    for ln in lines[1:]:
        s = ln.strip()
        fm = re.match(r"Feeds:\s*(.+)", s)
        if fm:
            feeds = fm.group(1).strip(); continue
        qm = re.match(r"-\s+(.+)", s)
        if qm:
            q = qm.group(1).strip()
            must = q.startswith("★")
            if must: q = q[1:].strip()
            qs.append({"q": q, "must": must})
    blocks.append({"letter": letter, "title": btitle, "feeds": feeds, "qs": qs})

DATA = json.dumps({"title": page_title, "blurb": blurb, "blocks": blocks})

HTML = r"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ — Review</title>
<style>
:root{--bg:#0f1115;--panel:#171a21;--panel2:#1e222b;--line:#2a2f3a;--text:#e7e9ee;--muted:#8b93a4;--accent:#F28129;--good:#3ecf8e;--bad:#cf5b5b;--star:#f5c84b}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,"Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--text);font-size:15px;line-height:1.5}
header{position:sticky;top:0;z-index:10;background:var(--panel);border-bottom:1px solid var(--line);padding:14px 20px;display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
header h1{font-size:18px;margin:0}header .sub{color:var(--muted);font-size:13px}
.bar{display:flex;gap:10px;align-items:center}
button{background:var(--panel2);border:1px solid var(--line);color:var(--text);padding:8px 14px;border-radius:8px;cursor:pointer;font-size:13px}
button:hover{border-color:var(--accent)}button.primary{background:var(--accent);border-color:var(--accent);color:#11130f;font-weight:600}
.progress{color:var(--muted);font-size:13px}
.wrap{max-width:840px;margin:0 auto;padding:22px}
.blurb{background:var(--panel2);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;padding:12px 14px;color:var(--muted);font-size:13px;margin-bottom:20px}
.block{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin-bottom:18px}
.block h2{margin:0 0 2px;font-size:16px}.block .feeds{color:var(--accent);font-size:12px;margin-bottom:12px}
.q{display:flex;gap:10px;align-items:flex-start;border:1px solid var(--line);border-radius:9px;padding:9px 11px;margin-bottom:8px}
.cutinfo{font-size:12px;color:var(--muted);margin-top:6px}
.cutinfo a{color:var(--accent);cursor:pointer;text-decoration:underline}
.star{cursor:pointer;font-size:18px;line-height:1.3;color:var(--line);user-select:none}
.star.on{color:var(--star)}
.qbody{flex:1}
.qtext{width:100%;background:transparent;border:1px solid transparent;color:var(--text);border-radius:6px;padding:5px 7px;font-family:inherit;font-size:14.5px;line-height:1.45;resize:none;overflow:hidden;min-height:30px}
.qtext:hover{border-color:var(--line)}.qtext:focus{border-color:var(--accent);background:var(--panel2);outline:none}
.qnote{width:100%;margin-top:5px;background:transparent;border:1px dashed var(--line);color:var(--muted);border-radius:6px;padding:4px 7px;font-family:inherit;font-size:12.5px;line-height:1.4;resize:none;overflow:hidden}
.qnote:focus{border-color:var(--accent);color:var(--text);outline:none}
.cutbtn{cursor:pointer;border:1px solid var(--line);border-radius:6px;padding:3px 9px;font-size:12px;color:var(--muted);user-select:none;white-space:nowrap}
.cutbtn.on{background:var(--bad);color:#2c0d0d;border-color:var(--bad);font-weight:600}
.addq{margin-top:6px;font-size:12.5px;color:var(--accent);background:none;border:1px dashed var(--line);width:100%}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.6);display:none;align-items:center;justify-content:center;z-index:20}
.modal.show{display:flex}.modal .inner{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px;max-width:680px;width:92%;max-height:82vh;overflow:auto}
.modal pre{white-space:pre-wrap;font-size:13px}
.legend{font-size:12px;color:var(--muted);margin-bottom:14px}
.legend .star{font-size:14px;color:var(--star)}
</style></head><body>
<header>
  <div><h1>__TITLE__</h1><div class="sub">Editable — reword questions, ★ = must-have, cut what you don't want, add your own. Saves in your browser.</div></div>
  <div class="bar"><span class="progress" id="prog"></span><button id="copyBtn" class="primary">Copy final script</button><button id="resetBtn">Reset</button></div>
</header>
<div class="wrap">
  <div class="blurb" id="blurb"></div>
  <div class="legend">Tap the <span class="star">★</span> to mark a must-have · click in any question to edit it · <b>Cut</b> to drop one · <b>+ add question</b> at the bottom of a block.</div>
  <div id="list"></div>
</div>
<div class="modal" id="modal"><div class="inner"><h2 style="margin-top:0">Final interview script</h2><pre id="summary"></pre><div style="margin-top:12px"><button id="closeModal">Close</button></div></div></div>
<script>
const DATA = __DATA__;
const KEY = "interview-review-__SLUG__";
let state = JSON.parse(localStorage.getItem(KEY) || "{}");
// state[blockIdx] = { q: {qi:{text,must,cut,note}}, extra:[{text,must,note}] }
function save(){localStorage.setItem(KEY, JSON.stringify(state));renderProg();}
function bs(bi){if(!state[bi])state[bi]={q:{},extra:[]};return state[bi];}
function qs(bi,qi){const b=bs(bi);if(!b.q[qi])b.q[qi]={};return b.q[qi];}
function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}

document.getElementById("blurb").textContent = DATA.blurb;
document.title = DATA.title + " — Review";

function qRow(bi,qi,base,extraIdx){
  const ov = extraIdx!=null ? (bs(bi).extra[extraIdx]||{}) : qs(bi,qi);
  const text = ov.text!==undefined?ov.text:(base?base.q:"");
  const must = ov.must!==undefined?ov.must:(base?base.must:false);
  const cut  = !!ov.cut;
  const note = ov.note||"";
  const id = extraIdx!=null?("x"+extraIdx):qi;
  return `<div class="q">
     <span class="star ${must?'on':''}" data-bi="${bi}" data-id="${id}" data-act="must">★</span>
     <div class="qbody">
       <textarea class="qtext" data-bi="${bi}" data-id="${id}" data-f="text" rows="1">${esc(text)}</textarea>
       <textarea class="qnote" data-bi="${bi}" data-id="${id}" data-f="note" rows="1" placeholder="note / how I'd answer…">${esc(note)}</textarea>
     </div>
     <span class="cutbtn ${cut?'on':''}" data-bi="${bi}" data-id="${id}" data-act="cut">${cut?'cut':'Cut'}</span>
   </div>`;
}

function render(){
  const list=document.getElementById("list"); list.innerHTML="";
  DATA.blocks.forEach((blk,bi)=>{
    const b=bs(bi);
    let rows="",cutCount=0;
    blk.qs.forEach((base,qi)=>{const o=b.q[qi]||{};if(o.cut){cutCount++;return;}rows+=qRow(bi,qi,base,null);});
    (b.extra||[]).forEach((e,xi)=>{if(e.cut){cutCount++;return;}rows+=qRow(bi,null,null,xi);});
    const el=document.createElement("div"); el.className="block";
    el.innerHTML=`<h2>Block ${esc(blk.letter)} — ${esc(blk.title)}</h2>
      ${blk.feeds?`<div class="feeds">↳ feeds: ${esc(blk.feeds)}</div>`:''}
      ${rows}
      <button class="addq" data-bi="${bi}">+ add question</button>
      ${cutCount?`<div class="cutinfo">${cutCount} cut · <a class="restore" data-bi="${bi}">restore</a></div>`:''}`;
    list.appendChild(el);
  });
  list.querySelectorAll(".star,.cutbtn").forEach(el=>el.onclick=()=>{
    const bi=el.dataset.bi,id=el.dataset.id,act=el.dataset.act;
    let o; if(id[0]==="x"){o=bs(bi).extra[+id.slice(1)];} else {o=qs(bi,id);}
    if(act==="must")o.must=!o.must; else o.cut=!o.cut; save(); render();
  });
  const grow=el=>{el.style.height="auto";el.style.height=el.scrollHeight+"px";};
  list.querySelectorAll(".qtext,.qnote").forEach(el=>el.oninput=()=>{
    const bi=el.dataset.bi,id=el.dataset.id,f=el.dataset.f;
    let o; if(id[0]==="x"){o=bs(bi).extra[+id.slice(1)];} else {o=qs(bi,id);}
    o[f]=el.value; save(); grow(el);
  });
  list.querySelectorAll(".addq").forEach(el=>el.onclick=()=>{bs(el.dataset.bi).extra.push({text:"",must:false,note:""});save();render();});
  list.querySelectorAll(".restore").forEach(el=>el.onclick=()=>{const b=bs(el.dataset.bi);for(const k in b.q)b.q[k].cut=false;(b.extra||[]).forEach(e=>e.cut=false);save();render();});
  list.querySelectorAll(".qtext,.qnote").forEach(grow);
  renderProg();
}
function renderProg(){
  let must=0; DATA.blocks.forEach((blk,bi)=>{const b=bs(bi);
    blk.qs.forEach((base,qi)=>{const o=b.q[qi]||{};const m=o.must!==undefined?o.must:base.must;if(m&&!o.cut)must++;});
    (b.extra||[]).forEach(e=>{if(e.must&&!e.cut)must++;});});
  document.getElementById("prog").textContent = must+" must-haves";
}
document.getElementById("copyBtn").onclick=()=>{
  let out = DATA.title.toUpperCase()+"\n\n";
  DATA.blocks.forEach((blk,bi)=>{const b=bs(bi);
    out+=`BLOCK ${blk.letter} — ${blk.title}`+(blk.feeds?`  (feeds: ${blk.feeds})`:"")+"\n";
    const emit=(text,must,cut,note)=>{if(cut)return;out+=`  ${must?"★ ":"  "}${text}\n`;if(note)out+=`      ↳ ${note}\n`;};
    blk.qs.forEach((base,qi)=>{const o=b.q[qi]||{};emit(o.text!==undefined?o.text:base.q,o.must!==undefined?o.must:base.must,o.cut,o.note);});
    (b.extra||[]).forEach(e=>emit(e.text,e.must,e.cut,e.note));
    out+="\n";});
  document.getElementById("summary").textContent=out;
  document.getElementById("modal").classList.add("show");
  if(navigator.clipboard)navigator.clipboard.writeText(out);
};
document.getElementById("closeModal").onclick=()=>document.getElementById("modal").classList.remove("show");
document.getElementById("resetBtn").onclick=()=>{if(confirm("Clear all edits in this browser?")){state={};save();render();}};
render();
</script></body></html>"""

slug = re.sub(r"[^a-z0-9]+","-",page_title.lower()).strip("-")
HTML = (HTML.replace("__TITLE__", html.escape(page_title))
            .replace("__DATA__", DATA)
            .replace("__SLUG__", slug))
open(out_path,"w",encoding="utf-8").write(HTML)
print("wrote", out_path)
print("blocks:", len(blocks), "| questions:", sum(len(b["qs"]) for b in blocks))
