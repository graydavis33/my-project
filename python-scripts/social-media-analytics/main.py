import os
import sys
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

# Fix Windows terminal encoding so Unicode characters don't crash
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

_REQUIRED = ["ANTHROPIC_API_KEY"]
_missing = [k for k in _REQUIRED if not os.getenv(k)]
if _missing:
    print(f"ERROR: Missing required env vars in .env: {', '.join(_missing)}")
    print(f"  Add them to: {os.path.join(os.path.dirname(__file__), '.env')}")
    sys.exit(1)

from youtube_fetcher import get_youtube_data
from sheets_writer import write_video_data
from ai_analyzer import analyze_and_write, get_sheet_insights

_DIR = os.path.dirname(__file__)
_DASHBOARD_DIR = os.path.normpath(os.path.join(_DIR, '..', '..', 'web-apps', 'social-media-analytics'))
_JSON_PATH = os.path.join(_DASHBOARD_DIR, 'analytics_data.json')
_TRENDS_CACHE = os.path.join(_DIR, '.trends_cache.json')
_EXPLANATIONS_CACHE = os.path.join(_DIR, '.post_explanations_cache.json')


# ── Fetch helpers ────────────────────────────────────────────────────────────

def _fetch_instagram():
    if not os.getenv('META_ACCESS_TOKEN') or not os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID'):
        print("  Skipping Instagram — META_ACCESS_TOKEN / INSTAGRAM_BUSINESS_ACCOUNT_ID not in .env")
        return []
    from meta_fetcher import get_instagram_data
    return get_instagram_data()


def _fetch_facebook():
    if not os.getenv('META_ACCESS_TOKEN') or not os.getenv('FACEBOOK_PAGE_ID'):
        print("  Skipping Facebook — META_ACCESS_TOKEN / FACEBOOK_PAGE_ID not in .env")
        return []
    from meta_fetcher import get_facebook_data
    return get_facebook_data()


def _fetch_tiktok():
    if not os.getenv('TIKTOK_CLIENT_KEY') or not os.getenv('TIKTOK_CLIENT_SECRET'):
        return []
    from tiktok_fetcher import get_tiktok_data
    return get_tiktok_data()


# ── Post explanations (Claude Haiku, cached per video URL) ───────────────────

