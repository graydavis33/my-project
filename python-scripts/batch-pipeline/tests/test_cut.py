import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cut

def test_plan_drops_dead_air_and_maps_caption_times():
    sr = 48000; audio = np.zeros(int(300*sr), dtype=np.float32)  # silence => snap_out cuts tight
    words = [{"start":10.0,"end":10.4,"word":"hello"},{"start":10.5,"end":10.9,"word":"world"}]
    ranges = [(10.0, 10.9, None, None)]
    keep, caps, total = cut.plan(words, ranges, audio, sr)
    assert len(keep) == 1
    assert caps[0]["word"] == "hello" and abs(caps[0]["start"]) < 0.2  # first kept word near t=0
    assert total > 0.9
