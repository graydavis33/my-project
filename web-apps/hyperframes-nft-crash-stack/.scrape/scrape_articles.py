"""
Capture above-the-fold screenshots of real NFT-crash news articles.
Headless Chromium, viewport 1600x1000, crop to top ~1000px.
"""
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from playwright.async_api import async_playwright

OUT_DIR = Path(r"c:/Users/Gray Davis/my-project/web-apps/hyperframes-nft-crash-stack/article-screenshots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Hand-picked real articles (well-known outlets, NFT crash topic, mostly non-paywalled
# or with archive.org fallbacks).  We'll try direct first, fall back to web.archive.org.
ARTICLES = [
    {
        "outlet": "reuters",
        "headline_hint": "NFT sales sink as crypto crash spreads",
        "url": "https://www.reuters.com/technology/nft-sales-hit-18-month-low-bored-ape-prices-plummet-2022-08-29/",
    },
    {
        "outlet": "cnbc",
        "headline_hint": "NFT trading volumes collapse 97% from January peak",
        "url": "https://www.cnbc.com/2022/09/29/nft-trading-volumes-collapse-97percent-from-januarys-all-time-high.html",
    },
    {
        "outlet": "bloomberg",
        "headline_hint": "NFT Market Is Worthless Now, New Report Claims",
        "url": "https://www.bloomberg.com/news/articles/2023-09-22/nfts-are-flopping-95-of-collections-are-worthless-dappgambl-report",
    },
    {
        "outlet": "the-verge",
        "headline_hint": "NFTs are nearly worthless for 95% of holders",
        "url": "https://www.theverge.com/2023/9/21/23884381/nfts-95-percent-worthless-dappgambl-report",
    },
    {
        "outlet": "decrypt",
        "headline_hint": "Bored Ape Yacht Club Floor Price Crashes",
        "url": "https://decrypt.co/195840/bored-ape-yacht-club-floor-price-2-year-low-bitcoin-ethereum-prices-decline",
    },
    {
        "outlet": "coindesk",
        "headline_hint": "NFT Market Endured Brutal 2023",
        "url": "https://www.coindesk.com/markets/2024/01/02/the-nft-market-endured-a-brutal-2023-but-some-collections-thrived",
    },
    {
        "outlet": "techcrunch",
        "headline_hint": "Are NFTs dead? Trading volume has collapsed",
        "url": "https://techcrunch.com/2023/05/15/the-nft-market-hasnt-died-it-evolved/",
    },
    {
        "outlet": "forbes",
        "headline_hint": "95% Of NFTs Are Now Worthless",
        "url": "https://www.forbes.com/sites/digital-assets/2023/09/21/95-of-nfts-are-now-worthless-research-shows/",
    },
    {
        "outlet": "business-insider",
        "headline_hint": "NFT market in collapse",
        "url": "https://www.businessinsider.com/nft-market-decline-trading-volumes-bored-ape-cryptopunks-2022-9",
    },
    {
        "outlet": "wsj",
        "headline_hint": "NFT Sales Are Flatlining",
        "url": "https://www.wsj.com/articles/nft-sales-are-flatlining-11651552616",
    },
    {
        "outlet": "nyt",
        "headline_hint": "NFTs Are Going Through a Slump",
        "url": "https://www.nytimes.com/2022/08/28/business/nft-sales-crypto-slump.html",
    },
    {
        "outlet": "vice",
        "headline_hint": "NFT market is collapsing",
        "url": "https://www.vice.com/en/article/nft-market-crash-bored-ape/",
    },
]

ARCHIVE_PREFIX = "https://web.archive.org/web/2024/"

COOKIE_DISMISS_SELECTORS = [
    'button:has-text("Accept")',
    'button:has-text("Accept All")',
    'button:has-text("Accept all")',
    'button:has-text("I Accept")',
    'button:has-text("Agree")',
    'button:has-text("I Agree")',
    'button:has-text("OK")',
    'button:has-text("Got it")',
    'button:has-text("Continue")',
    'button[aria-label*="Accept"]',
    'button[aria-label*="accept"]',
    'button[aria-label*="Close"]',
    '[id*="onetrust-accept"]',
    '#onetrust-accept-btn-handler',
    '.fc-cta-consent',
]


async def try_dismiss_overlays(page):
    for sel in COOKIE_DISMISS_SELECTORS:
        try:
            btn = await page.query_selector(sel)
            if btn:
                await btn.click(timeout=1500)
                await page.wait_for_timeout(400)
        except Exception:
            pass


async def capture(page, url, out_path):
    print(f"  -> GET {url}", flush=True)
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=35000)
    except Exception as e:
        print(f"     goto failed: {e}", flush=True)
        return False, None
    # Give hero / fonts a moment
    await page.wait_for_timeout(2500)
    await try_dismiss_overlays(page)
    await page.wait_for_timeout(600)
    # Try grabbing headline text for manifest
    headline = None
    for h_sel in ["h1", "[data-testid='headline']", "article h1", ".headline"]:
        try:
            el = await page.query_selector(h_sel)
            if el:
                txt = (await el.inner_text()).strip()
                if txt and len(txt) > 8:
                    headline = txt.split("\n")[0][:200]
                    break
        except Exception:
            continue
    # Screenshot the top of the page
    try:
        await page.screenshot(
            path=str(out_path),
            clip={"x": 0, "y": 0, "width": 1600, "height": 1000},
            full_page=False,
        )
        return True, headline
    except Exception as e:
        print(f"     screenshot failed: {e}", flush=True)
        return False, headline


async def main():
    manifest = []
    captured = 0
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

        for i, art in enumerate(ARTICLES, start=1):
            idx_slot = captured + 1
            fname = f"article-{idx_slot:02d}-{art['outlet']}.png"
            out_path = OUT_DIR / fname
            print(f"[{i}/{len(ARTICLES)}] {art['outlet']}", flush=True)

            ok, headline = await capture(page, art["url"], out_path)
            used_url = art["url"]

            if not ok:
                # Try archive.org fallback
                archive_url = ARCHIVE_PREFIX + art["url"]
                print(f"     fallback -> archive.org", flush=True)
                ok, headline = await capture(page, archive_url, out_path)
                used_url = archive_url

            if ok and out_path.exists() and out_path.stat().st_size > 5000:
                captured += 1
                manifest.append({
                    "filename": fname,
                    "source_url": used_url,
                    "outlet": art["outlet"],
                    "headline": headline or art["headline_hint"],
                    "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                })
                print(f"     OK ({out_path.stat().st_size//1024} KB) - {headline or art['headline_hint']}", flush=True)
                if captured >= 8:
                    # We have enough good ones; keep going only a couple more to have spares
                    if captured >= 10:
                        break
            else:
                # Wipe partial file
                if out_path.exists():
                    try:
                        out_path.unlink()
                    except Exception:
                        pass
                print(f"     SKIP (no usable capture)", flush=True)

        await browser.close()

    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nCaptured {captured} screenshots -> {OUT_DIR}", flush=True)
    print(f"Manifest -> {manifest_path}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
