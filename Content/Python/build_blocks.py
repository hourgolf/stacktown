#!/usr/bin/env python3
"""Build one or more blocks additively, then re-run the shared steps, then re-run the shared steps.

Additive on purpose: it does NOT wipe. The shared steps that follow
(elevations, roles, cores, practicals) each clear only their own prefix and
then rebuild for every block in the city table, so running them here brings
blocks A, B and C to the same state without a full rebuild of the street.
"""
import os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RUNG = os.path.join(ROOT, 'Tools', 'rung.sh')
sys.path.insert(0, HERE)
for f in ('.mcp_sid',):
    try: os.remove(os.path.join(HERE, f))
    except OSError: pass
from city import BLOCKS
WANT = set(sys.argv[1:]) or {'C'}
WANT = {n for b in BLOCKS for n in [b['name']] if any(n.startswith(w) for w in WANT)}
from genbuild import build as genbuild
import zones
import step_elevations


def ue(script, label):
    t = time.time()
    r = subprocess.run([RUNG, script], capture_output=True, text=True, cwd=HERE)
    ok = 'success: True' in r.stdout
    print('  %-24s %5.1fs %s' % (label, time.time() - t, 'ok' if ok else 'FAILED'))
    for l in r.stdout.splitlines():
        if l.startswith('[Info]') and 'guard' not in l and l[7:].strip():
            print('      ' + l[7:])
    if not ok:
        print('      ' + (r.stdout[-400:] or r.stderr[-400:]))
    return ok


t0 = time.time()
for blk in BLOCKS:
    if blk['name'] not in WANT:
        continue
    print('=== block %s: origin %s yaw %.0f ===' % (blk['name'], blk['origin'], blk['yaw']))
    for spec in blk['lots']:
        # kind dispatches the way style does inside kind='gen'. 'av' is handled
        # by its own step; anything else is an open zone, not a building.
        if spec['kind'] == 'gen':
            genbuild(spec, origin=blk['origin'], yaw=blk['yaw'])
        elif spec['kind'] != 'av':
            zones.build(spec, origin=blk['origin'], yaw=blk['yaw'])
print('  generated in %.0fs' % (time.time() - t0))

print('=== exposed flank elevations (all blocks) ===')
t = time.time(); step_elevations.run(); print('  flanks in %.0fs' % (time.time() - t))
print('=== shared steps ===')
ue('step_roles.py', 'materials by role')
ue('step_cores3.py', 'solid cores')
ue('practicals.py', 'practicals')
print('=== street lamps ===')
ue('wipe_lamps.py', 'clear old lamps')
import street_lamps
street_lamps.run()
ue('lamp_lights.py', 'lamp lights')
# Second role sweep: lamps are created above, after the first one, so this is
# what binds them. Idempotent - it re-assigns, it does not accumulate.
ue('step_roles.py', 'role sweep (late actors)')
print('=== checks ===')
ue('check_block.py', 'geometry + party walls')
ue('gap_check2.py', 'no hollow facades')
# Whole-level invariants run last, after every dressing pass. Self-tests first.
ue('invariants.py', 'invariants')
print('\n%s complete in %.0fs' % (','.join(sorted(WANT)), time.time() - t0))
