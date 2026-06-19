# Workflow: Batch 3 Multicam Short Pipeline (A/B-cam interview shorts)

**Status:** LIVE — Mac (`/Volumes/Footage`), free (mlx_whisper + ffmpeg, no paid APIs)
**Scripts:** `python-scripts/multicam-mirror/batch3_pipeline/` (`build_cut.py`, `caption_render.py`) + `python-scripts/multicam-mirror/sync.py` (offset)
**Proven on:** Batch 3 Vid 1 ("Business is Spiritual") + Vid 2 ("Scaling — Every Unit as Good as 10,000"), 2026-06-18.

---

## Objective

Turn one organized Batch 3 interview take (Gray asks a question, Sai answers, two cameras) into a finished short: synced A/B angles, a tight word-accurate cut, Sai-style captions (alpha .mov), burned A-cam + B-cam final versions, and a horizontal-only B-roll pull. Built so the WHOLE batch (Vid 1–13) gets the same treatment, one video per pass.

---

## When to Run

- Once per Batch 3 video (Vid_01 … Vid_13). Do one fully, get Gray's review, then the next.
- Each batch video = a question Gray asks + Sai's answer. Titles/sources: see `01_ORGANIZED/Batch_03/Vid_NN/_INFO.txt`.

---

## Source files (per video)

- **Use the FULL source clips, NOT the `_vNN` pre-trims.** The `Batch_03/Vid_NN/A-cam/C####_vNN.MP4` sub-clips were trimmed to start at the answer and **cut off Gray's question.** Use:
  - A-cam: `01_ORGANIZED/A Cam Batch 3/C####.MP4`
  - B-cam: `01_ORGANIZED/B-Cam Batch 3/MVI_####.MP4`  (B-cam = the side / more zoomed-in angle)
- The A↔B clip pairing is in `01_ORGANIZED/_b3_edit/.tmp/batch3_split.py` (PAIR map) and each `Vid_NN/_INFO.txt`.

---

## The 8 phases

### 1. Sync (audio cross-correlation)
Extract mono 48k wav from each FULL clip → `multicam-mirror/sync.py` `compute_offset(a,b)`.
- `offset = tB − tA`. **Positive = B-cam started first** (it usually did — by a few seconds).
- Confidence: peak/std should be >20 (we see 140–150).
Build the synced pair (trim both to the common overlap, synced t=0 = A-cam full t=0, keep native fps): A from `0`, B from `offset`, both length = `min(durA, durB−offset)`. Re-verify residual ≈ 0 ms.

### 2. Transcribe (free, Mac)
`mlx_whisper --model mlx-community/whisper-large-v3-mlx --word-timestamps True --language en --output-format json` on the **synced A-cam**.
- **The question is often only clear on the B-cam mic** (faint on A-cam → Whisper skips it). Also transcribe the B-cam and splice the question words in, converting B time → synced: `synced = B_orig − offset`.

### 3. Selection (editorial — the part that needs judgment)
Read the transcript. Keep: the **question** (hook, from B-cam) + the best-take answer segments. **Drop: false starts, duplicate/retake lines, "Alright"/dead air.** Define `SEGMENTS` (in synced time) in `build_cut.py`.

### 4. Trim → two locked angle files
`python build_cut.py` (edit `VID`, `SEGMENTS`, `B_OFFSET`, question-word splice per video).
- Word-level keep-ranges from the transcript; collapse pauses > `PAUSE_S` (0.45–0.50).
- Handles: **LEAD 0.08, TAIL 0.30.** Tail must be long — Whisper marks word-ENDS early, so a short tail clips the last word. (This was the repeated "you cut him off at Ns" bug.)
- **Per-segment overrides** where a retake butts against a line: use the CLEAN take that has air to ring out (e.g. the 2nd "…worse and worse" take), and set head=0 where a head pad would grab a dropped duplicate's fragment.
- **fps-lock both cams** to `24000/1001` (`-r … -vsync cfr`) so cut points stay frame-aligned.
- **CONCAT MUST RE-ENCODE, never `-c copy`.** Stream-copy concat leaves per-segment timestamps that make **QuickTime freeze** at a seam. Re-encode with `-fflags +genpts -r 24000/1001 -movflags +faststart`.
- Output: `Batch_03/Vid_NN/Cut/Vid_NN_A-cam_CUT.mp4` + `_B-cam_CUT.mp4` (identical length, ≈0 ms apart) + `caption_words.json` + `cut_plan.txt`.

