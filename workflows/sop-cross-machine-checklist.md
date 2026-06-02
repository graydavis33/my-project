# SOP System — Mac ↔ Windows Cross-Machine Checklist

**Created:** 2026-06-02 (Mac session)
**Purpose:** One place that tracks every Python script powering the Content-OS SOP system and exactly what each one needs to run on **both** the Mac and the Windows PC. Work down this list one row at a time.

> Companion: the `device-compatibility` memory (GitHub is the sync bridge) and `business/sai-karra/content-os/` (the SOPs themselves). This doc is about the **scripts** that the SOPs call.

---

## The core truth (read this first)

Git already syncs all the **code** to both machines. What git does **NOT** sync (on purpose, for security):

1. **Secrets** — `.env` files and `token.json` are gitignored. The code arrives on the new machine; the keys do not.
2. **Local tools** — Whisper, ffmpeg, Pillow, fonts. These are installed per-machine, not committed.
3. **Python environments** (`venv/`) — each machine builds its own.

So "this script only works on one machine" almost always means **one of those three is missing on the other machine**, OR the script has a **hardcoded path** (`D:/Sai/...`) that only exists on one machine.

### How secrets travel (they don't — you set them by hand)

Per your security rule: **you create every `.env` file yourself, in your own Terminal. Never paste a key into this chat.** Claude gives you the template and the commands; you fill in the real values. The same key values go in the matching `.env` on each machine.

### The clean pattern for every tool

Each tool gets its **own `venv`** (isolated Python) + its **own `.env`** + its requirements installed. `sai-captions` already does this correctly — copy that pattern for the rest.

```bash
cd python-scripts/<tool>
python3 -m venv venv          # build the isolated environment (once per machine)
source venv/bin/activate       # Mac/Linux   (Windows: venv\Scripts\activate)
pip install -r requirements.txt
# then create .env by hand (see each tool's row below)
```

---

## Status legend

