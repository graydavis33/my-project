"""
Analytical — FastAPI backend (SQLite local build)
"""
import os
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
import json
import secrets
import stripe
import anthropic
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Header, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from jose import JWTError
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GRequest

import auth as auth_module
import database
import models
from youtube_fetcher import YouTubeFetcher
from tiktok_fetcher import TikTokFetcher
from ai_analyzer import generate_insights

load_dotenv()

# ─── Config ──────────────────────────────────────────────────
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID', '')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET', '')
TIKTOK_CLIENT_KEY = os.getenv('TIKTOK_CLIENT_KEY', '')
TIKTOK_CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET', '')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
STRIPE_CREATOR_PRICE_ID = os.getenv('STRIPE_CREATOR_PRICE_ID', '')

stripe.api_key = STRIPE_SECRET_KEY

YOUTUBE_SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly',
]
YOUTUBE_REDIRECT_URI = os.getenv('YOUTUBE_REDIRECT_URI', 'http://localhost:8000/api/connect/youtube/callback')
TIKTOK_REDIRECT_URI = os.getenv('TIKTOK_REDIRECT_URI', 'http://localhost:8000/api/connect/tiktok/callback')

_oauth_states = {}

# ─── App ─────────────────────────────────────────────────────
app = FastAPI(title='Analytical API', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, 'http://localhost:3000', 'http://localhost:8080',
                   'http://127.0.0.1:5500', 'http://127.0.0.1:3000', 'null'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.on_event('startup')
def startup():
    database.init_db()


# ─── Auth Dependency ─────────────────────────────────────────
def get_current_user_id(authorization: str = Header(None)) -> int:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing or invalid Authorization header')
    token = authorization.split(' ', 1)[1]
    try:
        return auth_module.decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid or expired token')


# ─── Pydantic Models ─────────────────────────────────────────
class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ChatMessage(BaseModel):
    message: str
    history: list = []


# ─── Auth Routes ─────────────────────────────────────────────
@app.post('/api/auth/signup')
def signup(body: SignupRequest):
    email = body.email.strip().lower()
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail='Password must be at least 8 characters')

    conn = database.get_connection()
    try:
        if models.get_user_by_email(conn, email):
            raise HTTPException(status_code=409, detail='An account with this email already exists')
        pw_hash = auth_module.hash_password(body.password)
        user = models.create_user(conn, email, pw_hash)
        token = auth_module.create_token(user['id'])
        return {'token': token, 'user': {'id': user['id'], 'email': user['email'], 'tier': user['tier']}}
    finally:
        conn.close()


@app.post('/api/auth/login')
def login(body: LoginRequest):
    email = body.email.strip().lower()
    conn = database.get_connection()
    try:
        user = models.get_user_by_email(conn, email)
        if not user or not auth_module.verify_password(body.password, user['password_hash']):
            raise HTTPException(status_code=401, detail='Invalid email or password')
        token = auth_module.create_token(user['id'])
        return {'token': token, 'user': {'id': user['id'], 'email': user['email'], 'tier': user['tier']}}
    finally:
        conn.close()


@app.get('/api/auth/me')
def me(authorization: str = Header(None)):
    user_id = get_current_user_id(authorization)
    conn = database.get_connection()
    try:
        user = models.get_user_by_id(conn, user_id)
        if not user:
            raise HTTPException(status_code=404, detail='User not found')
        return {'id': user['id'], 'email': user['email'], 'tier': user['tier']}
    finally:
        conn.close()


# ─── YouTube OAuth ────────────────────────────────────────────
@app.get('/api/connect/youtube')
def connect_youtube(token: str = Query(...)):
    try:
        user_id = auth_module.decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid token')

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {'user_id': user_id, 'platform': 'youtube'}

    flow = Flow.from_client_config(
        {'web': {
            'client_id': YOUTUBE_CLIENT_ID,
            'client_secret': YOUTUBE_CLIENT_SECRET,
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'redirect_uris': [YOUTUBE_REDIRECT_URI],
        }},
        scopes=YOUTUBE_SCOPES,
    )
    flow.redirect_uri = YOUTUBE_REDIRECT_URI
    auth_url, _ = flow.authorization_url(
        access_type='offline', include_granted_scopes='true',
        state=state, prompt='consent',
    )
    return RedirectResponse(auth_url)


