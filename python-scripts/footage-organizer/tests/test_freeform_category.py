from pathlib import Path

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli_index import _category_from_path

LIB = Path("/lib")


def test_freeform_folder_name_is_category():
    # Gray's own folder name (not one of the 17) should be its own category
    clip = LIB / "05_FOOTAGE_LIBRARY" / "nyc-street" / "W10_Jun-15-21" / "C2700.MP4"
    assert _category_from_path(clip, LIB) == "nyc-street"


def test_existing_category_still_works():
    clip = LIB / "05_FOOTAGE_LIBRARY" / "interview-solo" / "W01_Apr-15-19" / "C0001.MP4"
    assert _category_from_path(clip, LIB) == "interview-solo"


def test_non_library_path_is_misc():
    clip = LIB / "02_ACTIVE_PROJECTS" / "shorts" / "W01_Apr-15-19" / "proj.mp4"
    assert _category_from_path(clip, LIB) == "misc"
