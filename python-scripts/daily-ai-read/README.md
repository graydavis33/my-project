# Daily AI Read

A daily 5-10 minute email that teaches Gray one AI topic, researched live with web search
and backed by cited sources. Lands in graydavis33@gmail.com around 9:00 AM ET.

## How it works

1. `.github/workflows/daily-ai-read.yml` fires daily at 10:36 UTC. GitHub does not run
   scheduled jobs on time — measured delays here are 96–171 minutes — so the email
   actually lands around 9:00 AM ET. See the comment in the workflow before changing it.
2. `main.py` reads `topics-log.json` (every topic already covered), asks Claude
   (claude-sonnet-4-6 + web search) to pick a fresh topic and write the issue, then
   sends it via the Gmail API and archives the HTML to `archive/`.
3. The workflow commits the updated log + archive back to the repo.

## Content buckets (set 2026-07-29)

Every issue is exactly one of three, tagged in the `CATEGORY` field:

| Bucket | Slug | What it covers |
|---|---|---|
| Claude Code | `claude-code` | One capability or workflow at a time — slash commands, CLAUDE.md, subagents, MCP, hooks, plan mode, git inside Claude Code. Always verified against the live docs. |
| Tech literacy | `literacy` | One term Gray keeps hitting but can't yet explain — repo, GitHub, commit, branch, cron, API, terminal, server, .env. |
| Creator AI workflows | `workflows` | A specific named person's non-obvious AI workflow, found on Reddit/YouTube/blogs. High bar — generic tool roundups and anything a working editor already knows are banned. |

**Phase shift:** issues 1–18 run a foundation mix (~3/5 literacy) to build Gray's
vocabulary first; issue 19 onward flips to ~3/5 Claude Code. Controlled by
`FOUNDATION_THROUGH_ISSUE` in `main.py`.

## Reliability

The model drifts off the strict output format regularly — it has emitted preambles,
markdown-bolded labels, and a missing `===HTML===` marker, which crashed the runs on
7/27 and 7/28. `parse_issue()` now tolerates that drift, and `generate_issue()` retries
up to 2x with a corrective message before failing. `python test_parse.py` covers both
real failure shapes. Look for `attempt N: bad output format` in the Action log.

## Secrets used (GitHub Actions)

- `ANTHROPIC_API_KEY` — shared with morning-briefing/expense-sync.
- `GMAIL_SEND_TOKEN_JSON` — a copy of email-agent's Gmail token (has gmail.send scope,
  project email-agent-489114, minted in production mode so it does not expire on a timer).
  Source of truth: `/root/my-project/python-scripts/email-agent/token.json` on the VPS.

## Changing things

- **Delivery time**: edit the cron in `.github/workflows/daily-ai-read.yml` (UTC). Account
  for GitHub's delay — do not set it to the time you want the email.
- **Content buckets / style / length**: edit `SYSTEM_PROMPT` in `main.py`.
- **When the foundation phase ends**: `FOUNDATION_THROUGH_ISSUE` in `main.py`.
- **Recipient**: `TO_ADDRESS` in `main.py`.

## Troubleshooting

- Action fails with a Google 401/invalid_grant: the Gmail token died. Re-copy it from the
  VPS: `ssh root@72.61.10.152 cat /root/my-project/python-scripts/email-agent/token.json`
  piped into the GMAIL_SEND_TOKEN_JSON secret (see the google-oauth-refresh skill).
- Test locally without sending: `python main.py --no-email` (needs ANTHROPIC_API_KEY;
  writes the HTML to `archive/` so you can open it in a browser).
