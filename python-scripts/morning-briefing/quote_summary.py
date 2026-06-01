"""
quote_summary.py
Fetches a random inspirational quote from ZenQuotes API (free, no key needed).
"""

import json
import urllib.request

_URL = "https://zenquotes.io/api/random"


def get_daily_quote():
    """
    Return dict with quote text and author.
    Returns None on error.
    """
    try:
        with urllib.request.urlopen(_URL, timeout=5) as resp:
            data = json.loads(resp.read())
        return {
            "quote": data[0]["q"],
            "author": data[0]["a"],
        }
    except Exception:
        return None
