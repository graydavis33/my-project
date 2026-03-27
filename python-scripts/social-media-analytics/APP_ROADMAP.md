# Social Media Analytics — App Roadmap
**Last updated:** 2026-03-27
**Status:** Planning phase — no app code written yet

---

## What Is This App?

A unified social media analytics dashboard for content creators — connect any social media platform in one place, see your real numbers, and get AI-powered insights on what's working and what to post next.

**One-sentence value prop:**
"Stop switching between 4 apps to check your stats — see everything in one dashboard with AI that tells you what to do next."

**Long-term platform vision:**
This app is not limited to 4 platforms. It is designed to eventually support ANY platform with analytics data — including but not limited to:
- YouTube, TikTok, Instagram, Facebook (Phase 1–2)
- X (Twitter), LinkedIn (Phase 2–3)
- Pinterest, Snapchat, Threads (Phase 3+)
- Whatnot, Amazon Live, and other live-selling/emerging platforms (future)
- CapCut and any platform that exposes creator analytics via API

**Architectural requirement:** The backend must be built platform-agnostic from day one — each platform is a self-contained module. Adding a new platform should never require rewriting core logic.

---

## Who Is This For?

**Primary target:** Solo content creators (videographers, vloggers, educators, coaches) posting on 2–4 platforms who are frustrated by jumping between apps and not knowing what's actually driving growth.

**Secondary target:** Social media managers handling 1–3 clients who need quick reporting without paying $200/mo for enterprise tools.

**NOT for (yet):** Agencies managing 10+ accounts, brands, or enterprise teams.

---

## The Problem With the Current Version

The existing Python scraper works for personal use but cannot become a product because:

| Issue | Current Approach | App Approach |
|-------|-----------------|--------------|
| Instagram/Facebook | Playwright scraping (breaks constantly, 2FA issues) | Official Meta Business API (OAuth) |
| YouTube | OAuth per user (works, but token expires every 7 days in testing mode) | OAuth with production app approval |
| TikTok | API credentials hardcoded | OAuth per user |
| Data storage | JSON files, Google Sheets | Database (PostgreSQL) |
| Multi-user | Not possible | Auth system, user accounts |
| Hosting | Runs on Gray's computer | Deployed server (Railway/Render) |

---

## Revenue Model

**Subscription (SaaS) — monthly recurring revenue**

| Tier | Price | What You Get |
|------|-------|-------------|
| Free | $0 | 1 platform, last 30 days, basic metrics only |
| Creator | $19/mo | All 4 platforms, 90 days history, AI insights |
| Pro | $39/mo | All platforms, 1 year history, competitor tracking, export |

**Why subscription over one-time:**
Analytics data is ongoing — people need it every week. Subscription = predictable income. Even 50 Creator subscribers = $950/mo.

---

## Tech Stack Decision

Keep it simple. Build for speed to market, not perfection.

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | Python + FastAPI | Already know Python, FastAPI is fast and simple |
| Frontend | HTML/CSS/JS (no framework) | You already have a working dashboard — extend it |
| Database | PostgreSQL (via Railway) | Free tier available, scales later |
| Hosting | Railway.app | Free tier, simple deploys, handles Python well |
| Auth | Email + password (simple JWT) | Don't over-engineer auth for V1 |
| Platform OAuth | Each platform's official SDK | Required for real API access |

**Not using:** React, Next.js, mobile apps, microservices — too much complexity for V1.

---

## Platform API Reality Check

| Platform | API Access | Difficulty | Notes |
|----------|-----------|------------|-------|
| YouTube | YouTube Data API v3 + Analytics API | Easy ✅ | Already working. Need to publish OAuth app to remove 7-day token limit. |
| TikTok | TikTok for Developers API | Medium ⚠️ | Already have credentials. Need to handle per-user OAuth. |
| Instagram | Meta Business API | Hard ❌ | Requires Meta Developer App approval. Need a Facebook Page + Instagram Business account linked. No scraping. |
| Facebook | Meta Business API | Hard ❌ | Same approval process as Instagram. Scraping is dead — use the API. |