def _generate_post_explanations(videos):
    """Generate AI bullet-point explanations for best/worst posts. Cached by URL."""
    import anthropic

    today = datetime.now().strftime('%Y-%m-%d')

    # Load existing cache
    cache = {}
    if os.path.exists(_EXPLANATIONS_CACHE):
        try:
            with open(_EXPLANATIONS_CACHE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    if not videos:
        return {}

    # Sort by views to find best and worst
    sorted_by_views = sorted(videos, key=lambda v: v.get('views', 0), reverse=True)
    best = sorted_by_views[:3]
    worst = sorted_by_views[-3:] if len(sorted_by_views) >= 5 else []

    to_explain = [(v, 'best') for v in best] + [(v, 'worst') for v in worst]

    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    for video, post_type in to_explain:
        url = video.get('url', '')
        cache_key = url

        # Skip if already cached for today
        if cache.get(cache_key, {}).get('date') == today:
            continue

        metrics_summary = (
            f"Platform: {video.get('platform')}, "
            f"Views: {video.get('views', 0):,}, "
            f"Likes: {video.get('likes', 0):,}, "
            f"Comments: {video.get('comments', 0):,}, "
            f"Shares: {video.get('shares', 0):,}, "
            f"Engagement Rate: {video.get('engagement_rate', 0):.2f}%, "
            f"CTR: {video.get('ctr_pct', 0):.2f}%, "
            f"Avg Retention: {video.get('avg_view_pct', 0):.1f}%"
        )

        performance = "performed very well (top views)" if post_type == 'best' else "underperformed (lowest views)"

        prompt = (
            f"A social media post titled \"{video.get('title', 'Untitled')}\" {performance}.\n"
            f"Metrics: {metrics_summary}\n\n"
            f"In exactly 3 short bullet points, explain specifically why this post "
            f"{'worked well' if post_type == 'best' else 'underperformed'} based on the data. "
            f"Be direct and specific. Return only the 3 bullet points, each starting with •"
        )

        try:
            response = client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=200,
                messages=[{'role': 'user', 'content': prompt}]
            )
            raw = response.content[0].text.strip()
            bullets = [line.strip().lstrip('•').strip() for line in raw.split('\n') if line.strip()]
            cache[cache_key] = {
                'date': today,
                'type': post_type,
                'reasons': bullets[:3]
            }
        except Exception as e:
            print(f"  Warning: Could not generate explanation for '{video.get('title', '')}': {e}")

    # Save updated cache
    try:
        with open(_EXPLANATIONS_CACHE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return cache


# ── Trends (YouTube search + Claude Haiku, cached daily) ────────────────────

def _generate_trends():
    """Search YouTube for real trending videos in the niche, then analyze with Claude."""
    import anthropic

    today = datetime.now().strftime('%Y-%m-%d')

    # Check cache
    if os.path.exists(_TRENDS_CACHE):
        try:
            with open(_TRENDS_CACHE, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            if cached.get('date') == today:
                print("  → Trends loaded from cache")
                return cached.get('trends', [])
        except Exception:
            pass

    niche = os.getenv('CONTENT_NICHE', 'videography video editing tutorial')
    print(f"  → Searching YouTube for: \"{niche}\"")

    trends = []

    # Search YouTube for real trending videos
    try:
        from auth import get_credentials
        from googleapiclient.discovery import build

        creds = get_credentials()
        youtube = build('youtube', 'v3', credentials=creds)

        search_resp = youtube.search().list(
            q=niche,
            type='video',
            order='viewCount',
            maxResults=5,
            part='snippet',
            videoDuration='medium',  # 4–20 minutes (not shorts)
            relevanceLanguage='en'
        ).execute()

        results = search_resp.get('items', [])

        # Get view counts for each result
        if results:
            video_ids = [item['id']['videoId'] for item in results]
            stats_resp = youtube.videos().list(
                part='statistics',
                id=','.join(video_ids)
            ).execute()
            stats_map = {item['id']: int(item['statistics'].get('viewCount', 0))
                         for item in stats_resp.get('items', [])}

            # Sort by view count, pick top 2
            results_with_views = [
                (item, stats_map.get(item['id']['videoId'], 0))
                for item in results
            ]
            results_with_views.sort(key=lambda x: x[1], reverse=True)
            top_two = results_with_views[:2]

            client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

            for item, view_count in top_two:
                video_id = item['id']['videoId']
                title = item['snippet']['title']
                channel = item['snippet']['channelTitle']
                url = f"https://www.youtube.com/watch?v={video_id}"

                prompt = (
                    f"Here is a real YouTube video that is performing very well:\n"
                    f"Title: \"{title}\"\n"
                    f"Channel: {channel}\n"
                    f"Views: {view_count:,}\n\n"
                    f"Analyze this video for a videography and video editing content creator "
                    f"targeting beginner-to-intermediate creators. Respond with ONLY valid JSON "
                    f"in this exact format:\n"
                    f'{{"what_it_is": "2-3 sentences explaining what content trend or format this video represents", '
                    f'"why_it_works": "2-3 sentences explaining why this format gets views", '
                    f'"how_to_implement": ["step 1", "step 2", "step 3", "step 4"]}}'
                )

                try:
                    response = client.messages.create(
                        model='claude-haiku-4-5-20251001',
                        max_tokens=400,
                        messages=[{'role': 'user', 'content': prompt}]
                    )
                    raw = response.content[0].text.strip()
                    # Strip markdown code blocks if present
                    if raw.startswith('```'):
                        raw = raw.split('\n', 1)[1].rsplit('```', 1)[0].strip()
                    analysis = json.loads(raw)
                    trends.append({
                        'title': title,
                        'url': url,
                        'channel': channel,
                        'views': view_count,
                        'what_it_is': analysis.get('what_it_is', ''),
                        'why_it_works': analysis.get('why_it_works', ''),
                        'how_to_implement': analysis.get('how_to_implement', [])
                    })
                    print(f"  → Analyzed: {title[:50]}...")
                except Exception as e:
                    print(f"  Warning: Could not analyze trend video '{title[:40]}': {e}")

    except Exception as e:
        print(f"  Warning: YouTube trend search failed ({type(e).__name__}): {e}")
        print("  Trends tab will be empty until YouTube auth is available.")

    # Save cache
    try:
        with open(_TRENDS_CACHE, 'w', encoding='utf-8') as f:
            json.dump({'date': today, 'trends': trends}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return trends


# ── JSON export ──────────────────────────────────────────────────────────────

def _export_dashboard_json(videos, ai_insights, post_explanations, trends):
    """Write analytics_data.json for the web dashboard."""
    os.makedirs(_DASHBOARD_DIR, exist_ok=True)

    payload = {
        'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'posts': videos,
        'ai_insights': ai_insights or {},
        'post_explanations': post_explanations or {},
        'trends': trends or []
    }

    with open(_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, default=str)

    print(f"  → Exported: {_JSON_PATH}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    try:
        import sys as _sys, os as _os
        _sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', 'shared'))
        from usage_logger import log_run
        log_run("social-media-analytics")
    except Exception:
        pass

    print("=" * 55)
    print("    Social Media Analytics Dashboard")
    print("=" * 55)

    # 1. Fetch all platforms
    print("\n[1/5] Fetching data from all platforms...")

    print("  → YouTube")
    try:
        yt_videos = get_youtube_data()
    except Exception as e:
        print(f"  YouTube skipped — auth error ({type(e).__name__}). Re-run auth.py to fix.")
        yt_videos = []

    print("  → Instagram")
    ig_videos = _fetch_instagram()

    print("  → Facebook")
    fb_videos = _fetch_facebook()

    print("  → TikTok")
    tt_videos = _fetch_tiktok()

    videos = yt_videos + ig_videos + fb_videos + tt_videos

    # Compute engagement_rate for every post
    for v in videos:
        if v.get('views', 0) > 0:
            v['engagement_rate'] = round(
                (v.get('likes', 0) + v.get('comments', 0) + v.get('shares', 0)) / v['views'] * 100, 1
            )
        else:
            v['engagement_rate'] = 0.0

    if not videos:
        print("No data fetched from any platform. Exiting.")
        return

    platforms = sorted(set(v['platform'] for v in videos))
    print(f"\n  Total: {len(videos)} posts/videos across {len(platforms)} platform(s): {', '.join(platforms)}")

    # 2. Get AI insights (single Haiku call, cached daily)
    print("\n[2/5] Generating AI sheet insights...")
    ai_insights = get_sheet_insights(videos)

    # 3. Generate post explanations (best/worst, cached per URL)
    print("\n[3/5] Generating best/worst post explanations...")
    post_explanations = _generate_post_explanations(videos)
    print(f"  → {len(post_explanations)} posts explained")

    # 4. Generate trends (YouTube search + Claude, cached daily)
    print("\n[4/5] Generating trend recommendations...")
    trends = _generate_trends()
    print(f"  → {len(trends)} trends found")

    # 4.5. Export JSON for web dashboard
    print("\n  Exporting JSON for web dashboard...")
    _export_dashboard_json(videos, ai_insights, post_explanations, trends)

    # 5. Write to Google Sheets (all tabs)
    print("\n[5/5] Writing to Google Sheets...")
    spreadsheet = write_video_data(videos, ai_insights=ai_insights)

    # (Background) Deep AI analysis → Notion
    analyze_and_write(spreadsheet, videos)

    print("\n" + "=" * 55)
    print("    All done!")
    print(f"    Sheet: {spreadsheet.url}")
    print(f"    Dashboard: open web-apps/social-media-analytics/index.html")
    print("=" * 55)


if __name__ == '__main__':
    main()
