"""
meta_scraper.py — Scrapes Instagram + Facebook analytics using Playwright.
Replaces meta_fetcher.py — no Meta API tokens required.

Required .env vars:
  META_EMAIL     — Facebook/Instagram login email
  META_PASSWORD  — password
  IG_USERNAME    — Instagram username (e.g. graydientmedia)
  FB_PAGE_SLUG   — Facebook Page URL slug (e.g. graydientmedia)

Install deps first:
  pip install playwright
  playwright install chromium
"""
import os
import re
import time
import random
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

load_dotenv()

EMAIL    = os.getenv('META_EMAIL', '').strip()
PASSWORD = os.getenv('META_PASSWORD', '').strip()
IG_USER  = os.getenv('IG_USERNAME', '').strip()
FB_PAGE  = os.getenv('FB_PAGE_SLUG', '').strip()

# Set SCRAPER_HEADLESS=false in .env to watch the browser (useful for debugging)
HEADLESS  = os.getenv('SCRAPER_HEADLESS', 'true').lower() == 'true'
MAX_POSTS = int(os.getenv('SCRAPER_MAX_POSTS', '50'))

# Session files — saved after first login so future runs skip login entirely
_DIR = os.path.dirname(os.path.abspath(__file__))
IG_SESSION = os.path.join(_DIR, 'ig_session.json')
FB_SESSION = os.path.join(_DIR, 'fb_session.json')


def _sleep(lo=1.0, hi=2.5):
    """Random delay to avoid looking like a bot."""
    time.sleep(random.uniform(lo, hi))


def _parse_count(text):
    """Convert '1.2K', '10,234', '1M' → integer."""
    if not text:
        return 0
    text = text.strip().replace(',', '').replace(' ', '')
    multiplier = 1
    if text.upper().endswith('K'):
        multiplier = 1_000
        text = text[:-1]
    elif text.upper().endswith('M'):
        multiplier = 1_000_000
        text = text[:-1]
    try:
        return int(float(text) * multiplier)
    except (ValueError, TypeError):
        return 0


# ─── Instagram ────────────────────────────────────────────────────────────────

def _login_instagram(page):
    """Log into Instagram. Returns True on success."""
    print("    Navigating to Instagram...")
    page.goto('https://www.instagram.com/', timeout=30000)
    _sleep(2, 3)

    # Dismiss cookie / consent dialogs
    for btn_text in ['Allow all cookies', 'Accept all', 'Allow essential and optional cookies',
                     'Only allow essential cookies', 'Decline optional cookies']:
        try:
            page.click(f'button:has-text("{btn_text}")', timeout=3000)
            _sleep(1, 2)
            break
        except PlaywrightTimeout:
            pass

    # Navigate to the login page if we're not already there
    if 'accounts/login' not in page.url:
        page.goto('https://www.instagram.com/accounts/login/', timeout=30000)
        _sleep(2, 3)
        # Dismiss cookie dialogs
        for btn_text in ['Allow all cookies', 'Accept all']:
            try:
                page.click(f'button:has-text("{btn_text}")', timeout=3000)
                _sleep(1, 2)
                break
            except PlaywrightTimeout:
                pass

    # Wait for the username/email field
    try:
        page.wait_for_selector('input[name="email"], input[name="username"]', timeout=15000)
    except PlaywrightTimeout:
        print(f"    Could not find login form. URL: {page.url}")
        return False

    # Fill login form — Instagram uses name="email" for the username field on web
    email_sel = 'input[name="email"]' if page.query_selector('input[name="email"]') else 'input[name="username"]'
    pass_sel  = 'input[name="pass"]'  if page.query_selector('input[name="pass"]')  else 'input[name="password"]'

    page.fill(email_sel, EMAIL)
    _sleep(0.5, 1)
    page.fill(pass_sel, PASSWORD)
    _sleep(0.5, 1)
    # Submit by pressing Enter (works even when the button isn't visible)
    page.press(pass_sel, 'Enter')

    # Wait for login to complete
    try:
        page.wait_for_load_state('networkidle', timeout=20000)
    except PlaywrightTimeout:
        pass
    _sleep(2, 4)

    # Dismiss "Save login info?" dialog
    for btn_text in ['Not now', 'Not Now', 'Save Info']:
        try:
            page.click(f'button:has-text("{btn_text}")', timeout=4000)
            _sleep()
            break
        except PlaywrightTimeout:
            pass

    # Dismiss "Turn on notifications?" dialog
    try:
        page.click('button:has-text("Not Now")', timeout=4000)
        _sleep()
    except PlaywrightTimeout:
        pass

    logged_in = 'instagram.com' in page.url and 'login' not in page.url
    if logged_in:
        print("    Instagram login successful.")
    else:
        print(f"    Instagram login may have failed. Current URL: {page.url}")
    return logged_in


