# Mac Pull Notes — 2026-06-15 session

Quick guide for picking this session's work up on the Mac. **Two sources: GitHub for code/docs/scripts, the SSD for footage.**

---

## 1. Get the latest from GitHub
```bash
cd ~/path/to/my-project
git pull
```
The Mac is already authenticated to GitHub (it's been pushing) — no token from Windows is needed. If pull complains about local changes, `git stash` first, pull, then `git stash pop`.

## 2. Plug in the SSD for footage
Footage is **NOT on GitHub** (gitignored — too big). It lives on the shared SSD:
- **Windows:** `D:/Sai/`  →  **Mac:** `/Volumes/Footage/Sai/`
- EP2 long-form review pool (renamed in story-arc order): `…/Sai/07_QUERY_PULLS/EP2-arc-map/` — scrub `01_…` → `17_…` in order; see `_EDIT-GUIDE.md` inside it.
- Raw sources: `…/Sai/01_ORGANIZED/06-06-26 / 06-09-26 / 06-10-26` + `…/Sai/Rest of week` (C2614–C2686).

---

## What this session added (all in the repo via `git pull`)

**Shorts — Batch 3 (films next):**
- `business/social-media/sai/scripts/2026-06-15-batch-3.md` — 12 scripts, A/B/C hooks each w/ a Visual: treatment, Sandcastles reference links
- `business/social-media/sai/scripts/2026-06-15-batch-3-review.html` — **open in a browser.** Editable review (edit hooks/visuals/script text, pick a hook, Approve/Swap/Cut, "Copy decisions + edits" to export). Same file goes to Sai.

**Long-form — EP2:**
- `business/social-media/sai/longform/ep2/EP2-ARC-MAP.md` — the story arc, every clip placed on its beat, [A-ROLL] interview slots marked
- `business/social-media/sai/longform/ep2/EP2-STORYLINE.md` — full beat sheet + the interview Blocks A–G (questions)
- `business/social-media/sai/longform/ep2/_SERIES-TEMPLATE.md` — the repeatable BTS-doc format

**Review of all 3 systems (the source of this week's direction):**
- `business/social-media/sai/reviews/2026-06-14-production-system-review.md`
- `business/social-media/sai/reviews/SYSTEM-BACKLOG.md` — living list of systems still to build

**New tool:**
- `web-apps/story-arc-board/` — folder-scoped story-arc board. Run: `cd web-apps/story-arc-board && python server.py` → http://localhost:4500

**Record:** `decisions/log.md` (6 new 2026-06-15 entries), `sai-script-style-guide.md` (new Hook-Testing visual rule).

---

## Caveats
- **Memories don't sync via this repo** — they live in `~/.claude/...` (machine-local to Claude). The decision log + style guide + docs carry the same context, so the Mac session still has it.
- **`.build_batch_review.py` / `.patch_refs.py`** are the generators for the review HTML — re-run after editing the script `.md` to regenerate.
- Open `.html` files in a **browser**, not the code editor.

---
_Delete this file once synced — it's a one-off handoff note._