@app.get('/api/connect/youtube/callback')
def youtube_callback(code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    if error or not code or not state:
        return RedirectResponse(f'{FRONTEND_URL}/connect.html?error=youtube_denied')

    state_data = _oauth_states.pop(state, None)
    if not state_data:
        return RedirectResponse(f'{FRONTEND_URL}/connect.html?error=invalid_state')

    flow = Flow.from_client_config(
        {'web': {
            'client_id': YOUTUBE_CLIENT_ID,
            'client_secret': YOUTUBE_CLIENT_SECRET,
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'redirect_uris': [YOUTUBE_REDIRECT_URI],
        }},
        scopes=YOUTUBE_SCOPES,
        state=state,
    )
    flow.redirect_uri = YOUTUBE_REDIRECT_URI
    flow.fetch_token(code=code)
    creds = flow.credentials

    conn = database.get_connection()
    try:
        models.upsert_connection(
            conn, user_id=state_data['user_id'], platform='youtube',
            access_token=creds.token, refresh_token=creds.refresh_token,
            expires_at=creds.expiry,
        )
    finally:
        conn.close()

    return RedirectResponse(f'{FRONTEND_URL}/connect.html?connected=youtube')


# ─── TikTok OAuth ─────────────────────────────────────────────
@app.get('/api/connect/tiktok')
def connect_tiktok(token: str = Query(...)):
    try:
        user_id = auth_module.decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid token')

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {'user_id': user_id, 'platform': 'tiktok'}

    auth_url = (
        f'https://www.tiktok.com/v2/auth/authorize/'
        f'?client_key={TIKTOK_CLIENT_KEY}'
        f'&response_type=code&scope=user.info.basic,video.list'
        f'&redirect_uri={TIKTOK_REDIRECT_URI}&state={state}'
    )
    return RedirectResponse(auth_url)


@app.get('/api/connect/tiktok/callback')
def tiktok_callback(code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    if error or not code or not state:
        return RedirectResponse(f'{FRONTEND_URL}/connect.html?error=tiktok_denied')

    state_data = _oauth_states.pop(state, None)
    if not state_data:
        return RedirectResponse(f'{FRONTEND_URL}/connect.html?error=invalid_state')

    import requests as req
    resp = req.post('https://open.tiktokapis.com/v2/oauth/token/', data={
        'client_key': TIKTOK_CLIENT_KEY,
        'client_secret': TIKTOK_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': TIKTOK_REDIRECT_URI,
    }, timeout=20)

    if not resp.ok:
        return RedirectResponse(f'{FRONTEND_URL}/connect.html?error=tiktok_token_failed')

    token_data = resp.json().get('data', {})
    conn = database.get_connection()
    try:
        models.upsert_connection(
            conn, user_id=state_data['user_id'], platform='tiktok',
            access_token=token_data.get('access_token', ''),
            refresh_token=token_data.get('refresh_token', ''),
        )
    finally:
        conn.close()

    return RedirectResponse(f'{FRONTEND_URL}/connect.html?connected=tiktok')


# ─── Stats ────────────────────────────────────────────────────
@app.get('/api/stats')
def get_stats(authorization: str = Header(None)):
    user_id = get_current_user_id(authorization)
    conn = database.get_connection()
    try:
        connections = models.get_all_connections(conn, user_id)
        result = {
            'connections': {p: True for p in connections},
            'fetched_at': None,
            'youtube': None,
            'tiktok': None,
        }

        latest_fetch = None

        if 'youtube' in connections:
            snapshot = models.get_latest_snapshot(conn, user_id, 'youtube')
            if not models.is_snapshot_stale(snapshot):
                result['youtube'] = snapshot['data']
                if snapshot.get('fetched_at'):
                    latest_fetch = snapshot['fetched_at']

        if 'tiktok' in connections:
            snapshot = models.get_latest_snapshot(conn, user_id, 'tiktok')
            if not models.is_snapshot_stale(snapshot):
                result['tiktok'] = snapshot['data']

        if latest_fetch:
            result['fetched_at'] = latest_fetch

        return result
    finally:
        conn.close()


@app.post('/api/stats/refresh')
def refresh_stats(authorization: str = Header(None)):
    user_id = get_current_user_id(authorization)
    conn = database.get_connection()
    try:
        connections = models.get_all_connections(conn, user_id)

        if 'youtube' in connections:
            yt_conn = connections['youtube']
            def on_yt_refresh(new_access, new_refresh):
                models.upsert_connection(conn, user_id, 'youtube', new_access, new_refresh)
            fetcher = YouTubeFetcher(
                access_token=yt_conn['access_token'],
                refresh_token=yt_conn['refresh_token'],
                on_token_refresh=on_yt_refresh,
            )
            try:
                data = fetcher.fetch_stats()
                models.save_snapshot(conn, user_id, 'youtube', data)
            except Exception as e:
                print(f'YouTube fetch failed: {e}')

        if 'tiktok' in connections:
            tt_conn = connections['tiktok']
            def on_tt_refresh(new_access, new_refresh):
                models.upsert_connection(conn, user_id, 'tiktok', new_access, new_refresh)
            fetcher = TikTokFetcher(
                access_token=tt_conn['access_token'],
                refresh_token=tt_conn['refresh_token'],
                on_token_refresh=on_tt_refresh,
            )
            try:
                data = fetcher.fetch_stats()
                models.save_snapshot(conn, user_id, 'tiktok', data)
            except Exception as e:
                print(f'TikTok fetch failed: {e}')

        return {'status': 'ok'}
    finally:
        conn.close()


# ─── Insights ─────────────────────────────────────────────────
@app.get('/api/insights')
def get_insights(authorization: str = Header(None), force: bool = Query(False)):
    user_id = get_current_user_id(authorization)
    conn = database.get_connection()
    try:
        insight = models.get_latest_insight(conn, user_id)

        if not force and not models.is_insight_stale(insight):
            return {
                'content': insight['content'],
                'generated_at': insight['generated_at'],
            }

        yt_snap = models.get_latest_snapshot(conn, user_id, 'youtube')
        tt_snap = models.get_latest_snapshot(conn, user_id, 'tiktok')

        stats = {}
        if yt_snap:
            stats['youtube'] = yt_snap['data']
        if tt_snap:
            stats['tiktok'] = tt_snap['data']

        if not stats:
            return {'content': '', 'generated_at': None}

        content = generate_insights(stats)
        if content:
            models.save_insight(conn, user_id, content)

        return {'content': content, 'generated_at': datetime.now(timezone.utc).isoformat()}
    finally:
        conn.close()


# ─── Comments ─────────────────────────────────────────────────
@app.get('/api/comments/youtube/{video_id}')
def get_youtube_comments(video_id: str, authorization: str = Header(None)):
    """Fetch top 20 comments for a YouTube video using stored credentials."""
    user_id = get_current_user_id(authorization)
    conn = database.get_connection()
    try:
        yt_conn = models.get_platform_connection(conn, user_id, 'youtube')
        if not yt_conn:
            raise HTTPException(status_code=400, detail='YouTube not connected')

        creds = Credentials(
            token=yt_conn['access_token'],
            refresh_token=yt_conn['refresh_token'],
            token_uri='https://oauth2.googleapis.com/token',
            client_id=YOUTUBE_CLIENT_ID,
            client_secret=YOUTUBE_CLIENT_SECRET,
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(GRequest())
            models.upsert_connection(conn, user_id, 'youtube', creds.token, creds.refresh_token)

        youtube = build('youtube', 'v3', credentials=creds)
        resp = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=20,
            order='relevance',
        ).execute()

        comments = []
        for item in resp.get('items', []):
            top = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'author': top.get('authorDisplayName', 'Unknown'),
                'text': top.get('textDisplay', ''),
                'likes': top.get('likeCount', 0),
                'published_at': top.get('publishedAt', '')[:10],
            })

        return {'video_id': video_id, 'comments': comments}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch comments: {str(e)}')
    finally:
        conn.close()


