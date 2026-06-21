# Batch Pipeline — Edit Core (Plan 1: Unified Core to Parity / Drift Kill) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build ONE cross-platform `python-scripts/batch-pipeline/` that runs an organized batch video through sync → cut+clip-guard → captions → verify → package (ProRes 422 angles + alpha captions + _INFO), proven to reproduce Batch 3 Vid 4, then delete the two old drift-prone script families.

**Architecture:** A driver (`run.py`) walks a per-video config through ordered, independently-tested stage modules. All paths come from `SAI_LIBRARY_ROOT` and the Whisper backend is auto-detected, so the same code runs identically on Mac and Windows — that is the drift fix. Stages are ports of today's proven code (`_cut_v04.py`, `_caption_v04.py`, `multicam-mirror/sync.py`) consolidated and config-driven.

**Tech Stack:** Python 3, ffmpeg/ffprobe (PATH), numpy, scipy, Pillow, openai-whisper (Win/CUDA) / mlx_whisper (Mac), pytest 9.

## Global Constraints

- Library root from env `SAI_LIBRARY_ROOT` (`/Volumes/Footage/Sai` Mac, `D:/Sai` Windows). No drive-letter literals; `pathlib` only.
- Force UTF-8 stdout/stderr at every entry point (`sys.stdout.reconfigure(encoding="utf-8")`).
- FPS lock: `24000/1001` (23.976) on every video re-encode.
- Concat MUST re-encode (never `-c copy`) with `-fflags +genpts`.
- Angle-cut codec: **ProRes 422 HQ** (`-c:v prores_ks -profile:v 3`), `.mov`, audio AAC 48k stereo. (V01–V03 H.264 grandfathered; standard applies V04+.)
- Caption codec: ProRes 4444 alpha (`-c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le`).
- Caption house style: Montserrat SemiBold, size 60, white, soft drop shadow, lower-third (`TOP_MARGIN=858`), lowercase except `I`/`I'm`/`I've`/`I'll`/`I'd` + proper nouns (Sai/Trendify), no punctuation, ≤3 words/card.
- Deliverable layout: `08_AI_EDITS/shorts/Batch_NN/B#_V## - Title/` → `ANGLES/B#_V##_{A,B}-cam.mov` + `CAPTIONS/B#_V##_captions.mov` + `_INFO.txt`.
- Audio = the lav-mic camera on BOTH angles (identical track). Lav cam is a per-video config field for now.
- Clip-guard on every cut-out: search `[sout, sout+0.6]`, cap at next transcript word − 0.02s, cut at the quietest 60ms.
- Tests mirror the footage-organizer pattern (`tests/` package + `conftest.py`); run with `py -m pytest` (Win) / `python3 -m pytest` (Mac).

---

### Task 1: Project scaffold + `config.py`

**Files:**
- Create: `python-scripts/batch-pipeline/__init__.py` (empty)
- Create: `python-scripts/batch-pipeline/config.py`
- Create: `python-scripts/batch-pipeline/tests/__init__.py` (empty)
- Create: `python-scripts/batch-pipeline/tests/conftest.py`
- Test: `python-scripts/batch-pipeline/tests/test_config.py`

**Interfaces:**
- Produces: `library_root() -> Path`; `whisper_backend() -> str` (`"mlx"`|`"openai"`); `font_path() -> Path`; constants `FPS="24000/1001"`, `PRORES422=["-c:v","prores_ks","-profile:v","3"]`, `PRORES4444=["-c:v","prores_ks","-profile:v","4444","-pix_fmt","yuva444p10le"]`, `CAPTION_STYLE` dict.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import os, sys, platform
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config

def test_library_root_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("SAI_LIBRARY_ROOT", str(tmp_path))
    assert config.library_root() == tmp_path

def test_library_root_missing_raises(monkeypatch):
    monkeypatch.delenv("SAI_LIBRARY_ROOT", raising=False)
    try:
        config.library_root(); assert False, "expected error"
    except RuntimeError:
        pass

def test_whisper_backend_values():
    assert config.whisper_backend() in ("mlx", "openai")

def test_fps_constant():
    assert config.FPS == "24000/1001"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_config.py -v`
Expected: FAIL (`ModuleNotFoundError: config`)

- [ ] **Step 3: Write `config.py`**

```python
import os, sys, platform
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

