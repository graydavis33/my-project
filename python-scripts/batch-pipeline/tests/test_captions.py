import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import captions

def test_clean_casing_and_punct():
    assert captions.clean("Money.") == "money"
    assert captions.clean("I'm") == "I'm"
    assert captions.clean("Sai") == "Sai"

def test_group_max_three_words():
    words = [{"start":i*0.3,"end":i*0.3+0.2,"word":f"w{i}"} for i in range(5)]
    cards = captions.group(words)
    assert all(len(c[0]) <= 3 for c in cards)
