# Documentary Episode Finalize (`ship --episode`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One finalize command — `ship --episode "Name"` — that, after a documentary episode is delivered, moves ALL of its footage (A-roll talking + b-roll alike) from `01_ORGANIZED` into the reusable b-roll library, auto-tags the new b-roll, parks the verticals, and archives the Premiere project.

**Architecture:** A new `--episode` mode on the existing `ship` command, reusing the established plan-first move machinery and the tagging helper shipped earlier today. **Gray organizes the episode's footage by hand** in a folder named for the episode directly under `01_ORGANIZED` (e.g. `01_ORGANIZED/ep2 doc/2026-05-25/...`), with day subfolders inside — no intake command, `_INBOX` stays batch-only. `02_ACTIVE_PROJECTS` holds ONLY the Premiere project, never raw footage. `ship --episode` is the single explicit step that converges everything into the library when the episode is done. **No A-roll/B-roll distinction, no shot-type detection** — both become reusable library footage at the end.

**Tech Stack:** Python 3.13 stdlib, ffmpeg/ffprobe (orientation + filmed-week), Anthropic SDK (Opus Vision tagging, already wired), SQLite index, pytest.

## Global Constraints

- Python only; default Vision model `claude-opus-4-8` ($0.015/clip), Haiku `claude-haiku-4-5` cheap (`config.VISION_TAG_MODEL` / `VISION_TAG_COST_PER_CLIP`).
- No new pip dependencies; no schema changes.
- Force UTF-8 stdout in any entry script.
- SQLite stores POSIX-relative paths.
- Pure planner split from ffmpeg/ffprobe/API (inject `orient_fn`/`week_fn`) so tests run without a drive or paid calls — mirror `_intake_plan`/`_ship_plan`.
- Plan-first: `_episode_ship_plan` returns moves and moves nothing; `cmd` prints the plan + prompts; `_execute_consolidation` performs it; then reindex.
- Paid Vision run prompts unless `--yes`.
- `D:/Sai` is NOT in git. Tests use `tmp_path`.

**The lifecycle (only the last stage is automated here):**
| Stage | Where the footage lives | Tool |
|---|---|---|
| 1. Drop & organize | `01_ORGANIZED/<Episode>/<day>/` (Gray organizes by hand; folder = episode name, day subfolders inside) | manual |
| 2. Edit | `02_ACTIVE_PROJECTS/longform/<week>/<Episode>/` — **Premiere project only, no footage** | Premiere |
| 3. Review / final export | `03_DELIVERED/drafts/` → `03_DELIVERED/longform/<week>/` | existing `promote` |
| **4. Finalize** | **footage → `05_FOOTAGE_LIBRARY/b-roll/<week>` (auto-tagged) + `vertical/<week>` (parked); project → `04_ARCHIVE/longform/<week>/<Episode>/`** | **`ship --episode` (this plan)** |

Documentary footage is **never** filed into `_BATCHES` (only the 2-cam Q&A shorts). The batch system is untouched.

---

## File Structure

- `cli_index.py` — add `_episode_ship_plan()`; add `--episode`/`--footage`/`--tag-model` flags + an episode branch in `cmd_ship`.
- `tests/test_episode_ship_plan.py` — new.
- Docs — `README.md`, `CLAUDE.md` (footage-organizer), `decisions/log.md`, memory.

No changes to `config.py`, `index.py`, `analyzer.py`, `extractor.py`, or the dashboard. The default footage location is `01_ORGANIZED/<episode-name>/` — built from existing `FOLDER_ORGANIZED`, no new constant.

---

## Task 1: Episode-ship plan (footage → library + project → archive)

**Files:**
- Modify: `python-scripts/footage-organizer/cli_index.py`
- Test: `python-scripts/footage-organizer/tests/test_episode_ship_plan.py`

