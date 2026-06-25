#!/usr/bin/env python3
"""
Calendar Blocker — Gray's work-schedule tool.

Creates/updates time blocks on a dedicated Google "Work" calendar so Sai can see
what Gray is working on. Reuses the Google login already set up for the calendar
MCP (~/.calendar-mcp/), so no extra sign-in is needed.

Commands:
  python gcal.py setup        Find or create the "Work" calendar (saves its id)
  python gcal.py share EMAIL  Share the Work calendar with someone (e.g. Sai)
  python gcal.py block FILE   Create blocks for a day from a JSON file
  python gcal.py list DATE    List the Work calendar's events for YYYY-MM-DD
  python gcal.py clear DATE   Delete all Work-calendar events on YYYY-MM-DD
                              (use before re-blocking a day — keeps things fluid)

Block JSON file format:
  {
    "date": "2026-06-26",
    "blocks": [
      {"start": "08:00", "end": "08:30", "title": "Plan & Prime", "desc": "optional"},
      ...
    ]
  }
"""
import json
import os
import sys
import datetime as dt
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

HOME = Path.home()
TOKEN_PATH = HOME / ".calendar-mcp" / "credentials.json"          # MCP-saved OAuth token
KEYS_PATH = HOME / ".calendar-mcp" / "gcp-oauth.keys.json"        # OAuth app (client id/secret)
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"    # our saved calendar id + tz
SCOPES = ["https://www.googleapis.com/auth/calendar"]
WORK_CAL_NAME = "Work — Gray (Schedule)"


def detect_timezone():
    """Best-effort IANA timezone from the Mac system clock."""
    try:
        link = os.readlink("/etc/localtime")  # e.g. .../zoneinfo/America/New_York
        if "zoneinfo/" in link:
            return link.split("zoneinfo/")[-1]
    except OSError:
        pass
    return "America/New_York"


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {}


