# Footage Organizer — Windows + Mac Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the SQLite footage index portable across Windows and Mac so the same external SSD (`D:/Sai` on Windows, `/Volumes/Footage/Sai` on Mac) works transparently from either machine without re-indexing or breaking the existing Mac workflow.

**Architecture:** Switch the SQLite `clips.path` column from machine-absolute strings (`/Volumes/Footage/Sai/05_FOOTAGE_LIBRARY/...`) to library-relative POSIX strings (`05_FOOTAGE_LIBRARY/...`). Resolve to absolute at read time using the calling machine's `<CLIENT>_LIBRARY_ROOT` env var. Detect legacy absolute-path rows on first run and auto-wipe + rebuild — symmetrical, so works regardless of which OS runs the upgraded code first.

**Tech Stack:** Python 3, `pathlib.Path`, `sqlite3`, `pytest`. No new dependencies.

---

## Critical Safety Property

**Plugging the drive back into Mac after these changes must not break anything.**

The migration is symmetrical:

1. First time the new `cli_index.py` runs on **either** machine: detects the existing DB has absolute paths (Mac-style or Windows-style), drops the `clips` table, re-creates schema, re-indexes from disk (~30 sec for 238 clips, $0).
2. Result: DB now contains only relative paths, fully portable.
3. Subsequent runs on either machine: relative paths resolve via that machine's `library_root` env var. No more wipe needed.

There is no intermediate state where one machine sees a half-migrated DB and the other sees something incompatible — the table either has all-absolute (legacy) or all-relative (post-migration) paths, never both. The cache file (`.cache.json`) is unaffected (its keys are filename + filesize, already portable).

The `pull` command, the `archive` command (in `main.py`), the organize flow, and the cache guardrail all stay functionally identical — they don't read the SQLite directly, only `cli_index.py` and `pull.py` do.

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `python-scripts/footage-organizer/index.py` | Modify | SQLite schema + helpers; now expects relative paths in `ClipRecord.path` |
| `python-scripts/footage-organizer/pull.py` | Modify | Take `library_root` param; resolve `r.path` against it before hardlinking |
| `python-scripts/footage-organizer/cli_index.py` | Modify | Compute `clip.relative_to(library).as_posix()` before upsert; resolve before pull; legacy-DB detection at command entry; AppleDouble filter |
| `python-scripts/footage-organizer/migrate_structure.py` | Delete | Legacy pre-flatten script with hardcoded Mac path; obsolete |
| `python-scripts/footage-organizer/test-set-template.csv` | Modify | Replace `01_RAW_INCOMING` references with `01_ORGANIZED/<date>/` |
| `python-scripts/footage-organizer/main.py` | Modify | Add Windows path example to error message at line 178 |
| `python-scripts/footage-organizer/config.py` | Modify | Add Windows path example to comment at line 21 |
| `python-scripts/footage-organizer/CLAUDE.md` | Modify | Add note about relative-path index in Cross-platform section |
| `python-scripts/footage-organizer/tests/test_index.py` | Modify | Update fixtures to use relative paths; add legacy-detection test |
| `python-scripts/footage-organizer/tests/test_pull.py` | Modify | Update fixtures to use relative paths + library_root param |
| `python-scripts/footage-organizer/tests/test_index_compat.py` | Create | New: cross-machine round-trip + legacy migration tests |
| `workflows/footage-organizer.md` | Modify | Document the relative-path index property |
| `decisions/log.md` | Modify | Append entry: "index stores relative paths for cross-machine compat" |

---

## Task 1: Update `index.py` to relative-path API + add legacy detection

**Files:**
- Modify: `python-scripts/footage-organizer/index.py`
- Test: `python-scripts/footage-organizer/tests/test_index.py`

- [ ] **Step 1: Update `tests/test_index.py` to use relative paths (failing test)**

Replace the file contents with:

