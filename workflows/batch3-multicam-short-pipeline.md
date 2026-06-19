# SOP: Batch 3 Multicam Short Pipeline (A/B-cam interview shorts)

**Status:** LIVE — Mac, free (mlx_whisper + ffmpeg, no paid APIs)
**Audience:** Gray, a handoff editor/assistant, or any future Claude session. Written so someone who didn't build it can run it.
**Proven on:** Batch 3 Vid 1 ("Business is Spiritual") + Vid 2 ("Scaling — Every Unit as Good as 10,000"), Jun 2026.
**Scripts:** `python-scripts/multicam-mirror/batch3_pipeline/` (`build_cut.py`, `caption_render.py`) + `python-scripts/multicam-mirror/sync.py`.

---

## What this produces (per video)

From one interview take (Gray asks a question off-camera, Sai answers, filmed on two cameras) you get:
1. A **synced A/B pair** (both angles starting on the same instant).
2. A **tight cut** of both angles (question + best-take answer, dead air removed), frame-aligned so they drop onto a multicam timeline.
3. A **caption layer** (transparent .mov, Sai house style) you composite on top.
4. Two **finished videos** — an A-cam version and a B-cam version, captions burned in.
5. A **B-roll folder** of horizontal-only clips matched to the script, by beat.

---

## Plain-language glossary (for handoff)

- **A-cam / B-cam** — the two cameras. A-cam = the `C####.MP4` files. **B-cam = the side / more zoomed-in angle = the `MVI_####.MP4` files.**
- **Sync** — lining the two cameras up in time so they play together (we do it by matching their audio).
- **Offset** — how many seconds apart the two cameras started recording.
- **Cut / selects** — choosing which sentences to keep and stitching them together.
- **Alpha .mov** — a video file with a see-through background (just the captions), to lay over the footage in Premiere.
- **mlx_whisper** — a free Mac transcription tool (turns speech into text with the timing of every word).

---

## Prerequisites (one-time)

- [ ] **Footage SSD mounted** at `/Volumes/Footage` (check with `ls /Volumes`). If it shows as `Footage 1` or isn't there, re-plug it.
- [ ] `ffmpeg` + `ffprobe` installed (`which ffmpeg`).
- [ ] `mlx_whisper` installed (`which mlx_whisper`). First run downloads the model.
- [ ] Python 3 with `scipy` + `numpy` (system python is fine: `python3 -c "import scipy"`).
- [ ] PIL for captions — use the sai-captions venv python: `~/Desktop/my-project/python-scripts/sai-captions/venv/bin/python`.

---

## Per-video inputs

- **Title + clip pair:** see `01_ORGANIZED/Batch_03/Vid_NN/_INFO.txt` and `_b3_edit/.tmp/batch3_split.py` (PAIR map). Vid 3 = "Shedding the old me", C2742 / MVI_5044.
- **USE THE FULL SOURCE CLIPS, not the `_vNN` pre-trims:**
  - A-cam: `01_ORGANIZED/A Cam Batch 3/C####.MP4`
  - B-cam: `01_ORGANIZED/B-Cam Batch 3/MVI_####.MP4`
  - (The `Batch_03/Vid_NN/A-cam/C####_vNN.MP4` sub-clips start at the answer and **cut Gray's question off** — don't use them.)

---

## THE AUDIO RULE (current standard)

**The deliverable audio is the B-cam audio, only.** Once the two cams are synced, every finished export uses the **B-cam's audio track** end to end (it has the clear question and is consistent through the answer). Do **not** mix in A-cam audio. (Earlier Vid 2 used a B-question/A-answer blend — that's deprecated; B-cam-only is the rule now.)

---

## Steps

### 1 — Sync
Extract mono 48k WAV from each FULL clip, then:
```bash
python python-scripts/multicam-mirror/sync.py A.wav B.wav    # prints offset = tB - tA
```
- **Positive offset = B-cam started first** (usual). Confidence (peak/std) should be >20.
- Build the synced pair: A from `0`, B from `offset`, both length = `min(durA, durB − offset)`, keep native fps. Save to `Batch_03/Vid_NN/Synced/Vid_NN_{A,B}-cam_synced.mp4`.
- **Verify:** re-extract both audios, cross-correlate → residual should be ≈ 0 ms.

### 2 — Transcribe (free)
```bash
mlx_whisper --model mlx-community/whisper-large-v3-mlx --word-timestamps True \
  --language en --output-format json --output-dir <Synced/> <Vid_NN_A-cam_synced.mp4>
```
- The **question is usually only clear on the B-cam** mic. Also transcribe the B-cam and convert its question words to synced time: `synced = B_orig − offset`.

