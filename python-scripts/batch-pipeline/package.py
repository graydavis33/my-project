import shutil
from pathlib import Path
import config


def folder_name(batch_n: int, vid_n: int, title: str) -> str:
    return f"B{batch_n}_V{vid_n:02d} - {title}"


def deliver(
    batch_n: int,
    vid_n: int,
    title: str,
    a_cut: Path,
    b_cut: Path,
    captions_mov: Path,
    info: dict,
    out_root=None,
) -> Path:
    """Build the deliverable package dir and return its path.

    Cuts are already final ProRes 422 + lav stereo — copied through unchanged.
    Layout:
        <out_root>/Batch_NN/B#_V## - Title/
            ANGLES/B#_V##_A-cam.mov
            ANGLES/B#_V##_B-cam.mov
            CAPTIONS/B#_V##_captions.mov
            _INFO.txt
    """
    root = out_root or (config.library_root() / "08_AI_EDITS" / "shorts")
    pkg = root / f"Batch_{batch_n:02d}" / folder_name(batch_n, vid_n, title)

    angles_dir = pkg / "ANGLES"
    captions_dir = pkg / "CAPTIONS"
    angles_dir.mkdir(parents=True, exist_ok=True)
    captions_dir.mkdir(exist_ok=True)

    tag = f"B{batch_n}_V{vid_n:02d}"
    shutil.copy2(a_cut, angles_dir / f"{tag}_A-cam.mov")
    shutil.copy2(b_cut, angles_dir / f"{tag}_B-cam.mov")
    shutil.copy2(captions_mov, captions_dir / f"{tag}_captions.mov")
    (pkg / "_INFO.txt").write_text(info["text"], encoding="utf-8")

    return pkg
