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
