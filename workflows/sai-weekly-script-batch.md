# Sai — Weekly Script Batch (SOP)

Repeatable workflow for turning Sai's weekly voice memos into 7 short-form scripts that get batch-filmed in one day.

**Cadence:**
- **Day before filming:** Sai records voice memo(s). Gray runs this SOP, Sai reviews scripts, both finalize.
- **Filming day (default Tuesday):** Sai batch-films all 7 in one session.
- **Following days:** post 1/day Mon–Fri, save reserves for catch-up days.

**Output:** Two files per week:
1. `business/social-media/sai/scripts/YYYY-MM-DD-batch.md` — the 7 picked scripts for that week
2. Updates to `business/social-media/sai/script-backlog.md` — every new idea surfaced (whether picked or carried forward)

---

## Inputs

### Primary input (this week's content)

- **Voice memos** at `/Volumes/Footage/Sai/06_ASSETS/Voice Memos/` — Sai records himself answering Gray's interview questions OR riffing on what's on his mind that week. These are the canonical source of script ideas.

### Reference inputs (read before drafting to stay in voice)

- **Sai script style guide** → `business/social-media/sai/sai-script-style-guide.md` — **READ THIS FIRST.** Living tracker of voice markers, structural patterns, theme lanes, hook-to-script-shape matches, length norms, closing patterns. Updates every batch.
- **Sai script backlog** → `business/social-media/sai/script-backlog.md` — every idea ever surfaced, status tracked
- **Sai-edition hook templates** → `business/social-media/hook-templates-sai.md` (2026 edition — short list of survivors)
- **Voice feedback log** → `~/.claude/projects/-Users-graydavis28/memory/feedback-sai-linkedin-voice.md` (AVOID rules only — DON'T mine for voice patterns)
- **Winning patterns** → `business/social-media/winning-patterns.md`
- **Killed archive** → `business/social-media/killed-archive.md`

### Sources EXPLICITLY NOT to use

- ❌ `python-scripts/sai-linkedin/reference/voice/sai-linkedin-posts-final.md` — LinkedIn voice
- ❌ `python-scripts/sai-linkedin/reference/voice/sai-newsletters-collected.md` — newsletter voice

**Why these are off-limits for shorts drafting:** Sai's LinkedIn voice and newsletter voice are *written* voice — they've been polished, structured, and edited. Pulling phrasing or rhythm from them is the #1 source of AI-flavored shorts scripts. Sai's short-form video voice is the *voice memo voice* — looser, more conversational, with connectors and natural repetition. Stay only in the voice memo transcripts for shorts.

These references are still useful for LinkedIn caption work (handled by `python-scripts/sai-linkedin/`) — just not for shorts.

---

## Default Mix (confirm with Gray each week — may shift with strategy)

- **5 scripts in-lane** (75%) — established Sai topics
- **2 scripts new territory** (25%) — topics he surfaced for the first time on the memo, or topics with high conviction in writing but never on his video

Adjust if Gray says otherwise that week.

---

## How Sai's Voice Memos Work

Confirmed format (from the 2026-05-26 session):

- Gray and Sai sit down together
- Gray asks open questions ("what's been on your mind?", "what did you learn this week?", "go deeper on that")
- Sai riffs — sometimes telling a story, sometimes a framework, sometimes a tactic
- Recording is typically split into two halves (Part 1 + Part 2) of ~15–25 min each
- Sai may flag mid-memo when something "needs more shape" — those get marked `needs-followup` in the backlog, NOT filmed without a sharpening session

**Sai's process preference (his own words from 2026-05-26 memo):**

> "As I'm saying the story, I'll come up with the new stories myself. I'll come up with each video idea where I would need your help is, like, imagining that as being an actual script. And thinking about what people might be missing from what I've already said. If there's something that you think can add more context or make a better hook — probing on that frame of mind versus, like, let's find a new video that we can add."

**Apply this on session day:** when listening live, your job is to identify what's MISSING from a script-shaped beat in his answer, then probe deeper on the same frame. Don't pivot to a new video unless the current one already lands.

---

## Weekly Process — Step by Step

### Step 1 — Confirm scope with Gray (2 min)

- Default 5+2 mix this week?
- Any constraints from strategy / Sai's calendar?
- Anything Sai said in passing to flag for capture this week?

### Step 2 — Transcribe the voice memos (5 min wall time, then walk away)

```bash
mkdir -p ~/Desktop/my-project/business/social-media/sai/voice-memos/YYYY-MM-DD-batch-recap
cd ~/Desktop/my-project/business/social-media/sai/voice-memos/YYYY-MM-DD-batch-recap

# Compress each .m4a → mp3 (mono, 16kHz, 64k)
ffmpeg -i "/Volumes/Footage/Sai/06_ASSETS/Voice Memos/Part 1.m4a" -vn -ac 1 -ar 16000 -b:a 64k part1.mp3
ffmpeg -i "/Volumes/Footage/Sai/06_ASSETS/Voice Memos/Part 2.m4a" -vn -ac 1 -ar 16000 -b:a 64k part2.mp3
```

Copy the transcribe.py template from `voice-memos/2026-05-26-batch-recap/transcribe.py` into the new folder, adjust file names, run with the content-pipeline venv:

```bash
~/Desktop/my-project/python-scripts/content-pipeline/venv/bin/python transcribe.py
```

**Model choice:** `small` is the default for voice memos (fast, plenty accurate for clear speech). Use `medium` only if speech is noisy or accents are heavy. `large-v3` is wall-time-expensive on Mac CPU — only worth it for high-stakes long-form, not weekly recaps.

**API alternative:** if the OpenAI API key is set in `python-scripts/content-pipeline/.env`, transcription via Whisper API runs in ~3 min for ~$0.25 (vs ~5–10 min local). Both work; default to local for cost.

### Step 3 — Read both transcripts and catalog every shootable idea (15–25 min)

Open each `partN-transcript.md`. For every standalone shootable idea, add an entry to `business/social-media/sai/script-backlog.md`:

```markdown
### N. id-slug

- **status:** `backlog`
- **topic:** one-line summary
- **pillar:** existing lane tag (or flag NEW LANE for Gray)
- **format:** talking-head / framework / tactic-reveal / personal-story / etc.
- **timestamp:** [MM:SS – MM:SS]
- **source_quote:** Sai's actual words, copied verbatim from the transcript
- **why it works:** 1-line take on the hook / save-bait / specificity
- **notes:** anything about pairing, conditions, follow-up needed
```

**Granularity rule:** one entry per shootable idea. A topic like "Learn finances yourself" is one entry, but a tactic embedded inside it like "30% of paycheck → Taxes vault" gets its own entry because it can stand alone as a 30-second short.

**Sai's own mid-memo flags:** if Sai says something like "I don't know if I want to use this" OR "this needs more shape" → mark `status: needs-followup` and note what would unblock it.

### Step 4 — Pick the 7 strongest (10 min)

Score each backlog idea against:
- **Specificity** — concrete numbers, dates, names = save-bait
- **Hook strength** — does it open with a line that stops the scroll
- **Standalone** — viewer needs zero context to get the lesson
- **Mix balance** — across the 7, want a variety of tactical / framework / story
- **Lane / new-territory split** — 5 in-lane + 2 new (default)

Avoid:
- Anything that overlaps a video Sai posted in the last 30 days (check `video-log.csv`)
- Anything in `killed-archive.md` without a real reason it's worth resurrecting
- Anything flagged `needs-followup` (those gate on Sai)

Mark the picks: `status: picked-YYYY-MM-DD` in the backlog file.

### Step 5 — Draft each script (45–60 min total)

**Drafting principles:**

- **Use Sai's actual words.** The transcript timestamps in the backlog entry are the raw material. The voice memo transcript IS the script — your job is mostly to trim and arrange, not to write.
- **What to remove:** Gray's interview questions. Pure filler ("um", false starts, repeated words). Tangents that go off the script's topic.
- **What to KEEP that you'll be tempted to remove:** Sai's connectors ("I was like", "what I used to do is", "the way I think about it", "so"). His repetition where he repeated. His casual phrasing and run-on energy. These are voice markers — removing them is what makes scripts sound AI-flavored.
- **Open with Sai's strongest line from the transcript.** Don't write a new opener — find his.
- **End where his thought naturally lands.** Question CTAs only on framework-shaped posts; default is to land on the punchline. Don't synthesize a closer ("the lesson is…") that he didn't say.
- **Apply voice rules every time:**
  - "Founder" never "CEO"
  - No "most founders…" punching down
  - No AI-flavored summary closers
  - No invented specifics — every number from Sai's actual mouth
  - Keep cusses if Sai used them in voice memo (flag for him to choose per-post)
  - No 3-beat "no X, no Y, no Z" — cap at 2 with intensifier
  - Don't drop the verb in callbacks
- **Target 30–60s** which is roughly 75–150 spoken words

**The "is this AI-flavored?" check before submitting:**
Read each script aloud. If it reads like a polished LinkedIn post — perfect parallel sentences, every line tightened, every transition rhetorically clean — it's been over-edited. Go back to the transcript. Put back the connectors. Put back the repetition. Sai's voice memo voice is looser than his written voice on purpose.

**When tightening would change Sai's meaning OR remove a voice marker:** stop. Keep the longer Sai version. The point is HIS voice, not script efficiency.

### Step 6 — Write the batch file

Save to `business/social-media/sai/scripts/YYYY-MM-DD-batch.md`.

**Required format per script (locked 2026-05-27):**

```
### N — Script Title

A. Hook option A (no quotation marks)

B. Hook option B

C. Hook option C

**Script:**

> Body of the script in blockquote.
>
> Mini-hooks **bolded** inline (NO ★ or asterisk markers).

**What I'd add:**

- Gray's opinion on what's missing
- Or what could be sharpened
```

**Format rules — DO NOT add:**
- ❌ "Hook options (pick one):" label
- ❌ `---` separator lines above or below the script title
- ❌ Quotation marks around hook lines
- ❌ ★ or asterisk markers for mini-hooks
- ❌ Lane / Format / Length / Visual metadata headers above each script

**Top of the file (above all scripts) — keep brief:**
1. Header — source material links + length target
2. Open Questions for Sai (after Script 7) — anything that gates the shoot

Don't add provenance trails, voice rules sections, filming plan sections, post-filming tracking sections. Those live in the SOP and the style guide — not in the script doc Sai reads.

### Step 7 — Hand off to Sai for review (5 min)

- Drop the batch file link wherever Sai reviews
- Surface the "Open Questions" prominently — those gate the shoot
- Confirm filming location(s) + any wardrobe / set needs

### Step 8 — Update the style guide (compound the craft)

After drafting the batch — BEFORE handing off to Sai — open `business/social-media/sai/sai-script-style-guide.md` and update:
- New voice markers observed in the voice memo (add to "Voice Markers That Read As Sai")
- New structural patterns that worked (add to "Structural Patterns That Work for Sai")
- New theme lanes that surfaced (add to "Theme Territories")
- Anything that read as AI-flavored and got cut (add to "Voice Markers That Read As AI")

After Sai gives revisions — update again:
- What he changed and why (specific patterns, not just the line)
- Lines he kept that you thought he might cut (positive confirmations)

After videos post (7 days later) — update again:
- Which patterns crossed performance threshold (cross-reference `winning-patterns.md`)
- Which patterns underperformed (cross-reference `killed-archive.md`)

This file compounds the craft — skipping these updates means each week starts from scratch.

### Step 9 — After Filming (status update only)

For each picked script, update its backlog entry: `picked-YYYY-MM-DD` → `filmed`.

### Step 10 — After Posting (tracking)

For each posted video, add a row to `business/social-media/video-log.csv`:

- `video_id`: `YYYY-MM-DD-{backlog-slug}`
- `series`: `Sai Voice-Memo Batch`
- `pillar`: from the backlog entry
- `format`: `talking-head-short-aroll` (this batch) — adjust if format changed
- Leave 7-day metrics blank until they're in

After 7 days, fill metrics, compare to rolling average. Update the backlog entry status `filmed` → `posted`.

Promote winners to `winning-patterns.md`. Demote floppers to `killed-archive.md` with retrospective.

---

## Cost / Tool Notes

**Default workflow uses ZERO API spend** (local Whisper + reading transcripts).

**When to spend on API:**
- Set `OPENAI_API_KEY` in `python-scripts/content-pipeline/.env` for ~$0.25/week × 4 weeks/month = $1/month in transcription. Saves ~5 min/week wall time. Pays off if Sai's memos start running longer (>30 min total) or quality becomes an issue.

**When to escalate to `content-researcher` or `creator-intel`:**
- Sai's lane list feels exhausted (no new topics in 4+ weeks of memos)
- Strategy shift introduces a new audience
- Sai asks for trending-topic reactive content
- Otherwise: Sai's voice memos + backlog are the deeper well. Re-read first.

---

## File Locations (Reference)

| File | Purpose |
|---|---|
| `/Volumes/Footage/Sai/06_ASSETS/Voice Memos/` | Raw .m4a voice memos from Sai |
| `business/social-media/sai/voice-memos/YYYY-MM-DD-batch-recap/` | Compressed audio + transcripts + the transcribe.py script |
| `business/social-media/sai/script-backlog.md` | Living index of every idea ever surfaced |
| `business/social-media/sai/scripts/YYYY-MM-DD-batch.md` | This week's 7 picked scripts |
| `business/social-media/video-log.csv` | All posted videos + performance |
| `business/social-media/winning-patterns.md` | Patterns that crossed HIT tier |
| `business/social-media/killed-archive.md` | Series / formats / hooks that got cut |
| `business/social-media/hook-templates-sai.md` | 50 verbal + 20 visual hook templates for Sai |
| `python-scripts/sai-linkedin/reference/voice/` | Sai's LinkedIn finals + newsletter corpus |
| `memory/feedback-sai-linkedin-voice.md` | AVOID rules from Sai's actual revisions |

---

## Why This Workflow Exists

**The core insight:** Sai's own current thinking — captured fresh in voice memo form — is a deeper well than any external research or our own newsletter mining. The 2026-05-26 session produced 18 standalone shootable ideas in 41 minutes of audio. That's a 4-week pipeline from one sitting.

**The backlog system means nothing valuable disappears.** Even ideas Sai mentions in passing get captured. Future weeks pick from accumulated material, not from a blank page.

**The voice rules + transcript-grounded drafting means scripts sound like Sai, not like AI.** Every line in the batch file traces back to a timestamp in the transcript. If a script ever drifts off-voice, we can audit which line came from which moment.

**The 75/25 lane/new-territory split is the iteration mechanism:** in-lane content compounds his existing audience's expectations; new territory tests whether a topic should join the lanes for next week's iteration.
