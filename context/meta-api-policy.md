# Meta API — Platform Terms, Developer Policies & Full Reference
_Last updated: 2026-04-10_
_Sources: developers.facebook.com/terms/ | developers.facebook.com/devpolicy/ | developers.facebook.com/docs/instagram-platform/overview | developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-media/insights | developers.facebook.com/docs/graph-api/reference/page/insights/ | developers.facebook.com/docs/graph-api/overview/access-levels_

---

## What We're Building

An analytics SaaS (Analytical) that lets creators connect their Instagram and Facebook accounts via OAuth and view their post-level metrics in a dashboard. **Read-only. No posting, no messaging, no advertising.**

---

## Access Levels

| Level | Who it works for | Approval needed |
|-------|-----------------|----------------|
| Standard Access | Only accounts with a role on your app (you, testers) | Automatic — no review |
| Advanced Access | Any user who connects their account publicly | Business Verification + App Review |

**Current status: Standard Access** — works for Gray's accounts only until App Review is passed.

- Standard Access is automatically approved for all Business apps
- Advanced Access requires **Business Verification** first, then App Review per permission
- Once Advanced Access is approved, it's active for all users
- Apps must be in **Live mode** before requesting permissions from non-role users
- Annual **Data Use Checkup** required once Advanced Access is granted — you certify every year that you're still using data as stated

---

## Permissions Needed for Analytical

### Via Facebook Login:
| Permission | What it unlocks | Review required |
|-----------|----------------|----------------|
| `instagram_basic` | Basic profile + media list | Standard — no review |
| `instagram_manage_insights` | Post-level analytics (reach, impressions, plays, saves, shares) | Advanced — needs review |
| `pages_show_list` | List of Facebook Pages the user manages | Standard |
| `pages_read_engagement` | Facebook Page post metrics | Advanced — needs review |

### Do NOT request (keeps review simpler + reduces risk):
- `instagram_content_publish` — posting on their behalf
- `instagram_manage_comments` — modifying comments
- `instagram_manage_messages` — DMs
- Any advertising, ad management, or Marketing API permissions

---

## Instagram Media Insights — Full Metrics Available

Base query: `GET /<INSTAGRAM_MEDIA_ID>/insights`

| Metric | What it measures | Media types | Notes |
|--------|-----------------|-------------|-------|
| `views` | Total times the video has been seen | FEED, REELS, STORY | New — marked "in development" |
| `reach` | Unique users who saw the media at least once | FEED, REELS, STORY | Estimated metric |
| `impressions` | Total times media has been seen (includes repeat views) | FEED, STORY | Deprecated for content after July 2, 2024 in API v22+ |
| `likes` | Number of likes | FEED, REELS | — |
| `comments` | Number of comments | FEED, REELS | — |
| `shares` | Number of shares | FEED, REELS, STORY | — |
| `saved` | Number of times media was saved | FEED, REELS | — |
| `total_interactions` | Likes + saves + comments + shares (minus removals) | FEED, REELS, STORY | Marked "in development" |
| `ig_reels_avg_watch_time` | Average time spent playing a reel | REELS | — |
| `ig_reels_video_view_total_time` | Total cumulative watch time including replays | REELS | Marked "in development" |
| `profile_visits` | Profile visits from this media | FEED, STORY | — |
| `profile_activity` | Actions taken on profile after engaging with media | FEED, STORY | Supports breakdown by action type |
| `follows` | New followers gained from this media | FEED, STORY | — |
| `replies` | Story reply count | STORY | Returns 0 in Europe/Japan |
| `navigation` | Actions taken from a story (taps forward/back/exit) | STORY | Supports breakdown |

### Deprecated metrics (avoid using):
- `plays` — sunsets April 21, 2025
- `clips_replays_count` — sunsets April 21, 2025
- `ig_reels_aggregated_all_plays_count` — sunsets April 21, 2025

### Instagram Insights Limitations:
- Data delay: up to **48 hours** — never real-time
- Data retention: **2 years max**
- Story metrics: only available for **24 hours** (extends if added to Highlights)
- Stories with fewer than **5 interactions** return error code 10 (no data)
- Album/carousel child media: insights unavailable
- Minimum **100 followers** required for some account-level metrics

---

## Instagram Account-Level Insights

Base query: `GET /<INSTAGRAM_ACCOUNT_ID>/insights`

| Metric | What it measures |
|--------|-----------------|
| `impressions` | Total views of all media in the period |
| `reach` | Unique users who saw any content in the period |
| `profile_views` | Users who viewed the profile in the period |

Supported periods: `day`, `lifetime`

---

## Facebook Page Insights — Full Metrics Available

Base query: `GET /<PAGE_ID>/insights`
Requires: Page access token + `pages_read_engagement` or `read_insights` permission

### Engagement Metrics:
| Metric | What it measures |
|--------|-----------------|
| `page_post_engagements` | Reactions + comments + shares on posts |
| `page_engaged_users` | Unique users who engaged with any page content |

### Reach & Impressions:
| Metric | What it measures |
|--------|-----------------|
| `page_impressions` | Total times any page content was seen |
| `page_impressions_unique` | Distinct users who saw any page content |
| `page_impressions_paid` | Impressions from paid/boosted content |
| `page_impressions_organic` | Impressions from organic content |

### Video:
| Metric | What it measures |
|--------|-----------------|
| `page_video_views` | Video views of 3+ seconds |
| `page_video_complete_views_30s` | Views that reached 30 seconds |