| Mark | Meaning |
|---|---|
| ✅ | Ready on this Mac |
| ⚠️ | Partly ready — needs one thing |
| ❌ | Not set up on this Mac yet |
| 🪟 | Windows status assumed working (verify on Windows when you're there) |
| ↪️ | Handled in another session |

---

## The scripts that power the SOP system

### 1. `screen-recording-analyzer` — the SOP generator itself
Turns a screen recording → frames + transcript bundle that Claude reads to write an SOP. **The on-ramp for the whole SOP system.**

| Needs | Mac | Note |
|---|---|---|
| ffmpeg | ✅ | installed (v8.1) |
| Whisper | ❌ | `pip install openai-whisper` — but Python 3.14 may fight it; use a venv with Python 3.12 if so |
| API key | — | **None.** SOP writing is done by Claude, not an API call |
| Hardcoded paths | ✅ | None — fully portable |

**One action for Mac:** install Whisper (in a venv). → then it runs on both machines.

---

### 2. `sai-captions` — auto-captions for shorts
Whisper transcribes → Pillow burns Montserrat captions → ffmpeg renders. Powers the shorts-editing SOP.

| Needs | Mac | Note |
|---|---|---|
| Own venv | ✅ | `venv/` already exists here |
| Whisper + Pillow | ✅ (in venv) | system Python lacks Pillow, but the tool's venv has it |
| Montserrat font | ✅ | `fonts/Montserrat.ttf` in repo |
| API key | — | None |
| Hardcoded paths | ✅ | None |

**Status:** Likely already cross-machine ✅. **One action:** run a quick test render on Mac to confirm, then build the same venv on Windows.

---

### 3. `content-pipeline` — video → transcript → clips → draft folder
Whisper transcript → Claude picks clips + writes title/caption/X-thread. Powers shorts + long-form drafting.

| Needs | Mac | Note |
|---|---|---|
| ffmpeg | ✅ | |
| Whisper | ❌ | same install as #1 |
| `ANTHROPIC_API_KEY` | ❌ | in `.env` (anthropic SDK reads it automatically) |
| `OPENAI_API_KEY` | ❌ | in `.env` |
| `OBSIDIAN_VOICE_MEMOS` | ✅ default | Mac path is the built-in default; **Windows must set this in `.env`** |
| Hardcoded paths | ✅ | Mac-friendly default, overridable per machine — good design |

**One action for Mac:** create `.env` (2 keys) + install Whisper. **For Windows:** also set `OBSIDIAN_VOICE_MEMOS` to the `C:/Users/...` path.

---

### 4. `sai-linkedin` — LinkedIn post in Sai's voice + frame finder
Powers the LinkedIn SOP. `main.py` drafts the post; `find_visuals.py` pulls matching footage frames.

| Needs | Mac | Note |
|---|---|---|
| `ANTHROPIC_API_KEY` | ❌ | in `.env` |
| Hardcoded paths | ❌ | **`ROOT = Path("D:/Sai")`** in `find_visuals.py` + a `/Volumes/Footage/Sai` example — Windows-only drive letter breaks on Mac |

**One action:** create `.env` **and** fix the hardcoded `D:/Sai` so it auto-detects the footage drive on each machine (Mac `/Volumes/...` vs Windows `D:/`).

---

### 5. `multicam-mirror` — dual-cam long-form sync + render
Powers the weekly YouTube long-form SOP. Syncs A-roll/B-roll, picks takes, renders.

| Needs | Mac | Note |
|---|---|---|
| ffmpeg + numpy | ⚠️ | numpy via venv |
| API key | — | None |
| Hardcoded paths | ❌ | **`ROOT` and `OUT_DIR` are hardcoded `D:/Sai/...`** — these should be command-line arguments, not baked in |

**One action:** change the hardcoded `D:/Sai` input/output paths into arguments you pass when you run it, so the same script works from any footage location on either machine.

---

### 6. `hook-optimizer` — score/generate hooks
Supports the shorts SOP. Pure Claude API, no files.

| Needs | Mac | Note |
|---|---|---|
| `ANTHROPIC_API_KEY` | ❌ | in `.env` |
| Hardcoded paths | ✅ | None |

**One action:** create `.env` (1 key). Then identical on both machines.

---

### 7. `content-researcher` — trend + Reddit research → Notion
Powers the research SOP. YouTube + Reddit + Claude → Notion report.

| Needs | Mac | Note |
|---|---|---|
| `ANTHROPIC_API_KEY` | ❌ | in `.env` |
| `YOUTUBE_API_KEY` | ❌ | in `.env` |
| `NOTION_TOKEN` + `NOTION_PAGE_ID` | ❌ | in `.env` |
| Hardcoded paths | ✅ | None |

**One action:** create `.env` (4 keys). Then identical on both machines.

---

### 8. `founders-series` — Founder Series helper
Powers the Founder Series SOP.

| Needs | Mac | Note |
|---|---|---|
| `ANTHROPIC_API_KEY` | ❌ | in `.env` |
| Hardcoded paths | ✅ | None |

**One action:** create `.env` (1 key).

---

### 9. `footage-organizer` — footage filing (underpins all SOPs)
↪️ **Being upgraded to a new version in a separate session.** Has hardcoded paths in `config.py` (lines 22–23) but the v2 work already made the SQLite index cross-machine. Leave it to that session; revisit here once it lands.

---

## Recommended order to work down this list

Grouped so each step unlocks the most at once:

1. **Install Whisper once (in a venv).** Unlocks #1 (SOP generator), #3 (content-pipeline), and confirms #2 (sai-captions). Biggest single win, **no secrets needed.**
2. **Create the `.env` files** for the API-key tools (#3, #4, #6, #7, #8). You do this in Terminal; Claude supplies each template. One sitting, knock them all out.
3. **Fix the hardcoded `D:/Sai` paths** in #4 (`sai-linkedin`) and #5 (`multicam-mirror`) so they auto-detect the drive. Code change Claude can do.
4. **Mirror the same setup on Windows** — build each venv + copy the same `.env` values. Verify each tool runs.

---

## Open questions for Gray
- Is there a single shared API key you want all tools to read from one place, or keep a separate `.env` per tool (current design)?
- On Windows, where does the footage drive mount — always `D:/Sai`, or does the letter change? (Decides how the auto-detect path fix should work.)
- Which SOP do you run most often day-to-day? That's the one to make bulletproof first.
