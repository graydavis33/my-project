# Plan: Analytical — Phase 1 Web App (MVP)

**Date:** 2026-03-30
**Status:** Draft
**Request:** Build the Phase 1 MVP of "Analytical" — a web-based social media analytics platform for content creators. Web-first (no mobile app). YouTube + TikTok only in Phase 1.

---

## What This Does

Builds a deployable web app at `web-apps/analytical/` — a FastAPI Python backend + plain HTML/CSS/JS frontend. Users sign up with email + password, connect their YouTube and TikTok accounts via OAuth, and see a unified analytics dashboard with AI insights. Stripe handles the $19/mo Creator tier subscription. This is the monetizable product built on top of the existing social media analytics scraper code.

---

## Current State

- `python-scripts/social-media-analytics/` — working scrapers for YouTube, TikTok, Instagram, Facebook. YouTube fetcher and TikTok fetcher can be refactored into the app backend.
- `python-scripts/social-media-analytics/APP_ROADMAP.md` — full roadmap already written. Phase 1 scope defined.
- `web-apps/` — exists, contains payday-checklist. No Analytical app code yet.
- No backend server, no database, no auth system, no Stripe integration exists.

**Tech stack decision (from roadmap):**
- Backend: Python + FastAPI
- Frontend: plain HTML + CSS + JS (no React, no framework)
- Database: PostgreSQL via Railway
- Hosting: Railway.app
- Auth: email + password with JWT tokens
- Payments: Stripe

---

## What We're Building

**New directory structure:**
```
web-apps/analytical/
  backend/
    main.py              — FastAPI app, all routes
    auth.py              — JWT auth: signup, login, token verify
    database.py          — PostgreSQL connection, table setup
    models.py            — User, Connection, AnalyticsSnapshot models
    youtube_fetcher.py   — refactored from social-media-analytics/
    tiktok_fetcher.py    — refactored from social-media-analytics/
    ai_analyzer.py       — Claude insights (refactored from social-media-analytics/)
    requirements.txt
    .env.example         — list of required env vars (no secrets)
  frontend/
    index.html           — landing page / marketing page
    login.html           — login page
    signup.html          — signup page
    dashboard.html       — main analytics dashboard
    connect.html         — connect social accounts (OAuth start page)
    style.css            — shared styles (dark theme, Graydient brand)
    app.js               — shared JS: auth state, API calls, navigation
    dashboard.js         — dashboard-specific: fetch data, render charts
```

**Nothing in `python-scripts/social-media-analytics/` is deleted.** The scraper stays as-is for personal use. The app backend gets its own copies of the fetcher files, refactored as classes.

---

## Step-by-Step Tasks

### Step 1: Project Scaffold + Frontend Shell

Create the directory structure and all frontend HTML files as shells (with correct structure, nav, and placeholders — no functionality yet).

Files to create:
- `web-apps/analytical/frontend/style.css` — full dark theme styles (colors, typography, nav, cards, buttons, forms, responsive)
- `web-apps/analytical/frontend/index.html` — landing page: headline, value prop, pricing table (Free/$19/$39), CTA to sign up
- `web-apps/analytical/frontend/login.html` — email + password form, link to signup
- `web-apps/analytical/frontend/signup.html` — email + password + confirm password form, link to login
- `web-apps/analytical/frontend/dashboard.html` — authenticated shell: nav, platform connection status cards, stats grid (placeholder data), AI insights panel
- `web-apps/analytical/frontend/connect.html` — platform connection page: YouTube OAuth button, TikTok OAuth button, status indicators
- `web-apps/analytical/frontend/app.js` — auth helpers: `getToken()`, `requireAuth()` (redirect to login if no token), `apiCall(endpoint, options)` wrapper, `logout()`
- `web-apps/analytical/frontend/dashboard.js` — placeholder: `fetchStats()`, `renderStats()`, `fetchInsights()`

**Design specs:**
- Background: `#0d0d0d`
- Surface cards: `#1a1a1a`
- Accent: `#6C63FF`
- Text: `#ffffff` primary, `#aaaaaa` secondary
- Font: Inter (Google Fonts)
- Fully responsive (mobile-friendly — creators check on their phones)

---

### Step 2: FastAPI Backend Scaffold

Create the backend Python app.

