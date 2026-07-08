# notion-batch

Pushes Sai shorts batch reference docs into a **Notion database** — each video becomes
its own Notion page with sortable columns and a rich body. Reuses the same Notion
integration token as `content-researcher` (no MCP, no new server).

## What it builds

One database **per batch** (each DB is its own batch — no Batch column), where each row = one video:

| Column | Type | Use |
|---|---|---|
| Video | Title | "1A — 5 small things I did to grow my business" |
| Status | Select | Draft / Needs Topics / Sai Review / Approved / Filmed / Sent to Editor / Revisions / Posted |
| Format | Text | simple 3–5 word description of the video (10 max) |
| Orientation | Select | Vertical (9:16, default) / Horizontal (only if footage reuses as long-form B-roll) |
| Sai notes | Text | Sai's notes, filled in Notion |
| Assets | URL | Google Drive folder the editor downloads graphics + b-roll from |
| Reference | URL | the public Original link (never the Sandcastles Watch link) |

The outside DB stays deliberately simple. Each page **body** holds the detail: Topics
(bold, bulleted, per-video — comparison videos list their side-by-side items here),
Verbal hook A/B/C, **Caption hook A/B/C** (on-screen text), Visual hook A/B/C,
**Props**, Editor brief (Structure / Captions / Length / Deliverable +
Keep-drop), an **Editor questions** box (editor asks for missing context; @mention Gray
in a Notion comment for a native notification), and the Reference **Original link only**.
The three hook types are multi-select checkboxes — Sai ticks the options + pairings he wants.

Each page also gets its **own inline "Shot list" child database** (one row per shot) mirroring
Gray's Notion Shot list DB: Section, Shot name, Shot type, Complete?, Shot Notes, Time of Day,
Location, Shoot Day — plus editor columns Duration, Prop, Graphics / effect, Retention beat,
Editor notes (clip-by-clip instruction for exactly what to do in that shot), and **Shot reference**
(Files & media — a reference photo/video/AI illustration of how Gray wants the shot set up, for film-day prep).
The API can't create the Basic/Editor *views* — add those two views by hand once per database.

## Setup (once)

1. `pip install -r requirements.txt`
2. Copy the token: `content-researcher/.env` -> `NOTION_TOKEN` into `notion-batch/.env`
3. In Notion, make a parent page (e.g. "Sai Shorts — Batches"), then share it with the
   integration: page `•••` -> Connections -> add your integration.
4. Create the database:
   ```bash
   python main.py setup --parent "https://www.notion.so/<your-parent-page-url>"
   ```
   This saves the database id to `config.json`.

One database = one batch. For the next batch, run `setup` again with a fresh title to
create a new database, then `push` into it.

## Use it every batch

1. Fill the batch markdown from `_BATCH-DOC-TEMPLATE.md` (v7).
2. Push it:
   ```bash
   python main.py push ../../business/social-media/sai/scripts/2026-07-08-batch-5.md
   ```
   Placeholder pages (title still "[working title]") and the Foundation are skipped.

## Notes
- The markdown stays the master scaffold; Notion is the live home Sai + the editor work in.
- After pushing, topics/status/assets are edited directly in Notion.
- Token expiry is the integration's, not OAuth — it does not rotate on the 7-day cycle.
