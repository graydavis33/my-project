"""
youtube_fetcher.py
Fetches recent videos for a list of YouTube channels using the YouTube Data API v3.
Reuses the same OAuth2 credential pattern as social-media-analytics.
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import YOUTUBE_CREDENTIALS_PATH, YOUTUBE_TOKEN_PATH, YOUTUBE_SCOPES, VIDEOS_PER_CREATOR


def _get_youtube_service():
    creds = None
    if os.path.exists(YOUTUBE_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(YOUTUBE_TOKEN_PATH, YOUTUBE_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(YOUTUBE_CREDENTIALS_PATH, YOUTUBE_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(YOUTUBE_TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def fetch_recent_videos(channel_id: str, creator_name: str) -> list:
    """
    Fetch the most recent N videos from a channel.
    Returns a list of video dicts with title, views, likes, url, published_at.
    """
    service = _get_youtube_service()

    try:
        # Get uploads playlist ID
        channel_resp = service.channels().list(
            part="contentDetails,statistics",
            id=channel_id,
        ).execute()

        if not channel_resp.get("items"):
            return []

        channel_info = channel_resp["items"][0]
        uploads_playlist = channel_info["contentDetails"]["relatedPlaylists"]["uploads"]
        channel_subscribers = channel_info.get("statistics", {}).get("subscriberCount", "?")

        # Get recent video IDs from uploads playlist
        playlist_resp = service.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist,
            maxResults=VIDEOS_PER_CREATOR,
        ).execute()

        video_ids = [
            item["snippet"]["resourceId"]["videoId"]
            for item in playlist_resp.get("items", [])
        ]

        if not video_ids:
            return []

        # Get stats for each video
        videos_resp = service.videos().list(
            part="snippet,statistics",
            id=",".join(video_ids),
        ).execute()

        videos = []
        for item in videos_resp.get("items", []):
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            videos.append({
                "creator": creator_name,
                "channel_id": channel_id,
                "channel_subscribers": channel_subscribers,
                "title": snippet.get("title", ""),
                "published_at": snippet.get("publishedAt", "")[:10],
                "description": snippet.get("description", "")[:300],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "url": f"https://youtube.com/watch?v={item['id']}",
                "video_id": item["id"],
            })

        return sorted(videos, key=lambda v: v["views"], reverse=True)

    except Exception as e:
        print(f"  ⚠️  Failed to fetch {creator_name}: {e}")
        return []


def fetch_all_creators(creators: list) -> list:
    """Fetch recent videos for all creators. Returns flat list of all video dicts."""
    all_videos = []
    for creator in creators:
        print(f"  Fetching {creator['name']}...")
        videos = fetch_recent_videos(creator["channel_id"], creator["name"])
        all_videos.extend(videos)
        print(f"    → {len(videos)} video(s) fetched")
    return all_videos