```python
from pathlib import Path
import index


def test_index_round_trip(tmp_path):
    db = tmp_path / "idx.sqlite"
    index.init(db)

    rec = index.ClipRecord(
        path="05_FOOTAGE_LIBRARY/interview-solo/W01_Apr-15-19/clip.mp4",
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
    assert rows[0].path == "05_FOOTAGE_LIBRARY/interview-solo/W01_Apr-15-19/clip.mp4"
    assert rows[0].category == "interview-solo"


def test_index_upsert_is_idempotent(tmp_path):
    db = tmp_path / "idx.sqlite"
    index.init(db)
    rec = index.ClipRecord(
        path="05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/y.mp4",
        category="misc", format="long-form",
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
            path=f"05_FOOTAGE_LIBRARY/{cat}/W01_Apr-15-19/{i}.mp4",
            category=cat, format=fmt,
            filmed_date=fdate, upload_date=fdate,
            duration_s=1.0, width=1, height=1, codec="x", sha1=str(i),
        ))

    assert len(index.query(db, format="short-form")) == 2
    assert len(index.query(db, category="interview-solo")) == 2
    assert len(index.query(db, filmed_date="2026-04-16")) == 2
    assert len(index.query(db, category="interview-solo", format="short-form")) == 1


def test_remove_missing_resolves_against_library(tmp_path):
    """remove_missing now takes library_root and joins before checking existence."""
    db = tmp_path / "idx.sqlite"; index.init(db)
    library = tmp_path / "library"
    real_dir = library / "05_FOOTAGE_LIBRARY" / "misc" / "W01_Apr-15-19"
    real_dir.mkdir(parents=True)
    real_file = real_dir / "real.mp4"; real_file.write_bytes(b"x")

    index.upsert(db, index.ClipRecord(
        path="05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/real.mp4",
        category="misc", format="long-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1920, height=1080, codec="h264", sha1="r",
    ))
    index.upsert(db, index.ClipRecord(
        path="05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/ghost.mp4",
        category="misc", format="long-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1920, height=1080, codec="h264", sha1="g",
    ))

    removed = index.remove_missing(db, library_root=library)
    assert removed == 1
    rows = index.query(db)
    assert len(rows) == 1
    assert rows[0].path.endswith("real.mp4")


def test_has_legacy_paths_detects_absolute(tmp_path):
    """has_legacy_paths returns True if any stored path is absolute."""
    db = tmp_path / "idx.sqlite"; index.init(db)
    # Insert one legacy-format absolute path directly (simulating pre-migration DB)
    import sqlite3
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO clips VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("/Volumes/Footage/Sai/05_FOOTAGE_LIBRARY/misc/x.mp4",
             "misc", "long-form", "2026-04-16", "2026-04-16",
             1.0, 1920, 1080, "h264", "abc"),
        )
    assert index.has_legacy_paths(db) is True


def test_has_legacy_paths_false_when_all_relative(tmp_path):
    db = tmp_path / "idx.sqlite"; index.init(db)
    index.upsert(db, index.ClipRecord(
        path="05_FOOTAGE_LIBRARY/misc/x.mp4",
        category="misc", format="long-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1920, height=1080, codec="h264", sha1="abc",
    ))
    assert index.has_legacy_paths(db) is False


def test_has_legacy_paths_false_on_empty_db(tmp_path):
    db = tmp_path / "idx.sqlite"; index.init(db)
    assert index.has_legacy_paths(db) is False


def test_wipe_clips_drops_all_rows(tmp_path):
    db = tmp_path / "idx.sqlite"; index.init(db)
    index.upsert(db, index.ClipRecord(
        path="x.mp4", category="misc", format="long-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1, height=1, codec="x", sha1="x",
    ))
    assert len(index.query(db)) == 1
    index.wipe_clips(db)
    assert len(index.query(db)) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python-scripts/footage-organizer && pytest tests/test_index.py -v`

Expected: FAIL — `has_legacy_paths`, `wipe_clips` not defined; `remove_missing` doesn't accept `library_root` kwarg.

- [ ] **Step 3: Update `index.py` with the new API**

Replace the entire file contents with:

```python
"""
SQLite index of every clip in the footage library.
Schema: one row per (path) — UNIQUE on path so re-scans are idempotent.
Query is a small DSL: keyword args → AND-joined filters.

Path storage: paths are stored RELATIVE to the library root (POSIX style,
forward slashes). Caller is responsible for joining against library_root
when an absolute path is needed (e.g. existence checks, hardlink source).
This makes the DB portable across Mac (`/Volumes/Footage/Sai`) and Windows
(`D:/Sai`) — same physical drive, different mount paths.
"""
import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path, PurePosixPath
from typing import Optional


@dataclass
class ClipRecord:
    path: str             # RELATIVE to library root, POSIX style ("05_FOOTAGE_LIBRARY/...")
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


def remove_missing(db_path: Path, library_root: Path) -> int:
    """Delete index rows whose file no longer exists on disk.
    Resolves each row's relative path against library_root. Returns count removed."""
    library_root = Path(library_root)
    with sqlite3.connect(db_path) as conn:
        all_paths = [r[0] for r in conn.execute("SELECT path FROM clips").fetchall()]
        gone = [p for p in all_paths if not (library_root / p).exists()]
        if gone:
            conn.executemany("DELETE FROM clips WHERE path = ?", [(p,) for p in gone])
    return len(gone)


def has_legacy_paths(db_path: Path) -> bool:
    """True if any row's path is absolute (legacy pre-migration format).
    Detects both POSIX (`/Volumes/...`) and Windows (`D:/...`, `C:\\...`) absolutes."""
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT path FROM clips LIMIT 50").fetchall()
    for (p,) in rows:
        # PurePosixPath("/Volumes/...").is_absolute() -> True
        # PurePosixPath("D:/Sai/...").is_absolute() -> False, but contains ":"
        # PurePosixPath("C:\\...").is_absolute() -> False, but contains ":"
        if PurePosixPath(p).is_absolute() or ":" in p or "\\" in p:
            return True
    return False


def wipe_clips(db_path: Path) -> None:
    """Drop all rows from the clips table. Schema and indexes are preserved."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM clips")
```

- [ ] **Step 4: Run tests to verify all pass**

Run: `cd python-scripts/footage-organizer && pytest tests/test_index.py -v`

Expected: PASS — all 8 tests green.

- [ ] **Step 5: Commit**

```bash
git add python-scripts/footage-organizer/index.py python-scripts/footage-organizer/tests/test_index.py
git commit -m "feat(footage-organizer): index stores relative paths for cross-machine compat

ClipRecord.path now relative to library root (POSIX-style). remove_missing
takes library_root arg. New helpers: has_legacy_paths() detects pre-migration
absolute paths, wipe_clips() drops rows without dropping schema."
```