# ─── AI Chat ──────────────────────────────────────────────────
@app.post('/api/chat')
def chat(body: ChatMessage, authorization: str = Header(None)):
    user_id = get_current_user_id(authorization)
    conn = database.get_connection()
    try:
        yt_snap = models.get_latest_snapshot(conn, user_id, 'youtube')
        tt_snap = models.get_latest_snapshot(conn, user_id, 'tiktok')

        context_parts = []
        if yt_snap:
            d = yt_snap['data']
            context_parts.append(
                f"YouTube ({d.get('channel_name','')}, {d.get('subscriber_count',0):,} subscribers):\n"
                + json.dumps(d.get('videos', [])[:30], indent=2)[:4000]
            )
        if tt_snap:
            d = tt_snap['data']
            context_parts.append(
                f"TikTok (@{d.get('username','')}, {d.get('follower_count',0):,} followers):\n"
                + json.dumps(d.get('videos', [])[:30], indent=2)[:4000]
            )

        context = '\n\n'.join(context_parts) if context_parts else 'No analytics data connected yet.'

        system_prompt = f"""You are an AI assistant built into Analytical, a social media analytics platform for content creators.

USER'S ANALYTICS DATA:
{context}

You can:
- Answer questions about this specific analytics data (views, engagement, top posts, trends)
- Generate custom reports (e.g. "top 5 Friday posts by views", "compare YouTube vs TikTok engagement")
- Give content strategy advice based on the data patterns
- Answer questions about the Analytical platform itself:
  - Pricing: Free ($0, 1 platform, 10 videos), Creator ($19/mo, both platforms, full history + AI), Pro ($39/mo, coming soon)
  - Connected platforms: YouTube, TikTok (Instagram and Facebook coming soon, LinkedIn in planning)
  - Features: unified dashboard, AI insights, top posts tracking, OAuth connect, comments viewer, video previews
- Answer general social media growth questions

Be specific. Reference actual video titles and numbers when they're in the data. Keep answers concise but complete."""

        api_key = os.getenv('ANTHROPIC_API_KEY', '').strip()
        if not api_key:
            return {'response': 'ANTHROPIC_API_KEY not configured in backend .env'}

        client = anthropic.Anthropic(api_key=api_key)

        messages = []
        for msg in body.history[-12:]:
            role = msg.get('role', 'user')
            if role in ('user', 'assistant'):
                messages.append({'role': role, 'content': msg.get('content', '')})
        messages.append({'role': 'user', 'content': body.message})

        response = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1200,
            system=system_prompt,
            messages=messages,
        )
        return {'response': response.content[0].text.strip()}
    finally:
        conn.close()


