"""
notion-batch — push Sai shorts batch docs into a Notion database.

Each video becomes its own Notion page in the "Sai Shorts — Batches" database.
The outside DB stays simple: Batch, Status, Format, Orientation, Sai notes,
Assets, Reference. The page body holds the detail: Topics (bulleted, per-video),
Verbal/Caption/Visual hooks A-B-C, Hook pick, Props, Editor brief, Editor
questions box, Reference (Original link only).
Each page also gets its own inline "Shot list" child database (one row per shot).

Commands:
  setup    --parent <page-url>          create the database under a parent page (run once)
  migrate                               add v5 columns to an existing database (run once after upgrade)
  push     <batch.md> --batch "Batch 4" create a page per video from a filled batch doc
  find                                  print the saved database id/url

Reuses NOTION_TOKEN (same integration as content-researcher). The parent page must
be shared with that integration first (page ••• -> Connections -> your integration).
"""
import os
import sys
import json
import argparse
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from parser import parse

CONFIG = os.path.join(os.path.dirname(__file__), "config.json")

STATUS_OPTIONS = [
    ("Draft", "default"),
    ("Needs Topics", "yellow"),
    ("Sai Review", "orange"),
    ("Approved", "green"),
    ("Filmed", "blue"),
    ("Sent to Editor", "purple"),
    ("Revisions", "red"),
    ("Posted", "pink"),
]

ORIENTATION_OPTIONS = [("Horizontal", "blue"), ("Vertical", "orange")]

# Per-video child shot-list database (mirrors Gray's Notion "Shot list" DB + editor columns).
# Colorful selects — never leave them grayed out.
SECTION_OPTIONS = [
    ("Intro", "blue"), ("Section 1", "orange"), ("Section 2", "green"),
    ("Section 3", "purple"), ("Section 4", "red"), ("Section 5", "yellow"), ("Outro", "pink"),
]
SHOT_TYPE_OPTIONS = [
    ("EXTREME WIDE", "blue"), ("WIDE", "green"), ("MEDIUM", "purple"), ("CLOSE UP", "pink"),
    ("EXTREME CLOSE UP", "red"), ("SCREEN RECORD", "gray"), ("POV", "orange"),
]


def client():
    token = os.getenv("NOTION_TOKEN")
    if not token:
        sys.exit("NOTION_TOKEN not set. Copy content-researcher/.env's token into notion-batch/.env")
    from notion_client import Client
    # notion-client 3.x speaks the multi-source API natively — use its default version.
    return Client(auth=token)


def page_id_from_url(url: str) -> str:
    raw = url.strip().split("?")[0].rstrip("/").split("-")[-1].split("/")[-1]
    hexs = "".join(c for c in raw if c in "0123456789abcdefABCDEF")
    if len(hexs) < 32:
        sys.exit(f"Could not find a 32-char page id in: {url}")
    h = hexs[-32:]
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def save_config(d):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)


def load_config():
    if not os.path.exists(CONFIG):
        sys.exit("No database yet. Run: python main.py setup --parent <page-url>")
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


# ---------- rich text helpers ----------

def rt(text):
    return [{"type": "text", "text": {"content": text[:2000]}}] if text else []


def link_rt(text, url):
    return [{"type": "text", "text": {"content": text, "link": {"url": url}}}]


def heading(text):
    return {"object": "block", "type": "heading_3",
            "heading_3": {"rich_text": rt(text)}}


def para(text):
    return {"object": "block", "type": "paragraph",
            "paragraph": {"rich_text": rt(text)}}


def para_rich(rich):
    return {"object": "block", "type": "paragraph",
            "paragraph": {"rich_text": rich}}


def bullet(text):
    return {"object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": rt(text)}}


def todo(text):
    return {"object": "block", "type": "to_do",
            "to_do": {"rich_text": rt(text), "checked": False}}


# ---------- commands ----------

def cmd_setup(args):
    notion = client()
    parent = page_id_from_url(args.parent)
    schema = {
        "Video": {"title": {}},
        "Batch": {"select": {}},
        "Status": {"select": {"options": [{"name": n, "color": c} for n, c in STATUS_OPTIONS]}},
        "Format": {"rich_text": {}},
        "Orientation": {"select": {"options": [{"name": n, "color": c} for n, c in ORIENTATION_OPTIONS]}},
        "Sai notes": {"rich_text": {}},
        "Assets": {"url": {}},
        "Reference": {"url": {}},
    }
    # notion-client 3.x (new multi-source API): schema lives under initial_data_source,
    # and pages attach to the data source, not the database.
    db = notion.databases.create(
        parent={"type": "page_id", "page_id": parent},
        title=rt(args.title),
        initial_data_source={"properties": schema},
    )
    url = db.get("url", "")
    ds_id = db.get("data_sources", [{}])[0].get("id")
    save_config({"database_id": db["id"], "data_source_id": ds_id, "url": url})
    print(f"Created database: {args.title}")
    print(f"URL: {url}")
    print("Saved database id to config.json. Now push a batch with:  python main.py push <batch.md> --batch \"Batch 4\"")


