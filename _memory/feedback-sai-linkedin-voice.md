---
name: Sai's Revisions on Generated LinkedIn Captions
description: Sai's edits to AI-generated LinkedIn captions — feedback loop to iterate the sai-linkedin pipeline's voice/style/structure
type: feedback
originSessionId: 636ac229-cf80-45a4-aad1-3147996d8c11
---
This is the feedback loop for the `python-scripts/sai-linkedin/` pipeline. Whenever Sai edits a generated `caption.txt`, log:
- The post date / source short
- What was generated vs what Sai changed
- The pattern (hook style, line breaks, voice tells, CTA, framework structure, etc.) that the change reveals

**Why:** The whole point of the sai-linkedin tool is to draft captions in Sai's voice. The reference corpus (`reference/posts/`, `reference/voice/`) and `SYSTEM_PROMPT_CORE` are only as good as the feedback they get. When Sai edits something, that edit is a free training signal — capture it.

**How to apply:**
- Read this file before generating a new LinkedIn caption — apply the patterns Sai has corrected before
- When patterns repeat (same edit type 2+ times), update `SYSTEM_PROMPT_CORE` in `main.py` or add an example to `reference/posts/` so the tool produces it correctly on the first draft
- Keep entries dated and in source-of-edit order so the most recent voice signal wins

---

## Persistent Voice Rules (already baked into SYSTEM_PROMPT_CORE — re-check before each run)

1. **"Founder" not "CEO"** — Sai self-identifies as a founder. Never write "CEO" / "young CEO" in his voice.
2. **No quippy/cute parenthetical asides** that aren't from the transcript. Specific phrases Sai has flagged: "exist like a human", "actually wake up". They read as AI flavor, not Sai. Keep day-block descriptions neutral.
3. **No grand-summary AI-flavored closer.** Specific phrasing flagged: "The structure that matters most:", "What this really comes down to is:", "The lesson is:". Either let the framework stand or close with a single question/callback.
4. **No "most founders" punching-down framing.** Specific lines flagged: "Most founders let their calendar get carved up by whoever asks first. Then wonder why nothing actually moves." Sai shares his own system; he doesn't dunk on peer founders.
5. **Keep specific real rituals from the transcript verbatim** (meditation, Mule #3, etc.) — don't paraphrase concrete details into generics, and don't invent details that aren't said.

---

## Edit Log

### 2026-04-30 — Round 1: "2026-04-27 Schedule V6" short

Source folder: `/Volumes/Footage/Sai/AI Edits/2026-04-27 Schedule V6/linkedin/`
Reference example added: `python-scripts/sai-linkedin/reference/posts/sai-approved-2026-04-27-schedule.md`

**Edits Sai made (5 total):**

| # | What Claude generated | What Sai changed it to | Pattern |
|---|---|---|---|
| 1 | "21-year-old CEO" | "21-year-old founder" | Identity word — Sai is "founder", never "CEO" |
| 2 | "8:00–10:30 — No work. Set an intention, eat breakfast, exist like a human." | "8:00–10:30 — No work. Meditation. Set an intention. Eat breakfast." | Two changes: (a) add real ritual ("Meditation") that was in the transcript intent; (b) delete cute "exist like a human" aside |
| 3 | (closer block) "The structure that matters most: meetings happen in one window. Deep work gets the best hours of the day, not the scraps." | (deleted) | AI-flavored summary closer — sounds synthesized, not native |
| 4 | "Most founders let their calendar get carved up by whoever asks first. Then wonder why nothing actually moves." | (deleted) | Demeaning to peer founders — Sai shares, doesn't dunk |
| 5 | (kept) "What does your current workday actually look like?" | (unchanged — kept) | Question CTA is the right closer shape |

**Net structural lesson:** the post should END on the framework or a single short question — NOT on a paragraph that summarizes/synthesizes/contrasts. Sai's voice is "here's my system" not "here's my system AND here's why most people fail at this".

**Action taken:** baked rules 1–4 into SYSTEM_PROMPT_CORE on 2026-04-30. Added the approved final caption to `reference/posts/` so future runs see a positive Sai-shaped example.

---

### 2026-05-03 — Round 2: "Pre-Workout Meditation" short

Source folder: `/Volumes/Footage/Sai/08_AI_EDITS/linkedin/2026-04-23-pre-workout-meditation/linkedin/`
Source short: `03_DELIVERED/shorts/W02_Apr-20-26/pre workout meditation.mp4`
Reference voice corpus updated: `reference/voice/sai-linkedin-posts-final.md` (appended Sai's final)

**Edits Sai made (4 total):**

| # | What Claude generated | What Sai changed it to | Pattern |
|---|---|---|---|
| 1 | "Before I started, my nervous system was all over the place." | "Before I started meditating, my nervous system was all over the place." | Don't drop the verb in callback references — restate "meditating" so the line stands on its own. Sai prefers explicit over elliptical. |
| 2 | "No crash. No jitters. No $60 tub of powder." | "No crash, definitely no jitters." | Two changes: (a) cut the over-specific copywriter-y joke detail ($60 tub of powder) — invented detail not in transcript, reads as AI cleverness; (b) compress 3 staccato sentences into a 2-beat comma+intensifier construction. Sai's voice doesn't pile up parallel rhetorical sentences. |
| 3 | "For a founder, that's a cheat code." | (deleted) | Don't reframe a transcript punchline through identity ("For a founder, ...", "For a CEO, ..."). The transcript already said "It's a literal cheat code" — adding the "For a founder, that's a..." wrapper synthesizes/restates it, which is its own AI tell. Either keep the original line or cut it. |
| 4 | "What's the one habit that's moved the needle most for how you show up?" | (deleted) | Question-CTA closer cut entirely. Note nuance: in Round 1 Sai KEPT the question CTA ("What does your current workday actually look like?") on a longer framework post. On a short, tight post like this, the question reads as engagement-bait. Rule: questions are optional, not mandatory. End on the punchline if the post lands clean. |

**Net structural lessons:**
- Elliptical references ("Before I started", "When I quit") read as cute when expanded callbacks read as conversational. Restate the verb.
- The "no X, no Y, no Z" three-beat parallel is a common copywriter move. Sai doesn't use it. Two beats max, conversational connector ("definitely", "honestly").
- Don't synthesize the transcript's closing line into a wrapper sentence. The transcript said "It's a literal cheat code" — keeping that as-is is fine, but reframing it as "For a founder, that's a cheat code." is AI restating-for-emphasis behavior.
- Question CTAs are optional. Default to NO question; only add one if the post is long-form/framework-shaped (Round 1 was; Round 2 wasn't).

**Action taken on 2026-05-03:**
- Replaced `caption.txt` with Sai's final
- Appended Sai's final to `reference/voice/sai-linkedin-posts-final.md`
- Adding 4 new AVOID rules to `SYSTEM_PROMPT_CORE` in `main.py`:
  - AVOID — ELLIPTICAL CALLBACKS: don't drop the verb in a callback reference
  - AVOID — INVENTED COPYWRITER DETAILS: never invent product/price specifics not in the transcript ($60 tub of powder, etc.)
  - AVOID — THREE-BEAT PARALLEL "NO X, NO Y, NO Z": cap at two beats with a comma + intensifier
  - AVOID — IDENTITY-WRAPPED RESTATEMENT CLOSERS: don't reframe a transcript punchline through "For a [role], that's a [thing]"
  - SOFTEN — QUESTION CTAs OPTIONAL: only add a question on long-form/framework posts; default is to end on the punchline
