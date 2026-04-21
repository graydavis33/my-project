# Workflow: Screen Recording → SOP → Automation

**Status:** Live
**Cost:** Free (local Whisper) + ~$0.05–0.20 Claude per recording for SOP generation
**Script:** `python-scripts/screen-recording-analyzer/`

---

## Objective

Someone (e.g. Sai) sends a screen recording of a manual workflow. Turn that recording into:
1. A **structured SOP** an AI agent can follow step-by-step
2. A **handoff brief** that feeds into an automation workflow (Python script, n8n, Zapier, Claude agent)

This workflow is the on-ramp for delegating any repeatable task to an AI agent.

---

## Inputs Required

- Path to the screen recording (`.mp4`, `.mov`)
- One-line description of what the recording shows (e.g. "Sai uploading a podcast to Buzzsprout")
- Optional: credentials, accounts, or tools shown in the recording (note names — never paste secrets)

---

## Stage 1 — Extract the bundle

Produces frames + transcript Claude can actually read.

```bash
cd python-scripts/screen-recording-analyzer
python main.py "path/to/recording.mp4"
```

Output lands in `output/{name}-{timestamp}/` with:
- `frames/` — scene-change JPGs
- `transcript.md` — timestamped audio
- `manifest.json` — frame ↔ timestamp index

Defaults are usually right. Use `--interval 5` only if scene detection misses clicks (recordings with no visual transitions).

---

## Stage 2 — Generate the SOP (agent step)

Hand the output folder to Claude with this prompt:

> Read `manifest.json`, `transcript.md`, and every image in `frames/`. Produce an SOP at `sop.md` following the template below. Use the narration (transcript) to explain *why* each step happens; use the frames as ground truth for *what* is clicked. If narration and visuals disagree, trust the visuals and flag the conflict in a **⚠ Open Questions** section.

### SOP template (must match exactly)

```markdown
# SOP: {task name}

**Trigger:** {what event starts this workflow}
**Frequency:** {daily / weekly / per-episode / on-demand}
**Owner today:** {human name} → **Future owner:** AI agent
**Expected runtime:** {minutes}

## Inputs
- {file / URL / credential name — reference only, never the value}

## Tools & Accounts
- {app name} — {what it's used for} — {login method}

## Steps
1. **{verb-phrase step name}**
   - Action: {exact click / command / paste}
   - Frame reference: `frames/frame_00001.jpg` @ 00:12
   - Expected result: {what the UI should show after}
2. ...

## Success Criteria
- {observable thing that proves the workflow finished correctly}

## Failure Modes
- {what goes wrong} → {how to recover}

## Automation Hooks
- **Fully automatable:** {steps 1, 3, 5 via API X}
- **Needs human review:** {step 4 — reason}
- **Next script to build:** `python-scripts/{slug}/main.py`

## ⚠ Open Questions
- {anything ambiguous or missing from the recording}
```

Save the SOP next to the bundle: `output/{name}-{timestamp}/sop.md`.

---

## Stage 3 — Connect to an automation workflow

The `Automation Hooks` section tells you what to build next. Three paths:

| Recording shows... | Build target |
|---|---|
| Mostly browser clicks on one tool with an API | New Python script in `python-scripts/{slug}/` using that API |
| Browser clicks on a tool **without** an API | Playwright script (same pattern as `social-media-analytics/meta_scraper.py`) |
| Moves data between apps (download → upload, copy → paste) | n8n workflow on the VPS OR Python glue script |

**Always:**
- Copy the `sop.md` into the new project's folder so the agent executing the automation has the source of truth
- Link the SOP from `workflows/` index and add the project to `context/priorities.md` if it's non-trivial
- Before coding: check existing tools in `python-scripts/` that already do part of the job

---

## Success Criteria (for this whole workflow)

- Any screen recording Gray drops on disk becomes a `sop.md` without asking Claude further questions
- The SOP is specific enough that a *different* Claude session — with no prior context — can execute or automate it
- Each SOP names its next build target so nothing rots in an "analyzed but not automated" state

---

## Failure Modes

- **ffmpeg not installed** → install it; `footage-organizer` already assumes it
- **Whisper model download stalls** → first run downloads ~3GB for `large-v3`; be patient or pass `--no-transcript` and paste a manual transcript later
- **Scene detection returns 0 frames** → screen-share with no visual transitions. Script auto-falls back to 5s interval, but you can force it with `--interval 3`
- **Narration ≠ visuals** → SOP writer MUST surface this under "Open Questions", not silently pick one

---

## Example: Sai's podcast upload

1. Sai sends `sai-podcast-upload.mp4`
2. Run Stage 1 → bundle at `output/sai-podcast-upload-20260420-143000/`
3. Run Stage 2 with context "Sai uploading a weekly podcast" → `sop.md`
4. Review SOP. If most steps are Buzzsprout + Descript, Stage 3 target = new Python script calling the Buzzsprout API with Descript export as the handoff
5. That script becomes the actual automation; this SOP becomes its spec
