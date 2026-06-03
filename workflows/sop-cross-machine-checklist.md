# SOP System — Mac ↔ Windows Cross-Machine Checklist

**Created:** 2026-06-02 (Mac session) · **Updated:** 2026-06-02 (after tool cleanup)
**Purpose:** Track every Python script powering the Content-OS SOP system and what each needs to run on both machines. Work down it one row at a time.

> Companion: the `device-compatibility` memory (GitHub is the sync bridge) and `business/sai-karra/content-os/` (the SOPs). This doc is about the **scripts** the SOPs call.

---

## The core truth

Git syncs all the **code** to both machines. What git does **NOT** sync (on purpose, for security):

1. **Secrets** — `.env` / `token.json` are gitignored. Code arrives on the new machine; keys do not.
2. **Local tools** — Whisper, ffmpeg, Pillow, fonts. Installed per-machine.
3. **Python environments** (`venv/`) — each machine builds its own.

So "only works on one machine" = one of those three is missing there, OR a **hardcoded path** (`D:/Sai/...`) that only exists on one machine.

### How secrets travel (they don't — you set them by hand)

**You create every `.env` yourself, in your Terminal. Never paste a key into chat.** The same key values go in the matching `.env` on each machine.

### Whisper decision (2026-06-02)

**Whisper is a Windows-only install.** ~95% of editing (and all batches) happen on the Windows PC, where Whisper runs fast on the RTX 5070 GPU. We are **not** installing it on the Mac.

---

## Status legend

✅ ready here · ⚠️ needs one thing · ❌ not set up · 🪟 Windows (where the work happens) · ↪️ other session · ⏸️ paused · 🗄️ archived

---

## The scripts that power the SOP system

| # | Tool | What it does | Needs to run | Status |
|---|---|---|---|---|
| 1 | **transcriber** (was content-pipeline) | audio/video → text; `--meeting-notes` → Obsidian notes | Whisper (🪟 Windows). `--meeting-notes` needs `ANTHROPIC_API_KEY` in `.env`. Plain transcript needs **no keys**. | 🪟 lives on Windows. Mac = not needed. |
| 2 | **sai-captions** | Whisper + Pillow burn captions on shorts | own `venv` (already on Mac ✅), Whisper, Montserrat font (in repo ✅) | ✅ likely cross-machine. Test a render to confirm. |
| 3 | **sai-linkedin** | LinkedIn post in Sai's voice + frame finder | `ANTHROPIC_API_KEY` + fix hardcoded `D:/Sai` path | ⏸️ **PAUSED** (Gray's call 2026-06-02) |
| 4 | **multicam-mirror** | dual-cam long-form sync + render | numpy; fix hardcoded `D:/Sai` input/output → make them arguments | ❌ path fix pending |
| 5 | **content-researcher** | trending topics + Reddit → Notion | `ANTHROPIC_API_KEY`, `YOUTUBE_API_KEY`, `NOTION_TOKEN`, `NOTION_PAGE_ID` | 🎯 **repositioned as a Graydient-brand tool** (Gray's own content), not Sai-SOP |
| 6 | **footage-organizer** | footage filing (underpins all SOPs) | (cross-machine SQLite already done in v2) | ↪️ being upgraded in another session |
| — | screen-recording-analyzer | recording → SOP | — | ⏭️ ignored (Gray doesn't use it enough) |
| — | hook-optimizer | hook scoring | — | 🗄️ archived → `_archive/` (playbook handles hooks) |
| — | founders-series | Founder Series helper | — | 🗄️ archived → `_archive/` |

---

## "Hardcoded path" — what it means (plain English)

A hardcoded path is a folder location typed directly into the code and frozen there — e.g. `ROOT = Path("D:/Sai")`. `D:/` only exists on **Windows**; on the Mac the same drive is `/Volumes/Footage/Sai`. So the script crashes on the other machine. **Fix:** pass the folder in when you run the script (like a mail-merge field) instead of baking it in.

---

## What's actually left to do

After the 2026-06-02 cleanup, the cross-machine to-do list is small:

1. **sai-captions** — run one test render on the Mac to confirm it works, then build the same `venv` on Windows. *(no secrets)*
2. **multicam-mirror** — change its hardcoded `D:/Sai` input/output paths into command-line arguments so it runs from any drive. *(code change, Claude can do)*
3. **transcriber** — when you next want `--meeting-notes`, set `ANTHROPIC_API_KEY` (+ `OPENAI_API_KEY`) in `transcriber/.env` on Windows. *(you do this in Terminal)*
4. **content-researcher** — keep for your own brand; set its 4 keys when you want to use it on Mac.
5. **sai-linkedin** — ⏸️ paused. Revisit later (needs `.env` + the `D:/Sai` path fix).

---

## Open questions for Gray
- On Windows, where does the footage drive mount — always `D:/Sai`, or does the letter change? (Decides how the multicam path fix should auto-detect.)
- Which SOP do you run most day-to-day? That's the one to make bulletproof first.
