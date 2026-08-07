"""Create a dedicated 'Founder Story Short' calendar on gray@karramedia.com
and populate it with the shoot schedule.

Standalone on purpose: calendar-blocker/config.json holds ONE calendar id
(the daily Work calendar). Repointing it would break /prime's day blocks.
Does NOT share the calendar - Gray shares it with Sai himself.
"""
import sys

sys.path.insert(0, r"c:/Users/Gray Davis/my-project/python-scripts/calendar-blocker")
import gcal

TZ = "America/New_York"
CAL_NAME = "Founder Story Short — Shoot"

svc = gcal.get_service()

# Reuse if it already exists, so re-running never duplicates the calendar.
cal_id = None
page = None
while True:
    lst = svc.calendarList().list(pageToken=page).execute()
    for c in lst.get("items", []):
        if c.get("summary") == CAL_NAME:
            cal_id = c["id"]
    page = lst.get("nextPageToken")
    if not page:
        break

if cal_id:
    print(f"Reusing existing calendar: {cal_id}")
else:
    created = svc.calendars().insert(body={
        "summary": CAL_NAME,
        "description": "Founder Story Short (Sai) — pre-production, film day, edit, delivery.",
        "timeZone": TZ,
    }).execute()
    cal_id = created["id"]
    print(f"Created calendar: {cal_id}")

# Wipe any events we previously wrote, so re-running is idempotent.
existing = svc.events().list(calendarId=cal_id, maxResults=250).execute().get("items", [])
for e in existing:
    svc.events().delete(calendarId=cal_id, eventId=e["id"]).execute()
if existing:
    print(f"Cleared {len(existing)} existing event(s) before rebuild.")

ALLDAY = [
    # (start, end_exclusive, title, description, colorId)
    ("2026-08-07", "2026-08-08", "🔧 Rig check + prop buys",
     "Confirm whether the key-light rig takes a camera attachment for shot 5's overhead "
     "bird's-eye. LAST SAFE ORDER DAY if a part is needed.\n"
     "Finish the prop run: ~8-12 4x6 prints, 1 roll red yarn, ~25-30 push pins, 3-4 magnets.\n"
     "Reference images continue.", 6),

    ("2026-08-08", "2026-08-09", "📸 DEADLINE — Sai's photos in hand",
     "HARD GATE on the film day.\n"
     "Needed from Sai: archival photos for shots 7/8 (phone, family albums, old drives) "
     "and the team photo for shots 13/14/15.\n"
     "Build a contact sheet, get his yes/no on each pick. Nothing prints without approval.\n"
     "If these do not land today, Tuesday slips.", 11),

    ("2026-08-09", "2026-08-10", "🖨 Prep + print photos",
     "Prep every final to exactly 1200x1800 (4x6 at 300dpi). Upscale anything soft.\n"
     "Order 4x6 MATTE, 2 copies of everything, same-day pickup.\n"
     "EVERY print is 4x6 with no exceptions - shot 8's match cut breaks if sizes differ.\n"
     "Press any curled prints flat overnight.", 6),

    ("2026-08-10", "2026-08-11", "📋 Buffer — board build test + pack",
     "Dry-run the board build: full photo set pinned, red yarn strung, nothing crooked.\n"
     "Pack camera, rigs, lights, practicals, spare prints.\n"
     "Close the open script gaps: shot 10 and shot 11 still have no How to Edit.", 6),

    ("2026-08-12", "2026-08-13", "✂️ Edit day 1 — assembly",
     "Ingest, sync, select takes, build the spine in order. No effects yet.\n"
     "9 of 15 shots carry After Effects work - front-load the assembly so VFX has room.", 9),
    ("2026-08-13", "2026-08-14", "✂️ Edit day 2 — VFX pass 1",
     "AE work: shot 1 glitch/RGB split, shot 2 bloom + party overlays, shot 4 wall composite, "
     "shot 5 3D floating photos + light wrap (shot 6 reuses shot 5's rig).", 9),
    ("2026-08-14", "2026-08-15", "✂️ Edit day 3 — VFX pass 2",
     "AE work: shot 8 match-cut stabilize, shot 9 Echo, shot 11 whip transition, "
     "shot 13 freeze-into-motion.", 9),
    ("2026-08-15", "2026-08-16", "✂️ Edit day 4 — grade, sound, captions",
     "Colour, music, SFX, captions. Shot 15's final push settles, music lands its last note, "
     "then a breath of silence.", 9),

    ("2026-08-16", "2026-08-17", "👀 Buffer + final review",
     "Watch it cold, top to bottom. Fix pass. Sai's review if he wants one.\n"
     "This day exists so Monday is not a scramble.", 6),

    ("2026-08-17", "2026-08-18", "🚀 POST — Founder Story Short",
     "Deliver and post. Target set 2026-08-06.", 6),
]

