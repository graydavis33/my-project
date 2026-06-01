# Python & Code Rules

Rules for how to write and modify code in this project.

---

## Language

- Python only — no JavaScript, TypeScript, or other languages unless explicitly asked
- Default model for all AI calls: `claude-sonnet-4-6`
- Use `claude-haiku-4-5-20251001` for simple/cheap tasks (classification, labeling, formatting)
- All API keys and secrets live in `.env` files only — never hardcoded

## API Cost Rules

- Cache aggressively — if a result can be reused, cache it (disk cache preferred)
- Batch API calls wherever possible instead of calling one at a time
- Use Haiku for simple tasks, Sonnet for reasoning/analysis
- If a fix requires re-running a paid API call, ask Gray before running

## Code Style

- Keep it simple — don't over-engineer
- No premature abstractions — three similar lines beats a helper function for one use
- No error handling for things that can't happen — only validate at real boundaries
- No backwards-compatibility hacks — just change the code
- Don't add docstrings, type annotations, or comments to code that wasn't changed

## File Structure

- All Python automation tools live in `python-scripts/{project-name}/`
- Each project has its own `.env` file and `requirements.txt`
- Temp/intermediate files go in `.tmp/` inside the project folder
- Final outputs go to cloud services (Google Sheets, Notion, Slack) — not local files

## Security

- `.env`, `token.json`, `client_secret*.json`, `credentials.json` are always gitignored
- Never commit secrets — check `.gitignore` before any commit
- Root `.gitignore` covers all projects