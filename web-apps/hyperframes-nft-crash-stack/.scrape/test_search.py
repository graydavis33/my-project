"""Test which search engine works in headless Playwright for finding article URLs."""
import asyncio, sys, re
from urllib.parse import quote_plus, unquote
sys.stdout.reconfigure(encoding="utf-8")
from playwright.async_api import async_playwright

QUERY = "NFT market crash 95 percent worthless"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1600, "height": 1000},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            locale="en-US",
        )
        page = await ctx.new_page()

        # Try DuckDuckGo HTML
        print("=== DDG HTML ===")
        await page.goto(f"https://html.duckduckgo.com/html/?q={quote_plus(QUERY)}", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)
        anchors = await page.query_selector_all("a[href*='http']")
        print(f"  total anchors: {len(anchors)}")
        # Print first 10 hrefs that aren't duckduckgo internal
        seen = 0
        for a in anchors[:50]:
            href = await a.get_attribute("href")
            if not href or "duckduckgo.com" in href or href.startswith("/"):
                continue
            print(f"  -> {href[:130]}")
            seen += 1
            if seen >= 10:
                break

        # Try Bing
        print("\n=== Bing ===")
        try:
            await page.goto(f"https://www.bing.com/search?q={quote_plus(QUERY)}", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)
            anchors = await page.query_selector_all("li.b_algo h2 a")
            print(f"  result links: {len(anchors)}")
            for a in anchors[:8]:
                href = await a.get_attribute("href")
                print(f"  -> {href[:130]}")
        except Exception as e:
            print(f"  err: {e}")

        # Try Brave
        print("\n=== Brave ===")
        try:
            await page.goto(f"https://search.brave.com/search?q={quote_plus(QUERY)}", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2500)
            anchors = await page.query_selector_all("a.h")
            print(f"  result links (a.h): {len(anchors)}")
            anchors2 = await page.query_selector_all("a[data-type='web']")
            print(f"  result links (a[data-type=web]): {len(anchors2)}")
            anchors3 = await page.query_selector_all("#results a")
            print(f"  result links (#results a): {len(anchors3)}")
            for a in anchors3[:10]:
                href = await a.get_attribute("href")
                if href and href.startswith("http") and "brave.com" not in href:
                    print(f"  -> {href[:130]}")
        except Exception as e:
            print(f"  err: {e}")

        await browser.close()

asyncio.run(main())
