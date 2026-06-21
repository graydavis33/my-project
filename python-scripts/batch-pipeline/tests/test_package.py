import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package

def test_folder_name():
    assert package.folder_name(3, 4, "Money Reflects Who You Are") == \
        "B3_V04 - Money Reflects Who You Are"
