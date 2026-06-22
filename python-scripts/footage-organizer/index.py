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
    # TRUE display orientation from extractor.get_display_orientation (rotation-aware,
    # so Sony 1920x1080 + 90° flag = 'vertical'). Set at scan time, overwritten on
    # rescan like width/height (it's ffprobe-derived, NOT a tag). NULL until a row
    # is re-indexed under the new code. 'horizontal'|'vertical'|'square'|'unknown'.
    orientation: Optional[str] = None
    batch_num: Optional[int] = None  # set when filed under Batch_NN/Vid_MM (v3 batch command)
    vid_num: Optional[int] = None
    # v4 b-roll tags — set by Vision (Opus) + the tagging dashboard, NOT by the
    # ffprobe scan. A plain re-index leaves these None; upsert COALESCEs so a
    # rescan never wipes a tag. emotion/action/location are single-valued;
    # objects is a pipe-wrapped multi-value string ("|cup|laptop|") — use
    # pack_objects/unpack_objects. emotion present ⇒ Sai in frame.
    emotion: Optional[str] = None
    action: Optional[str] = None
    location: Optional[str] = None
    objects: Optional[str] = None


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
    orientation  TEXT,
    batch_num    INTEGER,
    vid_num      INTEGER,
    emotion      TEXT,
    action       TEXT,
    location     TEXT,
    objects      TEXT
);
CREATE INDEX IF NOT EXISTS idx_filmed_date ON clips(filmed_date);
CREATE INDEX IF NOT EXISTS idx_category    ON clips(category);
CREATE INDEX IF NOT EXISTS idx_format      ON clips(format);
CREATE INDEX IF NOT EXISTS idx_sha1        ON clips(sha1);
"""

# objects is stored pipe-WRAPPED ("|cup|laptop|") so a LIKE '%|cup|%' match
# can't collide on a substring ("cup" never matches "coffee cup").
OBJ_DELIM = "|"


def pack_objects(objs) -> Optional[str]:
    """List of object tags → pipe-wrapped storage string (None when empty)."""
    cleaned = [o.strip() for o in (objs or []) if o and o.strip()]
    if not cleaned:
        return None
    return OBJ_DELIM + OBJ_DELIM.join(cleaned) + OBJ_DELIM


def unpack_objects(stored: Optional[str]) -> list:
    """Pipe-wrapped storage string → list of object tags."""
    if not stored:
        return []
    return [o for o in stored.strip(OBJ_DELIM).split(OBJ_DELIM) if o]


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
    # TRUE display orientation (rotation-aware) — ffprobe-derived, plain overwrite.
    if "orientation" not in cols:
        conn.execute("ALTER TABLE clips ADD COLUMN orientation TEXT")
    # v4 b-roll tag columns — non-destructive ALTER, idempotent per machine.
    for tag_col in ("emotion", "action", "location", "objects"):
        if tag_col not in cols:
            conn.execute(f"ALTER TABLE clips ADD COLUMN {tag_col} TEXT")
    # Created here (not in _SCHEMA) so they run AFTER the columns exist on an
    # older DB being migrated in place.
    conn.execute("CREATE INDEX IF NOT EXISTS idx_batch ON clips(batch_num, vid_num)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_orientation ON clips(orientation)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON clips(emotion, action, location)")


def upsert(db_path: Path, rec: ClipRecord) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO clips (path, category, format, filmed_date, upload_date,
                               duration_s, width, height, codec, sha1, orientation,
                               batch_num, vid_num,
                               emotion, action, location, objects)
            VALUES (:path, :category, :format, :filmed_date, :upload_date,
                    :duration_s, :width, :height, :codec, :sha1, :orientation,
                    :batch_num, :vid_num,
                    :emotion, :action, :location, :objects)
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
                -- ffprobe-derived, plain overwrite (NOT COALESCE — it's not a tag).
                orientation = excluded.orientation,
                batch_num   = excluded.batch_num,
                vid_num     = excluded.vid_num,
                -- Tags are set by Vision/the dashboard, never by the ffprobe scan.
                -- COALESCE(excluded, existing) keeps the tag when a rescan passes
                -- NULL; an explicit write (value or "" to clear) still updates it.
                emotion     = COALESCE(excluded.emotion,  clips.emotion),
                action      = COALESCE(excluded.action,   clips.action),
                location    = COALESCE(excluded.location, clips.location),
                objects     = COALESCE(excluded.objects,  clips.objects)
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
    orientation: Optional[str] = None,
    batch_num: Optional[int] = None,
    vid_num: Optional[int] = None,
    emotion: Optional[str] = None,
    action: Optional[str] = None,
    location: Optional[str] = None,
    object: Optional[str] = None,
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
    if orientation:
        # TRUE display orientation (rotation-aware). NULL rows simply don't match.
        where.append("orientation = :orientation"); params["orientation"] = orientation
    if batch_num is not None:
        where.append("batch_num = :batch_num"); params["batch_num"] = batch_num
    if vid_num is not None:
        where.append("vid_num = :vid_num"); params["vid_num"] = vid_num
    if emotion:
        where.append("emotion = :emotion"); params["emotion"] = emotion
    if action:
        where.append("action = :action"); params["action"] = action
    if location:
        where.append("location = :location"); params["location"] = location
    if object:
        # objects is pipe-wrapped, so match the delimited token (no substring collisions)
        where.append("objects LIKE :object_pat")
        params["object_pat"] = f"%{OBJ_DELIM}{object}{OBJ_DELIM}%"

    sql = "SELECT path, category, format, filmed_date, upload_date, duration_s, width, height, codec, sha1, orientation, batch_num, vid_num, emotion, action, location, objects FROM clips"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY filmed_date DESC, path"

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()

    return [ClipRecord(*r) for r in rows]


_SELECT_COLS = ("path, category, format, filmed_date, upload_date, duration_s, "
                "width, height, codec, sha1, orientation, batch_num, vid_num, "
                "emotion, action, location, objects")


def get(db_path: Path, path: str):
    """Fetch one clip by its relative path, or None."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(f"SELECT {_SELECT_COLS} FROM clips WHERE path = ?", (path,)).fetchone()
    return ClipRecord(*row) if row else None


