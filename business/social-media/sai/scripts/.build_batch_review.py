"""Generate a self-contained HTML review page from a batch script .md file.
Parses ### N — Title blocks, their A/B/C hooks (+ Visual: lines), body, notes/flags,
and renders a reviewable page with hook-pick + Approve/Swap/Cut + notes (localStorage),
plus a 'Copy decisions' export. No server, no deps — just open the .html."""
import json, re, sys, html, os

SRC = sys.argv[1] if len(sys.argv) > 1 else "2026-06-15-batch-3.md"
HERE = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(HERE, SRC)
out_path = os.path.splitext(src_path)[0] + "-review.html"

text = open(src_path, encoding="utf-8").read()
# intro = everything before first "### "
parts = re.split(r"\n### ", text)
intro = parts[0]
title_m = re.search(r"^#\s*(.+)", intro)
page_title = title_m.group(1).strip() if title_m else "Batch Review"

scripts = []
for block in parts[1:]:
    lines = block.split("\n")
    head = lines[0].strip()
    if head.startswith("#"):  # hit the trailing "## Open Questions" section
        continue
    m = re.match(r"(\d+)\s*[—-]\s*(.+)", head)
    num = m.group(1) if m else "?"
    title = (m.group(2) if m else head).strip()
    body_md = "\n".join(lines[1:])

    fmt = ""
    fm = re.search(r"\*\*Format:\*\*\s*(.+)", body_md)
    if fm: fmt = fm.group(1).strip()

    # hooks: lines "A. text" optionally followed by "**Visual:** ..."
    hooks = []
    hl = body_md.split("\n")
    for i, ln in enumerate(hl):
        hm = re.match(r"^([ABC])\.\s+(.+)", ln)
        if hm:
            verbal = hm.group(2).strip()
            visual = ""
            if i + 1 < len(hl):
                vm = re.match(r"\*\*Visual:\*\*\s*(.+)", hl[i+1].strip())
                if vm: visual = vm.group(1).strip()
            hooks.append({"label": hm.group(1), "verbal": verbal, "visual": visual})

    # body: blockquote lines after **Script:**
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
    why = grab("Why it works")

    scripts.append({"num": num, "title": title, "format": fmt, "why": why,
                    "hooks": hooks, "body": body, "prop": prop, "flags": flags})

DATA = json.dumps(scripts)

HTML = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
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
.wrap{max-width:860px;margin:0 auto;padding:22px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px;margin-bottom:18px}
.card.approve{border-color:var(--good)}.card.swap{border-color:var(--warn)}.card.cut{border-color:var(--bad);opacity:.7}
.card h2{margin:0 0 4px;font-size:17px}.fmt{color:var(--accent);font-size:13px;margin-bottom:2px}
.why{color:var(--muted);font-size:12.5px;margin-bottom:14px}
.section-label{text-transform:uppercase;letter-spacing:.6px;font-size:11px;color:var(--muted);margin:14px 0 8px}
.hook{border:1px solid var(--line);border-radius:9px;padding:11px 13px;margin-bottom:8px;cursor:pointer;display:flex;gap:11px;align-items:flex-start}
.hook:hover{border-color:var(--accent)}.hook.picked{border-color:var(--accent);background:rgba(242,129,41,.08)}
.hook .tag{font-weight:700;color:var(--accent);min-width:18px}
.hook .verbal{font-weight:600}.hook .visual{color:var(--muted);font-size:12.5px;margin-top:3px}
.body{background:var(--panel2);border-radius:9px;padding:14px 16px;font-size:14.5px}
.body p{margin:0 0 7px}
.note{font-size:12.5px;color:var(--muted);margin-top:10px}.note b{color:var(--text)}
.flag{font-size:12.5px;color:var(--warn);margin-top:6px}
.controls{display:flex;gap:8px;margin-top:14px;align-items:center;flex-wrap:wrap}
.pill{padding:7px 14px;border-radius:20px;border:1px solid var(--line);cursor:pointer;font-size:13px}
.pill.approve.on{background:var(--good);color:#06281a;border-color:var(--good);font-weight:600}
.pill.swap.on{background:var(--warn);color:#3a2a0d;border-color:var(--warn);font-weight:600}
.pill.cut.on{background:var(--bad);color:#2c0d0d;border-color:var(--bad);font-weight:600}
textarea{width:100%;margin-top:10px;background:var(--panel2);border:1px solid var(--line);color:var(--text);border-radius:8px;padding:10px;font-family:inherit;font-size:13.5px;resize:vertical;min-height:48px}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.6);display:none;align-items:center;justify-content:center;z-index:20}
.modal.show{display:flex}.modal .inner{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px;max-width:640px;width:92%;max-height:80vh;overflow:auto}
.modal pre{white-space:pre-wrap;font-size:13px;color:var(--text)}
</style></head><body>
<header>
  <div><h1>__PAGE_TITLE__</h1><div class="sub">Hook pick + Approve / Swap / Cut + notes. Saves in your browser automatically.</div></div>
  <div class="bar"><span class="progress" id="prog"></span><button id="copyBtn" class="primary">Copy decisions</button><button id="resetBtn">Reset</button></div>
</header>
<div class="wrap" id="wrap"></div>
<div class="modal" id="modal"><div class="inner"><h2 style="margin-top:0">Decisions summary</h2><pre id="summary"></pre><div style="margin-top:12px"><button id="closeModal">Close</button></div></div></div>
<script>
const DATA = __DATA__;
const KEY = "batch-review-__SLUG__";
let state = JSON.parse(localStorage.getItem(KEY) || "{}");
function save(){localStorage.setItem(KEY, JSON.stringify(state));renderProg();}
function st(n){return state[n] || (state[n] = {hook:null,status:null,notes:""});}
function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}

