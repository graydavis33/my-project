"""
meta_fetcher.py — Instagram + Facebook analytics via Meta Graph API v19.0.
Used by the Analytical backend. Tokens are per-user, stored in SQLite.
"""
import requests

GRAPH = 'https://graph.facebook.com/v19.0'


def _get(path, params, timeout=15):
    resp = requests.get(f'{GRAPH}/{path}', params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _paginate(path, params, limit=50):
    params = {**params, 'limit': limit}
    while True:
        data = _get(path, params)
        yield from data.get('data', [])
        after = data.get('paging', {}).get('cursors', {}).get('after')
        if not after:
            break
        params = {**params, 'after': after}


# ─── Instagram ───────────────────────────────────────────────────────────────

def fetch_instagram(page_token: str, ig_account_id: str) -> dict:
    """
    Fetch Instagram account info + per-post insights.
    Returns a dict shaped like the YouTube/TikTok snapshot format.
    """
    # Account-level info
    profile = _get(ig_account_id, {
        'fields': 'name,username,followers_count,media_count,biography,website',
        'access_token': page_token,
    })

    posts = []
    media_params = {
        'fields': 'id,timestamp,permalink,media_type,like_count,comments_count,caption',
        'access_token': page_token,
    }

    for item in _paginate(f'{ig_account_id}/media', media_params):
        media_id   = item['id']
        published  = item.get('timestamp', '')[:10]
        url        = item.get('permalink', '')
        likes      = int(item.get('like_count', 0))
        comments   = int(item.get('comments_count', 0))
        media_type = item.get('media_type', 'IMAGE')
        caption    = (item.get('caption') or '').replace('\n', ' ').strip()[:100]
        title      = caption or f"[{media_type}] {published}"

        insights = {'plays': 0, 'reach': 0, 'impressions': 0, 'shares': 0, 'saved': 0}
        try:
            ins_resp = _get(f'{media_id}/insights', {
                'metric': 'plays,reach,impressions,shares,saved',
                'access_token': page_token,
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
        engagement = likes + comments + int(insights.get('shares', 0))
        eng_rate = round(engagement / views * 100, 1) if views > 0 else 0.0

        posts.append({
            'id':              media_id,
            'title':           title,
            'url':             url,
            'published_date':  published,
            'media_type':      media_type,
            'views':           int(views),
            'likes':           likes,
            'comments':        comments,
            'shares':          int(insights.get('shares', 0)),
            'saves':           int(insights.get('saved', 0)),
            'reach':           int(insights.get('reach', 0)),
            'impressions':     int(insights.get('impressions', 0)),
            'engagement_rate': eng_rate,
        })

    return {
        'username':       profile.get('username', ''),
        'display_name':   profile.get('name', ''),
        'follower_count': int(profile.get('followers_count', 0)),
        'post_count':     int(profile.get('media_count', 0)),
        'posts':          posts,
    }


# ─── Facebook ────────────────────────────────────────────────────────────────

def fetch_facebook(page_token: str, page_id: str) -> dict:
    """
    Fetch Facebook Page info + per-post insights.
    Returns a dict shaped like the YouTube/TikTok snapshot format.
    """
    # Page-level info
    page_info = _get(page_id, {
        'fields': 'name,fan_count,followers_count',
        'access_token': page_token,
    })

    posts = []
    post_params = {
        'fields': 'id,created_time,permalink_url,message',
        'access_token': page_token,
    }

    _ins_map = {
        'post_impressions':          'impressions',
        'post_reactions_like_total': 'likes',
        'post_comments':             'comments',
        'post_shares':               'shares',
        'post_video_views':          'video_views',
        'post_clicks':               'clicks',
    }

    for item in _paginate(f'{page_id}/posts', post_params):
        post_id   = item['id']
        published = item.get('created_time', '')[:10]
        url       = item.get('permalink_url', '')
        message   = (item.get('message') or '').replace('\n', ' ').strip()
        title     = message[:100] or f"Post {post_id}"

        ins = {v: 0 for v in _ins_map.values()}
        try:
            ins_resp = _get(f'{post_id}/insights', {
                'metric': ','.join(_ins_map.keys()),
                'access_token': page_token,
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

        views = int(ins['video_views']) or int(ins['impressions'])
        engagement = int(ins['likes']) + int(ins['comments']) + int(ins['shares'])
        eng_rate = round(engagement / views * 100, 1) if views > 0 else 0.0

        posts.append({
            'id':              post_id,
            'title':           title,
            'url':             url,
            'published_date':  published,
            'views':           int(ins['video_views']),
            'impressions':     int(ins['impressions']),
            'likes':           int(ins['likes']),
            'comments':        int(ins['comments']),
            'shares':          int(ins['shares']),
            'clicks':          int(ins['clicks']),
            'engagement_rate': eng_rate,
        })

    return {
        'page_name':      page_info.get('name', ''),
        'fan_count':      int(page_info.get('fan_count', 0)),
        'follower_count': int(page_info.get('followers_count', 0)),
        'posts':          posts,
    }


# ─── OAuth Helpers ───────────────────────────────────────────────────────────

def exchange_code_for_token(code: str, app_id: str, app_secret: str, redirect_uri: str) -> str:
    """Exchange an auth code for a short-lived user access token."""
    resp = requests.get(f'{GRAPH}/oauth/access_token', params={
        'client_id':     app_id,
        'client_secret': app_secret,
        'redirect_uri':  redirect_uri,
        'code':          code,
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()['access_token']


def exchange_for_long_lived(short_token: str, app_id: str, app_secret: str) -> str:
    """Exchange a short-lived user token for a 60-day long-lived token."""
    resp = requests.get(f'{GRAPH}/oauth/access_token', params={
        'grant_type':        'fb_exchange_token',
        'client_id':         app_id,
        'client_secret':     app_secret,
        'fb_exchange_token': short_token,
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()['access_token']


def get_page_and_ig_account(long_lived_token: str) -> tuple[str, str, str]:
    """
    Returns (page_token, page_id, ig_account_id) for the first Page found.
    Page tokens returned here are permanent (never expire).
    """
    # Check what permissions the token actually has
    perm_resp = requests.get(f'{GRAPH}/me/permissions', params={'access_token': long_lived_token}, timeout=15)
    print(f'DEBUG permissions: {perm_resp.text[:500]}')

    # Check what /me returns
    me_resp = requests.get(f'{GRAPH}/me', params={
        'fields': 'id,name,accounts{id,name,access_token,instagram_business_account}',
        'access_token': long_lived_token,
    }, timeout=15)
    print(f'DEBUG /me nested accounts: {me_resp.text[:500]}')

    resp = requests.get(f'{GRAPH}/me/accounts', params={
        'access_token': long_lived_token,
        'fields': 'id,name,access_token,instagram_business_account',
    }, timeout=15)
    print(f'DEBUG /me/accounts status: {resp.status_code}')
    print(f'DEBUG /me/accounts response: {resp.text[:500]}')
    resp.raise_for_status()
    pages = resp.json().get('data', [])
    if not pages:
        raise ValueError('No Facebook Pages found on this account')

    page = pages[0]
    page_id    = page['id']
    page_token = page['access_token']

    ig_resp = requests.get(f'{GRAPH}/{page_id}', params={
        'fields':       'instagram_business_account',
        'access_token': page_token,
    }, timeout=15)
    ig_resp.raise_for_status()
    ig_id = ig_resp.json().get('instagram_business_account', {}).get('id', '')

    return page_token, page_id, ig_id