### Followers:
| Metric | What it measures |
|--------|-----------------|
| `page_fan_adds_unique` | New followers in the period |
| `page_fans_locale` | Follower breakdown by locale |

### Revenue (if monetized):
| Metric | What it measures |
|--------|-----------------|
| `content_monetization_earnings` | Earnings from qualified views |
| `monetization_approximate_earnings` | Approximate total earnings |

### Facebook Page Insights Limitations:
- Only available for pages with **100+ likes**
- Metrics update once every **24 hours**
- Only last **2 years** of data available
- Max **90 days** per query using `since`/`until`
- Demographic metrics require data from **100+ people**
- Unique impression values calculated independently — won't always sum to total reach
- Reshared videos return 0 for certain metrics

---

## OAuth Flow for Multi-User SaaS

When a new user connects their account:
1. User clicks "Connect Instagram" on your app
2. Your app redirects to Meta's OAuth dialog with your App ID + requested permissions
3. User logs in and approves permissions
4. Meta redirects back to your app with a short-lived code
5. Your backend exchanges the code for a short-lived token (1 hour)
6. Your backend exchanges the short-lived token for a long-lived token (60 days)
7. Store the long-lived token encrypted in your database
8. Use the token to pull their data on your schedule

**Token refresh:** Long-lived tokens auto-refresh if used within 60 days. If unused for 60 days, user must reconnect.

---

## What You Can Do

- Read analytics/insights from accounts users explicitly connect via OAuth
- Store metrics data in your database to display on their dashboard
- Cache API responses to reduce API calls
- Aggregate anonymized/aggregated data across users (e.g. average engagement rates)
- Share tokens with your own backend services (encrypted, with written agreement if using third-party infrastructure)

---

## What You Cannot Do

- Sell, license, or purchase any platform data
- Share user data with third parties beyond your own service providers
- Build user profiles beyond what's needed to run the service
- Use data to discriminate based on protected characteristics
- Use data to make eligibility decisions (employment, housing, credit, etc.)
- Use platform data for surveillance of any kind
- Retarget users on or off Meta using platform data
- Mix one user's Meta data with another user's advertising campaigns
- Request or store user login credentials directly — OAuth only
- Attempt to decode, re-identify, or de-anonymize any provided data
- Buy or sell likes, followers, or accounts
- Use data beyond the purposes stated in your privacy policy

---

## Security Requirements

- **Encrypt all tokens at rest** — AES-256 minimum
- **HTTPS everywhere** — no HTTP connections
- **Never expose tokens client-side** — all token handling server-side only
- **Never log tokens** in any log files or error reports
- Set up a **vulnerability reporting mechanism** (minimum: a security@ email address)
- Report any unauthorized access or data breach to Meta immediately via their incident reporting form
- Security safeguards must meet **industry standards** given the sensitivity of data handled

---

## Privacy Policy Requirements (Required Before Going Public)

Must be publicly accessible at a real URL. Must explain:
- What data you collect (post metrics, account IDs, access tokens)
- How you process it (stored securely, displayed in dashboard only)
- Why you collect it (to display analytics to the account owner)
- That you never sell it
- How users can request their data be deleted
- How to contact you

Data processing must match exactly what the policy says — Meta can audit this.

---

## Data Deletion Requirements

You must delete all user platform data when:
- User disconnects their account from your app
- User requests deletion
- You discontinue the product or service
- Meta requests deletion for user protection
- Required by applicable law

Keep **proof of deletion** — Meta can audit and request evidence.

---

## App Review Process (Required for Advanced Access / Going Public)

Before letting real users connect:
1. Put app in **Live mode**
2. Complete **Business Verification** for your developer account
3. Submit each permission for review with:
   - Written explanation of why you need it
   - How you use the data
   - How users benefit
4. Record a **screencast video** showing the full OAuth flow working
5. Provide your **privacy policy URL**
6. Meta reviews — may ask follow-up questions
7. Approval can take days to weeks

**What Meta looks for:**
- Are you only requesting permissions you actually use?
- Is data use clearly explained to users before they connect?
- Do you have a real, accessible privacy policy?
- Does the app work without crashing?
- Is the OAuth consent screen clear and accurate?

---

## Compliance & Audit

- Meta can audit your app **up to once per year** (more often if violations are suspected)
- Must supply certifications about data processing on request
- Must provide Meta access to verify compliance
- Annual **Data Use Checkup** to recertify your data usage
- Non-compliance = app suspension (sometimes without notice)
- You are responsible for violations by any third-party service providers you use

---

## Enforcement

Meta may suspend or terminate your app for:
- Violating Platform Terms or Developer Policies
- Failing to respond to monitoring or audit requests
- Circumventing prior enforcement actions
- Negatively impacting the platform or users

Suspension can happen **with or without notice**.

---

## Key Dates

- **April 21, 2025** — `plays`, `clips_replays_count`, `ig_reels_aggregated_all_plays_count` sunset (deprecated)
- **July 2, 2024** — `impressions` metric deprecated for new content in API v22+
- **Feb 3, 2027** — New ad spend transparency rules for apps managing client ads (not relevant for read-only analytics)

---

## Implementation Notes

- `meta_fetcher.py` is already built and ready — just needs `.env` tokens
- For multi-user SaaS: each user gets their own OAuth flow + their own encrypted token in DB
- Standard Access is fine for Gray's own accounts indefinitely (no review needed)
- App Review only required when opening to the public
- Request only `instagram_manage_insights` + `pages_read_engagement` — no other permissions needed for read-only analytics
- Data is never real-time — always up to 48 hours delayed, plan the UI accordingly
