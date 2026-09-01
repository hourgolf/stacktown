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

# six blocks spanning the form vocabulary AND the tone ladder, so one frame
# can answer edges, wear and species together
SET = [
    ('shed',    'maple',  dict(width=640, depth=620, height=340,
                               stages=[(1.0, 0.0)], cap=0.0)),
    ('low',     'ash',    dict(width=900, depth=760, height=760,
                               stages=[(1.0, 0.0)], cap=0.0)),
    ('midrise', 'oak',    dict(width=820, depth=800, height=1740,
                               stages=[(0.72, 0.0), (0.28, 74)], cap=110.0)),
    ('setback', 'cherry', dict(width=880, depth=840, height=2900,
                               stages=[(0.58, 0.0), (0.42, 96)], cap=0.0)),
    ('ziggurat', 'sapele', dict(width=980, depth=940, height=4100,
                                stages=[(0.46, 0.0), (0.30, 104),
                                        (0.24, 118)], cap=180.0)),
    ('tower',   'walnut', dict(width=720, depth=700, height=6400,
                               stages=[(0.70, 0.0), (0.30, 66)], cap=260.0)),
]


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
                    wall='MI_wood_%s' % sp, roofmat='MI_wood_%s' % sp,
                    trim='MI_wood_%s' % sp)
        genbuild.record()
        with contextlib.redirect_stdout(io.StringIO()):
            genbuild.build(spec)
        rec = genbuild.drain()
        asset = 'SM_Mass_%s' % name
        json.dump({'boxes': rec, 'out': '%s/%s' % (OUT, asset),
                   'wall': spec['wall'], 'roofmat': spec['roofmat'],
                   'trim': spec['trim'], 'panel_overrides': {}},
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
