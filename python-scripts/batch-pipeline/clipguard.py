import numpy as np

WIN = 0.08  # measurement window; 80ms so an early micro-dip that still has the
            # word's release spike right after it reads LOUD (not a false dip)

def _rms(a, sr, t, win=WIN):
    s = a[int(t * sr): int((t + win) * sr)]
    return float(np.sqrt(np.mean(s ** 2))) if len(s) else 0.0

def snap_out(audio, sr, sout, next_word_start):
    """Cut after the trailing word rings out, at the quietest WIN-second window
    that fits FULLY within [sout+0.10, hard_cap].

    hard_cap = sout + 0.6, capped at the next transcript word (-0.02s) so the cut
    never bleeds into it. Only full-length windows are scored: the search upper
    bound is hard_cap - WIN, so no window spills past the cap AND none degenerates
    to a 1-2 sample sliver near the cap (a sliver's RMS is meaningless and was
    pulling cuts to the boundary). If the legal region is too short for one full
    window (a very close next word), cut as early as allowed (lo_bound).
    """
    hard_cap = sout + 0.6
    if next_word_start is not None:
        hard_cap = min(hard_cap, next_word_start - 0.02)
    lo_bound = min(sout + 0.10, hard_cap)
    hi_bound = hard_cap - WIN
    if hi_bound <= lo_bound:
        return lo_bound
    best_t, best_e = lo_bound, 1e18
    t = lo_bound
    while t <= hi_bound + 1e-6:
        e = _rms(audio, sr, t)
        if e < best_e:
            best_e, best_t = e, t
        t += 0.02
    return best_t
