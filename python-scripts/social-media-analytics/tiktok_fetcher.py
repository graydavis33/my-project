"""
Fetches all TikTok videos for the authenticated user via TikTok Display API.
Requires: TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET in .env
          tiktok_token.json created by running: python tiktok_auth.py
"""
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_URL = 'https://open.tiktokapis.com/v2/video/list/'
FIELDS  = 'id,title,share_url,create_time,duration,view_count,like_count,comment_count,share_count'


def _format_duration(seconds):
    if not seconds:
        return '0:00'
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _fetch_page(access_token, cursor):
    """POST one page of videos. Returns raw response."""
    return requests.post(
        API_URL,
        params={'fields': FIELDS},
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type':  'application/json',
        },
        json={'max_count': 20, 'cursor': cursor},
        timeout=20
    )


def get_tiktok_data():
    """Fetch all TikTok videos for the authenticated user."""
    from tiktok_auth import get_tiktok_token, refresh_token, _load_token

    client_key    = os.getenv('TIKTOK_CLIENT_KEY', '').strip()
    client_secret = os.getenv('TIKTOK_CLIENT_SECRET', '').strip()
    if not client_key or not client_secret:
        print("Skipping TikTok — TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET not set in .env")
        return []

    try:
        access_token, token_data = get_tiktok_token()
    except FileNotFoundError as e:
        print(f"Skipping TikTok — {e}")
        return []

    videos = []
    cursor   = 0
    has_more = True

    while has_more:
        resp = _fetch_page(access_token, cursor)

        # Token expired — refresh once and retry
        if resp.status_code == 401:
            print("TikTok token expired — refreshing...")
            token_data   = _load_token()
            token_data   = refresh_token(token_data)
            access_token = token_data['access_token']
            resp         = _fetch_page(access_token, cursor)

        resp.raise_for_status()
        body = resp.json()
        data = body.get('data', {})

        for item in data.get('videos', []):
            ts        = item.get('create_time', 0)
            published = datetime.fromtimestamp(ts).strftime('%Y-%m-%d') if ts else ''
            dur_sec   = int(item.get('duration', 0))
            title     = (item.get('title') or '').strip() or f"TikTok {item.get('id', '')}"

            videos.append({
                'platform':              'TikTok',
                'title':                 title,
                'url':                   item.get('share_url', ''),
                'published_date':        published,
                'duration':              _format_duration(dur_sec),
                'views':                 int(item.get('view_count', 0)),
                'likes':                 int(item.get('like_count', 0)),
                'comments':              int(item.get('comment_count', 0)),
                'shares':                int(item.get('share_count', 0)),
                'impressions':           0,
                'ctr_pct':               0.0,
                'watch_time_minutes':    0.0,
                'avg_view_duration_sec': 0,
                'avg_view_pct':          0.0,
                'subscribers_gained':    0,
            })

        has_more = data.get('has_more', False)
        cursor   = data.get('cursor', 0)

    print(f"TikTok: {len(videos)} videos fetched.")
    return videos
