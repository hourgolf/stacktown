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
import math
import json
import genbuild, recipes, step_elevations, cores, rolemap, modelgate

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
    spec['parcel_x0'] = 0.0
    spec['parcel_depth'] = spec['depth']
    spec['depth'] = spec['depth'] - step_elevations.rear_allowance(spec)
    genbuild.record()
    genbuild.build(spec, origin=STAGE, yaw=0.0)
    step_elevations.freestanding(spec, origin=STAGE, yaw=0.0)
    cores.build_core(spec, origin=STAGE, yaw=0.0)
    return spec, genbuild.drain()


def _load_bounds():
    """Donor bounds, measured once by meshbounds.py. Keyed by asset path."""
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    f = os.path.join(here, 'Tools', 'measure', 'meshbounds.json')
    try:
        with open(f) as fh:
            return {v['asset']: v for v in json.load(fh)['meshes'].values()}
    except Exception:
        return {}


_BOUNDS = _load_bounds()


def as_snapshot(rec, spec):
    """Turn the recorded box list into the shape modelgate reads.

    The fast path baked without ever running the gate - so every preview
    produced an UNVERIFIED mesh, which catalogue_audit duly reported. I built
    a gate to keep unchecked meshes out of the catalogue and then built a
    route around it.

    It costs nothing to close: the sink already holds every box, its name and
    its transform, and the material follows from the name through rolemap.
    No editor, no snapshot, no round trip.
    """
    actors, by_ref = [], {}
    for i, e in enumerate(rec):
        if e['kind'] != 'actor':
            continue
        a = dict(label=e['name'], family=e['name'].split('_')[0],
                 cls='Actor', loc=tuple(e['loc']), rot=tuple(e['rot']),
                 comps=[])
        by_ref[i] = a
        actors.append(a)
    for e in rec:
        if e['kind'] != 'box':
            continue
        a = by_ref.get(e['actor'])
        if a is None:
            continue
        cx, cy, cz = e['c']
        dx, dy, dz = (v/2.0 for v in e['d'])
        pitch, yaw, roll = e['r']
        if any(abs(v) > 1e-6 for v in (pitch, yaw, roll)):
            # exact AABB of a rotated box: transform all eight corners
            cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
            cy_, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
            lo = [1e18]*3
            hi = [-1e18]*3
            for sxs in (-1, 1):
                for sys_ in (-1, 1):
                    for szs in (-1, 1):
                        x, y, z = sxs*dx, sys_*dy, szs*dz
                        y, z = y*cr - z*sr, y*sr + z*cr        # roll  about X
                        x, z = x*cp + z*sp, -x*sp + z*cp       # pitch about Y
                        x, y = x*cy_ - y*sy, x*sy + y*cy_      # yaw   about Z
                        for k, v in enumerate((cx+x, cy+y, cz+z)):
                            lo[k] = min(lo[k], v)
                            hi[k] = max(hi[k], v)
        else:
            lo = [cx-dx, cy-dy, cz-dz]
            hi = [cx+dx, cy+dy, cz+dz]
        m = rolemap.material_for(e['name'], spec.get('wall'),
                                 spec.get('roofmat'), a['family'],
                                 spec.get('trim'))
        a['comps'].append(dict(name=e['name'], mesh='Cube',
                               aabb=(lo, hi), mats=[m]))

    # DONOR MESHES. This loop did not exist, and its absence was not a gap in
    # coverage - it was a route around the gate. The fast path is LIVE and it
    # STAMPS, so a model whose oversail comes from a donor piece could be
    # stamped Gate=PASS here while the editor gate refuses the identical mesh,
    # and catalogue_audit then inherited the same blind spans. A donor's true
    # extent is not in the record (the record holds a path, a transform and a
    # scale), so it comes from Tools/measure/meshbounds.json - measured once
    # per asset by meshbounds.py, which self-checks against a bound somebody
    # had already measured by hand.
    blind = []
    for e in rec:
        if e['kind'] != 'mesh':
            continue
        a = by_ref.get(e['actor'])
        if a is None:
            continue
        b = _BOUNDS.get(e.get('asset'))
        if not b:
            blind.append(e.get('asset'))
            continue
        sx, sy, sz = (e.get('s') or [1.0, 1.0, 1.0])
        cx, cy, cz = e['c']
        pitch, yaw, roll = e.get('r') or (0.0, 0.0, 0.0)
        cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        cy_, sy_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        lo = [1e18]*3
        hi = [-1e18]*3
        for i in (0, 1):
            for j in (0, 1):
                for k in (0, 1):
                    x = (b['hi'][0] if i else b['lo'][0]) * sx
                    y = (b['hi'][1] if j else b['lo'][1]) * sy
                    z = (b['hi'][2] if k else b['lo'][2]) * sz
                    y, z = y*cr - z*sr, y*sr + z*cr        # roll  about X
                    x, z = x*cp + z*sp, -x*sp + z*cp       # pitch about Y
                    x, y = x*cy_ - y*sy_, x*sy_ + y*cy_    # yaw   about Z
                    for n, v in enumerate((cx+x, cy+y, cz+z)):
                        lo[n] = min(lo[n], v)
                        hi[n] = max(hi[n], v)
        mm = e.get('mat') or rolemap.material_for_slot(e['name'], spec.get('wall'))
        a['comps'].append(dict(name=e['name'], mesh=str(e.get('asset', '')).rsplit('/', 1)[-1],
                               aabb=(lo, hi), mats=[mm]))

    # LOUD, not silent. Silent omission is what let this path certify a mesh
    # the editor gate refuses; a donor with no bounds entry must announce
    # itself so the gap is visible the first time rather than the fiftieth.
    if blind:
        print('  DONOR-BLIND: %d piece(s) with no bounds entry - run '
              'meshbounds.py: %s' % (len(blind), ', '.join(sorted(set(blind))[:4])))
    return dict(actors=actors, unread_material_slots=0, seconds=0.0,
                donor_blind=len(blind))


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

    # GATE FIRST, on data, before anything is written
    ok, findings, facts = modelgate.run(modelgate.model(spec, as_snapshot(rec, spec)['actors']))
    print('  gate %s  parts %d  materials %d  %.2f/m2  span %sx%s'
          % ('PASS' if ok else 'FAIL', facts.get('parts', 0),
             facts.get('materials', 0), facts.get('density', 0.0),
             facts.get('span_x'), facts.get('span_y')))
    for rid_, subj, detail in findings:
        print('    %-8s %-22s %s' % (rid_, subj, detail))
    if not ok and '--force' not in sys.argv:
        raise SystemExit('preview: gate failed - not baking (use --force to look anyway)')

    asset = recipes.asset_name(rid, tier, w)
    json.dump({'boxes': rec, 'out': '%s/%s' % (OUT, asset),
               'wall': spec.get('wall'), 'roofmat': spec.get('roofmat'),
               'trim': spec.get('trim'),
               # SECOND CLADDING. fastbake has had panel_overrides since it
               # was written and nothing ever sent them, so a building could
               # only ever wear one wall material. A contemporary block is
               # two masses in two claddings meeting on a vertical line.
               'panel_overrides': spec.get('panels') or {}},
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

    # ...and STAMP, so a previewed mesh is evidence like any other
    json.dump({'asset': '%s/%s' % (OUT, asset), 'recipe': rid, 'tier': tier,
               'tier_name': recipes.tier_name(rid, tier), 'width': w,
               'verdict': {'ok': ok, 'facts': facts},
               # fastbake reads the recorded parts directly, so its donors
               # cannot silently fail the way the live path's did
               'bake_path': 'fastbake',
               'donors': sum(1 for e in rec if e['kind'] == 'mesh'),
               'donor_fails': 0},
              open(os.path.join(TMP, 'stacktown_stamp_job.json'), 'w'))
    sr = subprocess.run([RUNG, 'stamp.py'], capture_output=True, text=True, cwd=HERE)
    st = [l[7:] for l in sr.stdout.splitlines() if 'STAMPED' in l]
    if 'success: True' not in sr.stdout or not st:
        raise SystemExit('stamp failed\n' + (sr.stdout[-600:] or sr.stderr[-600:]))
    print(st[0])

    if '--no-bench' not in sys.argv:
        b = subprocess.run([RUNG, 'bench.py', asset], capture_output=True,
                           text=True, cwd=HERE)
        for l in b.stdout.splitlines():
            if l.startswith('[Info] bench:') or l.startswith('[Info]   BENCH_'):
                print(l[7:])


if __name__ == '__main__':
    main()
