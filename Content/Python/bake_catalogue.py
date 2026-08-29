#!/usr/bin/env python3
"""Bake every recipe at every tier into the catalogue.

    python3 bake_catalogue.py [recipe ...]
    python3 bake_catalogue.py --force          bake even if the gate fails
    python3 bake_catalogue.py --width=1230     just one parcel width

Builds each one far off the board, GATES it while it is still boxes, merges it
to a StaticMesh, STAMPS the verdict onto the asset, and removes the temporary
actors. The board is never touched.

The gate sits between the role sweep and the merge because that is the only
moment anything can see the model: afterwards it is one component and every
rule in the suite goes blind. --force exists for deliberately baking a known
failure to look at it, and it stamps Gate=FAIL rather than lying.
"""
import os, sys, json, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _path  # noqa: F401
import genbuild, recipes, step_elevations, cores

RUNG = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'Tools', 'rung.sh')
OUT = '/Game/Stacktown/Baked'
STAGE = (0.0, 60000.0, 0.0)          # well clear of the board
# widths come from the recipe now - each declares which of the shared
# S/M/L ladder it accepts, so a works refusing a small parcel is data
# rather than a special case here.

# PREFLIGHT: PIE BLOCKS ACTOR CREATION, so find out at second zero.
#
# On 29 Aug both verification bakes died on their first actor because a play
# session was still running from a flight - Sandbox_Bench carries an
# auto-possess pawn, so any casual Play leaves a session up with nothing
# moving and no one watching. The editor said exactly that ("Cannot create
# actors while PIE is active") and three separate tools fed the sentence to
# json.loads, so what surfaced was a JSONDecodeError about column 1.
#
# ue.tool now raises with the real message, which makes the loss legible.
# This makes it impossible: one line, before any geometry is built.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'StacktownAlpha', 'Tools', 'measure'))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '..', 'Tools', 'measure'))
try:
    import ue as _ue
    if json.loads(_ue.tool('EditorToolset.EditorAppToolset',
                           'IsPIERunning', {}))['returnValue']:
        raise SystemExit('bake_catalogue: PIE is active - stop play before '
                         'baking (nothing was built)')
except SystemExit:
    raise
except Exception as _e:
    print('bake_catalogue: could not check PIE state (%s); continuing' % _e)

argv = [a for a in sys.argv[1:] if not a.startswith('--')]
FORCE = '--force' in sys.argv
want = argv or list(recipes.RECIPES)
made, refused = [], []
TMP = tempfile.gettempdir()
ONLY_W = next((float(a.split('=')[1]) for a in sys.argv[1:]
               if a.startswith('--width=')), None)
JOBS = [(rid, w) for rid in want for w in recipes.widths(rid)
        if ONLY_W is None or abs(w - ONLY_W) < 1.0]
print('baking %d meshes: %s' % (len(JOBS)*max(1, recipes.tier_count(want[0])),
                                ', '.join('%s@%.0f' % j for j in JOBS)))