Files to create:
- `web-apps/analytical/backend/requirements.txt`:
  ```
  fastapi
  uvicorn
  psycopg2-binary
  python-jose[cryptography]
  passlib[bcrypt]
  python-dotenv
  anthropic
  google-auth
  google-auth-oauthlib
  google-auth-httplib2
  google-api-python-client
  requests
  stripe
  ```
- `web-apps/analytical/backend/.env.example`:
  ```
  DATABASE_URL=postgresql://user:password@host:5432/analytical
  JWT_SECRET=your-secret-key-here
  ANTHROPIC_API_KEY=
  YOUTUBE_CLIENT_ID=
  YOUTUBE_CLIENT_SECRET=
  TIKTOK_CLIENT_KEY=
  TIKTOK_CLIENT_SECRET=
  STRIPE_SECRET_KEY=
  STRIPE_WEBHOOK_SECRET=
  FRONTEND_URL=http://localhost:3000
  ```
- `web-apps/analytical/backend/database.py` — PostgreSQL connection via psycopg2. `get_connection()` function. `init_db()` creates tables if they don't exist.
- `web-apps/analytical/backend/models.py` — SQL table definitions (not ORM — plain SQL strings):
  - `users` — id, email, password_hash, tier (free/creator/pro), created_at, stripe_customer_id
  - `platform_connections` — id, user_id, platform (youtube/tiktok/instagram/facebook), access_token (encrypted), refresh_token, connected_at, expires_at
  - `analytics_snapshots` — id, user_id, platform, fetched_at, data (JSONB)
  - `ai_insights` — id, user_id, generated_at, content (text)
- `web-apps/analytical/backend/auth.py` — four functions:
  - `hash_password(password)` → bcrypt hash
  - `verify_password(password, hash)` → bool
  - `create_token(user_id)` → signed JWT (expires 7 days)
  - `decode_token(token)` → user_id or raises
- `web-apps/analytical/backend/main.py` — FastAPI app with these routes:
  - `POST /api/auth/signup` — create user, return JWT
  - `POST /api/auth/login` — verify password, return JWT
  - `GET /api/auth/me` — return current user info (requires auth header)
  - `GET /api/connect/youtube` — redirect to YouTube OAuth consent page
  - `GET /api/connect/youtube/callback` — handle OAuth callback, store tokens in DB
  - `GET /api/connect/tiktok` — redirect to TikTok OAuth consent page
  - `GET /api/connect/tiktok/callback` — handle OAuth callback, store tokens
  - `GET /api/stats` — fetch analytics for authenticated user (from DB snapshots or live fetch if stale)
  - `POST /api/stats/refresh` — force-refresh all platform data for the user
  - `GET /api/insights` — return latest AI insight for the user (generate if >7 days old)
  - `POST /api/billing/subscribe` — create Stripe checkout session for Creator tier
  - `GET /api/billing/portal` — Stripe customer portal link (for managing subscription)
  - `POST /api/billing/webhook` — Stripe webhook handler (update user tier on payment events)

---

### Step 3: YouTube OAuth + Data Fetcher (Refactored)

Create `web-apps/analytical/backend/youtube_fetcher.py` as a class.

Refactored from `python-scripts/social-media-analytics/youtube_fetcher.py`. Key changes:
- Takes `access_token` + `refresh_token` as constructor args (not a file-based token.json)
- Returns structured dict instead of writing to Sheets
- Method: `fetch_stats(days=30)` → returns `{channel_name, subscriber_count, videos: [{id, title, views, likes, comments, published_at}]}`
- Handles token refresh inline and updates the DB record if token was refreshed

The `GET /api/stats` route in main.py calls this fetcher when user has YouTube connected.

---

### Step 4: TikTok OAuth + Data Fetcher (Refactored)

Create `web-apps/analytical/backend/tiktok_fetcher.py` as a class.

Refactored from `python-scripts/social-media-analytics/tiktok_fetcher.py`. Key changes:
- Takes `access_token` + `refresh_token` as constructor args
- Returns structured dict: `{username, follower_count, videos: [{id, title, views, likes, comments, shares, published_at}]}`
- Handles token refresh inline

---

### Step 5: AI Insights

Create `web-apps/analytical/backend/ai_analyzer.py`.

Refactored from `python-scripts/social-media-analytics/ai_analyzer.py`. Changes:
- Takes raw stats dict (YouTube + TikTok combined) instead of reading from Sheets
- Returns plain-text insight string (no Notion output, no Slack output)
- Model: `claude-haiku-4-5-20251001` (cheap — this runs per user, per week)
- Caches result in `ai_insights` table for 7 days — never generates twice in a week for the same user

