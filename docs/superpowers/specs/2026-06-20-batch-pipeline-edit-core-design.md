# Batch Content System — Phase 1: Edit Core

**Date:** 2026-06-20
**Status:** Design — awaiting Gray's review
**Author:** Claude + Gray

---

## Why this exists

Batch content is its own production lane: N short videos filmed in one session, one location, two cameras (A = Sony `C####`, B = Canon `MVI_####`), one lav mic, Gray asks a question off-camera, Sai answers (often multiple takes). Every video is edited **the same way every time**.

Today that "same way" is a prose SOP + per-video hardcoded scripts + Claude's hand-judgment, with **separate Mac and Windows script copies that drift** — which is why the same mistakes (clipped trailing words, wrong pads) recur on every new video. Phase 1 converts the proven mechanics into **one cross-platform tool** so the only human input per batch is the review pass, and the recurring bugs become enforced code.

This is **Phase 1 of 3**. The full system:
1. **Edit core** *(this spec)* — drive an already-organized batch through sync → … → verified package.
2. **Organize/split front-door** *(later)* — footage-organizer `batch` extended to take a dropped raw batch and auto-split (clap + "Section N") + pair A/B into `Vid_MM` folders.
3. **Premiere timeline (FCPXML)** *(later)* — generate an importable timeline (bins + A/B cut clips + b-roll placed + clean audio).

Phases 2 and 3 build on Phase 1's outputs; nothing here blocks them.

---

## Locked decisions (from brainstorming)

- **Selection:** auto-cut every video, **Gray approves each** via a batched review before finals.
- **Input (this phase):** reads already-grouped footage at `01_ORGANIZED/Batch_NN/Vid_MM/{A,B}` (full per-video sources, grouped but NOT editorially trimmed). The drop→split→group step is Phase 2.
- **Finish line (this phase):** the locked deliverable **package** per video (`ANGLES/` + `CAPTIONS/` + `_INFO.txt`) + b-roll by beat. FCPXML timeline is Phase 3, but package layout must be FCPXML-consumable.
- **Audio:** clean the lav source once (Adobe-Podcast-equivalent), right after sync, so cut + finals inherit clean audio. Backend chosen by a spike (below).
- **Build around existing work** — reuse `sync.py`, today's clip-guard + cut, `caption_render`, the HyperFrames trim-review. Do not rebuild.
- **Correlate with footage-organizer** — share its SQLite index and its cross-platform convention; the pipeline owns the *edit*, footage-organizer owns *file movement*.

---

## Architecture

New tool: `python-scripts/batch-pipeline/`. A driver (`run.py`) walks each `Vid_MM` through ordered, independently-testable stage modules. One codebase, platform auto-detected — **the anti-drift fix**.

```
python-scripts/batch-pipeline/
  config.py        # SAI_LIBRARY_ROOT env, platform detect, FPS/pads/caption-style constants, font path per OS
  sync.py          # A/B offset via audio cross-correlation        (move from multicam-mirror, unchanged logic)
  audio_clean.py   # clean(in_wav) -> clean_wav  (pluggable backend; pick via spike)
  transcribe.py    # platform-shim Whisper -> word-level JSON in synced time
  select.py        # transcript -> proposed keep-ranges (drop rejected/dup takes, dead air)
  clipguard.py     # snap each cut-out to quietest point before next word (today's guard, generalized)
  cut.py           # trim + fps-lock + re-encode concat -> A/B cuts + caption_words.json
  captions.py      # alpha .mov, Sai house style (from caption_render.py)
  verify.py        # gate: no-clip, decode-clean, no-freeze, A/B length match, audio source correct -> log
  review.py        # build ONE batched HyperFrames trim-review for all N videos
  package.py       # render ANGLES/ + CAPTIONS/ + _INFO.txt to 08_AI_EDITS/shorts/Batch_NN/
  broll.py         # horizontal-only b-roll by beat (footage-puller + cached rotation-aware index flag)
  run.py           # batch driver
  tests/
```

**Supersedes** the Mac `multicam-mirror/batch3_pipeline/` and the Windows drive scripts `D:/Sai/01_ORGANIZED/_b3_edit/`. Those stay until Phase 1 reaches parity, then are removed (one tool, no drift).

### Cross-platform foundation (shared with footage-organizer)

- Library root from `SAI_LIBRARY_ROOT` env (`/Volumes/Footage/Sai` on Mac, `D:/Sai` on Windows). No drive-letter assumptions; `pathlib` everywhere.
- UTF-8 stdout/stderr forced (Windows cp1252).
- Whisper backend auto-detected: `mlx_whisper` on Apple Silicon, `openai-whisper` CUDA on Windows. Same word-level JSON contract out of both.
- Font path resolved per-OS in `config.py` (today this was the one hardcoded divergence in `caption_render`).
- ffmpeg/ffprobe assumed on PATH on both machines.

