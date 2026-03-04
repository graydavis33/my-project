"""
On-demand comment summarizer.
Run: python comment_summarizer.py
Pick a video, Claude summarizes the comments and saves to the sheet.
"""
import os
import gspread
import anthropic
from dotenv import load_dotenv
from datetime import datetime
from googleapiclient.discovery import build
from auth import get_credentials

load_dotenv()

MAX_COMMENTS = 100


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
            for item in resp['items']:
                s = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'text': s['textDisplay'][:300],
                    'likes': s['likeCount'],
                    'author': s['authorDisplayName']
                })
            page_token = resp.get('nextPageToken')
            if not page_token:
                break
    except Exception as e:
        if 'disabled' in str(e).lower():
            print("Comments are disabled for this video.")
        else:
            print(f"Error fetching comments: {e}")
    return comments


def summarize_with_claude(video_title, comments):
    """Send comments to Claude and get a structured summary."""
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY', ''))

    comment_block = '\n'.join(
        f"[{c['likes']} likes] {c['author']}: {c['text']}"
        for c in comments
    )

    prompt = f"""Analyze the audience comments for the YouTube video: "{video_title}"

Top {len(comments)} comments:
{comment_block}

Provide a structured analysis:
1. **Overall Sentiment** — Positive / Negative / Mixed and why
2. **Main Themes** — What topics keep coming up?
3. **What They Loved** — Specific praise or moments viewers called out
4. **Criticism / Suggestions** — Any complaints or requests?
5. **Actionable Takeaways** — What should the creator do more or less of based on this feedback?

Be concise and specific. Reference actual comments where relevant."""

    response = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY', '')).messages.create(
        model='claude-sonnet-4-6',
        max_tokens=1000,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.content[0].text


def save_to_sheet(summary, video_title, video_id):
    """Save the summary to the Comment Summaries tab."""
    creds = get_credentials()
    gc = gspread.authorize(creds)
    sheet_id = os.getenv('SHEET_ID', '').strip()
    if not sheet_id:
        print("No SHEET_ID in .env — summary not saved to sheet.")
        return

    spreadsheet = gc.open_by_key(sheet_id)
    headers = ['Video Title', 'Video ID', 'Summary', 'Generated At']

    try:
        ws = spreadsheet.worksheet('Comment Summaries')
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet('Comment Summaries', rows=500, cols=4)
        ws.update('A1', [headers])

    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Update existing row if video already has a summary
    existing = ws.get_all_values()
    for i, row in enumerate(existing[1:], start=2):
        if len(row) > 1 and row[1] == video_id:
            ws.update(f'A{i}', [[video_title, video_id, summary, now]])
            print("Updated existing summary in sheet.")
            return

    ws.append_row([video_title, video_id, summary, now])
    print("Summary saved to 'Comment Summaries' tab.")


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
    print(f"\nFetching up to {MAX_COMMENTS} comments for: {video['title']}")
    comments = fetch_comments(youtube, video['video_id'])

    if not comments:
        print("No comments to summarize.")
        return

    print(f"Got {len(comments)} comments. Generating summary...")
    summary = summarize_with_claude(video['title'], comments)

    print("\n" + "=" * 50)
    print(summary)
    print("=" * 50 + "\n")

    save_to_sheet(summary, video['title'], video['video_id'])


if __name__ == '__main__':
    main()
