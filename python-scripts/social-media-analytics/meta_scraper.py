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

def _login_facebook(page):
    """Log into Facebook. Returns True on success."""
    print("    Navigating to Facebook login...")
    page.goto('https://www.facebook.com/login', wait_until='load', timeout=30000)
    _sleep(2, 3)

    # Accept cookies if banner appears
    for sel in ['button[data-cookiebanner="accept_button"]', 'button:has-text("Allow all cookies")',
                'button:has-text("Accept all")']:
        try:
            page.click(sel, timeout=3000)
            _sleep()
            break
        except PlaywrightTimeout:
            pass

    try:
        page.wait_for_selector('input[name="email"], input[id="email"]', timeout=15000)
    except PlaywrightTimeout:
        print(f"    Could not find Facebook login form. URL: {page.url}")
        return False

    page.fill('input[name="email"]', EMAIL)
    _sleep(0.8, 1.5)
    page.fill('input[name="pass"]', PASSWORD)
    _sleep(0.8, 1.5)

    # Click the login button (more reliable than pressing Enter)
    submitted = False
    for btn_sel in [
        'button[name="login"]',
        '[data-testid="royal_login_button"]',
        'button[type="submit"]',
    ]:
        try:
            page.click(btn_sel, timeout=5000)
            submitted = True
            break
        except PlaywrightTimeout:
            pass
    if not submitted:
        page.press('input[name="pass"]', 'Enter')

    # Wait for the URL to move away from the login page
    try:
        page.wait_for_url(lambda url: 'login' not in url, timeout=25000)
    except PlaywrightTimeout:
        pass
    _sleep(3, 5)

    logged_in = 'facebook.com' in page.url and 'login' not in page.url
    if logged_in:
        print("    Facebook login complete.")
    else:
        print(f"    Facebook login failed. URL: {page.url}")
    return logged_in