**Key insight:** YouTube + TikTok are ready to build with NOW. Instagram + Facebook require Meta App approval which takes 1–4 weeks and requires a privacy policy, terms of service, and a working demo. Plan accordingly.

---

## Phase 1 — MVP (Goal: First Paying Customer)

**Scope:** YouTube + TikTok only. Web app. No mobile.

**Features:**
- [ ] User signs up with email + password
- [ ] Connects YouTube channel via OAuth
- [ ] Connects TikTok account via OAuth
- [ ] Dashboard: views, likes, comments, engagement rate, avg watch time
- [ ] Last 30 days vs previous 30 days (% change indicators)
- [ ] Top 5 performing posts with thumbnails
- [ ] 1 AI insight per week ("Your Shorts get 3x more views when posted Tuesday–Thursday")
- [ ] Export to CSV
- [ ] Stripe payment integration (Creator tier = $19/mo)

**What MVP does NOT include:**
- Instagram or Facebook (pending Meta approval)
- Competitor tracking
- Content calendar
- Mobile app
- Team/agency features
- Real-time data (daily refresh is fine)

**Done when:** 1 person outside of Gray is paying $19/mo and using it weekly.

---

## Phase 2 — Growth (After MVP is live and stable)

- [ ] Instagram + Facebook (after Meta App approval)
- [ ] Best time to post recommendations
- [ ] Hashtag performance tracking
- [ ] Competitor channel monitoring (YouTube + TikTok)
- [ ] Weekly email digest with your top stats
- [ ] AI content ideas based on your best-performing posts
- [ ] Pro tier features ($39/mo)

---

## Phase 3 — Scale (Future)

- [ ] Mobile app (React Native or just PWA)
- [ ] Agency dashboard (manage multiple clients)
- [ ] White-label option
- [ ] Zapier/webhook integrations
- [ ] API access for power users
- [ ] X (Twitter) analytics integration
- [ ] LinkedIn analytics integration
- [ ] Pinterest, Snapchat, Threads integrations
- [ ] Whatnot / Amazon Live / live-selling platform support
- [ ] CapCut and any emerging platform with creator API access
- [ ] Platform request voting (let users vote on which platform to add next)

---

## What Carries Over From Current Code

| Existing File | Keep? | Notes |
|--------------|-------|-------|
| `youtube_fetcher.py` | ✅ Yes | Refactor into a class, move to backend |
| `tiktok_fetcher.py` | ✅ Yes | Refactor into a class, handle per-user tokens |
| `meta_scraper.py` | ❌ No | Replace entirely with Meta Business API |
| `web-apps/social-media-analytics/index.html` | 🔄 Partial | Use as design reference, rebuild as proper app |
| `main.py` (current orchestrator) | ❌ No | Replace with FastAPI routes |
| `analytics_data.json` | ❌ No | Replace with database |

---

## Immediate Next Steps (Before Writing App Code)

1. **Apply for Meta Developer App approval** — do this NOW because it takes weeks. Need: privacy policy page, terms of service, app description, demo video showing Instagram analytics use case.

2. **Publish YouTube OAuth app** — currently in "testing mode" (7-day tokens). Submit for Google verification to remove the limit. Need: privacy policy, app description.

3. **Buy a domain** — something like `graydient.io` or `analytiq.app` or similar. ~$12/yr.

4. **Set up Railway account** — free tier is enough to start. graydavis33@gmail.com.

5. **Write privacy policy + terms of service** — required by both Meta and Google for production OAuth. Use a generator (Termly.io is free).

---

## Known Limitations & Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Meta takes too long to approve | High | Launch with YouTube + TikTok only, add Meta later |
| TikTok API changes/restricts access | Medium | Monitor TikTok developer portal, have backup plan |
| Google rejects YouTube OAuth app | Low | Their process is straightforward with proper docs |
| Not enough users to justify building | Medium | Validate with 5 paying users before building Phase 2 |

---

## Success Metrics

- **Month 1:** App deployed, YouTube + TikTok working, Gray uses it himself daily
- **Month 2:** 5 users signed up (free tier)
- **Month 3:** 3 paying users ($57/mo MRR)
- **Month 6:** 25 paying users (~$475/mo MRR)
- **Month 12:** 100 paying users (~$1,900/mo MRR)
