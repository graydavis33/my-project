"""
Analytical — FastAPI backend
All routes in one file for simplicity.
"""
import os
import json
import secrets
import stripe
import anthropic
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Header, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
from jose import JWTError
from google_auth_oauthlib.flow import Flow

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

# In-memory state store for OAuth flows (fine for single-server; use Redis for multi-instance)
_oauth_states = {}

# ─── App ─────────────────────────────────────────────────────
app = FastAPI(title='Analytical API', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, 'http://localhost:3000', 'http://localhost:8080', 'http://127.0.0.1:5500'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# ─── Startup ─────────────────────────────────────────────────
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


# ─── Auth Routes ─────────────────────────────────────────────
@app.post('/api/auth/signup')
def signup(body: SignupRequest):
    email = body.email.strip().lower()
    password = body.password

    if len(password) < 8:
        raise HTTPException(status_code=400, detail='Password must be at least 8 characters')

    conn = database.get_connection()
    try:
        existing = models.get_user_by_email(conn, email)
        if existing:
            raise HTTPException(status_code=409, detail='An account with this email already exists')

        pw_hash = auth_module.hash_password(password)
        user = models.create_user(conn, email, pw_hash)
        token = auth_module.create_token(user['id'])
        return {
            'token': token,
            'user': {'id': user['id'], 'email': user['email'], 'tier': user['tier']},
        }
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
        return {
            'token': token,
            'user': {'id': user['id'], 'email': user['email'], 'tier': user['tier']},
        }
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
    """Redirect user to YouTube OAuth consent page. Token passed as query param."""
    try:
        user_id = auth_module.decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid token')

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {'user_id': user_id, 'platform': 'youtube'}

    flow = Flow.from_client_config(
        {
            'web': {
                'client_id': YOUTUBE_CLIENT_ID,
                'client_secret': YOUTUBE_CLIENT_SECRET,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': [YOUTUBE_REDIRECT_URI],
            }
        },
        scopes=YOUTUBE_SCOPES,
    )
    flow.redirect_uri = YOUTUBE_REDIRECT_URI
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=state,
        prompt='consent',
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
        {
            'web': {
                'client_id': YOUTUBE_CLIENT_ID,
                'client_secret': YOUTUBE_CLIENT_SECRET,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': [YOUTUBE_REDIRECT_URI],
            }
        },
        scopes=YOUTUBE_SCOPES,
        state=state,
    )
    flow.redirect_uri = YOUTUBE_REDIRECT_URI
    flow.fetch_token(code=code)
    creds = flow.credentials

    conn = database.get_connection()
    try:
        models.upsert_connection(
            conn,
            user_id=state_data['user_id'],
            platform='youtube',
            access_token=creds.token,
            refresh_token=creds.refresh_token,
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
        f'&response_type=code'
        f'&scope=user.info.basic,video.list'
        f'&redirect_uri={TIKTOK_REDIRECT_URI}'
        f'&state={state}'
    )
    return RedirectResponse(auth_url)


@app.get('/api/connect/tiktok/callback')
def tiktok_callback(code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    if error or not code or not state:
        return RedirectResponse(f'{FRONTEND_URL}/connect.html?error=tiktok_denied')

    state_data = _oauth_states.pop(state, None)
    if not state_data:
        return RedirectResponse(f'{FRONTEND_URL}/connect.html?error=invalid_state')

    # Exchange code for tokens
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
    access_token = token_data.get('access_token', '')
    refresh_token = token_data.get('refresh_token', '')

    conn = database.get_connection()
    try:
        models.upsert_connection(
            conn,
            user_id=state_data['user_id'],
            platform='tiktok',
            access_token=access_token,
            refresh_token=refresh_token,
        )
    finally:
        conn.close()

    return RedirectResponse(f'{FRONTEND_URL}/connect.html?connected=tiktok')


# ─── Stats ────────────────────────────────────────────────────
@app.get('/api/stats')
def get_stats(authorization: str = Header(None)):
    """Return analytics for the authenticated user. Uses cached snapshots when fresh."""
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

        # YouTube
        if 'youtube' in connections:
            snapshot = models.get_latest_snapshot(conn, user_id, 'youtube')
            if not models.is_snapshot_stale(snapshot):
                result['youtube'] = snapshot['data']
                if snapshot['fetched_at']:
                    ts = snapshot['fetched_at']
                    if hasattr(ts, 'isoformat'):
                        latest_fetch = ts.isoformat()

        # TikTok
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
    """Force-fetch fresh data from all connected platforms."""
    user_id = get_current_user_id(authorization)
    conn = database.get_connection()
    try:
        connections = models.get_all_connections(conn, user_id)

        # YouTube
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
                print(f'YouTube fetch failed for user {user_id}: {e}')

        # TikTok
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
                print(f'TikTok fetch failed for user {user_id}: {e}')

        return {'status': 'ok'}
    finally:
        conn.close()


# ─── Insights ─────────────────────────────────────────────────
@app.get('/api/insights')
def get_insights(authorization: str = Header(None), force: bool = Query(False)):
    """Return latest AI insight. Generates if >7 days old (or forced)."""
    user_id = get_current_user_id(authorization)
    conn = database.get_connection()
    try:
        insight = models.get_latest_insight(conn, user_id)

        if not force and not models.is_insight_stale(insight):
            return {
                'content': insight['content'],
                'generated_at': insight['generated_at'].isoformat() if hasattr(insight['generated_at'], 'isoformat') else str(insight['generated_at']),
            }

        # Build stats dict from latest snapshots
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

        return {
            'content': content,
            'generated_at': datetime.now(timezone.utc).isoformat(),
        }
    finally:
        conn.close()


# ─── Billing — Stripe ─────────────────────────────────────────
@app.post('/api/billing/subscribe')
def subscribe(authorization: str = Header(None)):
    """Create a Stripe Checkout Session for the Creator tier."""
    user_id = get_current_user_id(authorization)
    conn = database.get_connection()
    try:
        user = models.get_user_by_id(conn, user_id)
        if not user:
            raise HTTPException(status_code=404, detail='User not found')

        # Create or reuse Stripe customer
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
    """Create a Stripe Customer Portal session."""
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
    """Handle Stripe webhook events to update user tiers."""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature', '')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail='Invalid Stripe signature')

    conn = database.get_connection()
    try:
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            customer_id = session.get('customer')
            user = models.get_user_by_stripe_customer(conn, customer_id)
            if user:
                models.update_user_tier(conn, user['id'], 'creator')

        elif event['type'] == 'customer.subscription.deleted':
            sub = event['data']['object']
            customer_id = sub.get('customer')
            user = models.get_user_by_stripe_customer(conn, customer_id)
            if user:
                models.update_user_tier(conn, user['id'], 'free')

    finally:
        conn.close()

    return {'received': True}