FPS = "24000/1001"
PRORES422 = ["-c:v", "prores_ks", "-profile:v", "3"]
PRORES4444 = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le"]
CAPTION_STYLE = {
    "font_size": 60, "top_margin": 858, "max_words": 3,
    "text_color": (255, 255, 255, 255), "shadow_color": (0, 0, 0, 165),
    "shadow_offset": (0, 5), "shadow_blur": 6,
    "preserve_case": {"i": "I", "i'm": "I'm", "i've": "I've", "i'll": "I'll",
                      "i'd": "I'd", "sai": "Sai", "sai's": "Sai's"},
    "punct": ".,!?;:\"()[]{}—–-…",
}

def library_root() -> Path:
    v = os.environ.get("SAI_LIBRARY_ROOT")
    if not v:
        raise RuntimeError("SAI_LIBRARY_ROOT not set (see batch-pipeline .env)")
    return Path(v)

def whisper_backend() -> str:
    return "mlx" if platform.system() == "Darwin" and platform.machine() == "arm64" else "openai"

def font_path() -> Path:
    here = Path(__file__).resolve().parents[2]  # repo root
    return here / "python-scripts" / "sai-captions" / "fonts" / "Montserrat.ttf"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_config.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add python-scripts/batch-pipeline/__init__.py python-scripts/batch-pipeline/config.py python-scripts/batch-pipeline/tests/
git commit -m "feat(batch-pipeline): cross-platform config + constants"
```

---

### Task 2: Port `sync.py`

**Files:**
- Create: `python-scripts/batch-pipeline/sync.py`
- Test: `python-scripts/batch-pipeline/tests/test_sync.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `compute_offset(a_wav: Path, b_wav: Path, window_s=30.0) -> float` (tB − tA; add to an A-time to get the B-time). Identical contract to `multicam-mirror/sync.py`.

- [ ] **Step 1: Write the failing test** (synthetic: shift a noise signal by a known lag)

```python
# tests/test_sync.py
import sys, numpy as np
from pathlib import Path
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sync

def test_known_offset(tmp_path):
    sr = 48000; rng = np.random.default_rng(0)
    base = rng.standard_normal(sr*10).astype(np.float32)
    lag = int(2.0*sr)                     # B starts 2s "after" -> B leads A by 2s of content
    a = base[lag:]; b = base[:-lag]
    wavfile.write(tmp_path/"a.wav", sr, a)
    wavfile.write(tmp_path/"b.wav", sr, b)
    off = sync.compute_offset(tmp_path/"a.wav", tmp_path/"b.wav")
    assert abs(off - 2.0) < 0.01
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_sync.py -v`
Expected: FAIL (`ModuleNotFoundError: sync`)

- [ ] **Step 3: Port the module.** Copy `python-scripts/multicam-mirror/sync.py` verbatim to `python-scripts/batch-pipeline/sync.py` (its `compute_offset` is the proven implementation — cross-correlation, no negation, see its docstring). No logic changes.

- [ ] **Step 4: Run test to verify it passes**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_sync.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add python-scripts/batch-pipeline/sync.py python-scripts/batch-pipeline/tests/test_sync.py
git commit -m "feat(batch-pipeline): port audio-sync offset"
```

---

### Task 3: `clipguard.py` (generalized from today's V04 guard)

**Files:**
- Create: `python-scripts/batch-pipeline/clipguard.py`
- Test: `python-scripts/batch-pipeline/tests/test_clipguard.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `snap_out(audio: np.ndarray, sr: int, sout: float, next_word_start: float|None) -> float` — returns the cut-out time: the quietest 60ms in `[sout, min(sout+0.6, next_word_start-0.02)]`.

- [ ] **Step 1: Write the failing test** (a word ringing past its marked end, then a louder breath, then the next word)

