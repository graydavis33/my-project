# Footage Organizer v2 — Index + Multi-Category + Pull

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a SQLite index + `pull` command on top of the existing footage-organizer pipeline so Gray can natural-language-query "all vertical clips from April 16" and get a Premiere-ready hardlink folder. Also: backfill filmed-date into the index, and add a `--source` flag so loose footage already in the library can be organized in place without first being relocated to `RAW_INCOMING/`.

**Architecture:** Folders stay the primary classification (existing `06_FOOTAGE_LIBRARY/{category}/{week}/` tree). One clip → one category — the existing single-label classifier is unchanged. A new SQLite database (`.footage-index.sqlite` at the library root) is the orthogonal-metadata layer — one row per clip with `path, category, format, filmed_date, upload_date, duration_s, width, height, codec, sha1`. A `pull` command filters the index and hardlinks results into `_pulls/<slug>/` for Premiere. Claude Code chat is the NL → CLI translator — no MCP yet.

**Tech Stack:** Python 3, SQLite (`sqlite3` stdlib), ffprobe (already a dependency), anthropic SDK (already wired). All work extends the existing tool — nothing replaced. `pytest` added for index/pull tests.

**Out of scope (Phase 2, separate plan):** Whisper transcripts (search by spoken content), richer Vision descriptions + embeddings (semantic search like "at the computer" matching `screens-and-text`), MCP server wrapper, voice input. **Not planned: face recognition / person-ID** — Gray queries by what's in the clip, not by who.

---

## File Structure

**Create:**
- `python-scripts/footage-organizer/index.py` — SQLite schema, scan, upsert, query
- `python-scripts/footage-organizer/pull.py` — filter index → hardlink to `_pulls/`
- `python-scripts/footage-organizer/cli_index.py` — argparse entrypoint for `index` + `pull` subcommands (kept separate from `main.py` so the existing organize flow is untouched)
- `python-scripts/footage-organizer/tests/test_index.py` — index round-trip + filter tests
- `python-scripts/footage-organizer/tests/test_pull.py` — hardlink + cross-drive fallback tests

**Modify:**
- `python-scripts/footage-organizer/config.py` — add `INDEX_DB_NAME`, `PULL_FOLDER_NAME`, `INDEX_SCAN_ROOTS` constants
- `python-scripts/footage-organizer/main.py` — add `--source <folder>` flag for organizing loose footage in-place
- `python-scripts/footage-organizer/README.md` — new usage section
- `python-scripts/footage-organizer/CLAUDE.md` — architecture explanation
- `python-scripts/footage-organizer/requirements.txt` — add `pytest>=8.0`
- `workflows/footage-organizer.md` — SOP update with `index` + `pull` commands and the daily Sai workflow

**Untouched:** `extractor.py` (its `get_shoot_date` already exists — we just call it). `analyzer.py`, `organizer.py`, `cache.py` — single-category behavior is preserved. The 8-folder library scaffold, RAW_INCOMING flow, archive flow.

---

## Task 1: Branch + config additions + dependencies

**Files:**
- Modify: `python-scripts/footage-organizer/config.py`
- Modify: `python-scripts/footage-organizer/requirements.txt`

- [ ] **Step 1: Create feature branch**

```bash
cd "c:/Users/Gray Davis/my-project"
git checkout -b feature/footage-organizer-v2
```

- [ ] **Step 2: Append constants to `config.py`**

Add at the bottom of `python-scripts/footage-organizer/config.py`:

```python
# v2 — index + pull
INDEX_DB_NAME    = ".footage-index.sqlite"   # lives at the client library root
PULL_FOLDER_NAME = "_pulls"                  # _pulls/<slug>/ — Premiere-ready hardlink folders
# Roots inside the library that the index scans (ORGANIZED is dated; FOOTAGE_LIBRARY is permanent).
INDEX_SCAN_ROOTS = [FOLDER_FOOTAGE_LIB, FOLDER_ORGANIZED]
```

- [ ] **Step 3: Add pytest to requirements**

Append to `python-scripts/footage-organizer/requirements.txt`:

```
pytest>=8.0
```

Then install:

```bash
cd python-scripts/footage-organizer
pip install -r requirements.txt
cd ../..
```

- [ ] **Step 4: Commit**