FILM_DAY = "2026-08-11"
TIMED = [
    ("09:00", "10:30", "🎬 Load in + BUILD THE BOARD",
     "Pin the complete photo set, string the red yarn between push pins, check every photo is "
     "straight and the tension is even.\n"
     "The board is on screen longest in shot 12 and every earlier shot is a close-up, so it has "
     "to be complete and tidy before a single frame is shot.", 11),
    ("10:30", "13:00", "🎬 Board — wides + OTS (shots 12, 10, 9, 7)",
     "Shot 12 is the payoff: FIRST time the full board is seen, over-the-shoulder past Sai, "
     "whole board visible. A person must be in frame - a flat board-only plate is the wrong shot.\n"
     "Light the whole board EVENLY for 12 (everything before was pools of light).\n"
     "Shots 9/10 are the board-POV from behind. Shot 7 is the pinning and connecting.\n"
     "Tripod.", 11),
    ("13:00", "13:45", "🍽 Lunch", "", 5),
    ("13:45", "16:30", "🎬 Board — macro passes (shots 2, 3, 8, 13, 15)",
     "Relight tighter: lamp in close on the hero photos, 3200K.\n"
     "Shot 2 = the first photo going up (macro, magnet). Shot 3 = close-up on the pinned photo.\n"
     "Shot 8 = the match-cut series - EVERY print must be the same 4x6 or the cuts break.\n"
     "Shot 13 = macro slider across the faces, following the red strings; hold steady and "
     "constant-speed across the 1-2 hero photos for the come-alive moment.\n"
     "Shot 15 = FINAL IMAGE. Two takes, one static and one with a barely perceptible push. "
     "Lock focus on the faces, no hunting. Matte print, no glare. Hold 2s after the move settles.", 11),
    ("16:30", "17:30", "🎬 Shot 14 + pickups",
     "Laptop video-call b-roll, over-shoulder with the screen visible. In-person handshake if "
     "anyone is around. Plain and warm, no effects by design.\n"
     "Then sweep the shot list for anything missed while the board is still up.", 11),
    ("17:30", "18:30", "💡 Relight + blackout for the bedroom setup",
     "Full turnaround. Blackout the room, set the red practical.", 11),
    ("18:30", "21:00", "🎬 Bedroom — dark (shots 4, 5, 6)",
     "Scheduled after dark on purpose so the blackout does the work instead of fighting daylight.\n"
     "Shot 4 = Sai at the end of the bed in the dark. Shot 5 = falls back, needs the OVERHEAD "
     "bird's-eye rig. Shot 6 = photos and videos appear above him (reuses shot 5's rig).\n"
     "Shot 5's overhead is the one rig question outstanding - confirm Friday.", 11),
    ("21:00", "21:30", "✅ Checks + wrap",
     "Playback every setup before striking anything. Confirm the shot list is fully covered - "
     "this is a one-day shoot and there is no second board build.", 11),
]


def add_allday(start, end, title, desc, color):
    svc.events().insert(calendarId=cal_id, body={
        "summary": title, "description": desc,
        "start": {"date": start}, "end": {"date": end},
        "colorId": str(color),
    }).execute()
    print(f"  {start}  ALL DAY  {title}")


def add_timed(date, s, e, title, desc, color):
    svc.events().insert(calendarId=cal_id, body={
        "summary": title, "description": desc,
        "start": {"dateTime": f"{date}T{s}:00", "timeZone": TZ},
        "end": {"dateTime": f"{date}T{e}:00", "timeZone": TZ},
        "colorId": str(color),
    }).execute()
    print(f"  {date}  {s}-{e}  {title}")


print("\n--- events ---")
for a in ALLDAY:
    add_allday(*a)

add_allday("2026-08-11", "2026-08-12", "🎬 FILM DAY — Founder Story Short (all shots)",
           "One-day shoot. 15 shots on the list; shot 1 is fully AI-generated and shot 11 is "
           "archival b-roll, so ~13 get filmed.\n"
           "Two setups: the board (day) and the bedroom (after dark).\n"
           "OPEN: the team photo for shots 13/14/15 does not exist yet.", 11)

for t in TIMED:
    add_timed(FILM_DAY, *t)

print(f"\nCalendar: {CAL_NAME}")
print(f"id: {cal_id}")
print("NOT shared - share it with Sai from Google Calendar settings.")