### 5. Captions (alpha .mov, Sai house style, LANDSCAPE)
`python caption_render.py Vid_NN` (uses the sai-captions venv for PIL).
- 1920×1080, Montserrat SemiBold white, soft drop shadow, lower-third, 2–3 words/card.
- Driven by `caption_words.json` (the cut's word timings) → **no re-transcription, nothing clips.**
- Output: `Vid_NN_captions.mov` (ProRes 4444 alpha).

### 6. Render/export finals (A-cam + B-cam versions)
For each angle: video = that angle's CUT, overlay `captions.mov`, audio = **combined best-audio** (B-cam audio for the question span, A-cam audio for the answer — A-cam is the better mic for the answer, B-cam is the only clear one for the question). libx264 crf18, faststart. Verify decode-clean + `freezedetect` + equal length.
- Also export `Vid_NN B-cam audio.wav` on request (B-cam audio of the cut, 48k stereo).

### 7. B-roll (DEEP, horizontal-only, NEVER photos) — see [[feedback-broll-horizontal-no-photos]]
- ffprobe **display** orientation of the whole `05_FOOTAGE_LIBRARY` (rotation-aware: `if abs(rot)%180==90: swap w,h; horizontal = w>h`). Build a horizontal-only inventory. Most `06_ASSETS/All Broll` are vertical phone clips; the real pool is the Sony library incl. the big `_TO_SORT`.
- Extract one frame per horizontal clip → tile into labeled contact sheets → fan out vision agents to tag each clip to a beat by content + fit (1–5).
- Copy top ~3–4 horizontal **videos** per beat into `07_QUERY_PULLS/b3vNN-broll-deep/<beat>/`. Re-verify: 0 vertical, 0 jpg. Frames go to /tmp only.

### 8. Review in HyperFrames
Make a light proxy of the captioned cut → minimal HyperFrames project (`web-apps/hyperframes/sai-b3vNN-review/`, `npx hyperframes preview`) so Gray scrubs it in Studio. A side-by-side A/B sync-check comp is the same pattern with both videos on separate tracks.

---

## Hard-won gotchas (do not relearn these)

1. **Use full source clips** (`A Cam Batch 3` / `B-Cam Batch 3`), not the `_vNN` pre-trims — they cut the question.
2. **Question lives on the B-cam** audio; splice it in.
3. **TAIL ≥ 0.30** or trailing words clip.
4. **Watch for retakes** butting against a kept line → use the clean take with air after it.
5. **Concat = re-encode**, never stream-copy → otherwise QuickTime freezes mid-clip.
6. **fps-lock both cams to 23.976** so cuts align on the multicam timeline.
7. **B-roll: horizontal-only (display orientation), never photos.**
8. Everything is free (mlx_whisper + ffmpeg) — no paid API calls.

---

## Output layout (per video)

```
01_ORGANIZED/Batch_03/Vid_NN/
  Synced/   Vid_NN_A-cam_synced.mp4  Vid_NN_B-cam_synced.mp4  (+ A-cam json transcript)
  Cut/      Vid_NN_A-cam_CUT.mp4  Vid_NN_B-cam_CUT.mp4  Vid_NN_captions.mov
            Vid_NN ... - A-cam FINAL.mp4  ... - B-cam FINAL.mp4  (captions + combined audio)
            caption_words.json  cut_plan.txt
07_QUERY_PULLS/b3vNN-broll-deep/<beat>/   (horizontal video clips + _PULL-MANIFEST.md)
```
