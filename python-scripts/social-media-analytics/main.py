import os
import sys
from dotenv import load_dotenv

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


def _fetch_instagram():
    if not os.getenv('META_EMAIL') or not os.getenv('IG_USERNAME'):
        return []
    from meta_scraper import get_instagram_data
    return get_instagram_data()


def _fetch_facebook():
    if not os.getenv('META_EMAIL') or not os.getenv('FB_PAGE_SLUG'):
        return []
    from meta_scraper import get_facebook_data
    return get_facebook_data()


def _fetch_tiktok():
    if not os.getenv('TIKTOK_CLIENT_KEY') or not os.getenv('TIKTOK_CLIENT_SECRET'):
        return []
    from tiktok_fetcher import get_tiktok_data
    return get_tiktok_data()


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
    print("\n[1/4] Fetching data from all platforms...")

    print("  → YouTube")
    yt_videos = get_youtube_data()

    print("  → Instagram")
    ig_videos = _fetch_instagram()

    print("  → Facebook")
    fb_videos = _fetch_facebook()

    print("  → TikTok")
    tt_videos = _fetch_tiktok()

    videos = yt_videos + ig_videos + fb_videos + tt_videos

    if not videos:
        print("No data fetched from any platform. Exiting.")
        return

    platforms = sorted(set(v['platform'] for v in videos))
    print(f"\n  Total: {len(videos)} posts/videos across {len(platforms)} platform(s): {', '.join(platforms)}")

    # 2. Get AI insights for Sheets (single Haiku call, cached daily)
    print("\n[2/4] Generating AI sheet insights...")
    ai_insights = get_sheet_insights(videos)

    # 3. Write to Google Sheets (all tabs)
    print("\n[3/4] Writing to Google Sheets...")
    spreadsheet = write_video_data(videos, ai_insights=ai_insights)

    # 4. Deep AI analysis → Notion (Sonnet, only if Notion is configured)
    print("\n[4/4] Running deep AI analysis...")
    analyze_and_write(spreadsheet, videos)

    print("\n" + "=" * 55)
    print("    All done!")
    print(f"    Open your sheet: {spreadsheet.url}")
    print("=" * 55)


if __name__ == '__main__':
    main()
