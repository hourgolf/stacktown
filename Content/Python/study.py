#!/usr/bin/env python3
"""Build the material study wall: six panels, one variable apart.

    python3 study.py

Each panel is the SAME geometry - a wall with a pier either side, a band
course, and one recessed window with frame, cill and glazing bars - because
the question is not "what does this colour look like" but "does the CARD
READ at building distance", and a flat swatch cannot answer that. The reveal
shadow and the band offset are most of what carries the look.

Built through the fast path, which is the point of having built it: this is
six seconds now, and it was six minutes an hour ago.
"""
import os, sys, json, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _path  # noqa: F401
import genbuild

ROOT = os.path.dirname(os.path.dirname(HERE))
RUNG = os.path.join(ROOT, 'Tools', 'rung.sh')
TMP = tempfile.gettempdir()
OUT = '/Game/Stacktown/Baked/SM_MatStudy'

PANELS = ['MI_st0_base', 'MI_st1_darker', 'MI_st2_paper',
          'MI_st3_coarse', 'MI_st4_seams', 'MI_st5_wear']
PW, PH, PD, GAP = 430.0, 700.0, 60.0, 40.0


def panel(a, i, x0):
    """One wall bay: piers, band, and a recessed window. Names carry a per
    panel suffix so the material map can give each its own variant."""
    t = 'S%d' % i
    g = genbuild
    x1 = x0 + PW
    # the wall plane, and a pier at each end standing proud
    g.box(a, 'Wall_%s_Field' % t, x0, x1, 0, PD, 0, PH)
    g.box(a, 'Wall_%s_PierL' % t, x0, x0 + 52, -14, PD, 0, PH)
    g.box(a, 'Wall_%s_PierR' % t, x1 - 52, x1, -14, PD, 0, PH)
    g.box(a, 'Band_%s_Course' % t, x0 - 6, x1 + 6, -20, PD, PH - 44, PH - 14)
    g.box(a, 'Band_%s_Plinth' % t, x0 - 6, x1 + 6, -20, PD, 0, 40)
    # a recessed opening: glass set back, frame proud, cill proud again
    wx0, wx1 = x0 + 92, x1 - 92
    wz0, wz1 = 150.0, PH - 150.0
    gy = 27.0
    g.box(a, 'Glass_%s' % t, wx0 + 6, wx1 - 6, gy, gy + 2, wz0 + 6, wz1 - 6)
    g.box(a, 'Interior_%s' % t, wx0, wx1, gy + 20, gy + 26, wz0, wz1)
    for s, (ax0, ax1) in (('L', (wx0, wx0 + 6)), ('R', (wx1 - 6, wx1))):
        g.box(a, 'Frame_%s_%s' % (t, s), ax0, ax1, gy - 8, gy + 2, wz0, wz1)
    g.box(a, 'Frame_%s_T' % t, wx0, wx1, gy - 8, gy + 2, wz1 - 6, wz1)
    g.box(a, 'Frame_%s_Cill' % t, wx0 - 8, wx1 + 8, gy - 16, gy + 2, wz0 - 8, wz0)
    mx = (wx0 + wx1) / 2.0
    g.box(a, 'Mullion_%s_V' % t, mx - 3, mx + 3, gy - 6, gy + 1, wz0, wz1)
    mz = wz0 + (wz1 - wz0) * 0.62
    g.box(a, 'Mullion_%s_H' % t, wx0, wx1, gy - 6, gy + 1, mz - 3, mz + 3)


genbuild.record()
a = genbuild.mkactor('STUDY_Wall', (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
for i in range(len(PANELS)):
    panel(a, i, i * (PW + GAP))
rec = genbuild.drain()

# each panel's Wall_/Band_ takes its own variant; everything else is shared
overrides = {}
for i, m in enumerate(PANELS):
    overrides['S%d' % i] = m
json.dump({'boxes': rec, 'out': OUT, 'wall': PANELS[0],
           'roofmat': 'MI_shingle_grey', 'panel_overrides': overrides},
          open(os.path.join(TMP, 'stacktown_fastbake_job.json'), 'w'))
r = subprocess.run([RUNG, 'fastbake.py'], capture_output=True, text=True, cwd=HERE)
line = [l[7:] for l in r.stdout.splitlines() if 'FASTBAKED' in l]
if 'success: True' not in r.stdout or not line:
    raise SystemExit('study bake failed\n' + (r.stdout[-900:] or r.stderr[-900:]))
print(line[0])
print('  %d panels, %.0f uu wide overall' % (len(PANELS),
                                             len(PANELS) * (PW + GAP)))
