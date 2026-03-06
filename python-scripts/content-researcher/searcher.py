"""
YouTube search: generate query variants → search → fetch metadata + subscriber counts.
"""
import os
import sys
import re
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import anthropic

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

_DIR = os.path.dirname(__file__)
_CLIENT_SECRET = os.path.join(_DIR, '..', 'social-media-analytics', 'client_secret.json')
_TOKEN_PATH = os.path.join(_DIR, 'token.json')
_SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

RESULTS_PER_QUERY = 15
NUM_QUERIES = 4


def _get_youtube():
    creds = None
    if os.path.exists(_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(_TOKEN_PATH, _SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(_CLIENT_SECRET):
                print(f"ERROR: client_secret.json not found at {_CLIENT_SECRET}")
                print("Copy it from python-scripts/social-media-analytics/")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(_CLIENT_SECRET, _SCOPES)
            creds = flow.run_local_server(port=0)
        with open(_TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)


def generate_queries(concept: str) -> list[str]:
    """Use Claude Haiku to generate NUM_QUERIES YouTube search variants."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        # Fallback: just use the concept as-is
        return [concept]

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": (
                f"Generate {NUM_QUERIES} distinct YouTube search queries for finding videos similar to this concept:\n"
                f'"{concept}"\n\n'
                "Return ONLY the queries, one per line. No numbering, no explanation. "
                "Vary the angle: include the original concept, a how-to variant, "
                "a niche-specific variant, and a broader trend variant."
            )
        }]
    )
    lines = [ln.strip() for ln in msg.content[0].text.strip().splitlines() if ln.strip()]
    # Always include the raw concept
    if concept not in lines:
        lines = [concept] + lines[:NUM_QUERIES - 1]
    return lines[:NUM_QUERIES]


def _parse_duration(iso: str) -> int:
    """Convert ISO 8601 duration (PT4M13S) to seconds."""
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso or '')
    if not m:
        return 0
    h, mins, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mins * 60 + s


def _format_duration(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def search_videos(queries: list[str]) -> list[dict]:
    """
    Search YouTube for each query, fetch video metadata, deduplicate.
    Returns list of video dicts with: video_id, channel_id, title, views,
    likes, comments, duration, duration_seconds, published_at, description, url
    """
    youtube = _get_youtube()
    seen_ids = set()
    video_ids = []

    for query in queries:
        try:
            resp = youtube.search().list(
                q=query,
                type='video',
                maxResults=RESULTS_PER_QUERY,
                part='id',
                relevanceLanguage='en',
                videoDefinition='high',
            ).execute()
            for item in resp.get('items', []):
                vid = item['id']['videoId']
                if vid not in seen_ids:
                    seen_ids.add(vid)
                    video_ids.append(vid)
        except Exception as e:
            print(f"  [search] Query failed ({query}): {e}")

    if not video_ids:
        return []

    # Fetch metadata in batches of 50
    videos = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        try:
            resp = youtube.videos().list(
                id=','.join(batch),
                part='snippet,statistics,contentDetails,status',
            ).execute()
            for item in resp.get('items', []):
                if item.get('status', {}).get('privacyStatus') != 'public':
                    continue
                stats = item.get('statistics', {})
                snippet = item.get('snippet', {})
                dur_sec = _parse_duration(item.get('contentDetails', {}).get('duration', ''))
                videos.append({
                    'video_id': item['id'],
                    'channel_id': snippet.get('channelId', ''),
                    'channel_name': snippet.get('channelTitle', ''),
                    'title': snippet.get('title', ''),
                    'description': (snippet.get('description', '') or '')[:300],
                    'published_at': snippet.get('publishedAt', '')[:10],
                    'duration': _format_duration(dur_sec),
                    'duration_seconds': dur_sec,
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'comments': int(stats.get('commentCount', 0)),
                    'subscribers': 0,  # filled in by fetch_subscriber_counts
                    'url': f"https://youtu.be/{item['id']}",
                })
        except Exception as e:
            print(f"  [videos.list] Batch failed: {e}")

    return videos


def fetch_subscriber_counts(videos: list[dict]) -> list[dict]:
    """Add 'subscribers' field to each video dict via channels.list."""
    if not videos:
        return videos

    youtube = _get_youtube()
    channel_ids = list({v['channel_id'] for v in videos if v['channel_id']})
    sub_map = {}

    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i:i + 50]
        try:
            resp = youtube.channels().list(
                id=','.join(batch),
                part='statistics',
            ).execute()
            for item in resp.get('items', []):
                cid = item['id']
                sub_map[cid] = int(item.get('statistics', {}).get('subscriberCount', 0))
        except Exception as e:
            print(f"  [channels.list] Batch failed: {e}")

    for v in videos:
        v['subscribers'] = sub_map.get(v['channel_id'], 0)

    return videos
