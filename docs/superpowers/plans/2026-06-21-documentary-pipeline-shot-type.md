# Documentary Pipeline + Shot-Type Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the footage organizer a documentary-aware intake that splits a mixed card three ways — Sai talking-to-camera (A-roll) → the episode project folder, reusable b-roll → the library, vertical → parked — using an automatic `talking-head` vs `b-roll` detector.

**Architecture:** A new `shot_type` classification combines a free local audio signal (ffmpeg `silencedetect` → speech ratio) with the existing Opus Vision pass (extended to judge "is the subject addressing the camera?"). A new `intake --documentary --episode NAME` mode runs that classifier per horizontal clip and routes by `shot_type`. Detection is plan-first and reviewable before any file moves — it flags, it doesn't blindly trust.

**Tech Stack:** Python 3.13 stdlib, ffmpeg/ffprobe (already shelled everywhere), Anthropic SDK (Opus 4.8 Vision, already wired in `analyzer.py`), SQLite index, pytest.

## Global Constraints

- Python only; default Vision model `claude-opus-4-8` (cost `$0.015/clip`), Haiku `claude-haiku-4-5` for cheap passes — copied from `config.VISION_TAG_MODEL` / `VISION_TAG_COST_PER_CLIP`.
- **No new pip dependencies.** Speech detection uses ffmpeg `silencedetect` (already a dependency), not a VAD library.
- Force UTF-8 stdout in any script entry (`sys.stdout.reconfigure(encoding="utf-8")`) — Windows cp1252 crashes on arrows/em-dashes.
- SQLite stores POSIX-relative paths; schema changes are **non-destructive** (`ALTER TABLE ADD COLUMN` in `index._migrate`, never a rebuild) so the live ~570-clip DB keeps every row.
- Pure logic (parsers, planners, classifiers) split from ffmpeg/ffprobe/API calls so tests run without a drive, ffmpeg, or paid calls — mirror the existing `orient_fn`/`week_fn` injection pattern in `_intake_plan`.
- Plan-first for any command that moves files: a `_plan` function returns moves and moves nothing; the `cmd_` prints the plan + prompts; an `_execute` performs it; then reindex.
- `D:/Sai` footage drive is NOT in git. Tests use `tmp_path`.

**Routing contract (the whole point of this plan):**
| Clip | Destination |
|---|---|
| horizontal + `talking-head` (A-roll) | `02_ACTIVE_PROJECTS/longform/<week>/<episode>/A-roll/` |
| horizontal + `b-roll` | `05_FOOTAGE_LIBRARY/b-roll/<week>/` (+ Vision-tagged) |
| vertical | `05_FOOTAGE_LIBRARY/vertical/<week>/` (parked, untagged) |
| undetermined orientation | left in source, reported |

Documentary footage is **never** filed into `_BATCHES` — that bucket is only for the 2-cam Q&A short-form shoots.

---

## File Structure

- `extractor.py` — add `speech_ratio()` + pure parser `_speech_ratio_from_silencedetect()`.
- `analyzer.py` — extend `_TAG_PROMPT` + `_coerce_tags` + `tag_video` to also return `addressing_camera` (bool).
- `config.py` — add `SHOT_TYPE_TALKING`, `SHOT_TYPE_BROLL`, `SPEECH_MIN_RATIO`.
- `cli_index.py` — add `classify_shot_type()`, `_documentary_plan()`, `--documentary`/`--episode` flags + branch in `cmd_intake`.
- `index.py` — add `shot_type` column (schema + migrate + `ClipRecord` field + COALESCE upsert + query filter).
- `tagger/server.py` — surface `shot_type` in the dashboard (label + filter).
- `tests/` — `test_speech_ratio.py`, `test_shot_type.py`, `test_documentary_plan.py`, plus additions to `test_tags_schema.py`.
- Docs — `README.md`, `CLAUDE.md` (footage-organizer), decision log, memory.

---

## Phase 1 — Shot-type detection (foundation)

### Task 1: Speech-ratio from ffmpeg silencedetect

**Files:**
- Modify: `python-scripts/footage-organizer/extractor.py`
- Test: `python-scripts/footage-organizer/tests/test_speech_ratio.py`

