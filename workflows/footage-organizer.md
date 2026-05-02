# Workflow: Footage Organizer

**Status:** LIVE on Mac + Windows
**Cost:** ~$0.003/clip (Claude Haiku Vision, 4 frames). Re-runs hit the permanent cache = $0.
**Script:** `python-scripts/footage-organizer/`

---

## Objective

Drop a card's worth of raw footage into a dated RAW folder → run one command → Claude Vision classifies every clip by format (long-form vs short-form, by orientation) + 17 content categories. Then archive what you didn't use into the Footage Library, and mark what you did use as "used" when the video ships.

Reliability bar: **Gray never has to manually re-sort a clip.**

---

## Library Structure (per client) — updated 2026-05-01

The organizer operates on a client library root (`SAI_LIBRARY_ROOT` or `GRAYDIENT_LIBRARY_ROOT` in `.env`). Each library has nine top-level folders:

```
00_TEMPLATES/                                    LUTs, title cards, Premiere templates
01_ORGANIZED/<date>/                             drop loose footage here for the day's shoot
01_ORGANIZED/<category>/<date>/                  AI-categorized output (post-organize)
02_ACTIVE_PROJECTS/                              active editing projects
03_DELIVERED/shorts · linkedin · episodes/       finished published exports
04_ARCHIVE/                                      retired projects
05_FOOTAGE_LIBRARY/<category>/W##_MMM-DD-DD/     permanent reusable footage, weekly
06_ASSETS/brand · fonts · music · sfx/           reusable assets
07_QUERY_PULLS/<slug>/                           temp query results — deleted after publish
08_AI_EDITS/<pipeline>/<source>/                 AI pipeline outputs grouped by pipeline
.footage-index.sqlite                            SQLite index of every clip
```

`RAW_INCOMING` was removed in the 2026-05-01 restructure — Gray now drops loose footage directly into `01_ORGANIZED/<date>/` and the organize command categorizes in place.

Archive subfolders now use the **week label** (`W##_MMM-DD-DD`), not the exact shoot date. Week numbering: W01 = the ISO week containing 2026-04-15 (Sai project Day 1). All archive operations route through `week_utils.week_label_for(date)`.

### Weekly Workflow

```bash
# Every Monday: create this week's folders under all 17 categories
python cli_index.py --client sai create-week

# Backfill a specific past week
python cli_index.py --client sai create-week --week 2026-04-13
```

Idempotent. Future weeks are not pre-scaffolded — only weeks that have started exist on disk.

### Pull Lifecycle (no-duplication rule)

Every clip lives in ONE permanent location. Pull operations create temp duplicates in `08_QUERY_PULLS/<slug>/`. After the edit ships, run cleanup:

```bash
# Interactive: prompts per-folder
python cli_index.py --client sai pull-cleanup

# Bulk-delete pulls 30+ days old (no prompts)
python cli_index.py --client sai pull-cleanup --older-than 30
```

---

## Commands

```bash
cd python-scripts/footage-organizer

# First-time setup for a client (creates all folders)
python main.py --client sai --setup
python main.py --client graydient --setup

# Organize today's card (reads from 01_ORGANIZED/{today})
python main.py --client sai

# Organize a specific date
python main.py --client sai --date 2026-04-15

# Organize old/undated footage (any label works as the subfolder name)
python main.py --client sai --date old-broll

# Default mode is MOVE (RAW folder deleted after). Pass --copy to keep originals.
python main.py --client sai --copy

# Process loose footage already in the library (e.g., 01_ORGANIZED/<date>/ flat dump).
# --source defaults to MOVE; --format overrides orientation detection; --top-level-only
# skips subdirs (existing categorized output, Premiere project files, etc.)
python main.py --client sai --source "D:/Sai/01_ORGANIZED/2026-04-21" --date 2026-04-21 --format short-form --top-level-only

# Archive an organized date into the Footage Library as "unused"
# Run after pulling selects into 02_ACTIVE_PROJECTS/. Deletes 01_ORGANIZED/{date}/.
python main.py --client sai --archive 2026-04-16

# Mark clips from a shoot date as used (unused/ → used/)
# Run after publishing a video that used footage from that date
python main.py --client sai --mark-used 2026-04-16
```

---

## The 17 Categories

Defined in `config.py → CATEGORIES`. Mutually exclusive — the model picks exactly one per clip, or falls back to `misc` when two could fit. Never invents folders.

Category names map directly to folder names. Use the eval harness before adding or renaming any.

---

## Format Detection

