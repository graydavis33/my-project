import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from organizer import organize_file, archive_file


def _make(path, content=b"x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)


def test_organize_moves_sony_xml_sidecar(tmp_path):
    src_dir = tmp_path / "drop"
    out_dir = tmp_path / "organized"
    _make(str(src_dir / "C2106.MP4"))
    _make(str(src_dir / "C2106M01.XML"))

    organize_file(str(src_dir / "C2106.MP4"), str(out_dir), "2026-05-01", "interview-solo", move=True)

    assert (out_dir / "interview-solo" / "2026-05-01" / "C2106.MP4").exists()
    assert (out_dir / "interview-solo" / "2026-05-01" / "C2106M01.XML").exists()
    assert not (src_dir / "C2106M01.XML").exists()


def test_organize_handles_xmp_sidecar(tmp_path):
    src_dir = tmp_path / "drop"
    out_dir = tmp_path / "organized"
    _make(str(src_dir / "clip.MP4"))
    _make(str(src_dir / "clip.xmp"))

    organize_file(str(src_dir / "clip.MP4"), str(out_dir), "2026-05-01", "misc", move=True)

    assert (out_dir / "misc" / "2026-05-01" / "clip.MP4").exists()
    assert (out_dir / "misc" / "2026-05-01" / "clip.xmp").exists()


def test_organize_silent_when_no_sidecar(tmp_path):
    src_dir = tmp_path / "drop"
    out_dir = tmp_path / "organized"
    _make(str(src_dir / "lonely.MP4"))

    organize_file(str(src_dir / "lonely.MP4"), str(out_dir), "2026-05-01", "misc", move=True)

    assert (out_dir / "misc" / "2026-05-01" / "lonely.MP4").exists()


def test_archive_moves_sidecar_too(tmp_path):
    src_dir = tmp_path / "src"
    archive_dir = tmp_path / "archive"
    _make(str(src_dir / "C9999.MP4"))
    _make(str(src_dir / "C9999M01.XML"))

    archive_file(str(src_dir / "C9999.MP4"), str(archive_dir), "interview-solo", move=True)

    assert (archive_dir / "interview-solo" / "C9999.MP4").exists()
    assert (archive_dir / "interview-solo" / "C9999M01.XML").exists()
