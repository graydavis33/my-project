# Sai — Batch Video Production (Master SOP)

**Status:** LIVE — runs weekly across Mac + Windows
**Cost:** Near-zero if the token rule below is followed. The only real Claude spend is graphics + script drafting.
**Scripts:** No single script — this is the master process SOP. It chains existing tools (`content-pipeline`, `sai-captions`, HyperFrames, the Windows trim script) and links out to stage-specific SOPs.

---

## Objective

Turn one weekly sit-down with Sai into a batch of finished short-form videos, on a repeatable 4-day rhythm, without blowing the Claude usage limit. The whole system is built so **heavy media (video/audio) is processed by local tools for free, and Claude tokens are only spent on judgment** (writing scripts, building graphics).

Target cadence: **7 shorts/week now → 2 videos/day by August.**

## Scope — which shorts this covers

There are **two tiers of Sai shorts**, and this SOP is about the first one:

- **Batch / produced shorts (THIS SOP)** — the polished ones with graphics + effects, made on the Saturday→Monday rhythm. These get HyperFrames graphics, captions, the full pipeline.
- **UGC shorts (NOT this SOP)** — when Sai grabs his phone and films something quick. Strip-down editing, **no graphics / B-roll / music**, Sai films and edits himself. Those follow the per-platform SOPs in `business/sai-karra/content-os/` (`tiktok-sop.md`, `instagram-reels-sop.md`, etc.).

The detailed editing mechanics for batch shorts (exact trim rules, caption pixel positions, paths, fps) live in **[business/sai-karra/content-os/sai-shorts-editing-sop.md](../business/sai-karra/content-os/sai-shorts-editing-sop.md)** — this master SOP is the higher-level rhythm and links to it for the how.

---

## THE TOKEN RULE (read first — this is why the SOP exists)

Gray hit a usage limit once by feeding raw batch video into an interactive Claude Code session. Never again. The rule:

> **Raw video and long audio NEVER enter Claude's context. Local tools (Whisper, ffmpeg, the trim script, sai-captions) do the heavy lifting for free. Claude only ever sees text.**

Practical consequences:
- Trimming, captioning, and transcription run as **unattended scripts**, not as a chat where Claude "watches" footage.
- Transcribe each video **once**; reuse that one transcript for trimming AND captions AND (future) B-roll matching.
- The only steps that legitimately spend Claude tokens are **script drafting** and **graphics building** — and both run in subagents so the main session stays lean.