---

## Task 2: Update `pull.py` to resolve relative paths via library_root

**Files:**
- Modify: `python-scripts/footage-organizer/pull.py`
- Test: `python-scripts/footage-organizer/tests/test_pull.py`

- [ ] **Step 1: Update `tests/test_pull.py` to use relative paths + library_root (failing tests)**

Replace the file contents with:

```python
from pathlib import Path
import index, pull


def _seed(db, library, n=3, **overrides):
    """Seed n clips at <library>/05_FOOTAGE_LIBRARY/<category>/W01_Apr-15-19/clip_*.mp4
    and insert matching index rows with RELATIVE paths."""
    cat = overrides.get("category", "interview-solo")
    week = "W01_Apr-15-19"
    src_dir = library / "05_FOOTAGE_LIBRARY" / cat / week
    src_dir.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        rel = f"05_FOOTAGE_LIBRARY/{cat}/{week}/clip_{i}.mp4"
        f = library / rel
        f.write_bytes(b"fake video bytes")
        index.upsert(db, index.ClipRecord(
            path=rel,
            category=cat,
            format=overrides.get("format", "short-form"),
            filmed_date=overrides.get("filmed_date", "2026-04-16"),
            upload_date=overrides.get("upload_date", "2026-04-17"),
            duration_s=10.0, width=1080, height=1920, codec="hevc",
            sha1=f"sha-{i}",
        ))


def test_pull_creates_hardlinks(tmp_path):
    library = tmp_path / "library"; library.mkdir()
    db = library / "idx.sqlite"; index.init(db)
    _seed(db, library)
    out = library / "07_QUERY_PULLS" / "test"

    result = pull.pull(db, out, library_root=library, format="short-form", filmed_date="2026-04-16")

    assert result.count == 3
    assert out.is_dir()
    pulled = sorted(out.iterdir())
    assert len(pulled) == 3
    # Hardlinks share inode on same volume
    src0 = library / result.records[0].path
    assert pulled[0].stat().st_ino == src0.stat().st_ino


def test_pull_skips_dupes_by_sha1(tmp_path):
    library = tmp_path / "library"; library.mkdir()
    db = library / "idx.sqlite"; index.init(db)
    src_dir = library / "05_FOOTAGE_LIBRARY" / "misc" / "W01_Apr-15-19"
    src_dir.mkdir(parents=True)
    for name in ("a.mp4", "b.mp4"):
        rel = f"05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/{name}"
        (library / rel).write_bytes(b"x")
        index.upsert(db, index.ClipRecord(
            path=rel, category="misc", format="short-form",
            filmed_date="2026-04-16", upload_date="2026-04-16",
            duration_s=1.0, width=1, height=1, codec="x", sha1="SAME",
        ))
    out = library / "07_QUERY_PULLS" / "dedup"
    result = pull.pull(db, out, library_root=library, dedup_by_sha1=True)
    assert result.count == 1


def test_pull_empty_result(tmp_path):
    library = tmp_path / "library"; library.mkdir()
    db = library / "idx.sqlite"; index.init(db)
    out = library / "07_QUERY_PULLS" / "nothing"
    result = pull.pull(db, out, library_root=library, category="interview-duo")
    assert result.count == 0
    # Empty result should NOT create the folder
    assert not out.exists()


def test_pull_count_reflects_actually_linked_not_matched(tmp_path):
    """If a source file is missing on disk, PullResult.count should NOT include it."""
    library = tmp_path / "library"; library.mkdir()
    db = library / "idx.sqlite"; index.init(db)
    src_dir = library / "05_FOOTAGE_LIBRARY" / "misc" / "W01_Apr-15-19"
    src_dir.mkdir(parents=True)

    # Two clips: one exists on disk, one is a ghost row
    real_rel = "05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/real.mp4"
    ghost_rel = "05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/ghost.mp4"
    (library / real_rel).write_bytes(b"x")  # ghost intentionally not created

    index.upsert(db, index.ClipRecord(
        path=real_rel, category="misc", format="short-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1, height=1, codec="x", sha1="real-sha",
    ))
    index.upsert(db, index.ClipRecord(
        path=ghost_rel, category="misc", format="short-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1, height=1, codec="x", sha1="ghost-sha",
    ))

    out = library / "07_QUERY_PULLS" / "missing-src"
    result = pull.pull(db, out, library_root=library, filmed_date="2026-04-16")

    assert result.count == 1, f"Expected 1 (only real file linked), got {result.count}"
    assert len(list(out.iterdir())) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python-scripts/footage-organizer && pytest tests/test_pull.py -v`

Expected: FAIL — `pull.pull()` does not accept `library_root` keyword.

- [ ] **Step 3: Update `pull.py` to take `library_root` and resolve paths**

Replace the entire file contents with:

```python
"""
Filter the index → build a Premiere-ready folder of hardlinks.
Falls back to copy if hardlink isn't possible (cross-drive on Windows, exFAT, etc).
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
    library_root: Path,
    dedup_by_sha1: bool = True,
    **filters,
) -> PullResult:
    library_root = Path(library_root)
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
    linked = 0
    for r in rows:
        src = library_root / r.path        # resolve relative path against library
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
        linked += 1

    return PullResult(folder=out_folder, count=linked, records=rows, fallback_copies=fallback_copies)
```

