"""
organizer.py
Handles placing video files into the correct destination folder.
"""
import os
import shutil


def organize_file(src_path, output_dir, date_str, category, move=False):
    """
    Copy/move src into ORGANIZED/category/date_str/
    Same shape as FOOTAGE_LIBRARY (since 2026-04-28 — format folder dropped).
    Returns destination path.
    """
    dest_dir = os.path.join(output_dir, category, date_str)
    return _place_file(src_path, dest_dir, move)


def archive_file(src_path, archive_dir, category, move=True):
    """
    Move/copy src into ARCHIVE/category/ — global, no dates.
    Returns destination path.
    """
    dest_dir = os.path.join(archive_dir, category)
    return _place_file(src_path, dest_dir, move)


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
