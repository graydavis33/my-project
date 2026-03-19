"""
organizer.py
Copies or moves a video file into output_dir/category/, with collision handling.
"""
import os
import shutil


def organize_file(
    src_path: str,
    output_dir: str,
    category: str,
    move: bool = False,
) -> str:
    """
    Copy (default) or move src_path into output_dir/category/filename.
    Returns the destination path.

    - Creates the category subfolder if it doesn't exist.
    - If a file with the same name already exists, appends _2, _3, etc.
      Never silently overwrites.
    - Uses shutil.copy2 to preserve original file timestamps.
    """
    dest_dir = os.path.join(output_dir, category)
    os.makedirs(dest_dir, exist_ok=True)

    filename = os.path.basename(src_path)
    dest_path = os.path.join(dest_dir, filename)

    # Collision handling
    if os.path.exists(dest_path) and not _same_file(src_path, dest_path):
        stem, ext = os.path.splitext(filename)
        counter = 2
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_dir, f"{stem}_{counter}{ext}")
            counter += 1

    if move:
        shutil.move(src_path, dest_path)
    else:
        shutil.copy2(src_path, dest_path)  # copy2 preserves timestamps

    return dest_path


def _same_file(a: str, b: str) -> bool:
    try:
        return os.path.samefile(a, b)
    except Exception:
        return False
