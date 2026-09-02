#!/usr/bin/env python3
"""Bake THE WOODEN CATALOGUE - the 36 masses phase F resolves to.

    python3 Content/Python/mk_woodcat.py            all 36
    python3 Content/Python/mk_woodcat.py w1230      just one width

The look study's 20 masses were sized for a demo board (600-1000 uu) and the
flagship's lots are 820-2460, so a mass from that set covers as little as 41%
of a wide lot's frontage. These are the same vocabulary re-parameterised onto
the FLAGSHIP WIDTH LADDER, so every catalogue key resolves to a mass that
fits its parcel exactly.

woodmap.py owns WHICH mass a key resolves to. This owns what those masses ARE.
The two agree by construction: the names are built by woodmap.asset_name, so
a mass this bakes and a mass woodmap asks for cannot drift apart.
"""
import contextlib
import io
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _path  # noqa: F401,E402
import genbuild  # noqa: E402
import woodmap  # noqa: E402

RUNG = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'Tools', 'rung.sh')
OUT = '/Game/Stacktown/BakedWood'
TMP = tempfile.gettempdir()
CHAMFER = 14.0

# height and gesture per band, carried over from the look study's vocabulary
# so the catalogue looks like the board the owner has been judging
BAND = {
    'flat':     dict(h=(320, 900),   form=('bar', 'ell', None),
                     stages=[(1.0, 0.0)]),
    'setback1': dict(h=(1200, 2600), form=('podium', 'ell', 'stepped'),
                     stages=[(0.72, 0.0), (0.28, 66)]),
    'setback2': dict(h=(2800, 4600), form=('podium', 'crown', 'ell'),
                     stages=[(0.55, 0.0), (0.27, 76), (0.18, 96)]),
    'tower':    dict(h=(5000, 6600), form=('crown', 'stepped', 'crown'),
                     stages=[(0.68, 0.0), (0.32, 60)]),
}


def jobs():
    out = []
    for w in woodmap.WIDTHS:
        for b in woodmap.BANDS:
            out.append((w, b, False))
    for w in woodmap.CORNER_WIDTHS:
        for b in woodmap.BANDS:
            out.append((w, b, True))
    return out


def main():
    only = [a for a in sys.argv[1:] if not a.startswith('-')]
    todo = [j for j in jobs()
            if not only or ('w%d' % int(j[0])) in only or j[1] in only]
    print('%-30s %6s %s' % ('asset', 'parts', ''))
    ok = 0
    for w, band, corner in todo:
        spec_b = BAND[band]
        rnd = random.Random(zlib.crc32(('%d%s%d' % (w, band, corner)).encode()))
        h = spec_b['h'][0] + rnd.random() * (spec_b['h'][1] - spec_b['h'][0])
        name = woodmap.asset_name(w, band, corner)
        # SPECIES IS NOT BAKED IN. woodmap picks the timber per RECIPE, and
        # the material is bound per instance, so one mass serves every species
        # - which is why 36 masses cover a catalogue of hundreds of keys.
        spec = dict(style='mass', name=name.replace('SM_', ''),
                    width=float(w),
                    depth=woodmap.DEPTH_CORNER if corner else woodmap.DEPTH_BASE,
                    height=h, stages=spec_b['stages'],
                    cap=0.0, seed=zlib.crc32(name.encode()) % 9999,
                    plinth=0.0, hand_tolerance=True,
                    form=spec_b['form'][int(rnd.random() * 3) % 3],
                    roof='furniture',
                    wall='MI_wood_oak', roofmat='MI_wood_oak',
                    trim='MI_wood_oak')
        genbuild.record()
        with contextlib.redirect_stdout(io.StringIO()):
            genbuild.build(spec)
        rec = genbuild.drain()
        json.dump({'boxes': rec, 'out': '%s/%s' % (OUT, name),
                   'wall': spec['wall'], 'roofmat': spec['roofmat'],
                   'trim': spec['trim'], 'panel_overrides': {},
                   'chamfer': CHAMFER},
                  open(os.path.join(TMP, 'stacktown_fastbake_job.json'), 'w'))
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
        if not line or 'success: True' not in r.stdout:
            print('%-30s FAILED: %s' % (name,
                  (r.stdout[-200:] or r.stderr[-200:]).replace('\n', ' ')))
            continue
        ok += 1
        print('%-30s %s' % (name, line[0].split('FASTBAKED')[-1].strip()))
    print('\n%d of %d baked into %s' % (ok, len(todo), OUT))
    # THE CATALOGUE AND THE MAPPING MUST AGREE, or the pointer swap resolves
    # to assets that do not exist - which is the failure the owner just hit
    # from the other direction.
    if not only:
        want = set(woodmap.catalogue())
        got = set(woodmap.asset_name(w, b, c) for w, b, c in jobs())
        assert want == got, 'bake table and woodmap disagree: %s' % (
            want.symmetric_difference(got))
        print('bake table matches woodmap.catalogue() exactly (%d assets)'
              % len(want))
    return 0 if ok == len(todo) else 1


if __name__ == '__main__':
    sys.exit(main())
