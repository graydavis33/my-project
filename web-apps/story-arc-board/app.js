// Story-Arc Board — folder-scoped long-form storyboarding.
// Cards (clips + text notes) get dragged onto story-arc lanes; spine/title/thumbnail
// are locked at the top before the A-roll is filmed. Board state saves to the server.

const LANES = [
  { id: "coldopen", name: "Cold Open / Hook", desc: "The grab. Signature open.", color: "#F28129" },
  { id: "setup",    name: "Setup",            desc: "Who/where/what's at stake.", color: "#e0a44a" },
  { id: "rising",   name: "Rising Action",    desc: "Something's coming. Tension builds.", color: "#d6c24a" },
  { id: "conflict", name: "Conflict / Climax",desc: "The peak. The hard moment.", color: "#cf5b5b" },
  { id: "turn",     name: "Character Arc / Turn", desc: "The epiphany. The change.", color: "#7a6cd6" },
  { id: "resolution", name: "Resolution",     desc: "Coming down. The lesson, through the story.", color: "#3ecf8e" },
];

// state
let clipsById = {};           // id -> clip meta
let cardState = {};           // id -> { lane, note? }
let order = {};               // lane -> [ids]
let thumbnailId = null;
LANES.forEach(l => order[l.id] = []);
order["pool"] = [];
let noteSeq = 1;

const $ = sel => document.querySelector(sel);

// ---- build lanes ----
function buildLanes() {
  const arc = $("#arc");
  arc.innerHTML = "";
  for (const lane of LANES) {
    const el = document.createElement("section");
    el.className = "lane";
    el.style.setProperty("--lane-color", lane.color);
    el.innerHTML = `<h3>${lane.name}</h3><div class="desc">${lane.desc}</div>
      <div class="cards droptarget" data-lane="${lane.id}"></div>`;
    arc.appendChild(el);
  }
  wireDropTargets();
}

// ---- card rendering ----
function cardEl(id) {
  const st = cardState[id];
  const div = document.createElement("div");
  div.className = "card";
  div.draggable = true;
  div.dataset.id = id;

  if (st.note !== undefined) {
    div.classList.add("note");
    div.innerHTML = `<button class="del" title="delete">✕</button>
      <textarea class="note-text" placeholder="plot point…">${st.note}</textarea>`;
    div.querySelector(".note-text").addEventListener("input", e => { cardState[id].note = e.target.value; });
    div.querySelector(".del").addEventListener("click", () => deleteCard(id));
  } else {
    const c = clipsById[id];
    if (c.vertical) div.classList.add("vertical");
    const mins = Math.floor(c.duration / 60), secs = Math.round(c.duration % 60);
    const dur = c.duration ? `${mins}:${String(secs).padStart(2, "0")}` : "";
    div.innerHTML = `
      <button class="star ${thumbnailId === id ? "active" : ""}" title="use as thumbnail">★</button>
      <div class="thumb" style="background-image:url('/api/thumb?path=${encodeURIComponent(c.path)}')"></div>
      <div class="meta">
        <div class="name">${c.name}</div>
        <div class="sub"><span>${dur}</span><span>${c.filmed_date || ""}</span></div>
      </div>`;
    div.querySelector(".star").addEventListener("click", e => { e.stopPropagation(); setThumbnail(id); });
  }

  wireDrag(div);
  return div;
}

function render() {
  for (const lane of [...LANES.map(l => l.id), "pool"]) {
    const host = document.querySelector(`.cards[data-lane="${lane}"]`);
    if (!host) continue;
    host.innerHTML = "";
    for (const id of order[lane]) host.appendChild(cardEl(id));
  }
}

// ---- drag & drop ----
let draggingId = null;
function wireDrag(el) {
  el.addEventListener("dragstart", e => {
    draggingId = el.dataset.id;
    el.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
  });
  el.addEventListener("dragend", () => { el.classList.remove("dragging"); draggingId = null; });
}

function wireDropTargets() {
  document.querySelectorAll(".droptarget").forEach(host => {
    host.addEventListener("dragover", e => {
      e.preventDefault();
      host.classList.add("drag-over");
    });
    host.addEventListener("dragleave", () => host.classList.remove("drag-over"));
    host.addEventListener("drop", e => {
      e.preventDefault();
      host.classList.remove("drag-over");
      if (!draggingId) return;
      const lane = host.dataset.lane;
      const after = e.target.closest(".card");
      moveCard(draggingId, lane, after ? after.dataset.id : null);
    });
  });
}

