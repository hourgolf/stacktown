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
