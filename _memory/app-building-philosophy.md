---
name: App Building Philosophy
description: Gray's preferences for how to build apps — cost-efficiency, demo-first, security, and scaling approach
type: feedback
---

Build in phases: demo first, scale later.

**Phase approach:**
- Phase 1 (now): Demo only — cheapest viable stack, minimal features, personal use
- Phase 2: Friends + own social media full time — test thoroughly, validate
- Phase 3: Client use (boss's social media, etc.) — upgrade models/features as needed

**Cost efficiency:**
- Use cheapest models that get the job done (Haiku > Sonnet > Opus — start small)
- Avoid paid APIs or services unless free tier covers demo needs
- No cloud hosting costs during demo — run locally or use GitHub Pages (free)
- Cache aggressively to avoid repeat API calls
- Batch API calls where possible

**Security & safety (always required, even in demo):**
- Never hardcode API keys — always use .env files
- Never commit secrets to GitHub (.env, token.json, client_secret.json are gitignored)
- Validate all user inputs at system boundaries
- No storing other people's credentials or data locally
- When adding clients (boss's accounts), use proper OAuth — never store their passwords

**Build philosophy:**
- Solid, working base > feature-rich but buggy
- Demo must be fully functional before adding complexity
- Don't over-engineer for Phase 1 — keep it simple and stable
- Test everything before using with real client accounts

**Why:** Gray is building toward a sellable web service, but wants a safe, stable, low-cost demo first before committing to bigger infrastructure.
