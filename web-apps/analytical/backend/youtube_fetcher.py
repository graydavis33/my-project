"""
YouTubeFetcher — takes access_token + refresh_token, returns structured stats dict.
Refactored from python-scripts/social-media-analytics/youtube_fetcher.py.
"""
import re
import os
import requests
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


YOUTUBE_TOKEN_URI = 'https://oauth2.googleapis.com/token'


def _parse_duration(duration_str):
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str or 'PT0S')
    if not match:
        return 0
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    return h * 3600 + m * 60 + s


def _format_duration(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class YouTubeFetcher:
    def __init__(self, access_token, refresh_token, client_id=None, client_secret=None,
                 on_token_refresh=None):
        """
        access_token    — current OAuth access token
        refresh_token   — OAuth refresh token
        client_id       — YouTube OAuth client ID (reads from env if not provided)
        client_secret   — YouTube OAuth client secret (reads from env if not provided)
        on_token_refresh — optional callback(new_access_token, new_refresh_token) called
                           when a token refresh happens, so the caller can update the DB
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id or os.getenv('YOUTUBE_CLIENT_ID', '')
        self.client_secret = client_secret or os.getenv('YOUTUBE_CLIENT_SECRET', '')
        self.on_token_refresh = on_token_refresh

    def _get_credentials(self):
        creds = Credentials(
            token=self.access_token,
            refresh_token=self.refresh_token,
            token_uri=YOUTUBE_TOKEN_URI,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=[
                'https://www.googleapis.com/auth/youtube.readonly',
                'https://www.googleapis.com/auth/yt-analytics.readonly',
            ]
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self.access_token = creds.token
            if self.on_token_refresh:
                self.on_token_refresh(creds.token, creds.refresh_token)
        return creds

    def fetch_stats(self):
        """
        Returns:
        {
          channel_name: str,
          subscriber_count: int,
          videos: [
            {
              id, title, views, likes, comments, shares,
              published_at, duration, duration_seconds,
              is_short, url, watch_time_minutes,
              avg_view_pct, impressions, ctr_pct,
              subscribers_gained, platform
            }
          ]
        }
        """
        creds = self._get_credentials()
        youtube = build('youtube', 'v3', credentials=creds)

        # Channel info
        ch_resp = youtube.channels().list(
            part='id,snippet,contentDetails,statistics', mine=True
        ).execute()

        if not ch_resp.get('items'):
            return {'channel_name': '', 'subscriber_count': 0, 'videos': []}

        channel = ch_resp['items'][0]
        channel_id = channel['id']
        channel_name = channel['snippet']['title']
        subscriber_count = int(channel['statistics'].get('subscriberCount', 0))
        uploads_playlist = channel['contentDetails']['relatedPlaylists']['uploads']

        # Collect all video IDs
        video_ids = []
        page_token = None
        while True:
            resp = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=uploads_playlist,
                maxResults=50,
                pageToken=page_token
            ).execute()
            video_ids += [item['contentDetails']['videoId'] for item in resp['items']]
            page_token = resp.get('nextPageToken')
            if not page_token:
                break

        # Get video metadata in batches of 50
        videos_map = {}
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i + 50]
            resp = youtube.videos().list(
                part='snippet,statistics,contentDetails,status',
                id=','.join(batch)
            ).execute()
            for item in resp['items']:
                if item.get('status', {}).get('privacyStatus') != 'public':
                    continue
                vid_id = item['id']
                snippet = item['snippet']
                stats = item.get('statistics', {})
                duration_sec = _parse_duration(item['contentDetails'].get('duration', 'PT0S'))
                description = snippet.get('description', '')
                is_short = '#shorts' in (snippet['title'] + ' ' + description).lower() or duration_sec <= 180
                videos_map[vid_id] = {
                    'platform': 'YouTube',
                    'id': vid_id,
                    'title': snippet['title'],
                    'published_at': snippet['publishedAt'][:10],
                    'duration': _format_duration(duration_sec),
                    'duration_seconds': duration_sec,
                    'is_short': is_short,
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'comments': int(stats.get('commentCount', 0)),
                    'shares': 0,
                    'url': f"https://youtu.be/{vid_id}",
                    'watch_time_minutes': 0.0,
                    'avg_view_pct': 0.0,
                    'impressions': 0,
                    'ctr_pct': 0.0,
                    'subscribers_gained': 0,
                }

        # Fetch analytics data
        try:
            analytics = build('youtubeAnalytics', 'v2', credentials=creds)
            end_date = datetime.now().strftime('%Y-%m-%d')
            try:
                a_resp = analytics.reports().query(
                    ids=f'channel=={channel_id}',
                    startDate='2005-01-01',
                    endDate=end_date,
                    dimensions='video',
                    metrics='views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,'
                            'likes,comments,shares,subscribersGained,impressions,impressionsClickThroughRate',
                    maxResults=500,
                    sort='-views'
                ).execute()
                has_impressions = True
            except Exception:
                a_resp = analytics.reports().query(
                    ids=f'channel=={channel_id}',
                    startDate='2005-01-01',
                    endDate=end_date,
                    dimensions='video',
                    metrics='views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,'
                            'likes,comments,shares,subscribersGained',
                    maxResults=500,
                    sort='-views'
                ).execute()
                has_impressions = False

            min_cols = 11 if has_impressions else 9
            for row in a_resp.get('rows', []):
                if len(row) < min_cols:
                    continue
                vid_id = row[0]
                if vid_id in videos_map:
                    videos_map[vid_id].update({
                        'views': int(row[1]),
                        'watch_time_minutes': round(float(row[2]), 1),
                        'avg_view_pct': round(float(row[4]), 1),
                        'likes': int(row[5]),
                        'comments': int(row[6]),
                        'shares': int(row[7]),
                        'subscribers_gained': int(row[8]),
                    })
                    if has_impressions:
                        videos_map[vid_id]['impressions'] = int(row[9])
                        videos_map[vid_id]['ctr_pct'] = round(float(row[10]) * 100, 2)
        except Exception:
            pass  # Fall back to basic stats from videos.list

        videos = sorted(videos_map.values(), key=lambda x: x['published_at'], reverse=True)
        return {
            'channel_name': channel_name,
            'subscriber_count': subscriber_count,
            'videos': videos,
        }
