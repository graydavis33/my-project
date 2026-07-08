"""
Parse a Sai shorts batch markdown doc (v6 template) into structured video dicts.

The template is plain "Label: value" lines, one page per "## Video N — title".
Hooks come in three flavors (Verbal / Caption / Visual), each A/B/C; Topics is a
bulleted list of this video's real subjects. The Editor brief holds a markdown
shot-list table that becomes a per-video child database in Notion. Placeholder
pages (title contains "[working title]") and the Foundation are skipped.
"""
import re

# Fields that hold a single line of text after "Label:"
SINGLE = {
    "Status": "status",
    "Format": "format",
    "Orientation": "orientation",
    "Props": "props",
    "Assets": "assets",
    "Keep / drop from raw": "keep_drop",
}

TOPICS_LABEL = "Topics (Sai to fill):"

# Shot-list table columns, in order. Maps to the child shot-list database.
SHOT_COLS = ["section", "shot_name", "shot_type", "duration", "prop", "graphics", "retention", "editor_notes"]

VIDEO_RE = re.compile(r"^##\s+Video\s+(.+?)\s+[—-]\s+(.+)$")
SUBITEM_RE = re.compile(r"^-\s*([^:]+):\s*(.*)$")
OUTLIER_RE = re.compile(r"[—-]\s*([\d.]+)x")


def _parse_table_row(stripped):
    """Return a shot dict for a real data row, or None for header/separator/placeholder rows."""
    cells = [c.strip() for c in stripped.strip("|").split("|")]
    joined = "".join(cells)
    if joined and set(joined) <= set("-: "):  # separator row like |---|---|
        return None
    if cells and cells[0].lower() == "section":  # header row
        return None
    sec = cells[0] if cells else ""
    if not sec or sec.startswith("[") or sec == "...":  # empty or template placeholder
        return None
    return {k: (cells[i] if i < len(cells) else "") for i, k in enumerate(SHOT_COLS)}


def parse(md: str) -> list[dict]:
    videos = []
    cur = None
    mode = None  # which block we're collecting: verbal/visual/editor/shots/reference

    def push():
        if cur and "[working title]" not in cur.get("title", ""):
            videos.append(cur)

    for raw in md.splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        m = VIDEO_RE.match(stripped)
        if m:
            push()
            cur = {
                "id": m.group(1).strip(),
                "title": f"{m.group(1).strip()} — {m.group(2).strip()}",
                "verbal": {}, "caption": {}, "visual": {}, "editor": {}, "reference": {},
                "shots": [], "topics_list": [],
            }
            mode = None
            continue

        if cur is None:
            continue

        # Leaving the per-video region
        if stripped.startswith("## ") or stripped == "---":
            push()
            cur = None
            mode = None
            continue

        if not stripped:
            continue

        # Block headers
        if stripped == "Verbal hook:":
            mode = "verbal"; continue
        if stripped == "Caption hook:":
            mode = "caption"; continue
        if stripped == "Visual hook:":
            mode = "visual"; continue
        if stripped.startswith(TOPICS_LABEL):
            mode = "topics"
            inline = stripped[len(TOPICS_LABEL):].strip()
            if inline:
                cur["topics_list"].append(inline)
            continue
        if stripped.startswith("Editor brief"):
            mode = "editor"; continue
        if stripped.startswith("Shot list"):
            mode = "shots"; continue
        if stripped.startswith("Reference:"):
            mode = "reference"
            cur["reference"]["label"] = stripped[len("Reference:"):].strip()
            mo = OUTLIER_RE.search(stripped)
            if mo:
                cur["outlier"] = float(mo.group(1))
            continue

        # Shot-list table rows (only collected while in the shots block)
        if mode == "shots" and stripped.startswith("|"):
            row = _parse_table_row(stripped)
            if row:
                cur["shots"].append(row)
            continue

        # Topic bullets (plain "- item", no key:value)
        if mode == "topics" and stripped.startswith("-"):
            cur["topics_list"].append(stripped.lstrip("-").strip())
            continue

        # Sub-items inside a block
        if stripped.startswith("-") and mode in ("verbal", "caption", "visual", "editor", "reference"):
            sm = SUBITEM_RE.match(stripped)
            if sm:
                key, val = sm.group(1).strip(), sm.group(2).strip()
                if mode in ("verbal", "caption", "visual"):
                    cur[mode][key] = val
                elif mode == "editor":
                    cur["editor"][key] = val
                elif mode == "reference":
                    cur["reference"][key.lower()] = val
                continue

        # Single-line "Label: value" fields
        if ":" in stripped:
            label, _, val = stripped.partition(":")
            label = label.strip()
            if label in SINGLE:
                cur[SINGLE[label]] = val.strip()
                mode = None
                continue

    push()
    return videos