**Interfaces:**
- Consumes: `_walk_videos`, `_clip_group`, `_find_stage_item`, `_filmed_week`, `current_week_label`, `get_display_orientation`, folder constants (`FOLDER_ORGANIZED`, `FOLDER_FOOTAGE_LIB`, `FOLDER_BROLL`, `FOLDER_VERTICAL`, `FOLDER_PROJECTS`, `FOLDER_ARCHIVE`).
- Produces: `_episode_ship_plan(library, episode, footage_root=None, orient_fn=None, week_fn=None) -> (moves, warnings)`. `moves` = `[(src, dest)]` covering every footage move PLUS the project-archive move. `warnings` = human-readable strings. `footage_root` defaults to `library/01_ORGANIZED/<episode>/`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_episode_ship_plan.py
import os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cli_index as cli

def _touch(p): p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b"x")

def test_footage_to_library_and_project_archived(tmp_path):
    lib = tmp_path / "Sai"
    epf = lib / "01_ORGANIZED" / "ep2 doc"
    for n in ("A.MP4", "B.MP4", "V.MP4"):
        _touch(epf / "2026-05-26" / n)
    proj = lib / "02_ACTIVE_PROJECTS" / "longform" / "W07_May-25-31" / "ep2 doc"
    _touch(proj / "edit.prproj")
    orient = lambda p: ("vertical", True) if p.name == "V.MP4" else ("horizontal", False)
    week = lambda p: "W07_May-25-31"
    moves, warnings = cli._episode_ship_plan(lib, "ep2 doc", orient_fn=orient, week_fn=week)
    dests = {s.name: d.as_posix() for s, d in moves}
    assert "05_FOOTAGE_LIBRARY/b-roll/W07_May-25-31/A.MP4" in dests["A.MP4"]
    assert "05_FOOTAGE_LIBRARY/b-roll/W07_May-25-31/B.MP4" in dests["B.MP4"]
    assert "05_FOOTAGE_LIBRARY/vertical/W07_May-25-31/V.MP4" in dests["V.MP4"]
    assert any(s.name == "ep2 doc" and "04_ARCHIVE/longform/" in d.as_posix()
               for s, d in moves)
    assert warnings == []

def test_custom_footage_root(tmp_path):
    lib = tmp_path / "Sai"
    custom = lib / "01_ORGANIZED" / "my-doc-week"
    _touch(custom / "A.MP4")
    moves, warnings = cli._episode_ship_plan(
        lib, "Ep", footage_root=custom,
        orient_fn=lambda p: ("horizontal", False), week_fn=lambda p: "W07")
    assert moves[0][1].as_posix().endswith("05_FOOTAGE_LIBRARY/b-roll/W07/A.MP4")

def test_missing_footage_warns_not_crashes(tmp_path):
    lib = tmp_path / "Sai"
    proj = lib / "02_ACTIVE_PROJECTS" / "longform" / "W07" / "Ep"
    _touch(proj / "edit.prproj")
    moves, warnings = cli._episode_ship_plan(
        lib, "Ep", orient_fn=lambda p: ("horizontal", False), week_fn=lambda p: "W07")
    assert any("no footage" in w.lower() for w in warnings)