def get_instagram_data():
    """Scrape recent posts for IG_USERNAME. Returns list of post dicts."""
    if not EMAIL or not PASSWORD:
        print("  Skipping Instagram — META_EMAIL / META_PASSWORD not set in .env")
        return []
    if not IG_USER:
        print("  Skipping Instagram — IG_USERNAME not set in .env")
        return []

    posts = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)

        # Load saved session if it exists — skips login entirely
        ctx_kwargs = dict(
            viewport={'width': 1280, 'height': 900},
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/122.0.0.0 Safari/537.36'
            )
        )
        if os.path.exists(IG_SESSION):
            ctx_kwargs['storage_state'] = IG_SESSION

        context = browser.new_context(**ctx_kwargs)
        page = context.new_page()

        try:
            # Check if saved session is still valid
            session_valid = False
            if os.path.exists(IG_SESSION):
                print("    Loading saved Instagram session...")
                page.goto('https://www.instagram.com/', wait_until='load', timeout=30000)
                _sleep(2, 3)
                session_valid = 'login' not in page.url and page.query_selector('svg[aria-label="Home"]') is not None
                if session_valid:
                    print("    Session valid — skipping login.")
                else:
                    print("    Session expired — logging in fresh...")

            if not session_valid:
                if not _login_instagram(page):
                    print("  Instagram: login failed — skipping.")
                    return []
                # Save session for future runs
                context.storage_state(path=IG_SESSION)
                print("    Session saved — future runs will skip login.")

            # Go to profile
            print(f"  Loading @{IG_USER} profile...")
            page.goto(f'https://www.instagram.com/{IG_USER}/', wait_until='load', timeout=30000)
            _sleep(2, 3)

            # Scroll to load more posts and collect post links
            post_links = set()
            prev_count = 0
            no_new_scroll = 0

            while len(post_links) < MAX_POSTS and no_new_scroll < 5:
                links = page.query_selector_all('a[href*="/p/"], a[href*="/reel/"]')
                for link in links:
                    href = link.get_attribute('href') or ''
                    if '/p/' in href or '/reel/' in href:
                        clean = href.split('?')[0]
                        if not clean.startswith('http'):
                            clean = 'https://www.instagram.com' + clean
                        post_links.add(clean)

                if len(post_links) == prev_count:
                    no_new_scroll += 1
                else:
                    no_new_scroll = 0
                    prev_count = len(post_links)

                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                _sleep(1.5, 2.5)

            print(f"  Found {len(post_links)} posts — scraping metrics...")

            # Visit each post
            for i, url in enumerate(list(post_links)[:MAX_POSTS]):
                try:
                    page.goto(url, wait_until='load', timeout=30000)
                    _sleep(1, 2)

                    # Dismiss "Sign up / Log in" popup if present
                    try:
                        page.click('svg[aria-label="Close"], button:has-text("Close"), [role="dialog"] button:first-child', timeout=3000)
                        _sleep(0.5)
                    except PlaywrightTimeout:
                        pass

                    # Published date
                    published = ''
                    date_el = page.query_selector('time[datetime]')
                    if date_el:
                        dt_str = date_el.get_attribute('datetime') or ''
                        try:
                            published = datetime.fromisoformat(
                                dt_str.replace('Z', '+00:00')
                            ).strftime('%Y-%m-%d')
                        except Exception:
                            published = dt_str[:10]

                    # Get all page text for extraction
                    body_text = page.inner_text('body')

                    # Caption → title
                    # When logged in as owner, Instagram shows: username → relative_time → caption
                    # Pattern: a line matching "Xw", "Xd", "Xh", "Xm" followed by the caption
                    title = ''
                    time_caption = re.search(r'\b\d+[wdhm]\b\n(.{5,})', body_text)
                    if time_caption:
                        title = time_caption.group(1).split('\n')[0][:80].strip()
                    if not title:
                        title = f"Post {published or i+1}"

                    # Likes — when logged in as owner, Instagram shows:
                    # "Boost reel\n{count}\n{Month Day}"  — no "likes" label
                    likes = 0
                    boost_match = re.search(r'Boost (?:reel|post)\n([\d,]+(?:\.\d+)?[KMk]?)\n', body_text)
                    if boost_match:
                        likes = _parse_count(boost_match.group(1))
                    else:
                        # Fallback: labeled like count
                        like_match = re.search(r'([\d,]+(?:\.\d+)?[KMk]?)\s+likes?', body_text, re.IGNORECASE)
                        if like_match:
                            likes = _parse_count(like_match.group(1))

                    # Views (reels/videos) — labeled "X views" or "X plays"
                    views = 0
                    view_match = re.search(r'([\d,]+(?:\.\d+)?[KMk]?)\s+(?:views?|plays?)', body_text, re.IGNORECASE)
                    if view_match:
                        views = _parse_count(view_match.group(1))

                    posts.append({
                        'platform':              'Instagram',
                        'title':                 title,
                        'url':                   url,
                        'published_date':        published,
                        'duration':              '',
                        'views':                 views or likes,
                        'likes':                 likes,
                        'comments':              0,
                        'shares':                0,
                        'impressions':           0,
                        'ctr_pct':               0.0,
                        'watch_time_minutes':    0.0,
                        'avg_view_duration_sec': 0,
                        'avg_view_pct':          0.0,
                        'subscribers_gained':    0,
                    })

                    if (i + 1) % 10 == 0:
                        print(f"    Instagram: scraped {i + 1} posts...")

                except Exception as e:
                    print(f"    Warning: skipped {url} — {e}")
                    continue

        except Exception as e:
            print(f"  Instagram scraper error: {e}")
        finally:
            browser.close()

    print(f"  Instagram: {len(posts)} posts scraped.")
    return posts


