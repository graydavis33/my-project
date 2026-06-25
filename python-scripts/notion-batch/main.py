"""
notion-batch — push Sai shorts batch docs into a Notion database.

Each video becomes its own Notion page in the "Sai Shorts — Batches" database,
with columns (Batch, Status, Format, Props, Assets, Reference, Outlier) and a
rich body (Topics, Verbal/Visual hooks A-B-C, Camera, Graphics, Editor brief).

Commands:
  setup  --parent <page-url>            create the database under a parent page (run once)
  push   <batch.md> --batch "Batch 4"   create a page per video from a filled batch doc
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
    ("Approved", "green"),
    ("Filmed", "blue"),
    ("Sent to Editor", "purple"),
    ("Posted", "pink"),
]


def client():
    token = os.getenv("NOTION_TOKEN")
    if not token:
        sys.exit("NOTION_TOKEN not set. Copy content-researcher/.env's token into notion-batch/.env")
    from notion_client import Client
    # Pin the stable API version: keeps databases single-source (properties live on
    # the database itself, not a separate data_source) — matches this tool's model.
    return Client(auth=token, notion_version="2022-06-28")


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


# ---------- commands ----------

def cmd_setup(args):
    notion = client()
    parent = page_id_from_url(args.parent)
    db = notion.databases.create(
        parent={"type": "page_id", "page_id": parent},
        title=rt(args.title),
        properties={
            "Video": {"title": {}},
            "Batch": {"select": {}},
            "Status": {"select": {"options": [{"name": n, "color": c} for n, c in STATUS_OPTIONS]}},
            "Format": {"rich_text": {}},
            "Props": {"rich_text": {}},
            "Assets": {"url": {}},
            "Reference": {"url": {}},
            "Outlier": {"number": {"format": "number"}},
        },
    )
    url = db.get("url", "")
    save_config({"database_id": db["id"], "url": url})
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
        "Props": {"rich_text": rt(v.get("props", ""))},
    }
    if v.get("assets") and v["assets"].startswith("http"):
        props["Assets"] = {"url": v["assets"]}
    watch = v["reference"].get("watch", "")
    if watch.startswith("http"):
        props["Reference"] = {"url": watch}
    if v.get("outlier") is not None:
        props["Outlier"] = {"number": v["outlier"]}

    body = []
    topics = v.get("topics", "")
    body.append(heading("Topics (Sai to fill)"))
    body.append({"object": "block", "type": "callout",
                 "callout": {"rich_text": rt(topics or "Sai — add the real subjects here."),
                             "icon": {"emoji": "✍️"}, "color": "yellow_background"}})

    for label, key in (("Verbal hook", "verbal"), ("Visual hook", "visual")):
        body.append(heading(label))
        block = v.get(key, {})
        for opt in ("A", "B", "C"):
            val = block.get(opt, "")
            body.append(bullet(f"{opt}: {val}".rstrip(": ")))

    body.append(heading("Camera shots"))
    body.append(para(v.get("camera", "")))
    body.append(heading("Graphics and effects"))
    body.append(para(v.get("graphics", "")))

    body.append(heading("Editor brief"))
    for k, val in v.get("editor", {}).items():
        body.append(bullet(f"{k}: {val}".rstrip(": ")))

    body.append(heading("Reference"))
    if v["reference"].get("label"):
        body.append(para(v["reference"]["label"]))
    links = []
    if v["reference"].get("watch", "").startswith("http"):
        links += link_rt("Watch", v["reference"]["watch"]) + rt("   ")
    if v["reference"].get("original", "").startswith("http"):
        links += link_rt("Original", v["reference"]["original"])
    if links:
        body.append(para_rich(links))

    return props, body


def cmd_push(args):
    notion = client()
    cfg = load_config()
    with open(args.file, encoding="utf-8") as f:
        videos = parse(f.read())
    if not videos:
        sys.exit("No videos found in that doc (placeholders are skipped). Fill real video pages first.")

    for v in videos:
        props, body = video_to_page(cfg["database_id"], args.batch, v)
        page = notion.pages.create(
            parent={"database_id": cfg["database_id"]},
            properties=props,
            children=body[:100],
        )
        print(f"  + {v['title'][:60]}  ->  {page['url']}")
    print(f"Pushed {len(videos)} videos into '{args.batch}'.")
    print(f"Database: {cfg.get('url', '')}")


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

    f = sub.add_parser("find", help="print the saved database id/url")
    f.set_defaults(func=cmd_find)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
