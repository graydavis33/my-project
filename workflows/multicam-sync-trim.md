# Workflow: Multi-Cam Sync & Trim

**Status:** LIVE — Windows (RTX 5070 for Whisper). Proven on the EP2 doc interviews (6 A/B pairs, 2026-06-23).
**Cost:** Free — local Whisper + ffmpeg only. No API calls.
**Script:** N/A — process SOP. Per-clip reusable scripts (`_prep.py`, `build_review.py`, `render_*.py`) live in a scratch/working area off the footage drive; copy + edit per pair.

> This is Gray's preferred way to cut multi-camera talking footage (A-cam Sony C#### + B-cam Canon MVI_####, and any future N-cam shoots). **It replaces the batch-pipeline `orchestrate` for this kind of work** — Gray found that worse. The win: audio-accurate sync, transcript-driven trimming, a scrub-able HyperFrames preview BEFORE any render, and clean reel-only exports.

---

## Objective

Take raw multi-cam footage of someone talking (interview, Q&A, monologue) and produce **synced, trimmed, frame-locked camera reels** ready to drop on a Premiere multicam timeline — dead air, bad takes, slates, and director-notes removed, complete thoughts kept.

---

## When to Run

- Any 2+ camera talking-head / interview shoot that needs cutting (doc interviews, podcast, batch Q&A).
- One pair/clip at a time. Gray reviews each in HyperFrames before the next, unless he says to run a batch unattended.

---

## Inputs Required

- **A-cam clip** + **B-cam clip** of the same take (e.g. `C2747.MP4` + `MVI_5048.MP4`).
- Pair them **chronologically** (1st A-cam ↔ 1st B-cam, etc.) — the audio-sync step confirms the pairing.
- B-cam = the cam whose audio you cut to (it carries the approved track / the interviewer question). Transcribe THAT one.

---

## The Pipeline (5 phases)

### 1. PREP — sync + transcribe (`_prep.py`)
- Extract both clips' audio to 8 kHz mono.
- **Sync:** bandpassed (300–3000 Hz) cross-correlation → `OFFSET = tB − tA`. Trust the **dominant** peak even when the absolute peak is low (lav vs camera mic lowers it). A-time = B-time − OFFSET.
- **Verify sync** with a paired A/B frame at 2–3 timestamps (same pose/mic position = synced). Cheap insurance.
- **Transcribe the B-cam** word-level with Whisper large-v3.
- Working files (wavs, `Bcam_words.json`, offset) go to **scratch, NOT the footage drive**.

### 2. CUT — build segments from the transcript
Read the transcript and build a `SEGMENTS` list (B-cam in/out per kept sentence). Rules:
- Keep **complete thoughts / sentences**; keep the question + the full answer.
- **DROP:** dead air, slate calls ("Block F", "Recording"), director-notes to the editor ("cut to a montage", "lean back"), duplicate/false-start takes (keep the fuller take), pet/baby/off-camera interruptions, trailing chitchat ("alright", "good on that", "it's a wrap").
- For in-sentence restarts/dups, use the word-level timings to start at the clean take.

### 3. MERGE — kill the overlap-stutter (critical)
Splitting continuous speech into separate segments and concatenating makes the **tail of one segment overlap the head of the next** → a word plays twice = a stutter/glitch. So **merge adjacent segments whose gap < 0.5 s** into one continuous extract. Keep cuts only where there's a real gap (dropped dead air / dup). This is automatic in the build scripts (`MERGE_GAP = 0.5`).

### 4. REVIEW — HyperFrames Studio (the default deliverable)
- Build a 720p B-cam proxy + a read-along trim-review comp (`build_review.py`) in the **repo** (`web-apps/hyperframes/sai-<clip>-review/`), NOT the drive.
- `npx hyperframes preview` → give Gray the **localhost URL** to scrub. He flags the worst 3–4 spots; fix the *class* of problem, not each instance.
- **Common note: a final word gets clipped** ("week", "productivity", "brain"). Whisper marks word-ends early → bump that segment's **tail to ~0.8 s**.

### 5. EXPORT — only on explicit "render and export"
Render per-segment **ProRes 422** A-cam + B-cam reels (A-cam video + B-cam audio; A falls back to B-cam video if a segment lands before A's footage), frame-locked **23.976 fps**, concat-copy. Export ONLY the two reels to the folder Gray names.

---

## Export hygiene (HARD RULES)

The export folder must contain **ONLY the A-cam + B-cam reels**. NEVER leave behind:
- ❌ PNGs (sync-check frames, contact sheets)  ❌ audio `.wav` files  ❌ JSON / `offset.txt`  ❌ `PREVIEW.mp4` (preview lives in HyperFrames only)
- ❌ any of my working/intermediate files on `D:/Sai` — those go to scratch or the repo.

Naming: `<Project> <ClipID> - A-cam.mov` / `- B-cam.mov`. Identical cut points so they stack on a multicam.

---

## How to Handle Failures

| Problem | Fix |
|---|---|
| Stutter/glitch on a word at a cut | Two tight segments overlapped — covered by the `MERGE_GAP = 0.5` merge; if it persists, merge those segments manually. |
| Last word of a line clipped | Bump that segment's `tail` to ~0.8 s (Whisper marks word-ends early). |
| A-cam reel looks out of sync | Re-check OFFSET sign (`A-time = B-time − OFFSET`); verify with paired frames. Low xcorr peak is fine if it's the dominant one. |
| Whisper smears words over a long pause | A 10–16 s "segment" for a few words = a pause artifact; use word-level timings to find the real continuous speech, start there, and flag it for an ear-check. |
| `npx hyperframes preview` exits immediately | Don't pipe its output to `head` (SIGPIPE kills it). Run it clean in the background. |
| Comp folder won't delete | An orphaned `hyperframes preview` node proc or Premiere holds it — close it first. |

---

## Known Constraints / Notes

- Default deliverable = **HyperFrames Studio preview**. Render/export to the drive happens ONLY on an explicit "render and export." See [[feedback_ask_before_writing_to_drive]].
- Never change the footage-organizer or any production tool without Gray's explicit OK first. See [[feedback_no_silent_tool_changes]].
- Editing reels MUST be ProRes (all-intra) so concat-copy scrubs clean in Premiere; H.264 segments throw seam errors.
- Scales to N cameras: sync each extra cam to the B-cam the same way (its own offset), mirror the same cut points.
- Memory: workflow_ab_interview_sync_trim. Related: [[workflow_sai_batch3_2cam_qa]] (the shorts variant).
