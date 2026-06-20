import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import transcribe

def test_to_words_shifts_and_strips():
    raw = {"segments":[{"start":6.2,"end":7.0,"words":[
        {"start":6.2,"end":6.5,"word":" Hello"},{"start":6.5,"end":7.0,"word":"world "}]}]}
    out = transcribe.to_words(raw, shift=6.0)
    w = out["segments"][0]["words"]
    assert w[0]["word"] == "Hello" and abs(w[0]["start"]-0.2) < 1e-6
