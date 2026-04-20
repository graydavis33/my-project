# Footage Organizer Refinement Plan

**Goal:** Make the Footage Organizer reliable enough that Gray never has to manually re-sort a clip — fix the long-form detection bug from the 1080p switch, redesign categories for zero overlap, and build an eval harness so we can iterate the prompt against a labeled test set until it's a beast.

**Architecture:** Three changes to the existing tool — (1) format detection becomes orientation-only (horizontal vs vertical), (2) categories get rewritten as a larger, mutually-exclusive set with strict definitions, (3) a new `eval.py` script runs the analyzer against a Gray-labeled CSV test set and prints accuracy + a confusion matrix so prompt changes can be measured. Cache is bypassed during eval so prompt edits actually re-run.

**Tech Stack:** Python, Anthropic SDK (Claude Haiku Vision), ffmpeg/ffprobe, CSV (stdlib).

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| [config.py](python-scripts/footage-organizer/config.py) | Modify | Drop 4K constants, rewrite category list, drop `FORMAT_OTHER` |
| [main.py](python-scripts/footage-organizer/main.py) | Modify | Simplify `detect_format()` to orientation-only |
| [analyzer.py](python-scripts/footage-organizer/analyzer.py) | Modify | New prompt with strict definitions + "use miscellaneous when uncertain" rule |
| [eval.py](python-scripts/footage-organizer/eval.py) | Create | Eval harness — runs analyzer against a labeled CSV, reports accuracy + confusion matrix |
| [eval_runs/](python-scripts/footage-organizer/eval_runs/) | Create | Folder for timestamped eval result logs |
| [test-set-template.csv](python-scripts/footage-organizer/test-set-template.csv) | Create | Empty CSV template Gray fills with `filepath,correct_category` |
| [README.md](python-scripts/footage-organizer/README.md) | Modify | Document new categories, eval workflow |
| [CLAUDE.md](python-scripts/footage-organizer/CLAUDE.md) | Modify | Replace `@README.md` stub with the iteration workflow |

---

## Decisions Locked In

- **Format:** `width >= height → long-form`, `height > width → short-form`. `FORMAT_OTHER` is deleted.
- **Folder structure stays:** `02_ORGANIZED/{date}/{long-form|short-form}/{category}/` — unchanged.
- **No `voiceover` category.**
- **17 categories**, mutually exclusive, with hard visual discriminators.
- **`miscellaneous` is the "I'm not sure" bucket.** The prompt explicitly tells the model to use it when two categories could fit. Model never invents a folder.
- **No pytest.** The eval harness IS the test rigor for this tool. Other footage-organizer files don't have unit tests and Gray's CLAUDE.md says "no premature abstractions."
- **No worktree.** Gray's auto-commit hook handles save/push. We work on `main`.

---

## The New Category Set (17)

Designed for visual discriminability from 4 frames. Each category has a primary visual question that separates it from neighbors.

### People — addressing camera
1. **`interview-solo`** — One person, framed and clearly speaking to the camera, static or near-static framing.
2. **`interview-duo`** — Two people in frame, both engaged in on-camera conversation/interview.
3. **`walk-and-talk`** — Subject is moving through space AND speaking to camera (handheld follow, vlog-style).

### People — not addressing camera
4. **`candid-people`** — One or two people in natural activity, not speaking to camera.
5. **`reaction-listening`** — A person reacting, listening, or in over-the-shoulder framing — not the speaker.
6. **`crowd-group`** — Three or more people, group dynamic, audience, gathering, meeting room.

### Details / Objects
7. **`insert-hands`** — Hands are the primary subject (typing, holding, gesturing, working).
8. **`insert-product`** — A product, gear, or piece of equipment is the static subject of the frame.
9. **`insert-food-drink`** — Food, beverages, or dining is the subject.
10. **`insert-detail`** — Extreme close-up of an object, texture, material — not hands, not product, not food.

### Screens / Graphics
11. **`screens-and-text`** — A computer monitor, phone screen, dashboard, or prominent text/signage is the subject.