- [ ] **Step 4: Run tests to verify all pass**

Run: `cd python-scripts/footage-organizer && pytest tests/test_pull.py -v`

Expected: PASS — all 4 tests green.

- [ ] **Step 5: Commit**

```bash
git add python-scripts/footage-organizer/pull.py python-scripts/footage-organizer/tests/test_pull.py
git commit -m "feat(footage-organizer): pull resolves relative index paths via library_root

pull() now requires library_root kwarg; joins it with each record's relative
path before hardlinking. Tests updated to seed real files inside a tmp library
root so existence checks + hardlinks work end-to-end."
```

---

## Task 3: Wire `cli_index.py` to the new API + add legacy migration on entry

**Files:**
- Modify: `python-scripts/footage-organizer/cli_index.py`

- [ ] **Step 1: Read the current file to confirm scope**

Run: `cd python-scripts/footage-organizer && wc -l cli_index.py`

Expected: ~270 lines.

- [ ] **Step 2: Replace `cmd_index`, `cmd_pull`, `_walk_videos`, and add `_check_legacy_db()`**

In `python-scripts/footage-organizer/cli_index.py`:

Replace `_walk_videos` (the existing function) with this version that filters AppleDouble files and `.DS_Store`:

```python
_PREMIERE_DIR_PREFIXES = ("Adobe Premiere Pro",)


def _walk_videos(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune Premiere project subdirs — they generate .mp4 preview renders
        # that are NOT real footage. Skip names like "Adobe Premiere Pro Video
        # Previews/" and any "*.PRV" sidecar dirs.
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(_PREMIERE_DIR_PREFIXES) and not d.endswith(".PRV")
        ]
        for name in filenames:
            # Mac on exFAT sprinkles `._<name>` AppleDouble sidecars + `.DS_Store`.
            # These are not real footage — skip even if extension matches.
            if name.startswith("._") or name == ".DS_Store":
                continue
            if Path(name).suffix in VIDEO_EXTENSIONS:
                yield Path(dirpath) / name
```

Replace `cmd_index` with:

```python
def cmd_index(args):
    client = args.client
    library = _library(client)
    db_path = _db(client)
    index.init(db_path)

    _check_legacy_db(db_path)

    added = 0
    skipped = 0

    for sub in INDEX_SCAN_ROOTS:
        root = library / sub
        if not root.exists():
            continue
        for clip in _walk_videos(root):
            try:
                w, h = get_resolution(str(clip))
                duration = get_duration(str(clip))
                filmed = get_shoot_date(str(clip))
            except Exception as e:
                print(f"  [skip] {clip.name}: {e}")
                skipped += 1
                continue

            upload = datetime.fromtimestamp(clip.stat().st_mtime).strftime("%Y-%m-%d")
            rel_path = clip.relative_to(library).as_posix()
            rec = index.ClipRecord(
                path=rel_path,
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

    removed = index.remove_missing(db_path, library_root=library)
    print(f"\n  Indexed {added} clip(s), skipped {skipped}, removed {removed} missing")
    print(f"  DB: {db_path}\n")
```

Replace `cmd_pull` with:

```python
def cmd_pull(args):
    client = args.client
    library = _library(client)
    db_path = _db(client)
    if not db_path.exists():
        print(f"Error: index not built yet. Run: python cli_index.py --client {client} index")
        sys.exit(1)

    _check_legacy_db(db_path)

    slug_parts = []
    if args.filmed_date: slug_parts.append(args.filmed_date)
    if args.category:    slug_parts.append(args.category)
    if args.orientation: slug_parts.append(args.orientation)
    slug = "-".join(slug_parts) or "all"
    out = library / PULL_FOLDER_NAME / slug

    fmt_map = {"vertical": FORMAT_SHORT_FORM, "horizontal": FORMAT_LONG_FORM}
    fmt = fmt_map.get(args.orientation) if args.orientation else None

    result = pull_mod.pull(
        db_path, out,
        library_root=library,
        category=args.category,
        format=fmt,
        filmed_date=args.filmed_date,
        filmed_after=args.filmed_after,
        filmed_before=args.filmed_before,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
    )

    print(f"\n  Pull → {result.folder}")
    print(f"  Linked {result.count} clip(s); fallback copies: {result.fallback_copies}\n")
```

Add this new helper function near the top of the file (right after `_db`):

```python
def _check_legacy_db(db_path: Path) -> None:
    """If the DB has legacy absolute paths, wipe + warn. The next index build
    will repopulate with relative paths. Safe to run on an empty DB.

    This is symmetrical: whichever machine (Mac or Windows) runs first after the
    relative-path migration triggers the wipe; subsequent runs on either machine
    see relative paths and short-circuit.
    """
    if not db_path.exists():
        return
    if not index.has_legacy_paths(db_path):
        return
    print(f"\n  ! Detected legacy absolute-path index at {db_path}")
    print(f"  ! Wiping clips table and rebuilding with relative paths.")
    print(f"  ! (This is safe — clip files on disk are untouched.)\n")
    index.wipe_clips(db_path)
```

- [ ] **Step 3: Run all tests to make sure nothing regressed**

Run: `cd python-scripts/footage-organizer && pytest tests/ -v`

Expected: PASS — all tests from test_index.py + test_pull.py + test_organizer.py + test_week_utils.py green.

