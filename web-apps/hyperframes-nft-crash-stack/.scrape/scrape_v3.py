"""
V3: Use Brave Search to find REAL article URLs by domain, validate, then capture.
Bot-blocked outlets (Reuters/Bloomberg/WSJ/NYT/FT) auto-go through web.archive.org.
"""
import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlparse

sys.stdout.reconfigure(encoding="utf-8")

from playwright.async_api import async_playwright

OUT_DIR = Path(r"c:/Users/Gray Davis/my-project/web-apps/hyperframes-nft-crash-stack/article-screenshots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Outlets to chase, in priority order. via_archive=True means we go through wayback by default
# (because they block headless browsers and/or paywall).
OUTLETS = [
    # Tier 1 — high-recognition brands.  Bot-blockers go via_archive.
    {"slug": "the-verge",        "domain": "theverge.com",        "via_archive": False},
    {"slug": "cnbc",             "domain": "cnbc.com",            "via_archive": False},
    {"slug": "techcrunch",       "domain": "techcrunch.com",      "via_archive": False},
    {"slug": "forbes",           "domain": "forbes.com",          "via_archive": False},
    {"slug": "fortune",          "domain": "fortune.com",         "via_archive": False},
    {"slug": "guardian",         "domain": "theguardian.com",     "via_archive": False},
    {"slug": "wired",            "domain": "wired.com",           "via_archive": False},
    {"slug": "business-insider", "domain": "businessinsider.com", "via_archive": False},
    {"slug": "coindesk",         "domain": "coindesk.com",        "via_archive": False},
    {"slug": "decrypt",          "domain": "decrypt.co",          "via_archive": False},
    {"slug": "cnn",              "domain": "cnn.com",             "via_archive": False},
    {"slug": "nbc-news",         "domain": "nbcnews.com",         "via_archive": False},
    {"slug": "engadget",         "domain": "engadget.com",        "via_archive": False},
    {"slug": "rolling-stone",    "domain": "rollingstone.com",    "via_archive": False},
    {"slug": "vice",             "domain": "vice.com",            "via_archive": False},
    # Bot-blocked / paywall outlets — go via archive.org by default
    {"slug": "reuters",          "domain": "reuters.com",         "via_archive": True},
    {"slug": "bloomberg",        "domain": "bloomberg.com",       "via_archive": True},
    {"slug": "wsj",              "domain": "wsj.com",             "via_archive": True},
    {"slug": "nyt",              "domain": "nytimes.com",         "via_archive": True},
    {"slug": "ft",               "domain": "ft.com",              "via_archive": True},
    {"slug": "independent",      "domain": "independent.co.uk",   "via_archive": False},
]

SEARCH_QUERIES = [
    "NFT crash {domain}",
    "NFT market collapse {domain}",
    "NFTs worthless {domain}",
    "NFT sales plummet {domain}",
    "Bored Ape floor price {domain}",
    "NFT bubble burst {domain}",
]

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


def looks_like_block(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    bad = [
        "404", "page not found", "page does not exist", "page could not",
        "we're sorry", "we are sorry", "page you were looking",
        "couldn't find", "cannot be found", "page no longer",
        "access is temporarily restricted", "unusual activity", "press & hold",
        "whoops", "the wayback machine has not archived",
        "hrm.", "sorry, we couldn't", "page can't be found",
        "this page isn", "wayback machine doesn't have that page",
    ]
    return any(b in t for b in bad)


async def try_dismiss(page):
    sels = [
        'button:has-text("Accept All")',
        'button:has-text("Accept all")',
        'button:has-text("Accept")',
        'button:has-text("Agree")',
        'button:has-text("OK")',
        'button:has-text("Got it")',
        'button:has-text("Continue")',
        '#onetrust-accept-btn-handler',
        '.fc-cta-consent',
    ]
    for s in sels:
        try:
            el = await page.query_selector(s)
            if el:
                await el.click(timeout=1200)
                await page.wait_for_timeout(350)
        except Exception:
            pass


async def get_headline(page):
    for sel in ["h1", "[data-testid='headline']", "article h1", ".headline"]:
        try:
            el = await page.query_selector(sel)
            if el:
                txt = (await el.inner_text()).strip().split("\n")[0].strip()
                if len(txt) >= 8:
                    return txt[:240]
        except Exception:
            continue
    try:
        title = await page.title()
        if title:
            return title.strip()[:240]
    except Exception:
        pass
    return None


async def brave_search(page, query: str, domain: str):
    """Return list of URLs from Brave Search results that live on the given domain."""
    url = f"https://search.brave.com/search?q={quote_plus(query)}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
    except Exception as e:
        print(f"     brave goto failed: {e}", flush=True)
        return []
    await page.wait_for_timeout(2000)
    urls = []
    try:
        anchors = await page.query_selector_all("#results a")
        for a in anchors[:80]:
            href = await a.get_attribute("href")
            if not href or not href.startswith("http"):
                continue
            if "brave.com" in href:
                continue
            try:
                p = urlparse(href)
            except Exception:
                continue
            host = p.netloc.lower()
            if domain in host:
                # Heuristic: real article URLs usually have a path with /YYYY/ or /article/ or a slug
                path = p.path
                if path in ("", "/"):
                    continue
                if href not in urls:
                    urls.append(href)
    except Exception:
        pass
    return urls


async def capture(page, url, out_path, via_archive=False):
    target = url
    if via_archive:
        # Use the if_/ flag to skip the wayback toolbar
        target = f"https://web.archive.org/web/2024if_/{url}"
    try:
        await page.goto(target, wait_until="domcontentloaded", timeout=40000)
    except Exception as e:
        print(f"        goto failed: {e}", flush=True)
        return False, None
    await page.wait_for_timeout(2800)
    await try_dismiss(page)
    await page.wait_for_timeout(700)
    headline = await get_headline(page)
    if headline and looks_like_block(headline):
        print(f"        block/404 headline: {headline!r}", flush=True)
        return False, None
    try:
        body_text = await page.evaluate("() => (document.body.innerText || '').slice(0, 1200)")
        if looks_like_block(body_text or ""):
            print(f"        block/404 body", flush=True)
            return False, None
    except Exception:
        pass
    try:
        await page.screenshot(
            path=str(out_path),
            clip={"x": 0, "y": 0, "width": 1600, "height": 1000},
            full_page=False,
        )
        return True, headline
    except Exception as e:
        print(f"        screenshot failed: {e}", flush=True)
        return False, None


async def main():
    manifest = []
    captured = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1600, "height": 1000},
            user_agent=UA,
            locale="en-US",
        )
        page = await ctx.new_page()

        for outlet in OUTLETS:
            if captured >= 10:
                break
            slug = outlet["slug"]
            domain = outlet["domain"]
            print(f"\n[{slug}] domain={domain} via_archive={outlet['via_archive']}", flush=True)
            candidates = []
            for q in SEARCH_QUERIES:
                hits = await brave_search(page, q.format(domain=domain), domain)
                for h in hits:
                    if h not in candidates:
                        candidates.append(h)
                if len(candidates) >= 6:
                    break
                await page.wait_for_timeout(700)
            print(f"  {len(candidates)} candidate URLs", flush=True)
            success = False
            for cand in candidates[:6]:
                fname = f"article-{captured+1:02d}-{slug}.png"
                out_path = OUT_DIR / fname
                print(f"   try {cand[:140]}", flush=True)
                ok, headline = await capture(page, cand, out_path, via_archive=outlet["via_archive"])
                if not ok and not outlet["via_archive"]:
                    print(f"      fallback -> archive.org", flush=True)
                    ok, headline = await capture(page, cand, out_path, via_archive=True)
                if ok and out_path.exists() and out_path.stat().st_size > 8000:
                    captured += 1
                    manifest.append({
                        "filename": fname,
                        "source_url": cand,
                        "outlet": slug,
                        "headline": headline,
                        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    })
                    print(f"      OK ({out_path.stat().st_size//1024} KB) - {headline}", flush=True)
                    success = True
                    break
                else:
                    if out_path.exists():
                        try:
                            out_path.unlink()
                        except Exception:
                            pass
            if not success:
                print(f"  [{slug}] no usable capture", flush=True)

        await browser.close()

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n=== DONE: {captured} captures ===", flush=True)
    for m in manifest:
        print(f"  {m['outlet']:18s} - {m['headline']}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