_UNSET = object()


def update_tags(db_path: Path, path: str, *, emotion=_UNSET, action=_UNSET,
                location=_UNSET, objects=_UNSET) -> int:
    """Directly set tag columns on one clip (the dashboard's write path). Only
    the fields you pass are touched — so "" clears a tag, a value sets it, and an
    omitted field is left unchanged. Returns rows updated (0 if path unknown)."""
    cols = {"emotion": emotion, "action": action, "location": location, "objects": objects}
    params = {k: v for k, v in cols.items() if v is not _UNSET}
    if not params:
        return 0
    assignment = ", ".join(f"{k} = :{k}" for k in params)
    params["path"] = path
    with sqlite3.connect(db_path) as conn:
        return conn.execute(f"UPDATE clips SET {assignment} WHERE path = :path", params).rowcount


def relocate(db_path: Path, old_path: str, new_path: str, category: str) -> int:
    """Repoint a clip's index row to a new path + category (e.g. b-roll→vertical
    when an orientation was wrong). Drops any stale row at new_path first to avoid
    a UNIQUE(path) clash. Returns rows updated."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM clips WHERE path = ?", (new_path,))
        return conn.execute("UPDATE clips SET path = ?, category = ? WHERE path = ?",
                            (new_path, category, old_path)).rowcount


def remove(db_path: Path, path: str) -> int:
    """Delete a single clip's index row by path. Returns rows removed (0 or 1).
    Used when the dashboard permanently deletes a clip from disk."""
    with sqlite3.connect(db_path) as conn:
        return conn.execute("DELETE FROM clips WHERE path = ?", (path,)).rowcount


def distinct_tag_values(db_path: Path) -> dict:
    """All distinct tag values currently in the index — feeds dashboard autocomplete.
    Returns {emotion:[...], action:[...], location:[...], object:[...]}."""
    out = {"emotion": set(), "action": set(), "location": set(), "object": set()}
    with sqlite3.connect(db_path) as conn:
        for col in ("emotion", "action", "location"):
            for (v,) in conn.execute(f"SELECT DISTINCT {col} FROM clips WHERE {col} IS NOT NULL AND {col} != ''"):
                out[col].add(v)
        for (v,) in conn.execute("SELECT objects FROM clips WHERE objects IS NOT NULL AND objects != ''"):
            out["object"].update(unpack_objects(v))
    return {k: sorted(s) for k, s in out.items()}


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
