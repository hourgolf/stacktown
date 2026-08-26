"""Stamp a baked mesh with the gate verdict it earned.

A mesh in the catalogue should be EVIDENCE, not an assurance. Once merged, the
mesh is one component and nothing downstream can re-derive what it was made
of - so the numbers the gate measured while it was still boxes are written
onto the asset itself, and an unstamped mesh is presumed unverified rather
than presumed fine.

    job: {"asset": "/Game/...", "recipe":..., "tier":..., "width":...,
          "verdict": {"ok":bool, "facts":{...}}}

Tags are read back and printed after writing, because a stamp nobody verified
is the same class of thing as a check that returns "ok" without looking.
"""
import os, json, tempfile, datetime
import unreal

JOB = os.path.join(tempfile.gettempdir(), 'stacktown_stamp_job.json')
PREFIX = 'Stacktown.'

job = json.load(open(JOB))
path = job['asset']
sm = unreal.load_asset(path)
if not sm:
    raise SystemExit('stamp: no asset at %s' % path)

f = job['verdict'].get('facts', {})
tags = {
    'Recipe':     str(job['recipe']),
    'Tier':       str(job['tier']),
    'TierName':   str(job.get('tier_name', '')),
    'Width':      str(int(round(job['width']))),
    'Gate':       'PASS' if job['verdict'].get('ok') else 'FAIL',
    'GateRules':  str(f.get('rules', 0)),
    'Parts':      str(f.get('parts', 0)),
    'Materials':  str(f.get('materials', 0)),
    'Density':    '%.3f' % f.get('density', 0.0),
    'SpanX':      '%.0f' % (f.get('span_x') or 0.0),
    'SpanY':      '%.0f' % (f.get('span_y') or 0.0),
    'Stamped':    datetime.date.today().isoformat(),
}
for k, v in tags.items():
    unreal.EditorAssetLibrary.set_metadata_tag(sm, PREFIX + k, v)
unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)

back = {k: unreal.EditorAssetLibrary.get_metadata_tag(sm, PREFIX + k)
        for k in tags}
bad = [k for k in tags if back[k] != tags[k]]
if bad:
    raise SystemExit('stamp: wrote %s but read back %s'
                     % ({k: tags[k] for k in bad}, {k: back[k] for k in bad}))
print('  STAMPED %s  gate=%s parts=%s mats=%s density=%s'
      % (path.rsplit('/', 1)[-1], back['Gate'], back['Parts'],
         back['Materials'], back['Density']))
