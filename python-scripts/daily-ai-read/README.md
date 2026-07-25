# Daily AI Read

A daily 5-10 minute email that teaches Gray one AI topic, researched live with web search
and backed by cited sources. Lands in graydavis33@gmail.com around 9:00 AM ET.

## How it works

1. `.github/workflows/daily-ai-read.yml` fires daily at 12:35 UTC (~8:35 AM EDT; GitHub
   adds a variable delay, so the email typically arrives close to 9:00 AM).
2. `main.py` reads `topics-log.json` (every topic already covered), asks Claude
   (claude-sonnet-4-6 + web search) to pick a fresh topic and write the issue, then
   sends it via the Gmail API and archives the HTML to `archive/`.
3. The workflow commits the updated log + archive back to the repo.

Content mix: ~3 of 5 issues are AI fundamentals explainers, ~1 of 5 is real AI news from
the last week, ~1 of 5 is how video/marketing/content people use AI in their work.

## Secrets used (GitHub Actions)

- `ANTHROPIC_API_KEY` — shared with morning-briefing/expense-sync.
- `GMAIL_SEND_TOKEN_JSON` — a copy of email-agent's Gmail token (has gmail.send scope,
  project email-agent-489114, minted in production mode so it does not expire on a timer).
  Source of truth: `/root/my-project/python-scripts/email-agent/token.json` on the VPS.

## Changing things

- **Delivery time**: edit the cron in `.github/workflows/daily-ai-read.yml` (UTC).
- **Content mix / style / length**: edit `SYSTEM_PROMPT` in `main.py`.
- **Recipient**: `TO_ADDRESS` in `main.py`.

## Troubleshooting

- Action fails with a Google 401/invalid_grant: the Gmail token died. Re-copy it from the
  VPS: `ssh root@72.61.10.152 cat /root/my-project/python-scripts/email-agent/token.json`
  piped into the GMAIL_SEND_TOKEN_JSON secret (see the google-oauth-refresh skill).
- Test locally without sending: `python main.py --no-email` (needs ANTHROPIC_API_KEY;
  writes the HTML to `archive/` so you can open it in a browser).
