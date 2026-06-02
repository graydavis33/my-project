"""
V4 (additive): fetch MORE article URLs using Bing + DDG-lite as backups for outlets
not yet captured. Append to existing manifest, don't overwrite.
"""
import asyncio, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlparse, unquote

sys.stdout.reconfigure(encoding="utf-8")

from playwright.async_api import async_playwright

OUT_DIR = Path(r"c:/Users/Gray Davis/my-project/web-apps/hyperframes-nft-crash-stack/article-screenshots")
manifest_path = OUT_DIR / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
already = {m["outlet"] for m in manifest}
print(f"Already have: {sorted(already)}", flush=True)

OUTLETS = [
    {"slug": "wired",            "domain": "wired.com",           "via_archive": False},
    {"slug": "business-insider", "domain": "businessinsider.com", "via_archive": False},
    {"slug": "coindesk",         "domain": "coindesk.com",        "via_archive": False},
    {"slug": "decrypt",          "domain": "decrypt.co",          "via_archive": False},
    {"slug": "cnn",              "domain": "cnn.com",             "via_archive": False},
    {"slug": "nbc-news",         "domain": "nbcnews.com",         "via_archive": False},
    {"slug": "engadget",         "domain": "engadget.com",        "via_archive": False},
    {"slug": "rolling-stone",    "domain": "rollingstone.com",    "via_archive": False},
    {"slug": "independent",      "domain": "independent.co.uk",   "via_archive": False},
    {"slug": "reuters",          "domain": "reuters.com",         "via_archive": True},
    {"slug": "bloomberg",        "domain": "bloomberg.com",       "via_archive": True},
    {"slug": "nyt",              "domain": "nytimes.com",         "via_archive": True},
]
OUTLETS = [o for o in OUTLETS if o["slug"] not in already]
print(f"Targets: {[o['slug'] for o in OUTLETS]}", flush=True)

QUERIES = [
    "NFT crash {domain}",
    "NFT market collapse {domain}",
    "NFTs worthless {domain}",
    "Bored Ape floor crash {domain}",
]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def looks_block(text):
    if not text:
        return False
    t = text.lower()
    bad = [
        "404", "page not found", "page does not exist",
        "we're sorry", "cannot be found", "page no longer",
        "access is temporarily restricted", "unusual activity", "press & hold",
        "whoops", "the wayback machine has not", "sorry, we couldn't",
        "page can't be found", "hrm.",
    ]
    return any(b in t for b in bad)


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


async def headline(page):
    for sel in ["h1", "article h1", "[data-testid='headline']"]:
        try:
            el = await page.query_selector(sel)
            if el:
                t = (await el.inner_text()).strip().split("\n")[0].strip()
                if len(t) >= 8:
                    return t[:240]
        except Exception:
            pass
    try:
        return (await page.title()).strip()[:240]
    except Exception:
        return None


async def bing_search(page, query, domain):
    url = f"https://www.bing.com/search?q={quote_plus(query)}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except Exception:
        return []
    await page.wait_for_timeout(1800)
    urls = []
    # Bing renders article URLs as cite text or in the link
    anchors = await page.query_selector_all("li.b_algo h2 a, .b_algo cite")
    for a in anchors[:30]:
        try:
            tag = await a.evaluate("e => e.tagName")
            if tag == "A":
                href = await a.get_attribute("href")
                if not href:
                    continue
                # Bing redirect URLs decode to actual target via cite text near them — but
                # we can just GET the redirect, it 302s to the real URL.  We follow that.
                if "bing.com/ck/" in href:
                    # follow redirect in a separate fetch
                    real = await follow_redirect(page.context, href)
                    if real and domain in real:
                        urls.append(real)
                elif domain in href:
                    urls.append(href)
            else:
                txt = (await a.inner_text()).strip()
                # cite text like "www.theguardian.com › technology › jul › ..." — not always usable
                if domain in txt and " › " in txt:
                    # Skip — not directly usable as URL
                    pass
        except Exception:
            continue
    # Dedup
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


