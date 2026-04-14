---
name: google-oauth-refresh
description: Re-authenticate Google OAuth when token.json expires. Trigger whenever anything breaks with a 401 from Google APIs, a RefreshError, invalid_grant, "token expired", "auth broken", "re-auth google", "auth.py", or when YouTube fetch / Sheets write silently fails. Applies to python-scripts/invoice-system/ and python-scripts/social-media-analytics/ — both use Google OAuth in testing mode where refresh tokens expire every 7 days. Use this skill proactively the moment a Google-auth-shaped error shows up instead of guessing at the cause.
---

# Google OAuth Refresh

Two projects use Google OAuth with `token.json`:
- `python-scripts/invoice-system/` — Gmail + Sheets
- `python-scripts/social-media-analytics/` — YouTube Data API + Sheets

The OAuth consent screen for Google Cloud project `social-media-analytics-488803` is in **testing mode**, so refresh tokens expire every 7 days by design. When anything 401s or throws `RefreshError`, the fix is almost always re-auth.

## When to use

Trigger on any of these symptoms:
- YouTube fetch returns 401 / `HttpError 401`
- Sheets write returns 401
- Error trace mentions `google.auth.exceptions.RefreshError` or `invalid_grant`
- Morning Briefing or weekly analytics silently skipped a platform
- User says "auth broken", "token expired", "re-auth", "google oauth"

## The fix (~30 seconds)

1. **Identify which project is failing.** Check the stack trace:
   - Gmail or invoice Sheets → `python-scripts/invoice-system/`
   - YouTube or analytics Sheets → `python-scripts/social-media-analytics/`

2. **Run the re-auth from that project's directory:**

   ```bash
   cd python-scripts/social-media-analytics && python auth.py
   ```

   Or for invoice-system:

   ```bash
   cd python-scripts/invoice-system && python auth.py
   ```

3. Browser opens → log in with the Google account tied to that project → approve permissions.

4. Script writes a fresh `token.json` in the project directory. Done.

5. Re-run whatever was failing to confirm the fix.

## Why it keeps happening

Google Cloud project `social-media-analytics-488803` is in **testing mode** (not published). In testing mode, refresh tokens expire every 7 days. Two ways to solve permanently:

- **Publish the OAuth app** — removes the 7-day expiry. Requires OAuth verification (one-time, ~30 min of forms).
- **Accept periodic re-auth** — just rerun `auth.py` when it breaks.

Gray currently accepts the re-auth. If this skill fires more than once a month, push back and suggest publishing.

## Security guardrails

- **Never ask Gray to paste tokens or secrets into chat.** The browser flow writes `token.json` — he just logs in.
- `token.json`, `client_secret*.json`, `credentials.json` are gitignored. If you ever see one staged for commit, unstage it immediately.
- If `auth.py` doesn't exist in a project that uses Google OAuth, check that project's CLAUDE.md for its auth pattern before generalizing — don't invent an `auth.py`.

## Don't do this

- Don't re-run paid API calls to "test" the fix before Gray is back — just confirm the auth step succeeded and stop.
- Don't delete `token.json` manually as a "fix" — `auth.py` handles it.
- Don't assume the Anthropic key is the problem. 401s from Google are always Google auth, not Claude auth.