# ─── Facebook ─────────────────────────────────────────────────────────────────

def get_facebook_data():
    """Scrape recent posts from the Facebook Page. Returns list of post dicts."""
    if not EMAIL or not PASSWORD:
        print("  Skipping Facebook — META_EMAIL / META_PASSWORD not set in .env")
        return []
    if not FB_PAGE:
        print("  Skipping Facebook — FB_PAGE_SLUG not set in .env")
        return []

    posts = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)

        # Load saved session if it exists — skips login entirely
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
        page = context.new_page()

        try:
            # Check if saved session is still valid
            session_valid = False
            if os.path.exists(FB_SESSION):
                print("    Loading saved Facebook session...")
                page.goto('https://www.facebook.com/', wait_until='load', timeout=30000)
                _sleep(2, 3)
                session_valid = 'login' not in page.url and page.query_selector('[aria-label="Facebook"]') is not None
                if session_valid:
                    print("    Session valid — skipping login.")
                else:
                    print("    Session expired — logging in fresh...")

            if not session_valid:
                print("    Navigating to Facebook login...")
                page.goto('https://www.facebook.com/login', wait_until='load', timeout=30000)
                _sleep(1, 2)

                # Accept cookies
                for sel in ['button[data-cookiebanner="accept_button"]', 'button:has-text("Allow all cookies")',
                            'button:has-text("Accept all")']:
                    try:
                        page.click(sel, timeout=3000)
                        _sleep()
                        break
                    except PlaywrightTimeout:
                        pass

                # Wait for the email field to appear
                page.wait_for_selector('input[name="email"], input[id="email"]', timeout=15000)
                page.fill('input[name="email"]', EMAIL)
                _sleep(0.5, 1)
                page.fill('input[name="pass"]', PASSWORD)
                _sleep(0.5, 1)
                page.press('input[name="pass"]', 'Enter')
                page.wait_for_load_state('load', timeout=20000)
                _sleep(2, 4)
                print("    Facebook login complete.")
                # Save session for future runs
                context.storage_state(path=FB_SESSION)
                print("    Session saved — future runs will skip login.")

            # Navigate to the page (FB_PAGE_SLUG can be a slug OR a full URL)
            fb_url = FB_PAGE if FB_PAGE.startswith('http') else f'https://www.facebook.com/{FB_PAGE}'
            print(f"  Loading Facebook page: {fb_url}...")
            page.goto(fb_url, wait_until='load', timeout=30000)
            _sleep(2, 3)

            # Scroll to load posts
            for _ in range(6):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                _sleep(2, 3)

            # Grab all post article elements
            post_els = page.query_selector_all('div[role="article"]')
            print(f"  Found {len(post_els)} post elements — parsing...")

            for el in post_els[:MAX_POSTS]:
                try:
                    # Post URL
                    url = ''
                    for link_sel in ['a[href*="/posts/"]', 'a[href*="story_fbid"]', 'a[href*="/videos/"]']:
                        link_el = el.query_selector(link_sel)
                        if link_el:
                            url = link_el.get_attribute('href') or ''
                            if url and not url.startswith('http'):
                                url = 'https://www.facebook.com' + url
                            break

                    # Published date — try multiple Facebook timestamp formats
                    published = ''
                    # Modern FB: abbr with title like "Wednesday, March 5, 2025 at 3:00 PM"
                    for ts_sel in ['abbr[title]', 'abbr[data-utime]']:
                        ts_el = el.query_selector(ts_sel)
                        if ts_el:
                            if ts_sel == 'abbr[data-utime]':
                                ts = ts_el.get_attribute('data-utime')
                                if ts:
                                    try:
                                        published = datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d')
                                    except Exception:
                                        pass
                            else:
                                title_attr = ts_el.get_attribute('title') or ''
                                try:
                                    from dateutil import parser as dateparser
                                    published = dateparser.parse(title_attr).strftime('%Y-%m-%d')
                                except Exception:
                                    # Fallback: extract date pattern from title
                                    m = re.search(r'(\w+ \d+, \d{4})', title_attr)
                                    if m:
                                        try:
                                            published = datetime.strptime(m.group(1), '%B %d, %Y').strftime('%Y-%m-%d')
                                        except Exception:
                                            pass
                            if published:
                                break
                    # Last resort: look for date-like text in post body
                    if not published:
                        body_text_el = el.inner_text()
                        date_match = re.search(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}', body_text_el)
                        if date_match:
                            try:
                                published = datetime.strptime(date_match.group(0).replace(',', ''), '%B %d %Y').strftime('%Y-%m-%d')
                            except Exception:
                                pass

                    # Caption → title
                    title = ''
                    for cap_sel in ['div[data-ad-comet-preview="message"] span',
                                    'div[dir="auto"] span', 'div[data-testid="post_message"] span']:
                        cap_el = el.query_selector(cap_sel)
                        if cap_el:
                            title = cap_el.inner_text()[:80].replace('\n', ' ').strip()
                            if title:
                                break
                    if not title:
                        title = f"Post {published or 'unknown'}"

                    # Reactions (likes equivalent) — try reading text from reaction count
                    likes = 0
                    body_text = el.inner_text()
                    react_match = re.search(r'([\d,]+(?:\.\d+)?[KMk]?)\s*(?:reaction|like|people reacted)', body_text, re.IGNORECASE)
                    if react_match:
                        likes = _parse_count(react_match.group(1))

                    # Comments
                    comments = 0
                    comment_match = re.search(r'([\d,]+(?:\.\d+)?[KMk]?)\s*comment', body_text, re.IGNORECASE)
                    if comment_match:
                        comments = _parse_count(comment_match.group(1))

                    # Shares
                    shares = 0
                    share_match = re.search(r'([\d,]+(?:\.\d+)?[KMk]?)\s*share', body_text, re.IGNORECASE)
                    if share_match:
                        shares = _parse_count(share_match.group(1))

                    # Skip empty/ad posts with no URL
                    if not url and not title:
                        continue

                    posts.append({
                        'platform':              'Facebook',
                        'title':                 title,
                        'url':                   url,
                        'published_date':        published,
                        'duration':              '',
                        'views':                 likes,
                        'likes':                 likes,
                        'comments':              comments,
                        'shares':                shares,
                        'impressions':           0,
                        'ctr_pct':               0.0,
                        'watch_time_minutes':    0.0,
                        'avg_view_duration_sec': 0,
                        'avg_view_pct':          0.0,
                        'subscribers_gained':    0,
                    })

                except Exception as e:
                    print(f"    Warning: skipped a Facebook post — {e}")
                    continue

        except Exception as e:
            print(f"  Facebook scraper error: {e}")
        finally:
            browser.close()

    print(f"  Facebook: {len(posts)} posts scraped.")
    return posts
