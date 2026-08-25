#!/usr/bin/env python3
"""Bake every recipe at every tier into the catalogue.

    python3 bake_catalogue.py [recipe ...]

Builds each one far off the board, merges it to a StaticMesh, and removes the
temporary actors. The board is never touched.
"""
import os, sys, json, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _path  # noqa: F401
import genbuild, recipes

RUNG = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'Tools', 'rung.sh')
OUT = '/Game/Stacktown/Baked'
STAGE = (0.0, 60000.0, 0.0)          # well clear of the board
WIDTHS = {'cottage': 820.0, 'walkup': 1420.0}

want = sys.argv[1:] or list(recipes.RECIPES)
made = []
for rid in want:
    w = WIDTHS[rid]
    for t in range(recipes.tier_count(rid)):
        tag = 'BAKE%s%d' % (rid.capitalize(), t)
        spec = recipes.spec_for(rid, t, tag, 0.0, w)
        genbuild.build(spec, origin=STAGE, yaw=0.0)
        # bind the roles BEFORE merging, or every component arrives on the same
        # default material and the merge compacts it to one slot - which is
        # exactly what the first bake produced
        json.dump({tag: {'wall': spec.get('wall'),
                         'roofmat': spec.get('roofmat')}},
                  open(os.path.join(tempfile.gettempdir(),
                                    'stacktown_role_overrides.json'), 'w'))
        rr = subprocess.run([RUNG, 'step_roles.py'], capture_output=True,
                            text=True, cwd=HERE)
        if 'success: True' not in rr.stdout:
            raise SystemExit('role sweep failed\n' + rr.stdout[-500:])
        labels = [l % tag for l in ('BLD2_%s_H', 'BLD2_%s_A', 'PLOT_%s')]
        asset = recipes.asset_name(rid, t, w)
        json.dump({'labels': labels, 'out': '%s/%s' % (OUT, asset)},
                  open(os.path.join(tempfile.gettempdir(),
                                    'stacktown_bake_job.json'), 'w'))
        r = subprocess.run([RUNG, 'bake_merge.py'], capture_output=True,
                           text=True, cwd=HERE)
        line = [l[7:] for l in r.stdout.splitlines() if l.startswith('[Info] BAKED')]
        if 'success: True' not in r.stdout or not line:
            raise SystemExit('bake failed for %s t%d\n%s'
                             % (rid, t, r.stdout[-700:] or r.stderr[-700:]))
        print('  ' + line[0])
        made.append(asset)
        # clear the staging actors before the next one
        open(os.path.join(tempfile.gettempdir(), 'stacktown_wipe_lots.txt'),
             'w').write(tag)
        subprocess.run([RUNG, 'wipe_lots.py'], capture_output=True, text=True, cwd=HERE)
os.remove(os.path.join(tempfile.gettempdir(), 'stacktown_role_overrides.json'))
print('catalogue: %d baked meshes' % len(made))
