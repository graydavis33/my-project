"""
Outlier detection: rank videos by views-to-subscribers ratio.
A 500k view video on a 10k sub channel is a bigger outlier than
500k views on a 2M sub channel.
"""

MIN_VIEWS = 1_000
MAX_DURATION_SECONDS = 180  # 3 minutes — exclude longform videos


def score_and_rank(videos: list[dict], top_n: int = 10) -> list[dict]:
    """
    Filter, score, and return top_n outlier videos.
    Adds 'outlier_score' field (views / max(subscribers, 1)).
    """
    # Filter out micro-videos and longform videos
    filtered = [
        v for v in videos
        if v.get('views', 0) >= MIN_VIEWS
        and v.get('duration_seconds', 0) <= MAX_DURATION_SECONDS
        and v.get('duration_seconds', 0) > 10
    ]

    for v in filtered:
        subs = max(v.get('subscribers', 0), 1)
        v['outlier_score'] = round(v['views'] / subs, 2)

    filtered.sort(key=lambda v: v['outlier_score'], reverse=True)
    return filtered[:top_n]