async def follow_redirect(ctx, url):
    """Use a fresh page to follow Bing's redirect and grab the final URL."""
    try:
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            final = page.url
        finally:
            await page.close()
        return final
    except Exception:
        return None


async def brave_search(page, query, domain):
    url = f"https://search.brave.com/search?q={quote_plus(query)}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except Exception:
        return []
    await page.wait_for_timeout(2000)
    urls = []
    anchors = await page.query_selector_all("#results a")
    for a in anchors[:80]:
        href = await a.get_attribute("href")
        if not href or not href.startswith("http") or "brave.com" in href:
            continue
        try:
            p = urlparse(href)
            if domain in p.netloc.lower() and p.path not in ("", "/"):
                if href not in urls:
                    urls.append(href)
        except Exception:
            continue
    return urls


async def ddg_lite_search(page, query, domain):
    """ddg lite is a stripped-down search page that's more scraper-friendly."""
    url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except Exception:
        return []
    await page.wait_for_timeout(1500)
    urls = []
    anchors = await page.query_selector_all("a[href]")
    for a in anchors[:80]:
        href = await a.get_attribute("href")
        if not href:
            continue
        # DDG lite gives direct URLs sometimes, redirects via /l/?uddg= other times
        if "uddg=" in href:
            m = re.search(r"uddg=([^&]+)", href)
            if m:
                href = unquote(m.group(1))
        if href.startswith("http") and domain in href and "duckduckgo.com" not in href:
            if href not in urls:
                urls.append(href)
    return urls


async def capture(page, url, out_path, via_archive=False):
    target = f"https://web.archive.org/web/2024if_/{url}" if via_archive else url
    try:
        await page.goto(target, wait_until="domcontentloaded", timeout=40000)
    except Exception as e:
        print(f"      goto failed: {e}", flush=True)
        return False, None
    await page.wait_for_timeout(2800)
    await dismiss(page)
    await page.wait_for_timeout(700)
    h = await headline(page)
    if h and looks_block(h):
        return False, None
    try:
        body = await page.evaluate("() => (document.body.innerText||'').slice(0,1200)")
        if looks_block(body):
            return False, None
    except Exception:
        pass
    try:
        await page.screenshot(path=str(out_path),
                              clip={"x":0,"y":0,"width":1600,"height":1000},
                              full_page=False)
        return True, h
    except Exception:
        return False, None


async def main():
    captured = len(manifest)
    print(f"Starting at captured={captured}", flush=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width":1600,"height":1000},
                                        user_agent=UA, locale="en-US")
        page = await ctx.new_page()

        for outlet in OUTLETS:
            if captured >= 10:
                break
            slug, domain = outlet["slug"], outlet["domain"]
            print(f"\n[{slug}] domain={domain}", flush=True)
            candidates = []
            # Try each search engine
            for engine_name, fn in [("brave", brave_search), ("ddg-lite", ddg_lite_search), ("bing", bing_search)]:
                if len(candidates) >= 4:
                    break
                for qt in QUERIES:
                    hits = await fn(page, qt.format(domain=domain), domain)
                    for h in hits:
                        if h not in candidates:
                            candidates.append(h)
                    if len(candidates) >= 4:
                        break
                    await page.wait_for_timeout(600)
                print(f"  via {engine_name}: total {len(candidates)} candidates", flush=True)
            if not candidates:
                print(f"  [{slug}] no candidates from any engine", flush=True)
                continue
            success = False
            for cand in candidates[:5]:
                fname = f"article-{captured+1:02d}-{slug}.png"
                out_path = OUT_DIR / fname
                print(f"   try {cand[:140]}", flush=True)
                ok, h = await capture(page, cand, out_path, via_archive=outlet["via_archive"])
                if not ok and not outlet["via_archive"]:
                    print(f"      fallback archive.org", flush=True)
                    ok, h = await capture(page, cand, out_path, via_archive=True)
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

        await browser.close()

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n=== DONE: {captured} captures total ===", flush=True)
    for m in manifest:
        print(f"  {m['outlet']:18s} - {m['headline']}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
