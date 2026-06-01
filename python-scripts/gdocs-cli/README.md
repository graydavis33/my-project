# gdocs-cli

CLI for creating, updating, finding, and reading Google Docs from local text files. Used by Claude to push edits straight into Drive without copy-paste.

## What It Does

- `create` — make a new Google Doc from a `.txt`/`.md` file, return the URL
- `update` — replace the contents of an existing Doc with the contents of a file
- `find` — search Drive for Docs by title (returns IDs + URLs)
- `read` — print the plain-text contents of a Doc to stdout

## Setup

1. Copy the OAuth client file from social-media-analytics (same Google Cloud project):
   ```bash
   cp ../social-media-analytics/client_secret.json .
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. First-time auth (opens browser, signs in to Google):
   ```bash
   python auth.py
   ```
   Creates `token.json` in this folder.

4. Make sure these APIs are enabled in your Cloud project:
   - Google Docs API: https://console.developers.google.com/apis/api/docs.googleapis.com/overview
   - Google Drive API: https://console.developers.google.com/apis/api/drive.googleapis.com/overview

   The CLI will print these links if it hits a "not enabled" error.

## Commands

```bash
# Create new doc from a file (title defaults to filename)
python main.py create path/to/file.txt --title "My Doc Title"

# Update existing doc — accepts ID or full URL
python main.py update <doc-id-or-url> path/to/file.txt

# Find docs by title substring
python main.py find "Recommendation"

# Print contents of a doc
python main.py read <doc-id-or-url>
```

## Token Lifecycle

- `token.json` expires every 7 days while the Google Cloud project is in **testing mode**
- If you see `RefreshError` or `invalid_grant`, re-run `python auth.py`
- The `google-oauth-refresh` skill in `.claude/skills/` handles this automatically when triggered

## Scopes

- `https://www.googleapis.com/auth/documents` — read/write Google Docs
- `https://www.googleapis.com/auth/drive.file` — search/list Docs created by this app

## Notes

- Plain text only for now. Markdown/styling support not yet wired (Docs API uses `batchUpdate` style requests, not raw markdown).
- Each tool has its own `client_secret.json` and `token.json` by convention in this workspace.