- [ ] **Step 4: Commit**

```bash
git add python-scripts/footage-organizer/cli_index.py
git commit -m "feat(footage-organizer): cli_index uses relative paths + legacy DB migration

cmd_index now stores clip.relative_to(library).as_posix(); cmd_pull resolves
via library_root. _check_legacy_db() detects pre-migration absolute paths and
wipes the clips table on entry — next index build repopulates with portable
relative paths. Symmetrical migration: works whether Mac or Windows runs first.

Walker also filters Mac AppleDouble (._*) and .DS_Store files which appear on
exFAT-formatted shared drives."
```

---

## Task 4: Cross-machine compatibility tests

**Files:**
- Create: `python-scripts/footage-organizer/tests/test_index_compat.py`

- [ ] **Step 1: Create the new test file**

Write `python-scripts/footage-organizer/tests/test_index_compat.py`:

```python
"""Cross-machine compatibility tests — simulate the same DB being read from
two different library roots (e.g. /Volumes/Footage/Sai vs D:/Sai)."""
from pathlib import Path
import sqlite3
import index, pull


def _make_clip(library: Path, rel: str) -> Path:
    """Create a real file at <library>/<rel> and return its Path."""
    full = library / rel
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_bytes(b"fake video bytes")
    return full


def test_same_db_resolves_under_two_different_library_roots(tmp_path):
    """The same SQLite DB (with relative paths) must work when the library root
    changes between machines. Simulates the user's actual flow: build index on
    Mac at /tmp/mac_lib, then read it back as if mounted at /tmp/win_lib."""
    mac_lib = tmp_path / "mac_lib"
    win_lib = tmp_path / "win_lib"
    mac_lib.mkdir()
    win_lib.mkdir()

    rel = "05_FOOTAGE_LIBRARY/interview-solo/W01_Apr-15-19/clip.mp4"

    # Step 1: Mac creates the file + DB at mac_lib
    _make_clip(mac_lib, rel)
    db = tmp_path / "shared.sqlite"
    index.init(db)
    index.upsert(db, index.ClipRecord(
        path=rel, category="interview-solo", format="short-form",
        filmed_date="2026-04-16", upload_date="2026-04-17",
        duration_s=10.0, width=1080, height=1920, codec="hevc", sha1="abc",
    ))

    # Step 2: Windows mounts the SAME drive at a different path. Recreate the
    # file at win_lib and read the DB through that root.
    _make_clip(win_lib, rel)

    rows = index.query(db, format="short-form")
    assert len(rows) == 1
    assert rows[0].path == rel  # path is relative — no machine-specific prefix

    # Existence check via Windows root works
    removed = index.remove_missing(db, library_root=win_lib)
    assert removed == 0  # file exists under win_lib

    # Pull via Windows root works
    out = win_lib / "07_QUERY_PULLS" / "x"
    result = pull.pull(db, out, library_root=win_lib, filmed_date="2026-04-16")
    assert result.count == 1
    assert (out / "clip.mp4").exists()


def test_legacy_absolute_path_db_is_detected(tmp_path):
    """A DB built before the migration (absolute Mac paths) must be flagged as legacy."""
    db = tmp_path / "legacy.sqlite"; index.init(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO clips VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("/Volumes/Footage/Sai/05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/x.mp4",
             "misc", "long-form", "2026-04-16", "2026-04-16",
             1.0, 1920, 1080, "h264", "abc"),
        )
    assert index.has_legacy_paths(db) is True


def test_legacy_windows_absolute_path_db_is_detected(tmp_path):
    """Same legacy detection for absolute Windows paths (drive letter)."""
    db = tmp_path / "legacy.sqlite"; index.init(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO clips VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("D:/Sai/05_FOOTAGE_LIBRARY/misc/W01_Apr-15-19/x.mp4",
             "misc", "long-form", "2026-04-16", "2026-04-16",
             1.0, 1920, 1080, "h264", "abc"),
        )
    assert index.has_legacy_paths(db) is True


def test_wipe_clips_then_reindex_produces_relative_paths(tmp_path):
    """Full migration round-trip: legacy DB → wipe → upsert with relative path."""
    db = tmp_path / "idx.sqlite"; index.init(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO clips VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("/Volumes/Footage/Sai/05_FOOTAGE_LIBRARY/misc/x.mp4",
             "misc", "long-form", "2026-04-16", "2026-04-16",
             1.0, 1920, 1080, "h264", "abc"),
        )
    assert index.has_legacy_paths(db) is True

    index.wipe_clips(db)
    assert len(index.query(db)) == 0
    assert index.has_legacy_paths(db) is False

    index.upsert(db, index.ClipRecord(
        path="05_FOOTAGE_LIBRARY/misc/x.mp4",
        category="misc", format="long-form",
        filmed_date="2026-04-16", upload_date="2026-04-16",
        duration_s=1.0, width=1920, height=1080, codec="h264", sha1="abc",
    ))
    assert index.has_legacy_paths(db) is False
```

- [ ] **Step 2: Run the new test file**

Run: `cd python-scripts/footage-organizer && pytest tests/test_index_compat.py -v`

Expected: PASS — all 4 tests green.

- [ ] **Step 3: Run the full test suite to confirm nothing else regressed**

Run: `cd python-scripts/footage-organizer && pytest tests/ -v`

