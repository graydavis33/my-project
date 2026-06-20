"""The drafts-cleanup sweep deletes stale review files in 03_DELIVERED/drafts/
but must NEVER delete editable project files (.prproj/.aep/.psd/...), and must
leave recent drafts alone. Mirrors the query-pull sweep but also handles loose
files (not just folders) and the project-file shield.
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


def _run(tmp_path, monkeypatch, older_than):
    drafts = tmp_path / "03_DELIVERED" / "drafts"
    drafts.mkdir(parents=True)
    monkeypatch.setattr(cli_index, "_library", lambda client: tmp_path)
    cli_index.cmd_drafts_cleanup(SimpleNamespace(client="sai", older_than=older_than))
    return drafts


def test_deletes_stale_files_keeps_recent(tmp_path, monkeypatch):
    drafts = tmp_path / "03_DELIVERED" / "drafts"
    drafts.mkdir(parents=True)
    stale = _mk(drafts / "old draft.mp4"); _age(stale, 10)
    recent = _mk(drafts / "fresh draft.mp4"); _age(recent, 2)
    monkeypatch.setattr(cli_index, "_library", lambda client: tmp_path)

    cli_index.cmd_drafts_cleanup(SimpleNamespace(client="sai", older_than=7))

    assert not stale.exists()      # 10d old → gone
    assert recent.exists()         # 2d old → kept


def test_never_deletes_project_files(tmp_path, monkeypatch):
    drafts = tmp_path / "03_DELIVERED" / "drafts"
    drafts.mkdir(parents=True)
    prproj = _mk(drafts / "edit.prproj"); _age(prproj, 30)
    aep = _mk(drafts / "comp.aep"); _age(aep, 30)
    psd = _mk(drafts / "thumb.psd"); _age(psd, 30)
    monkeypatch.setattr(cli_index, "_library", lambda client: tmp_path)

    cli_index.cmd_drafts_cleanup(SimpleNamespace(client="sai", older_than=7))

    assert prproj.exists() and aep.exists() and psd.exists()  # all shielded


def test_folder_with_project_file_is_skipped_whole(tmp_path, monkeypatch):
    drafts = tmp_path / "03_DELIVERED" / "drafts"
    drafts.mkdir(parents=True)
    proj_dir = drafts / "Vid 5 edit"
    _mk(proj_dir / "render.mp4")
    _mk(proj_dir / "Vid 5.prproj")
    _age(proj_dir / "render.mp4", 30)
    _age(proj_dir / "Vid 5.prproj", 30)
    _age(proj_dir, 30)

    plain_dir = drafts / "old renders"
    _mk(plain_dir / "v1.mp4")
    _age(plain_dir / "v1.mp4", 30)
    _age(plain_dir, 30)

    monkeypatch.setattr(cli_index, "_library", lambda client: tmp_path)
    cli_index.cmd_drafts_cleanup(SimpleNamespace(client="sai", older_than=7))

    assert proj_dir.exists()        # contains a .prproj → whole folder kept
    assert not plain_dir.exists()   # no project file + stale → deleted


def test_ignores_dotfiles(tmp_path, monkeypatch):
    drafts = tmp_path / "03_DELIVERED" / "drafts"
    drafts.mkdir(parents=True)
    ds = _mk(drafts / ".DS_Store"); _age(ds, 30)
    monkeypatch.setattr(cli_index, "_library", lambda client: tmp_path)

    # Should not crash on / count dotfiles; they're just left alone.
    cli_index.cmd_drafts_cleanup(SimpleNamespace(client="sai", older_than=7))
    assert ds.exists()
