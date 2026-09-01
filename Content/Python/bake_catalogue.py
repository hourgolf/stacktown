#!/usr/bin/env python3
"""Bake every recipe at every tier into the catalogue.

    python3 bake_catalogue.py [recipe ...]
    python3 bake_catalogue.py --force          bake even if the gate fails
    python3 bake_catalogue.py --width=1230     just one parcel width
    python3 bake_catalogue.py --tier=6         just one tier
    python3 bake_catalogue.py --corner=right   the on-demand corner variant

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

genbuild.live()   # this script builds into the OPEN level; see genbuild._LIVE

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
except Exception as _e:
    _ue = None
    print('bake_catalogue: could not import ue (%s); PIE unchecked' % _e)


def no_pie(phase):
    """Refuse to enter an actor-creating phase while PIE holds the level.

    ONCE IS NOT ENOUGH, and 2026-09-01 is why. The preflight below has always
    been a SNAPSHOT taken at second zero, and a bake runs for minutes. On that
    date the check passed, a play session started partway through, and the
    bake died mid-create inside cores.build_core with 28 half-built actors
    stranded in the level - which could not then be cleaned up either, because
    actor REMOVAL is blocked during PIE as well.

    The 29 Aug incident in this file's own docstring was PIE already running
    when the bake started; the preflight fixed exactly that and nothing more.
    A precondition checked once cannot protect a process that runs for
    minutes: it turns a minutes-wide hole into a smaller one only if it is
    re-checked at each boundary. This is that re-check - one cheap snapshot
    per phase, so the exposure is the length of a phase rather than the length
    of a bake, and a refusal happens BETWEEN phases where nothing is stranded.

    It cannot close the window completely. Nothing can, short of a lock the
    editor does not offer - Play pressed mid-phase still lands mid-create.
    The scheduling rule is the other half: bakes get an announced window,
    granted serially, exactly as PIE blocks do.
    """
    if _ue is None:
        return
    try:
        active = json.loads(_ue.tool('EditorToolset.EditorAppToolset',
                                     'IsPIERunning', {}))['returnValue']
    except Exception as _e:
        print('bake_catalogue: could not check PIE state (%s); continuing'
              % _e)
        return
    if active:
        raise SystemExit(
            'bake_catalogue: PIE became active before phase %r - refusing to '
            'continue. Nothing was created in this phase, so the level holds '
            'only whatever completed cleanly. Stop play, clear any BAKE* '
            'actors, and re-run.' % phase)


no_pie('preflight')

argv = [a for a in sys.argv[1:] if not a.startswith('--')]
FORCE = '--force' in sys.argv
want = argv or list(recipes.RECIPES)
made, refused = [], []
TMP = tempfile.gettempdir()
ONLY_W = next((float(a.split('=')[1]) for a in sys.argv[1:]
               if a.startswith('--width=')), None)
# THE ON-DEMAND VARIANT AXIS. recipes.depths() declares a corner depth and
# says it is "BAKED ON DEMAND - only where the placer actually sites a corner
# - so declaring it costs nothing and no catalogue-wide corner bake is
# implied." That is why this script never grew corner support: the ten corner
# meshes on disk were baked one at a time for whatever a draw asked for.
#
# Absent, everything below is exactly what it was, so the 548 are unaffected.
# Applied, the variant lands on the spec where preview.collect puts it -
# BEFORE the rear allowance comes off, or the allowance would be subtracted
# from a depth the recipe never saw.
ONLY_T = next((int(a.split('=')[1]) for a in sys.argv[1:]
               if a.startswith('--tier=')), None)
CORNER = next((a.split('=')[1] for a in sys.argv[1:]
               if a.startswith('--corner=')), None)
if CORNER not in (None, 'left', 'right'):
    raise SystemExit('--corner must be left or right, got %r' % CORNER)
JOBS = [(rid, w) for rid in want for w in recipes.widths(rid)
        if ONLY_W is None or abs(w - ONLY_W) < 1.0]
# count the tiers that will ACTUALLY bake - the old line multiplied by the
# full tier count and so reported "7 meshes" for a --tier=6 run of one
_ntiers = (1 if ONLY_T is not None
           else max(1, recipes.tier_count(want[0])))
print('baking %d mesh(es): %s%s' % (
    len(JOBS) * _ntiers, ', '.join('%s@%.0f' % j for j in JOBS),
    '' if CORNER is None else '  corner=%s d%.0f' % (CORNER,
                                                     recipes.DEPTH_CORNER)))
for rid, w in JOBS:
    for t in range(recipes.tier_count(rid)):
        if ONLY_T is not None and t != ONLY_T:
            continue
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
        if CORNER is not None:
            spec['depth'] = float(recipes.DEPTH_CORNER)
            spec['corner'] = True
            spec['corner_return'] = CORNER
        spec['parcel_width'] = w
        spec['parcel_x0'] = 0.0
        spec['parcel_depth'] = spec['depth']
        spec['depth'] = spec['depth'] - step_elevations.rear_allowance(spec)
        # how many donor pieces this model SHOULD carry - recorded off the
        # sink, so the stamp can be compared against reality later
        no_pie('build:%s t%d' % (rid, t))
        genbuild.record()
        genbuild.build(spec, origin=STAGE, yaw=0.0)
        _ndonors = sum(1 for e in genbuild.drain() if e.get('kind') == 'mesh')
        genbuild.piece_failures(reset=True)
        no_pie('build-live:%s t%d' % (rid, t))
        genbuild.build(spec, origin=STAGE, yaw=0.0)
        # EVERY face, because a catalogue model has no neighbours. Without this
        # the commercial generators bake a street facade and a roof - they emit
        # the front, and step_elevations supplies flanks and rear only for the
        # end lots of a real block. Measured on the built city, Court had 1.3%
        # of its parts behind its own front third and Narrow 1.9%.
        no_pie('elevations:%s t%d' % (rid, t))
        step_elevations.freestanding(spec, origin=STAGE, yaw=0.0)
        # ...and the SOLID CORE behind the facades. Without it the model is a
        # shell of four skins and you can see through the building - the exact
        # look the first freestanding vernacular bake produced.
        no_pie('core:%s t%d' % (rid, t))
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
        asset = (recipes.asset_name(rid, t, w) if CORNER is None else
                 recipes.asset_name(rid, t, w, depth=recipes.DEPTH_CORNER,
                                    corner=CORNER))

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
