"""
V5 (final additive pass): fresh browser session, single search engine per outlet,
fewer queries, more wait between calls.  Append to existing manifest.
"""
import asyncio, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlparse

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from playwright.async_api import async_playwright

OUT_DIR = Path(r"c:/Users/Gray Davis/my-project/web-apps/hyperframes-nft-crash-stack/article-screenshots")
manifest_path = OUT_DIR / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
already = {m["outlet"] for m in manifest}
print(f"already: {sorted(already)}", flush=True)

# Slim target list — just a few of the most recognizable still-missing outlets
TARGETS = [
    {"slug": "business-insider", "domain": "businessinsider.com"},
    {"slug": "cnn",              "domain": "cnn.com"},
    {"slug": "wired",            "domain": "wired.com"},
    {"slug": "rolling-stone",    "domain": "rollingstone.com"},
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
              'button:has-text("Agree")','#onetrust-accept-btn-handler']:
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
    await page.wait_for_timeout(2800)
    await dismiss(page)
    await page.wait_for_timeout(700)
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
        # Fresh context per outlet to dodge rate limits
        for outlet in TARGETS:
            if captured >= 10:
                break
            slug, domain = outlet["slug"], outlet["domain"]
            print(f"\n[{slug}] domain={domain}", flush=True)
            ctx = await browser.new_context(viewport={"width":1600,"height":1000},
                                            user_agent=UA, locale="en-US")
            page = await ctx.new_page()
            # Warm up with a homepage hit
            try:
                await page.goto("https://search.brave.com/", wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000)
            except Exception:
                pass

            cands = await search_brave(page, f"NFT crash {domain}", domain)
            if len(cands) < 3:
                await page.wait_for_timeout(2500)
                cands += [u for u in await search_brave(page, f"NFT worthless {domain}", domain) if u not in cands]

            success = False
            for cand in cands[:5]:
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
