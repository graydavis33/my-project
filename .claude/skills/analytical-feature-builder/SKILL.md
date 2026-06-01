---
name: analytical-feature-builder
description: Build and modify features inside the Analytical SaaS app while preserving its established visual language. Trigger on "add to Analytical", "new Analytical widget", "new dashboard chart", "Analytical feature", any edit to preview-real.html, dashboard.html, app.js, dashboard.js, chat.js, or style.css in web-apps/analytical/, or FastAPI work in web-apps/analytical/backend/. Enforces Chart.js + barGlow plugin, --accent-rgb theming, glass variants, and custom metric card persistence patterns. Use this even for "small" tweaks — a one-line change can still drift from the house style.
---

# Analytical Feature Builder

Analytical is Gray's SaaS app at `web-apps/analytical/`. The visual language is locked in. Drift means rework.

## House style — non-negotiable

| Pattern | Rule | Where it lives |
|---------|------|----------------|
| **Charts** | Chart.js with custom `barGlow` plugin (`shadowBlur: 18`, `barPercentage: 0.88`). Not 3D isometric. Not plain default. | `preview-real.html` line ~1087 (plugin def), line ~1101 (registration) |
| **Accent color** | Whole-dashboard color driven by `--accent-rgb` CSS variable. Update this var, everything re-themes including chart glow. | `preview-real.html` line ~24 |
| **Glass variants** | `applyGlassVariant(value)` updates all CSS vars + re-renders charts. Use it, don't reinvent. | `preview-real.html` line ~1495 |
| **Custom metric cards** | Persist via `localStorage` key `analytical_custom_metrics`. Backend persistence is deferred. | `saveCustomMetrics` / `loadCustomMetrics` in `preview-real.html` |
| **Prototype file** | `preview-real.html` is the canvas for new UI. `frontend/dashboard.html` is the shipped app. Build new patterns in `preview-real.html` first, then port. | `web-apps/analytical/preview-real.html` |
| **Checkpoints** | `preview-checkpoint2.html` is a frozen older version. Do not edit. Slated for deletion in a future cleanup — reference only. | `web-apps/analytical/` root |

## Stack

- **Backend:** FastAPI at `web-apps/analytical/backend/` — `main.py`, `auth.py`, `database.py`, `models.py`, `ai_analyzer.py`, `youtube_fetcher.py`, `tiktok_fetcher.py`
- **Frontend:** vanilla HTML/CSS/JS in `web-apps/analytical/frontend/` — `app.js`, `dashboard.js`, `chat.js`, `style.css`
- **Database:** SQLite (`backend/analytical.db`) local → PostgreSQL/Railway planned
- **Stripe:** intentionally deferred. Do not scaffold payment UI or pricing gates.

## Workflow for a new feature

1. **Locate.** UI tweak → prototype in `preview-real.html` first, port to `frontend/dashboard.html` after. Backend → FastAPI route in `backend/main.py`.

2. **Reuse before inventing.** Glass cards, stat cards, metric edit buttons — patterns already exist. Grep before writing new CSS.

3. **Always `--accent-rgb`, never hardcoded RGB.** Anything color-adaptive must use `rgba(var(--accent-rgb), alpha)`.

4. **Charts use `barGlow`.** The plugin is registered globally. New Chart.js configs inherit it — don't re-register.

5. **Test both glass variants** if the change touches color. `applyGlassVariant('light')` and `applyGlassVariant('default')` should both look correct.

## Run locally

```bash
cd web-apps/analytical/backend
uvicorn main:app --reload --port 8000
```

For OAuth connection flow, open `http://localhost:3000/connect.html` (needs creds in `backend/.env`).

## Don't do this

- Don't rewrite the chart style unless Gray explicitly asks. Decision logged 2026-04-09: default Chart.js + barGlow wins over 3D block style.
- Don't scaffold Stripe, paywalls, or pricing UI. Deferred on purpose.
- Don't hardcode accent colors. Always `rgba(var(--accent-rgb), alpha)`.
- Don't ship straight to `frontend/dashboard.html` before prototyping in `preview-real.html`.
- Don't introduce Tailwind, Bootstrap, or other CSS frameworks. Vanilla + CSS vars is intentional.
- Don't wire Meta (IG/FB) into Analytical backend yet. That's the next major unlock, but the Meta API path is currently shelved — IG/FB data is coming from Playwright scrapers in `python-scripts/social-media-analytics/`, not the Graph API.

## Related files when touching the data layer

- `ai_analyzer.py` — Claude analysis. Uses Sonnet (`claude-sonnet-4-6`).
- `youtube_fetcher.py` — YouTube Data API v3
- `tiktok_fetcher.py` — TikTok Display API
- Instagram + Facebook: currently NOT wired into Analytical. Data source lives in `python-scripts/social-media-analytics/meta_scraper.py` (Playwright) and writes to Google Sheets. Wiring into Analytical is a future task.