See the [Token Budget](#token-budget) table for exactly what costs what.

---

## When to Run — The Weekly Rhythm

| Day | Stage | What happens |
|---|---|---|
| **Saturday** | Preproduction | Recap the week → record voice memos → transcribe + analyze → write scripts |
| **Sunday** | Production | Film all approved scripts as talking-head, vertical, 3 hooks each |
| **Monday** | Post-Production | Trim (local script) → captions (local tool) → graphics (one at a time) → SFX/color (manual) |
| **Monday → done** | Review + Publish | Frame.io review loop with Sai → fix → manual upload → log in Notion |

---

## Stage 1 — Preproduction (Saturday)

**Goal:** approved scripts, ready to film.

1. Sai recaps everything that happened the past week.
2. Record **30–60 min** of Sai talking on the past week / interesting topics.
3. Gray's job during recording: **stay engaged, build the voice memos, ask questions that go DEEPER on a topic** — not questions that spawn a separate video.
   - Example (topic = hiring tactics): do NOT ask "what are the worst 5 employees you've hired?" (that's a different video). DO ask "how did you come about these tactics?" (drives deeper on the same beat).
4. Voice memo → **transcribe + analyze** locally (Whisper, $0 Claude tokens).
5. Use the story structure + analysis to **write the scripts** for each topic.

**This stage IS the "AI scripting assistant."** The detailed drafting process (voice rules, backlog, hook format, style-guide updates) already lives in its own SOP — follow it:

→ **[workflows/sai-weekly-script-batch.md](sai-weekly-script-batch.md)** (now on the Saturday cadence, not the old Tuesday one)

Scripting draws on three inputs:
- **Sai's voice memo transcript** — the substance
- **The story-arc-playbook** (`business/social-media/story-arc-playbook/`) — structure, frameworks, hooks, viral patterns (built from 8 reference-video transcripts on 2026-06-01)
- **The Sai style guide** (`business/social-media/sai/sai-script-style-guide.md`) — makes it sound like Sai

The `scriptwriter` subagent (`.claude/agents/scriptwriter.md`) wraps this so the big reference files load in the agent's context, not the main session — keeping tokens low. (Writes in Sai's voice-memo voice — never his LinkedIn voice — for shorts.)

**Definition of done:** every script reviewed multiple times and **approved by Sai**.

---

## Stage 2 — Production (Sunday)

**Goal:** all raw footage filmed.

1. Only after scripts are reviewed + approved.
2. Film all scripts as **talking-head**.
3. Location can be random or all in one spot (podcast room) — either is fine.
4. **All filmed vertical.**
5. **Each script filmed with 3 different hooks** (for trial reels). Always make the best 3; how many actually post is Gray's call.

**Definition of done:** every approved script has raw footage with its 3 hook variants.

---

## Stage 3 — Post-Production (Monday)

**Runs on Windows** — the PC handles the heavier load and finishes far faster (RTX GPU + footage live on `D:` / the Footage SSD).

**Full mechanics** (exact trim rules, caption positions, paths) → [sai-shorts-editing-sop.md](../business/sai-karra/content-os/sai-shorts-editing-sop.md). This is the rhythm overview.

**Frame-rate rule:** trim, captions, and the final delivered video are **24fps (23.976)**. The ONLY thing rendered at **60fps is the HyperFrames graphics** — so Gray can speed-adjust them in Premiere without losing quality. (Note: the editing SOP's Step 3 graphic-render line should read `--fps 60`, not 24 — fixed in that doc.)

**Batch logic:**
- **Vid 1 must post Monday**; the rest are edited by end of Monday.
- `*` videos are **edited together** (batch-processed back to back).
- Non-`*` videos are edited one at a time.

**The post-production loop (one unattended run over the whole batch folder):**

```
for each raw_video in the batch folder:
    1. Transcribe once (Whisper, local)              -> transcript     [$0 Claude]
    2. Detect bad takes + dead space                 -> trim plan       [Windows trim script]
    3. Cut with ffmpeg                               -> trimmed.mp4     [$0 Claude]
    4. Render captions FROM THE SAME transcript      -> captions.mov    [sai-captions, $0 Claude]
    5. Output trimmed.mp4 + captions.mov to the video's folder
```

- **Trimming:** the Windows Python trim script (already built + trained, "good not perfect"). Cuts bad takes + dead space. AI-trimmed videos export to a new folder.
- **Captions:** generated from the **same** trim transcript (transcribe once). Style is already built (`sai-captions` — Montserrat SemiBold, upper third). **Captions export separately** so they can be edited independently in the NLE.
- **Graphics:** **all shorts in the batch get graphics.** Done **one video at a time** to control token spend. Built in HyperFrames (60fps greenscreen MP4 → Footage SSD). Keep cheap by reusing the parameterized templates from `web-apps/hyperframes/sai-shorts-2026-05-27/` (change text/numbers, don't rebuild) and building each in its own subagent.
- **SFX:** manual for now (worth automating later).
- **Color grading:** manual.
- **Music:** manual, part of the edit.
- **B-roll:** manual placeholder for now (future: AI B-roll matcher).

**Definition of done:** every video trimmed, captioned, graphics added, SFX/color/music done.

---

## Stage 4 — Review + Publish

1. Finished edits → upload to **Frame.io**.
2. Sai reviews all of them.
3. Gray fixes the corrections. **Back-and-forth until Sai is satisfied.**
4. **Manual upload** to the platforms — no third-party social schedulers (team preference).
5. Input everything into the **Notion content calendar**: video type, title, publish date, status (Script → Scheduled → Posted).
   - Calendar page: `Content Calendar` in Notion HQ (data source `c6d86cf4-836f-4d11-baab-487a8199f31d`).

**Definition of done:** Sai-approved, posted, and logged in Notion.

---

## Token Budget

What each step actually costs. Anything marked **$0 Claude** runs as a local tool and must never be done by feeding media into a chat.

| Step | Where | Claude tokens? |
|---|---|---|
| Voice memo transcription | Whisper (local) | **$0** |
| Transcript analysis for scripts | Subagent on text | Low (text only) |
| Script drafting | `sai-script-writer` subagent | Low–moderate (text only) |
| Trimming (bad takes + dead space) | Windows trim script | **$0** (pennies if it calls Claude on transcript text) |
| Caption rendering | `sai-captions` (local Whisper + Pillow) | **$0** |
| Graphics | HyperFrames build (one subagent per graphic) | **Moderate — the main cost.** Template-reuse keeps it small |
| SFX / color / music | Manual edit | **$0** |
| Publishing | Manual upload | **$0** |

If a step ever feels like it's burning tokens, the cause is almost always **media in the context**. Stop and route it through a local tool.

---

## How to Handle Failures

| Problem | Fix |
|---|---|
| Usage limit / tokens spiking during post | You've got media in the chat. Kill it. Run trimming/captions as scripts; Claude only sees text. |
| Captions don't match the cut | Captions must be rendered from the **trim** transcript, not a fresh transcribe of the raw video. Re-run captions on the trimmed transcript. |
| Trim script cuts good takes / leaves bad ones | It's "good not perfect." Manual review pass after the batch run. Log misses to improve the Windows script next session. |
| Graphics taking too long / costing too much | Reuse the parameterized templates in `sai-shorts-2026-05-27/`. Don't build from scratch. One subagent per graphic. |
| Scripts read AI-flavored | Go back to the transcript; see the voice rules in `sai-weekly-script-batch.md` + style guide. |

---

## Known Constraints / Notes

- **Windows trim script is not synced to Mac yet.** It's built + trained on Windows. Plan: improve it and sync to Mac so post-production can run on either machine. **The Stage 3 loop above is documented from Gray's description — verify against the actual Windows script next Windows session.**
- **Post-production is Windows-first by design** (GPU + footage there). Don't try to run heavy trims on the Mac.
- **Footage backup** (moving source/render videos off the repo to the Footage SSD) is a **separate** open issue, not part of this SOP. See memory `todo-caption-videos-to-ssd`.
- **Manual-for-now steps** that are future automation candidates: SFX, B-roll matching, the AI scripting assistant's full automation. Sai's rule: **manual first, then automate.**
- Old cadence drift: `sai-weekly-script-batch.md` header still references a Tuesday film day / 7-per-week framing. The current rhythm is Saturday script / Sunday film / Monday post. Reconcile that header next time it's touched.

---

## Related

- [workflows/sai-weekly-script-batch.md](sai-weekly-script-batch.md) — the Stage 1 scripting detail
- [workflows/content-pipeline.md](content-pipeline.md) — transcribe → clip → caption tooling
- [workflows/footage-organizer.md](footage-organizer.md) — pulling/organizing footage
- `business/social-media/story-arc-playbook/` — structure/hook reference for scripting
- `business/social-media/sai/sai-script-style-guide.md` — Sai's voice
- [business/sai-karra/content-os/sai-shorts-editing-sop.md](../business/sai-karra/content-os/sai-shorts-editing-sop.md) — detailed editing mechanics for batch shorts
- `business/sai-karra/content-os/` — per-platform SOPs (incl. UGC-shorts tier)
- `workflows/caption-standards.md` — house caption rules (font/case/position)
- `.claude/agents/scriptwriter.md` — the scriptwriter subagent
- Memory: `sai-motion-graphics-2026-05-27`, `sai-captions-tool`, `hyperframes-usage`, `notion-content-calendar`
</content>
</invoke>