def test_no_project_warns(tmp_path):
    lib = tmp_path / "Sai"
    _touch(lib / "01_ORGANIZED" / "Ep" / "2026-05-26" / "A.MP4")
    moves, warnings = cli._episode_ship_plan(
        lib, "Ep", orient_fn=lambda p: ("horizontal", False), week_fn=lambda p: "W07")
    assert any("no active project" in w.lower() for w in warnings)
    assert any(s.name == "A.MP4" for s, d in moves)  # footage still planned
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_episode_ship_plan.py -q`
Expected: FAIL — `AttributeError: module 'cli_index' has no attribute '_episode_ship_plan'`

- [ ] **Step 3: Write minimal implementation**

In `cli_index.py`, add:

```python
def _episode_ship_plan(library, episode, footage_root=None, orient_fn=None, week_fn=None):
    """Finalize a delivered documentary episode. Move ALL its footage →
    b-roll/<week> (horizontal) or vertical/<week> (vertical), and archive the
    Premiere project → 04_ARCHIVE/longform/<week>/<episode>/. Returns
    (moves, warnings). footage_root defaults to 01_ORGANIZED/<episode>/."""
    orient_fn = orient_fn or (lambda p: get_display_orientation(str(p)))
    week_fn = week_fn or _filmed_week
    moves, warnings, seen, processed = [], [], set(), set()

    ep_root = Path(footage_root) if footage_root else (
        library / FOLDER_ORGANIZED / episode)
    footage = list(_walk_videos(ep_root)) if ep_root.is_dir() else []
    if not footage:
        warnings.append(f"no footage found under {ep_root}")

    archive_week = None
    for clip in footage:
        if clip in processed:
            continue
        group = _clip_group(clip)
        for f in group:
            processed.add(f)
        orientation, _flip = orient_fn(clip)
        bucket = (FOLDER_BROLL if orientation == "horizontal"
                  else FOLDER_VERTICAL if orientation == "vertical" else None)
        if bucket is None:
            warnings.append(f"undetermined orientation, left in source: {clip.name}")
            continue
        week = week_fn(clip) or current_week_label()
        archive_week = archive_week or week
        dest_dir = library / FOLDER_FOOTAGE_LIB / bucket / week
        for f in group:
            dest = dest_dir / f.name
            if dest.exists() or dest.as_posix() in seen:
                warnings.append(f"collision skipped: {f.name} -> {dest.relative_to(library).as_posix()}")
                continue
            seen.add(dest.as_posix())
            moves.append((f, dest))

    matches = _find_stage_item(library / FOLDER_PROJECTS, episode)
    if not matches:
        warnings.append(f"no active project named '{episode}' to archive")
    elif len(matches) > 1:
        warnings.append(f"multiple projects named '{episode}' — archive by hand: "
                        + ", ".join(str(m) for m in matches))
    else:
        wk = archive_week or current_week_label()
        dest = library / FOLDER_ARCHIVE / "longform" / wk / episode
        if dest.exists():
            warnings.append(f"archive destination already exists: {dest.relative_to(library).as_posix()}")
        else:
            moves.append((matches[0], dest))
    return moves, warnings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_episode_ship_plan.py -q`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add python-scripts/footage-organizer/cli_index.py python-scripts/footage-organizer/tests/test_episode_ship_plan.py
git commit -m "feat(footage): _episode_ship_plan finalize → library + archive"
```

---

## Task 2: Wire `ship --episode "Name"` (with auto-tag)

**Files:**
- Modify: `python-scripts/footage-organizer/cli_index.py` (`cmd_ship` + the `ship` subparser)
- Test: manual (the plan is covered by Task 1)

**Interfaces:**
- Consumes: `_episode_ship_plan`, `_execute_consolidation`, `_prune_empty_dirs`, `_reindex`, `_run_tagging`, `_is_untagged`, `VISION_TAG_COST_PER_CLIP`, `VISION_TAG_MODEL`, `index.query`, `FOLDER_ORGANIZED`, `FOLDER_BROLL`.

- [ ] **Step 1: Add the flags to the ship subparser**

Find the `ship` subparser (the line `<var> = sub.add_parser("ship", ...)`) and add to that `<var>`:

```python
    <var>.add_argument("--episode", help="Finalize a documentary episode: footage → library + auto-tag, project → archive")
    <var>.add_argument("--footage", help="Episode footage folder (default 01_ORGANIZED/<episode>/); relative to library or absolute")
    <var>.add_argument("--tag-model", default=VISION_TAG_MODEL, help=f"Vision model for the auto-tag pass (default {VISION_TAG_MODEL})")
```

(Replace `<var>` with the real subparser variable name in the file.)

- [ ] **Step 2: Branch in `cmd_ship`**

At the very top of `cmd_ship`, before the existing video-based logic:

```python
    if getattr(args, "episode", None):
        return _cmd_ship_episode(args, args.client)
```

Then add the handler:

```python
def _cmd_ship_episode(args, client):
    library = _library(client)
    footage_root = None
    if args.footage:
        footage_root = Path(args.footage)
        if not footage_root.is_absolute():
            footage_root = library / args.footage
    moves, warnings = _episode_ship_plan(library, args.episode, footage_root=footage_root)

    print(f"\n  Finalize episode: {args.episode}  ({client.upper()})")
    print(f"  Plan — {len(moves)} move(s):")
    for s, d in moves[:60]:
        print(f"    {s.name}  ->  {d.relative_to(library).as_posix()}")
    if len(moves) > 60:
        print(f"    … +{len(moves) - 60} more")
    for w in warnings:
        print(f"  ! {w}")
    if not moves:
        print("\n  Nothing to finalize.\n"); return
    if not args.yes and input("\n  Execute this finalize? [y/N]: ").strip().lower() != "y":
        print("  Aborted — nothing moved.\n"); return

    _execute_consolidation(moves)
    ep_root = footage_root or (library / FOLDER_ORGANIZED / args.episode)
    if ep_root.is_dir():
        _prune_empty_dirs(ep_root)
    db_path = _db(client)
    added, skipped, removed = _reindex(library, db_path)
    print(f"\n  Re-indexed: {added}, skipped {skipped}, removed {removed} missing")

    todo = [c for c in index.query(db_path, category=FOLDER_BROLL) if _is_untagged(c)]
    per_clip = VISION_TAG_COST_PER_CLIP.get(args.tag_model, 0.015)
    print(f"  Auto-tag {len(todo)} new b-roll clip(s)  Model: {args.tag_model}  Est. ~${len(todo) * per_clip:.2f}")
    if todo and (args.yes or input("  Proceed with the paid Vision run? [y/N]: ").strip().lower() == "y"):
        tagged, cache_hits, failed = _run_tagging(library, db_path, todo, args.tag_model)
        print(f"  Tagged {tagged} clip(s) ({cache_hits} from cache, {failed} skipped).")
    print(f"  Episode finalized. DB: {db_path}\n")
```

