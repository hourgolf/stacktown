#!/usr/bin/env python3
"""Rebuild only block F, the way rebuild_zones.py rebuilds only the open lots."""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _path  # noqa: F401
import city, genbuild

RUNG = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'Tools', 'rung.sh')
r = subprocess.run([RUNG, 'wipe_F.py'], capture_output=True, text=True, cwd=HERE)
if 'success: True' not in r.stdout:
    raise SystemExit('wipe_F.py FAILED - refusing to build on top of the old set\n'
                     + (r.stdout[-400:] or r.stderr[-400:]))
print([l[7:] for l in r.stdout.splitlines() if 'removed' in l][0])

blk = next(b for b in city.BLOCKS if b['name'] == 'F')
n = sum(genbuild.build(s, origin=blk['origin'], yaw=blk['yaw']) for s in blk['lots'])
print('block F: %d boxes' % n)
