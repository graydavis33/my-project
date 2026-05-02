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
    subfolder_fn=None,
    **filters,
) -> PullResult:
    """Filter the index and build a Premiere-ready folder.

    subfolder_fn: optional callable(record) -> str. If provided, each clip lands
    inside out_folder/<subfolder>/. Used by --by-week to group clips by W## label.
    """
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
        src = Path(r.path)
        if not src.exists():
            continue
        dest_dir = out_folder
        if subfolder_fn is not None:
            sub = subfolder_fn(r)
            if sub:
                dest_dir = out_folder / sub
                dest_dir.mkdir(parents=True, exist_ok=True)
        dst = dest_dir / src.name
        if dst.exists():
            stem, ext = dst.stem, dst.suffix
            n = 2
            while dst.exists():
                dst = dest_dir / f"{stem}_{n}{ext}"
                n += 1
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)
            fallback_copies += 1
        linked += 1

    return PullResult(folder=out_folder, count=linked, records=rows, fallback_copies=fallback_copies)
