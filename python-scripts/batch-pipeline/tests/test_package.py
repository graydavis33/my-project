import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package

def test_folder_name():
    assert package.folder_name(3, 4, "Money Reflects Who You Are") == \
        "B3_V04 - Money Reflects Who You Are"

def test_deliver_filesystem_layout(tmp_path):
    # Create tiny placeholder .mov files (deliver only copies them)
    a_cut = tmp_path / "a_cut.mov"
    b_cut = tmp_path / "b_cut.mov"
    captions_mov = tmp_path / "captions.mov"
    a_cut.write_bytes(b"PLACEHOLDER_A")
    b_cut.write_bytes(b"PLACEHOLDER_B")
    captions_mov.write_bytes(b"PLACEHOLDER_CAPTIONS")

    pkg = package.deliver(
        3, 4, "Money Reflects Who You Are",
        a_cut, b_cut, captions_mov,
        {"text": "info"},
        out_root=tmp_path,
    )

    assert pkg.exists()
    assert (pkg / "ANGLES" / "B3_V04_A-cam.mov").exists()
    assert (pkg / "ANGLES" / "B3_V04_B-cam.mov").exists()
    assert (pkg / "CAPTIONS" / "B3_V04_captions.mov").exists()
    assert (pkg / "_INFO.txt").read_text(encoding="utf-8") == "info"
