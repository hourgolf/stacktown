"""Illuminance spread across the board, measured on the CENTRAL crop.

The capture is letterboxed - the viewport pane is 1.56:1 and the frame is not -
so whole-frame crushed counts are dominated by the black bars, not the scene.
Everything here is measured on the middle 80% of the image.
"""
import img, cap2, sys

# A lighting change makes Lumen re-converge, and it is not quick over a board
# this size. An earlier sweep read the street at mean 32.0, then 22.5, then
# 22.7 for progressively BRIGHTER rigs - the 32.0 was simply an unconverged
# frame. Settle before measuring, or the sweep measures convergence instead of
# light.
FLOOR = 4.6
def settled(view, tag, max_tries=14):
    prev = None; quiet = 0
    for i in range(max_tries):
        p = '%s_%d.png' % (tag, i)
        cap2.capture(p, view)
        cur = img.load(p)
        if prev is not None:
            d = img.mean_abs_diff(prev, cur)
            quiet = quiet + 1 if d < FLOOR else 0
            if quiet >= 2:
                return cur, i + 1
        prev = cur
    return prev, max_tries

VIEWS = sys.argv[1:] or ['zoom', 'streetC', 'deco', 'board']

def crop(im):
    return (int(im.w*0.10), int(im.h*0.10), int(im.w*0.90), int(im.h*0.90))

print('%-10s %8s %8s %8s' % ('view', 'mean', 'blown%', 'crushed%'))
rows = []
for v in VIEWS:
    # MEDIAN OF MANY, not "settled". The scene drifts upward for ~16 frames and
    # then destabilises, so a two-quiet-frames test fires partway up the curve
    # and reports convergence as light. Measured curve on this street: 39.09
    # rising to 41.17 over 16 frames, then oscillating 37-39. A median over a
    # long burst is the only statistic here that repeats.
    vals = []
    for i in range(12):
        p = 'sp_%s_%d.png' % (v, i)
        cap2.capture(p, v)
        if i >= 4:
            vals.append(img.load(p))
    vals.sort(key=lambda a: img.mean(a.px))
    im, nshots = vals[len(vals)//2], 12
    x0, y0, x1, y1 = crop(im)
    px = img.patch(im, x0, y0, x1, y1)
    n = float(len(px))
    mean = sum(px)/n
    blown = 100.0*sum(1 for p in px if p >= 250)/n
    crush = 100.0*sum(1 for p in px if p <= 4)/n
    rows.append((v, mean, blown, crush))
    print('%-10s %8.1f %8.4f %8.4f   (median of 8)' % (v, mean, blown, crush))
ms = [r[1] for r in rows]
print('\nmean spread %.1f .. %.1f  (ratio %.2fx)' % (min(ms), max(ms), max(ms)/max(min(ms), 0.01)))
print('gate: blown <= 0.02%%, crushed <= 0.05%%')