**Orientation only.** Vertical (height > width) → `short-form/`. Horizontal → `long-form/`. 4K vs 1080p is irrelevant and explicitly rejected (see decision 2026-04-19 — Sai's workflow shoots 1080p for long-form now).

---

## What It Does (Step by Step)

1. Reads `01_ORGANIZED/{date}/` (recursive — finds `.mp4` / `.mov`)
2. Reads width/height with ffprobe → picks `long-form/` or `short-form/`
3. Checks `.cache.json` (keyed by filename + filesize) — skips analysis if hit
4. Extracts 4 frames per clip at 20/40/60/80% via ffmpeg
5. Sends all 4 frames to Claude Haiku Vision in one call; model returns exactly one category from the CATEGORIES list
6. Copies (or moves with `--move`) into `01_ORGANIZED/{category}/{date}/`
7. Writes the cache so the clip is never analyzed twice
8. Deletes `01_ORGANIZED/{date}/` automatically on success (no dangling RAW)

---

## Archive + Mark-Used Flow

- **`--archive {date}`** moves everything from `01_ORGANIZED/{date}/` into `05_FOOTAGE_LIBRARY/unused/{category}/{date}/` using the cached category from step 5. Deletes the organized folder afterwards.
- **`--mark-used {date}`** promotes all clips from `unused/*/{date}/` into `used/*/{date}/`. Run this after you publish a video that pulled from that shoot day.

---

## Cache Sync Guardrail (2026-04-20 fix)

`.cache.json` is committed to git as the cross-machine sync layer. Before any cache-touching command (`organize`, `--archive`, `--mark-used`), the script runs a read-only `git fetch` + `git log HEAD..@{u} -- .cache.json` and WARNS + PROMPTS if the remote is ahead.

- Default prompt answer is "no" — type `y` to override
- Non-blocking if git is unavailable or no upstream set
- Silent on clean state — only speaks up when there's actually a cache drift

**Why this exists:** 2026-04-16 misc/ incident. Windows ran `--archive` without pulling the Mac's cache update → 40 clips missed the cache → fell back to `misc/`.

---

## How to Handle Failures

| Problem | Fix |
|---------|-----|
| ffmpeg not found | Install ffmpeg + ffprobe; script aborts on startup if missing |
| Clips landing in `misc/` | Either ambiguous content (expected — review manually) OR cache drift (see guardrail above) |
| `--client` unknown | Add `SAI_LIBRARY_ROOT` or `GRAYDIENT_LIBRARY_ROOT` to `.env` |
| Category looks wrong | Run the eval harness (`eval.py`) against `test-set.csv` before tightening the prompt — never tune blind |
| New category needed | Last resort. First check if `misc` + manual review handles it. See `CLAUDE.md` in the project folder. |

---

## Env Vars Required

```
ANTHROPIC_API_KEY
SAI_LIBRARY_ROOT         # absolute path to Sai's library root
GRAYDIENT_LIBRARY_ROOT   # absolute path to Graydient Media's library root
```

---

## Iteration Discipline

See `python-scripts/footage-organizer/CLAUDE.md` for the rules when improving the organizer:

- Run the latest eval first — never tune blind
- Look at the confusion matrix — find the worst-confused pair
- Tighten the prompt for that pair specifically; don't mass-rewrite
- Commit one tightening per commit
- Never restore 4K-based format detection
- Never add a `voiceover` category (explicitly rejected)

---

## Cost Estimate

| Shoot Size | First-run cost | Re-run (cached) |
|------------|----------------|-----------------|
| 20 clips | ~$0.06 | $0 |
| 100 clips | ~$0.30 | $0 |
| 1,000 clips | ~$3.00 | $0 |

---

## v2: Index + Pull

A SQLite index (`.footage-index.sqlite` at the library root) makes the library queryable. `pull` builds Premiere-ready folders via hardlinks — folders stay the source of truth.

### Commands

- `python cli_index.py --client sai index` — refresh SQLite index from library
- `python cli_index.py --client sai pull --orientation vertical --filmed-date YYYY-MM-DD` — Premiere-ready folder of vertical clips from that day
- `python cli_index.py --client sai pull --category interview-solo --filmed-after YYYY-MM-DD` — all solo interviews since that date

All `pull` filters: `--category`, `--orientation`, `--filmed-date`, `--filmed-after`, `--filmed-before`, `--min-duration`, `--max-duration`

### Talking to Claude in chat

> Gray says: "pull all vertical clips from April 16"
> Claude translates to: `python cli_index.py --client sai pull --orientation vertical --filmed-date 2026-04-16`
>
> Gray says: "give me every solo interview from this past week"
> Claude translates to: `python cli_index.py --client sai pull --category interview-solo --filmed-after 2026-04-20`

### Daily Sai loop

```
1. Dump card → 01_ORGANIZED/<today>/
2. python main.py --client sai          (Vision categorizes + files into FOOTAGE_LIBRARY/)
3. python cli_index.py --client sai index   (refresh the SQLite index)
4. As you edit, pull working sets:
   python cli_index.py --client sai pull --orientation vertical --filmed-date <day>
   python cli_index.py --client sai pull --category interview-solo --filmed-date <day>
   etc.
```