function render(){
  const wrap = document.getElementById("wrap");
  wrap.innerHTML = "";
  DATA.forEach(s=>{
    const cur = st(s.num);
    const card = document.createElement("div");
    card.className = "card" + (cur.status?(" "+cur.status):"");
    card.id = "c"+s.num;
    let hooks = s.hooks.map(h=>`
      <div class="hook ${cur.hook===h.label?'picked':''}" data-num="${s.num}" data-hook="${h.label}">
        <div class="tag">${h.label}</div>
        <div><div class="verbal">${esc(h.verbal)}</div>${h.visual?`<div class="visual">🎬 ${esc(h.visual)}</div>`:''}</div>
      </div>`).join("");
    let body = s.body.map(p=>`<p>${esc(p)}</p>`).join("");
    card.innerHTML = `
      <div class="fmt">#${s.num} · ${esc(s.format)}</div>
      <h2>${esc(s.title)}</h2>
      ${s.why?`<div class="why">${esc(s.why)}</div>`:''}
      <div class="section-label">Hooks — pick the one to test (visual + verbal)</div>
      ${hooks}
      <div class="section-label">Script</div>
      <div class="body">${body}</div>
      ${s.prop?`<div class="note"><b>Setup:</b> ${esc(s.prop)}</div>`:''}
      ${s.flags?`<div class="flag"><b>⚑ Invented:</b> ${esc(s.flags)}</div>`:''}
      <div class="controls">
        <div class="pill approve ${cur.status==='approve'?'on':''}" data-num="${s.num}" data-status="approve">✓ Approve</div>
        <div class="pill swap ${cur.status==='swap'?'on':''}" data-num="${s.num}" data-status="swap">↻ Swap</div>
        <div class="pill cut ${cur.status==='cut'?'on':''}" data-num="${s.num}" data-status="cut">✕ Cut</div>
      </div>
      <textarea data-num="${s.num}" placeholder="Notes / changes for this one…">${esc(cur.notes)}</textarea>`;
    wrap.appendChild(card);
  });
  wrap.querySelectorAll(".hook").forEach(el=>el.onclick=()=>{const n=el.dataset.num;st(n).hook=el.dataset.hook;save();render();});
  wrap.querySelectorAll(".pill").forEach(el=>el.onclick=()=>{const n=el.dataset.num;const s=st(n);s.status=(s.status===el.dataset.status?null:el.dataset.status);save();render();});
  wrap.querySelectorAll("textarea").forEach(el=>el.oninput=()=>{st(el.dataset.num).notes=el.value;save();});
  renderProg();
}
function renderProg(){
  const done = DATA.filter(s=>state[s.num] && state[s.num].status).length;
  document.getElementById("prog").textContent = done+" / "+DATA.length+" reviewed";
}
document.getElementById("copyBtn").onclick=()=>{
  let out = "BATCH DECISIONS\\n\\n";
  DATA.forEach(s=>{const c=state[s.num]||{};
    out += `#${s.num} ${s.title}\\n  status: ${c.status||"(none)"} | hook: ${c.hook||"(none)"}\\n`;
    if(c.notes) out += `  notes: ${c.notes}\\n`; out += "\\n";});
  document.getElementById("summary").textContent = out;
  document.getElementById("modal").classList.add("show");
  navigator.clipboard && navigator.clipboard.writeText(out);
};
document.getElementById("closeModal").onclick=()=>document.getElementById("modal").classList.remove("show");
document.getElementById("resetBtn").onclick=()=>{if(confirm("Clear all your review decisions?")){state={};save();render();}};
render();
</script></body></html>"""

slug = re.sub(r"[^a-z0-9]+", "-", page_title.lower()).strip("-")
HTML = (HTML.replace("__PAGE_TITLE__", html.escape(page_title))
            .replace("__DATA__", DATA)
            .replace("__SLUG__", slug))
open(out_path, "w", encoding="utf-8").write(HTML)
print("wrote", out_path)
print("scripts parsed:", len(scripts))
for s in scripts:
    print(f"  #{s['num']} {s['title']}  ({len(s['hooks'])} hooks, {len(s['body'])} body lines)")
