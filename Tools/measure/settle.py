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
"""
import img, cap2, os, sys

FLOOR = 4.3          # noise floor 3.65-3.86 measured over 5 idle captures, + margin
MAX_TRIES = 12

def settled(tag, view='zoom', verbose=True):
    """Capture until stable; return the settled Img and its path."""
    prev = None; quiet = 0
    for i in range(MAX_TRIES):
        p = '%s_s%d.png' % (tag, i)
        cap2.capture(p, view)
        cur = img.load(p)
        if prev is not None:
            d = img.mean_abs_diff(prev, cur)
            if verbose: print('    settle %d: d=%.2f mean=%.2f' % (i, d, img.mean(cur.px)))
            # TWO consecutive quiet frames, not one. A transient can pass
            # through a momentarily small delta on its way somewhere else.
            quiet = quiet + 1 if d < FLOOR else 0
            if quiet >= 2:
                return cur, p, i+1
        elif verbose:
            print('    settle 0: mean=%.2f' % img.mean(cur.px))
        prev = cur
    raise SystemExit('%s never settled after %d captures' % (tag, MAX_TRIES))

def floor(n=5, view='zoom'):
    """Measure the idle capture-to-capture noise floor right now."""
    ims = []
    for i in range(n):
        p = 'floor_%d.png' % i
        cap2.capture(p, view)
        ims.append(img.load(p))
    ds = [img.mean_abs_diff(ims[i], ims[i+1]) for i in range(len(ims)-1)]
    return ds

if __name__ == '__main__':
    ds = floor()
    print('idle noise floor: ' + '  '.join('%.3f' % d for d in ds))
    print('max %.3f' % max(ds))
