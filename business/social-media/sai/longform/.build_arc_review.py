"""Generate a self-contained, draggable/editable HTML board from an episode's
EP{N}-ARC-MAP.md so Gray can SYNTHESIZE the arc (drag clips between beats, edit,
cut, add). Reusable weekly:

    python .build_arc_review.py ep2/EP2-ARC-MAP.md

Parses '## Beat' headings and their '- ' bullet items into draggable cards.
Saves in the browser; 'Copy synthesized arc' exports the current layout.
No server, no deps — open the .html."""
import json, re, sys, html, os

SRC = sys.argv[1] if len(sys.argv) > 1 else "ep2/EP2-ARC-MAP.md"
HERE = os.path.dirname(os.path.abspath(__file__))
src_path = SRC if os.path.isabs(SRC) else os.path.join(HERE, SRC)
out_path = os.path.splitext(src_path)[0] + "-review.html"

text = open(src_path, encoding="utf-8").read()
parts = re.split(r"\n## ", text)
intro = parts[0]
tm = re.search(r"^#\s*(.+)", intro)
page_title = tm.group(1).strip() if tm else "Arc Map"

cid = 0
sections = []
for p in parts[1:]:
    lines = p.split("\n")
    title = lines[0].strip()
    desc, cards = [], []
    for ln in lines[1:]:
        s = ln.strip()
        m = re.match(r"-\s+(.+)", s)
        if m:
            cards.append({"id": f"c{cid}", "text": m.group(1).strip()}); cid += 1
        elif s and not s.startswith("|") and not s.startswith("#"):
            desc.append(s)
    sections.append({"title": title, "desc": " ".join(desc)[:240], "cards": cards})

DATA = json.dumps({"title": page_title, "sections": sections})

HTML = r"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ — Synthesize</title>
<style>
:root{--bg:#0f1115;--panel:#171a21;--panel2:#1e222b;--line:#2a2f3a;--text:#e7e9ee;--muted:#8b93a4;--accent:#F28129;--bad:#cf5b5b}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,"Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--text);font-size:15px;line-height:1.5}
header{position:sticky;top:0;z-index:10;background:var(--panel);border-bottom:1px solid var(--line);padding:14px 20px;display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
header h1{font-size:18px;margin:0}header .sub{color:var(--muted);font-size:13px}
.bar{display:flex;gap:10px;align-items:center}
button{background:var(--panel2);border:1px solid var(--line);color:var(--text);padding:8px 14px;border-radius:8px;cursor:pointer;font-size:13px}
button:hover{border-color:var(--accent)}button.primary{background:var(--accent);border-color:var(--accent);color:#11130f;font-weight:600}
.wrap{max-width:900px;margin:0 auto;padding:22px}
.hint{color:var(--muted);font-size:12.5px;margin-bottom:16px}
.beat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:14px}
.beat h2{margin:0 0 2px;font-size:15px}.beat .desc{color:var(--muted);font-size:12px;margin-bottom:10px}
.zone{min-height:30px;display:flex;flex-direction:column;gap:7px}
.zone.over{outline:2px dashed var(--accent);outline-offset:3px;border-radius:8px}
.card{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:7px 9px;display:flex;gap:8px;align-items:flex-start}
.card.dragging{opacity:.4}
.grip{cursor:grab;color:var(--muted);user-select:none;font-size:14px;padding-top:4px}
.ctext{flex:1;background:transparent;border:1px solid transparent;color:var(--text);border-radius:6px;padding:4px 6px;font-family:inherit;font-size:13.5px;line-height:1.45;resize:none;overflow:hidden;min-height:26px}
.ctext:hover{border-color:var(--line)}.ctext:focus{border-color:var(--accent);outline:none;background:var(--bg)}
.x{cursor:pointer;color:var(--muted);user-select:none;padding:2px 6px;border-radius:6px;font-size:13px}
.x:hover{color:var(--bad)}
.addc{margin-top:8px;font-size:12.5px;color:var(--accent);background:none;border:1px dashed var(--line);width:100%}
.cutinfo{font-size:12px;color:var(--muted);margin-top:6px}.cutinfo a{color:var(--accent);cursor:pointer;text-decoration:underline}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.6);display:none;align-items:center;justify-content:center;z-index:20}
.modal.show{display:flex}.modal .inner{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px;max-width:700px;width:92%;max-height:82vh;overflow:auto}
.modal pre{white-space:pre-wrap;font-size:12.5px}
</style></head><body>
<header>
  <div><h1>__TITLE__</h1><div class="sub">Synthesize the arc — drag cards between beats, edit, cut, add. Saves in your browser.</div></div>
  <div class="bar"><button id="copyBtn" class="primary">Copy synthesized arc</button><button id="resetBtn">Reset</button></div>
</header>
<div class="wrap">
  <div class="hint">Grab the ⠿ handle to drag a clip into another beat · click any card to edit · ✕ to cut · <b>+ add</b> a beat note/clip.</div>
  <div id="board"></div>