Expected: PASS — every test green (test_index, test_pull, test_index_compat, test_organizer, test_week_utils).

- [ ] **Step 4: Commit**

```bash
git add python-scripts/footage-organizer/tests/test_index_compat.py
git commit -m "test(footage-organizer): cross-machine + legacy migration coverage

Verifies that one SQLite DB with relative paths resolves correctly under two
different library roots (simulating Mac /Volumes/... → Windows D:/...) and
that legacy absolute-path DBs are detected + wiped cleanly."
```

---

## Task 5: Clean up Mac-isms in non-code files

**Files:**
- Delete: `python-scripts/footage-organizer/migrate_structure.py`
- Modify: `python-scripts/footage-organizer/test-set-template.csv`
- Modify: `python-scripts/footage-organizer/main.py:178`
- Modify: `python-scripts/footage-organizer/config.py:21`

- [ ] **Step 1: Confirm `migrate_structure.py` is no longer referenced**

Run: `cd python-scripts/footage-organizer && grep -r "migrate_structure" . --include="*.py" --include="*.md"`

Expected: No matches (or only matches inside migrate_structure.py itself).

- [ ] **Step 2: Delete `migrate_structure.py`**

Run: `rm python-scripts/footage-organizer/migrate_structure.py`

- [ ] **Step 3: Update `test-set-template.csv`**

Read the current contents. Replace any path containing `01_RAW_INCOMING` with the equivalent under `01_ORGANIZED`. Keep the platform-neutral path examples — show one Mac path and one Windows path side-by-side in the comment header so future readers see both:

```csv
# Format: full_path_to_clip,expected_category
# Examples (paths can be Mac or Windows-style — script uses pathlib):
# /Volumes/Footage/Sai/01_ORGANIZED/2026-04-17/C0001.MP4,interview-solo
# D:/Sai/01_ORGANIZED/2026-04-17/C0001.MP4,interview-solo
```

- [ ] **Step 4: Update `main.py:178` error-message Windows hint**

In `python-scripts/footage-organizer/main.py`, find:

```python
        print(f"  Add it like: SAI_LIBRARY_ROOT=/Volumes/SSD/Sai")
```

Replace with:

```python
        print(f"  Add it like:")
        print(f"    Mac:     SAI_LIBRARY_ROOT=/Volumes/Footage/Sai")
        print(f"    Windows: SAI_LIBRARY_ROOT=D:/Sai")
```

- [ ] **Step 5: Update `config.py:21` comment**

In `python-scripts/footage-organizer/config.py`, find:

```python
# Client library roots — set in .env to the root of each client's SSD folder
# e.g. SAI_LIBRARY_ROOT=/Volumes/SSD/Sai
```

Replace with:

```python
# Client library roots — set in .env to the root of each client's SSD folder.
# Same physical exFAT drive across machines:
#   Mac:     SAI_LIBRARY_ROOT=/Volumes/Footage/Sai
#   Windows: SAI_LIBRARY_ROOT=D:/Sai
```

- [ ] **Step 6: Commit**

```bash
git add python-scripts/footage-organizer/test-set-template.csv \
        python-scripts/footage-organizer/main.py \
        python-scripts/footage-organizer/config.py
git rm python-scripts/footage-organizer/migrate_structure.py
git commit -m "chore(footage-organizer): purge Mac-isms from helpers + docs

Delete obsolete migrate_structure.py (had hardcoded /Volumes path; superseded
by migrate_to_flat_structure.py + migrate_library_to_weeks.py).
Update test-set-template.csv to reference 01_ORGANIZED instead of removed
01_RAW_INCOMING. Show both Mac and Windows path examples in main.py error
message and config.py comment so .env setup is obvious on either OS."
```

---

## Task 6: Update docs to reflect relative-path index property

**Files:**
- Modify: `python-scripts/footage-organizer/CLAUDE.md`
- Modify: `workflows/footage-organizer.md`
- Modify: `decisions/log.md`

- [ ] **Step 1: Update `python-scripts/footage-organizer/CLAUDE.md` Cross-platform block**

Read the file. Find the `**Cross-platform:**` section (currently 4 bullets). Replace that section with:

```markdown
**Cross-platform:**
- All paths use `pathlib.Path`, no drive-letter assumptions. Drive root is read from `<CLIENT>_LIBRARY_ROOT` env var (`.env` differs per machine: `/Volumes/Footage/Sai` on Mac, `D:/Sai` on Windows).
- All scripts force UTF-8 stdout/stderr (Windows defaults to cp1252).
- Folder names contain no spaces or non-ASCII (`W01_Apr-15-19` — hyphen-separated).
- **SQLite index stores POSIX-relative paths** (`05_FOOTAGE_LIBRARY/...`) so the same `.footage-index.sqlite` on the shared SSD works from either machine. `cli_index.py` resolves against the current machine's library root at read time. First run on the upgraded code (post-2026-05-02) auto-wipes any pre-migration DB containing absolute paths and rebuilds — symmetrical, runs once per machine, free.
- Walker filters Mac AppleDouble files (`._*`) and `.DS_Store` so they don't pollute the index when the drive is mounted on Mac.
```

- [ ] **Step 2: Update `workflows/footage-organizer.md` v2 section**

Find the `## v2: Index + Pull` section. Right under the existing first sentence (`A SQLite index ... makes the library queryable`), insert this paragraph:

```markdown
The index stores **paths relative to the library root** (POSIX style, e.g.
`05_FOOTAGE_LIBRARY/interview-solo/W01_Apr-15-19/C0001.MP4`). The same
`.footage-index.sqlite` file on the shared external SSD is portable —
whichever machine reads it (Mac mounted at `/Volumes/Footage/Sai/`, Windows
mounted at `D:/Sai/`) joins the relative path with its own library root at
read time.
```

- [ ] **Step 3: Append to `decisions/log.md`**

Append (do not overwrite — `decisions/log.md` is append-only):

```markdown
## 2026-05-02 — Footage Organizer index uses relative paths for cross-machine compat

The SQLite index (`.footage-index.sqlite`) at the library root now stores
clip paths relative to the library root (`05_FOOTAGE_LIBRARY/...`) in POSIX
form, instead of machine-absolute strings. Resolution to absolute happens at
read time using the current machine's `<CLIENT>_LIBRARY_ROOT` env var.

**Why:** `D:/Sai` on Windows is the same physical exFAT SSD as
`/Volumes/Footage/Sai` on Mac. Storing absolute paths meant the index was
single-machine — switching machines made `Path(p).exists()` return False for
every row, `remove_missing()` deleted them all, and `pull` returned zero
results until re-indexed.

**Migration:** symmetrical + automatic. `cli_index._check_legacy_db()` detects
absolute paths in the existing DB and wipes the `clips` table; the next
`index` run repopulates with relative paths. No manual migration step. First
run on either machine after the upgrade triggers it; subsequent runs on
either machine short-circuit.

**Why this is safe for the existing Mac workflow:** The `clips` table is the
only thing wiped. `.cache.json` (vision-classification cache) is unaffected
— its keys are filename + filesize and were already portable. The vision
cache prevents any paid Claude API re-classification; rebuilding the index is
just ffprobe + sha1 of the first 1 MB per clip, ~30 seconds for 238 clips at
zero cost.
```

- [ ] **Step 4: Commit**

```bash
git add python-scripts/footage-organizer/CLAUDE.md workflows/footage-organizer.md decisions/log.md
git commit -m "docs(footage-organizer): cross-platform index property + decision log

Document that .footage-index.sqlite is portable across the Mac and Windows
mounts of the shared exFAT SSD. CLAUDE.md cross-platform block now explains
the relative-path scheme and the symmetrical wipe-on-detect migration.
Append decisions/log entry."
```

---

## Task 7: Verify on Windows (the machine we're on)

This is manual smoke-testing, not automated. Run from `python-scripts/footage-organizer/`.

- [ ] **Step 1: Confirm `.env` has the Windows path**

Run: `Get-Content .env | Select-String LIBRARY_ROOT`

Expected: `SAI_LIBRARY_ROOT=D:/Sai` (forward slashes, no trailing slash).

If missing: open `.env` in your editor and add the line. Do not commit `.env`.

- [ ] **Step 2: Run the full pytest suite**

Run: `pytest tests/ -v`

Expected: every test passes — `test_index.py` (8), `test_pull.py` (4), `test_index_compat.py` (4), `test_organizer.py` (existing), `test_week_utils.py` (existing).

- [ ] **Step 3: First `index` run will detect + wipe the legacy Mac-built DB**

Run: `python cli_index.py --client sai index`

Expected output starts with:

```
  ! Detected legacy absolute-path index at D:/Sai/.footage-index.sqlite
  ! Wiping clips table and rebuilding with relative paths.
  ! (This is safe — clip files on disk are untouched.)

  Indexed <N> clip(s), skipped 0, removed 0 missing
  DB: D:/Sai/.footage-index.sqlite
```

`<N>` should be ~238 (or the post-flatten/post-week-migration count — record what you see).

- [ ] **Step 4: Run `index` again to confirm no-op + no legacy warning**

Run: `python cli_index.py --client sai index`

Expected: no `! Detected legacy` warning. Output something like `Indexed <N>, skipped 0, removed 0`. Same `<N>` as Step 3.

- [ ] **Step 5: Verify `create-week` works idempotently**

Run: `python cli_index.py --client sai create-week`

Expected: prints something like `Week W03_Apr-27-May-3 (SAI)` and `Created 0 folder(s), skipped 17 existing` (assuming Mac already created them).

- [ ] **Step 6: Verify `pull` works end-to-end**

Run: `python cli_index.py --client sai pull --orientation vertical --filmed-date 2026-04-21`

Expected: prints `Pull → D:/Sai/07_QUERY_PULLS/2026-04-21-vertical` and `Linked <K> clip(s); fallback copies: <K>` where `<K>` matches the actual count. Open the folder — files should be there.

- [ ] **Step 7: Clean up the test pull**

Run: `python cli_index.py --client sai pull-cleanup --older-than 0`

Expected: deletes the test pull folder you just created. Or use the interactive form and answer `y`.

- [ ] **Step 8: Commit any incidentals (no source changes expected here)**

```bash
git status
```

