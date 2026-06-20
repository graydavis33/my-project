import numpy as np

def _rms(a, sr, t, win=0.06):
    s = a[int(t*sr): int((t+win)*sr)]
    return float(np.sqrt(np.mean(s**2))) if len(s) else 0.0

def snap_out(audio, sr, sout, next_word_start):
    hard_cap = sout + 0.6
    if next_word_start is not None:
        hard_cap = min(hard_cap, next_word_start - 0.02)
    lo_bound = min(sout + 0.10, hard_cap)
    best_t, best_e = lo_bound, 1e18
    t = sout
    while t <= hard_cap + 1e-6:
        if t >= lo_bound:
            e = _rms(audio, sr, t)
            if e < best_e:
                best_e, best_t = e, t
        t += 0.02
    return best_t
