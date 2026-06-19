# Footage Organizer — New Hire Operator's Manual

**Status:** LIVE on Mac (primary) + Windows
**Cost:** Free for everyday use (`index`, `pull`, `batch`, `promote`, `ship` make **zero** AI calls). Only the paused AI auto-sort (`main.py`) costs money (~$0.003/clip).
**Script folder:** `python-scripts/footage-organizer/`
**Main program (newest version):** `cli_index.py`
**This doc:** a teach-from-scratch guide. For the dev/iteration rules, see the companion [footage-organizer.md](footage-organizer.md).

> Read this top-to-bottom once. After that, the **Cheat Sheet** at the bottom is all you'll need day-to-day.

---

## 1. What this tool actually is (the 30-second version)

It's a **filing system for video clips**, run from the command line. It does two jobs:

1. **Keeps the footage drive organized** — every clip lives in exactly one place, in a predictable folder structure, so you (and Premiere) can always find it.
2. **Makes the drive searchable** — it builds a hidden database (an "index") of every clip so you can instantly grab, say, "every vertical clip filmed on June 10" without scrolling through folders.

That's it. It moves files into the right folders and remembers what's where.

### The single most important idea: **folders are the truth**

The tool does **not** decide where clips go based on magic. **The folder a clip sits in IS its category.** If a clip is in a folder called `interview-solo`, the tool records it as `interview-solo`. If you make a brand-new folder called `b-roll-nyc`, the tool happily treats `b-roll-nyc` as a category too.

So the database never "fights" the folders — it just reads them. If you ever move a clip by hand, just re-run `index` and the database catches up. **You can't really break it by reorganizing folders.**

---

## 2. The mental model: how footage flows

Picture a clip's life from camera to archive. Each box is a top-level folder on the drive:

```
  CAMERA CARD
      │  (you copy files off the card)
      ▼
  01_ORGANIZED/        ← raw footage lands here, sorted into shoots
      │  (you edit a video using these clips)
      ▼
  02_ACTIVE_PROJECTS/  ← the Premiere project you're editing right now
      │  (video is finished + exported)
      ▼
  03_DELIVERED/        ← the final published export
      │  (cleanup time)
      ├─► 04_ARCHIVE/         ← the retired edit project gets parked here
      └─► 05_FOOTAGE_LIBRARY/ ← the raw clips get filed for permanent reuse
```

And off to the side, any time you need clips for an edit:

```
  05_FOOTAGE_LIBRARY  ──(pull)──►  07_QUERY_PULLS/  ← a TEMPORARY working folder
                                    (delete it after the edit ships)
```

The tool's commands are just the arrows in those diagrams. Once you know which arrow you want, you know which command to run.

---

## 3. The library structure (the 9 folders)

