"""Run the per-model gate against the staged model, before it is baked.

Reads its job from a temp file, exactly as bake_merge.py does - rung.sh hands
this script to the editor over remote execution and the editor does not
inherit the caller's environment.

    job:     {"labels": [...], "spec": {...}}
    writes:  stacktown_gate_verdict.json  {"ok":bool,"findings":[...],"facts":{}}

The verdict file is the contract with bake_catalogue.py: no verdict file, or
ok false, and the bake does not happen.
"""
import os, json, tempfile
import _path  # noqa: F401
import snapshot
import modelgate

JOB = os.path.join(tempfile.gettempdir(), 'stacktown_gate_job.json')
OUT = os.path.join(tempfile.gettempdir(), 'stacktown_gate_verdict.json')

job = json.load(open(JOB))
want = set(job['labels'])
snap = snapshot.take()
actors = [a for a in snap['actors'] if a['label'] in want]

# S20: comps arrive at the gate in PARCEL FRAME. snapshot.take() is WORLD
# (get_world_transform), and the bake stages at job['stage'] - without this
# subtraction GATE-10's in-front-of-the-core exemption compared world Y
# against a spec-local plane and was dead at the (0, 60000, 0) stage while
# alive at the preview's origin: the two gate paths disagreed. A job with no
# stage declares it stages at the origin.
_sx, _sy, _sz = job.get('stage', (0.0, 0.0, 0.0))
if any((_sx, _sy, _sz)):
    for a in actors:
        a['loc'] = (a['loc'][0] - _sx, a['loc'][1] - _sy, a['loc'][2] - _sz)
        for c in a['comps']:
            if c.get('aabb'):
                lo, hi = c['aabb']
                c['aabb'] = ([lo[0]-_sx, lo[1]-_sy, lo[2]-_sz],
                             [hi[0]-_sx, hi[1]-_sy, hi[2]-_sz])

# The label list is a SUPERSET covering every style - bake_merge picks whichever
# of them exist and skips the rest, so a house having no BLD2_*_A actor is
# normal, not a defect. The gate has to agree with the merger about what it is
# looking at, or it refuses to bake perfectly good models: the first run of
# this file rejected all three cottage tiers for exactly that reason.
#
# What IS fatal is no building at all. A model that was never built is not "a
# model with no defects", and reporting ok for it would stamp a mesh that does
# not exist - the precise failure the stamp is meant to make impossible.
building = [a for a in actors if a['label'].startswith(('BLD2_', 'ELEV_'))]
if not building:
    json.dump(dict(ok=False, facts={},
                   findings=[['GATE-00', ','.join(sorted(want)),
                              'no building actor was staged']]),
              open(OUT, 'w'))
    print('GATE FAIL: no building actor among %s' % sorted(want))
    raise SystemExit(0)
print('  staged: %s' % ', '.join(sorted(a['label'] for a in actors)))

m = modelgate.model(job['spec'], actors)
ok, findings, facts = modelgate.run(m)
json.dump(dict(ok=ok, findings=[list(f) for f in findings], facts=facts),
          open(OUT, 'w'))
print('  gate %s  parts %d (of %d)  materials %d  %.2f/m2  span %sx%s'
      % ('PASS' if ok else 'FAIL', facts.get('parts', 0),
         facts.get('parts_total', 0), facts.get('materials', 0),
         facts.get('density', 0.0), facts.get('span_x'), facts.get('span_y')))
for rid, subj, detail in findings:
    print('    %-8s %-22s %s' % (rid, subj, detail))
