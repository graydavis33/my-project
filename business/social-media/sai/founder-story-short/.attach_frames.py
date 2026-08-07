"""Attach approved reference frames to the REAL founder-story shot list (karramedia workspace).

Usage:
    NOTION_KARRAMEDIA_TOKEN=... python .attach_frames.py [--dry-run]

Additive only: fetches each row's current Frame Visual files, re-sends every existing
entry unchanged, and appends the new uploads. Never removes anything (see
feedback-surgical-edits-only). Aborts per-row if the row can't be found by Shot #.

Approved 2026-08-07 (Gray): shot 2 = v7 TIGHT sequence (3), shot 3 = v4 soft-blue series (3),
shot 4 = v4 real-room frame (1).
"""
import json
import os
import sys
import time
import urllib.request

TOKEN = os.environ.get("NOTION_KARRAMEDIA_TOKEN")
DATA_SOURCE = "d589d846-464f-4822-bd38-b50c7d3aa99b"  # REAL DB — never the 3cddfd3e duplicate
NOTION_VERSION = "2025-09-03"
DRY = "--dry-run" in sys.argv

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(HERE, "reference-frames")

# shot number -> approved files, in display order
ATTACH = {
    2: [
        "shot2-v7-still1-relit-TIGHT-PENDING.png",
        "shot2-v7-still2-relit-TIGHT-PENDING.png",
        "shot2-v7-endstate-relit-TIGHT-PENDING.png",
    ],
    3: [
        "shot3-v4-A-medium-softblue-PENDING.png",
        "shot3-v4-B-fullboard-softblue-PENDING.png",
        "shot3-v4-C-wide-softblue-PENDING.png",
    ],
    4: [
        "shot4-bed-scroll-v4-realroom-PENDING.png",
    ],
}


def api(path, payload=None, method=None, raw_body=None, content_type="application/json"):
    url = f"https://api.notion.com/v1/{path}"
    body = raw_body if raw_body is not None else (json.dumps(payload).encode() if payload is not None else None)
    req = urllib.request.Request(url, data=body, method=method or ("POST" if body else "GET"))
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Notion-Version", NOTION_VERSION)
    if body is not None:
        req.add_header("Content-Type", content_type)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def upload_file(path):
    """Notion File Upload API: create upload slot, send bytes, return file_upload id."""
    name = os.path.basename(path)
    slot = api("file_uploads", {"filename": name, "content_type": "image/png"})
    upload_id = slot["id"]
    boundary = "----attachframes"
    with open(path, "rb") as f:
        data = f.read()
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    api(f"file_uploads/{upload_id}/send", raw_body=body,
        content_type=f"multipart/form-data; boundary={boundary}")
    return upload_id


def find_row(shot_no):
    res = api(f"data_sources/{DATA_SOURCE}/query", {
        "filter": {"property": "Shot #", "number": {"equals": shot_no}}})
    rows = res.get("results", [])
    if len(rows) != 1:
        raise SystemExit(f"shot {shot_no}: expected 1 row, got {len(rows)} — aborting")
    return rows[0]


def resend_entry(f):
    """Re-encode an existing files entry so the update doesn't wipe it."""
    if f["type"] == "external":
        return {"name": f["name"], "type": "external", "external": {"url": f["external"]["url"]}}
    # notion-hosted files re-send as file with url
    return {"name": f["name"], "type": "file", "file": {"url": f["file"]["url"],
            "expiry_time": f["file"].get("expiry_time")}}


def main():
    if not TOKEN:
        raise SystemExit("NOTION_KARRAMEDIA_TOKEN not set")
    who = api("users/me")
    print("authed as:", who.get("name"), "-", who.get("bot", {}).get("workspace_name", "?"))
    for shot_no, files in ATTACH.items():
        row = find_row(shot_no)
        existing = row["properties"]["Frame Visual"]["files"]
        print(f"shot {shot_no}: {len(existing)} existing attachments, adding {len(files)}")
        if DRY:
            continue
        new_entries = []
        for fn in files:
            p = os.path.join(FRAMES, fn)
            uid = upload_file(p)
            new_entries.append({"name": fn, "type": "file_upload", "file_upload": {"id": uid}})
            time.sleep(0.4)
        payload = {"properties": {"Frame Visual": {
            "files": [resend_entry(f) for f in existing] + new_entries}}}
        api(f"pages/{row['id']}", payload, method="PATCH")
        print(f"shot {shot_no}: attached {len(new_entries)} — verify in Notion")


if __name__ == "__main__":
    main()