def video_to_page(db_id, batch, v):
    status = v.get("status", "Draft")
    if status not in [n for n, _ in STATUS_OPTIONS]:
        status = "Draft"

    props = {
        "Video": {"title": rt(v["title"])},
        "Batch": {"select": {"name": batch}},
        "Status": {"select": {"name": status}},
        "Format": {"rich_text": rt(v.get("format", ""))},
    }
    orientation = v.get("orientation", "")
    if orientation.startswith("Vertical"):
        props["Orientation"] = {"select": {"name": "Vertical"}}
    elif orientation.startswith("Horizontal"):
        props["Orientation"] = {"select": {"name": "Horizontal"}}
    if v.get("assets") and v["assets"].startswith("http"):
        props["Assets"] = {"url": v["assets"]}
    # Reference column = the public Original link (recipients have no Sandcastles account).
    original = v["reference"].get("original", "")
    if original.startswith("http"):
        props["Reference"] = {"url": original}

    body = []
    # Topics — bold, bulleted, impossible to miss. Each video carries its own real subjects.
    topics_list = v.get("topics_list", [])
    body.append(heading("Topics — Sai fill this in"))
    body.append({"object": "block", "type": "callout",
                 "callout": {"rich_text": rt("Sai — add the real subjects for this video:" if topics_list
                                             else "Sai — add the real subjects here."),
                             "icon": {"emoji": "✍️"}, "color": "yellow_background"}})
    for t in topics_list:
        body.append(bullet(t))

    # Verbal/Caption/Visual hooks are to-do checkboxes — Sai multi-selects the
    # options he wants and how to pair them.
    for label, key in (("Verbal hook", "verbal"), ("Caption hook", "caption"), ("Visual hook", "visual")):
        body.append(heading(label))
        block = v.get(key, {})
        for opt in ("A", "B", "C"):
            val = block.get(opt, "")
            body.append(todo(f"{opt}: {val}".rstrip(": ")))

    body.append(heading("Hook pick"))
    body.append(para(v.get("hook_pick", "") or "Sai picks; multi-select the options + pairings you want. Blank = editor gets all options."))

    body.append(heading("Props"))
    body.append(para(v.get("props", "") or "none"))

    body.append(heading("Editor brief"))
    for k, val in v.get("editor", {}).items():
        body.append(bullet(f"{k}: {val}".rstrip(": ")))
    if v.get("keep_drop"):
        body.append(bullet(f"Keep / drop from raw: {v['keep_drop']}"))
    body.append(para("Shot list -> the linked database below."))

    # Editor questions — the editor's "I'm stuck on this" box. Native Notion
    # comments + an @Gray mention here send him a notification (no custom build).
    body.append(heading("Editor questions"))
    body.append({"object": "block", "type": "callout",
                 "callout": {"rich_text": rt("Editor — drop any question or missing-context request here. "
                                             "Add a Notion comment and @mention Gray so he gets notified."),
                             "icon": {"emoji": "❓"}, "color": "blue_background"}})

    body.append(heading("Reference"))
    if v["reference"].get("label"):
        body.append(para(v["reference"]["label"]))
    # Original link only — never the Sandcastles Watch link (recipients have no account).
    if v["reference"].get("original", "").startswith("http"):
        body.append(para_rich(link_rt("Original", v["reference"]["original"])))

    return props, body


def _clean(val):
    """Treat the template's em-dash placeholder as empty."""
    v = (val or "").strip()
    return "" if v in ("—", "-", "...") else v


