"""
fb_setup.py — Manual Facebook login to save a session for the scraper.

Run this once whenever the Facebook session expires:
    python3 fb_setup.py

It opens a real browser window. You log in manually like normal.
When you're done, press Enter in the terminal and it saves the session.
"""
import os
from playwright.sync_api import sync_playwright

_DIR       = os.path.dirname(os.path.abspath(__file__))
FB_SESSION = os.path.join(_DIR, 'fb_session.json')

print("=" * 55)
print("  Facebook Session Setup")
print("=" * 55)
print()
print("A browser window will open. Log into Facebook normally.")
print("Once you're fully logged in and can see your feed,")
print("come back here and press Enter.")
print()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        viewport={'width': 1280, 'height': 900},
        user_agent=(
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/122.0.0.0 Safari/537.36'
        )
    )
    page = context.new_page()
    page.goto('https://www.facebook.com/login', wait_until='load', timeout=30000)

    input("Press Enter once you are fully logged into Facebook... ")

    # Save the session
    context.storage_state(path=FB_SESSION)
    print(f"\nSession saved to: {FB_SESSION}")
    print("The scraper will use this session automatically.")
    print("Re-run this script if Facebook starts failing again.")

    browser.close()
