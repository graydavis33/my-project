"""
Fetches Instagram and Facebook analytics via Meta Graph API v19.0.
Both platforms use the same META_ACCESS_TOKEN (long-lived Page Access Token).

Required .env vars:
  META_ACCESS_TOKEN              — 60-day long-lived token from Graph API Explorer
  INSTAGRAM_BUSINESS_ACCOUNT_ID — IG business account ID
  FACEBOOK_PAGE_ID               — Facebook Page ID
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH = 'https://graph.facebook.com/v19.0'


def _get(path, params):
    resp = requests.get(f'{GRAPH}/{path}', params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _paginate(path, params, limit=50):
    """Yield all items across cursor-paginated Graph API responses."""
    params = {**params, 'limit': limit}
    while True:
        data = _get(path, params)
        yield from data.get('data', [])
        after = data.get('paging', {}).get('cursors', {}).get('after')
        if not after:
            break
        params = {**params, 'after': after}


# ─── Instagram ───────────────────────────────────────────────────────────────

def get_instagram_data():
    """Fetch all Instagram media + per-post insights."""
    token      = os.getenv('META_ACCESS_TOKEN', '').strip()
    account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID', '').strip()
    if not token or not account_id:
        print("Skipping Instagram — META_ACCESS_TOKEN / INSTAGRAM_BUSINESS_ACCOUNT_ID not set in .env")
        return []

    media_params = {
        'fields':       'id,timestamp,permalink,media_type,like_count,comments_count',
        'access_token': token,
    }

    posts = []
    for item in _paginate(f'{account_id}/media', media_params):
        media_id   = item['id']
        published  = item.get('timestamp', '')[:10]
        url        = item.get('permalink', '')
        likes      = int(item.get('like_count', 0))
        comments   = int(item.get('comments_count', 0))
        media_type = item.get('media_type', 'IMAGE')
        title      = f"[{media_type}] {published}"

        # Fetch per-media insights — 400 on old posts or personal accounts, skip gracefully
        insights = {'plays': 0, 'reach': 0, 'shares': 0, 'saved': 0}
        try:
            ins_resp = _get(f'{media_id}/insights', {
                'metric':       'plays,reach,impressions,shares,saved',
                'access_token': token,
            })
            for metric in ins_resp.get('data', []):
                name = metric['name']
                val  = metric.get('values')
                if isinstance(val, list) and val:
                    insights[name] = val[0].get('value', 0)
                else:
                    insights[name] = metric.get('value', 0)
        except Exception:
            pass

        views = insights.get('plays') or insights.get('reach') or 0

        posts.append({
            'platform':              'Instagram',
            'title':                 title,
            'url':                   url,
            'published_date':        published,
            'duration':              '',
            'views':                 int(views),
            'likes':                 likes,
            'comments':              comments,
            'shares':                int(insights.get('shares', 0)),
            'impressions':           int(insights.get('reach', 0)),
            'ctr_pct':               0.0,
            'watch_time_minutes':    0.0,
            'avg_view_duration_sec': 0,
            'avg_view_pct':          0.0,
            'subscribers_gained':    int(insights.get('saved', 0)),  # Saves
        })

    print(f"Instagram: {len(posts)} posts fetched.")
    return posts


# ─── Facebook ────────────────────────────────────────────────────────────────

def get_facebook_data():
    """Fetch all Facebook Page posts + per-post insights."""
    token   = os.getenv('META_ACCESS_TOKEN', '').strip()
    page_id = os.getenv('FACEBOOK_PAGE_ID', '').strip()
    if not token or not page_id:
        print("Skipping Facebook — META_ACCESS_TOKEN / FACEBOOK_PAGE_ID not set in .env")
        return []

    post_params = {
        'fields':       'id,created_time,permalink_url,message',
        'access_token': token,
    }

    _ins_map = {
        'post_impressions':          'impressions',
        'post_reactions_like_total': 'likes',
        'post_comments':             'comments',
        'post_shares':               'shares',
        'post_video_views':          'video_views',
    }

    posts = []
    for item in _paginate(f'{page_id}/posts', post_params):
        post_id   = item['id']
        published = item.get('created_time', '')[:10]
        url       = item.get('permalink_url', '')
        message   = (item.get('message') or '').replace('\n', ' ').strip()
        title     = message[:80] or f"Post {post_id}"

        ins = {'impressions': 0, 'likes': 0, 'comments': 0, 'shares': 0, 'video_views': 0}
        try:
            ins_resp = _get(f'{post_id}/insights', {
                'metric':       ','.join(_ins_map.keys()),
                'access_token': token,
            })
            for metric in ins_resp.get('data', []):
                key = _ins_map.get(metric['name'])
                if not key:
                    continue
                val = metric.get('values')
                if isinstance(val, list) and val:
                    ins[key] = val[0].get('value', 0)
                else:
                    ins[key] = metric.get('value', 0)
        except Exception:
            pass

        posts.append({
            'platform':              'Facebook',
            'title':                 title,
            'url':                   url,
            'published_date':        published,
            'duration':              '',
            'views':                 int(ins['video_views']),
            'likes':                 int(ins['likes']),
            'comments':              int(ins['comments']),
            'shares':                int(ins['shares']),
            'impressions':           int(ins['impressions']),
            'ctr_pct':               0.0,
            'watch_time_minutes':    0.0,
            'avg_view_duration_sec': 0,
            'avg_view_pct':          0.0,
            'subscribers_gained':    0,
        })

    print(f"Facebook: {len(posts)} posts fetched.")
    return posts
