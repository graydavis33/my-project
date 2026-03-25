"""
fb_debug.py — dumps Facebook Page HTML structure to figure out what selectors to use.
Run: python3 fb_debug.py
"""
import os, json, time, random
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

load_dotenv()
EMAIL    = os.getenv('META_EMAIL', '').strip()
PASSWORD = os.getenv('META_PASSWORD', '').strip()
FB_PAGE  = os.getenv('FB_PAGE_SLUG', '').strip()
_DIR     = os.path.dirname(os.path.abspath(__file__))
FB_SESSION = os.path.join(_DIR, 'fb_session.json')

def _sleep(lo=1.0, hi=2.5):
    time.sleep(random.uniform(lo, hi))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # visible so you can see what's happening
    ctx_kwargs = dict(
        viewport={'width': 1280, 'height': 900},
        user_agent=(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/122.0.0.0 Safari/537.36'
        )
    )
    if os.path.exists(FB_SESSION):
        ctx_kwargs['storage_state'] = FB_SESSION

    context = browser.new_context(**ctx_kwargs)
    page    = context.new_page()

    # Load page
    fb_url = FB_PAGE if FB_PAGE.startswith('http') else f'https://www.facebook.com/{FB_PAGE}'
    print(f"Navigating to {fb_url} ...")
    try:
        page.goto(fb_url, wait_until='domcontentloaded', timeout=30000)
    except Exception as e:
        print(f"  Nav warning (usually fine): {e}")

    _sleep(3, 4)
    # Try /posts tab
    posts_url = fb_url.rstrip('/') + '/posts'
    print(f"Navigating to {posts_url} ...")
    try:
        page.goto(posts_url, wait_until='domcontentloaded', timeout=30000)
    except Exception as e:
        print(f"  Nav warning: {e}")
    _sleep(3, 4)

    # Scroll to trigger lazy load
    for i in range(4):
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        _sleep(2, 3)

    print(f"\nCurrent URL: {page.url}")
    print(f"Page title: {page.title()}")

    # Test various selectors
    selectors_to_test = [
        'div[role="article"]',
        'div[role="feed"]',
        'div[data-pagelet*="FeedUnit"]',
        'div[data-pagelet*="TimelinePost"]',
        'div[data-ad-preview="message"]',
        'div[data-ad-comet-preview="message"]',
        'a[href*="/posts/"]',
        'a[href*="story_fbid"]',
        '[data-testid="post_message"]',
        'div.x1yztbdb',
    ]
    print("\n--- Selector counts ---")
    for sel in selectors_to_test:
        try:
            els = page.query_selector_all(sel)
            print(f"  {sel!r:55s} → {len(els)}")
        except Exception as e:
            print(f"  {sel!r:55s} → ERROR: {e}")

    # Dump all unique role values on the page
    roles = page.evaluate("""
        () => {
            const els = document.querySelectorAll('[role]');
            const counts = {};
            els.forEach(e => { counts[e.getAttribute('role')] = (counts[e.getAttribute('role')]||0)+1; });
            return counts;
        }
    """)
    print("\n--- All [role] values on page ---")
    for role, count in sorted(roles.items(), key=lambda x: -x[1]):
        print(f"  role={role!r}: {count}")

    # Dump unique data-pagelet values
    pagelets = page.evaluate("""
        () => {
            const els = document.querySelectorAll('[data-pagelet]');
            const counts = {};
            els.forEach(e => { counts[e.getAttribute('data-pagelet')] = (counts[e.getAttribute('data-pagelet')]||0)+1; });
            return counts;
        }
    """)
    print("\n--- All [data-pagelet] values on page ---")
    for plet, count in sorted(pagelets.items(), key=lambda x: -x[1]):
        print(f"  data-pagelet={plet!r}: {count}")

    input("\nPress Enter to close browser...")
    browser.close()