def get_facebook_data():
    """Scrape recent posts from the Facebook Page. Returns list of post dicts."""
    if not EMAIL or not PASSWORD:
        print("  Skipping Facebook — META_EMAIL / META_PASSWORD not set in .env")
        return []
    if not FB_PAGE:
        print("  Skipping Facebook — FB_PAGE_SLUG not set in .env")
        return []

    posts = []
    fb_base = FB_PAGE if FB_PAGE.startswith('http') else f'https://www.facebook.com/{FB_PAGE}'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)

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
                page.goto('https://www.facebook.com/', wait_until='domcontentloaded', timeout=30000)
                _sleep(2, 3)
                # Valid if we're on FB and not on a login page
                session_valid = ('facebook.com' in page.url
                                 and 'login' not in page.url
                                 and page.query_selector('input[placeholder="Search Facebook"], [aria-label="Facebook"]') is not None)
                if session_valid:
                    print("    Session valid — skipping login.")
                else:
                    print("    Session expired — logging in fresh...")
                    # Close the old context and open a fresh one (no stale cookies)
                    browser.close()
                    browser = p.chromium.launch(headless=HEADLESS)
                    context = browser.new_context(**{k: v for k, v in ctx_kwargs.items() if k != 'storage_state'})
                    page = context.new_page()

            if not session_valid:
                if not _login_facebook(page):
                    print("  Facebook: login failed — skipping.")
                    return []
                # Save session so future runs skip login
                context.storage_state(path=FB_SESSION)
                print("    Session saved.")

            # Navigate directly to the /posts tab of the page
            posts_url = fb_base.rstrip('/') + '/posts'
            print(f"  Loading Facebook page: {posts_url}...")
            try:
                page.goto(posts_url, wait_until='domcontentloaded', timeout=30000)
            except Exception:
                pass
            _sleep(3, 4)

            # If we got redirected away from the page, try the base URL
            if FB_PAGE.lower() not in page.url.lower():
                print(f"  Redirected to {page.url} — trying base URL...")
                try:
                    page.goto(fb_base, wait_until='domcontentloaded', timeout=30000)
                except Exception:
                    pass
                _sleep(3, 4)

            print(f"  On page: {page.url}")

            # Scroll to trigger lazy-load
            for _ in range(8):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                _sleep(1.5, 2.5)

            # Collect post links — Facebook Pages use these URL patterns
            post_links = set()
            for sel in [
                'a[href*="/posts/"]',
                'a[href*="story_fbid"]',
                'a[href*="/videos/"]',
                'a[href*="/reel/"]',
                'a[href*="/photo/"]',
            ]:
                for el in page.query_selector_all(sel):
                    href = el.get_attribute('href') or ''
                    href = href.split('?')[0]
                    if not href.startswith('http'):
                        href = 'https://www.facebook.com' + href
                    # Filter to links that belong to this page
                    slug = FB_PAGE.lstrip('https://www.facebook.com/').lower()
                    if slug in href.lower() or '/posts/' in href or '/reel/' in href or '/videos/' in href:
                        post_links.add(href)

            print(f"  Found {len(post_links)} post links — scraping metrics...")

            for i, url in enumerate(list(post_links)[:MAX_POSTS]):
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    _sleep(1.5, 2.5)

                    body_text = page.inner_text('body')

                    # Published date from <time> or text
                    published = ''
                    time_el = page.query_selector('abbr[data-utime], time[datetime], abbr[title]')
                    if time_el:
                        utime = time_el.get_attribute('data-utime')
                        dt_attr = time_el.get_attribute('datetime')
                        title_attr = time_el.get_attribute('title') or ''
                        if utime:
                            try:
                                published = datetime.fromtimestamp(int(utime)).strftime('%Y-%m-%d')
                            except Exception:
                                pass
                        elif dt_attr:
                            try:
                                published = datetime.fromisoformat(
                                    dt_attr.replace('Z', '+00:00')
                                ).strftime('%Y-%m-%d')
                            except Exception:
                                published = dt_attr[:10]
                        elif title_attr:
                            m = re.search(r'(\w+ \d+, \d{4})', title_attr)
                            if m:
                                try:
                                    published = datetime.strptime(m.group(1), '%B %d, %Y').strftime('%Y-%m-%d')
                                except Exception:
                                    pass
                    if not published:
                        date_match = re.search(
                            r'\b(January|February|March|April|May|June|July|August'
                            r'|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
                            body_text
                        )
                        if date_match:
                            try:
                                published = datetime.strptime(
                                    date_match.group(0).replace(',', ''), '%B %d %Y'
                                ).strftime('%Y-%m-%d')
                            except Exception:
                                pass

                    # Caption / title — first substantial line of body text after page header
                    title = f"Post {published or i + 1}"
                    lines = [ln.strip() for ln in body_text.splitlines() if len(ln.strip()) > 20]
                    for ln in lines:
                        # Skip navigation / UI lines
                        if any(skip in ln for skip in ['Facebook', 'Log in', 'Sign up', 'GraydientMedia', 'Graydient Media']):
                            continue
                        title = ln[:80]
                        break

                    # Reactions / likes
                    likes = 0
                    react_match = re.search(
                        r'([\d,]+(?:\.\d+)?[KMk]?)\s*(?:reaction|like|people reacted)',
                        body_text, re.IGNORECASE
                    )
                    if react_match:
                        likes = _parse_count(react_match.group(1))

                    # Views (videos/reels)
                    views = 0
                    view_match = re.search(
                        r'([\d,]+(?:\.\d+)?[KMk]?)\s*(?:view|play)',
                        body_text, re.IGNORECASE
                    )
                    if view_match:
                        views = _parse_count(view_match.group(1))

                    # Comments
                    comments = 0
                    comment_match = re.search(
                        r'([\d,]+(?:\.\d+)?[KMk]?)\s*comment', body_text, re.IGNORECASE
                    )
                    if comment_match:
                        comments = _parse_count(comment_match.group(1))

                    # Shares
                    shares = 0
                    share_match = re.search(
                        r'([\d,]+(?:\.\d+)?[KMk]?)\s*share', body_text, re.IGNORECASE
                    )
                    if share_match:
                        shares = _parse_count(share_match.group(1))

                    posts.append({
                        'platform':              'Facebook',
                        'title':                 title,
                        'url':                   url,
                        'published_date':        published,
                        'duration':              '',
                        'views':                 views or likes,
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

                    if (i + 1) % 5 == 0:
                        print(f"    Facebook: scraped {i + 1} posts...")

                except Exception as e:
                    print(f"    Warning: skipped {url} — {e}")
                    continue

        except Exception as e:
            print(f"  Facebook scraper error: {e}")
        finally:
            browser.close()

    print(f"  Facebook: {len(posts)} posts scraped.")
    return posts