# ─── Billing ──────────────────────────────────────────────────
@app.post('/api/billing/subscribe')
def subscribe(authorization: str = Header(None)):
    user_id = get_current_user_id(authorization)
    conn = database.get_connection()
    try:
        user = models.get_user_by_id(conn, user_id)
        if not user:
            raise HTTPException(status_code=404, detail='User not found')

        customer_id = user.get('stripe_customer_id')
        if not customer_id:
            customer = stripe.Customer.create(email=user['email'])
            customer_id = customer.id
            models.update_stripe_customer(conn, user_id, customer_id)

        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode='subscription',
            line_items=[{'price': STRIPE_CREATOR_PRICE_ID, 'quantity': 1}],
            success_url=f'{FRONTEND_URL}/dashboard.html?subscribed=true',
            cancel_url=f'{FRONTEND_URL}/dashboard.html?canceled=true',
        )
        return {'checkout_url': session.url}
    finally:
        conn.close()


@app.get('/api/billing/portal')
def billing_portal(authorization: str = Header(None)):
    user_id = get_current_user_id(authorization)
    conn = database.get_connection()
    try:
        user = models.get_user_by_id(conn, user_id)
        if not user or not user.get('stripe_customer_id'):
            raise HTTPException(status_code=400, detail='No billing account found')

        session = stripe.billing_portal.Session.create(
            customer=user['stripe_customer_id'],
            return_url=f'{FRONTEND_URL}/dashboard.html',
        )
        return {'portal_url': session.url}
    finally:
        conn.close()


@app.post('/api/billing/webhook')
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature', '')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail='Invalid Stripe signature')

    conn = database.get_connection()
    try:
        if event['type'] == 'checkout.session.completed':
            customer_id = event['data']['object'].get('customer')
            user = models.get_user_by_stripe_customer(conn, customer_id)
            if user:
                models.update_user_tier(conn, user['id'], 'creator')
        elif event['type'] == 'customer.subscription.deleted':
            customer_id = event['data']['object'].get('customer')
            user = models.get_user_by_stripe_customer(conn, customer_id)
            if user:
                models.update_user_tier(conn, user['id'], 'free')
    finally:
        conn.close()

    return {'received': True}