Everything lives under one "library root" per client. On Gray's Mac that's `/Volumes/Footage/Sai/` (on Windows it's `D:/Sai/`). Inside:

| Folder | Plain-English purpose |
|---|---|
| `00_TEMPLATES/` | Reusable stuff: Premiere templates, LUTs (color presets), title cards. |
| `01_ORGANIZED/` | **The inbox.** Raw footage off the card lands here, grouped by shoot date or by batch. |
| `02_ACTIVE_PROJECTS/` | Edit projects you're **working on right now**. |
| `03_DELIVERED/` | **Finished, published** video exports. |
| `04_ARCHIVE/` | Old edit projects you're done with — parked, not deleted. |
| `05_FOOTAGE_LIBRARY/` | **The permanent home** for all reusable raw clips, sorted by category. |
| `06_ASSETS/` | Brand assets — fonts, music, sound effects, graphics (the HyperFrames renders go here). |
| `07_QUERY_PULLS/` | **Temporary scratch folders.** Output of `pull`. Delete after the edit ships. |
| `08_AI_EDITS/` | Outputs from the AI editing pipelines, grouped by pipeline. |

There's also a hidden file at the root, `.footage-index.sqlite` — that's the searchable database. You never open it directly; the tool manages it.

### Two folders have an extra layer of structure

**`02 / 03 / 04` are split by FORMAT** — the kind of video:
- `episodes/` (long-form)
- `shorts/` (vertical short-form)
- `linkedin/`

…and then by **week**. So a finished short looks like:
`03_DELIVERED/shorts/W09_Jun-8-14/`

**`05_FOOTAGE_LIBRARY` is split by CATEGORY, then by week:**
`05_FOOTAGE_LIBRARY/interview-solo/W09_Jun-8-14/C2574.MP4`

---

## 4. Vocabulary a new hire needs (glossary)

| Term | What it means |
|---|---|
| **Library root** | The top folder for one client (`/Volumes/Footage/Sai`). Set in `.env`. |
| **Client** | Which library to act on. Currently `sai` or `graydient`. You pass it with `--client`. |
| **Index** | The searchable database of every clip. "Re-index" = update it after files change. |
| **Category** | What's in a clip (`interview-solo`, `insert-hands`, …). **= the folder name** it sits in. |
| **Format** | The video shape: `long-form` (horizontal) or `short-form` (vertical). Auto-detected from the clip's dimensions. |
| **Format bucket** | The folders `episodes` / `shorts` / `linkedin` inside 02/03/04. |
| **Week label** | A folder like `W09_Jun-8-14`. Week 1 (`W01`) = the week of Apr 15, 2026 (Sai project Day 1). The tool calculates these for you. |
| **Pull** | Grab a working set of clips out of the library into a temporary folder for editing. |
| **Slug** | The auto-generated name of a pull folder, e.g. `2026-06-10-vertical`. |
| **Clip ID** | The camera's filename, e.g. `C2574`. Sony cameras name files `C####`. |
| **Batch / Vid** | A "batch shoot" is a day where you film several short videos back-to-back. Each video = a "Vid". They get filed as `Batch_02/Vid_01/`, etc. |
| **Sidecar** | A small companion file the camera writes next to a clip (e.g. `C2493M01.XML`). The tool keeps these with their clip automatically. |

---

## 5. The two programs (and why one is paused)

The folder has **two** command-line programs. Know the difference:

| Program | What it's for | Status |
|---|---|---|
| **`cli_index.py`** | The everyday tool: index, pull, batch, promote, ship, week folders, cleanup. **Free** (no AI). | **This is what you use.** |
| **`main.py`** | The original AI auto-sorter: looks at each clip with Claude Vision and guesses its category. Costs money. | **Paused.** Folders are made by hand now. |

**Why `main.py` is paused:** Gray decided hand-made / batch-filed folders are more reliable than the AI guesses for his workflow. So **don't run `main.py` unless Gray specifically asks to turn AI auto-sorting back on.** The rest of this manual is about `cli_index.py`.

---

## 6. First-time setup (do this once per machine)

You only do this when setting up the tool on a new computer.

```bash
# 1. Go to the tool folder
cd ~/Desktop/my-project/python-scripts/footage-organizer

# 2. Turn on the project's Python environment ("venv" = isolated Python)
source .venv/bin/activate        # Mac/Linux
#  .venv\Scripts\activate        # Windows

# 3. Install the Python packages it needs (only if venv is fresh)
pip install -r requirements.txt
```

**Two more things must be true:**

1. **`ffmpeg` is installed** and on your PATH. It's the tool that reads video dimensions/dates. Test with `ffmpeg -version`. (Only needed for `index` — the parts that read clip metadata.)
2. **A `.env` file exists** in the tool folder with the library paths. It's already set up on Gray's machines. It contains:
   ```
   SAI_LIBRARY_ROOT=/Volumes/Footage/Sai
   GRAYDIENT_LIBRARY_ROOT=...
   ANTHROPIC_API_KEY=...          # only needed if you re-enable main.py's AI
   ```
   > **Security rule:** the `.env` holds secrets and is never committed to GitHub. Never paste API keys into chat — handle them in your own terminal.

**The drive must be plugged in.** If `/Volumes/Footage/Sai` isn't mounted, every command will stop with a clear "does not exist on disk" error.

> From here on, examples assume you've already `cd`'d into the folder and run `source .venv/bin/activate`. If you skip the venv, just use `.venv/bin/python` instead of `python`.

---

## 7. The commands — one by one, with examples

Every command follows the same shape:

```bash
python cli_index.py --client sai <COMMAND> [options]
```

`--client sai` says "act on Sai's library." (`--client graydient` for the other one.) Below, each command has: **what it does → when to use it → a real example → what you'll see.**

---

### 7.1 `index` — update the searchable database

**What it does:** Walks `01_ORGANIZED/` and `05_FOOTAGE_LIBRARY/`, records every clip (its folder/category, format, filmed date, length, size) into the database, and removes entries for files that no longer exist.

**When to use it:** After you add, move, or delete footage by hand. (The other commands that change files re-index automatically — this is the manual "catch up" button.)

```bash
python cli_index.py --client sai index
```

**What you'll see:**
```
  Indexed 841 clip(s), skipped 0, removed 0 missing
  DB: /Volumes/Footage/Sai/.footage-index.sqlite
```
- **Indexed** = clips recorded/refreshed. **skipped** = files it couldn't read (corrupt/odd). **removed** = database entries whose files are gone.
- Safe to run anytime, as often as you want. It also auto-creates the current week's folders if they don't exist yet.

---

### 7.2 `pull` — grab a working set of clips for an edit

**What it does:** Searches the database with the filters you give it and **copies** the matching clips into a fresh temporary folder under `07_QUERY_PULLS/`. **It never moves or deletes your originals** — pull only makes a working copy.

**When to use it:** When you're about to edit and want just the relevant clips in one place.

**The filters you can combine:**

| Filter | Meaning | Example value |
|---|---|---|
| `--category` | A category/folder name | `interview-solo` |
| `--orientation` | `vertical` or `horizontal` | `vertical` |
| `--filmed-date` | Exactly this day | `2026-06-10` |
| `--filmed-after` | On/after this day | `2026-06-01` |
| `--filmed-before` | On/before this day | `2026-06-15` |
| `--min-duration` | At least N seconds long | `5` |
| `--max-duration` | At most N seconds long | `30` |
| `--by-week` | Sort the results into weekly subfolders | (no value, it's a switch) |

**Example — "give me every vertical clip filmed on June 10":**
```bash
python cli_index.py --client sai pull --orientation vertical --filmed-date 2026-06-10
```

**What you'll see:**
```
  Pull → /Volumes/Footage/Sai/07_QUERY_PULLS/2026-06-10-vertical
  Linked 23 clip(s); fallback copies: 23
```
The folder name (`2026-06-10-vertical`) is built automatically from your filters. ("fallback copies" just means it copied the files — normal on Gray's drive. Don't worry about it.)

**More examples:**
```bash
# Every solo-interview clip from this past week
python cli_index.py --client sai pull --category interview-solo --filmed-after 2026-06-08

# Short vertical clips (under 30s) of hands, sorted into weekly subfolders
python cli_index.py --client sai pull --category insert-hands --orientation vertical --max-duration 30 --by-week
```

> ⚠️ **Heads-up on "vertical":** most of Sai's clips are Sony files stored as 1920×1080 (horizontal) but with a rotation flag so they *display* vertical. `--orientation vertical` matches on the **stored** shape and can MISS those. If a vertical pull comes back nearly empty, that's why — ask Gray or use the `footage-puller` agent for content-based searches.

---

### 7.3 `batch` — file a whole batch shoot in one command

**What it does:** When you film several short videos in one session, this sorts the takes into `01_ORGANIZED/Batch_NN/Vid_MM/` folders and re-indexes. No AI, no hand-dragging.

**When to use it:** Right after copying a batch-shoot's card to a temp folder.

**The key option is `--map`** — it tells the tool which clips belong to which video:
- `1:C2493-C2495` → Vid 1 gets clips C2493, C2494, C2495 (a **range**)
- `2:C2496,C2498` → Vid 2 gets C2496 and C2498 (a **list**)
- `3:C2500` → Vid 3 gets just C2500 (a **single** clip)

**Example:**
```bash
python cli_index.py --client sai batch --num 2 \
    --from "01_ORGANIZED/2026-06-07" \
    --map "1:C2493-C2495 2:C2496-C2498 3:C2500"
```

- `--num 2` → creates `Batch_02/`.
- `--from` → the folder holding the raw clips (relative to the library root, or a full path).
- `--map` → the Vid-to-clips plan, space-separated.

**What you'll see:**
```
  Batch 2 ← /Volumes/Footage/Sai/01_ORGANIZED/2026-06-07
  → /Volumes/Footage/Sai/01_ORGANIZED/Batch_02

    Vid_01 ← 3 file(s): C2493.MP4, C2494.MP4, C2495.MP4
    Vid_02 ← 3 file(s): C2496.MP4, C2497.MP4, C2498.MP4
    Vid_03 ← 1 file(s): C2500.MP4

  Moved 7 file(s) into Batch_02.
  Re-indexed: 841 clip(s), skipped 0, removed 0 missing
```

**Safety nets built in:**
- It **reports any clip you mapped that has no matching file**, and **any video file left unmapped** — nothing is silently lost.
- Sony sidecar files (the `.XML` companions) move with their clip automatically.
- Re-running the same command is safe — clips already filed are left alone.

---

### 7.4 `promote` — move a finished project to the next stage

**What it does:** Moves a project folder/file from one stage to the next: **Active → Delivered**, or **Delivered → Archive**. It figures out the format bucket and week folder for you and files it correctly.

**When to use it:** When a video changes status (you finished editing it; or you're retiring a delivered project).

```bash
# Finished editing → mark delivered
python cli_index.py --client sai promote --item "Batch 2 Vid 1 - 10 Truths About Ads" --to delivered

# Retire a delivered project → archive
python cli_index.py --client sai promote --item "Subway Challenge Day 1" --to archive
```

- `--item` = the **exact** name of the folder (or file) to move.
- `--to delivered` automatically pulls from Active; `--to archive` pulls from Delivered. (Override the source with `--from active|delivered` if needed.)
- Lands in `<stage>/<format>/<current-week>/`. Use `--week 2026-06-10` for a specific week, or `--no-week` to skip the week subfolder.
- The **format** (episodes/shorts/linkedin) is guessed from where the item currently lives; pass `--format shorts` if it can't tell.

**Safety:** it only **moves** (never copies or deletes), it **refuses to overwrite** an existing destination, and if the name matches two places it **stops and lists them** so you can be specific.

---

### 7.5 `ship` — one-step cleanup after a video is published

**What it does:** This is the everyday "I'm done, clean up after me" command. After a finished video lands in `03_DELIVERED`, `ship` does **two** chores at once:
1. Moves the **edit project** from `02_ACTIVE_PROJECTS` → `04_ARCHIVE`.
2. Moves the **raw footage** from `01_ORGANIZED` into the library, then re-indexes. A **batch** video's interview originals go to `05_FOOTAGE_LIBRARY/_BATCHES/Batch_NN/Vid_MM/` (their own scheme, kept out of b-roll search); a loose `--footage` shoot goes to `05_FOOTAGE_LIBRARY/<category>/<week>/`.

**It shows you the plan first and moves NOTHING until you type `y`.**

```bash
python cli_index.py --client sai ship --video "Batch 2 Vid 1 - 10 Truths About Ads"
```

**What you'll see:**
```
  Ship cleanup for: Batch 2 Vid 1 - 10 Truths About Ads

  Planned moves (nothing has moved yet):
    • edit project → archive
        02_ACTIVE_PROJECTS/shorts/W01_Apr-15-19/Batch 2 Vid 1 - 10 Truths About Ads
        → 04_ARCHIVE/shorts/W09_Jun-8-14/Batch 2 Vid 1 - 10 Truths About Ads
    • raw footage → library
        01_ORGANIZED/Batch_02/Vid_01
        → 05_FOOTAGE_LIBRARY/Batch 2 Vid 1 - 10 Truths About Ads/W09_Jun-8-14

  Proceed with these moves? [y/N]:
```
Type `y` to do it, anything else to cancel. Add `--yes` to skip the prompt.

- It finds the footage by reading "Batch N Vid M" out of the video name. If it can't, pass `--footage <folder>`.
- If it can only find one of the two halves, it **warns and skips the other** rather than guessing.
- Other overrides: `--project "exact name"`, `--category <library subfolder>`, `--format`, `--week`/`--no-week`.

> **`ship` vs `promote`:** `promote` does ONE move you name explicitly. `ship` is the all-in-one post-publish cleanup (archive the project AND file the footage) with a preview. For finished videos, reach for `ship`.

---

### 7.6 `create-week` — pre-build a specific week's folders

**What it does:** Creates the empty weekly folders for a given week across the library (the 17 categories + the 3 format buckets in 02/03/04).

**When to use it:** Almost never by hand — `index`, `pull`, and the other commands auto-create the **current** week. Use `create-week` only to **backfill a past week** or **pre-build a future one**.

```bash
python cli_index.py --client sai create-week --week 2026-04-13
```
Idempotent (running it twice does no harm). Defaults to today's week if you omit `--week`.

---

### 7.7 `pull-cleanup` — delete temporary pull folders

**What it does:** Clears out the `07_QUERY_PULLS/` scratch folders once you're done editing, so duplicate copies don't pile up on the drive.

**When to use it:** After a video ships and you no longer need its pulled working set.

```bash
# Interactive — asks y/N per folder
python cli_index.py --client sai pull-cleanup

# Bulk — auto-delete anything 30+ days old, no prompts
python cli_index.py --client sai pull-cleanup --older-than 30
```

**What you'll see (interactive):**
```
  Pull cleanup (SAI)
  Root: /Volumes/Footage/Sai/07_QUERY_PULLS

  Delete 2026-06-10-vertical? (23 files, 7d old) [y/N]: y
    deleted 2026-06-10-vertical

  Done. Deleted 1 of 3 folder(s).
```

---

### 7.8 (Reference only) `main.py` — the paused AI auto-sorter

You won't run this unless Gray re-enables AI sorting. For completeness, it categorizes raw clips with Claude Vision:
```bash
python main.py --client sai                 # categorize today's 01_ORGANIZED/_INBOX/<date>/ dump
python main.py --client sai --date 2026-06-10
python main.py --client sai --archive 2026-06-10   # file an organized date into the library
```
It costs ~$0.003/clip (cached re-runs are free). **Leave it alone unless asked.**

---

## 8. Everyday recipes (the workflows you'll actually do)

### Recipe A — A normal shoot day
```bash
# 1. Copy the card into 01_ORGANIZED/<today>/ (in Finder)
# 2. Refresh the database so the new clips are searchable
python cli_index.py --client sai index
# 3. Pull what you need to edit
python cli_index.py --client sai pull --orientation vertical --filmed-date 2026-06-17
```

### Recipe B — A batch shorts shoot
```bash
# 1. Copy the card into a temp folder, e.g. 01_ORGANIZED/2026-06-17
# 2. File every video's takes in one shot
python cli_index.py --client sai batch --num 3 \
    --from "01_ORGANIZED/2026-06-17" \
    --map "1:C2600-C2602 2:C2603-C2605 3:C2606"
```

### Recipe C — A video is finished and published
```bash
# 1. Confirm the export is sitting in 03_DELIVERED/
# 2. One-step cleanup (archive the project + file the footage), review the plan, type y
python cli_index.py --client sai ship --video "Batch 3 Vid 1 - <title>"
# 3. Delete the scratch pull folder you used while editing
python cli_index.py --client sai pull-cleanup
```

---

## 9. You can also just ask Claude

You don't have to memorize flags. Tell Claude in plain English and it runs the right command. Examples of how requests map:

| You say… | Claude runs… |
|---|---|
| "pull all vertical clips from June 10" | `pull --orientation vertical --filmed-date 2026-06-10` |
| "give me every solo interview from this past week" | `pull --category interview-solo --filmed-after 2026-06-08` |
| "file this batch — 3 videos, clips C2600–C2606" | `batch --num N --from ... --map ...` |
| "mark Batch 3 Vid 1 as delivered" | `promote --item "..." --to delivered` |
| "clean up after the video I just posted" | `ship --video "..."` then `pull-cleanup` |

For "find clips of Sai doing X" (content-based, not date/category), there's a dedicated **`footage-puller`** agent that's better at it — just ask.

---

## 10. The 17 standard categories

These are the built-in category folders in `05_FOOTAGE_LIBRARY/` (you can also make your own freeform folders — the tool indexes those too).

| Group | Categories |
|---|---|
| **People — on camera** | `interview-solo`, `interview-duo`, `walk-and-talk` |
| **People — off camera** | `candid-people`, `reaction-listening`, `crowd-group` |
| **Details / objects** | `insert-hands`, `insert-product`, `insert-food-drink`, `insert-detail` |
| **Screens** | `screens-and-text` |
| **Environments** | `establishing-exterior`, `establishing-interior`, `environment-detail` |
| **Movement** | `action-sport-fitness`, `transit-vehicles` |
| **Catch-all** | `misc` (used when nothing else clearly fits) |

---

## 11. Hard safety rules (memorize these)

1. **Every clip lives in exactly ONE permanent place** (`05_FOOTAGE_LIBRARY/`). The only allowed duplicates are temporary pulls in `07_QUERY_PULLS/` — and you delete those after the edit ships (`pull-cleanup`).
2. **The tool never overwrites or deletes your footage.** `pull` copies. `batch`/`promote`/`ship` move and **refuse to overwrite** an existing destination. The only command that deletes is `pull-cleanup`, and only the scratch pull folders.
3. **Plan-first commands show you the plan.** `ship` moves nothing until you type `y`.
4. **Folders are the truth.** Move clips by hand if you want, then run `index` to resync. You won't corrupt anything.
5. **Don't run `main.py`** (the AI sorter) unless Gray asks — it's intentionally paused.
6. **The drive must be mounted** and you must pass `--client sai` (or `graydient`).

---

## 12. Troubleshooting

| What you see / what happened | Fix |
|---|---|
| `Error: SAI_LIBRARY_ROOT does not exist on disk` | The footage drive isn't plugged in / mounted. Plug it in and retry. |
| `Error: SAI_LIBRARY_ROOT not set in .env` | The `.env` file is missing the path. Check `python-scripts/footage-organizer/.env`. |
| `Error: index not built yet` (on a `pull`) | Run `index` first, then pull again. |
| A vertical pull returns almost nothing | Sony clips are stored horizontal + rotation flag — `--orientation vertical` misses them. Use the `footage-puller` agent or filter by category/date instead. |
| `'<name>' is ambiguous` (promote/ship) | Two items share that name. Re-run with the exact path, or pass `--project "exact name"`. |
| `destination already exists, refusing to overwrite` | Something's already filed under that name/week. The tool won't clobber it — move/rename by hand or pick a different `--week`. |
| `ship` says "couldn't locate the raw footage" | The video name didn't contain a parseable "Batch N Vid M." Add `--footage <folder>`. |
| `ffmpeg not found` (during `index`) | Install ffmpeg and make sure it's on PATH (`ffmpeg -version`). |
| Some clips landed in `misc` | `misc` is the "unsure" bucket — review and move them by hand, then `index`. |
| `command not found: python` | You didn't activate the venv. Run `source .venv/bin/activate`, or use `.venv/bin/python`. |

---

## 13. Cheat Sheet (print this)

```bash
cd ~/Desktop/my-project/python-scripts/footage-organizer
source .venv/bin/activate        # do once per terminal session

# Refresh the searchable database (after any hand-changes)
python cli_index.py --client sai index

# Pull a working set into 07_QUERY_PULLS/ (copies; never moves originals)
python cli_index.py --client sai pull --orientation vertical --filmed-date 2026-06-17
python cli_index.py --client sai pull --category interview-solo --filmed-after 2026-06-08

# File a batch shoot → 01_ORGANIZED/Batch_NN/Vid_MM/
python cli_index.py --client sai batch --num 3 --from "01_ORGANIZED/2026-06-17" \
    --map "1:C2600-C2602 2:C2603-C2605 3:C2606"

# Move a finished project to the next stage
python cli_index.py --client sai promote --item "Batch 3 Vid 1 - <title>" --to delivered

# Post-publish cleanup (archive project + file footage); shows a plan, asks y/N
python cli_index.py --client sai ship --video "Batch 3 Vid 1 - <title>"

# Backfill a specific week's folders (rarely needed)
python cli_index.py --client sai create-week --week 2026-06-15

# Delete temporary pull folders after editing
python cli_index.py --client sai pull-cleanup
python cli_index.py --client sai pull-cleanup --older-than 30
```

**Golden rules:** drive plugged in • always `--client sai` • `pull` copies, everything else moves & never overwrites • delete pulls when done • folders are the truth, `index` resyncs • don't touch `main.py`.

---

## 14. Going deeper

- **Dev / iteration rules** (eval harness, prompt tuning, adding a category): [footage-organizer.md](footage-organizer.md) and `python-scripts/footage-organizer/CLAUDE.md`.
- **The code:** the everyday commands all live in `python-scripts/footage-organizer/cli_index.py`.
- **Cross-machine notes** (Mac↔Windows, the shared SQLite index): the `Cross-platform` section of the project's `CLAUDE.md`.
```