Note: confirm `_prune_empty_dirs` exists and takes a single root Path (it's used by `consolidate-broll`); match its current call convention.

- [ ] **Step 3: Syntax-check + full suite**

Run: `python -c "import ast; ast.parse(open('cli_index.py',encoding='utf-8').read()); print('ok')" && python -m pytest tests/ -q`
Expected: `ok` then all pass.

- [ ] **Step 4: Live smoke test (end-to-end)**

Make `01_ORGANIZED/Test Ep/2026-05-26/` with 2 horizontal + 1 vertical clip, and a dummy project `02_ACTIVE_PROJECTS/longform/W07_May-25-31/Test Ep/`. Run without `--yes` to preview, then with confirm.

Run: `python cli_index.py --client sai ship --episode "Test Ep"`
Expected: preview shows footage→b-roll/vertical + project→archive; on confirm, footage migrates, b-roll auto-tags, project archived, episode folder cleaned up. Clean up the test artifacts afterward.

- [ ] **Step 5: Commit**

```bash
git add python-scripts/footage-organizer/cli_index.py
git commit -m "feat(footage): ship --episode finalize (library + tag + archive)"
```

---

## Task 3: Docs + memory

**Files:**
- Modify: `python-scripts/footage-organizer/README.md`, `python-scripts/footage-organizer/CLAUDE.md`, `decisions/log.md`
- Modify: memory `project_footage_v4_broll_tags.md`

- [ ] **Step 1: README**

Add a "Documentary episodes" section: the 4-stage lifecycle table; that Gray organizes episode footage by hand under `01_ORGANIZED/<episode name>/<day>/` (folder = episode name, day subfolders inside) and `_INBOX` is batch-only; that `02_ACTIVE_PROJECTS` holds only the Premiere project; `ship --episode "Name" [--footage <path>]` migrates ALL footage → library (auto-tagged) + parks verticals + archives the project. State plainly: A-roll and b-roll both become reusable library footage; episode footage stays in `01_ORGANIZED` during the edit so each episode uses only its own timeline; never `_BATCHES`.

- [ ] **Step 2: CLAUDE.md (footage-organizer)**

Add a "Documentary episode finalize" subsection: `ship --episode` behavior, the footage-waits-in-organized rationale, that active projects hold only the Premiere project, and the no-shot-type-detection decision.

- [ ] **Step 3: decision log + commit**

```bash
cat >> ../../decisions/log.md <<'EOF'

## 2026-06-21 — Documentary episode finalize (ship --episode); intake command dropped
- Gray organizes each documentary episode's footage by hand under 01_ORGANIZED/<episode name>/<day>/ (folder = episode name, e.g. "ep2 doc", with date subfolders inside) while editing — _INBOX stays batch-only, no episode-intake command. 02_ACTIVE_PROJECTS holds only the Premiere project, never raw footage. Footage waits in organized so each episode edits from only its own week's timeline (no past-week library b-roll bleeding in).
- `ship --episode "Name" [--footage <path>]` is the single finalize step: after delivery it moves ALL footage (A-roll talking + b-roll) → 05_FOOTAGE_LIBRARY/b-roll/<week> (auto-tagged) + vertical/<week> (parked), and archives the Premiere project → 04_ARCHIVE/longform/<week>/<Name>/. Default footage location 01_ORGANIZED/<episode>/.
- No A-roll/B-roll distinction, no shot-type detector (dropped): both converge into the reusable library at finalize. Documentary footage never goes to _BATCHES; batch system unchanged.
EOF
git add ../../decisions/log.md
git commit -m "docs: log documentary episode finalize"
```

- [ ] **Step 4: memory + commit docs**

Update `project_footage_v4_broll_tags.md` with the episode finalize flow + the command. Commit README + CLAUDE.md:

```bash
git add python-scripts/footage-organizer/README.md python-scripts/footage-organizer/CLAUDE.md
git commit -m "docs(footage): documentary episode finalize pipeline"
```

---

## Self-Review

**1. Spec coverage:**
- Footage folder = just the episode name under `01_ORGANIZED`, day subfolders inside → default `footage_root = 01_ORGANIZED/<episode>/`; tests use `01_ORGANIZED/ep2 doc/<day>/`. ✅
- Active Projects holds only the Premiere project → `ship --episode` archives the project from `02_ACTIVE_PROJECTS`; footage comes from `01_ORGANIZED`, never active. ✅
- Gray organizes by hand; no intake command → no intake task. ✅
- `_INBOX` batch-only → untouched; documented in Task 3. ✅
- `ship` migrates footage to library when done + uploaded → Task 1/2. ✅
- ALL footage (A-roll + b-roll) → library, by week, auto-tagged; verticals parked → Task 1 routes by orientation, Task 2 auto-tags b-roll. ✅
- Project archived → Task 1 adds the archive move. ✅
- Never `_BATCHES`; batch unchanged → no `_BATCHES` destination; batch code untouched. ✅
- Explicit command, no auto-trigger → run by hand. ✅

**2. Placeholder scan:** No TBD/TODO. `<var>` in Task 2 Step 1 is an explicit instruction to substitute the real subparser variable, and the `_prune_empty_dirs` note is a verification step — both reference real code, not unspecified work.

**3. Type consistency:** `_episode_ship_plan(library, episode, footage_root=None, orient_fn=None, week_fn=None) -> (moves, warnings)` matches its call in Task 2; `moves` is `[(Path, Path)]` fed to existing `_execute_consolidation`; `_run_tagging(library, db_path, todo, model)` matches today's shipped signature; default footage path uses existing `FOLDER_ORGANIZED`, no new constant.
