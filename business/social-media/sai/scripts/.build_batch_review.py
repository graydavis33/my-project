"""Generate a self-contained, EDITABLE HTML review page from a batch script .md file.
Parses ### N — Title blocks, their A/B/C hooks (+ Visual: lines), body, notes/flags,
and renders a reviewable page where the hook lines, visual notes, and body text are all
editable inline; plus hook-pick + Approve/Swap/Cut + notes (localStorage) and a
'Copy decisions' export that includes every edit. No server, no deps — just open the .html."""
import json, re, sys, html, os

SRC = sys.argv[1] if len(sys.argv) > 1 else "2026-06-15-batch-3.md"
HERE = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(HERE, SRC)
out_path = os.path.splitext(src_path)[0] + "-review.html"

text = open(src_path, encoding="utf-8").read()
parts = re.split(r"\n### ", text)
intro = parts[0]
title_m = re.search(r"^#\s*(.+)", intro)
page_title = title_m.group(1).strip() if title_m else "Batch Review"

scripts = []
for block in parts[1:]:
    lines = block.split("\n")
    head = lines[0].strip()
    if head.startswith("#"):
        continue
    m = re.match(r"(\d+)\s*[—-]\s*(.+)", head)
    num = m.group(1) if m else "?"
    title = (m.group(2) if m else head).strip()
    body_md = "\n".join(lines[1:])

    fm = re.search(r"\*\*Format:\*\*\s*(.+)", body_md)
    fmt = fm.group(1).strip() if fm else ""
    wm = re.search(r"\*\*Why it works:?\*\*\s*(.+)", body_md)
    why = wm.group(1).strip() if wm else ""

    hooks = []
    hl = body_md.split("\n")
    for i, ln in enumerate(hl):
        hm = re.match(r"^([ABC])\.\s+(.+)", ln)
        if hm:
            visual = ""
            if i + 1 < len(hl):
                vm = re.match(r"\*\*Visual:\*\*\s*(.+)", hl[i+1].strip())
                if vm: visual = vm.group(1).strip()
            hooks.append({"label": hm.group(1), "verbal": hm.group(2).strip(), "visual": visual})

    body = []
    sm = re.search(r"\*\*Script:\*\*\n(.*?)(?:\n\*\*|\Z)", body_md, re.S)
    if sm:
        for ln in sm.group(1).split("\n"):
            ln = ln.strip()
            if ln.startswith(">"):
                t = ln[1:].strip()
                if t: body.append(t)

    def grab(label):
        g = re.search(r"\*\*" + re.escape(label) + r":?\*\*\s*(.+)", body_md)
        return g.group(1).strip() if g else ""
    prop = grab("Setup/prop note")
    flags = grab("Invented-line flags")
    ref = grab("Sandcastles ref")
    ref_html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                      r'<a href="\2" target="_blank" rel="noopener">\1</a>', ref) if ref else ""

    scripts.append({"num": num, "title": title, "format": fmt, "why": why, "refHtml": ref_html,
                    "hooks": hooks, "body": "\n".join(body), "prop": prop, "flags": flags})

DATA = json.dumps(scripts)