```python
# tests/test_clipguard.py
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import clipguard

def _env(sr, segments):  # segments: list of (start, end, amp)
    a = np.zeros(int(8*sr), dtype=np.float32)
    rng = np.random.default_rng(0)
    for s, e, amp in segments:
        n = int((e-s)*sr); a[int(s*sr):int(s*sr)+n] = amp*rng.standard_normal(n)
    return a

def test_rings_out_then_cuts_in_the_dip():
    sr = 48000
    # word marked end at 1.00, but energy rings to 1.20; dip 1.20-1.30; loud breath 1.30-1.45
    a = _env(sr, [(0.0,1.20,0.3),(1.30,1.45,0.6)])
    out = clipguard.snap_out(a, sr, sout=1.00, next_word_start=None)
    assert 1.18 < out < 1.31   # cut in the dip, not mid-ring, not into the breath

def test_never_passes_next_word():
    sr = 48000
    a = _env(sr, [(0.0,1.05,0.3),(1.10,1.40,0.4)])
    out = clipguard.snap_out(a, sr, sout=1.00, next_word_start=1.10)
    assert out <= 1.08
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_clipguard.py -v`
Expected: FAIL (`ModuleNotFoundError: clipguard`)

- [ ] **Step 3: Write `clipguard.py`** (today's proven logic, parameterized on the audio array)

```python
import numpy as np

def _rms(a, sr, t, win=0.06):
    s = a[int(t*sr): int((t+win)*sr)]
    return float(np.sqrt(np.mean(s**2))) if len(s) else 0.0

def snap_out(audio, sr, sout, next_word_start):
    hard_cap = sout + 0.6
    if next_word_start is not None:
        hard_cap = min(hard_cap, next_word_start - 0.02)
    lo_bound = min(sout + 0.10, hard_cap)
    best_t, best_e = lo_bound, 1e18
    t = sout
    while t <= hard_cap + 1e-6:
        if t >= lo_bound:
            e = _rms(audio, sr, t)
            if e < best_e:
                best_e, best_t = e, t
        t += 0.02
    return best_t
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_clipguard.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add python-scripts/batch-pipeline/clipguard.py python-scripts/batch-pipeline/tests/test_clipguard.py
git commit -m "feat(batch-pipeline): clip-guard (never chop a trailing word)"
```

---

### Task 4: `cut.py` (ranges → A/B ProRes422 cuts + caption words)

**Files:**
- Create: `python-scripts/batch-pipeline/cut.py`
- Test: `python-scripts/batch-pipeline/tests/test_cut.py`

**Interfaces:**
- Consumes: `clipguard.snap_out`, `config.FPS`, `config.PRORES422`.
- Produces: `build_cut(synced_a: Path, synced_b: Path, lav_wav: Path, words: list[dict], ranges: list[tuple], out_dir: Path, vid_tag: str) -> dict` where `words` = `[{start,end,word}]` (synced time), `ranges` = `[(sin,sout,head,tail)]`. Writes `{vid_tag}_{A,B}-cam_CUT.mov`, `caption_words.json`, `cut_plan.txt`; returns `{"a": Path, "b": Path, "caption_words": Path, "total_s": float}`.

- [ ] **Step 1: Write the failing test** (pure range/word math — no ffmpeg; factor the planning out)

```python
# tests/test_cut.py
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cut

def test_plan_drops_dead_air_and_maps_caption_times():
    sr = 48000; audio = np.zeros(int(300*sr), dtype=np.float32)  # silence => snap_out cuts tight
    words = [{"start":10.0,"end":10.4,"word":"hello"},{"start":10.5,"end":10.9,"word":"world"}]
    ranges = [(10.0, 10.9, None, None)]
    keep, caps, total = cut.plan(words, ranges, audio, sr)
    assert len(keep) == 1
    assert caps[0]["word"] == "hello" and abs(caps[0]["start"]) < 0.2  # first kept word near t=0
    assert total > 0.9
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_cut.py -v`
Expected: FAIL (`ModuleNotFoundError: cut`)

- [ ] **Step 3: Write `cut.py`.** Port the body of `D:/Sai/01_ORGANIZED/Batch_03/Vid_04/_cut_v04.py` with these changes: (a) split the range/word math into `plan(words, ranges, audio, sr) -> (keep, caps, total)` (loop over ranges, `head=0.10`/`tail=0.25` defaults, `lo=sin-head`, `hi=clipguard.snap_out(audio, sr, sout, next_word_start)`, build `keep=[(lo,dur)]` and `caps` mapped to cut-time as in `_cut_v04`); (b) `build_cut(...)` calls `plan`, then `ff_extract`/`concat` using `config.FPS` and **`config.PRORES422`** (was libx264) writing `.mov`; (c) audio comes from `lav_wav` passed in (extract each range from the lav source so both angles carry identical lav audio); (d) read paths via args, not module constants. Show the `plan` function and the ProRes extract/concat exactly:

```python
import json, subprocess, tempfile
from pathlib import Path
import numpy as np
from scipy.io import wavfile
import clipguard, config

HEAD, TAIL = 0.10, 0.25

def plan(words, ranges, audio, sr):
    keep, caps, cum = [], [], 0.0
    for (sin, sout, head, tail) in ranges:
        head = HEAD if head is None else head
        lo = sin - head
        nxt = next((w["start"] for w in words if w["start"] >= sout - 1e-6), None)
        hi = clipguard.snap_out(audio, sr, sout, nxt)
        dur = hi - lo
        for w in [w for w in words if w["start"] < sout and w["end"] > sin]:
            caps.append({"start": round(cum + (w["start"]-lo), 3),
                         "end": round(cum + (w["end"]-lo), 3), "word": w["word"]})
        keep.append((lo, dur)); cum += dur
    return keep, caps, cum

def _extract(src, start, dur, dst):
    subprocess.run(["ffmpeg","-y","-ss",f"{start:.4f}","-i",str(src),"-t",f"{dur:.4f}",
        "-r",config.FPS,"-vsync","cfr",*config.PRORES422,
        "-c:a","aac","-b:a","256k","-ar","48000",str(dst)], check=True, capture_output=True)

def _concat(parts, dst):
    lf = dst.parent / (dst.stem + "_list.txt")
    lf.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts))
    subprocess.run(["ffmpeg","-y","-fflags","+genpts","-f","concat","-safe","0","-i",str(lf),
        "-r",config.FPS,*config.PRORES422,"-c:a","aac","-b:a","256k","-ar","48000",
        "-movflags","+faststart",str(dst)], check=True, capture_output=True)
    lf.unlink()

def build_cut(synced_a, synced_b, lav_wav, words, ranges, out_dir, vid_tag):
    out_dir.mkdir(parents=True, exist_ok=True)
    _, audio = wavfile.read(str(lav_wav)); audio = audio.astype(np.float32)
    sr = 48000
    keep, caps, total = plan(words, ranges, audio, sr)
    (out_dir/"caption_words.json").write_text(json.dumps(caps, indent=1), encoding="utf-8")
    res = {"caption_words": out_dir/"caption_words.json", "total_s": total}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for cam, src in (("A", synced_a), ("B", synced_b)):
            parts = []
            for i,(lo,dur) in enumerate(keep):
                p = td/f"{cam}_{i:02d}.mov"; _extract(src, lo, dur, p); parts.append(p)
            dst = out_dir/f"{vid_tag}_{cam}-cam_CUT.mov"; _concat(parts, dst); res[cam.lower()] = dst
    return res
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_cut.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add python-scripts/batch-pipeline/cut.py python-scripts/batch-pipeline/tests/test_cut.py
git commit -m "feat(batch-pipeline): cut stage (ProRes422 angles + caption words)"
```

---

### Task 5: `transcribe.py` (platform-shim Whisper)

**Files:**
- Create: `python-scripts/batch-pipeline/transcribe.py`
- Test: `python-scripts/batch-pipeline/tests/test_transcribe.py`

**Interfaces:**
- Consumes: `config.whisper_backend`.
- Produces: `to_words(raw: dict, shift: float) -> dict` (normalizes either backend's output to `{"segments":[{"start","end","words":[{start,end,word}]}]}` with `t -= shift`); `transcribe(media: Path, shift: float) -> dict` (runs the platform backend, then `to_words`).

- [ ] **Step 1: Write the failing test** (normalization only — no model load)

```python
# tests/test_transcribe.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import transcribe

def test_to_words_shifts_and_strips():
    raw = {"segments":[{"start":6.2,"end":7.0,"words":[
        {"start":6.2,"end":6.5,"word":" Hello"},{"start":6.5,"end":7.0,"word":"world "}]}]}
    out = transcribe.to_words(raw, shift=6.0)
    w = out["segments"][0]["words"]
    assert w[0]["word"] == "Hello" and abs(w[0]["start"]-0.2) < 1e-6
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_transcribe.py -v`
Expected: FAIL (`ModuleNotFoundError: transcribe`)

- [ ] **Step 3: Write `transcribe.py`**

```python
import json, subprocess, tempfile
from pathlib import Path
import config

def to_words(raw, shift):
    segs = []
    for s in raw.get("segments", []):
        ws = [{"start": round(float(w["start"])-shift, 3),
               "end": round(float(w["end"])-shift, 3),
               "word": w["word"].strip()} for w in s.get("words", [])]
        segs.append({"start": round(float(s["start"])-shift, 3),
                     "end": round(float(s["end"])-shift, 3), "words": ws})
    return {"segments": segs}

def transcribe(media, shift=0.0):
    if config.whisper_backend() == "openai":
        import whisper
        model = whisper.load_model("large-v3", device="cuda")
        raw = model.transcribe(str(media), language="en", word_timestamps=True)
    else:
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["mlx_whisper","--model","mlx-community/whisper-large-v3-mlx",
                "--word-timestamps","True","--language","en","--output-format","json",
                "--output-dir",td,str(media)], check=True)
            raw = json.loads(next(Path(td).glob("*.json")).read_text())
    return to_words(raw, shift)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_transcribe.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add python-scripts/batch-pipeline/transcribe.py python-scripts/batch-pipeline/tests/test_transcribe.py
git commit -m "feat(batch-pipeline): cross-platform Whisper transcribe shim"
```

---

### Task 6: `captions.py` (port caption_render, config-driven)

**Files:**
- Create: `python-scripts/batch-pipeline/captions.py`
- Test: `python-scripts/batch-pipeline/tests/test_captions.py`

**Interfaces:**
- Consumes: `config.CAPTION_STYLE`, `config.font_path`, `config.FPS`, `config.PRORES4444`.
- Produces: `group(words: list[dict]) -> list[(card, s, e)]`; `render(caption_words: Path, ref_video: Path, out_mov: Path) -> Path`.

- [ ] **Step 1: Write the failing test** (grouping + casing/punctuation — no ffmpeg)

```python
# tests/test_captions.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import captions

def test_clean_casing_and_punct():
    assert captions.clean("Money.") == "money"
    assert captions.clean("I'm") == "I'm"
    assert captions.clean("Sai") == "Sai"

def test_group_max_three_words():
    words = [{"start":i*0.3,"end":i*0.3+0.2,"word":f"w{i}"} for i in range(5)]
    cards = captions.group(words)
    assert all(len(c[0]) <= 3 for c in cards)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_captions.py -v`
Expected: FAIL (`ModuleNotFoundError: captions`)

- [ ] **Step 3: Port the module.** Copy the body of `D:/Sai/01_ORGANIZED/Batch_03/Vid_04/_caption_v04.py` to `captions.py` with these changes: read `FONT_PATH` from `config.font_path()`; read style values (font size, margins, colors, max-words, preserve-case, punct) from `config.CAPTION_STYLE`; replace the hardcoded `prores_ks 4444` ffmpeg args with `config.PRORES4444`; expose `clean(word)`, `group(words)`, and `render(caption_words, ref_video, out_mov)` as functions (the existing `clean`/`group`/`render_card`/`main` logic, refactored so `render` takes args instead of module-level paths). Keep all rendering math (`TOP_MARGIN`, shadow blur, overlay-enable timing) identical.

- [ ] **Step 4: Run test to verify it passes**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_captions.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add python-scripts/batch-pipeline/captions.py python-scripts/batch-pipeline/tests/test_captions.py
git commit -m "feat(batch-pipeline): caption stage (alpha .mov, house style from config)"
```

---

### Task 7: `verify.py` (the gate)

**Files:**
- Create: `python-scripts/batch-pipeline/verify.py`
- Test: `python-scripts/batch-pipeline/tests/test_verify.py`

**Interfaces:**
- Consumes: nothing (ffprobe/ffmpeg on PATH).
- Produces: `check_no_clips(lav_wav: Path, cut_plan_synced_outs: list[float]) -> list[dict]` (each `{t, inside, after, ok}`; `ok` = not(inside>700 and after>700)); `decode_clean(path) -> bool`; `same_length(a, b, tol=0.05) -> bool`; `audio_md5(path) -> str`; `gate(...) -> dict` aggregating all with a top-level `passed: bool`.

- [ ] **Step 1: Write the failing test** (no-clip logic against a synthetic lav)

```python
# tests/test_verify.py
import sys, numpy as np
from pathlib import Path
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify

def test_clip_detection(tmp_path):
    sr = 48000; a = np.zeros(int(5*sr), dtype=np.float32)
    rng = np.random.default_rng(0)
    a[int(1.0*sr):int(1.5*sr)] = 0.5*rng.standard_normal(int(0.5*sr))  # word 1.0-1.5
    wav = tmp_path/"lav.wav"; wavfile.write(wav, sr, a)
    # cut-out at 1.25 = mid-word (clip); at 1.80 = silence (clean)
    res = verify.check_no_clips(wav, [1.25, 1.80])
    assert res[0]["ok"] is False and res[1]["ok"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_verify.py -v`
Expected: FAIL (`ModuleNotFoundError: verify`)

- [ ] **Step 3: Write `verify.py`**

```python
import subprocess
import numpy as np
from scipy.io import wavfile

def _rms(a, sr, t, win=0.06):
    s = a[int(t*sr):int((t+win)*sr)]; return float(np.sqrt(np.mean(s**2))) if len(s) else 0.0

def check_no_clips(lav_wav, synced_outs):
    sr, a = wavfile.read(str(lav_wav)); a = a.astype(np.float32)
    out = []
    for t in synced_outs:
        inside, after = _rms(a, sr, t-0.06), _rms(a, sr, t)
        out.append({"t": t, "inside": inside, "after": after,
                    "ok": not (inside > 700 and after > 700)})
    return out

def decode_clean(path):
    r = subprocess.run(["ffmpeg","-v","error","-i",str(path),"-f","null","-"],
                       capture_output=True, text=True)
    return r.returncode == 0 and not r.stderr.strip()

def _dur(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=nk=1:nw=1",str(path)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())

def same_length(a, b, tol=0.05):
    return abs(_dur(a) - _dur(b)) <= tol

def audio_md5(path):
    r = subprocess.run(["ffmpeg","-v","error","-i",str(path),"-map","0:a",
        "-ar","48000","-ac","1","-f","md5","-"], capture_output=True, text=True, check=True)
    return r.stdout.strip()

def gate(a_cut, b_cut, lav_wav, synced_outs):
    clips = check_no_clips(lav_wav, synced_outs)
    res = {"clips": clips, "a_decode": decode_clean(a_cut), "b_decode": decode_clean(b_cut),
           "length_match": same_length(a_cut, b_cut),
           "audio_match": audio_md5(a_cut) == audio_md5(b_cut)}
    res["passed"] = (all(c["ok"] for c in clips) and res["a_decode"] and res["b_decode"]
                     and res["length_match"] and res["audio_match"])
    return res
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_verify.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add python-scripts/batch-pipeline/verify.py python-scripts/batch-pipeline/tests/test_verify.py
git commit -m "feat(batch-pipeline): verification gate (no-clip/decode/length/audio)"
```

---

### Task 8: `package.py` (deliverable layout)

**Files:**
- Create: `python-scripts/batch-pipeline/package.py`
- Test: `python-scripts/batch-pipeline/tests/test_package.py`

**Interfaces:**
- Consumes: `config.library_root`.
- Produces: `deliver(batch_n: int, vid_n: int, title: str, a_cut: Path, b_cut: Path, lav_wav: Path, captions_mov: Path, info: dict) -> Path` — builds `08_AI_EDITS/shorts/Batch_NN/B#_V## - Title/{ANGLES,CAPTIONS}/...`, A/B angles = their cut video + lav audio (stereo), copies captions, writes `_INFO.txt`; returns the package dir. `folder_name(batch_n, vid_n, title) -> str`.

- [ ] **Step 1: Write the failing test** (naming only)

```python
# tests/test_package.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package

def test_folder_name():
    assert package.folder_name(3, 4, "Money Reflects Who You Are") == \
        "B3_V04 - Money Reflects Who You Are"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_package.py -v`
Expected: FAIL (`ModuleNotFoundError: package`)

- [ ] **Step 3: Write `package.py`** (mux lav audio onto each angle; ProRes video copied through)

```python
import shutil, subprocess
from pathlib import Path
import config

def folder_name(batch_n, vid_n, title):
    return f"B{batch_n}_V{vid_n:02d} - {title}"

def _angle(cut_video, lav_wav, dst):
    subprocess.run(["ffmpeg","-y","-i",str(cut_video),"-i",str(lav_wav),
        "-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","256k",
        "-ar","48000","-ac","2","-shortest","-movflags","+faststart",str(dst)],
        check=True, capture_output=True)

def deliver(batch_n, vid_n, title, a_cut, b_cut, lav_wav, captions_mov, info, out_root=None):
    root = out_root or (config.library_root()/"08_AI_EDITS"/"shorts")
    pkg = root/f"Batch_{batch_n:02d}"/folder_name(batch_n, vid_n, title)
    (pkg/"ANGLES").mkdir(parents=True, exist_ok=True); (pkg/"CAPTIONS").mkdir(exist_ok=True)
    tag = f"B{batch_n}_V{vid_n:02d}"
    _angle(a_cut, lav_wav, pkg/"ANGLES"/f"{tag}_A-cam.mov")
    _angle(b_cut, lav_wav, pkg/"ANGLES"/f"{tag}_B-cam.mov")
    shutil.copy2(captions_mov, pkg/"CAPTIONS"/f"{tag}_captions.mov")
    (pkg/"_INFO.txt").write_text(info["text"], encoding="utf-8")
    return pkg
```

> Note: `a_cut`/`b_cut` already carry lav audio from `cut.py` (both extracted from `lav_wav`); re-muxing here is a belt-and-suspenders guarantee both angles are byte-identical audio for the gate's MD5 check.

- [ ] **Step 4: Run test to verify it passes**

Run: `py -m pytest python-scripts/batch-pipeline/tests/test_package.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add python-scripts/batch-pipeline/package.py python-scripts/batch-pipeline/tests/test_package.py
git commit -m "feat(batch-pipeline): deliverable package (ANGLES/CAPTIONS/_INFO)"
```

---

> **Seam notes from the Phase-1 final review (address in this task):**
> - **Flatten transcribe→cut/captions:** `transcribe.to_words` returns nested `{"segments":[{"words":[…]}]}`, but `cut.plan` and `captions.group` consume a FLAT word list. `run.py` must flatten in ONE place: `words = [w for s in t["segments"] for w in s["words"]]` — don't let two callers flatten differently.
> - **Feed the gate cut's own out-points (don't recompute):** `cut.build_cut` now returns `synced_outs` (the snapped cut-out times). Pass THOSE into `verify.gate(..., synced_outs)` — never recompute `snap_out` in `run.py` (that reintroduces drift).
> - **Settle the audio/MD5 contract BEFORE the parity run:** the gate checks `audio_md5(a)==audio_md5(b)`. Cuts carry AAC lav audio on both angles; on V04 today the MD5s matched (ffmpeg AAC is deterministic for identical input), so this likely passes — but confirm empirically on the first real run. If it false-fails, switch the angle audio to PCM (ProRes can hold PCM) or compare each angle against the source-lav MD5 instead of A-vs-B.

### Task 9: `run.py` driver + Batch 3 Vid 4 parity (integration)

**Files:**
- Create: `python-scripts/batch-pipeline/run.py`
- Create: `python-scripts/batch-pipeline/videos/B3_V04.json` (per-video config: sources, lav cam, offset, title, ranges — from today's V04)
- Test: manual integration (real media; documented, not a unit test)

**Interfaces:**
- Consumes: all stage modules.
- Produces: `run_video(cfg: dict, out_root: Path|None=None) -> dict` — sync (or use cfg offset) → extract lav wav → transcribe (or load cfg transcript) → `cut.build_cut` → `captions.render` → `verify.gate` → `package.deliver(..., out_root=out_root)`; returns paths + gate result. CLI: `python run.py --video videos/B3_V04.json [--out-root <dir>]`.

> **Parity-run safety:** B3_V04 already exists as a hand-made deliverable (possibly open in Premiere → overwriting a `.mov` in use fails with EBUSY). The parity run MUST write to a scratch dir via `--out-root`, NOT the live `08_AI_EDITS/shorts/Batch_03/` path. Compare, then (with Gray's OK) re-run without `--out-root` to upgrade the live V04 to ProRes.

- [ ] **Step 1: Write the per-video config** `videos/B3_V04.json` using the values proven today (offset −6.156, lav = B, the 9 ranges from `_cut_v04.py`, title "Money Reflects Who You Are", full sources under `01_ORGANIZED/Batch_03/Vid_04`). Sources referenced as POSIX-relative to library root. May reuse the existing `Synced/Vid_04_B-cam_synced.json` transcript to skip re-transcription.

- [ ] **Step 2: Write `run.py`** wiring the stages in order, reading the JSON, resolving paths against `config.library_root()`, extracting the lav wav with ffmpeg, calling each stage, printing the gate result and package path, threading `out_root` through to `package.deliver`. (Full wiring — each call uses the exact signatures from Tasks 2–8.)

- [ ] **Step 3: Run it to a SCRATCH dir (do not clobber live V04)**

Run: `py python-scripts/batch-pipeline/run.py --video python-scripts/batch-pipeline/videos/B3_V04.json --out-root "D:/Sai/01_ORGANIZED/Batch_03/Vid_04/_parity"`
Expected: gate `passed: True`; package written under `…/Vid_04/_parity/Batch_03/B3_V04 - Money Reflects Who You Are/`.

- [ ] **Step 4: Parity check vs today's hand-made V04**

Compare the scratch package against the live `08_AI_EDITS/shorts/Batch_03/B3_V04 …`: cut duration within 0.1s, captions alpha valid, audio MD5 equal on both angles, `cut_plan` ranges match `_cut_v04` within 1 frame. The angles will now be **ProRes 422** vs the live H.264 — that codec change is the intended upgrade, not a parity failure. Document the comparison in the commit message.
Expected: matches (ProRes is the intended difference). Then delete the `_parity` scratch dir.

- [ ] **Step 5: Commit**

```bash
git add python-scripts/batch-pipeline/run.py python-scripts/batch-pipeline/videos/B3_V04.json
git commit -m "feat(batch-pipeline): driver + Batch3 Vid4 parity (ProRes422)"
```

---

### Task 10: Cross-platform note, README, retire the old script families (kill the drift)

**Files:**
- Create: `python-scripts/batch-pipeline/README.md` (what it is, env, run command, per-video config schema, the stage list)
- Create: `python-scripts/batch-pipeline/.env.example` (`SAI_LIBRARY_ROOT=`)
- Modify: `workflows/batch3-multicam-short-pipeline.md` (point at the new tool; mark the manual SOP superseded for the mechanical stages)
- Delete: `python-scripts/multicam-mirror/batch3_pipeline/` and the drive scripts `D:/Sai/01_ORGANIZED/_b3_edit/*.py` (only AFTER Task 9 parity passes)

**Interfaces:** none (docs + cleanup).

- [ ] **Step 1: Write `README.md` + `.env.example`** documenting the tool, the env var, the run command, and the per-video JSON schema.

- [ ] **Step 2: Confirm parity is green** (Task 9 passed) before deleting anything. If parity failed, STOP — do not delete the old scripts.

- [ ] **Step 3: Delete the superseded families**

```bash
git rm -r python-scripts/multicam-mirror/batch3_pipeline/
rm -f "/d/Sai/01_ORGANIZED/_b3_edit/"*.py   # drive scripts, not in git
```

- [ ] **Step 4: Update the SOP** `workflows/batch3-multicam-short-pipeline.md` — replace the per-stage script references with `python python-scripts/batch-pipeline/run.py --video <cfg>`, keep the gotchas/audio-rule sections, note Mac+Windows now run the same code.

- [ ] **Step 5: Run the full test suite + commit**

```bash
py -m pytest python-scripts/batch-pipeline/tests/ -v
git add -A && git commit -m "chore(batch-pipeline): docs + retire drift-prone old script families"
```

---

## Self-Review

**Spec coverage:** sync ✓(T2) · clip-guard ✓(T3) · cut/ProRes422 ✓(T4) · transcribe shim ✓(T5) · captions ✓(T6) · verify gate ✓(T7) · package layout ✓(T8) · driver+parity ✓(T9) · cross-platform config ✓(T1) · drift retirement ✓(T10). Deferred to Plan 2 (per spec scope): auto-select, batched review, b-roll cache, audio-clean spike — explicitly out of this plan.

**Placeholder scan:** none — every code step shows code; ported modules name the exact source file + the exact changes.

**Type consistency:** `snap_out(audio, sr, sout, next_word_start)` used identically in T3/T4; `plan`/`build_cut` signatures match T4↔T9; `gate(...)` fields match T7↔T9; `folder_name`/`deliver` match T8↔T9.

**Note:** real-media steps (T9) are integration, not unit tests — flagged as such per the spec's testing section.
