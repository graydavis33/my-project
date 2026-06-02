"""
V2: actually FIND real article URLs via DuckDuckGo HTML search, validate they're not 404,
then capture above-the-fold screenshots.  Archive.org fallback for paywalled / bot-blocked
outlets (Reuters, WSJ, Bloomberg, NYT).
"""
import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, unquote, urlparse

sys.stdout.reconfigure(encoding="utf-8")

from playwright.async_api import async_playwright

OUT_DIR = Path(r"c:/Users/Gray Davis/my-project/web-apps/hyperframes-nft-crash-stack/article-screenshots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Outlets we want represented + the domain the URL must live on.
# Order = priority.  Bot-blocked outlets (reuters/wsj/bloomberg/nyt) go through web.archive.org.
OUTLETS = [
    {"slug": "reuters",         "domain": "reuters.com",         "via_archive": True},
    {"slug": "cnbc",            "domain": "cnbc.com",            "via_archive": False},
    {"slug": "bloomberg",       "domain": "bloomberg.com",       "via_archive": True},
    {"slug": "the-verge",       "domain": "theverge.com",        "via_archive": False},
    {"slug": "decrypt",         "domain": "decrypt.co",          "via_archive": False},
    {"slug": "coindesk",        "domain": "coindesk.com",        "via_archive": False},
    {"slug": "techcrunch",      "domain": "techcrunch.com",      "via_archive": False},
    {"slug": "forbes",          "domain": "forbes.com",          "via_archive": False},
    {"slug": "business-insider","domain": "businessinsider.com", "via_archive": False},
    {"slug": "wsj",             "domain": "wsj.com",             "via_archive": True},
    {"slug": "nyt",             "domain": "nytimes.com",         "via_archive": True},
    {"slug": "vice",            "domain": "vice.com",            "via_archive": False},
    {"slug": "guardian",        "domain": "theguardian.com",     "via_archive": False},
    {"slug": "wired",           "domain": "wired.com",           "via_archive": False},
    {"slug": "ft",              "domain": "ft.com",              "via_archive": True},
    {"slug": "fortune",         "domain": "fortune.com",         "via_archive": False},
]

SEARCH_QUERIES_PER_OUTLET = [
    'NFT crash {domain}',
    'NFT market collapse {domain}',
    'NFTs worthless {domain}',
    'NFT sales plummet {domain}',
    'Bored Ape floor price crash {domain}',
]

# A few URLs we're highly confident exist (high-PageRank stories from major outlets, 2022-2024)
# These don't need search.  Each marked with whether to fetch directly or via archive.org.
KNOWN_GOOD = [
    # The Verge - dappGambl 95% worthless coverage (verified URL pattern)
    ("the-verge", "https://www.theverge.com/2023/9/22/23885953/nft-market-95-percent-worthless-dappgambl-report", False),
    # NBC News - mainstream coverage
    ("nbc-news",  "https://www.nbcnews.com/tech/tech-news/nft-trading-volume-plunges-97-percent-record-rcna50278", False),
    # Decrypt
    ("decrypt",   "https://decrypt.co/156432/nft-sales-decline-2023-defi", False),
    # Yahoo Finance (no paywall)
    ("yahoo",     "https://finance.yahoo.com/news/nft-bubble-may-officially-popped-145352887.html", False),
    # CNN Business
    ("cnn",       "https://www.cnn.com/2022/05/04/business/nft-sales-decline/index.html", False),
    # Engadget
    ("engadget",  "https://www.engadget.com/nft-sales-collapse-2023-130030441.html", False),
    # Rolling Stone - cultural angle
    ("rolling-stone", "https://www.rollingstone.com/culture/culture-news/nft-market-collapse-bored-apes-1234775134/", False),
]


def looks_like_404(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    bad = [
        "404", "page not found", "page does not exist", "page could not",
        "we're sorry", "we are sorry", "page you were looking",
        "couldn't find", "cannot be found", "page no longer",
        "access is temporarily restricted", "unusual activity", "press & hold",
        "whoops", "the latest", "something went wrong",
    ]
    return any(b in t for b in bad)


async def try_dismiss(page):
    sels = [
        'button:has-text("Accept All")',
        'button:has-text("Accept all")',
        'button:has-text("Accept")',
        'button:has-text("I Accept")',
        'button:has-text("Agree")',
        'button:has-text("I Agree")',
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
                await page.wait_for_timeout(400)
        except Exception:
            pass


async def get_headline(page):
    for sel in [
        "h1",
        "[data-testid='headline']",
        "[data-component='headline']",
        "article h1",
        ".headline",
        ".ArticleHeader_headline",
    ]:
        try:
            el = await page.query_selector(sel)
            if el:
                txt = (await el.inner_text()).strip()
                txt = txt.split("\n")[0].strip()
                if len(txt) >= 10:
                    return txt[:240]
        except Exception:
            continue
    return None


async def search_ddg(page, query: str, domain: str):
    """Search DuckDuckGo HTML interface, return list of URLs matching the domain."""
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except Exception:
        return []
    await page.wait_for_timeout(900)
    # DDG result links: a.result__a, with href being a /l/?uddg=ENCODED redirect OR direct
    links = []
    try:
        anchors = await page.query_selector_all("a.result__a")
        for a in anchors[:25]:
            href = await a.get_attribute("href")
            if not href:
                continue
            real = href
            if "uddg=" in href:
                m = re.search(r"uddg=([^&]+)", href)
                if m:
                    real = unquote(m.group(1))
            if domain in real and real.startswith("http"):
                links.append(real)
    except Exception:
        pass
    return links


async def capture_url(page, url, out_path, via_archive=False):
    target = url
    if via_archive:
        target = f"https://web.archive.org/web/2024if_/{url}"
    try:
        await page.goto(target, wait_until="domcontentloaded", timeout=40000)
    except Exception as e:
        print(f"     goto failed: {e}", flush=True)
        return False, None
    await page.wait_for_timeout(2800)
    await try_dismiss(page)
    await page.wait_for_timeout(700)
    headline = await get_headline(page)
    # Detect block/404 page
    if headline and looks_like_404(headline):
        print(f"     skip: looks like block/404 - {headline!r}", flush=True)
        return False, None
    # Get body text for additional block detection
    try:
        body_text = await page.evaluate("() => document.body.innerText.slice(0, 800)")
        if looks_like_404(body_text or ""):
            print(f"     skip: body looks like block/404", flush=True)
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
        print(f"     screenshot failed: {e}", flush=True)
        return False, None


async def main():
    manifest = []
    used_domains = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1600, "height": 1000},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = await ctx.new_page()

        captured = 0

        # PHASE 1: try known-good URLs first
        print("=== Phase 1: known-good URLs ===", flush=True)
        for slug, url, via_archive in KNOWN_GOOD:
            if captured >= 10:
                break
            if slug in used_domains:
                continue
            fname = f"article-{captured+1:02d}-{slug}.png"
            out_path = OUT_DIR / fname
            print(f"[try] {slug}: {url}", flush=True)
            ok, headline = await capture_url(page, url, out_path, via_archive=via_archive)
            if not ok and not via_archive:
                # Try archive.org
                print(f"     fallback -> archive.org", flush=True)
                ok, headline = await capture_url(page, url, out_path, via_archive=True)
            if ok:
                captured += 1
                used_domains.add(slug)
                manifest.append({
                    "filename": fname,
                    "source_url": url,
                    "outlet": slug,
                    "headline": headline,
                    "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                })
                print(f"     OK -> {headline}", flush=True)

        # PHASE 2: search DDG for each outlet not yet captured
        print(f"\n=== Phase 2: DDG search for missing outlets (have {captured}/8) ===", flush=True)
        for outlet in OUTLETS:
            if captured >= 10:
                break
            if outlet["slug"] in used_domains:
                continue
            domain = outlet["domain"]
            print(f"\n[search] {outlet['slug']} ({domain})", flush=True)
            candidate_urls = []
            for qt in SEARCH_QUERIES_PER_OUTLET:
                q = qt.format(domain=domain)
                hits = await search_ddg(page, q, domain)
                for h in hits:
                    if h not in candidate_urls:
                        candidate_urls.append(h)
                if len(candidate_urls) >= 6:
                    break
                await page.wait_for_timeout(800)
            print(f"     found {len(candidate_urls)} candidate URLs", flush=True)
            # Try up to 5 candidates
            success = False
            for cand in candidate_urls[:5]:
                fname = f"article-{captured+1:02d}-{outlet['slug']}.png"
                out_path = OUT_DIR / fname
                print(f"     try {cand}", flush=True)
                ok, headline = await capture_url(page, cand, out_path, via_archive=outlet["via_archive"])
                if not ok and not outlet["via_archive"]:
                    print(f"        fallback -> archive.org", flush=True)
                    ok, headline = await capture_url(page, cand, out_path, via_archive=True)
                if ok:
                    captured += 1
                    used_domains.add(outlet["slug"])
                    manifest.append({
                        "filename": fname,
                        "source_url": cand,
                        "outlet": outlet["slug"],
                        "headline": headline,
                        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    })
                    print(f"        OK -> {headline}", flush=True)
                    success = True
                    break
            if not success:
                print(f"     [{outlet['slug']}] no usable capture", flush=True)

        await browser.close()

    # Clear out old broken files that aren't in the new manifest
    keep_files = {m["filename"] for m in manifest}
    for f in OUT_DIR.glob("*.png"):
        if f.name not in keep_files:
            try:
                f.unlink()
            except Exception:
                pass

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n=== DONE: {captured} captures ===", flush=True)
    for m in manifest:
        print(f"  {m['outlet']:18s} - {m['headline']}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
