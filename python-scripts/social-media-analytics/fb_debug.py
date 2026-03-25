"""
fb_debug.py — dumps all links on the Facebook Page /posts tab.
Uses your saved fb_session.json (run fb_setup.py first if needed).
Run: python3 fb_debug.py
"""
import os, time, random
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
FB_PAGE    = os.getenv('FB_PAGE_SLUG', '').strip()
_DIR       = os.path.dirname(os.path.abspath(__file__))
FB_SESSION = os.path.join(_DIR, 'fb_session.json')

def _sleep(lo=1.0, hi=2.5):
    time.sleep(random.uniform(lo, hi))

if not os.path.exists(FB_SESSION):
    print("No fb_session.json found — run python3 fb_setup.py first.")
    exit(1)

fb_base = FB_PAGE if FB_PAGE.startswith('http') else f'https://www.facebook.com/{FB_PAGE}'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        storage_state=FB_SESSION,
        viewport={'width': 1280, 'height': 900},
        user_agent=(
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/122.0.0.0 Safari/537.36'
        )
    )
    page = context.new_page()

    print(f"Loading {fb_base} ...")
    try:
        page.goto(fb_base, wait_until='domcontentloaded', timeout=30000)
    except Exception:
        pass
    _sleep(3, 4)

    print(f"Current URL: {page.url}")

    # Scroll to load more posts
    for i in range(6):
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        _sleep(2, 3)
        print(f"  Scrolled {i+1}/6...")

    # Dump ALL unique hrefs on the page
    all_links = page.evaluate("""
        () => {
            const links = document.querySelectorAll('a[href]');
            const hrefs = new Set();
            links.forEach(a => hrefs.add(a.href));
            return Array.from(hrefs);
        }
    """)

    print(f"\n--- All unique Facebook links on page ({len(all_links)} total) ---")
    fb_links = [h for h in all_links if 'facebook.com' in h]
    for href in sorted(fb_links):
        print(f"  {href}")

    input("\nPress Enter to close browser...")
    browser.close()