The `GET /api/insights` route calls this.

---

### Step 6: Stripe Integration

In `main.py`, implement Stripe routes using the `stripe` Python SDK:

- `POST /api/billing/subscribe`:
  - Creates a Stripe Checkout Session for the Creator tier ($19/mo)
  - `success_url` and `cancel_url` point back to the frontend
  - Returns `{checkout_url}` — frontend redirects user there
- `GET /api/billing/portal`:
  - Creates a Stripe Customer Portal session for the current user
  - Returns `{portal_url}` — frontend redirects user there
- `POST /api/billing/webhook`:
  - Verifies Stripe signature with `STRIPE_WEBHOOK_SECRET`
  - On `checkout.session.completed` → update user tier to "creator" in DB
  - On `customer.subscription.deleted` → update user tier back to "free"

---

### Step 7: Wire Frontend to Backend

Update the frontend JS to actually call the API:

- `app.js`:
  - `signup()` — POST to `/api/auth/signup`, store JWT in localStorage
  - `login()` — POST to `/api/auth/login`, store JWT
  - `logout()` — clear localStorage, redirect to login
  - `requireAuth()` — check JWT exists, redirect to login if not
  - `apiCall(path, options)` — fetch wrapper that injects `Authorization: Bearer <token>` header

- `dashboard.js`:
  - On load: call `requireAuth()`, then `GET /api/stats` and `GET /api/insights`
  - Render stats cards (views, likes, engagement rate, top posts)
  - Render AI insights panel
  - "Refresh" button calls `POST /api/stats/refresh`
  - Show "Connect YouTube" / "Connect TikTok" buttons if platforms not connected

- `connect.html` + JS:
  - "Connect YouTube" button → redirect to `GET /api/connect/youtube`
  - "Connect TikTok" button → redirect to `GET /api/connect/tiktok`
  - Show connected/not connected status badges

---

### Step 8: Local Dev Setup Instructions

Create `web-apps/analytical/README.md` with:
- How to set up PostgreSQL locally (or use Railway)
- How to fill in `.env` from `.env.example`
- How to run: `cd web-apps/analytical/backend && uvicorn main:app --reload`
- How to serve frontend locally (Python's `http.server` or just open in browser)
- How to set up YouTube OAuth credentials in Google Cloud Console
- How to test Stripe webhooks locally with Stripe CLI

---

## How to Verify It Works

- [ ] `uvicorn main:app --reload` starts without errors
- [ ] `POST /api/auth/signup` creates a user and returns a JWT
- [ ] `POST /api/auth/login` with correct password returns JWT; wrong password returns 401
- [ ] `GET /api/auth/me` with valid token returns user info; no token returns 401
- [ ] `GET /api/connect/youtube` redirects to Google OAuth page
- [ ] Frontend `index.html` opens in browser and renders correctly
- [ ] Frontend `login.html` submits and stores token in localStorage
- [ ] Frontend `dashboard.html` redirects to login if no token found
- [ ] `GET /api/stats` returns structured data when YouTube is connected

---

## Notes

- **No Railway deployment in this plan.** Get it working locally first. Deployment is a separate step after Phase 1 is verified.
- **No Instagram/Facebook.** The roadmap is clear: Meta requires app approval that takes weeks. Phase 1 = YouTube + TikTok only.
- **Database:** If no local PostgreSQL is set up, SQLite can substitute temporarily for development. Use `DATABASE_URL=sqlite:///./analytical.db` — but the SQL schemas must be PostgreSQL-compatible so the swap to Railway is seamless.
- **Stripe test mode:** Use Stripe's test API keys and test card numbers (`4242 4242 4242 4242`) for all development and smoke tests. Never use live keys in local dev.
- **Token encryption:** `access_token` and `refresh_token` stored in `platform_connections` should ideally be encrypted at rest. For V1, storing them as plaintext in the DB is acceptable (Railway's database is not public). Add encryption in V1.1.
- **CORS:** FastAPI needs `CORSMiddleware` to allow the frontend (running on a different port or domain) to call the backend. Add this in `main.py` from day one.
- **What carries over from APP_ROADMAP.md:** this plan implements exactly Phase 1 as defined. Phase 2 (Instagram/Facebook, competitor tracking, weekly email digest) is not touched here.
