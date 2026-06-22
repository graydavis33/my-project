# batch-pipeline

One cross-platform tool that edits Sai 2-cam batch interview shorts end-to-end —
from raw camera files to a Premiere-ready deliverable folder.

**Consolidates and will eventually retire** the drift-prone Mac
`multicam-mirror/batch3_pipeline/` and Windows `_b3_edit/` scripts.
Those old scripts are **not yet retired** — they remain until a supervised real-footage
parity run confirms output matches (Task 9, pending).

Full design spec: `docs/superpowers/specs/2026-06-20-batch-pipeline-edit-core-design.md`
Implementation plan: `docs/superpowers/plans/2026-06-20-batch-pipeline-edit-core.md`

---

## Status

| Stage | Module | Built + tested |
|---|---|---|
| 1 Config | `config.py` | yes |
| 2 Sync | `sync.py` | yes |
| 3 Clip guard | `clipguard.py` | yes |
| 4 Transcribe | `transcribe.py` | yes |
| 5 Cut | `cut.py` | yes |
| 6 Captions | `captions.py` | yes |
| 7 Verify | `verify.py` | yes |
| 8 Package | `package.py` | yes |
| 9 `run.py` driver | — | PENDING |
| 10 Real-footage parity + old-script retirement | — | PENDING |

---

## Orchestrator — human-in-the-loop (prep → review → render)

`orchestrate.py` now runs the **proven manual trim recipe** (the Vid_09/Vid_13 "best first-try trim" process), NOT a fully-automatic cut. Shape:

```
python orchestrate.py --batch 3 --video 13 --prep     # verify-sync, transcribe B-cam, seed editable SEGMENTS.json, build trim-review
#   -> open the HyperFrames trim-review (web-apps/hyperframes/sai-bNvMM-trim-review/), edit Cut/SEGMENTS.json
python orchestrate.py --batch 3 --video 13 --render    # per-segment ProRes reels + H.264 angles -> deliverable
```