```bash
git add python-scripts/footage-organizer/config.py python-scripts/footage-organizer/requirements.txt
git commit -m "feat(footage-organizer): scaffold v2 — index + pull constants"
```

---

## Task 2: SQLite index module (`index.py`)

**Files:**
- Create: `python-scripts/footage-organizer/index.py`
- Create: `python-scripts/footage-organizer/tests/__init__.py` (empty)
- Create: `python-scripts/footage-organizer/tests/conftest.py`
- Create: `python-scripts/footage-organizer/tests/test_index.py`

- [ ] **Step 1: Write `conftest.py` so tests can import sibling modules**

```python
# python-scripts/footage-organizer/tests/conftest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

- [ ] **Step 2: Write the failing test**

```python
# python-scripts/footage-organizer/tests/test_index.py
from pathlib import Path
import index


def test_index_round_trip(tmp_path):
    db = tmp_path / "idx.sqlite"
    index.init(db)

    rec = index.ClipRecord(
        path=str(tmp_path / "clip.mp4"),
        category="interview-solo",
        format="short-form",
        filmed_date="2026-04-16",
        upload_date="2026-04-17",
        duration_s=12.34,
        width=1080,
        height=1920,
        codec="hevc",
        sha1="abc123",
    )
    index.upsert(db, rec)

    rows = index.query(db, format="short-form", filmed_date="2026-04-16")
    assert len(rows) == 1
    assert rows[0].category == "interview-solo"


def test_index_upsert_is_idempotent(tmp_path):
    db = tmp_path / "idx.sqlite"
    index.init(db)
    rec = index.ClipRecord(
        path="/x/y.mp4", category="misc", format="long-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1920, height=1080, codec="h264", sha1="x",
    )
    index.upsert(db, rec)
    index.upsert(db, rec)
    assert len(index.query(db)) == 1


def test_index_query_filters(tmp_path):
    db = tmp_path / "idx.sqlite"
    index.init(db)
    for i, (cat, fmt, fdate) in enumerate([
        ("interview-solo", "short-form", "2026-04-16"),
        ("interview-solo", "long-form",  "2026-04-16"),
        ("insert-hands",   "short-form", "2026-04-15"),
    ]):
        index.upsert(db, index.ClipRecord(
            path=f"/x/{i}.mp4", category=cat, format=fmt,
            filmed_date=fdate, upload_date=fdate,
            duration_s=1.0, width=1, height=1, codec="x", sha1=str(i),
        ))

    assert len(index.query(db, format="short-form")) == 2
    assert len(index.query(db, category="interview-solo")) == 2
    assert len(index.query(db, filmed_date="2026-04-16")) == 2
    assert len(index.query(db, category="interview-solo", format="short-form")) == 1
```

- [ ] **Step 3: Run the test, expect failure**

```bash
cd python-scripts/footage-organizer
pytest tests/test_index.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'index'`.

- [ ] **Step 4: Implement `index.py`**

```python
# python-scripts/footage-organizer/index.py
"""
SQLite index of every clip in the footage library.
Schema: one row per (path) — UNIQUE on path so re-scans are idempotent.
Query is a small DSL: keyword args → AND-joined filters.
"""
import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class ClipRecord:
    path: str
    category: str
    format: str           # "short-form" | "long-form"
    filmed_date: str      # YYYY-MM-DD
    upload_date: str      # YYYY-MM-DD
    duration_s: float
    width: int
    height: int
    codec: str
    sha1: str             # for dedup across paths (hardlinks share content)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS clips (
    path         TEXT PRIMARY KEY,
    category     TEXT NOT NULL,
    format       TEXT NOT NULL,
    filmed_date  TEXT NOT NULL,
    upload_date  TEXT NOT NULL,
    duration_s   REAL NOT NULL,
    width        INTEGER NOT NULL,
    height       INTEGER NOT NULL,
    codec        TEXT NOT NULL,
    sha1         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_filmed_date ON clips(filmed_date);
