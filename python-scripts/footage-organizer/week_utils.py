"""
week_utils.py — single source of truth for the W##_MMM-DD-DD weekly folder scheme.

Week 1 = the ISO week containing 2026-04-15 (Sai project Day 1, a Wednesday).
Monday of W01 = 2026-04-13. W01 partial-week label uses Apr 15 (project start),
so W01 displays as "W01_Apr-15-19" rather than "W01_Apr-13-19".

All other weeks use Mon-Sun ISO bounds.
"""
from datetime import date, timedelta

PROJECT_START = date(2026, 4, 15)
PROJECT_W01_MONDAY = date(2026, 4, 13)

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def week_label_for(d: date) -> str:
    """Return 'W##_MMM-DD-DD' for the ISO week containing d.
    For W01 the label uses Apr 15 (project start) instead of the Monday Apr 13."""
    monday = _monday_of(d)
    sunday = monday + timedelta(days=6)
    week_num = ((monday - PROJECT_W01_MONDAY).days // 7) + 1
    if week_num < 1:
        raise ValueError(f"Date {d} is before project start {PROJECT_START}")

    start = PROJECT_START if week_num == 1 else monday
    start_mon = MONTH_ABBR[start.month - 1]
    sun_mon = MONTH_ABBR[sunday.month - 1]

    if start.month == sunday.month:
        return f"W{week_num:02d}_{start_mon}-{start.day}-{sunday.day}"
    return f"W{week_num:02d}_{start_mon}-{start.day}-{sun_mon}-{sunday.day}"


def current_week_label() -> str:
    return week_label_for(date.today())
