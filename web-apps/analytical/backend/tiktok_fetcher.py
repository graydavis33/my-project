"""
TikTokFetcher — takes access_token + refresh_token, returns structured stats dict.
Refactored from python-scripts/social-media-analytics/tiktok_fetcher.py.
"""
import os
import requests
from datetime import datetime


API_URL = 'https://open.tiktokapis.com/v2/video/list/'
VIDEO_FIELDS = 'id,title,share_url,create_time,duration,view_count,like_count,comment_count,share_count'
USER_INFO_URL = 'https://open.tiktokapis.com/v2/user/info/'
USER_FIELDS = 'display_name,follower_count,following_count,likes_count'

REFRESH_URL = 'https://open.tiktokapis.com/v2/oauth/token/'


def _format_duration(seconds):
    if not seconds:
        return '0:00'
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class TikTokFetcher:
    def __init__(self, access_token, refresh_token, client_key=None, client_secret=None,
                 on_token_refresh=None):
        """
        access_token    — current TikTok Display API access token
        refresh_token   — refresh token
        client_key      — TikTok app client key (reads from env if not provided)
        client_secret   — TikTok app client secret (reads from env if not provided)
        on_token_refresh — optional callback(new_access_token, new_refresh_token)
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_key = client_key or os.getenv('TIKTOK_CLIENT_KEY', '')
        self.client_secret = client_secret or os.getenv('TIKTOK_CLIENT_SECRET', '')
        self.on_token_refresh = on_token_refresh

    def _refresh_token(self):
        resp = requests.post(
            REFRESH_URL,
            data={
                'client_key': self.client_key,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
            },
            timeout=20
        )
        resp.raise_for_status()
        data = resp.json().get('data', {})
        self.access_token = data['access_token']
        self.refresh_token = data.get('refresh_token', self.refresh_token)
        if self.on_token_refresh:
            self.on_token_refresh(self.access_token, self.refresh_token)

    def _get(self, url, params):
        resp = requests.get(url, params=params, headers={
            'Authorization': f'Bearer {self.access_token}',
        }, timeout=20)
        if resp.status_code == 401:
            self._refresh_token()
            resp = requests.get(url, params=params, headers={
                'Authorization': f'Bearer {self.access_token}',
            }, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def _post_page(self, cursor):
        resp = requests.post(
            API_URL,
            params={'fields': VIDEO_FIELDS},
            headers={
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
            },
            json={'max_count': 20, 'cursor': cursor},
            timeout=20
        )
        if resp.status_code == 401:
            self._refresh_token()
            resp = requests.post(
                API_URL,
                params={'fields': VIDEO_FIELDS},
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json',
                },
                json={'max_count': 20, 'cursor': cursor},
                timeout=20
            )
        resp.raise_for_status()
        return resp.json()

    def fetch_stats(self):
        """
        Returns:
        {
          username: str,
          follower_count: int,
          videos: [
            {
              id, title, views, likes, comments, shares,
              published_at, duration, url, platform
            }
          ]
        }
        """
        # Get user info
        username = ''
        follower_count = 0
        try:
            user_data = self._get(USER_INFO_URL, {'fields': USER_FIELDS})
            user = user_data.get('data', {}).get('user', {})
            username = user.get('display_name', '')
            follower_count = int(user.get('follower_count', 0))
        except Exception:
            pass

        # Fetch all videos with cursor pagination
        videos = []
        cursor = 0
        has_more = True

        while has_more:
            body = self._post_page(cursor)
            data = body.get('data', {})

            for item in data.get('videos', []):
                ts = item.get('create_time', 0)
                published = datetime.fromtimestamp(ts).strftime('%Y-%m-%d') if ts else ''
                dur_sec = int(item.get('duration', 0))
                title = (item.get('title') or '').strip() or f"TikTok {item.get('id', '')}"

                videos.append({
                    'platform': 'TikTok',
                    'id': item.get('id', ''),
                    'title': title,
                    'url': item.get('share_url', ''),
                    'published_at': published,
                    'duration': _format_duration(dur_sec),
                    'views': int(item.get('view_count', 0)),
                    'likes': int(item.get('like_count', 0)),
                    'comments': int(item.get('comment_count', 0)),
                    'shares': int(item.get('share_count', 0)),
                })

            has_more = data.get('has_more', False)
            cursor = data.get('cursor', 0)

        # Extract username from video URL if user.info scope wasn't granted
        if not username and videos:
            url = videos[0].get('url', '')
            if '/@' in url:
                username = url.split('/@')[1].split('/')[0]

        return {
            'username': username,
            'follower_count': follower_count,
            'videos': videos,
        }