**Interfaces:**
- Produces: `_speech_ratio_from_silencedetect(stderr: str, duration: float) -> float` (pure), `speech_ratio(filepath: str) -> float` (shells ffmpeg).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_speech_ratio.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extractor import _speech_ratio_from_silencedetect as sr

def test_no_silence_is_all_speech():
    assert sr("", 10.0) == 1.0

def test_one_silence_block_subtracts():
    log = ("[silencedetect @ x] silence_start: 2.0\n"
           "[silencedetect @ x] silence_end: 4.0 | silence_duration: 2.0\n")
    assert sr(log, 10.0) == 0.8  # 2s silent of 10s

def test_trailing_silence_to_end():
    log = "[silencedetect @ x] silence_start: 7.0\n"  # no matching end → silent to 10s
    assert sr(log, 10.0) == 0.7

def test_clamped_and_zero_duration():
    assert sr("", 0.0) == 0.0
    log = ("[silencedetect @ x] silence_start: 0.0\n"
           "[silencedetect @ x] silence_end: 99.0 | silence_duration: 99.0\n")
    assert sr(log, 10.0) == 0.0  # never negative
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_speech_ratio.py -q`
Expected: FAIL with `ImportError: cannot import name '_speech_ratio_from_silencedetect'`

- [ ] **Step 3: Write minimal implementation**

```python
# extractor.py — add near the other helpers
import re

def _speech_ratio_from_silencedetect(stderr: str, duration: float) -> float:
    """Fraction of the clip containing non-silent (speech/sound) audio, parsed
    from ffmpeg silencedetect stderr. Pure + unit-testable."""
    if duration <= 0:
        return 0.0
    silent = 0.0
    starts = [float(m) for m in re.findall(r"silence_start:\s*([0-9.]+)", stderr)]
    durs = [float(m) for m in re.findall(r"silence_duration:\s*([0-9.]+)", stderr)]
    silent += sum(durs)
    if len(starts) > len(durs):  # a silence_start with no matching end → runs to clip end
        silent += max(0.0, duration - starts[-1])
    ratio = 1.0 - (silent / duration)
    return max(0.0, min(1.0, round(ratio, 4)))


def speech_ratio(filepath: str, noise_db: int = 30, min_silence_s: float = 0.5) -> float:
    """Run ffmpeg silencedetect on a clip → fraction of it that has speech/sound."""
    duration = get_duration(filepath)
    proc = subprocess.run(
        ["ffmpeg", "-i", filepath, "-af",
         f"silencedetect=noise=-{noise_db}dB:d={min_silence_s}", "-f", "null", "-"],
        capture_output=True, text=True, timeout=120)
    return _speech_ratio_from_silencedetect(proc.stderr, duration)
```

Confirm `import subprocess` already exists at the top of `extractor.py` (it does — used by other functions). Add `import re` if missing.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_speech_ratio.py -q`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add python-scripts/footage-organizer/extractor.py python-scripts/footage-organizer/tests/test_speech_ratio.py
git commit -m "feat(footage): speech_ratio via ffmpeg silencedetect"
```

---

### Task 2: Vision judges "addressing the camera"

**Files:**
- Modify: `python-scripts/footage-organizer/analyzer.py:99-160`
- Test: `python-scripts/footage-organizer/tests/test_shot_type.py` (first half)

**Interfaces:**
- Produces: `_coerce_tags(data)` now returns key `addressing_camera: bool`. `tag_video(...)` return dict gains `addressing_camera`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_shot_type.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import analyzer

def test_coerce_addressing_camera_true():
    out = analyzer._coerce_tags({"person_present": True, "addressing_camera": True,
                                 "location": "office", "objects": []})
    assert out["addressing_camera"] is True

def test_coerce_addressing_camera_defaults_false():
    out = analyzer._coerce_tags({"person_present": False, "location": "street", "objects": []})
    assert out["addressing_camera"] is False  # missing → False

def test_coerce_addressing_false_when_no_person():
    out = analyzer._coerce_tags({"person_present": False, "addressing_camera": True,
                                 "location": "street", "objects": []})
    assert out["addressing_camera"] is False  # can't address camera with no person
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_shot_type.py -q`
Expected: FAIL with `KeyError: 'addressing_camera'`

