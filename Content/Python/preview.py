#!/usr/bin/env python3
"""Fast preview: recipe -> baked mesh -> on the bench, in one pass.

    python3 preview.py [recipe] [tier] [--width=1230] [--no-bench]

The art loop was twelve minutes: ~900 MCP round trips to spawn boxes, a role
sweep over the whole level, a merge, then a capture. Nothing in that needs a
round trip - the geometry is fully known before the editor is touched. With
genbuild's sink armed the whole building comes back as data, and fastbake
turns it into a mesh in one editor call.

Same generator, same specs, same role table. Not a second implementation:
that is what bakegen.py is, and it has already drifted past cornices, stepped
setbacks, roof gardens and penthouses.
"""
import os, sys, json, time, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _path  # noqa: F401
import genbuild, recipes, step_elevations, cores

ROOT = os.path.dirname(os.path.dirname(HERE))
RUNG = os.path.join(ROOT, 'Tools', 'rung.sh')
TMP = tempfile.gettempdir()
OUT = '/Game/Stacktown/Baked'
STAGE = (0.0, 0.0, 0.0)          # local: the mesh is built about its own origin


def collect(rid, tier, w):
    """Every box of one model, as data. No editor involved."""
    probe = recipes.spec_for(rid, tier, 'PRE', 0.0, w)
    al = step_elevations.flank_allowance(probe)
    spec = recipes.spec_for(rid, tier, 'PRE', al/2.0, w - al)
    spec['parcel_width'] = w
    spec['parcel_depth'] = spec['depth']
    spec['depth'] = spec['depth'] - step_elevations.rear_allowance(spec)
    genbuild.record()
    genbuild.build(spec, origin=STAGE, yaw=0.0)
    step_elevations.freestanding(spec, origin=STAGE, yaw=0.0)
    cores.build_core(spec, origin=STAGE, yaw=0.0)
    return spec, genbuild.drain()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    rid = args[0] if args else 'vernacular'
    tier = int(args[1]) if len(args) > 1 else recipes.tier_count(rid) - 1
    w = next((float(a.split('=')[1]) for a in sys.argv[1:]
              if a.startswith('--width=')), recipes.widths(rid)[len(recipes.widths(rid))//2])

    t0 = time.time()
    spec, rec = collect(rid, tier, w)
    nbox = sum(1 for e in rec if e['kind'] == 'box')
    t_gen = time.time() - t0

    asset = recipes.asset_name(rid, tier, w)
    json.dump({'boxes': rec, 'out': '%s/%s' % (OUT, asset),
               'wall': spec.get('wall'), 'roofmat': spec.get('roofmat')},
              open(os.path.join(TMP, 'stacktown_fastbake_job.json'), 'w'))
    t1 = time.time()
    r = subprocess.run([RUNG, 'fastbake.py'], capture_output=True, text=True, cwd=HERE)
    t_bake = time.time() - t1
    line = [l[7:] for l in r.stdout.splitlines() if 'FASTBAKED' in l]
    if 'success: True' not in r.stdout or not line:
        raise SystemExit('fastbake failed\n' + (r.stdout[-900:] or r.stderr[-900:]))
    print(line[0])
    print('  generate %5.1fs (%d boxes, no editor)   bake %5.1fs   TOTAL %5.1fs'
          % (t_gen, nbox, t_bake, time.time() - t0))

    if '--no-bench' not in sys.argv:
        b = subprocess.run([RUNG, 'bench.py', asset], capture_output=True,
                           text=True, cwd=HERE)
        for l in b.stdout.splitlines():
            if l.startswith('[Info] bench:') or l.startswith('[Info]   BENCH_'):
                print(l[7:])


if __name__ == '__main__':
    main()
