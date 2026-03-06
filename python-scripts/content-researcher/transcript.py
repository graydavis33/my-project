"""
Extract the hook section (first 90s) of YouTube video transcripts.
Uses youtube-transcript-api. Gracefully skips on any failure.
"""

HOOK_SECONDS = 90


def get_hook_transcript(video_id: str) -> str:
    """
    Return transcript text for first HOOK_SECONDS of the video.
    Returns empty string if transcript unavailable.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        entries = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
        hook_parts = [e['text'] for e in entries if e.get('start', 999) < HOOK_SECONDS]
        return ' '.join(hook_parts).strip()
    except Exception:
        return ''


def enrich_with_hooks(videos: list[dict]) -> list[dict]:
    """Add 'hook_transcript' field to each video. Silently skips failures."""
    for v in videos:
        hook = get_hook_transcript(v['video_id'])
        v['hook_transcript'] = hook
        status = f"({len(hook)} chars)" if hook else "(no transcript)"
        print(f"  [transcript] {v['title'][:50]}... {status}")
    return videos