---

## Data flow

`run.py --batch 04`:

1. **Discover** `01_ORGANIZED/Batch_04/Vid_*`; read each video's A/B sources + title.
2. **Prep each video** (independent, parallelizable):
   sync → verify residual → **audio-clean lav** → transcribe (clean audio) → **auto-select** proposed cut → **cut + clip-guard** → captions → **verify gate**.
   A video that fails the gate is flagged, not silently advanced.
3. **Batched review:** build ONE review surface (all N reviewcuts) → Gray scrubs, approves or requests range edits per video.
4. **Finalize approved:** re-cut any edited video → render **package** (ANGLES/CAPTIONS/_INFO) + pull **b-roll** by beat.
5. **Report:** per-video status, flags, output paths, verification log.

Gray's hands-on time = the one review pass (+ range tweaks). Everything else runs unattended.

---

## Component contracts

**`select.py` — the codified editorial judgment** (proposes; review catches misses):
- **Hook** = the question (interrogative spoken off-camera, before the answer).
- **Drop rejected takes:** detect rejection markers ("redo", "let me redo", "start over", "I don't like that", "scratch that") → drop from that take's start to the marker; keep the take after it.
- **Dedupe immediate repeats:** same phrase said back-to-back → keep the later/cleaner pass.
- **Drop false starts:** a partial phrase immediately restarted.
- **Collapse dead air** between kept words beyond a pause threshold.
- Output: ordered keep-ranges `(synced_in, synced_out)` per video. Imperfect is OK — Gray approves each.

**Auto-select training corpus** — `select.py` is built from Gray's documented rules, not invented. Canonical sources the implementation must load and encode:
- `business/social-media/sai/editing/shorts-auto-edit-training.md` (live Batch 3 training log — most recent)
- `business/social-media/sai/editing/sai-shorts-editing-sop.md`, `training_notes.md`
- `ai-edit-vs-final-study-*.md` (AI cut vs Gray's final Premiere edit — the before/after diffs)
- memories: `feedback_sai_short_form_ai_edit_lessons.md` (Rules 1–8), `feedback_graydient_take_session_edit_rules.md`, `feedback_long_form_editing_from_gray_diff.md`, `workflow_sai_batch3_2cam_qa.md`, the `feedback_caption_*` set

Condensed ruleset (full detail + citations in those files):
- **Take selection:** last clean take wins; drop false-start vetoes ("No.", "All right."); drop aborted-then-restated sentences; keep continuous mid-sentence stumbles whole (no-pause restarts clip if cut); RMS-detect hidden restarts inside a single long Whisper "word" and keep the post-pause attempt; composite across takes at word boundaries when the best version spans two; duplicate hook → keep the punchier/more specific one.
- **What to cut:** collapse dead air ≥0.30s → ~0.10s breath; cut redundant phrase repetitions to one instance; drop setup/meta-narration before the punchline; drop isolated leading connectors (And/So/But/Then/Now) when their antecedent was removed — KEEP when they bridge ideas or carry contrast; cut tangents and post-sign-off chatter.
- **Pacing/length:** target 30–40s, bias tight; if keeping >50% of body words, keeping too much.
- **Hook/ring-out:** hook = Gray's off-cam question, always (never Sai's paraphrase); generous tail on the closer (~0.8s) — clip-guard handles this; head-pad 0 when a dropped retake butts the kept take.