- [ ] **Step 3: Write minimal implementation**

In `analyzer.py`, add the key to `_TAG_PROMPT` (after the `person_present` line):

```python
# inside _TAG_PROMPT, add this bullet under the Keys list:
- "addressing_camera" (boolean): true ONLY if a person is looking at and speaking
    directly TO the camera as the clip's clear focus (a talking-head / piece-to-camera).
    false for candid action, b-roll, or someone talking to another person off-lens.
```

And in `_coerce_tags`, add to the returned dict:

```python
    return {
        "person_present": person,
        "addressing_camera": bool(data.get("addressing_camera")) if person else False,
        "emotion": _norm(data.get("emotion")) if person else None,
        "action": _norm(data.get("action")) if person else None,
        "location": _norm(data.get("location")),
        "objects": objs,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_shot_type.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add python-scripts/footage-organizer/analyzer.py python-scripts/footage-organizer/tests/test_shot_type.py
git commit -m "feat(footage): Vision returns addressing_camera"
```

---

### Task 3: Combine signals into shot_type

**Files:**
- Modify: `python-scripts/footage-organizer/config.py`, `python-scripts/footage-organizer/cli_index.py`
- Test: `python-scripts/footage-organizer/tests/test_shot_type.py` (second half)

**Interfaces:**
- Consumes: `speech_ratio` (Task 1), `addressing_camera` (Task 2).
- Produces: `config.SHOT_TYPE_TALKING = "talking-head"`, `config.SHOT_TYPE_BROLL = "b-roll"`, `config.SPEECH_MIN_RATIO = 0.5`; `cli_index.classify_shot_type(speech: float, addressing_camera: bool) -> str`.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_shot_type.py
import importlib
cli = importlib.import_module("cli_index")

def test_talking_head_needs_speech_and_camera():
    assert cli.classify_shot_type(0.8, True) == "talking-head"

def test_low_speech_is_broll_even_facing_camera():
    assert cli.classify_shot_type(0.1, True) == "b-roll"

def test_speech_but_not_addressing_is_broll():
    assert cli.classify_shot_type(0.9, False) == "b-roll"  # ambient/off-lens talk
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_shot_type.py -q`
Expected: FAIL with `AttributeError: module 'cli_index' has no attribute 'classify_shot_type'`

- [ ] **Step 3: Write minimal implementation**

In `config.py`:

```python
SHOT_TYPE_TALKING = "talking-head"
SHOT_TYPE_BROLL   = "b-roll"
SPEECH_MIN_RATIO  = 0.5   # a talking-head must have speech across >= half the clip
```

In `cli_index.py` (import the new constants in the existing `from config import (...)` block: `SHOT_TYPE_TALKING, SHOT_TYPE_BROLL, SPEECH_MIN_RATIO`), then add:

```python
def classify_shot_type(speech: float, addressing_camera: bool) -> str:
    """A clip is a talking-head (A-roll) only when someone is addressing the
    camera AND there's sustained speech; otherwise it's reusable b-roll."""
    if addressing_camera and speech >= SPEECH_MIN_RATIO:
        return SHOT_TYPE_TALKING
    return SHOT_TYPE_BROLL
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_shot_type.py -q`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add python-scripts/footage-organizer/config.py python-scripts/footage-organizer/cli_index.py python-scripts/footage-organizer/tests/test_shot_type.py
git commit -m "feat(footage): classify_shot_type combiner"
```

---

### Task 4: shot_type index column

**Files:**
- Modify: `python-scripts/footage-organizer/index.py`
- Test: `python-scripts/footage-organizer/tests/test_tags_schema.py`

**Interfaces:**
- Produces: `ClipRecord.shot_type: Optional[str] = None`; `query(..., shot_type=None)` filter; COALESCE-preserved on plain reindex.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_tags_schema.py
from index import ClipRecord
import index