def create_shot_list_db(notion, page_id, shots):
    """Create a per-video child shot-list database and add a row per shot.

    Mirrors Gray's Notion 'Shot list' DB (Section, Shot name, Shot type, Complete?,
    Shot Notes, Time of Day, Location, Shoot Day) plus the editor columns
    (Duration, Prop, Graphics / effect, Retention beat). On-set columns are left
    empty to fill in Notion. API can't create the Basic/Editor *views* — add those
    by hand once.
    """
    schema = {
        "Shot name": {"title": {}},
        "Section": {"select": {"options": [{"name": n, "color": c} for n, c in SECTION_OPTIONS]}},
        "Shot type": {"select": {"options": [{"name": n, "color": c} for n, c in SHOT_TYPE_OPTIONS]}},
        "Duration": {"rich_text": {}},
        "Prop": {"rich_text": {}},
        "Graphics / effect": {"rich_text": {}},
        "Retention beat": {"rich_text": {}},
        "Editor notes": {"rich_text": {}},
        "Complete?": {"checkbox": {}},
        "Shot Notes": {"rich_text": {}},
        "Time of Day": {"select": {}},
        "Location": {"select": {}},
        "Shoot Day": {"date": {}},
    }
    db = notion.databases.create(
        parent={"type": "page_id", "page_id": page_id},
        title=rt("Shot list"),
        is_inline=True,
        initial_data_source={"properties": schema},
    )
    ds_id = db.get("data_sources", [{}])[0].get("id")
    for s in shots:
        row = {
            "Shot name": {"title": rt(_clean(s.get("shot_name")) or "(unnamed shot)")},
            "Duration": {"rich_text": rt(_clean(s.get("duration")))},
            "Prop": {"rich_text": rt(_clean(s.get("prop")))},
            "Graphics / effect": {"rich_text": rt(_clean(s.get("graphics")))},
            "Retention beat": {"rich_text": rt(_clean(s.get("retention")))},
            "Editor notes": {"rich_text": rt(_clean(s.get("editor_notes")))},
        }
        sec = _clean(s.get("section"))
        if sec:
            row["Section"] = {"select": {"name": sec}}
        st = _clean(s.get("shot_type"))
        if st:
            row["Shot type"] = {"select": {"name": st}}
        notion.pages.create(parent={"type": "data_source_id", "data_source_id": ds_id}, properties=row)
    return len(shots)


def cmd_push(args):
    notion = client()
    cfg = load_config()
    with open(args.file, encoding="utf-8") as f:
        videos = parse(f.read())
    if not videos:
        sys.exit("No videos found in that doc (placeholders are skipped). Fill real video pages first.")

    ds_id = cfg.get("data_source_id")
    if not ds_id:
        sys.exit("config.json has no data_source_id — re-run setup.")
    for v in videos:
        props, body = video_to_page(cfg["database_id"], args.batch, v)
        page = notion.pages.create(
            parent={"type": "data_source_id", "data_source_id": ds_id},
            properties=props,
            children=body[:100],
        )
        # Always attach a shot-list database — empty rows are a fillable scaffold.
        n = create_shot_list_db(notion, page["id"], v.get("shots", []))
        print(f"  + {v['title'][:60]}  ->  {page['url']}  ({n} shots)")
    print(f"Pushed {len(videos)} videos into '{args.batch}'.")
    print(f"Database: {cfg.get('url', '')}")


def cmd_migrate(args):
    """Align an existing Batches database with the simple v5 schema.

    Ensures Orientation + Sai notes columns exist. Hook pick and Props moved into
    the page body, so their outside columns are no longer used — delete them by
    hand in Notion (deleting here would drop any data already in them).
    """
    notion = client()
    cfg = load_config()
    ds_id = cfg.get("data_source_id")
    if not ds_id:
        sys.exit("config.json has no data_source_id — re-run setup.")
    notion.data_sources.update(data_source_id=ds_id, properties={
        "Orientation": {"select": {"options": [{"name": n, "color": c} for n, c in ORIENTATION_OPTIONS]}},
        "Sai notes": {"rich_text": {}},
        "Status": {"select": {"options": [{"name": n, "color": c} for n, c in STATUS_OPTIONS]}},
    })
    print("Ensured Orientation + Sai notes columns and refreshed Status options.")
    print("Now delete the unused 'Hook pick' and 'Props' columns by hand (they moved into the page body).")


def cmd_find(args):
    print(json.dumps(load_config(), indent=2))


def main():
    ap = argparse.ArgumentParser(prog="notion-batch")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("setup", help="create the database under a parent page")
    s.add_argument("--parent", required=True, help="Notion parent page URL (shared with the integration)")
    s.add_argument("--title", default="Sai Shorts — Batches")
    s.set_defaults(func=cmd_setup)

    p = sub.add_parser("push", help="push a filled batch doc into the database")
    p.add_argument("file")
    p.add_argument("--batch", required=True, help='e.g. "Batch 4"')
    p.set_defaults(func=cmd_push)

    m = sub.add_parser("migrate", help="add v5 columns (Orientation, Hook pick) to the existing database")
    m.set_defaults(func=cmd_migrate)

    f = sub.add_parser("find", help="print the saved database id/url")
    f.set_defaults(func=cmd_find)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