</div>
<div class="modal" id="modal"><div class="inner"><h2 style="margin-top:0">Synthesized arc</h2><pre id="summary"></pre><div style="margin-top:12px"><button id="closeModal">Close</button></div></div></div>
<script>
const DATA=__DATA__;
const KEY="arc-review-__SLUG__";
let state=JSON.parse(localStorage.getItem(KEY)||"null");
function save(){localStorage.setItem(KEY,JSON.stringify(state));}
function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function init(){
  if(state&&state.cols)return;
  state={cols:[],card:{},next:0};
  DATA.sections.forEach((s,si)=>{state.cols[si]=[];s.cards.forEach(c=>{state.card[c.id]={text:c.text,cut:false};state.cols[si].push(c.id);state.next=Math.max(state.next,+c.id.slice(1)+1);});});
  save();
}
init();
let drag=null;
const grow=el=>{el.style.height="auto";el.style.height=el.scrollHeight+"px";};

function render(){
  const board=document.getElementById("board");board.innerHTML="";
  DATA.sections.forEach((s,si)=>{
    const ids=state.cols[si]||[];
    let cut=0;
    const cards=ids.map(id=>{const c=state.card[id]||{};if(c.cut){cut++;return"";}
      return `<div class="card" draggable="true" data-id="${id}">
        <span class="grip">⠿</span>
        <textarea class="ctext" data-id="${id}" rows="1">${esc(c.text)}</textarea>
        <span class="x" data-id="${id}" title="cut">✕</span></div>`;}).join("");
    const el=document.createElement("div");el.className="beat";
    el.innerHTML=`<h2>${esc(s.title)}</h2>${s.desc?`<div class="desc">${esc(s.desc)}</div>`:''}
      <div class="zone" data-si="${si}">${cards}</div>
      <button class="addc" data-si="${si}">+ add card</button>
      ${cut?`<div class="cutinfo">${cut} cut · <a class="restore" data-si="${si}">restore</a></div>`:''}`;
    board.appendChild(el);
  });
  // edit
  board.querySelectorAll(".ctext").forEach(t=>{grow(t);t.oninput=()=>{state.card[t.dataset.id].text=t.value;save();grow(t);};});
  // cut / restore / add
  board.querySelectorAll(".x").forEach(x=>x.onclick=()=>{state.card[x.dataset.id].cut=true;save();render();});
  board.querySelectorAll(".restore").forEach(r=>r.onclick=()=>{(state.cols[r.dataset.si]||[]).forEach(id=>{if(state.card[id])state.card[id].cut=false;});save();render();});
  board.querySelectorAll(".addc").forEach(a=>a.onclick=()=>{const id="c"+(state.next++);state.card[id]={text:"",cut:false};state.cols[+a.dataset.si].push(id);save();render();});
  // drag
  board.querySelectorAll(".card").forEach(c=>{
    c.addEventListener("dragstart",e=>{drag=c.dataset.id;c.classList.add("dragging");e.dataTransfer.effectAllowed="move";});
    c.addEventListener("dragend",()=>{c.classList.remove("dragging");drag=null;});
  });
  board.querySelectorAll(".zone").forEach(z=>{
    z.addEventListener("dragover",e=>{e.preventDefault();z.classList.add("over");});
    z.addEventListener("dragleave",()=>z.classList.remove("over"));
    z.addEventListener("drop",e=>{e.preventDefault();z.classList.remove("over");if(!drag)return;
      const si=+z.dataset.si;const after=e.target.closest(".card");
      for(const k in state.cols)state.cols[k]=state.cols[k].filter(x=>x!==drag);
      if(after&&after.dataset.id!==drag){const idx=state.cols[si].indexOf(after.dataset.id);state.cols[si].splice(idx,0,drag);}
      else state.cols[si].push(drag);
      save();render();});
  });
}
document.getElementById("copyBtn").onclick=()=>{
  let out=DATA.title.toUpperCase()+"\n\n";
  DATA.sections.forEach((s,si)=>{out+=s.title+"\n";
    (state.cols[si]||[]).forEach(id=>{const c=state.card[id]||{};if(c.cut||!(c.text||"").trim())return;out+="  - "+c.text+"\n";});
    out+="\n";});
  document.getElementById("summary").textContent=out;
  document.getElementById("modal").classList.add("show");
  if(navigator.clipboard)navigator.clipboard.writeText(out);
};
document.getElementById("closeModal").onclick=()=>document.getElementById("modal").classList.remove("show");
document.getElementById("resetBtn").onclick=()=>{if(confirm("Reset to the original arc map? Clears your edits.")){state=null;localStorage.removeItem(KEY);init();render();}};
render();
</script></body></html>"""

slug = re.sub(r"[^a-z0-9]+","-",page_title.lower()).strip("-")
HTML = (HTML.replace("__TITLE__", html.escape(page_title)).replace("__DATA__", DATA).replace("__SLUG__", slug))
open(out_path,"w",encoding="utf-8").write(HTML)
print("wrote", out_path)
print("beats:", len(sections), "| cards:", sum(len(s["cards"]) for s in sections))
