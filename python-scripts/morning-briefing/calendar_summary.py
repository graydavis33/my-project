"""
calendar_summary.py
Fetches today's events from Google Calendar primary calendar.
"""

from datetime import datetime, timezone, timedelta
from google_auth import get_google_service


def get_todays_events():
    """
    Return a list of today's calendar events sorted by start time.
    Each item: {title, time}
    Returns empty list on error or no events.
    """
    try:
        service = get_google_service("calendar", "v3")

        # Today's window in UTC
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        end = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

        result = service.events().list(
            calendarId="primary",
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = []
        for item in result.get("items", []):
            start_val = item["start"].get("dateTime", item["start"].get("date", ""))
            if "T" in start_val:
                dt = datetime.fromisoformat(start_val)
                time_str = dt.strftime("%-I:%M %p")
            else:
                time_str = "All day"
            events.append({
                "title": item.get("summary", "Untitled"),
                "time": time_str,
            })

        return events

    except Exception:
        return []
