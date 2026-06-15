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
    batch_num: Optional[int] = None  # set when filed under Batch_NN/Vid_MM (v3 batch command)
    vid_num: Optional[int] = None


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
    sha1         TEXT NOT NULL,
    batch_num    INTEGER,
    vid_num      INTEGER
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
        _migrate(conn)


def _migrate(conn) -> None:
    """Add columns introduced after the original 10-column schema to a pre-existing
    DB. ALTER ADD COLUMN is non-destructive + idempotent, so each machine runs it
    once on first init with the new code — no rebuild, no data loss."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(clips)").fetchall()}
    if "batch_num" not in cols:
        conn.execute("ALTER TABLE clips ADD COLUMN batch_num INTEGER")
    if "vid_num" not in cols:
        conn.execute("ALTER TABLE clips ADD COLUMN vid_num INTEGER")
    # Created here (not in _SCHEMA) so it runs AFTER the columns exist on an
    # older DB being migrated in place.
    conn.execute("CREATE INDEX IF NOT EXISTS idx_batch ON clips(batch_num, vid_num)")


def upsert(db_path: Path, rec: ClipRecord) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO clips (path, category, format, filmed_date, upload_date,
                               duration_s, width, height, codec, sha1,
                               batch_num, vid_num)
            VALUES (:path, :category, :format, :filmed_date, :upload_date,
                    :duration_s, :width, :height, :codec, :sha1,
                    :batch_num, :vid_num)
            ON CONFLICT(path) DO UPDATE SET
                category    = excluded.category,
                format      = excluded.format,
                filmed_date = excluded.filmed_date,
                upload_date = excluded.upload_date,
                duration_s  = excluded.duration_s,
                width       = excluded.width,
                height      = excluded.height,
                codec       = excluded.codec,
                sha1        = excluded.sha1,
                batch_num   = excluded.batch_num,
                vid_num     = excluded.vid_num
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
    batch_num: Optional[int] = None,
    vid_num: Optional[int] = None,
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
    if batch_num is not None:
        where.append("batch_num = :batch_num"); params["batch_num"] = batch_num
    if vid_num is not None:
        where.append("vid_num = :vid_num"); params["vid_num"] = vid_num

    sql = "SELECT path, category, format, filmed_date, upload_date, duration_s, width, height, codec, sha1, batch_num, vid_num FROM clips"
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
        rows = conn.execute("SELECT path FROM clips").fetchall()
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
