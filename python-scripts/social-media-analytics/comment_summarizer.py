"""
On-demand comment summarizer.
Run: python comment_summarizer.py
Pick a video, Claude summarizes the comments and saves to the sheet.
"""
import os
import json
import gspread
import anthropic
from dotenv import load_dotenv
from datetime import datetime
from googleapiclient.discovery import build
from auth import get_credentials

load_dotenv()

MAX_COMMENTS = 100
SUMMARY_CACHE_FILE = os.path.join(os.path.dirname(__file__), '.comment_summary_cache.json')


def _load_summary_cache():
    if os.path.exists(SUMMARY_CACHE_FILE):
        try:
            with open(SUMMARY_CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_summary_cache(cache):
    with open(SUMMARY_CACHE_FILE, 'w') as f:
        json.dump(cache, f)


def _safe_text(text, max_len=300):
    """Sanitize user-controlled text before inserting into Claude prompts."""
    if not isinstance(text, str):
        return ''
    return text.replace('\n', ' ').replace('\r', ' ')[:max_len]


def fetch_comments(youtube, video_id):
    """Fetch top-level comments ordered by relevance."""
    comments = []
    page_token = None
    try:
        while len(comments) < MAX_COMMENTS:
            resp = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=min(100, MAX_COMMENTS - len(comments)),
                pageToken=page_token,
                order='relevance'
            ).execute()
            for item in resp.get('items', []):
                snippet = item.get('snippet', {}).get('topLevelComment', {}).get('snippet', {})
                if not snippet:
                    continue
                comments.append({
                    'text': snippet.get('textDisplay', '')[:300],
                    'likes': snippet.get('likeCount', 0),
                    'author': snippet.get('authorDisplayName', 'Anonymous'),
                })
            page_token = resp.get('nextPageToken')
            if not page_token:
                break
    except Exception as e:
        if 'disabled' in str(e).lower():
            print("Comments are disabled for this video.")
        else:
            print(f"Error fetching comments: {type(e).__name__}")
    return comments


def summarize_with_claude(video_title, comments):
    """Send comments to Claude and get a structured summary."""
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY', ''))

    safe_title = _safe_text(video_title, 120)
    comment_block = '\n'.join(
        f"[{c['likes']} likes] {_safe_text(c['author'], 50)}: {_safe_text(c['text'], 300)}"
        for c in comments
    )

    prompt = f"""Analyze the audience comments for this YouTube video.
<video_title>{safe_title}</video_title>

Top {len(comments)} comments:
<comments>
{comment_block}
</comments>

Provide a structured analysis:
1. **Overall Sentiment** — Positive / Negative / Mixed and why
2. **Main Themes** — What topics keep coming up?
3. **What They Loved** — Specific praise or moments viewers called out
4. **Criticism / Suggestions** — Any complaints or requests?
5. **Actionable Takeaways** — What should the creator do more or less of based on this feedback?

Be concise and specific. Reference actual comments where relevant."""

    response = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=1000,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.content[0].text


def save_to_sheet(summary, video_title, video_id):
    """Update the AI Summary columns in the Comments tab for this video."""
    creds = get_credentials()
    gc = gspread.authorize(creds)
    sheet_id = os.getenv('SHEET_ID', '').strip()
    if not sheet_id:
        print("No SHEET_ID in .env — summary not saved to sheet.")
        return

    spreadsheet = gc.open_by_key(sheet_id)
    try:
        ws = spreadsheet.worksheet('Comments')
    except gspread.WorksheetNotFound:
        print("'Comments' tab not found. Run main.py first to create it.")
        return

    headers = ws.row_values(1)
    try:
        url_col     = headers.index('URL') + 1
        summary_col = headers.index('AI Summary') + 1
        date_col    = headers.index('Summary Generated At') + 1
    except ValueError:
        print("'Comments' tab is missing expected columns. Run main.py first.")
        return

    url = f"https://youtu.be/{video_id}"
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    all_urls = ws.col_values(url_col)
    for i, row_url in enumerate(all_urls[1:], start=2):  # skip header row
        if row_url == url:
            ws.update_cell(i, summary_col, summary)
            ws.update_cell(i, date_col, now)
            print(f"Summary saved to Comments tab for: {video_title}")
            return

    print("Video not found in Comments tab. Run main.py to refresh the tab first.")


def main():
    creds = get_credentials()
    youtube = build('youtube', 'v3', credentials=creds)

    # Get uploads playlist
    ch = youtube.channels().list(part='contentDetails', mine=True).execute()
    uploads_id = ch['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    resp = youtube.playlistItems().list(
        part='contentDetails,snippet', playlistId=uploads_id, maxResults=50
    ).execute()

    all_videos = [
        {'video_id': item['contentDetails']['videoId'], 'title': item['snippet']['title']}
        for item in resp['items']
    ]

    # Filter to public only
    ids = ','.join(v['video_id'] for v in all_videos)
    details = youtube.videos().list(part='status', id=ids).execute()
    public_ids = {i['id'] for i in details['items'] if i['status']['privacyStatus'] == 'public'}
    videos = [v for v in all_videos if v['video_id'] in public_ids]

    print("\nWhich video do you want to summarize comments for?\n")
    for i, v in enumerate(videos, 1):
        print(f"  {i}. {v['title']}")

    print("\nEnter a number:")
    try:
        choice = int(input("> ").strip()) - 1
        if not 0 <= choice < len(videos):
            print("Invalid selection.")
            return
    except (ValueError, EOFError):
        print("Invalid input.")
        return

    video = videos[choice]

    # Check disk cache before calling Claude
    cache = _load_summary_cache()
    if video['video_id'] in cache:
        print(f"\nLoaded cached summary for: {video['title']}")
        summary = cache[video['video_id']]['summary']
        print("\n" + "=" * 50)
        print(summary)
        print("=" * 50 + "\n")
        save_to_sheet(summary, video['title'], video['video_id'])
        return

    print(f"\nFetching up to {MAX_COMMENTS} comments for: {video['title']}")
    comments = fetch_comments(youtube, video['video_id'])

    if not comments:
        print("No comments to summarize.")
        return

    print(f"Got {len(comments)} comments. Generating summary...")
    summary = summarize_with_claude(video['title'], comments)

    # Cache result to disk
    cache[video['video_id']] = {'summary': summary, 'title': video['title'], 'cached_at': datetime.now().strftime('%Y-%m-%d')}
    _save_summary_cache(cache)

    print("\n" + "=" * 50)
    print(summary)
    print("=" * 50 + "\n")

    save_to_sheet(summary, video['title'], video['video_id'])


if __name__ == '__main__':
    main()
