"""
Collects B-roll for each story:
  - Pexels: portrait video clip (primary visual)
  - Playwright: screenshot of source article (secondary visual, overlay)
Cached per story — re-downloads only if .tmp files are missing.
"""

import asyncio
import hashlib
import requests
from pathlib import Path
from config import PEXELS_API_KEY, TMP_DIR

_PEXELS_SEARCH = 'https://api.pexels.com/videos/search'


# ─── Public API ───────────────────────────────────────────────────────────────

def collect_broll(script: dict) -> dict[int, dict]:
    """
    For each story, fetch Pexels B-roll + screenshot.
    Returns {0: {video: Path, screenshot: Path}, ...}
    """
    results = {}
    for i, story in enumerate(script['stories']):
        print(f"[broll] Collecting story {i+1}: {story['title']}")
        video_path = _fetch_pexels(i, story['broll_keywords'])
        screenshot_path = asyncio.run(_screenshot_url(i, story['source_url']))
        results[i] = {
            'video':      video_path,
            'screenshot': screenshot_path,
        }
    return results


# ─── Pexels ───────────────────────────────────────────────────────────────────

def _fetch_pexels(index: int, keywords: list[str]) -> Path | None:
    if not PEXELS_API_KEY:
        print("[broll] PEXELS_API_KEY not set")
        return None

    for query in keywords:
        cache_key = _hash(f"{index}:{query}")
        out_path  = TMP_DIR / f'broll_{index}_{cache_key}.mp4'

        if out_path.exists():
            print(f"[broll] Pexels cache hit for '{query}'")
            return out_path

        result = _pexels_search(query)
        if result:
            _download_video(result, out_path)
            return out_path

    print(f"[broll] No Pexels result for story {index+1} keywords: {keywords}")
    return None


def _pexels_search(query: str) -> str | None:
    """Return the best portrait MP4 download URL for a query."""
    try:
        r = requests.get(
            _PEXELS_SEARCH,
            headers={'Authorization': PEXELS_API_KEY},
            params={
                'query': query,
                'orientation': 'portrait',
                'size': 'medium',
                'per_page': 5,
            },
            timeout=10,
        )
        r.raise_for_status()
        videos = r.json().get('videos', [])
        if not videos:
            return None

        # Pick the HD portrait file from the first result
        video = videos[0]
        for f in video.get('video_files', []):
            if f.get('quality') == 'hd' and f.get('height', 0) > f.get('width', 1):
                return f['link']
        # Fallback: any file from first result
        files = video.get('video_files', [])
        return files[0]['link'] if files else None
    except Exception as e:
        print(f"[broll] Pexels error for '{query}': {e}")
        return None


def _download_video(url: str, out_path: Path):
    r = requests.get(url, timeout=60, stream=True)
    r.raise_for_status()
    with open(out_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)


# ─── Playwright screenshot ─────────────────────────────────────────────────────

async def _screenshot_url(index: int, url: str) -> Path | None:
    if not url or url.startswith('https://reddit.com') or url.startswith('https://www.reddit.com'):
        return None  # Reddit pages behind auth wall — skip

    cache_key = _hash(url)
    out_path  = TMP_DIR / f'screenshot_{index}_{cache_key}.png'

    if out_path.exists():
        print(f"[broll] Screenshot cache hit for story {index+1}")
        return out_path

    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page    = await browser.new_page(viewport={'width': 1280, 'height': 720})
            await page.goto(url, timeout=15000, wait_until='domcontentloaded')
            await page.wait_for_timeout(2000)
            await page.screenshot(path=str(out_path), full_page=False)
            await browser.close()
        print(f"[broll] Screenshot saved for story {index+1}")
        return out_path
    except Exception as e:
        print(f"[broll] Screenshot failed for story {index+1}: {e}")
        return None


def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:8]
