"""The drafts-cleanup sweep deletes stale review items in 03_DELIVERED/drafts/
on the same rule as the query-pull sweep: anything idle N+ days is removed, with
NO exceptions (videos AND project files alike). It also handles loose files, not
just folders, and ignores dotfiles.
"""
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cli_index


def _mk(p: Path, body=b"x"):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(body)
    return p


def _age(p: Path, days: int):
    """Backdate a path's mtime by `days` days."""
    old = time.time() - days * 86400
    os.utime(p, (old, old))


def test_deletes_stale_files_keeps_recent(tmp_path, monkeypatch):
    drafts = tmp_path / "03_DELIVERED" / "drafts"
    drafts.mkdir(parents=True)
    stale = _mk(drafts / "old draft.mp4"); _age(stale, 10)
    recent = _mk(drafts / "fresh draft.mp4"); _age(recent, 2)
    monkeypatch.setattr(cli_index, "_library", lambda client: tmp_path)

    cli_index.cmd_drafts_cleanup(SimpleNamespace(client="sai", older_than=7))

    assert not stale.exists()      # 10d old → gone
    assert recent.exists()         # 2d old → kept


def test_deletes_stale_project_files_too(tmp_path, monkeypatch):
    drafts = tmp_path / "03_DELIVERED" / "drafts"
    drafts.mkdir(parents=True)
    prproj = _mk(drafts / "edit.prproj"); _age(prproj, 30)
    aep = _mk(drafts / "comp.aep"); _age(aep, 30)
    fresh_psd = _mk(drafts / "wip.psd"); _age(fresh_psd, 1)
    monkeypatch.setattr(cli_index, "_library", lambda client: tmp_path)

    cli_index.cmd_drafts_cleanup(SimpleNamespace(client="sai", older_than=7))

    assert not prproj.exists()     # stale project file → deleted (no exception)
    assert not aep.exists()        # stale project file → deleted
    assert fresh_psd.exists()      # 1d old → kept (only the idle rule protects it)


def test_deletes_stale_subfolders(tmp_path, monkeypatch):
    drafts = tmp_path / "03_DELIVERED" / "drafts"
    drafts.mkdir(parents=True)
    old_dir = drafts / "old renders"
    _mk(old_dir / "v1.mp4")
    _age(old_dir / "v1.mp4", 30)
    _age(old_dir, 30)
    monkeypatch.setattr(cli_index, "_library", lambda client: tmp_path)

    cli_index.cmd_drafts_cleanup(SimpleNamespace(client="sai", older_than=7))

    assert not old_dir.exists()    # stale folder → deleted whole


def test_ignores_dotfiles(tmp_path, monkeypatch):
    drafts = tmp_path / "03_DELIVERED" / "drafts"
    drafts.mkdir(parents=True)
    ds = _mk(drafts / ".DS_Store"); _age(ds, 30)
    monkeypatch.setattr(cli_index, "_library", lambda client: tmp_path)

    cli_index.cmd_drafts_cleanup(SimpleNamespace(client="sai", older_than=7))
    assert ds.exists()             # dotfiles aren't treated as drafts
