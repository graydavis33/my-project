# Sandcastles Watchlists — Build Plan

> **LIVE as of 2026-06-03.** Single Graydient watchlist populated in "My Workspace" (Pro = one workspace; Sai handled via global tools / channel-UUID filter, see below). Watchlist sits at **~59 channels** — the "50 cap" from public pricing did NOT hard-block via the MCP (verify no overage flag in webapp). Composition: Gray's 3 own accounts (IG+TikTok+YT Shorts) + curated low-lift set (editing tips / AI-stack / talking-head gear / small-emerging) + 4 adjacent lenses (colinandsamir, itsryanto, aliabdaal, themayanknegi). **Pending cleanup:** prune cinematic/lifestyle pre-existing picks (blake.ridder, henbu_, qfroost, kevinbparry, prismlensfx, qmike, omgadrian, jordanagajanian) in the webapp — for signal quality, not space. **Gate that won:** production-fit (replicable in a few hours) > follower size > niche. Personal-brand-launch creator added by Gray directly.

---


**Plan:** Pro (≈50-channel cap total) → **25 per watchlist**, 2 lists (Gray + Sai).
**Design rules applied:** niche-fit = hard gate · size-tier = soft sort · skew nano/mid (replicable) · span formats · ~5 lateral picks each · prioritize *active short-form posters* · include own channel · skip saturated gurus · short-form accounts only (IG / TikTok / YT Shorts — NOT long-form YouTube).

**How to fill the `FIND` rows:** after reload + OAuth, run `/sandcastles:channels-search [niche]` per row, then `/sandcastles:channels-add`. Vet each for: posts short-form regularly, currently active, real outlier behavior.

---

## Gray's Watchlist (videography / editing / AI-tools / creator-education) — 25

| # | Tier | Slots | Niche direction | Format focus | Platform lean | Status |
|---|------|-------|-----------------|--------------|---------------|--------|
| 1 | Own | 1 | **@graydient_media** | — | IG primary (add TikTok/YT Shorts later) | SEED |
| 2 | Macro (≥500k) | 5 | Craft creators from your `creator-intel` set — **short-form accounts only** | talking-head, gear, edit-tips | IG/TikTok of: Peter McKinnon, Matti Haapoja, Parker Walbeck, Colin & Samir, MKBHD | SEED (confirm they post short-form; swap any that don't) |
| 3 | Mid (100k–500k) | 10 | 6 direct (videography/editing/AI-editing) + 4 lateral (tech-review, photography, AI-tools, general creator-ed) | b-roll, text-on-screen, tutorial, reaction | IG/TikTok/YT Shorts | FIND |
| 4 | Nano (<100k) | 9 | Your peer set — emerging videography / editing / AI-editing creators | all formats; this is the most replicable tier | IG/TikTok/YT Shorts | FIND |

**Pending:** add Callaway once Gray gives handle/platform (likely Mid or Nano, creator-education lateral).

---

## Sai's Watchlist (founder / business / build-in-public) — 25

| # | Tier | Slots | Niche direction | Format focus | Platform lean | Status |
|---|------|-------|-----------------|--------------|---------------|--------|
| 1 | Own | 1 | **Sai's primary short-form account** (confirm handle) | — | IG/TikTok/YT Shorts | SEED |
| 2 | Macro (≥500k) | 5 | Build-in-public founders / business creators who **film solo, in-office** (NOT mega-gurus) | talking-head, day-in-life | IG/TikTok | FIND (light — avoid saturated names) |
| 3 | Mid (100k–500k) | 10 | 6 direct (founder/business/startup) + 4 lateral (finance, productivity, sales, self-improvement) | talking-head, listicle, text-on-screen, story | IG/TikTok/YT Shorts | FIND |
| 4 | Nano (<100k) | 9 | Emerging founders / build-in-public creators at Trendify's growth stage | all formats; closest to Sai's actual scale | IG/TikTok/YT Shorts | FIND |

---

## Format coverage checklist (verify after filling each list)

Across the 25, make sure you've got at least 2–3 of each format you actually ship:
- [ ] Talking-head (direct-to-cam)
- [ ] B-roll heavy / cinematic
- [ ] Text-on-screen / silent
- [ ] Green-screen / reaction
- [ ] Day-in-life / vlog
- [ ] Listicle / tutorial

---

## Build order
1. Reload VS Code window → run any `/sandcastles:` command → OAuth.
2. Add own channels first (Gray, Sai).
3. Add Macro SEED rows (Gray's 5 craft creators — short-form accounts).
4. Fill Mid + Nano via `/sandcastles:channels-search` per niche direction, vetting for active short-form posting.
5. Run format-coverage checklist; swap to fill gaps.
6. Once populated: `/sandcastles:topics`, `/sandcastles:hooks-watchlist`, `/sandcastles:video-suggest`.
