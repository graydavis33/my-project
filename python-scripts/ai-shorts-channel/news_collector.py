"""
Collects AI news from Reddit, NewsAPI, and YouTube trending.
Results are cached per-day to avoid redundant API calls.
"""

import json
import os
import hashlib
import requests
from datetime import datetime, timedelta, timezone
from config import (
    NEWS_API_KEY, YOUTUBE_API_KEY,
    NEWSAPI_SOURCES, REDDIT_SUBS, REDDIT_MIN_SCORE,
    TMP_DIR,
)

_CACHE_FILE = TMP_DIR / 'news_cache.json'


def collect_news(force=False) -> list[dict]:
    """Return today's AI news stories. Uses cache to avoid repeated fetches."""
    today = datetime.now().strftime('%Y-%m-%d')

    if not force and _CACHE_FILE.exists():
        cached = json.loads(_CACHE_FILE.read_text())
        if cached.get('date') == today:
            return cached['stories']

    stories = []
    stories.extend(_fetch_newsapi())
    stories.extend(_fetch_reddit())
    stories.extend(_fetch_youtube_trending())
    stories = _deduplicate(stories)

    _CACHE_FILE.write_text(json.dumps({'date': today, 'stories': stories}, indent=2))
    print(f"[news] Collected {len(stories)} unique stories")
    return stories


def _fetch_newsapi() -> list[dict]:
    if not NEWS_API_KEY:
        print("[news] NEWS_API_KEY not set — skipping NewsAPI")
        return []

    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    try:
        r = requests.get('https://newsapi.org/v2/everything', params={
            'q': 'artificial intelligence OR OpenAI OR Anthropic OR Google AI OR AI model',
            'from': yesterday,
            'sortBy': 'relevancy',
            'language': 'en',
            'sources': NEWSAPI_SOURCES,
            'pageSize': 30,
            'apiKey': NEWS_API_KEY,
        }, timeout=10)
        r.raise_for_status()

        return [{
            'title': a['title'],
            'summary': a.get('description') or '',
            'url': a['url'],
            'source': a['source']['name'],
            'published': a.get('publishedAt', ''),
            'platform': 'news',
            'score': 0,
        } for a in r.json().get('articles', []) if a.get('title') and a.get('url')]
    except Exception as e:
        print(f"[news] NewsAPI error: {e}")
        return []


def _fetch_reddit() -> list[dict]:
    headers = {'User-Agent': 'AINewsBot/1.0 (by /u/graydient_media)'}
    stories = []

    for sub in REDDIT_SUBS:
        try:
            r = requests.get(
                f'https://www.reddit.com/r/{sub}/hot.json',
                params={'limit': 15, 't': 'day'},
                headers=headers, timeout=10,
            )
            r.raise_for_status()
            posts = r.json().get('data', {}).get('children', [])
            for post in posts:
                d = post['data']
                if d.get('score', 0) < REDDIT_MIN_SCORE:
                    continue
                if d.get('is_self') and not d.get('selftext'):
                    continue
                stories.append({
                    'title': d['title'],
                    'summary': (d.get('selftext') or '')[:400],
                    'url': d.get('url') or f"https://reddit.com{d['permalink']}",
                    'source': f"r/{sub}",
                    'published': str(datetime.fromtimestamp(d['created_utc'], tz=timezone.utc)),
                    'platform': 'reddit',
                    'score': d['score'],
                })
        except Exception as e:
            print(f"[news] Reddit error for r/{sub}: {e}")

    return stories


def _fetch_youtube_trending() -> list[dict]:
    if not YOUTUBE_API_KEY:
        print("[news] YOUTUBE_API_KEY not set — skipping YouTube trending")
        return []

    published_after = (datetime.now(tz=timezone.utc) - timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
    try:
        r = requests.get('https://www.googleapis.com/youtube/v3/search', params={
            'part': 'snippet',
            'q': 'AI news artificial intelligence 2026',
            'type': 'video',
            'order': 'viewCount',
            'publishedAfter': published_after,
            'relevanceLanguage': 'en',
            'maxResults': 10,
            'key': YOUTUBE_API_KEY,
        }, timeout=10)
        r.raise_for_status()

        return [{
            'title': item['snippet']['title'],
            'summary': item['snippet']['description'][:400],
            'url': f"https://youtube.com/watch?v={item['id']['videoId']}",
            'source': item['snippet']['channelTitle'],
            'published': item['snippet']['publishedAt'],
            'platform': 'youtube',
            'score': 0,
        } for item in r.json().get('items', [])]
    except Exception as e:
        print(f"[news] YouTube trending error: {e}")
        return []


def _deduplicate(stories: list[dict]) -> list[dict]:
    seen_words = []
    unique = []
    for story in stories:
        words = set(story['title'].lower().split())
        is_dup = any(len(words & prev) > 4 for prev in seen_words)
        if not is_dup:
            seen_words.append(words)
            unique.append(story)
    return unique
