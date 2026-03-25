# My Project — Claude Context

## Who I Am
Gray Davis. Freelance videographer building personal automation tools.
Goals: AI operator, automate business/life, monetize tools, grow social media.

## Preferences
- Python only · default model: claude-sonnet-4-6
- Explain step-by-step (beginner coder — no jargon without explanation)
- Minimize Claude API calls: cache aggressively, batch, use Haiku for simple tasks
- Auto-push to GitHub at end of every session

## Folder Structure
- `python-scripts/` → automation tools
- `web-apps/` → HTML/CSS/JS (future)
- `mobile-apps/` → future
- `business/` → docs, social, emails, leads

## GitHub
- Repo: https://github.com/graydavis33/my-project
- Auto-push: `cd ~/Desktop/my-project && git add . && git commit -m "Session update" && git push`

## Multi-Device Sync (set up 2026-03-25)
All devices stay in sync via GitHub. Claude Code handles this automatically:
- **Session Start hook** → runs `git pull origin main` on every device when you open Claude Code
- **Session Stop hook** → auto-commits and pushes all CLAUDE.md files to GitHub
- Config lives in `.claude/settings.json` (committed to repo, applies on all devices)

**To set up a new device:**
1. Clone the repo: `git clone https://github.com/graydavis33/my-project`
2. Open Claude Code in that folder — hooks run automatically from that point on

**Devices:**
- MacBook — primary
- Windows Desktop — secondary
- iPhone — Claude.ai mobile (manual context paste until Claude Code mobile supports hooks)

## Security
- All `.env`, `token.json`, `client_secret*.json` are gitignored — never commit them
- API keys live only in `.env` files, never hardcoded

## Current Priority List (as of 2026-03-25)
Scored 0–3 across: Unblocks others / Revenue+Time / Showcase / Sellable

| # | Project | Score | Status | Next Action |
|---|---------|-------|--------|-------------|
| 1 | Content Pipeline | 9/12 | Built on Windows | Set up on Mac, test with real video |
| 2 | Content Researcher | 9/12 | LIVE on Mac | V2: add Reddit layer, improvements |
| 3 | Client CRM | 7/12 | Built on Windows | Run setup, configure Google Sheet |
| 4 | Client Onboarding | 7/12 | Built on Windows | Fill .env, review contract template |
| — | Social Media Analytics | 9/12 | LIVE — all 4 platforms active | Schedule via GitHub Actions |
| 5 | Hook Optimizer | 6/12 | Built on Windows | Add .env on Mac |
| 6 | Creator Intel | 5/12 | Built on Windows | Needs YouTube OAuth |
| 7 | Morning Briefing | 4/12 | Built on Windows | Needs full .env setup |

## Project Index
| Project | Path | Status |
|---------|------|--------|
| Email Agent | python-scripts/email-agent/ | LIVE on Mac |
| Invoice System | python-scripts/invoice-system/ | LIVE on Mac |
| Content Researcher | python-scripts/content-researcher/ | LIVE on Mac |
| Social Media Analytics | python-scripts/social-media-analytics/ | LIVE — YouTube, TikTok, Instagram, Facebook |
| Hook Optimizer | python-scripts/hook-optimizer/ | Built on Windows |
| Morning Briefing | python-scripts/morning-briefing/ | Built on Windows |
| Client Onboarding | python-scripts/client-onboarding/ | Built on Windows |
| Client CRM | python-scripts/client-crm/ | Built on Windows |
| Creator Intel | python-scripts/creator-intel/ | Built on Windows |
| Content Pipeline | python-scripts/content-pipeline/ | Built on Windows |
| Footage Organizer | python-scripts/footage-organizer/ | Built on Windows |
| Dashboard | dashboard.html | Live at graydavis33.github.io/my-project/dashboard.html |

> Each project folder has its own CLAUDE.md that loads full details when you're working in that folder.
