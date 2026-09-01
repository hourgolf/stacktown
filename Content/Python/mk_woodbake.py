#!/usr/bin/env python3
"""Bake a SMALL set of direction-B masses, so edges and wear are real.

    python3 Content/Python/mk_woodbake.py

WHY THIS EXISTS - the finding that produced it. The live rig's blocks are
genbuild.box -> add_cube: PLAIN SHARP BOXES. Chamfering happens only in
fastbake. And the master's edge wear is saturate((1 - max|n|)/0.30), so on a
box whose every face is axis-aligned:

    flat face of a sharp box   max|n| 1.000   wear 0.00
    45-degree chamfer facet    max|n| 0.707   wear 0.98

EVERY SURFACE ON THE LIVE RIG SCORES ZERO. The edge-wear system is inert
there, and with it D3's whole patina design, which drives EdgeWearLift. Every
look note the owner gave on the live boards was about a surface with its edge
treatment switched off.

So the LOOK-JUDGING set is baked (owner, 2026-09-01, amending D11's
disposable-rig lock for this purpose) while the live rig stays the layout and
massing tool. Six blocks, not fifty-four: enough to judge edges, wear and
patina, few enough that the bake policy's editor-window cost stays trivial.

BakedWood, not Baked - the namespace ratified when the twin was designed:
the fork lives in the CATALOGUE, never in the key.
"""
import json
import os
import subprocess
import sys
import tempfile
import random
import zlib
import contextlib
import io
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _path  # noqa: F401,E402
import genbuild  # noqa: E402

RUNG = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'Tools', 'rung.sh')
OUT = '/Game/Stacktown/BakedWood'
TMP = tempfile.gettempdir()

# TWENTY BLOCKS. Six read as a cluster; a woodblock town needs population,
# and the owner asked for the count to rise at the quality bar the six held.
#
# PROPORTIONS ARE DELIBERATELY UNCHANGED. The 9:1 tower is a needle and I said
# so; the owner's call was to leave it and judge again once there is a skyline
# rather than a huddle. So this widens the POPULATION, not the ratios - if the
# proportions still read wrong at twenty, that is a cleaner verdict than one
# taken at six.
#
# Generated from a seeded table rather than hand-listed, so the set is
# reproducible from this file and a future change is a change to the RULE.
_R = random.Random(20260901)
_SPECIES = ('maple', 'pine', 'ash', 'oak', 'cherry', 'sapele', 'walnut')

# (count, height range, stage plan) - the form vocabulary, weighted so low
# buildings dominate, which is what a town actually looks like
_FORMS = [
    (7, (300, 900), 'flat'),
    (6, (1200, 2600), 'setback1'),
    (4, (2800, 4600), 'setback2'),
    (3, (5000, 6600), 'tower'),
]

# WHICH GESTURE EACH TIER GETS. The owner's note was that the blocks read as
# "blocks/monoliths instead of distinctly styled buildings" - about variety of
# SHAPE, and explicitly not about height. So heights are untouched and the
# gesture varies instead.
#
# Low buildings take the horizontal moves (bar, ell) because that is what the
# reference's low blocks are and this generator had none - every block was
# upright. Tall ones take podium and stepped, and a couple stay plain prisms:
# if every building has a gesture, the gesture stops being one.
_GESTURE = {
    'flat':     ('bar', 'ell', 'bar', None, 'ell', 'bar', 'ell'),
    'setback1': ('podium', 'ell', 'stepped', 'podium', None, 'bar'),
    'setback2': ('podium', 'stepped', 'podium', 'ell'),
    'tower':    ('podium', 'stepped', None),
}


def _cap_for(h, rnd):
    """Rooftop cap. FIVE OUTCOMES AND A BARE PLURALITY - a flat top is the
    commonest thing on a carved block, and giving every building a hat is its
    own repetition. At six blocks one centred cap read as variety; the owner
    flagged it as a stamp, and simple surfaces make silhouette carry more."""
    if h < 900:
        return 0.0
    r = rnd.random()
    if r < 0.34:
        return 0.0
    if r < 0.62:
        return 70.0 + 60.0 * rnd.random()
    if r < 0.80:
        return 150.0 + 90.0 * rnd.random()
    if r < 0.92:
        return 44.0 + 26.0 * rnd.random()
    return 240.0 + 140.0 * rnd.random()