for rid, w in JOBS:
    for t in range(recipes.tier_count(rid)):
        tag = 'BAKE%s%d' % (rid.capitalize(), t)
        # Build the CORE narrower by the flank allowance and start it half an
        # allowance in, so core + flanks land exactly on the parcel line.
        # parcel_width rides along for GATE-05, which judges the land claimed.
        _probe = recipes.spec_for(rid, t, tag, 0.0, w)
        al = step_elevations.flank_allowance(_probe)
        spec = recipes.spec_for(rid, t, tag, al/2.0, w - al)
        # ...and the same deduction in DEPTH, because the rear slab stands
        # proud too. Front projections are NOT deducted: they oversail the
        # pavement, which GATE-05 allows; the rear oversails the next plot,
        # which nothing does.
        spec['parcel_width'] = w
        spec['parcel_x0'] = 0.0
        spec['parcel_depth'] = spec['depth']
        spec['depth'] = spec['depth'] - step_elevations.rear_allowance(spec)
        # how many donor pieces this model SHOULD carry - recorded off the
        # sink, so the stamp can be compared against reality later
        genbuild.record()
        genbuild.build(spec, origin=STAGE, yaw=0.0)
        _ndonors = sum(1 for e in genbuild.drain() if e.get('kind') == 'mesh')
        genbuild.piece_failures(reset=True)
        genbuild.build(spec, origin=STAGE, yaw=0.0)
        # EVERY face, because a catalogue model has no neighbours. Without this
        # the commercial generators bake a street facade and a roof - they emit
        # the front, and step_elevations supplies flanks and rear only for the
        # end lots of a real block. Measured on the built city, Court had 1.3%
        # of its parts behind its own front third and Narrow 1.9%.
        step_elevations.freestanding(spec, origin=STAGE, yaw=0.0)
        # ...and the SOLID CORE behind the facades. Without it the model is a
        # shell of four skins and you can see through the building - the exact
        # look the first freestanding vernacular bake produced.
        print('  core: %d bands' % cores.build_core(spec, origin=STAGE, yaw=0.0))
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
        # The label set has to cover every actor the generators emit. It was
        # BLD2_*_H / BLD2_*_A / PLOT_*, which is complete for house and walkup
        # and misses everything vernacular, modern, deco and works produce -
        # they emit GF, F0..Fn, Roof, Canopy, Shaft - plus every ELEV_ face.
        labels = ([l % tag for l in ('BLD2_%s_H', 'BLD2_%s_A', 'BLD2_%s_GF',
                                     'BLD2_%s_Roof', 'BLD2_%s_Canopy',
                                     'BLD2_%s_Shaft', 'PLOT_%s')]
                  + ['BLD2_%s_F%d' % (tag, i) for i in range(40)]
                  + ['ELEV_%s_%s' % (tag, f) for f in ('W', 'E', 'R')]
                  + ['CORE_%s' % tag]
                  + ['CORE_%s_b%d' % (tag, i) for i in range(12)])
        asset = recipes.asset_name(rid, t, w)

        # --- the gate, while the model is still boxes -----------------------
        # 'stage' is the S20 frame contract: the gate judges the PARCEL, so
        # it must know where the parcel was staged.
        json.dump({'labels': labels, 'spec': spec, 'stage': list(STAGE)},
                  open(os.path.join(TMP, 'stacktown_gate_job.json'), 'w'))
        verdict_path = os.path.join(TMP, 'stacktown_gate_verdict.json')
        if os.path.exists(verdict_path):
            os.remove(verdict_path)          # a stale verdict must not pass
        gr = subprocess.run([RUNG, 'gate_run.py'], capture_output=True,
                            text=True, cwd=HERE)
        for ln in gr.stdout.splitlines():
            if ln.startswith('[Info]   gate') or ln.startswith('[Info]     GATE'):
                print(ln[7:])
        if 'success: True' not in gr.stdout or not os.path.exists(verdict_path):
            raise SystemExit('gate did not run for %s t%d\n%s'
                             % (rid, t, gr.stdout[-700:] or gr.stderr[-700:]))
        verdict = json.load(open(verdict_path))
        if not verdict['ok'] and not FORCE:
            print('  REFUSED to bake %s t%d - gate failed:' % (rid, t))
            for f in verdict['findings']:
                print('    %-8s %-22s %s' % tuple(f))
            refused.append('%s t%d' % (rid, t))
            open(os.path.join(TMP, 'stacktown_wipe_lots.txt'), 'w').write(tag)
            subprocess.run([RUNG, 'wipe_lots.py'], capture_output=True,
                           text=True, cwd=HERE)
            continue
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

        # --- the stamp: the mesh carries the verdict it earned --------------
        # A BAKER MUST NOT STAMP A MODEL MISSING PARTS IT THINKS IT HAS.
        # piece() now reports every donor the editor refused; before it did,
        # this path silently produced donorless meshes and stamped them PASS.
        _fails = genbuild.piece_failures(reset=True)
        if _fails:
            raise SystemExit(
                'REFUSED to stamp %s - %d donor placement(s) failed, so the '
                'mesh is missing geometry the gate believed it had:\n  %s'
                % (asset, len(_fails),
                   '\n  '.join('%s <- %s : %s' % f for f in _fails[:6])))
        json.dump({'asset': '%s/%s' % (OUT, asset), 'recipe': rid, 'tier': t,
                   'tier_name': recipes.tier_name(rid, t), 'width': w,
                   'verdict': verdict,
                   'bake_path': 'live', 'donors': _ndonors,
                   'donor_fails': 0},
                  open(os.path.join(TMP, 'stacktown_stamp_job.json'), 'w'))
        sr = subprocess.run([RUNG, 'stamp.py'], capture_output=True,
                            text=True, cwd=HERE)
        stamped = [l[7:] for l in sr.stdout.splitlines()
                   if l.startswith('[Info]   STAMPED')]
        if 'success: True' not in sr.stdout or not stamped:
            raise SystemExit('stamp failed for %s\n%s'
                             % (asset, sr.stdout[-700:] or sr.stderr[-700:]))
        print(stamped[0])
        made.append(asset)
        # clear the staging actors before the next one
        open(os.path.join(tempfile.gettempdir(), 'stacktown_wipe_lots.txt'),
             'w').write(tag)
        subprocess.run([RUNG, 'wipe_lots.py'], capture_output=True, text=True, cwd=HERE)
os.remove(os.path.join(tempfile.gettempdir(), 'stacktown_role_overrides.json'))
print('catalogue: %d baked and stamped%s'
      % (len(made), '' if not refused
         else ', %d REFUSED by the gate: %s' % (len(refused), ', '.join(refused))))
if refused:
    raise SystemExit(1)
