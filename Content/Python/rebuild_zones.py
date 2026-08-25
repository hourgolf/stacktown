#!/usr/bin/env python3
"""Rebuild only the ZONE_ actors from the city table.

The zone layout changes more often than the blocks around it, and a full block
rebuild to move a flower bed is both slow and a chance to break something that
was working. Runs locally over MCP, exactly as build_blocks.py drives
street_lamps.

    python3 rebuild_zones.py
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _path  # noqa: F401
import zones
from city import BLOCKS

import subprocess
ROOT = os.path.dirname(os.path.dirname(HERE))
RUNG = os.path.join(ROOT, 'Tools', 'rung.sh')

# The wipe goes through rung.sh, NOT over MCP. The MCP enumeration returned
# something unparseable here and the failure was swallowed, so the rebuild
# stacked a second set of zones on top of the first.
r = subprocess.run([RUNG, 'wipe_zones.py'], capture_output=True, text=True, cwd=HERE)
line = [l[7:] for l in r.stdout.splitlines() if 'removed' in l]
if 'success: True' not in r.stdout:
    raise SystemExit('wipe_zones.py FAILED - refusing to build on top of the old set\n'
                     + (r.stdout[-500:] or r.stderr[-500:]))
print(line[0] if line else 'wipe reported nothing')

made = 0
for blk in BLOCKS:
    for spec in blk['lots']:
        if spec.get('kind') in ('plaza', 'green', 'park', 'vacant'):
            made += zones.build(spec, origin=blk['origin'], yaw=blk['yaw'])
print('rebuilt %d zone boxes' % made)