### 3 — Selection (editorial — show Gray before rendering)
Read the transcript. Keep the **question (hook)** + the best-take answer sentences. **Drop:** false starts, duplicate/retake lines, "Alright"/dead air. Write the kept sentences as `SEGMENTS` (synced time) in `build_cut.py`. **Show Gray the cut list (the words being kept) for approval before cutting.**

### 4 — Trim → two locked angle files
Edit `build_cut.py` (`VID`, `SEGMENTS`, `B_OFFSET`, the question-splice) then run it.
- Word-level keep-ranges; collapse pauses > `PAUSE_S` (~0.45).
- **Handles: LEAD 0.08, TAIL 0.30.** Long tail is mandatory — Whisper marks word-ENDS early, so a short tail clips Sai mid-word.
- Per-segment override where a **retake butts against a kept line** → use the clean take that has air to ring out.
- **fps-lock both cams to 24000/1001** (`-r … -vsync cfr`).
- **Concat must RE-ENCODE** (`-fflags +genpts -r 24000/1001 -movflags +faststart`). NEVER `-c copy` — stream-copy seams make QuickTime freeze mid-clip.
- Output: `Cut/Vid_NN_{A,B}-cam_CUT.mp4` (identical length, ≈0 ms apart) + `caption_words.json` + `cut_plan.txt`.

### 5 — Captions (alpha .mov, landscape, Sai style)
```bash
~/Desktop/my-project/python-scripts/sai-captions/venv/bin/python \
  python-scripts/multicam-mirror/batch3_pipeline/caption_render.py Vid_NN
```
- 1920×1080, Montserrat SemiBold white, soft drop shadow, lower-third, 2–3 words/card.
- Driven by `caption_words.json` (no re-transcription → nothing clips). Output `Vid_NN_captions.mov` (ProRes 4444 alpha).

### 6 — Render finals (A-cam + B-cam versions) — **B-CAM AUDIO ONLY**
For each angle: video = that angle's CUT, overlay `captions.mov`, **audio = the B-cam CUT's audio track (both versions use B-cam audio).** libx264 crf18, faststart.
- **Verify:** decode-clean (`ffmpeg -v error … -f null -`), `freezedetect` finds nothing, both versions equal length.
- Optional deliverable: `Vid_NN B-cam audio.wav` (B-cam audio of the cut, 48k stereo).

### 7 — B-roll (DEEP, horizontal-only, NEVER photos)
See [[feedback-broll-horizontal-no-photos]].
- ffprobe **display** orientation of the whole `05_FOOTAGE_LIBRARY` (rotation-aware: `if abs(rot)%180==90: swap w,h; horizontal = w>h`). Build a horizontal-only inventory.
- Extract one frame per horizontal clip → labeled contact sheets → vision agents tag each clip to a beat by content + fit (1–5).
- Copy top ~3–4 horizontal **videos** per beat to `07_QUERY_PULLS/b3vNN-broll-deep/<beat>/`. Re-verify: 0 vertical, 0 jpg. (Frames go to /tmp only.)

### 8 — Review
Light proxy of the captioned cut → minimal HyperFrames project (`web-apps/hyperframes/sai-b3vNN-review/`, `npx hyperframes preview`) → give Gray the localhost URL to scrub.

---

## The 8 gotchas (do not relearn these)

1. **Full source clips**, not the `_vNN` pre-trims (they cut the question).
2. **Question is on the B-cam** audio — splice it in.
3. **TAIL ≥ 0.30s** or trailing words clip.
4. **Watch for retakes** butting a kept line → use the clean take with air after it.
5. **Concat = re-encode**, never stream-copy → or QuickTime freezes.
6. **fps-lock both cams to 23.976** so cuts align.
7. **Deliverable audio = B-cam only.**
8. **B-roll: horizontal-only (display orientation) + never photos.** Everything runs free.

---

## Output layout (per video)

```
01_ORGANIZED/Batch_03/Vid_NN/
  Synced/  Vid_NN_{A,B}-cam_synced.mp4  (+ A-cam .json transcript)
  Cut/     Vid_NN_{A,B}-cam_CUT.mp4   Vid_NN_captions.mov
           Vid_NN ... - {A,B}-cam FINAL.mp4   (captions burned, B-cam audio)
           caption_words.json   cut_plan.txt
07_QUERY_PULLS/b3vNN-broll-deep/<beat>/   (horizontal video clips + _PULL-MANIFEST.md)
```

---

## Verification checklist (before calling a video done)

- [ ] Synced pair residual ≈ 0 ms.
- [ ] Both CUT files identical length, ≈0 ms apart, 23.976 fps.
- [ ] No clipped words at cut joins (longer tail / clean retake).
- [ ] Finals: decode-clean, no freeze, **B-cam audio**, captions aligned.
- [ ] B-roll: every clip horizontal, zero photos.
```
