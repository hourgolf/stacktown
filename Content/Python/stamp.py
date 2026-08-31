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
    # WHICH PATH BUILT THIS, and whether its donors actually landed.
    #
    # Two bake paths exist and they disagreed for months without saying so:
    # the LIVE path (bake_catalogue) placed no donor geometry at all, because
    # piece() called a tool that exists on no toolset and discarded the error,
    # while FASTBAKE (preview) reads the recorded parts directly and always
    # carried them. Both stamped Gate=PASS. Nothing on the asset said which
    # path built it, so telling a complete mesh from a donorless one meant
    # inferring from material slots - see POLISH_BACKLOG S11.
    #
    # A mesh is meant to be evidence. Evidence that cannot say how it was
    # produced is a good deal weaker than it looks.
    'BakePath':   str(job.get('bake_path', 'unknown')),
    'Donors':     str(int(job.get('donors', -1))),
    'DonorFails': str(int(job.get('donor_fails', -1))),
    # GATE-11's per-model count and the budget it was judged against. The
    # arming contract (0766570) requires this on the asset "so nothing hides
    # in an aggregate", and it is also the ONLY thing that can make the
    # regression arm work - "may not increase" needs a number from last time.
    #
    # It was missing until 30 Aug. preview.py put coplanar_visible in the job
    # payload and this dict never carried it through, so the tag was never
    # written, so nothing could read it back, so the regression half of the
    # armed gate had no baselines and could not fire on any real model. I
    # reported the stamp as working because I had checked the JOB and not the
    # ASSET - the input, not the artifact.
    'Coplanar':       str(int(job.get('coplanar_visible', -1))),
    'CoplanarBudget': str(int(job.get('coplanar_budget', -1))),
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
# THE BASELINE LEDGER, written by the same code that writes the tag so the
# two cannot disagree. The gate needs the previous count at JUDGE time, which
# is before any editor call in the fastbake path - reading it back off the
# asset would cost a round trip per model. One writer, two outputs.
import os as _os
# PROJECT PATH FROM UNREAL, not from __file__. rung.sh concatenates the guard
# and the script into a temp file before running it, so __file__ here is
# /var/folders/... and deriving the project root from it wrote the ledger into
# the system temp directory - where preview.py would never find it, and the
# regression arm would have stayed dead while looking wired.
_led = _os.path.join(unreal.Paths.convert_relative_path_to_full(
    unreal.Paths.project_saved_dir()), 'coplanar_baselines.json')
try:
    _prev = json.load(open(_led)) if _os.path.exists(_led) else {}
except Exception:
    _prev = {}
_prev[path.rsplit('/', 1)[-1]] = int(job.get('coplanar_visible', -1))
_os.makedirs(_os.path.dirname(_led), exist_ok=True)
json.dump(_prev, open(_led, 'w'), indent=0, sort_keys=True)

print('  STAMPED %s  gate=%s parts=%s mats=%s density=%s coplanar=%s/%s'
      % (path.rsplit('/', 1)[-1], back['Gate'], back['Parts'],
         back['Materials'], back['Density'], back['Coplanar'],
         back['CoplanarBudget']))
