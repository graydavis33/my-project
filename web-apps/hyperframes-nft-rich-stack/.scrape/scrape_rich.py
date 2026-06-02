"""
Capture news article screenshots about people getting rich off NFTs at the peak.
Adapted from the crash-stack scraper — same brave-search + chromium-screenshot
loop, retargeted queries + outlets, with hard-coded fallback URLs for the
biggest peak-era stories so we always get a usable set even if search returns
nothing on-domain.
"""
import asyncio, json, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlparse

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from playwright.async_api import async_playwright

OUT_DIR = Path(r"c:/Users/Gray Davis/my-project/web-apps/hyperframes-nft-rich-stack/article-screenshots")
manifest_path = OUT_DIR / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
already = {m["outlet"] for m in manifest}
print(f"already: {sorted(already)}", flush=True)

# Outlet -> (search queries to try, fallback known peak-era URLs).
TARGETS = [
    {
        "slug": "cnbc",
        "domain": "cnbc.com",
        "queries": [
            "NFT millionaire cnbc.com",
            "Beeple 69 million cnbc.com",
            "NFT made millions cnbc.com",
        ],
        "fallbacks": [
            "https://www.cnbc.com/2021/03/11/most-expensive-nft-ever-sold-auctions-for-69point3-million.html",
            "https://www.cnbc.com/2021/08/23/bored-ape-yacht-club-creators-raised-millions-in-nft-sale.html",
        ],
    },
    {
        "slug": "forbes",
        "domain": "forbes.com",
        "queries": [
            "NFT millionaire forbes.com",
            "Bored Ape owner millions forbes.com",
            "CryptoPunk sold millions forbes.com",
        ],
        "fallbacks": [
            "https://www.forbes.com/sites/abrambrown/2021/08/13/an-nft-portrait-just-sold-for-118-million-the-highest-price-ever-paid-for-a-cryptopunk/",
        ],
    },
    {
        "slug": "businessinsider",
        "domain": "businessinsider.com",
        "queries": [
            "NFT millionaire businessinsider.com",
            "teen NFT made millions businessinsider.com",
            "bored ape millionaire businessinsider.com",
        ],
        "fallbacks": [
            "https://www.businessinsider.com/nft-artist-beeple-mike-winkelmann-sells-art-for-69-million-2021-3",
        ],
    },
    {
        "slug": "the-verge",
        "domain": "theverge.com",
        "queries": [
            "Beeple 69 million theverge.com",
            "NFT sold millions theverge.com",
            "CryptoPunk record theverge.com",
        ],
        "fallbacks": [
            "https://www.theverge.com/2021/3/11/22325054/beeple-christies-nft-sale-cost-everydays-69-million",
        ],
    },
    {
        "slug": "guardian",
        "domain": "theguardian.com",
        "queries": [
            "NFT millionaire theguardian.com",
            "Beeple sold 69 million theguardian.com",
            "NFT artist rich theguardian.com",
        ],
        "fallbacks": [
            "https://www.theguardian.com/artanddesign/2021/mar/11/beeple-everydays-69m-nft-art-sale-jpg-file-christies",
        ],
    },
    {
        "slug": "nytimes",
        "domain": "nytimes.com",
        "queries": [
            "NFT millionaire nytimes.com",
            "Beeple sold million nytimes.com",
            "NFT artist millions nytimes.com",
        ],
        "fallbacks": [
            "https://www.nytimes.com/2021/03/11/arts/design/nft-auction-christies-beeple.html",
        ],
    },
    {
        "slug": "techcrunch",
        "domain": "techcrunch.com",
        "queries": [
            "NFT millionaire techcrunch.com",
            "Bored Ape millions techcrunch.com",
            "NFT raises millions techcrunch.com",
        ],
        "fallbacks": [
            "https://techcrunch.com/2021/10/29/yuga-labs-bored-ape-yacht-club-creator-is-the-talk-of-crypto-twitter/",
        ],
    },
    {
        "slug": "rolling-stone",
        "domain": "rollingstone.com",
        "queries": [
            "NFT millionaire rollingstone.com",
            "celebrity NFT millions rollingstone.com",
        ],
        "fallbacks": [
            "https://www.rollingstone.com/culture/culture-features/nft-bored-ape-yacht-club-eminem-jimmy-fallon-1281583/",
        ],
    },
]
TARGETS = [t for t in TARGETS if t["slug"] not in already]
print(f"targets: {[t['slug'] for t in TARGETS]}", flush=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def block(text):
    if not text: return False
    t = text.lower()
    return any(x in t for x in [
        "404","page not found","page does not exist","whoops",
        "access is temporarily restricted","unusual activity","press & hold",
        "we're sorry","cannot be found","the wayback machine has not",
        "sorry, we couldn't","this page isn"])


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


async def search_brave(page, q, domain):
    print(f"   brave: {q}", flush=True)
    try:
        await page.goto(f"https://search.brave.com/search?q={quote_plus(q)}",
                        wait_until="domcontentloaded", timeout=25000)
    except Exception as e:
        print(f"     goto err: {e}", flush=True)
        return []
    await page.wait_for_timeout(3000)
    urls = []
    anchors = await page.query_selector_all("#results a")
    for a in anchors[:100]:
        href = await a.get_attribute("href")
        if not href or not href.startswith("http") or "brave.com" in href:
            continue
        try:
            p = urlparse(href)
            if domain in p.netloc.lower() and p.path not in ("","/"):
                if href not in urls: urls.append(href)
        except Exception:
            continue
    print(f"     -> {len(urls)} on-domain results", flush=True)
    return urls


async def capture(page, url, out_path):
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
    except Exception as e:
        print(f"      goto err: {e}", flush=True)
        return False, None
    await page.wait_for_timeout(3200)
    await dismiss(page)
    await page.wait_for_timeout(800)
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
        for outlet in TARGETS:
            if captured >= 8:
                break
            slug, domain = outlet["slug"], outlet["domain"]
            print(f"\n[{slug}] domain={domain}", flush=True)
            ctx = await browser.new_context(viewport={"width":1600,"height":1000},
                                            user_agent=UA, locale="en-US")
            page = await ctx.new_page()
            try:
                await page.goto("https://search.brave.com/", wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000)
            except Exception:
                pass

            cands = []
            for q in outlet["queries"]:
                if len(cands) >= 4:
                    break
                cands += [u for u in await search_brave(page, q, domain) if u not in cands]
                await page.wait_for_timeout(1800)
            # Always include the fallback URLs as last-resort candidates
            for f in outlet.get("fallbacks", []):
                if f not in cands:
                    cands.append(f)

            success = False
            for cand in cands[:6]:
                fname = f"article-{captured+1:02d}-{slug}.png"
                out_path = OUT_DIR / fname
                print(f"   try {cand[:140]}", flush=True)
                ok, h = await capture(page, cand, out_path)
                if ok and out_path.exists() and out_path.stat().st_size > 8000:
                    captured += 1
                    manifest.append({
                        "filename": fname,
                        "source_url": cand,
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