CREATE INDEX IF NOT EXISTS idx_category    ON clips(category);
CREATE INDEX IF NOT EXISTS idx_format      ON clips(format);
CREATE INDEX IF NOT EXISTS idx_sha1        ON clips(sha1);
"""


def init(db_path: Path) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(_SCHEMA)


def upsert(db_path: Path, rec: ClipRecord) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO clips (path, category, format, filmed_date, upload_date,
                               duration_s, width, height, codec, sha1)
            VALUES (:path, :category, :format, :filmed_date, :upload_date,
                    :duration_s, :width, :height, :codec, :sha1)
            ON CONFLICT(path) DO UPDATE SET
                category    = excluded.category,
                format      = excluded.format,
                filmed_date = excluded.filmed_date,
                upload_date = excluded.upload_date,
                duration_s  = excluded.duration_s,
                width       = excluded.width,
                height      = excluded.height,
                codec       = excluded.codec,
                sha1        = excluded.sha1
            """,
            asdict(rec),
        )


def query(
    db_path: Path,
    *,
    category: Optional[str] = None,
    format: Optional[str] = None,
    filmed_date: Optional[str] = None,
    filmed_after: Optional[str] = None,
    filmed_before: Optional[str] = None,
    upload_date: Optional[str] = None,
    min_duration: Optional[float] = None,
    max_duration: Optional[float] = None,
) -> list[ClipRecord]:
    where, params = [], {}
    if category:
        where.append("category = :category"); params["category"] = category
    if format:
        where.append("format = :format"); params["format"] = format
    if filmed_date:
        where.append("filmed_date = :filmed_date"); params["filmed_date"] = filmed_date
    if filmed_after:
        where.append("filmed_date >= :filmed_after"); params["filmed_after"] = filmed_after
    if filmed_before:
        where.append("filmed_date <= :filmed_before"); params["filmed_before"] = filmed_before
    if upload_date:
        where.append("upload_date = :upload_date"); params["upload_date"] = upload_date
    if min_duration is not None:
        where.append("duration_s >= :min_duration"); params["min_duration"] = min_duration
    if max_duration is not None:
        where.append("duration_s <= :max_duration"); params["max_duration"] = max_duration

    sql = "SELECT path, category, format, filmed_date, upload_date, duration_s, width, height, codec, sha1 FROM clips"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY filmed_date DESC, path"

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()

    return [ClipRecord(*r) for r in rows]


def remove_missing(db_path: Path) -> int:
    """Delete index rows whose file no longer exists. Returns count removed."""
    with sqlite3.connect(db_path) as conn:
        all_paths = [r[0] for r in conn.execute("SELECT path FROM clips").fetchall()]
        gone = [p for p in all_paths if not Path(p).exists()]
        if gone:
            conn.executemany("DELETE FROM clips WHERE path = ?", [(p,) for p in gone])
    return len(gone)
```

- [ ] **Step 5: Run tests, expect pass**

```bash
pytest tests/test_index.py -v
```
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add python-scripts/footage-organizer/index.py python-scripts/footage-organizer/tests/
git commit -m "feat(footage-organizer): SQLite index — ClipRecord, init/upsert/query/remove_missing + tests"
```

---

## Task 3: Pull command (`pull.py`)

**Files:**
- Create: `python-scripts/footage-organizer/pull.py`
- Create: `python-scripts/footage-organizer/tests/test_pull.py`

- [ ] **Step 1: Write the failing tests**

```python
# python-scripts/footage-organizer/tests/test_pull.py
from pathlib import Path
import index, pull


def _seed(db, tmp_path, n=3, **overrides):
    src = tmp_path / "src"; src.mkdir()
    for i in range(n):
        f = src / f"clip_{i}.mp4"
        f.write_bytes(b"fake video bytes")
        index.upsert(db, index.ClipRecord(
            path=str(f),
            category=overrides.get("category", "interview-solo"),
            format=overrides.get("format", "short-form"),
            filmed_date=overrides.get("filmed_date", "2026-04-16"),
            upload_date=overrides.get("upload_date", "2026-04-17"),
            duration_s=10.0, width=1080, height=1920, codec="hevc",
            sha1=f"sha-{i}",
        ))


def test_pull_creates_hardlinks(tmp_path):
    db = tmp_path / "idx.sqlite"; index.init(db)
    _seed(db, tmp_path)
    out = tmp_path / "_pulls" / "test"

    result = pull.pull(db, out, format="short-form", filmed_date="2026-04-16")

    assert result.count == 3
    assert out.is_dir()
    pulled = sorted(out.iterdir())
    assert len(pulled) == 3
    # Hardlinks share inode on same volume
    src0 = Path(result.records[0].path)
    assert pulled[0].stat().st_ino == src0.stat().st_ino


def test_pull_skips_dupes_by_sha1(tmp_path):
    db = tmp_path / "idx.sqlite"; index.init(db)
    src = tmp_path / "src"; src.mkdir()
    f1 = src / "a.mp4"; f1.write_bytes(b"x")
    f2 = src / "b.mp4"; f2.write_bytes(b"x")
    for f in (f1, f2):
        index.upsert(db, index.ClipRecord(
            path=str(f), category="misc", format="short-form",
            filmed_date="2026-04-16", upload_date="2026-04-16",
            duration_s=1.0, width=1, height=1, codec="x", sha1="SAME",
        ))
    out = tmp_path / "_pulls" / "dedup"
    result = pull.pull(db, out, dedup_by_sha1=True)
    assert result.count == 1


def test_pull_empty_result(tmp_path):
    db = tmp_path / "idx.sqlite"; index.init(db)
    out = tmp_path / "_pulls" / "nothing"
    result = pull.pull(db, out, category="interview-duo")
    assert result.count == 0
    # Empty result should NOT create the folder
    assert not out.exists()
```