function moveCard(id, lane, beforeId) {
  // remove from wherever it is
  for (const k of Object.keys(order)) order[k] = order[k].filter(x => x !== id);
  cardState[id].lane = lane;
  if (beforeId && beforeId !== id) {
    const idx = order[lane].indexOf(beforeId);
    order[lane].splice(idx, 0, id);
  } else {
    order[lane].push(id);
  }
  render();
}

function deleteCard(id) {
  for (const k of Object.keys(order)) order[k] = order[k].filter(x => x !== id);
  delete cardState[id];
  if (thumbnailId === id) setThumbnail(null);
  render();
}

// ---- thumbnail ----
function setThumbnail(id) {
  thumbnailId = id;
  const slot = $("#thumbSlot");
  if (id && clipsById[id]) {
    slot.innerHTML = `<img src="/api/thumb?path=${encodeURIComponent(clipsById[id].path)}">`;
  } else {
    slot.textContent = "no thumbnail yet";
  }
  render();
}

// ---- load clips from a specific folder ----
async function loadFolder() {
  const folder = $("#folderPath").value.trim();
  if (!folder) return;
  $("#scanStatus").textContent = "scanning…";
  try {
    const res = await fetch(`/api/scan?folder=${encodeURIComponent(folder)}&recursive=${$("#recursive").checked ? 1 : 0}`);
    const data = await res.json();
    if (data.error) { $("#scanStatus").textContent = data.error; return; }
    for (const c of data.clips) {
      if (clipsById[c.id]) continue;     // don't duplicate already-loaded clips
      clipsById[c.id] = c;
      cardState[c.id] = { lane: "pool" };
      order["pool"].push(c.id);
    }
    $("#scanStatus").textContent =
      `${data.count} clips · index ${data.indexed ? "connected" : "not mounted (ffprobe only)"}`;
    render();
  } catch (e) {
    $("#scanStatus").textContent = "scan failed — is server.py running?";
  }
}

// ---- text note cards ----
function addNote() {
  const id = "note-" + (noteSeq++);
  cardState[id] = { lane: "pool", note: "" };
  order["pool"].push(id);
  render();
}

// ---- save / load board ----
function snapshot() {
  return {
    name: $("#boardName").value.trim(),
    spine: { story: $("#spineStory").value, title: $("#spineTitle").value },
    thumbnailId,
    order,
    cardState,
    clips: clipsById,
    noteSeq,
  };
}

async function saveBoard() {
  const name = $("#boardName").value.trim();
  if (!name) { alert("Name the board first."); return; }
  const res = await fetch("/api/board", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(snapshot()),
  });
  const data = await res.json();
  $("#scanStatus").textContent = data.ok ? `saved · ${data.name}` : "save failed";
  refreshBoardList();
}

async function refreshBoardList() {
  const res = await fetch("/api/boards");
  const { boards } = await res.json();
  const sel = $("#loadSelect");
  sel.innerHTML = `<option value="">Load board…</option>` +
    boards.map(b => `<option value="${b}">${b}</option>`).join("");
}

async function loadBoard(name) {
  if (!name) return;
  const res = await fetch(`/api/board?name=${encodeURIComponent(name)}`);
  const b = await res.json();
  clipsById = b.clips || {};
  cardState = b.cardState || {};
  order = b.order || {};
  LANES.forEach(l => order[l.id] = order[l.id] || []);
  order["pool"] = order["pool"] || [];
  thumbnailId = b.thumbnailId || null;
  noteSeq = b.noteSeq || 1;
  $("#boardName").value = b.name || name;
  $("#spineStory").value = b.spine?.story || "";
  $("#spineTitle").value = b.spine?.title || "";
  setThumbnail(thumbnailId);
  render();
}

// ---- init ----
buildLanes();
$("#loadFolder").addEventListener("click", loadFolder);
$("#folderPath").addEventListener("keydown", e => { if (e.key === "Enter") loadFolder(); });
$("#addNote").addEventListener("click", addNote);
$("#saveBtn").addEventListener("click", saveBoard);
$("#loadSelect").addEventListener("change", e => loadBoard(e.target.value));
refreshBoardList();
