"""
Wayback-backed fallback: hit archive.org's archived snapshots of known peak-era
NFT-millionaire articles. Many original URLs now 404 but their archived copies
render fine. Captures screenshots that look like the original article.
"""
import asyncio, json, sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from playwright.async_api import async_playwright

OUT_DIR = Path(r"c:/Users/Gray Davis/my-project/web-apps/hyperframes-nft-rich-stack/article-screenshots")
manifest_path = OUT_DIR / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

# Known peak-era stories. Wayback snapshot prefix means we get the article view
# without paywalls + with the original chrome.
SNAPSHOTS = [
    # (slug, archive snapshot date, original url)
    ("cnbc",         "2021031200000", "https://www.cnbc.com/2021/03/11/most-expensive-nft-ever-sold-auctions-for-69point3-million.html"),
    ("forbes",       "2021081400000", "https://www.forbes.com/sites/abrambrown/2021/08/13/an-nft-portrait-just-sold-for-118-million-the-highest-price-ever-paid-for-a-cryptopunk/"),
    ("businessinsider","2021031300000","https://www.businessinsider.com/nft-artist-beeple-mike-winkelmann-sells-art-for-69-million-2021-3"),
    ("guardian",     "2021031200000", "https://www.theguardian.com/artanddesign/2021/mar/11/beeple-everydays-69m-nft-art-sale-jpg-file-christies"),
    ("techcrunch",   "2021110100000", "https://techcrunch.com/2021/10/29/yuga-labs-bored-ape-yacht-club-creator-is-the-talk-of-crypto-twitter/"),
    ("rolling-stone","2022012000000", "https://www.rollingstone.com/culture/culture-features/nft-bored-ape-yacht-club-eminem-jimmy-fallon-1281583/"),
    ("nytimes",      "2021031200000", "https://www.nytimes.com/2021/03/11/arts/design/nft-auction-christies-beeple.html"),
    ("vice",         "2021040100000", "https://www.vice.com/en/article/people-are-paying-millions-of-dollars-for-digital-jpegs/"),
    ("bloomberg",    "2021082000000", "https://www.bloomberg.com/news/articles/2021-08-19/bored-ape-yacht-club-nft-millionaires-yuga-labs"),
    ("fortune",      "2021040100000", "https://fortune.com/2021/03/11/beeple-everydays-the-first-5000-days-nft-record-sale-christies/"),
]

# Skip outlets already in manifest
already = {m["outlet"] for m in manifest}
SNAPSHOTS = [s for s in SNAPSHOTS if s[0] not in already]
print(f"already: {sorted(already)}", flush=True)
print(f"snapshots to try: {[s[0] for s in SNAPSHOTS]}", flush=True)


UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def block(t):
    if not t: return False
    t = t.lower()
    return any(x in t for x in [
        "404","page not found","got a moment","press & hold","we're sorry",
        "hrm.","the wayback machine has not","sorry, we couldn't",
        "this page isn","access denied","please enable javascript"])


async def dismiss(page):
    for s in ['button:has-text("Accept All")','button:has-text("Accept")',
              'button:has-text("Agree")','#onetrust-accept-btn-handler',
              'button:has-text("I Accept")','button:has-text("Continue")']:
        try:
            el = await page.query_selector(s)
            if el:
                await el.click(timeout=1000)
                await page.wait_for_timeout(300)
        except Exception:
            pass


async def get_h(page):
    for sel in ["h1","article h1","[data-testid='headline']"]:
        try:
            el = await page.query_selector(sel)
            if el:
                t = (await el.inner_text()).strip().split("\n")[0].strip()
                if len(t) >= 8: return t[:240]
        except Exception:
            pass
    try: return (await page.title()).strip()[:240]
    except Exception: return None


async def hide_wayback_toolbar(page):
    """Wayback adds a fixed toolbar at top — hide it so the screenshot looks
    like the article itself."""
    try:
        await page.add_style_tag(content="""
            #wm-ipp-base, #wm-ipp-print, #wm-ipp { display: none !important; }
            html { padding-top: 0 !important; }
        """)
    except Exception:
        pass


async def capture(page, url, out_path):
    try:
        # if_ flag = without wayback wrapper if available, else just the snapshot
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    except Exception as e:
        print(f"      goto err: {e}", flush=True)
        return False, None
    await page.wait_for_timeout(4500)
    await dismiss(page)
    await hide_wayback_toolbar(page)
    await page.wait_for_timeout(900)
    h = await get_h(page)
    if h and block(h):
        print(f"      headline blocked: {h!r}", flush=True)
        return False, None
    try:
        body = await page.evaluate("() => (document.body.innerText||'').slice(0,1500)")
        if block(body):
            print(f"      body blocked", flush=True)
            return False, None
    except Exception:
        pass
    try:
        await page.screenshot(path=str(out_path),
                              clip={"x":0,"y":0,"width":1600,"height":1000})
        return True, h
    except Exception as e:
        print(f"      screenshot err: {e}", flush=True)
        return False, None


async def main():
    captured = len(manifest)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for slug, ts, orig in SNAPSHOTS:
            if captured >= 8:
                break
            print(f"\n[{slug}] orig={orig[:90]}", flush=True)
            ctx = await browser.new_context(viewport={"width":1600,"height":1000},
                                            user_agent=UA, locale="en-US")
            page = await ctx.new_page()

            # Try a few wayback variations
            attempts = [
                f"https://web.archive.org/web/{ts}/{orig}",
                f"https://web.archive.org/web/2021*/{orig}",
                f"https://web.archive.org/web/2022*/{orig}",
                orig,  # last-ditch: original URL
            ]

            success = False
            for url in attempts:
                fname = f"article-{captured+1:02d}-{slug}.png"
                out_path = OUT_DIR / fname
                print(f"   try {url[:140]}", flush=True)
                ok, h = await capture(page, url, out_path)
                if ok and out_path.exists() and out_path.stat().st_size > 30000:
                    captured += 1
                    manifest.append({
                        "filename": fname,
                        "source_url": url,
                        "outlet": slug,
                        "headline": h,
                        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    })
                    print(f"      OK ({out_path.stat().st_size//1024} KB) - {h}", flush=True)
                    success = True
                    break
                else:
                    if out_path.exists():
                        try: out_path.unlink()
                        except: pass
            if not success:
                print(f"  [{slug}] no usable capture", flush=True)
            await ctx.close()

        await browser.close()

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n=== {captured} total ===", flush=True)
    for m in manifest:
        print(f"  {m['outlet']:18s} - {m['headline']}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
