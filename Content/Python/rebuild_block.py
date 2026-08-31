#!/usr/bin/env python3
"""Rebuild one block, the way rebuild_zones.py rebuilds only the open lots.

    python3 rebuild_block.py F G
"""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _path  # noqa: F401
import city, genbuild, zones

RUNG = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'Tools', 'rung.sh')
WANT = sys.argv[1:] or ['F']
names = [l['name'] for b in city.BLOCKS if b['name'] in WANT for l in b['lots']]
ZONES = [l['name'] for b in city.BLOCKS if b['name'] in WANT for l in b['lots']
         if l.get('kind') in ('plaza', 'green', 'park', 'vacant')]
import tempfile
open(os.path.join(tempfile.gettempdir(), 'stacktown_wipe_lots.txt'),
     'w').write(','.join(names))
r = subprocess.run([RUNG, 'wipe_lots.py'], capture_output=True, text=True, cwd=HERE)
if 'success: True' not in r.stdout:
    raise SystemExit('wipe_lots.py FAILED - refusing to build on top of the old set\n'
                     + (r.stdout[-500:] or r.stderr[-500:]))
print([l[7:] for l in r.stdout.splitlines() if 'removed' in l][0])

total = 0
for blk in city.BLOCKS:
    if blk['name'] not in WANT:
        continue
    # A block can hold zones as well as buildings. Feeding a zone lot to
    # genbuild raises KeyError('floors') and kills the rebuild HALF WAY, which
    # leaves the block partly destroyed - dispatch on kind, as build_blocks
    # already does.
    for sp in blk['lots']:
        k = sp.get('kind')
        if k in ('plaza', 'green', 'park', 'vacant'):
            total += zones.build(sp, origin=blk['origin'], yaw=blk['yaw'])
        elif k == 'gen':
            total += genbuild.build(sp, origin=blk['origin'], yaw=blk['yaw'])
print('rebuilt %s: %d boxes' % (','.join(WANT), total))
