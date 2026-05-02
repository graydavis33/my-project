"""
organizer.py
Handles placing video files into the correct destination folder.
Sidecars (Sony XML, Adobe .xmp) travel with their video by stem match.
"""
import os
import shutil


# Suffixes that pair with a video file by matching stem.
# Sony cameras produce C####M01.XML alongside C####.MP4; Adobe writes .xmp.
SIDECAR_SUFFIXES = ["M01.XML", ".XML", ".xmp"]


def organize_file(src_path, output_dir, date_str, category, move=False):
    """Copy/move src into ORGANIZED/category/date_str/.
    Same shape as FOOTAGE_LIBRARY. Sidecars with matching stem follow the video.
    Returns the destination path of the main file."""
    dest_dir = os.path.join(output_dir, category, date_str)
    main_dest = _place_file(src_path, dest_dir, move)
    _move_sidecars(src_path, dest_dir, move)
    return main_dest


def archive_file(src_path, archive_dir, category, move=True):
    """Move/copy src into ARCHIVE/category/. Sidecars with matching stem follow.
    Returns the destination path of the main file."""
    dest_dir = os.path.join(archive_dir, category)
    main_dest = _place_file(src_path, dest_dir, move)
    _move_sidecars(src_path, dest_dir, move)
    return main_dest


def _move_sidecars(src_path, dest_dir, move):
    """Find sidecar files next to src_path (same stem, known suffixes) and place them alongside.
    Silently skips suffixes that don't exist — most clips have only one or two sidecars."""
    src_dir = os.path.dirname(src_path)
    stem = os.path.splitext(os.path.basename(src_path))[0]
    for suffix in SIDECAR_SUFFIXES:
        candidate = os.path.join(src_dir, f"{stem}{suffix}")
        if os.path.exists(candidate):
            _place_file(candidate, dest_dir, move)


def _place_file(src_path, dest_dir, move):
    os.makedirs(dest_dir, exist_ok=True)

    filename = os.path.basename(src_path)
    dest_path = os.path.join(dest_dir, filename)

    if os.path.exists(dest_path) and not _same_file(src_path, dest_path):
        stem, ext = os.path.splitext(filename)
        counter = 2
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_dir, f"{stem}_{counter}{ext}")
            counter += 1

    if move:
        shutil.move(src_path, dest_path)
    else:
        shutil.copy2(src_path, dest_path)

    return dest_path


def _same_file(a, b):
    try:
        return os.path.samefile(a, b)
    except Exception:
        return False