**`clipguard.py`** (today's, generalized): for each cut-out, search `[sout, sout+0.6]` (capped at the next transcript word − 0.02s) and cut at the **quietest 60ms** — so a trailing word always rings out and we never bleed into a following hesitation/breath/retake.

**`cut.py`:** word-level keep-ranges; LEAD/TAIL pads via clip-guard; fps-lock both cams to `24000/1001`; concat must **re-encode** (never `-c copy` → QuickTime freeze). Emits `Vid_NN_{A,B}-cam_CUT.mp4` (identical length), `caption_words.json`, `cut_plan.txt`.

**`verify.py` — the gate (gotchas become enforced code):**
- **No clipped words:** energy 60ms after each cut-out drops (authoritative, against original synced audio — not the frame-snapped concat).
- **Decode-clean** (`ffmpeg -v error … -f null -`), **no freeze** (`freezedetect`).
- **A/B equal length**, ≈0ms apart.
- **Audio source correct** (lav cam on both angles — MD5 match).
- Writes a per-batch verification log. Any failure flags the video and blocks it from the "approved/finalized" path until resolved.

**`package.py`:** matches the locked convention exactly (verified against V01–V03):
```
08_AI_EDITS/shorts/Batch_NN/B#_V## - Title/
  ANGLES/    B#_V##_A-cam.mov   B#_V##_B-cam.mov   (ProRes 422 HQ 1920x1080 23.976, PCM/AAC 48k stereo, LAV audio both, NO captions)
  CAPTIONS/  B#_V##_captions.mov                   (ProRes 4444 alpha)
  _INFO.txt
```
Working files stay in `01_ORGANIZED/Batch_NN/Vid_MM/{Synced,Cut}`. B-roll → `07_QUERY_PULLS/b#v##-broll/<beat>/`.

**Lav-cam selection:** auto-detect (level/clarity) per video; surfaced in the review for a one-tap override. Wrong audio is a cheap re-mux, never silently shipped.

**`broll.py`:** reuse the footage-puller method (horizontal display-orientation only, never photos, ~5/beat). Add a **rotation-aware horizontal flag** to the shared SQLite index (via footage-organizer's non-destructive `_migrate` pattern) so horizontal selection is instant instead of re-probing every clip each run.

---

## The audio-cleanup spike (do first, it gates `audio_clean.py`)

Adobe Podcast Enhance is web/app-first; API access is gated/unverified. Evaluate integration-friendly alternatives on a real Sai lav clip, compared to Gray's current Adobe Podcast output:
- **ElevenLabs Audio Isolation API** (already on the ElevenLabs account; cheap, easy)
- **Local DeepFilterNet / Resemble-Enhance** (free, RTX 5070, no upload)
- **Auphonic API** (podcast-grade leveling + denoise) — fallback

**Decision criterion:** closest to Adobe Podcast quality at acceptable speed/cost, runs unattended in the pipeline. Winner implemented behind `audio_clean.clean(in_wav) -> clean_wav`; the interface stays stable if we swap backends later.

---

## Error handling

- Each stage validates its inputs at the real boundary (missing source clip, failed sync confidence, empty transcript) and fails that **video** with a clear reason — the batch continues with the others.
- Sync confidence below threshold → flag for manual offset rather than guessing.
- Verification-gate failures flag + block, never silently ship.
- Paid steps (audio API, if chosen) are cached by input hash; never re-run a paid call without reason.

---

## Testing

- **Unit:** `select.py` rejection/dedupe/pause-collapse on synthetic transcripts; `clipguard` on synthetic energy curves (incl. the "word rings past Whisper's marked end" case from Vid 4); `config` platform-detect; manifest parsing.
- **Integration:** run end-to-end on **Batch 4 Vid 4** (already produced this session) → package must match V03 specs; verification gate passes.
- **Regression:** a transcript+audio fixture where a naive fixed tail clips the last word → assert the guard prevents it (the exact bug from this session).

---

## Open questions for Gray (training gaps surfaced by the deep dive)

1. **Codec — RESOLVED (2026-06-20): ProRes 422 HQ for angle cuts.** These are editing intermediates (multicam scrubbing + re-export from Premiere), so all-intra ProRes wins: glitch-free scrubbing/concat seams and no stacked generation loss. Captions stay ProRes 4444 alpha. V01–V03 (H.264) are grandfathered; standard applies V04 onward. (This was the concrete "drift" example — the two old families disagreed H.264 vs ProRes 422.)
2. **Composite vs. single take** — rule says "composite when the best version spans two takes," but the threshold (how many flubs before compositing is worth it) is implied, not explicit.
3. **A vs B angle preference** — when both cams have a clean take of a line, is there a rule, or do you always angle-cut in Premiere? (Affects whether the package hints a default angle.)
4. **Color/level matching between takes** — no rule found. Manual in Premiere, or should the pipeline normalize audio loudness at least?
5. **B-roll per-beat selection thresholds** — "5 horizontal per beat" is set, but the content+fit criteria are thin. Want to tighten what makes a clip fit a beat?
6. **Tail by ending phoneme** — current tail is ~0.25–0.30s + clip-guard; fricative endings (s/f/sh) may ring longer than stops (t/p/k). Clip-guard already adapts by energy, so likely a non-issue — confirming.

I don't need all of these to start; #1 is the only one that blocks the build. The rest refine `select.py` and we can tune them against the before/after diffs.

## Out of scope (Phase 1)

- The drop→split→group front-door (Phase 2 — footage-organizer `batch` extension with clap/"Section N" detection).
- FCPXML timeline generation (Phase 3).
- Auto angle-switching, auto b-roll placement on a timeline, vertical reframe, thumbnails (Gray keeps editorial assembly in Premiere).

---

## Success criteria

- One command runs an organized batch end-to-end on **either machine, identical code**.
- Every shipped cut passes the verification gate — **no clipped words reach Gray**, ever.
- Gray's only hands-on step is the batched review.
- Output packages follow the locked layout (ANGLES/CAPTIONS/_INFO); angle codec standardized to ProRes 422 HQ from V04 onward (V01–V03 H.264 grandfathered); FCPXML-ready for Phase 3.
- A new batch goes from organized → reviewed packages in well under "30 minutes each, daily."