Expected: clean. If `.cache.json` updated (unlikely since you didn't `--archive`), commit it:

```bash
git add python-scripts/footage-organizer/.cache.json
git commit -m "chore: cache update after Windows verification run"
```

---

## Task 8: Verify on Mac after replugging the drive (the safety check)

This is the whole reason for the plan. Run after Task 7 succeeds and you've physically moved the SSD to the Mac.

- [ ] **Step 1: Pull latest from main on Mac**

```bash
cd ~/Desktop/my-project    # or wherever the repo lives on Mac
git pull
```

Expected: pulls the commits from Tasks 1–6.

- [ ] **Step 2: Confirm Mac `.env` is unchanged and correct**

```bash
grep LIBRARY_ROOT python-scripts/footage-organizer/.env
```

Expected: `SAI_LIBRARY_ROOT=/Volumes/Footage/Sai` (or whatever the Mac mount path is — unchanged from before this plan).

- [ ] **Step 3: Run pytest on Mac**

```bash
cd python-scripts/footage-organizer && pytest tests/ -v
```

Expected: every test passes (same as Windows).

- [ ] **Step 4: Run `index` on Mac**

```bash
python cli_index.py --client sai index
```

**Critical expected behavior:** NO `! Detected legacy` warning this time — Windows already migrated the DB. Output should be a normal incremental re-index:

```
  Indexed <N> clip(s), skipped 0, removed 0 missing
```

`<N>` should match the count from Windows Task 7 Step 3.

If you DO see the legacy warning, that means the Windows verification didn't actually persist the wiped DB — investigate (likely the drive wasn't safely ejected, or git pulled an old DB on top of it).

- [ ] **Step 5: Run `pull` on Mac and confirm it returns the same count as Windows**

```bash
python cli_index.py --client sai pull --orientation vertical --filmed-date 2026-04-21
```

Expected: `Linked <K> clip(s)` where `<K>` matches the count from Windows Task 7 Step 6.

- [ ] **Step 6: Clean up the test pull on Mac**

```bash
python cli_index.py --client sai pull-cleanup --older-than 0
```

- [ ] **Step 7: Document the verification**

Append a one-line entry to `decisions/log.md`:

```markdown
## 2026-05-02 — Cross-machine compat verified

Plan `plans/2026-05-02-footage-organizer-windows-compat.md` shipped. Verified
on Windows (D:/Sai) then Mac (/Volumes/Footage/Sai) with the same SSD —
identical clip counts and pull results, no legacy warning on the second
machine.
```

Commit:

```bash
git add decisions/log.md
git commit -m "docs: log Windows + Mac compat verification result"
git push
```

---

## How to Verify It Works

The plan has a built-in success criteria: Tasks 7 + 8 are the verification. If both checklists complete cleanly, the goal is met.

Additional sanity checks:
- [ ] `pytest tests/` passes on both machines without modification
- [ ] The same `.footage-index.sqlite` file (binary-equal after a fresh `index` from either machine) is not necessary, but the same row count + matching `pull` counts are
- [ ] `git diff` on `.env` files shows no spurious changes (`.env` is gitignored anyway, but double-check no path got hardcoded into a tracked file)
- [ ] Running the **organize** flow (`python main.py --client sai --date <past-date>`) on Windows still works and produces identical category folder names to a Mac run — this is unchanged by the plan but worth a smoke test if you happen to have a backlog day to organize

---

## Notes

**Trade-offs**
- The first `index` run on each machine costs ~30 sec (rebuilding from disk). The user gets one such run per machine, total. Fine.
- Storing `clips.path` as POSIX (`as_posix()`) on Windows means the value uses forward slashes regardless of the OS that wrote it. That's deliberate — lets us compare path strings across machines without normalization. `Path(rel)` on Windows correctly handles forward-slash strings.
- We don't add a schema version column. The legacy detection (any path with `:`, `\\`, or starting `/`) is sufficient for this single one-shot migration. If we ever need a second migration we'll revisit.

**Cross-platform safety**
- All file operations go through `pathlib.Path` + `as_posix()` for storage, native joins for filesystem operations. Tested implicitly via pytest on Windows in Task 7.
- AppleDouble (`._*`) and `.DS_Store` are filtered at the walker so Mac mount artifacts on the exFAT drive don't end up in the index.
- exFAT hardlink failure → copy fallback in `pull.py` is preserved (existing behavior, unchanged).

**Risks**
- If something interrupts Task 7 Step 3 (the wiping migration) mid-flight, the DB could be left empty but with the legacy detection no longer triggering. The next `index` run rebuilds it cleanly anyway, so this is self-healing.
- If the user runs `pull` on Windows BEFORE running `index` after deploying these changes, the legacy DB will be wiped (Step 1 of `cmd_pull` calls `_check_legacy_db()`) but no rows are added until `index` runs. `pull` will print `Linked 0 clip(s)`. User reaction: re-read the warning and run `index`. Acceptable.

**Follow-ups not in this plan**
- Auto-trigger `index` after `archive` runs (currently you have to manually re-index). Already in the FUTURE_IDEAS list — out of scope here.
- Compaction of the SQLite DB after wiping (`VACUUM`). Not worth it; DB is small.
- A `--force-rebuild` flag on `cli_index.py index` to manually trigger the wipe. Skip until needed.

**One thing to flag at /implement time**
- Task 7 Step 3 is the only step that touches the actual production index file. Everything else is either tests (sandboxed via `tmp_path`) or doc edits. If this step fails, the user can always `rm D:/Sai/.footage-index.sqlite` and run `index` again — the file is regenerable.
