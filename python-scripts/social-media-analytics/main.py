from youtube_fetcher import get_youtube_data
from sheets_writer import write_youtube_data
from ai_analyzer import analyze_and_write


def main():
    print("=" * 55)
    print("    Social Media Analytics Dashboard")
    print("=" * 55)

    # 1. Fetch YouTube data
    print("\n[1/3] Fetching YouTube data...")
    videos = get_youtube_data()
    if not videos:
        print("No data fetched. Exiting.")
        return

    # 2. Write to Google Sheets
    print("\n[2/3] Writing to Google Sheets...")
    spreadsheet = write_youtube_data(videos)

    # 3. AI Analysis
    print("\n[3/3] Running AI analysis...")
    analyze_and_write(spreadsheet, videos)

    print("\n" + "=" * 55)
    print("    All done!")
    print(f"    Open your sheet: {spreadsheet.url}")
    print("=" * 55)


if __name__ == '__main__':
    main()