HTML = r"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__PAGE_TITLE__ — Review</title>
<style>
:root{--bg:#0f1115;--panel:#171a21;--panel2:#1e222b;--line:#2a2f3a;--text:#e7e9ee;--muted:#8b93a4;--accent:#F28129;--good:#3ecf8e;--warn:#e0a44a;--bad:#cf5b5b}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,"Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--text);font-size:15px;line-height:1.5}
header{position:sticky;top:0;z-index:10;background:var(--panel);border-bottom:1px solid var(--line);padding:14px 20px;display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
header h1{font-size:18px;margin:0}header .sub{color:var(--muted);font-size:13px}
.bar{display:flex;gap:10px;align-items:center}
button{background:var(--panel2);border:1px solid var(--line);color:var(--text);padding:8px 14px;border-radius:8px;cursor:pointer;font-size:13px}
button:hover{border-color:var(--accent)}button.primary{background:var(--accent);border-color:var(--accent);color:#11130f;font-weight:600}
.progress{color:var(--muted);font-size:13px}
.wrap{max-width:880px;margin:0 auto;padding:22px}
.banner{background:var(--panel2);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;padding:10px 14px;color:var(--muted);font-size:13px;margin-bottom:18px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px;margin-bottom:18px;position:relative}
.delbtn{position:absolute;top:14px;right:16px;cursor:pointer;color:var(--muted);font-size:12px;border:1px solid var(--line);border-radius:6px;padding:2px 9px;user-select:none}
.delbtn:hover{color:var(--bad);border-color:var(--bad)}
.delbanner{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:9px 13px;margin-bottom:16px;color:var(--muted);font-size:13px}
.delbanner a{color:var(--accent);cursor:pointer;text-decoration:underline}
.card.approve{border-color:var(--good)}.card.swap{border-color:var(--warn)}.card.cut{border-color:var(--bad);opacity:.72}
.card h2{margin:0 0 4px;font-size:17px}.fmt{color:var(--accent);font-size:13px;margin-bottom:2px}
.why{color:var(--muted);font-size:12.5px;margin-bottom:8px}
.refrow{font-size:12.5px;color:var(--muted);margin-bottom:14px}
.refrow a{color:var(--accent);text-decoration:none;border-bottom:1px dotted var(--accent)}
.refrow a:hover{text-decoration:none;border-bottom-style:solid}
.section-label{text-transform:uppercase;letter-spacing:.6px;font-size:11px;color:var(--muted);margin:16px 0 8px}
.hook{border:1px solid var(--line);border-radius:9px;padding:10px 12px;margin-bottom:8px;display:flex;gap:11px;align-items:flex-start}
.hook.picked{border-color:var(--accent);background:rgba(242,129,41,.08)}
.hook .tag{font-weight:700;color:var(--accent);min-width:24px;cursor:pointer;user-select:none;border:1px solid var(--line);border-radius:6px;text-align:center;padding:2px 0}
.hook.picked .tag{background:var(--accent);color:#11130f;border-color:var(--accent)}
.hook .fields{flex:1}
.edit{width:100%;background:transparent;border:1px solid transparent;color:var(--text);border-radius:6px;padding:5px 7px;font-family:inherit;font-size:14px;line-height:1.45}
.edit:hover{border-color:var(--line)}.edit:focus{border-color:var(--accent);background:var(--panel2);outline:none}
.edit.verbal{font-weight:600}
.edit.visual{color:var(--muted);font-size:12.5px}
textarea.edit{resize:vertical}
.bodyedit{min-height:150px;background:var(--panel2);border:1px solid var(--line);border-radius:9px;font-size:14.5px}
.note{font-size:12.5px;color:var(--muted);margin-top:10px}.note b{color:var(--text)}
.flag{font-size:12.5px;color:var(--warn);margin-top:6px}
.controls{display:flex;gap:8px;margin-top:14px;align-items:center;flex-wrap:wrap}
.pill{padding:7px 14px;border-radius:20px;border:1px solid var(--line);cursor:pointer;font-size:13px}
.pill.approve.on{background:var(--good);color:#06281a;border-color:var(--good);font-weight:600}
.pill.swap.on{background:var(--warn);color:#3a2a0d;border-color:var(--warn);font-weight:600}
.pill.cut.on{background:var(--bad);color:#2c0d0d;border-color:var(--bad);font-weight:600}
.edited-badge{font-size:11px;color:var(--accent);margin-left:8px;display:none}
.edited .edited-badge{display:inline}
.notes{width:100%;margin-top:10px;background:var(--panel2);border:1px solid var(--line);color:var(--text);border-radius:8px;padding:10px;font-family:inherit;font-size:13.5px;resize:vertical;min-height:46px}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.6);display:none;align-items:center;justify-content:center;z-index:20}
.modal.show{display:flex}.modal .inner{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px;max-width:680px;width:92%;max-height:82vh;overflow:auto}
.modal pre{white-space:pre-wrap;font-size:12.5px;color:var(--text)}
.card.added{border-style:dashed}
.newtag{color:var(--accent);font-weight:700;letter-spacing:.5px;font-size:11px;text-transform:uppercase;margin-bottom:4px}
.titleedit{width:100%;font-size:17px;font-weight:600;background:transparent;border:1px solid transparent;color:var(--text);border-radius:6px;padding:4px 7px;font-family:inherit;margin:2px 0}
.titleedit:hover{border-color:var(--line)}.titleedit:focus{border-color:var(--accent);background:var(--panel2);outline:none}
.fmtedit{width:100%;font-size:13px;color:var(--accent);background:transparent;border:1px solid transparent;border-radius:6px;padding:3px 7px;font-family:inherit;margin-bottom:6px}
.fmtedit:hover{border-color:var(--line)}.fmtedit:focus{border-color:var(--accent);background:var(--panel2);outline:none}
.addcard{display:block;width:100%;padding:14px;border:1px dashed var(--line);background:transparent;color:var(--muted);border-radius:12px;font-size:14px;margin-bottom:18px;cursor:pointer}
.addcard:hover{border-color:var(--accent);color:var(--accent)}
.authorsel{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--muted)}
.authorsel select{background:var(--panel2);border:1px solid var(--line);color:var(--text);border-radius:7px;padding:6px 8px;font-family:inherit;font-size:13px}
.comments{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}
.thread{display:flex;flex-direction:column;gap:8px;margin-bottom:10px}
.cmt{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:8px 26px 8px 10px;font-size:13.5px;position:relative}
.cmt .who{font-weight:700}.cmt .who.whoGray{color:var(--accent)}.cmt .who.whoSai{color:var(--good)}
.cmt .when{color:var(--muted);font-size:11.5px;margin-left:6px}
.cmt .ctext{margin-top:3px;white-space:pre-wrap}
.cmt .cdel{position:absolute;top:6px;right:8px;color:var(--muted);cursor:pointer;font-size:11px;user-select:none}
.cmt .cdel:hover{color:var(--bad)}
.empty-thread{color:var(--muted);font-size:12.5px;font-style:italic}
.addcomment{display:flex;gap:8px;align-items:flex-start}
.commentinput{flex:1;background:var(--panel2);border:1px solid var(--line);color:var(--text);border-radius:8px;padding:8px;font-family:inherit;font-size:13.5px;resize:vertical;min-height:38px}
.commentinput:focus{border-color:var(--accent);outline:none}
.commentbtn{white-space:nowrap}
</style></head><body>
<header>
  <div><h1>__PAGE_TITLE__</h1><div class="sub">Editable — change hooks, visuals & script text inline. Pick a hook, set Approve/Swap/Cut. Saves in your browser.</div></div>
  <div class="bar"><span class="authorsel">Commenting as <select id="author"><option>Gray</option><option>Sai</option></select></span><span class="progress" id="prog"></span><button id="addBtnTop">+ Add card</button><button id="saveBtn">💾 Save file</button><button id="copyBtn" class="primary">Copy decisions + edits</button><button id="resetBtn">Reset</button></div>
</header>
<div class="wrap">
  <div class="banner">Everything you type is saved automatically in this browser. Set <b>Commenting as</b> (top) to your name, then leave 💬 comments on any card. Hit <b>💾 Save file</b> to download a complete copy — originals <i>plus</i> all edits &amp; comments — to hand off: the next person opens it, sees everything, and adds their own. <b>Copy decisions + edits</b> exports the lot as plain text.</div>
  <div id="list"></div>
</div>
<div class="modal" id="modal"><div class="inner"><h2 style="margin-top:0">Decisions + edits</h2><pre id="summary"></pre><div style="margin-top:12px"><button id="closeModal">Close</button></div></div></div>
<script id="saved-state" type="application/json">null</script>
<script>
const DATA = __DATA__;
const KEY = "batch-review-__SLUG__";
const SLUG = "__SLUG__";
let SAVED = null;
try{const _el=document.getElementById("saved-state");if(_el&&_el.textContent.trim()&&_el.textContent.trim()!=="null")SAVED=JSON.parse(_el.textContent);}catch(e){}
let _local = JSON.parse(localStorage.getItem(KEY) || "null");
let state;
if(SAVED && (!_local || (SAVED.savedAt||0) > (_local.savedAt||0))){ state = SAVED; localStorage.setItem(KEY, JSON.stringify(state)); }
else { state = _local || SAVED || {}; }
if(!state.added) state.added = [];
if(!state.author) state.author = "Gray";
function save(){localStorage.setItem(KEY, JSON.stringify(state));renderProg();}
function st(n){if(!state[n])state[n]={hook:null,status:null,notes:"",hk:{},body:null};return state[n];}
function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function escAttr(s){return esc(s).replace(/"/g,"&quot;");}
function allCards(){return DATA.concat(state.added);}
function newCard(){
  state.seq=(state.seq||0)+1;
  const id="new-"+state.seq;
  state.added.push({num:id,title:"",format:"",why:"",refHtml:"",hooks:[{label:"A",verbal:"",visual:""},{label:"B",verbal:"",visual:""},{label:"C",verbal:"",visual:""}],body:"",prop:"",flags:"",added:true});
  save();render();
  const el=document.querySelector('[data-num="'+id+'"][data-f="title"]');
  if(el){el.scrollIntoView({behavior:"smooth",block:"center"});el.focus();}
}
function downloadFile(text,name){
  const blob=new Blob([text],{type:"text/html"});
  const a=document.createElement("a");
  a.href=URL.createObjectURL(blob);a.download=name;
  document.body.appendChild(a);a.click();
  setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},0);
}
function buildSavedHtml(){
  const ss=document.getElementById("saved-state");
  const prev=ss.textContent;
  ss.textContent=JSON.stringify(state).replace(/</g,"\\u003c");
  const listEl=document.getElementById("list");const keep=listEl.innerHTML;listEl.innerHTML="";
  const out="<!DOCTYPE html>\n"+document.documentElement.outerHTML;
  listEl.innerHTML=keep;ss.textContent=prev;
  return out;
}
async function saveFile(){
  state.savedAt = Date.now();
  save();
  const out=buildSavedHtml();
  const name=SLUG+"-saved.html";
  const btn=document.getElementById("saveBtn");const orig=btn.textContent;
  if(window.showSaveFilePicker){
    try{
      const h=await window.showSaveFilePicker({suggestedName:name,types:[{description:"HTML file",accept:{"text/html":[".html"]}}]});
      const w=await h.createWritable();await w.write(out);await w.close();
      btn.textContent="Saved ✓";setTimeout(function(){btn.textContent=orig;},1500);return;
    }catch(e){if(e&&e.name==="AbortError")return;}
  }
  downloadFile(out,name);
  btn.textContent="Downloaded ✓";setTimeout(function(){btn.textContent=orig;},1500);
}

function render(){
  const list = document.getElementById("list");
  list.innerHTML = "";
  const deleted = DATA.filter(s=>st(s.num).deleted);
  if(deleted.length){
    const b=document.createElement("div"); b.className="delbanner";
    b.innerHTML=`${deleted.length} video${deleted.length>1?'s':''} deleted (#${deleted.map(s=>s.num).join(", #")}) · <a id="restoreAll">restore all</a>`;
    list.appendChild(b);
  }
  allCards().forEach(s=>{
    const cur = st(s.num);
    if(cur.deleted) return;
    const card = document.createElement("div");
    card.className = "card" + (cur.status?(" "+cur.status):"") + (s.added?" added":"");
    const hooks = s.hooks.map(h=>{
      const e = (cur.hk && cur.hk[h.label]) || {};
      const v = e.verbal!==undefined ? e.verbal : h.verbal;
      const vis = e.visual!==undefined ? e.visual : h.visual;
      return `<div class="hook ${cur.hook===h.label?'picked':''}">
        <div class="tag" data-num="${s.num}" data-hook="${h.label}" title="pick this hook to test">${h.label}</div>
        <div class="fields">
          <input class="edit verbal" data-num="${s.num}" data-hook="${h.label}" data-f="verbal" value="${escAttr(v)}">
          <input class="edit visual" data-num="${s.num}" data-hook="${h.label}" data-f="visual" value="${escAttr(vis)}" placeholder="🎬 visual treatment…">
        </div></div>`;
    }).join("");
    const bodyVal = cur.body!==null && cur.body!==undefined ? cur.body : s.body;
    const titleVal = (cur.title!==undefined && cur.title!==null) ? cur.title : s.title;
    const fmtVal = (cur.format!==undefined && cur.format!==null) ? cur.format : s.format;
    const head = s.added
      ? `<div class="newtag">✦ New card</div>
      <input class="edit titleedit" data-num="${s.num}" data-f="title" value="${escAttr(titleVal)}" placeholder="Title…">
      <input class="edit fmtedit" data-num="${s.num}" data-f="format" value="${escAttr(fmtVal)}" placeholder="Format (optional)…">`
      : `<div class="fmt">#${s.num} · ${esc(s.format)}</div>
      <h2>${esc(s.title)}</h2>
      ${s.why?`<div class="why">${esc(s.why)}</div>`:''}
      ${s.refHtml?`<div class="refrow">📊 Modeled on: ${s.refHtml}</div>`:''}`;
    const cmts = (cur.comments||[]).map((c,ci)=>`<div class="cmt"><span class="cdel" data-num="${s.num}" data-ci="${ci}" title="delete comment">✕</span><span class="who ${c.by==='Sai'?'whoSai':'whoGray'}">${esc(c.by)}</span><span class="when">${esc(c.at||'')}</span><div class="ctext">${esc(c.text)}</div></div>`).join("");
    const commentsBlock = `<div class="comments"><div class="section-label">💬 Comments</div><div class="thread">${cmts||'<div class="empty-thread">No comments yet.</div>'}</div><div class="addcomment"><textarea class="commentinput" data-num="${s.num}" placeholder="Add a comment as ${escAttr(state.author)}…"></textarea><button class="commentbtn" data-num="${s.num}">Comment</button></div></div>`;
    card.innerHTML = `
      <span class="delbtn" data-num="${s.num}" title="${s.added?'remove this card':'delete this video from the batch'}">${s.added?'✕ remove':'🗑 delete'}</span>
      ${head}
      <div class="section-label">Hooks — click a letter to pick the one to test; edit text directly</div>
      ${hooks}
      <div class="section-label">Script</div>
      <textarea class="edit bodyedit" data-num="${s.num}" data-f="body" placeholder="Script lines, one per line…">${esc(bodyVal)}</textarea>
      ${(!s.added&&s.prop)?`<div class="note"><b>Setup:</b> ${esc(s.prop)}</div>`:''}
      ${(!s.added&&s.flags)?`<div class="flag"><b>⚑ Invented:</b> ${esc(s.flags)}</div>`:''}
      <div class="controls">
        <div class="pill approve ${cur.status==='approve'?'on':''}" data-num="${s.num}" data-status="approve">✓ Approve</div>
        <div class="pill swap ${cur.status==='swap'?'on':''}" data-num="${s.num}" data-status="swap">↻ Swap</div>
        <div class="pill cut ${cur.status==='cut'?'on':''}" data-num="${s.num}" data-status="cut">✕ Cut</div>
      </div>
      <textarea class="notes" data-num="${s.num}" data-f="notes" placeholder="Notes / direction for this one…">${esc(cur.notes||"")}</textarea>
      ${commentsBlock}`;
    list.appendChild(card);
  });
  const addBtn = document.createElement("button");
  addBtn.className = "addcard"; addBtn.textContent = "+ Add a card";
  addBtn.onclick = newCard;
  list.appendChild(addBtn);
  // pick a hook
  list.querySelectorAll(".tag").forEach(el=>el.onclick=()=>{const c=st(el.dataset.num);c.hook=(c.hook===el.dataset.hook?null:el.dataset.hook);save();render();});
  // toggle status
  list.querySelectorAll(".pill").forEach(el=>el.onclick=()=>{const c=st(el.dataset.num);c.status=(c.status===el.dataset.status?null:el.dataset.status);save();render();});
  // delete a video — built-in = soft delete (restorable); added card = remove
  list.querySelectorAll(".delbtn").forEach(el=>el.onclick=()=>{
    const n=el.dataset.num;
    if(String(n).indexOf("new-")===0){state.added=state.added.filter(c=>c.num!==n);delete state[n];}
    else{st(n).deleted=true;}
    save();render();
  });
  const ra=document.getElementById("restoreAll"); if(ra) ra.onclick=()=>{DATA.forEach(s=>{if(state[s.num])state[s.num].deleted=false;});save();render();};
  // edits (hooks + body + notes) — save without re-render to keep focus
  list.querySelectorAll(".edit, .notes").forEach(el=>el.oninput=()=>{
    const c=st(el.dataset.num), f=el.dataset.f;
    if(f==="verbal"||f==="visual"){c.hk[el.dataset.hook]=c.hk[el.dataset.hook]||{};c.hk[el.dataset.hook][f]=el.value;}
    else if(f==="body"){c.body=el.value;}
    else if(f==="notes"){c.notes=el.value;}
    else if(f==="title"){c.title=el.value;}
    else if(f==="format"){c.format=el.value;}
    save();
  });
  list.querySelectorAll(".commentbtn").forEach(el=>el.onclick=()=>{
    const n=el.dataset.num;
    const ta=document.querySelector('.commentinput[data-num="'+n+'"]');
    const txt=(ta&&ta.value.trim())||"";
    if(!txt) return;
    const c=st(n); if(!c.comments) c.comments=[];
    c.comments.push({by:state.author||"Gray",at:new Date().toLocaleDateString(undefined,{month:"short",day:"numeric"}),text:txt});
    save();render();
  });
  list.querySelectorAll(".cdel").forEach(el=>el.onclick=()=>{
    const n=el.dataset.num,ci=+el.dataset.ci;const c=st(n);
    if(c.comments){c.comments.splice(ci,1);save();render();}
  });
  renderProg();
}
function renderProg(){
  const all = allCards();
  const done = all.filter(s=>state[s.num] && state[s.num].status).length;
  document.getElementById("prog").textContent = done+" / "+all.length+" reviewed";
}
document.getElementById("copyBtn").onclick=()=>{
  let out = "BATCH DECISIONS + EDITS\n\n";
  allCards().forEach(s=>{const c=state[s.num]||{};
    if(s.added){
      if(c.deleted) return;
      out += `NEW CARD: ${c.title||"(untitled)"}\n`;
      if(c.format) out += `  format: ${c.format}\n`;
      out += `  status: ${c.status||"(none)"} | hook: ${c.hook||"(none)"}\n`;
      if(c.hk) for(const k of ["A","B","C"]){const e=c.hk[k]; if(e){
        if(e.verbal) out+=`  hook ${k} verbal: ${e.verbal}\n`;
        if(e.visual) out+=`  hook ${k} visual: ${e.visual}\n`;
      }}
      if(c.body) out+=`  script:\n    ${c.body.replace(/\n/g,"\n    ")}\n`;
      if(c.notes) out += `  notes: ${c.notes}\n`;
      if(c.comments&&c.comments.length) for(const cm of c.comments) out += `  [${cm.by} ${cm.at||''}] ${cm.text}\n`;
      out += "\n";
      return;
    }
    if(c.deleted){out+=`#${s.num} ${s.title}\n  DELETED\n\n`;return;}
    out += `#${s.num} ${s.title}\n  status: ${c.status||"(none)"} | hook: ${c.hook||"(none)"}\n`;
    if(c.hk) for(const k of ["A","B","C"]){const e=c.hk[k]; if(e&&(e.verbal!==undefined||e.visual!==undefined)){
      const orig=s.hooks.find(h=>h.label===k)||{};
      if(e.verbal!==undefined&&e.verbal!==orig.verbal) out+=`  EDITED hook ${k} verbal: ${e.verbal}\n`;
      if(e.visual!==undefined&&e.visual!==orig.visual) out+=`  EDITED hook ${k} visual: ${e.visual}\n`;
    }}
    if(c.body!==undefined&&c.body!==null&&c.body!==s.body) out+=`  EDITED script:\n    ${c.body.replace(/\n/g,"\n    ")}\n`;
    if(c.notes) out += `  notes: ${c.notes}\n`;
    if(c.comments&&c.comments.length) for(const cm of c.comments) out += `  [${cm.by} ${cm.at||''}] ${cm.text}\n`;
    out += "\n";});
  document.getElementById("summary").textContent = out;
  document.getElementById("modal").classList.add("show");
  if(navigator.clipboard) navigator.clipboard.writeText(out);
};
document.getElementById("closeModal").onclick=()=>document.getElementById("modal").classList.remove("show");
document.getElementById("resetBtn").onclick=()=>{if(confirm("Clear all decisions AND edits in this browser?")){state={added:[],author:"Gray"};save();authSel.value="Gray";render();}};
document.getElementById("addBtnTop").onclick=newCard;
document.getElementById("saveBtn").onclick=saveFile;
const authSel=document.getElementById("author");
authSel.value=state.author||"Gray";
authSel.onchange=()=>{state.author=authSel.value;save();render();};
render();
</script></body></html>"""

slug = re.sub(r"[^a-z0-9]+", "-", page_title.lower()).strip("-")
HTML = (HTML.replace("__PAGE_TITLE__", html.escape(page_title))
            .replace("__DATA__", DATA)
            .replace("__SLUG__", slug))
open(out_path, "w", encoding="utf-8").write(HTML)
print("wrote", out_path, "| scripts:", len(scripts))