def test_shot_type_roundtrip_and_filter(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    def rec(p, st):
        return ClipRecord(path=p, category="b-roll", format="long-form",
                          filmed_date="2026-05-26", upload_date="", duration_s=3.0,
                          width=1920, height=1080, codec="", sha1=p, shot_type=st)
    index.upsert(db, rec("b-roll/W07/A.MP4", "talking-head"))
    index.upsert(db, rec("b-roll/W07/B.MP4", "b-roll"))
    assert index.get(db, "b-roll/W07/A.MP4").shot_type == "talking-head"
    only = index.query(db, shot_type="b-roll")
    assert [r.path for r in only] == ["b-roll/W07/B.MP4"]

def test_shot_type_preserved_by_coalesce_upsert(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    base = dict(path="b-roll/W07/A.MP4", category="b-roll", format="long-form",
                filmed_date="2026-05-26", upload_date="", duration_s=3.0,
                width=1920, height=1080, codec="", sha1="a")
    index.upsert(db, ClipRecord(**base, shot_type="talking-head"))
    index.upsert(db, ClipRecord(**base))  # plain reindex, shot_type=None
    assert index.get(db, "b-roll/W07/A.MP4").shot_type == "talking-head"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_tags_schema.py -q`
Expected: FAIL — `TypeError: ... unexpected keyword argument 'shot_type'`

- [ ] **Step 3: Write minimal implementation**

In `index.py`:
1. Add to `ClipRecord` dataclass (with the other tag fields): `shot_type: Optional[str] = None`.
2. In `_SCHEMA`'s `CREATE TABLE`, add `shot_type TEXT,` alongside `emotion`/`action` columns.
3. In `_migrate`, add the non-destructive ALTER (mirror the batch_num/vid_num pattern):

```python
    for col in ("emotion", "action", "location", "objects", "shot_type"):
        try:
            conn.execute(f"ALTER TABLE clips ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass  # already exists
```

(If the existing `_migrate` already ALTERs the first four, just add `"shot_type"` to that tuple.)

4. In `upsert`, add to the `ON CONFLICT(path) DO UPDATE SET` list: `shot_type=COALESCE(excluded.shot_type, clips.shot_type)`, and add `shot_type` to the INSERT column list + values.
5. In `query`, add a parameter `shot_type: str | None = None` and, when set, append `AND shot_type = ?` to the WHERE clause with the value.
6. In the row→ClipRecord mapping inside `get`/`query`, read the new column.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_tags_schema.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add python-scripts/footage-organizer/index.py python-scripts/footage-organizer/tests/test_tags_schema.py
git commit -m "feat(footage): shot_type index column"
```

---

## Phase 2 — Documentary routing

### Task 5: Three-way documentary plan

**Files:**
- Modify: `python-scripts/footage-organizer/cli_index.py`
- Test: `python-scripts/footage-organizer/tests/test_documentary_plan.py`

**Interfaces:**
- Consumes: `_walk_videos`, `_clip_group`, `_filmed_week`, `classify_shot_type`, folder constants.
- Produces: `_documentary_plan(source, library, default_week, episode, classify_fn=None, orient_fn=None, week_fn=None) -> (moves, counts, by_week, unknown, collisions)` where `moves` is a list of `(src_path, dest_path)` and `counts = {"talking_head":N, "broll":N, "vertical":N}`. `classify_fn(clip_path) -> str` returns a shot_type (injectable so tests need no ffmpeg/API).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_documentary_plan.py
import os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cli_index as cli

def _touch(p):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b"x")

def test_three_way_split(tmp_path):
    lib = tmp_path / "Sai"
    src = lib / "01_ORGANIZED" / "_INBOX" / "2026-05-26"
    for n in ("A.MP4", "B.MP4", "V.MP4"):
        _touch(src / n)
    orient = lambda p: ("vertical", True) if p.name == "V.MP4" else ("horizontal", False)
    classify = lambda p: "talking-head" if p.name == "A.MP4" else "b-roll"
    week = lambda p: "W07_May-25-31"
    moves, counts, by_week, unknown, coll = cli._documentary_plan(
        src, lib, "W07_May-25-31", "Systems Over Stress",
        classify_fn=classify, orient_fn=orient, week_fn=week)
    dests = {s.name: d.as_posix() for s, d in moves}
    assert "02_ACTIVE_PROJECTS/longform/W07_May-25-31/Systems Over Stress/A-roll/A.MP4" in dests["A.MP4"]
    assert "05_FOOTAGE_LIBRARY/b-roll/W07_May-25-31/B.MP4" in dests["B.MP4"]
    assert "05_FOOTAGE_LIBRARY/vertical/W07_May-25-31/V.MP4" in dests["V.MP4"]
    assert counts == {"talking_head": 1, "broll": 1, "vertical": 1}

def test_undetermined_orientation_left_in_source(tmp_path):
    lib = tmp_path / "Sai"; src = lib / "in"; _touch(src / "X.MP4")
    moves, counts, by_week, unknown, coll = cli._documentary_plan(
        src, lib, "W07", "Ep",
        classify_fn=lambda p: "b-roll",
        orient_fn=lambda p: (None, False), week_fn=lambda p: "W07")
    assert moves == [] and unknown == ["X.MP4"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_documentary_plan.py -q`
Expected: FAIL — `AttributeError: module 'cli_index' has no attribute '_documentary_plan'`

- [ ] **Step 3: Write minimal implementation**

Add to `cli_index.py` (adapt the `_intake_plan` shape; classify only horizontal clips):

```python
def _documentary_plan(source, library, default_week, episode,
                      classify_fn=None, orient_fn=None, week_fn=None):
    """Split a documentary card 3 ways: talking-head→project A-roll,
    b-roll→library, vertical→parked. Returns (moves, counts, by_week,
    unknown, collisions). classify_fn(clip)->shot_type is injected in tests."""
    orient_fn = orient_fn or (lambda p: get_display_orientation(str(p)))
    week_fn = week_fn or _filmed_week
    classify_fn = classify_fn or (lambda p: classify_shot_type(
        speech_ratio(str(p)), False))
    moves, unknown, collisions = [], [], []
    counts = {"talking_head": 0, "broll": 0, "vertical": 0}
    by_week, seen, processed = {}, set(), set()

    for clip in _walk_videos(source):
        if clip in processed:
            continue
        group = _clip_group(clip)
        for f in group:
            processed.add(f)
        orientation, _flip = orient_fn(clip)
        week = week_fn(clip) or default_week
        if orientation == "vertical":
            dest_dir = library / FOLDER_FOOTAGE_LIB / FOLDER_VERTICAL / week
            key = "vertical"
        elif orientation == "horizontal":
            if classify_fn(clip) == SHOT_TYPE_TALKING:
                dest_dir = library / FOLDER_PROJECTS / "longform" / week / episode / "A-roll"
                key = "talking_head"
            else:
                dest_dir = library / FOLDER_FOOTAGE_LIB / FOLDER_BROLL / week
                key = "broll"
        else:
            unknown.append(clip.relative_to(source).as_posix() if source in clip.parents else clip.name)
            continue
        for f in group:
            dest = dest_dir / f.name
            if dest.exists() or dest.as_posix() in seen:
                collisions.append((f.name, dest.relative_to(library).as_posix()))
                continue
            seen.add(dest.as_posix())
            moves.append((f, dest))
        counts[key] += 1
        by_week.setdefault(week, {"talking_head": 0, "broll": 0, "vertical": 0})[key] += 1
    return moves, counts, by_week, unknown, collisions
```

Import `speech_ratio` from `extractor` in the existing extractor import block.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_documentary_plan.py -q`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add python-scripts/footage-organizer/cli_index.py python-scripts/footage-organizer/tests/test_documentary_plan.py
git commit -m "feat(footage): _documentary_plan three-way split"
```

---

### Task 6: Wire `intake --documentary --episode`

**Files:**
- Modify: `python-scripts/footage-organizer/cli_index.py` (`cmd_intake` + the `intake` subparser)
- Test: manual (live command; the plan logic is covered by Task 5)

**Interfaces:**
- Consumes: `_documentary_plan`, `tag_video`, `speech_ratio`, `_execute_consolidation`, `_reindex`, `_run_tagging`.

- [ ] **Step 1: Add the flags to the intake subparser**

```python
    ik.add_argument("--documentary", action="store_true",
                    help="Split a documentary card: talking-head→project A-roll, b-roll→library, vertical→parked")
    ik.add_argument("--episode", help="Episode name (required with --documentary) — the A-roll project folder")
```

- [ ] **Step 2: Branch in `cmd_intake`**

At the top of `cmd_intake`, after `source` is resolved and validated, add:

```python
    if args.documentary:
        if not args.episode:
            print("Error: --documentary requires --episode \"Name\"")
            sys.exit(1)
        return _cmd_intake_documentary(args, client, library, source)
```

Then add the documentary handler. It Vision-tags each horizontal clip ONCE (the call yields both the shot_type signal and the b-roll tags, so no second pass), routes by shot_type, writes tags for clips that landed in b-roll, and reindexes:

```python
def _cmd_intake_documentary(args, client, library, source):
    import analyzer
    from cache import get_cached_tags, store_cached_tags
    default_week = (week_label_for(date.fromisoformat(args.date))
                    if args.date else current_week_label())

    # classify each horizontal clip with ONE Vision call (+ free speech check),
    # caching the tag dict so the later b-roll tag write is free.
    tag_cache = {}
    def classify(clip):
        orientation, _ = get_display_orientation(str(clip))
        if orientation != "horizontal":
            return SHOT_TYPE_BROLL
        abspath = str(clip)
        tags = get_cached_tags(abspath)
        if tags is None:
            dur = get_duration(abspath)
            frames = extract_frames(abspath, dur)
            tags = analyzer.tag_video(frames, clip.name, args.tag_model)
            store_cached_tags(abspath, tags)
        tag_cache[clip.name] = tags
        return classify_shot_type(speech_ratio(abspath), tags.get("addressing_camera", False))

    moves, counts, by_week, unknown, collisions = _documentary_plan(
        source, library, default_week, args.episode, classify_fn=classify)

    print(f"\n  Documentary intake ← {source}  ({client.upper()})  episode: {args.episode}")
    print(f"  Talking-head → project A-roll: {counts['talking_head']}    "
          f"B-roll → library: {counts['broll']}    Vertical → parked: {counts['vertical']}")
    if unknown:
        print(f"  ! {len(unknown)} undetermined-orientation clip(s) LEFT in source:")
        for p in unknown[:20]:
            print(f"      {p}")
    if collisions:
        print(f"  ! {len(collisions)} collision(s) SKIPPED:")
        for name, dest in collisions[:20]:
            print(f"      {name} -> {dest}")
    if not moves:
        print("\n  Nothing to route.\n"); return
    if not args.yes and input("\n  Route these clips? [y/N]: ").strip().lower() != "y":
        print("  Aborted — nothing moved.\n"); return

    moved = _execute_consolidation(moves)
    if source.is_dir() and not any(source.iterdir()):
        source.rmdir()
    db_path = _db(client)
    added, skipped, removed = _reindex(library, db_path)
    print(f"\n  Moved {moved} file(s). Re-indexed: {added}, skipped {skipped}, removed {removed} missing")

    # write the cached Vision tags onto the clips that landed in b-roll
    tagged = 0
    for c in index.query(db_path, category=FOLDER_BROLL):
        tags = tag_cache.get(Path(c.path).name)
        if tags and _is_untagged(c):
            _apply_tags_to_record(c, tags)
            c.shot_type = SHOT_TYPE_BROLL
            index.upsert(db_path, c)
            tagged += 1
    print(f"  Tagged {tagged} new b-roll clip(s). Episode A-roll → "
          f"{FOLDER_PROJECTS}/longform/<week>/{args.episode}/A-roll/")
    print(f"  DB: {db_path}\n")
```

- [ ] **Step 3: Syntax-check + run the full suite**

Run: `python -c "import ast; ast.parse(open('cli_index.py',encoding='utf-8').read()); print('ok')" && python -m pytest tests/ -q`
Expected: `ok` then all tests pass.

- [ ] **Step 4: Live smoke test (small real card)**

Point it at a small mixed folder on `D:/Sai` (or a hand-made test folder with 1 talking clip + 1 b-roll + 1 vertical). Run WITHOUT `--yes` to preview the plan, abort, eyeball the split, then re-run with `--yes`.

Run: `python cli_index.py --client sai intake --from "<test folder>" --documentary --episode "Test Ep"`
Expected: 3-way split printed; A-roll lands in `02_ACTIVE_PROJECTS/longform/<week>/Test Ep/A-roll/`, b-roll in the library + tagged, vertical parked.

- [ ] **Step 5: Commit**

```bash
git add python-scripts/footage-organizer/cli_index.py
git commit -m "feat(footage): intake --documentary --episode three-way routing"
```

---

### Task 7: Dashboard + docs

**Files:**
- Modify: `python-scripts/footage-organizer/tagger/server.py`, `README.md`, `CLAUDE.md`
- Test: manual (dashboard render)

- [ ] **Step 1: Surface shot_type in the dashboard**

In `tagger/server.py` `_clip_dict`, add `"shot_type": r.shot_type or ""` to the returned dict. In the card HTML (`render()`), show a small badge when `c.shot_type==='talking-head'` (e.g. an amber "🎙 talking-head" pill) so a mis-detected A-roll clip sitting in b-roll is obvious at a glance and can be reclassified with the existing "mark vertical"/delete controls. Optionally add a top-bar filter button "show talking-heads only" that filters `CLIPS`.

- [ ] **Step 2: Update README**

In `python-scripts/footage-organizer/README.md`, under the intake section, document `--documentary --episode`: the 3-way routing table, that talking-head = addressing-camera + sustained speech, that it's plan-first and reviewable, and that documentary footage never goes to `_BATCHES`.

- [ ] **Step 3: Update CLAUDE.md**

In `python-scripts/footage-organizer/CLAUDE.md`, add a short "Documentary intake" subsection to the v4 notes: the shot_type signals (speech_ratio + addressing_camera), the routing contract, and the rule that the b-roll from a documentary is reusable library footage (not a batch).

- [ ] **Step 4: Commit**

```bash
git add python-scripts/footage-organizer/tagger/server.py python-scripts/footage-organizer/README.md python-scripts/footage-organizer/CLAUDE.md
git commit -m "docs(footage): documentary pipeline + shot_type in dashboard"
```

- [ ] **Step 5: Update decision log + memory**

Append to `decisions/log.md` and update memory `project_footage_v4_broll_tags.md` (+ MEMORY.md pointer if needed): documentary intake splits 3 ways via shot_type; talking-head A-roll → episode project, b-roll → library, never `_BATCHES`.

```bash
git add decisions/log.md
git commit -m "docs: log documentary pipeline decision"
```

---

## Self-Review

**1. Spec coverage:**
- Interviews/episodes = projects → Task 5/6 route A-roll into `02_ACTIVE_PROJECTS/longform/<week>/<episode>/`. ✅
- B-roll from a documentary → library, NOT `_BATCHES` → Task 5 routes b-roll to `05_FOOTAGE_LIBRARY/b-roll/<week>`; `_BATCHES` is never a destination. ✅
- Build shot_type / talking-head detection → Tasks 1–3 (speech + Vision + combiner), Task 4 stores it. ✅
- Distinguish Sai-talking from b-roll automatically → `classify_shot_type` + `--documentary`. ✅
- Reviewable (detection isn't perfect) → plan-first preview (Task 6 Step 4) + dashboard badge (Task 7). ✅

**2. Placeholder scan:** No TBD/TODO; every code step has concrete code. The only "optional" is the dashboard filter button (Task 7 Step 1) — explicitly optional, core badge is concrete.

**3. Type consistency:** `shot_type` is `str` everywhere; `classify_shot_type(speech: float, addressing_camera: bool) -> str` matches its call in Task 6; `_documentary_plan` returns the 5-tuple consumed in Task 6; `counts` keys `talking_head`/`broll`/`vertical` are consistent between Task 5 impl and Task 6 print. `addressing_camera` bool flows analyzer→classify unchanged.

## Open decision for Gray (confirm before execution)

- **A-roll destination:** I chose `02_ACTIVE_PROJECTS/longform/<week>/<episode>/A-roll/` and require `--episode "Name"`. Alternative: a generic holding folder if you'd rather name the episode later. Confirm the path + the required episode name.
- **Single-cam assumption:** this splits ONE card. For 2-cam documentary interviews, run it per card; A/B sync stays with the existing `multicam-mirror` step after the A-roll is filed. Flag if you want 2-cam handled inside this command instead.