def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def get_service():
    """Build an authenticated Calendar API client, refreshing the token if needed."""
    tok = json.loads(TOKEN_PATH.read_text())
    keys_raw = json.loads(KEYS_PATH.read_text())
    keys = keys_raw.get("installed") or keys_raw.get("web")

    creds = Credentials(
        token=tok.get("access_token"),
        refresh_token=tok.get("refresh_token"),
        token_uri=keys.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=keys.get("client_id"),
        client_secret=keys.get("client_secret"),
        scopes=SCOPES,
    )
    # Always refresh so we never hit an expired access token, then write it back
    # so the MCP server stays in sync with the same fresh token.
    creds.refresh(Request())
    tok["access_token"] = creds.token
    if creds.expiry:
        # MCP stores expiry as epoch milliseconds
        tok["expiry_date"] = int(creds.expiry.replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
    TOKEN_PATH.write_text(json.dumps(tok))
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def api_error_help(e: HttpError):
    msg = str(e)
    if "has not been used in project" in msg or "accessNotConfigured" in msg or "API has not been used" in msg:
        print("\n⚠️  The Google Calendar API isn't switched on for your project yet.")
        print("    Fix (one click): open this link, click ENABLE, wait ~1 min, then re-run:")
        print("    https://console.developers.google.com/apis/api/calendar-json.googleapis.com/overview")
    else:
        print(f"\n⚠️  Calendar API error:\n{msg}")


def cmd_setup():
    svc = get_service()
    cfg = load_config()
    cfg.setdefault("timezone", detect_timezone())

    # Reuse an existing Work calendar if we already made one
    page_token = None
    while True:
        cal_list = svc.calendarList().list(pageToken=page_token).execute()
        for c in cal_list.get("items", []):
            if c.get("summary") == WORK_CAL_NAME:
                cfg["calendar_id"] = c["id"]
                save_config(cfg)
                print(f"Found existing Work calendar.\n  id: {c['id']}\n  timezone: {cfg['timezone']}")
                return
        page_token = cal_list.get("nextPageToken")
        if not page_token:
            break

    created = svc.calendars().insert(body={
        "summary": WORK_CAL_NAME,
        "description": "Gray's daily work time-blocks. Shared so Sai can see what's in progress.",
        "timeZone": cfg["timezone"],
    }).execute()
    cfg["calendar_id"] = created["id"]
    save_config(cfg)
    print(f"Created Work calendar.\n  id: {created['id']}\n  timezone: {cfg['timezone']}")


def cmd_share(email):
    svc = get_service()
    cfg = load_config()
    cal_id = cfg.get("calendar_id")
    if not cal_id:
        print("Run `python gcal.py setup` first.")
        return
    svc.acl().insert(calendarId=cal_id, body={
        "role": "reader",
        "scope": {"type": "user", "value": email},
    }).execute()
    print(f"Shared the Work calendar with {email} (read-only).")


def cmd_block(file_path):
    svc = get_service()
    cfg = load_config()
    cal_id = cfg.get("calendar_id")
    tz = cfg.get("timezone", detect_timezone())
    if not cal_id:
        print("Run `python gcal.py setup` first.")
        return

    data = json.loads(Path(file_path).read_text())
    date = data["date"]
    made = 0
    for b in data["blocks"]:
        start = f"{date}T{b['start']}:00"
        end = f"{date}T{b['end']}:00"
        body = {
            "summary": b["title"],
            "description": b.get("desc", ""),
            "start": {"dateTime": start, "timeZone": tz},
            "end": {"dateTime": end, "timeZone": tz},
        }
        if b.get("color"):
            body["colorId"] = str(b["color"])
        svc.events().insert(calendarId=cal_id, body=body).execute()
        made += 1
        print(f"  ✓ {b['start']}–{b['end']}  {b['title']}")
    print(f"\nDone — {made} blocks added for {date}.")


def cmd_list(date):
    svc = get_service()
    cfg = load_config()
    cal_id = cfg.get("calendar_id")
    if not cal_id:
        print("Run `python gcal.py setup` first.")
        return
    tmin = f"{date}T00:00:00Z"
    tmax = f"{date}T23:59:59Z"
    # widen window a bit for timezone offset safety
    events = svc.events().list(
        calendarId=cal_id, timeMin=f"{date}T00:00:00-12:00",
        timeMax=f"{date}T23:59:59+12:00", singleEvents=True, orderBy="startTime",
    ).execute().get("items", [])
    if not events:
        print(f"No blocks on {date}.")
        return
    for e in events:
        s = e["start"].get("dateTime", e["start"].get("date", ""))[11:16]
        en = e["end"].get("dateTime", e["end"].get("date", ""))[11:16]
        print(f"  {s}–{en}  {e.get('summary','(no title)')}")


def cmd_clear(date):
    svc = get_service()
    cfg = load_config()
    cal_id = cfg.get("calendar_id")
    if not cal_id:
        print("Run `python gcal.py setup` first.")
        return
    events = svc.events().list(
        calendarId=cal_id, timeMin=f"{date}T00:00:00-12:00",
        timeMax=f"{date}T23:59:59+12:00", singleEvents=True,
    ).execute().get("items", [])
    n = 0
    for e in events:
        svc.events().delete(calendarId=cal_id, eventId=e["id"]).execute()
        n += 1
    print(f"Cleared {n} blocks on {date}.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    try:
        if cmd == "setup":
            cmd_setup()
        elif cmd == "share" and len(sys.argv) > 2:
            cmd_share(sys.argv[2])
        elif cmd == "block" and len(sys.argv) > 2:
            cmd_block(sys.argv[2])
        elif cmd == "list" and len(sys.argv) > 2:
            cmd_list(sys.argv[2])
        elif cmd == "clear" and len(sys.argv) > 2:
            cmd_clear(sys.argv[2])
        else:
            print(__doc__)
    except HttpError as e:
        api_error_help(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
