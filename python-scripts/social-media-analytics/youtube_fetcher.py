import re
from datetime import datetime
from googleapiclient.discovery import build
from auth import get_credentials


def parse_duration(duration_str):
    """Convert ISO 8601 duration (e.g. PT4M13S) to total seconds."""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str or 'PT0S')
    if not match:
        return 0
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    return h * 3600 + m * 60 + s


def format_duration(seconds):
    """Format seconds as H:MM:SS or M:SS."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def get_youtube_data():
    """Fetch all YouTube video analytics for the authenticated user's channel."""
    creds = get_credentials()
    youtube = build('youtube', 'v3', credentials=creds)
    analytics = build('youtubeAnalytics', 'v2', credentials=creds)

    # Get channel info + uploads playlist ID
    ch_resp = youtube.channels().list(
        part='id,snippet,contentDetails', mine=True
    ).execute()

    if not ch_resp.get('items'):
        print("ERROR: No YouTube channel found for this Google account.")
        return []

    channel = ch_resp['items'][0]
    channel_id = channel['id']
    channel_name = channel['snippet']['title']
    uploads_playlist = channel['contentDetails']['relatedPlaylists']['uploads']
    print(f"Channel: {channel_name}")

    # Collect all video IDs from the uploads playlist (1 quota unit per page vs 100 for search)
    print("Collecting video list...")
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

    print(f"Found {len(video_ids)} videos.")

    # Get video metadata in batches of 50
    videos_map = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        resp = youtube.videos().list(
            part='snippet,statistics,contentDetails,status',
            id=','.join(batch)
        ).execute()
        for item in resp['items']:
            # Skip private and unlisted videos
            if item.get('status', {}).get('privacyStatus') != 'public':
                continue
            vid_id = item['id']
            snippet = item['snippet']
            stats = item.get('statistics', {})
            duration_sec = parse_duration(item['contentDetails'].get('duration', 'PT0S'))
            description = snippet.get('description', '')
            # Shorts: #shorts hashtag OR duration <= 3 minutes (covers older untagged Shorts)
            is_short = '#shorts' in (snippet['title'] + ' ' + description).lower() or duration_sec <= 180
            videos_map[vid_id] = {
                'platform': 'YouTube',
                'video_id': vid_id,
                'title': snippet['title'],
                'description': description,
                'is_short': is_short,
                'published_date': snippet['publishedAt'][:10],
                'duration': format_duration(duration_sec),
                'duration_seconds': duration_sec,
                'views': int(stats.get('viewCount', 0)),
                'likes': int(stats.get('likeCount', 0)),
                'comments': int(stats.get('commentCount', 0)),
                'watch_time_minutes': 0.0,
                'avg_view_duration_sec': 0,
                'avg_view_pct': 0.0,
                'impressions': 0,
                'ctr_pct': 0.0,
                'shares': 0,
                'subscribers_gained': 0,
                'url': f"https://youtu.be/{vid_id}",
            }

    # Get analytics data for all videos at once
    print("Fetching analytics (views, watch time, CTR, etc.)...")
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')

        # Try with impressions + CTR first; some accounts don't have access to these
        try:
            a_resp = analytics.reports().query(
                ids=f'channel=={channel_id}',
                startDate='2005-01-01',
                endDate=end_date,
                dimensions='video',
                metrics='views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,'
                        'likes,comments,shares,subscribersGained,impressions,impressionsClickThroughRate',
                maxResults=200,
                sort='-views'
            ).execute()
            has_impressions = True
            print("Impressions and CTR data available.")
        except Exception:
            a_resp = analytics.reports().query(
                ids=f'channel=={channel_id}',
                startDate='2005-01-01',
                endDate=end_date,
                dimensions='video',
                metrics='views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,'
                        'likes,comments,shares,subscribersGained',
                maxResults=200,
                sort='-views'
            ).execute()
            has_impressions = False
            print("Note: Impressions/CTR not available for this account — other metrics will still be fetched.")

        for row in a_resp.get('rows', []):
            vid_id = row[0]
            if vid_id in videos_map:
                update = {
                    'views': int(row[1]),
                    'watch_time_minutes': round(float(row[2]), 1),
                    'avg_view_duration_sec': int(row[3]),
                    'avg_view_pct': round(float(row[4]), 1),
                    'likes': int(row[5]),
                    'comments': int(row[6]),
                    'shares': int(row[7]),
                    'subscribers_gained': int(row[8]),
                }
                if has_impressions:
                    update['impressions'] = int(row[9])
                    update['ctr_pct'] = round(float(row[10]) * 100, 2)
                videos_map[vid_id].update(update)

    except Exception as e:
        print(f"Warning: Analytics API error: {e}")
        print("Proceeding with basic stats only (views, likes, comments).")

    videos = sorted(videos_map.values(), key=lambda x: x['published_date'], reverse=True)
    print(f"Done. Got data for {len(videos)} videos.")
    return videos
