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


def main():
    print("=" * 55)
    print("    Social Media Analytics Dashboard")
    print("=" * 55)

    # 1. Fetch YouTube data
    print("\n[1/4] Fetching YouTube data...")
    videos = get_youtube_data()
    if not videos:
        print("No data fetched. Exiting.")
        return

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