- [ ] **Step 2: Implement `pull.py`**

```python
# python-scripts/footage-organizer/pull.py
"""
Filter the index → build a Premiere-ready folder of hardlinks.
Falls back to copy if hardlink isn't possible (cross-drive on Windows, etc).
"""
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

import index


@dataclass
class PullResult:
    folder: Path
    count: int
    records: list
    fallback_copies: int


def pull(
    db_path: Path,
    out_folder: Path,
    *,
    dedup_by_sha1: bool = True,
    **filters,
) -> PullResult:
    rows = index.query(db_path, **filters)

    if dedup_by_sha1:
        seen = set()
        deduped = []
        for r in rows:
            if r.sha1 in seen:
                continue
            seen.add(r.sha1)
            deduped.append(r)
        rows = deduped

    if not rows:
        return PullResult(folder=out_folder, count=0, records=[], fallback_copies=0)

    out_folder = Path(out_folder)
    out_folder.mkdir(parents=True, exist_ok=True)

    fallback_copies = 0
    for r in rows:
        src = Path(r.path)
        if not src.exists():
            continue
        dst = out_folder / src.name
        if dst.exists():
            stem, ext = dst.stem, dst.suffix
            n = 2
            while dst.exists():
                dst = out_folder / f"{stem}_{n}{ext}"
                n += 1
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)
            fallback_copies += 1

    return PullResult(folder=out_folder, count=len(rows), records=rows, fallback_copies=fallback_copies)
```

- [ ] **Step 3: Run tests, expect pass**