- **`--prep`** → `sync.verify_offset` (envelope + bandpassed 300–3000 Hz xcorr with a dominance/confidence check — sharper than `compute_offset`'s 30s window), word-level B-cam Whisper transcript, seeds `Cut/SEGMENTS.json` from `select.py` (now only a **first-draft proposal Gray edits**), and auto-builds the HyperFrames trim-review via `review.py`.
- **You** scrub the review, edit segment in/out times in `Cut/SEGMENTS.json`.
- **`--render`** (`render.py`) → per-segment ProRes 422 reels (B-cam audio on both, A-cam falls back to B-cam video where the hook lands before A's footage), H.264 angles, export to the deliverable + `_INFO.txt`. ProRes masters stay in `Cut/`.

`select.py` is no longer the editorial decider — a human picks segments off the transcript (that's why the manual cut beat the old auto cut). Built 2026-06-21, 36 tests green.

---

## Setup

Copy `.env.example` to `.env` and fill in the path for your machine:

```
SAI_LIBRARY_ROOT=D:/Sai          # Windows
SAI_LIBRARY_ROOT=/Volumes/Footage/Sai   # Mac
```

The pipeline reads this value via `config.library_root()` — every file path is
built with `pathlib` so it works on both platforms.

---

## Cross-platform details

- **Whisper backend** — auto-detected by `config.whisper_backend()`:
  `mlx` (mlx-community/whisper-large-v3-mlx) on Apple Silicon Mac;
  `openai` (openai-whisper, CUDA) on Windows and Intel Mac.
- **Encoding** — UTF-8 forced on stdout/stderr at import time in `config.py`
  and `captions.py` (prevents Windows cp1252 crashes on arrows/em-dashes).
- **Paths** — `pathlib.Path` only throughout; no `os.path.join` string glue.

---

## Stages

### 1. `config.py`
Constants and environment helpers shared by all stages.

- `library_root() -> Path` — reads `SAI_LIBRARY_ROOT` from env; raises if unset.
- `whisper_backend() -> str` — returns `"mlx"` on Apple Silicon, `"openai"` otherwise.
- `font_path() -> Path` — resolves Montserrat.ttf from `python-scripts/sai-captions/fonts/`.
- Constants: `FPS = "24000/1001"`, `PRORES422`, `PRORES4444` ffmpeg arg lists, `CAPTION_STYLE` dict.

### 2. `sync.py` — audio offset detection
- `compute_offset(a_wav, b_wav, window_s=30.0) -> float` — cross-correlates the first
  `window_s` seconds of two WAV files; returns the offset in seconds such that
  `A_timestamp + offset = B_timestamp`. Negative means B started after A.

### 3. `clipguard.py` — clean output trim
- `snap_out(audio, sr, sout, next_word_start) -> float` — scans past the nominal cut point
  from +100 ms to +600 ms (grace zone before scoring window) and returns the quietest moment
  within that 100–600 ms scoring window, capped before the next word starts. Prevents audio
  clipping at segment boundaries.

### 4. `transcribe.py` — Whisper transcription
- `to_words(raw, shift) -> dict` — normalises a raw Whisper JSON result, shifting all
  timestamps by `shift` seconds (used to align lav-mic transcription to the cut timeline).
- `transcribe(media, shift=0.0) -> dict` — transcribes `media` with the auto-detected
  backend; returns `{"segments": [...]}` with per-word timestamps.

### 5. `cut.py` — ProRes 422 angle cuts
- `plan(words, ranges, audio, sr) -> (keep, caps, total)` — given edit ranges
  `(sin, sout, head, tail)`, applies `snap_out` to each out-point, collects keep
  segments `(start, duration)`, and builds a word-timing list for captions.
- `build_cut(synced_a, synced_b, lav_wav, words, ranges, out_dir, vid_tag) -> dict` —
  extracts each keep segment from both camera angles (lav audio on both), concatenates
  to ProRes 422 `.mov` files, and writes `caption_words.json`. Returns paths to
  A-cam cut, B-cam cut, `caption_words.json`, and total duration.

### 6. `captions.py` — alpha caption layer
- `clean(word) -> str` — strips punctuation and applies the preserve-case map
  (`i` → `I`, `sai` → `Sai`, etc.); lowercases everything else.
- `group(words) -> list` — groups word dicts into caption cards of ≤ 3 words,
  splitting on pause gaps > 0.45 s or card duration > 1.6 s. Returns
  `[(card_words, start, end)]`.
- `render(caption_words, ref_video, out_mov) -> Path` — renders all cards as
  Montserrat SemiBold PNGs with Gaussian shadow, overlays them via ffmpeg
  `overlay` filter chain, and encodes to ProRes 4444 yuva444p10le alpha `.mov`.

### 7. `verify.py` — quality gate
- `check_no_clips(lav_wav, synced_outs) -> list` — checks each output point for
  audio clipping: flags any point where both the 60 ms before and after exceed
  RMS 700 (indicating a hard clip in speech).
- `decode_clean(path) -> bool` — runs `ffmpeg -f null` decode and returns True if
  no errors in stderr.
- `same_length(a, b, tol=0.05) -> bool` — confirms A-cam and B-cam cuts are within
  50 ms of each other.
- `audio_md5(path) -> str` — hashes the 48 kHz mono audio stream for bit-exact
  A/B comparison.
- `gate(a_cut, b_cut, lav_wav, synced_outs) -> dict` — runs all checks and returns
  a result dict with a top-level `"passed"` bool.

### 8. `package.py` — deliverable layout
- `folder_name(batch_n, vid_n, title) -> str` — returns `"B#_V## - Title"`.
- `deliver(batch_n, vid_n, title, a_cut, b_cut, captions_mov, info, out_root=None) -> Path` —
  copies finals into the deliverable tree and writes `_INFO.txt`. Returns the package dir.

---

## Deliverable layout

```
08_AI_EDITS/shorts/Batch_NN/B#_V## - Title/
    ANGLES/
        B#_V##_A-cam.mov        # ProRes 422, lav audio
        B#_V##_B-cam.mov        # ProRes 422, lav audio
    CAPTIONS/
        B#_V##_captions.mov     # ProRes 4444 alpha, transparent except caption text
    _INFO.txt
```

`08_AI_EDITS/shorts/` lives under `SAI_LIBRARY_ROOT` (e.g. `D:/Sai/08_AI_EDITS/shorts/`).

---

## Running tests

```bash
# Windows
py -m pytest python-scripts/batch-pipeline/tests/ -q

# Mac / Linux
python3 -m pytest python-scripts/batch-pipeline/tests/ -q
```