### Environments
12. **`establishing-exterior`** — Wide exterior shot identifying a location (skyline, building exterior, street view).
13. **`establishing-interior`** — Wide interior shot identifying a venue or room.
14. **`environment-detail`** — Architectural details, textures, ambient interior shots — no person is the focus.

### Movement
15. **`action-sport-fitness`** — Sports, working out, physical activity.
16. **`transit-vehicles`** — Cars, subways, taxis, traffic, transportation as the subject.

### Catch-all
17. **`miscellaneous`** — Cannot confidently place, OR could fit two categories equally — Gray reviews these manually.

---

## Tasks

### Task 1: Fix format detection (1080p long-form bug)

**Files:**
- Modify: [config.py:37-43](python-scripts/footage-organizer/config.py#L37-L43)
- Modify: [main.py:151-159](python-scripts/footage-organizer/main.py#L151-L159)

- [ ] **Step 1: Edit `config.py` — remove 4K constants and `FORMAT_OTHER`**

Replace lines 37–43 of [config.py](python-scripts/footage-organizer/config.py):

```python
# Format detection — orientation only (horizontal=long-form, vertical=short-form)
# As of 2026-04-19: long-form is shot 1080p horizontal, short-form is shot vertical.
# Resolution no longer signals format — only orientation does.
FORMAT_LONG_FORM  = "long-form"   # Horizontal (width >= height)
FORMAT_SHORT_FORM = "short-form"  # Vertical   (height > width)
```

- [ ] **Step 2: Edit `main.py` — simplify `detect_format()`**

Replace lines 151–159 of [main.py](python-scripts/footage-organizer/main.py):

```python
def detect_format(filepath):
    width, height = get_resolution(filepath)
    if height > width:
        fmt = FORMAT_SHORT_FORM
    else:
        fmt = FORMAT_LONG_FORM
    return fmt, width, height
```

- [ ] **Step 3: Remove unused imports in `main.py`**

In [main.py:43-50](python-scripts/footage-organizer/main.py#L43-L50), remove `FORMAT_OTHER, LONGFORM_WIDTH, LONGFORM_HEIGHT` from the config import. Also remove the `FORMAT_OTHER` reference from line 290 — change `for fmt in [FORMAT_LONG_FORM, FORMAT_SHORT_FORM, FORMAT_OTHER]:` to `for fmt in [FORMAT_LONG_FORM, FORMAT_SHORT_FORM]:`.

- [ ] **Step 4: Verify with one synthetic file**

Create a 5-second 1080p test clip (or use any existing 1080p horizontal clip) and run:

```bash
cd python-scripts/footage-organizer
python -c "from main import detect_format; print(detect_format('PATH_TO_1080P_CLIP'))"
```

Expected output: `('long-form', 1920, 1080)` (or similar). If it prints `'other'` or errors, the change didn't take.

- [ ] **Step 5: Commit**

```bash
git add python-scripts/footage-organizer/config.py python-scripts/footage-organizer/main.py
git commit -m "fix(footage-organizer): detect long-form by orientation, not 4K resolution"
```

---

### Task 2: Replace category list with the new 17

**Files:**
- Modify: [config.py:45-60](python-scripts/footage-organizer/config.py#L45-L60)

- [ ] **Step 1: Edit `config.py` — replace `CATEGORIES` block**

Replace lines 45–60 of [config.py](python-scripts/footage-organizer/config.py) with:

```python
# Content categories — used in ORGANIZED/ (dated) and BROLL_LIBRARY/ (global)
# DESIGN PRINCIPLE: every category has a primary visual question that separates
# it from its neighbors. The model is told to fall back to `miscellaneous` whenever
# two categories could equally apply — Gray reviews those manually.
CATEGORIES = [
    # People — addressing camera
    "interview-solo",
    "interview-duo",
    "walk-and-talk",

    # People — not addressing camera
    "candid-people",
    "reaction-listening",
    "crowd-group",

    # Details / Objects
    "insert-hands",
    "insert-product",
    "insert-food-drink",
    "insert-detail",

    # Screens / Graphics
    "screens-and-text",

    # Environments
    "establishing-exterior",
    "establishing-interior",
    "environment-detail",

    # Movement
    "action-sport-fitness",
    "transit-vehicles",

    # Catch-all — model returns this when uncertain or when 2+ categories tie
    "miscellaneous",
]
```

- [ ] **Step 2: Verify nothing else imports the old category names**

Run:

```bash
grep -rn "broll-people\|broll-inserts\|broll-environment\|establishing-shots\|location-shots\|action-shots\|broll-office\|screen-recordings\|duo-shots\|reaction-shots\|product-shots" python-scripts/footage-organizer/
```

Expected: no matches outside of the cache file (`.cache.json`) and old README. If you find a reference in code, update it.

- [ ] **Step 3: Commit**

```bash
git add python-scripts/footage-organizer/config.py
git commit -m "refactor(footage-organizer): replace category list with 17 mutually-exclusive categories"
```

---

### Task 3: Rewrite the analyzer prompt

**Files:**
- Modify: [analyzer.py:17-44](python-scripts/footage-organizer/analyzer.py#L17-L44)

- [ ] **Step 1: Replace the `_PROMPT` block in `analyzer.py`**

Replace lines 17–44 of [analyzer.py](python-scripts/footage-organizer/analyzer.py) with:

```python
_CATEGORY_LIST = "\n".join(f"- {c}" for c in CATEGORIES)

_PROMPT = f"""You are classifying raw footage from a freelance videographer's SD card.
You have 4 frames extracted from a single video clip (at 20%, 40%, 60%, and 80% through the clip).

Your job: pick exactly ONE category from the list below. If two categories could equally apply, you MUST return `miscellaneous` — do not guess. The videographer reviews `miscellaneous` clips manually, so a wrong confident answer is worse than `miscellaneous`.

Categories (return one of these strings exactly):
{_CATEGORY_LIST}

Definitions — pick the category whose PRIMARY VISUAL QUESTION matches the clip:

PEOPLE — addressing camera (subject is engaging the lens):
- interview-solo: ONE person, framed and clearly speaking to camera, static or near-static framing. Talking-head.
- interview-duo: TWO people in frame, both engaged in on-camera conversation or being interviewed together.
- walk-and-talk: Subject is BOTH moving through space AND speaking to camera (handheld follow, vlog-style). Movement is the discriminator vs interview-solo.

PEOPLE — not addressing camera:
- candid-people: One or two people in natural activity, NOT speaking to camera. Working, walking, lifestyle.
- reaction-listening: A person is reacting, listening, or shown over-the-shoulder. They are NOT the active speaker in the frame.
- crowd-group: THREE or more people. Group dynamic, audience, meeting room, gathering.

DETAILS / OBJECTS (close-ups where an object is the subject):
- insert-hands: Hands are the PRIMARY subject — typing, holding, gesturing, working. Face may be absent or out of focus.
- insert-product: A product, piece of gear, or equipment is the static subject of the frame.
- insert-food-drink: Food, beverages, or dining is the subject.
- insert-detail: Extreme close-up of an object, texture, or material that is NOT hands, NOT a product, NOT food.

SCREENS:
- screens-and-text: A computer monitor, phone screen, dashboard, app UI, or prominent text/signage is the subject.

ENVIRONMENTS:
- establishing-exterior: Wide exterior shot that identifies a location — skyline, building, street view. No person is the focus.
- establishing-interior: Wide interior shot of a venue or room. No person is the focus.
- environment-detail: Architectural detail, texture, ambient interior — no person is the focus, not a wide establisher.

MOVEMENT:
- action-sport-fitness: Sports, working out, physical activity is the subject.
- transit-vehicles: Cars, subways, taxis, transportation, or traffic is the subject.

CATCH-ALL:
- miscellaneous: Use this when (a) you cannot confidently classify, or (b) two categories could equally apply, or (c) the clip is too dark/blurry/short to read.

Output rules:
- Reply with ONLY the category name. Nothing else. No punctuation. No explanation.
- Use only the exact strings from the category list above.
- When in doubt: `miscellaneous`. The videographer prefers manual review over a wrong confident answer."""
```

- [ ] **Step 2: Sanity-check the prompt builds**

Run:

```bash
cd python-scripts/footage-organizer
python -c "from analyzer import _PROMPT; print(_PROMPT[:500])"
```

Expected: prints the first 500 chars of the prompt without import errors.

- [ ] **Step 3: Commit**

```bash
git add python-scripts/footage-organizer/analyzer.py
git commit -m "refactor(footage-organizer): rewrite classification prompt with strict definitions and miscellaneous-when-uncertain rule"
```

---

### Task 4: Build the eval harness (`eval.py`)

**Files:**
- Create: [eval.py](python-scripts/footage-organizer/eval.py)
- Create: [eval_runs/.gitkeep](python-scripts/footage-organizer/eval_runs/.gitkeep)
- Create: [test-set-template.csv](python-scripts/footage-organizer/test-set-template.csv)

- [ ] **Step 1: Create the template CSV**

Create [test-set-template.csv](python-scripts/footage-organizer/test-set-template.csv) with exactly this content:

```csv
filepath,correct_category
# Fill this in with absolute paths to clips you've manually labeled.
# Example rows (delete these comment lines and the example rows when you start filling it in):
# /Volumes/Footage/Sai/01_RAW_INCOMING/2026-04-17/C0001.MP4,interview-solo
# /Volumes/Footage/Sai/01_RAW_INCOMING/2026-04-17/C0014.MP4,insert-hands
# /Volumes/Footage/Sai/01_RAW_INCOMING/2026-04-17/C0023.MP4,establishing-exterior
```

- [ ] **Step 2: Create the eval_runs folder placeholder**

Create [eval_runs/.gitkeep](python-scripts/footage-organizer/eval_runs/.gitkeep) as an empty file (just to keep the folder in git):

```bash
touch python-scripts/footage-organizer/eval_runs/.gitkeep
```

- [ ] **Step 3: Create `eval.py`**

Create [eval.py](python-scripts/footage-organizer/eval.py) with this content:

```python
"""
eval.py — measure analyzer accuracy against a hand-labeled test set.

Reads a CSV of (filepath, correct_category) rows, runs the current analyzer
on each clip (BYPASSING the cache), compares predictions to labels, and
prints overall accuracy + a confusion matrix + a list of misses.

Each run is also written to eval_runs/YYYY-MM-DD_HH-MM-SS.txt so we can
track improvement across prompt iterations.

Usage:
  cd python-scripts/footage-organizer
  python eval.py test-set.csv
  python eval.py test-set.csv --label "v3-stricter-interview-prompt"
"""
import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

from config import CATEGORIES
from extractor import ffmpeg_available, get_duration, extract_frames
from analyzer import classify_video


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate analyzer accuracy against a labeled CSV.")
    parser.add_argument("csv_path", help="Path to test-set CSV with columns: filepath, correct_category")
    parser.add_argument("--label", default="", help="Short label for this run (e.g. 'v3-stricter-prompt'). Saved in the log filename.")
    return parser.parse_args()


def load_test_set(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header != ["filepath", "correct_category"]:
            print(f"  Error: CSV header must be exactly: filepath,correct_category")
            print(f"  Got: {header}")
            sys.exit(1)
        for row in reader:
            if not row or row[0].strip().startswith("#"):
                continue
            if len(row) < 2:
                continue
            filepath, correct = row[0].strip(), row[1].strip()
            if not filepath or not correct:
                continue
            rows.append((filepath, correct))
    return rows


def validate_labels(rows):
    bad = [(p, c) for p, c in rows if c not in CATEGORIES]
    if bad:
        print(f"  Error: {len(bad)} row(s) use a label that isn't in CATEGORIES:")
        for p, c in bad[:10]:
            print(f"    {os.path.basename(p)} → '{c}'")
        print(f"  Valid categories: {', '.join(CATEGORIES)}")
        sys.exit(1)


def run_eval(rows):
    predictions = []
    for i, (filepath, correct) in enumerate(rows, 1):
        name = os.path.basename(filepath)
        print(f"  [{i}/{len(rows)}] {name}  (label: {correct})")

        if not os.path.isfile(filepath):
            print(f"         [skip] file not found")
            continue

        try:
            duration = get_duration(filepath)
            frames = extract_frames(filepath, duration)
            predicted = classify_video(frames, name)
        except Exception as e:
            print(f"         [skip] error: {e}")
            continue

        match = "OK " if predicted == correct else "MISS"
        print(f"         {match}  predicted: {predicted}")
        predictions.append((filepath, correct, predicted))
    return predictions


def report(predictions, label):
    total = len(predictions)
    if total == 0:
        print("\n  No predictions made — nothing to report.")
        return None

    correct = sum(1 for _, c, p in predictions if c == p)
    accuracy = correct / total * 100

    confusion = defaultdict(lambda: defaultdict(int))
    for _, c, p in predictions:
        confusion[c][p] += 1

    misses = [(os.path.basename(fp), c, p) for fp, c, p in predictions if c != p]

    lines = []
    lines.append("=" * 64)
    lines.append(f"EVAL RESULTS  {label or '(unlabeled run)'}")
    lines.append("=" * 64)
    lines.append(f"Total clips:    {total}")
    lines.append(f"Correct:        {correct}")
    lines.append(f"Accuracy:       {accuracy:.1f}%")
    lines.append("")
    lines.append("Per-category accuracy (rows = correct label, cols = predicted):")
    lines.append("")

    used_categories = sorted(set([c for _, c, _ in predictions] + [p for _, _, p in predictions]))
    col_w = max(len(c) for c in used_categories) + 2

    header = " " * (col_w + 2) + "  ".join(c[:10].ljust(10) for c in used_categories) + "   total  acc"
    lines.append(header)
    for actual in used_categories:
        row_total = sum(confusion[actual].values())
        if row_total == 0:
            continue
        row_correct = confusion[actual].get(actual, 0)
        row_acc = row_correct / row_total * 100 if row_total else 0
        cells = "  ".join(str(confusion[actual].get(p, 0)).rjust(10) for p in used_categories)
        lines.append(f"{actual.ljust(col_w)}  {cells}   {str(row_total).rjust(5)}  {row_acc:5.1f}%")

    lines.append("")
    if misses:
        lines.append(f"MISSES ({len(misses)}):")
        for name, actual, predicted in misses:
            lines.append(f"  {name}    expected: {actual:<24}  predicted: {predicted}")
    else:
        lines.append("No misses — perfect run.")
    lines.append("")

    text = "\n".join(lines)
    print("\n" + text)
    return text


def save_log(text, label):
    if text is None:
        return
    runs_dir = os.path.join(os.path.dirname(__file__), "eval_runs")
    os.makedirs(runs_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    label_part = f"_{label.replace(' ', '-')}" if label else ""
    out_path = os.path.join(runs_dir, f"{stamp}{label_part}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"  Log saved: {out_path}")


def main():
    args = parse_args()

    if not ffmpeg_available():
        print("  Error: ffmpeg and ffprobe are required.")
        sys.exit(1)

    rows = load_test_set(args.csv_path)
    if not rows:
        print(f"  Error: no usable rows in {args.csv_path}")
        sys.exit(1)

    validate_labels(rows)

    print(f"\n  Running eval on {len(rows)} clip(s)...")
    print(f"  Label: {args.label or '(none)'}")
    print(f"  Cache: BYPASSED (every clip re-analyzed)\n")

    predictions = run_eval(rows)
    text = report(predictions, args.label)
    save_log(text, args.label)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Smoke test the harness with no clips**

Run:

```bash
cd python-scripts/footage-organizer
python eval.py test-set-template.csv
```

Expected: errors out with "no usable rows" because the template only has comment lines. That confirms the CSV parser works.

- [ ] **Step 5: Smoke test with one fake row**

Create a temporary one-row CSV:

```bash
cd python-scripts/footage-organizer
printf "filepath,correct_category\n/tmp/does-not-exist.mp4,interview-solo\n" > /tmp/fake-test.csv
python eval.py /tmp/fake-test.csv --label "smoke-test"
```

Expected: prints `[skip] file not found`, then "No predictions made — nothing to report." That confirms the missing-file path works without crashing.

- [ ] **Step 6: Commit**

```bash
git add python-scripts/footage-organizer/eval.py python-scripts/footage-organizer/test-set-template.csv python-scripts/footage-organizer/eval_runs/.gitkeep
git commit -m "feat(footage-organizer): add eval harness for measuring analyzer accuracy"
```

---

### Task 5: Update README and CLAUDE.md

**Files:**
- Modify: [README.md](python-scripts/footage-organizer/README.md)
- Modify: [CLAUDE.md](python-scripts/footage-organizer/CLAUDE.md)

- [ ] **Step 1: Replace the "Output Categories" section in README.md**

Find the `## Output Categories` section (currently lists ~7 outdated categories) and replace it with:

```markdown
## Output Categories (17)

Mutually exclusive — each clip lands in exactly one. When the model can't choose confidently, it returns `miscellaneous` for manual review.

**People — on camera:** `interview-solo`, `interview-duo`, `walk-and-talk`
**People — off camera:** `candid-people`, `reaction-listening`, `crowd-group`
**Details:** `insert-hands`, `insert-product`, `insert-food-drink`, `insert-detail`
**Screens:** `screens-and-text`
**Environments:** `establishing-exterior`, `establishing-interior`, `environment-detail`
**Movement:** `action-sport-fitness`, `transit-vehicles`
**Catch-all:** `miscellaneous` (manual review)

Format folder is decided by orientation only: horizontal = `long-form`, vertical = `short-form`.
```

- [ ] **Step 2: Add an "Iteration / Eval Loop" section to README.md**

Append at the bottom of [README.md](python-scripts/footage-organizer/README.md):

```markdown
## Iteration / Eval Loop

Goal: get classification reliable enough that nothing gets manually re-sorted.

**1. Build a labeled test set** — pick ~40 representative clips from a real shoot day. For each, write down the correct category. Save as a CSV with two columns:

\```csv
filepath,correct_category
/Volumes/Footage/Sai/01_RAW_INCOMING/2026-04-17/C0001.MP4,interview-solo
/Volumes/Footage/Sai/01_RAW_INCOMING/2026-04-17/C0014.MP4,insert-hands
\```

Use [test-set-template.csv](test-set-template.csv) as a starting point. Save your real test set as `test-set.csv` (gitignored — paths are local).

**2. Run the eval**

\```bash
python eval.py test-set.csv --label "v1-baseline"
\```

Output: overall accuracy, per-category accuracy, confusion matrix, full miss list. Saved to `eval_runs/`.

**3. Iterate the prompt** — open [analyzer.py](analyzer.py), tighten the definitions of the categories that got confused, re-run with a new `--label`. Compare logs in `eval_runs/`.

**4. Stop when you're happy** — accuracy plateau + no surprising misses = ship it.

The cache is bypassed during eval, so prompt edits actually re-run on every clip.
```

- [ ] **Step 3: Add `test-set.csv` and the Mac path to .gitignore**

Check the project root [.gitignore](.gitignore) — if `test-set.csv` isn't already covered, append:

```
# Footage organizer — local test-set has machine-specific paths
python-scripts/footage-organizer/test-set.csv
```

- [ ] **Step 4: Replace the contents of `python-scripts/footage-organizer/CLAUDE.md`**

Currently it's just `@README.md`. Replace it with:

```markdown
# Footage Organizer — Working Notes

This tool is in active iteration. The reliability bar: Gray never has to manually re-sort a clip.

## Current state (2026-04-19)
- Format detection: orientation only (horizontal = long-form, vertical = short-form). 4K/1080p doesn't matter.
- 17 mutually-exclusive categories — see README.
- `miscellaneous` is the "I'm not sure" bucket — model uses it whenever two categories could fit. Gray reviews those manually.
- Eval harness in `eval.py` measures accuracy against a hand-labeled CSV. Logs go to `eval_runs/`.

## When asked to "improve the organizer"
1. Run the latest eval first — never tune blind.
2. Look at the confusion matrix. Find the worst-confused pair.
3. Tighten the prompt definitions for that pair specifically. Don't mass-rewrite.
4. Re-run with a new `--label`. Compare against the previous run.
5. Commit prompt changes incrementally — one tightening per commit.

## When asked to "add a category"
- Adding a category is a last resort. First check whether the missed clips fit `miscellaneous` and just need manual review.
- If you do add one: update `CATEGORIES` in `config.py`, add a strict definition with a primary visual question to the prompt in `analyzer.py`, re-label any test-set clips that are now better described by the new category, re-run the eval.

## Don't
- Don't restore the old 4K-based format detection.
- Don't add a `voiceover` category — Gray explicitly rejected it.
- Don't let the model invent categories or land files in unknown folders. The CATEGORIES list is the contract.
```

- [ ] **Step 5: Commit**

```bash
git add python-scripts/footage-organizer/README.md python-scripts/footage-organizer/CLAUDE.md .gitignore
git commit -m "docs(footage-organizer): document new categories, eval workflow, and iteration rules"
```

---

### Task 6: First real eval run (Gray's manual step on Mac)

This task isn't code — it's the handoff to Gray on the Mac where the footage lives. Document it so the next session knows what to do.

- [ ] **Step 1: Pick a recent Sai shoot day with a representative mix of shot types**

Look in `/Volumes/Footage/Sai/01_RAW_INCOMING/` for a date folder with at least 30–40 clips covering interview, B-roll, inserts, establishers. Avoid days that are 100% one shot type — the eval needs variety to be meaningful.

- [ ] **Step 2: Manually label ~40 clips into `test-set.csv`**

Open the clips in QuickTime/Finder previews. For each, decide which of the 17 categories it belongs to. Write to `python-scripts/footage-organizer/test-set.csv` in the format:

```csv
filepath,correct_category
/Volumes/Footage/Sai/01_RAW_INCOMING/2026-04-17/C0001.MP4,interview-solo
```

Aim for at least 2 examples per category that you expect to encounter on a typical day. If a clip is genuinely ambiguous to YOU, label it `miscellaneous` — that's the model's correct answer for ambiguous cases.

- [ ] **Step 3: Run the baseline eval**

```bash
cd python-scripts/footage-organizer
python eval.py test-set.csv --label "v1-baseline"
```

- [ ] **Step 4: Read the confusion matrix, identify the worst-confused pair, and bring the result back to a Claude session for prompt iteration**

The next iteration cycle starts here — and is intentionally OUT of scope for this plan. Each cycle = read confusion matrix → tighten one prompt definition → re-run → commit. Gray drives the cadence.

---

## Self-Review

**Spec coverage check:**
- ✅ Fix 1080p detection bug — Task 1
- ✅ Keep format split, redefine to orientation-only — Task 1
- ✅ No `voiceover` category — Task 2 (omitted from list); Task 5 CLAUDE.md (explicit "don't")
- ✅ Many specific, non-overlapping categories — Task 2 (17 categories with hard discriminators)
- ✅ `miscellaneous` as the "confused" bucket; model never invents folders — Task 3 (prompt) + Task 5 (CLAUDE.md)
- ✅ Iterative test loop ("running tests over and over") — Task 4 (eval harness) + Task 6 (handoff)

**Placeholder scan:** No "TBD", no "implement later", no "appropriate error handling". Every code block is complete. Test commands have expected output. Categories used in the prompt match the list in `config.py`.

**Type/name consistency:** `CATEGORIES` is the single source of truth. `_PROMPT` in analyzer.py builds the list dynamically via `_CATEGORY_LIST`, so they can't drift. `eval.py` validates labels against `CATEGORIES` at load time.

**One known pre-existing risk** (NOT introduced by this plan): the cache file `.cache.json` will contain old category names from previous runs. Once Task 2 ships, those cached values will fail the `if raw not in CATEGORIES` check in `analyzer.py:69`. The eval harness bypasses the cache, so it's not a problem there. But the main `python main.py` flow may hit cached old labels. **Mitigation:** Gray should manually delete `python-scripts/footage-organizer/.cache.json` once after Task 2 ships. Adding that as a one-line note here so it isn't forgotten — not a separate task because it's a single `rm` and only matters if there's an existing cache file.
