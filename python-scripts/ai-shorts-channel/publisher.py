"""
Handles YouTube: upload as private, make public after approval.
Reuses the OAuth pattern from social-media-analytics/auth.py.
"""

import os
from pathlib import Path
from datetime import datetime

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import YT_OAUTH_SCOPES, YT_TOKEN_FILE, YT_SECRET_FILE, CHANNEL_NAME


# ─── Auth ─────────────────────────────────────────────────────────────────────

def get_youtube():
    creds = None

    if YT_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(YT_TOKEN_FILE), YT_OAUTH_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not YT_SECRET_FILE.exists():
                raise FileNotFoundError(
                    f"\nclient_secret.json not found at:\n{YT_SECRET_FILE}\n"
                    "Download it from Google Cloud Console → APIs & Services → Credentials"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(YT_SECRET_FILE), YT_OAUTH_SCOPES)
            creds = flow.run_local_server(port=0)

        YT_TOKEN_FILE.write_text(creds.to_json())

    return build('youtube', 'v3', credentials=creds)


# ─── Upload ────────────────────────────────────────────────────────────────────

def upload_private(video_path: Path, script: dict) -> tuple[str, str]:
    """
    Upload video as private. Returns (video_id, watch_url).
    """
    yt = get_youtube()
    today = datetime.now().strftime('%Y-%m-%d')

    title       = script.get('youtube_title', f'AI News Short | {today}')
    description = _build_description(script)
    tags        = _build_tags(script)

    print(f"[youtube] Uploading as private: {title}")
    request = yt.videos().insert(
        part='snippet,status',
        body={
            'snippet': {
                'title':       title,
                'description': description,
                'tags':        tags,
                'categoryId':  '28',   # Science & Technology
            },
            'status': {
                'privacyStatus':          'private',
                'selfDeclaredMadeForKids': False,
            },
        },
        media_body=MediaFileUpload(
            str(video_path),
            mimetype='video/mp4',
            resumable=True,
            chunksize=8 * 1024 * 1024,
        ),
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"[youtube] Upload {pct}%...")

    video_id  = response['id']
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"[youtube] Uploaded private: {watch_url}")
    return video_id, watch_url


def make_public(video_id: str):
    """Change a private video to public."""
    yt = get_youtube()
    yt.videos().update(
        part='status',
        body={
            'id': video_id,
            'status': {
                'privacyStatus':          'public',
                'selfDeclaredMadeForKids': False,
            },
        },
    ).execute()
    print(f"[youtube] Published: https://www.youtube.com/watch?v={video_id}")


def delete_video(video_id: str):
    """Delete a private draft (used when rebuilding after video feedback)."""
    yt = get_youtube()
    yt.videos().delete(id=video_id).execute()
    print(f"[youtube] Deleted draft: {video_id}")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_description(script: dict) -> str:
    today = datetime.now().strftime('%B %d, %Y')
    stories_block = "\n".join(
        f"• {s['title']}" for s in script.get('stories', [])
    )
    base = script.get('description', '')
    return (
        f"{CHANNEL_NAME} | AI News — {today}\n\n"
        f"{stories_block}\n\n"
        f"{base}\n\n"
        f"#shorts #ai #ainews #artificialintelligence #tech #{CHANNEL_NAME.lower().replace(' ', '')}"
    )


def _build_tags(script: dict) -> list[str]:
    base = ['AI news', 'artificial intelligence', 'AI 2026', 'tech news', 'shorts', CHANNEL_NAME]
    for story in script.get('stories', []):
        base.extend(story.get('broll_keywords', [])[:2])
    return list(dict.fromkeys(base))[:30]   # YouTube max 30 tags, deduplicated