def _build_set():
    out = []
    i = 0
    for count, (hlo, hhi), plan in _FORMS:
        for _ in range(count):
            w = 600.0 + _R.randrange(9) * 50.0
            d = w - 60.0 + _R.randrange(5) * 30.0
            h = hlo + _R.random() * (hhi - hlo)
            if plan == 'flat':
                stages = [(1.0, 0.0)]
            elif plan == 'setback1':
                stages = [(0.72, 0.0), (0.28, 60.0 + _R.randrange(5) * 12.0)]
            elif plan == 'setback2':
                stages = [(0.55, 0.0), (0.27, 70.0 + _R.randrange(5) * 14.0),
                          (0.18, 90.0 + _R.randrange(5) * 16.0)]
            else:
                stages = [(0.68, 0.0), (0.32, 55.0 + _R.randrange(4) * 12.0)]
            gst = _GESTURE[plan]
            out.append(('b%02d' % i, _SPECIES[i % len(_SPECIES)],
                        dict(width=w, depth=d, height=h, stages=stages,
                             cap=_cap_for(h, _R),
                             form=gst[len([o for o in out
                                           if o[0]]) % len(gst)])))
            i += 1
    return out


SET = _build_set()

# A CARVED ARRIS, NOT A CARD EDGE. fastbake defaults to 4 uu, which is the
# flagship's card value and subtends 0.6% of a 640 uu wooden face - present in
# the mesh, invisible in the frame. 14 uu is what a chisel leaves on a block
# this size. fastbake clamps it to 0.35 x the thinnest dimension, so a small
# part cannot be collapsed by it.
CHAMFER = 14.0

def main():
    only = [a for a in sys.argv[1:] if not a.startswith('-')]
    todo = [b for b in SET if not only or b[0] in only]
    if only and not todo:
        raise SystemExit('no such block: %s (have %s)'
                         % (', '.join(only), ', '.join(b[0] for b in SET)))
    print('%-10s %-8s %6s %7s  %s' % ('block', 'species', 'parts', 'asset', ''))
    ok = 0
    for name, sp, geom in todo:
        spec = dict(geom, style='mass', name='Mass%s' % name.capitalize(),
                    # CRC32, NOT hash(). Python randomises str hashing per
                    # process, so hash(name) reseeded every block on every run
                    # and the baked asset could not be reproduced from this
                    # script - the one thing a generated asset must do.
                    seed=zlib.crc32(name.encode()) % 9999,
                    # NO PER-BUILDING PLINTH. Each mass carried a 24 uu skirt
                    # proud by 18, which is the owner's own note from the last
                    # board - "35 individual plinths tiled the board like
                    # trays". A city block shares ONE plot; the set script
                    # lays it, so the block is a plain carved solid.
                    plinth=0.0,
                    # THE POINT OF BAKING: chamfer needs geometry, and the
                    # hand tolerance is direction B's per D12
                    hand_tolerance=True,
                    # ROOF FURNITURE. B1 spends its detail budget on roofs,
                    # not walls - two to five elements on nearly every block -
                    # and this generator allowed one optional cap, which the
                    # owner called repetitive at twenty. Costs +75% parts
                    # across this set (55 -> 96), quoted before it was spent.
                    roof='furniture',
                    wall='MI_wood_%s' % sp, roofmat='MI_wood_%s' % sp,
                    trim='MI_wood_%s' % sp)
        genbuild.record()
        with contextlib.redirect_stdout(io.StringIO()):
            genbuild.build(spec)
        rec = genbuild.drain()
        asset = 'SM_Mass_%s' % name
        json.dump({'boxes': rec, 'out': '%s/%s' % (OUT, asset),
                   'wall': spec['wall'], 'roofmat': spec['roofmat'],
                   'trim': spec['trim'], 'panel_overrides': {},
                   'chamfer': CHAMFER},
                  open(os.path.join(TMP, 'stacktown_fastbake_job.json'), 'w'))
        # RETRY ON THE AMBIGUITY, NOT ON EVERYTHING. Two editors are running
        # on this machine and rung's discovery resolves intermittently - four
        # of six blocks failed the first pass and two succeeded, same command.
        # An unconditional retry would also re-run genuine bake failures, so
        # this retries only that one message and reports anything else once.
        line, r = [], None
        for _try in range(4):
            r = subprocess.run([RUNG, 'fastbake.py'], capture_output=True,
                               text=True, cwd=HERE)
            line = [l.strip() for l in r.stdout.splitlines() if 'FASTBAKED' in l]
            if line and 'success: True' in r.stdout:
                break
            if 'AMBIGUOUS' not in (r.stdout + r.stderr):
                break
            time.sleep(2.0)
        if 'success: True' not in r.stdout or not line:
            print('%-10s %-8s FAILED: %s' % (name, sp,
                  (r.stdout[-260:] or r.stderr[-260:]).replace('\n', ' ')))
            continue
        ok += 1
        print('%-10s %-8s %s' % (name, sp, line[0]))
    print('\n%d of %d baked into %s' % (ok, len(todo), OUT))
    return 0 if ok == len(todo) else 1


if __name__ == '__main__':
    sys.exit(main())
