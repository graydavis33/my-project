# Monetization Pipeline

_Maintained by the `monetization-strategist` subagent (spec: `docs/superpowers/specs/2026-07-08-monetization-strategist-design.md`). Written at `/save`, read at `/prime` ("Monetization Watch"). Gray may edit by hand — the strategist preserves manual edits._

**Rules for this file:** no dollar figures, revenue numbers, or client terms (public repo) — pitches and scores only. KILLED is append-only. One candidate max in NOW.

_Last strategist run: 2026-07-29_
_Backfill: pending (runs on Gray's explicit go — see spec)_

---

## NOW

_(empty — no candidate has cleared the bar yet)_

## WATCHLIST

_(empty)_

## RADAR

- **Licensed content-OS installed into brands** — Gray's long-horizon vision (2026-07-17 idea interview): a productized service where Gray adapts his own content systems (footage organizer, AI editing pipelines, analytics/research, scripting processes) into another brand's ecosystem — customized, rewired, not cookie-cutter — then teaches them to run it at a high level. Recurring revenue = licensing (they pay for the RIGHT to use; Gray retains all IP, they don't own the software/pipelines/structures) + per-change/maintenance/coaching fees folded into the monthly. Moat as Gray frames it = systems too elaborate to easily replicate; open strategic question I raised = whether the durable moat is actually the *software* or *Gray himself* (ongoing judgment + switching cost). Explicitly a "many years from now, if I ever leave my current role" avenue, NOT a near-term build — it's the north star the Sai-era systems quietly become inventory for. Near-term monetizable versions of the SAME asset surfaced in the same interview (unclaimed, Claude-proposed): (1) sell the KNOWLEDGE not the software — package the story-arc playbook, scripting frameworks, footage-folder system, batch workflow as templates + a course for other videographers/editors, funneled by Gray's own build-in-public content; (2) the case study IS the business — "one-man AI content operation for a real high-profile founder" as a positioning/lead-magnet asset. Unscored, no research yet.
- **Footage Organizer as a sellable structure/template** — Gray's own candidate (2026-07-08): package the footage-organizer folder scheme + SQLite index/batch/promote/ship tooling for other videographers/editors. Unscored, no research yet.
- **Social Media Analytics as a sellable product** — Gray's own candidate (2026-07-08): package the analytics tool (already Beta, already Gray's stated Q2 pick for "which tool to monetize first") for other creators. Unscored, no research yet.
- **"Improving content creation" as a service/product direction** — Gray floated this (2026-07-08) as a broader offer shape, not yet a specific product. Needs Gray to narrow scope (what exactly gets sold — audit? templates? done-for-you?) before it's scoreable.
- **IG→LinkedIn format router as a playbook/template product** — the 4-lane router built for Sai (2026-07-29): classify a posted reel's content shape → route to the highest-performing LinkedIn format (framework/list → PDF document carousel; story/lesson → text post + still frame; high-performer → native 9:16 video from original export; raw moment → short text post), grounded in fresh 2026 LinkedIn performance research. Repeatable pattern any creator/agency could run manually in ~5 min/reel — sellable as a playbook/Notion template, or later bundled with the sai-linkedin drafting engine (voice-rules prompt system) as the "pro" tier. Fits the "sell the knowledge, not the software" thread already on RADAR. Natural validation path: Gray uses it on Sai's reels first, then documents it as build-in-public content. Unscored, no research yet. (2026-07-29)
- **Personal AI daily-brief email as a template** — Daily AI Read shipped 2026-07-26 (GitHub Action cron → Claude + web search researches a fresh topic → cited HTML email via Gmail API, zero-maintenance, runs free on public-repo Actions). The generalizable asset is the *pattern*: a personalized daily research-backed email on any topic, self-hosted for pennies. Could be a template/tutorial product or build-in-public content for Gray's AI-workflow brand. Crowded space (AI newsletters everywhere) — the angle is "build your own, personalized, no subscription," not competing as a newsletter. Unscored, no research yet. (2026-07-29)
- **Founder photo harvest script kit** — DDGS image search + Playwright scraping + OpenCV face-detection + auto 9:16 crop + contact-sheet identity verification; built in scratchpad for Vault EP1; identity-verification step (impostor problem is real) is the genuine differentiator vs manual search; target buyer = short-form video editors doing entrepreneur/founder content; technical bar (Playwright + OpenCV) is high for non-coders. No research yet. (2026-07-16)

## KILLED

**Payday Checklist / Personal Finance PWA Starter Kit** (killed 2026-07-17) — Market check hit three simultaneous blockers: (1) multiple free open-source repos already cover the exact stack (Plaid + Firebase + PWA) with no paid demand signal anywhere; (2) buyer onboarding friction is prohibitive — three separate service setups required (Firebase, Plaid, GitHub Actions) before a buyer sees value; (3) Plaid's own free Quickstart docs already solve the "hard parts" Gray documented. Free alternatives: [zenmo-client](https://github.com/tgrander/zenmo-client), [personal-finance-app](https://github.com/jagodin/personal-finance-app), [money-manager PWA](https://github.com/chbandeira/money-manager). Plaid Quickstart: [plaid.com/docs/quickstart](https://plaid.com/docs/quickstart/).
