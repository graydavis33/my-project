"""
Parse a Sai shorts batch markdown doc (v4 template) into structured video dicts.

The template is plain "Label: value" lines, one page per "## Video N — title".
Placeholder pages (title contains "[working title]") and the Foundation are skipped.
"""
import re

# Fields that hold a single line of text after "Label:"
SINGLE = {
    "Status": "status",
    "Format": "format",
    "Topics (Sai to fill)": "topics",
    "Camera shots": "camera",
    "Graphics and effects": "graphics",
    "Props": "props",
    "Assets": "assets",
}

VIDEO_RE = re.compile(r"^##\s+Video\s+(.+?)\s+[—-]\s+(.+)$")
SUBITEM_RE = re.compile(r"^-\s*([^:]+):\s*(.*)$")
OUTLIER_RE = re.compile(r"[—-]\s*([\d.]+)x")


def parse(md: str) -> list[dict]:
    videos = []
    cur = None
    mode = None  # which multi-line block we're collecting: verbal/visual/editor/reference

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
                "verbal": {}, "visual": {}, "editor": {}, "reference": {},
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
        if stripped == "Visual hook:":
            mode = "visual"; continue
        if stripped == "Editor brief:":
            mode = "editor"; continue
        if stripped.startswith("Reference:"):
            mode = "reference"
            cur["reference"]["label"] = stripped[len("Reference:"):].strip()
            mo = OUTLIER_RE.search(stripped)
            if mo:
                cur["outlier"] = float(mo.group(1))
            continue

        # Sub-items inside a block
        if stripped.startswith("-") and mode:
            sm = SUBITEM_RE.match(stripped)
            if sm:
                key, val = sm.group(1).strip(), sm.group(2).strip()
                if mode in ("verbal", "visual"):
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