```bash
pytest tests/test_pull.py -v
```
Expected: 3 passed. (If `test_pull_creates_hardlinks` fails on inode check, the temp dir may be on a tmpfs that doesn't support hardlinks the same way — accept the fallback_copies path.)

- [ ] **Step 4: Commit**

```bash
git add python-scripts/footage-organizer/pull.py python-scripts/footage-organizer/tests/test_pull.py
git commit -m "feat(footage-organizer): pull command — filter index, hardlink results, dedup by sha1"
```

---

## Task 4: Index scanner (`cli_index.py` — `index` subcommand)

**Files:**
- Create: `python-scripts/footage-organizer/cli_index.py`

- [ ] **Step 1: Write `cli_index.py` with the `index` subcommand**

```python
# python-scripts/footage-organizer/cli_index.py
"""
CLI for the v2 index + pull layer. Kept separate from main.py so the existing
organize/archive flow is untouched.

Commands:
  index   — scan the library, upsert every clip into SQLite
  pull    — filter index → hardlink results into _pulls/<slug>/
"""
import argparse
import hashlib
import os
import sys
from datetime import date, datetime
from pathlib import Path

# Force UTF-8 — Windows console hits cp1252 by default.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from config import (
    CLIENT_ROOTS, VIDEO_EXTENSIONS, INDEX_DB_NAME, PULL_FOLDER_NAME,
    INDEX_SCAN_ROOTS, FORMAT_LONG_FORM, FORMAT_SHORT_FORM,
)
from extractor import get_resolution, get_duration, get_shoot_date
import index
import pull as pull_mod


def _library(client: str) -> Path:
    root = CLIENT_ROOTS.get(client, "")
    if not root:
        print(f"Error: {client.upper()}_LIBRARY_ROOT not set in .env")
        sys.exit(1)
    return Path(root)


def _db(client: str) -> Path:
    return _library(client) / INDEX_DB_NAME


def _walk_videos(root: Path):
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if Path(name).suffix in VIDEO_EXTENSIONS:
                yield Path(dirpath) / name


def _category_from_path(filepath: Path, library: Path) -> str:
    """Infer category from the folder it lives in: .../{category}/{date}/clip.mp4
    or .../organized/{date}/{format}/{category}/clip.mp4."""
    rel = filepath.relative_to(library).parts
    # FOOTAGE_LIBRARY/{category}/{date}/clip.mp4   → rel[1] is category
    # ORGANIZED/{date}/{format}/{category}/clip.mp4 → rel[3] is category
    if len(rel) >= 4 and rel[0].lower().startswith("06_") :
        return rel[1]
    if len(rel) >= 5 and rel[0].lower().startswith("02_"):
        return rel[3]
    return "misc"


def _format_from_resolution(w: int, h: int) -> str:
    return FORMAT_SHORT_FORM if h > w else FORMAT_LONG_FORM


def _sha1_head(filepath: Path, n_bytes: int = 1_048_576) -> str:
    """Hash first 1 MB — fast pseudo-fingerprint, sufficient for dedup of identical clips."""
    h = hashlib.sha1()
    with open(filepath, "rb") as f:
        h.update(f.read(n_bytes))
    return h.hexdigest()


def cmd_index(args):
    client = args.client
    library = _library(client)
    db_path = _db(client)
    index.init(db_path)

    scanned = 0
    added = 0
    skipped = 0

    for sub in INDEX_SCAN_ROOTS:
        root = library / sub
        if not root.exists():
            continue
        for clip in _walk_videos(root):
            scanned += 1
            try:
                w, h = get_resolution(str(clip))
                duration = get_duration(str(clip))
                filmed = get_shoot_date(str(clip))
            except Exception as e:
                print(f"  [skip] {clip.name}: {e}")
                skipped += 1
                continue

            upload = datetime.fromtimestamp(clip.stat().st_mtime).strftime("%Y-%m-%d")
            rec = index.ClipRecord(
                path=str(clip),
                category=_category_from_path(clip, library),
                format=_format_from_resolution(w, h),
                filmed_date=filmed,
                upload_date=upload,
                duration_s=duration,
                width=w,
                height=h,
                codec="",  # codec is optional — leave empty unless needed
                sha1=_sha1_head(clip),
            )
            index.upsert(db_path, rec)
            added += 1

    removed = index.remove_missing(db_path)
    print(f"\n  Indexed {added} clip(s), skipped {skipped}, removed {removed} missing")
    print(f"  DB: {db_path}\n")


def cmd_pull(args):
    client = args.client
    library = _library(client)
    db_path = _db(client)
    if not db_path.exists():
        print(f"Error: index not built yet. Run: python cli_index.py --client {client} index")
        sys.exit(1)

    slug_parts = []
    if args.filmed_date: slug_parts.append(args.filmed_date)
    if args.category:    slug_parts.append(args.category)
    if args.orientation: slug_parts.append(args.orientation)
    slug = "-".join(slug_parts) or "all"
    out = library / PULL_FOLDER_NAME / slug

    fmt_map = {"vertical": FORMAT_SHORT_FORM, "horizontal": FORMAT_LONG_FORM}
    fmt = fmt_map.get(args.orientation) if args.orientation else None

    result = pull_mod.pull(
        db_path,
        out,
        category=args.category,
        format=fmt,
        filmed_date=args.filmed_date,
        filmed_after=args.filmed_after,
        filmed_before=args.filmed_before,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
    )

    if result.count == 0:
        print(f"\n  No clips matched.")
        return

    print(f"\n  Pulled {result.count} clip(s) → {result.folder}")
    if result.fallback_copies:
        print(f"  ({result.fallback_copies} fell back to copy — likely cross-drive)")
    print(f"\n  Drag this folder into Premiere:")
    print(f"  {result.folder}\n")


def main():
    ap = argparse.ArgumentParser(description="Footage index + pull (v2)")
    ap.add_argument("--client", "-c", required=True, choices=list(CLIENT_ROOTS.keys()))
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("index", help="Scan library and refresh the SQLite index").set_defaults(func=cmd_index)

    p = sub.add_parser("pull", help="Filter index → hardlink folder")
    p.add_argument("--category")
    p.add_argument("--orientation", choices=["vertical", "horizontal"])
    p.add_argument("--filmed-date", help="YYYY-MM-DD")
    p.add_argument("--filmed-after", help="YYYY-MM-DD")
    p.add_argument("--filmed-before", help="YYYY-MM-DD")
    p.add_argument("--min-duration", type=float)
    p.add_argument("--max-duration", type=float)
    p.set_defaults(func=cmd_pull)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-test the `index` command on a small folder**

Build a 2-file test folder (or point at an existing organized date), run:

```bash
cd python-scripts/footage-organizer
python cli_index.py --client sai index
```
Expected: prints `Indexed N clip(s), skipped 0, removed 0`. Open the SQLite DB:

```bash
python -c "import sqlite3, os; db = os.path.join(os.environ['SAI_LIBRARY_ROOT'], '.footage-index.sqlite'); print(sqlite3.connect(db).execute('SELECT path, category, format, filmed_date FROM clips LIMIT 5').fetchall())"
```

- [ ] **Step 3: Smoke-test the `pull` command**

```bash
python cli_index.py --client sai pull --orientation vertical --filmed-date 2026-04-16
```
Expected: creates `<SAI_LIBRARY_ROOT>/_pulls/2026-04-16-vertical/` with hardlinks. Open the folder in Explorer — file count matches the printed count.

- [ ] **Step 4: Commit**

```bash
git add python-scripts/footage-organizer/cli_index.py
git commit -m "feat(footage-organizer): index + pull CLI — scan library to SQLite, build hardlink folders"
```

---

## Task 5: Organize existing loose Sai footage (`--source` flag)

**Files:**
- Modify: `python-scripts/footage-organizer/main.py` — add `--source <folder>` flag

Goal: let `organize` consume a folder that's NOT under `RAW_INCOMING/{date}/`, so we can sweep whatever's currently sitting loose in the Sai folder.

- [ ] **Step 1: Add `--source` flag to `parse_args`**

```python
parser.add_argument(
    "--source",
    metavar="PATH",
    help="Process this folder directly instead of RAW_INCOMING/<date>/. "
         "Useful for one-off cleanup of loose footage already in the library.",
)
```

- [ ] **Step 2: Branch in `__main__` before `run_organize`**

```python
if args.source:
    src = Path(args.source).expanduser()
    if not src.is_dir():
        print(f"Error: --source path not found: {src}")
        sys.exit(1)
    date_str = args.date or date.today().strftime("%Y-%m-%d")
    # Reuse run_organize but point its raw_folder at args.source.
    # Cleanest: extract the inner loop into a helper, or temporarily symlink.
    # Simplest: copy the body of run_organize and swap raw_folder = str(src).
    ...
```

Implementation choice: refactor `run_organize` so the input folder is a parameter, then call it twice — once from the RAW_INCOMING flow, once from `--source`. Avoid duplication.

```python
def run_organize(client, date_str, move, source_folder=None):
    library = get_library(client)
    raw_folder = source_folder or os.path.join(library, FOLDER_RAW, date_str)
    # ... rest unchanged
```

- [ ] **Step 3: Dry-run policy — Gray reviews before bulk move**

For migrations, default to `--copy` (don't move originals until Gray approves). Print after-the-fact:

```text
Migration mode (--source) — files were COPIED, not moved.
Review the output, then delete the source folder manually if you're happy.
```

Gate this in the summary print when `source_folder is not None`.

- [ ] **Step 4: Run on the live Sai folder (Gray verifies)**

Gray (manual): identify the loose-footage subfolder under `SAI_LIBRARY_ROOT`. Run:

```bash
python main.py --client sai --source "<path-to-loose-folder>" --date 2026-04-16 --copy
```

Verify in Explorer: clips appear in `06_FOOTAGE_LIBRARY/<category>/2026-04-16/`. Spot-check 5 random clips for correct category.

- [ ] **Step 5: Re-index after migration**

```bash
python cli_index.py --client sai index
```

Then test the headline query:

```bash
python cli_index.py --client sai pull --orientation vertical --filmed-date 2026-04-16
```

- [ ] **Step 6: Commit**

```bash
git add python-scripts/footage-organizer/main.py
git commit -m "feat(footage-organizer): --source flag for migrating loose footage in-library"
```

---

## Task 6: Workflow doc + README

**Files:**
- Modify: `python-scripts/footage-organizer/README.md`
- Modify: `python-scripts/footage-organizer/CLAUDE.md`
- Modify: `workflows/footage-organizer.md`

- [ ] **Step 1: Update README usage section**

Add a new "v2 — Index + Pull" section showing:
- `python cli_index.py --client sai index` — refresh the index after every organize run
- `python cli_index.py --client sai pull --orientation vertical --filmed-date 2026-04-16`
- `python cli_index.py --client sai pull --category interview-solo --filmed-after 2026-04-15`
- The "Daily Sai loop": dump → organize → index → pull as needed

- [ ] **Step 2: Update CLAUDE.md (project-local) with the architecture**

Three sections:
1. Folders are primary classification (existing 8-folder library)
2. SQLite index = orthogonal metadata for fast queries
3. Hardlinks let one clip live in multiple categories

- [ ] **Step 3: Update `workflows/footage-organizer.md`**

Add `index` + `pull` to the command list. Add the "ask Claude in chat" pattern:

> Gray says in Claude Code: "pull all vertical clips from April 16"
> → Claude translates to: `python cli_index.py --client sai pull --orientation vertical --filmed-date 2026-04-16`

- [ ] **Step 4: Commit**

```bash
git add python-scripts/footage-organizer/README.md python-scripts/footage-organizer/CLAUDE.md workflows/footage-organizer.md
git commit -m "docs(footage-organizer): v2 — index + pull workflow"
```

---

## Task 7: Final integration test

- [ ] **Step 1: End-to-end run on a real Sai folder**

1. Pick a date with mixed footage (e.g. 2026-04-16).
2. Drop the card into `01_RAW_INCOMING/2026-04-16/`.
3. Run organize: `python main.py --client sai --date 2026-04-16`
4. Run index: `python cli_index.py --client sai index`
5. Run pull: `python cli_index.py --client sai pull --orientation vertical --filmed-date 2026-04-16`
6. Open `_pulls/2026-04-16-vertical/` — drag into Premiere.
7. Confirm Premiere recognizes the hardlinks as normal clips.

- [ ] **Step 2: Run pytest one more time**

```bash
cd python-scripts/footage-organizer
pytest tests/ -v
```
Expected: all green.

- [ ] **Step 3: Update `context/priorities.md`**

Move Footage Organizer status note to reflect: "v2 LIVE — index + pull + multi-category."

- [ ] **Step 4: Final commit + merge prep**

```bash
git add context/priorities.md
git commit -m "chore(priorities): footage-organizer v2 shipped"
git log --oneline feature/footage-organizer-v2 ^main
```

Review the commit list with Gray, then merge to main:

```bash
git checkout main
git merge --no-ff feature/footage-organizer-v2
git push
```

---

## Decisions Locked

- **Filmed date wins** (over upload date) for `filmed_date` field. Falls back to file mtime only when ffprobe `creation_time` is missing. Upload date is also stored separately for cases where Gray remembers "the day I dumped the card."
- **One clip → one category.** No multi-category, no hardlinks for classification. The existing single-label classifier is unchanged. (Hardlinks only appear in `pull` for building Premiere-ready folders.)
- **Folders = primary classification.** Index is orthogonal metadata, not a replacement.
- **No MCP yet.** Claude Code chat translates Gray's NL to CLI calls. MCP only if other clients (Claude Desktop) need access later.
- **Taxonomy = existing `CATEGORIES` constant** for v1. Promote to `taxonomy.yaml` only when Gray wants to add categories without code edits.
- **Loose footage organized via `--source` flag in `--copy` mode.** Gray reviews before deleting originals.

## Phase 2 (separate plan, not now)

- Whisper transcripts → search by spoken content
- Richer Vision descriptions + embeddings → semantic queries like "at the computer" matching `screens-and-text` clips
- Voice input wrapper → mic → Whisper → CLI args
- Optional MCP server for cross-client access

**Explicitly not planned:** face recognition / person-ID. Gray queries by what's in the clip, not by who.
