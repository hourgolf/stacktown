"""Capture until the frame stops moving, then measure.

A material edit forces a shader recompile and invalidates Lumen's surface
cache. The FIRST capture afterwards is a transient: measured here, the same
PaperTiling=0.25 state read mean 179.12 on one visit and 142.98 on another,
a mean-abs-diff of 47.5 between two captures of an IDENTICAL scene. Taking one
shot after a change and calling the difference an effect would have produced a
confident, completely wrong answer - which is the failure mode this project
keeps writing down.

So: capture repeatedly until two consecutive frames agree within the noise
floor, and only then measure. FLOOR is measured, not assumed - see floor().

CONSECUTIVE AGREEMENT IS NOT ENOUGH, AND THE CURVE SAYS SO. After a LEVEL LOAD
Lumen rebuilds from cold, and it does so slowly and monotonically. Measured on
Sandbox_Bench 2026-08-31, sampling one parked frame every 10s for four minutes:

    t=15s  mean 64.91  crushed 2.82%
    t=252s mean 67.47  crushed 1.44%   and still climbing +0.07 per sample

Every consecutive delta over that whole run was 0.07-0.19 levels - under any
sane floor FROM THE FIRST SAMPLE - while the frame still had 2.5 levels and
1.4% of crushed pixels to go. A slow drift passes a consecutive-delta test
trivially; "the frame stopped moving" and "the frame is moving too slowly to
notice between two samples" are not the same statement.

The fix is a LONG BASELINE: a frame must also agree with one taken
BASELINE_S ago, not merely with its immediate predecessor. That is the test
that distinguishes a plateau from a ramp, and it is why this session's
TestCity levels disagreed by 16 between two identical rebuilds while their
falloff RATIOS agreed to 0.06 - a ratio survives a uniform ramp, a level
does not.
"""
import time

import img, cap2, os, sys

FLOOR = 4.3          # noise floor 3.65-3.86 measured over 5 idle captures, + margin
MAX_TRIES = 12
BASELINE_S = 60.0    # how far back the drift test looks
DRIFT = 0.5          # mean levels of movement allowed across BASELINE_S
SPACING = 10.0       # seconds between captures when drift-testing


def drifting(hist, now_mean, baseline_s=BASELINE_S, drift=DRIFT):
    """Is the level still ramping, judged against a frame baseline_s old?

    hist is [(t, mean), ...] oldest first. Returns None when there is not yet
    enough history to judge - which is NOT the same as 'settled'.
    """
    if not hist:
        return None
    t_now = hist[-1][0]
    old = [(t, m) for t, m in hist if t_now - t >= baseline_s]
    if not old:
        return None
    return abs(now_mean - old[-1][1]) >= drift

def settled(tag, view='zoom', verbose=True, drift_test=False, max_tries=None):
    """Capture until stable; return the settled Img and its path.

    drift_test=False keeps the original consecutive-frame behaviour, which is
    adequate for an A/B inside ONE warm session - both sides ride the same
    ramp, so it cancels. Pass drift_test=True after a LEVEL LOAD or any other
    cold start, where the ramp is the thing being measured: it spaces the
    captures and additionally requires agreement with a frame BASELINE_S old.
    """
    tries = max_tries or (MAX_TRIES if not drift_test else 40)
    prev = None; quiet = 0; hist = []
    t0 = time.time()
    for i in range(tries):
        p = '%s_s%d.png' % (tag, i)
        cap2.capture(p, view)
        cur = img.load(p)
        m = img.mean(cur.px)
        hist.append((time.time() - t0, m))
        if prev is not None:
            d = img.mean_abs_diff(prev, cur)
            if verbose: print('    settle %d: d=%.2f mean=%.2f' % (i, d, m))
            # TWO consecutive quiet frames, not one. A transient can pass
            # through a momentarily small delta on its way somewhere else.
            quiet = quiet + 1 if d < FLOOR else 0
            if quiet >= 2:
                if not drift_test:
                    return cur, p, i+1
                dr = drifting(hist, m)
                if dr is False:
                    return cur, p, i+1
                if verbose:
                    print('      still %s over the %.0fs baseline'
                          % ('drifting' if dr else 'accumulating history',
                             BASELINE_S))
        elif verbose:
            print('    settle 0: mean=%.2f' % m)
        prev = cur
        if drift_test:
            time.sleep(SPACING)
    raise SystemExit('%s never settled after %d captures' % (tag, tries))

def floor(n=5, view='zoom'):
    """Measure the idle capture-to-capture noise floor right now."""
    ims = []
    for i in range(n):
        p = 'floor_%d.png' % i
        cap2.capture(p, view)
        ims.append(img.load(p))
    ds = [img.mean_abs_diff(ims[i], ims[i+1]) for i in range(len(ims)-1)]
    return ds

# Known answer: a SLOW RAMP must be reported as still drifting even though
# every consecutive step is tiny. This is the exact shape measured on the
# bench, and the old consecutive-delta test passes it from the first sample.
def _selftest():
    ramp = [(10.0 * i, 64.91 + 0.135 * i) for i in range(26)]   # ~+0.14/sample
    for i in range(1, len(ramp)):
        step = abs(ramp[i][1] - ramp[i - 1][1])
        assert step < FLOOR, 'the ramp must be invisible to a consecutive test'
    mid = ramp[:13]
    assert drifting(mid, mid[-1][1]) is True, 'a ramp must read as drifting'
    plateau = [(10.0 * i, 67.50) for i in range(26)]
    assert drifting(plateau, plateau[-1][1]) is False, 'a plateau must settle'
    assert drifting(ramp[:2], ramp[1][1]) is None, 'too little history is not settled'
    print('settle drift self-check: ramp caught, plateau passes, short history '
          'is undecided   pass')


if __name__ == '__main__':
    _selftest()
    ds = floor()
    print('idle noise floor: ' + '  '.join('%.3f' % d for d in ds))
    print('max %.3f' % max(ds))
