"""Audit the baked catalogue from the STAMPS, not from anyone's memory.

A merged mesh is one component and nothing downstream can re-derive what it
was made of, so this reads back what the gate wrote at bake time. An unstamped
mesh is reported as UNVERIFIED rather than assumed fine - that distinction is
the entire point of stamping, and a report that quietly skipped them would be
the "check returns ok while asking the wrong question" failure again.

    ./Tools/rung.sh catalogue_audit.py
"""
import unreal
import _path  # noqa: F401
import recipes
from qc import DETAIL_MIN, MAT_MIN

OUT = '/Game/Stacktown/Baked'
P = 'Stacktown.'

rows, unverified, failed, missing = [], [], [], []
for rid in sorted(recipes.RECIPES):
  for w in recipes.widths(rid):
    for t in range(recipes.tier_count(rid)):
        name = recipes.asset_name(rid, t, w)
        path = '%s/%s' % (OUT, name)
        sm = unreal.load_asset(path)
        if not sm:
            missing.append(name)
            continue
        g = lambda k: unreal.EditorAssetLibrary.get_metadata_tag(sm, P + k)
        if not g('Gate'):
            unverified.append(name)
            continue
        slots = len(sm.get_editor_property('static_materials'))
        rows.append((name, g('Gate'), g('TierName'), int(g('Parts')),
                     int(g('Materials')), float(g('Density')),
                     float(g('SpanX')), float(g('SpanY')), slots,
                     int(g('Width')), g('Stamped')))
        if g('Gate') != 'PASS':
            failed.append(name)

print('%-26s %-5s %-13s %5s %4s %7s %8s %6s' %
      ('asset', 'gate', 'tier', 'parts', 'mats', 'per m2', 'span x', 'slots'))
for r in rows:
    flag = ''
    if r[5] < DETAIL_MIN:
        flag += '  <-- density under %.2f' % DETAIL_MIN
    if r[4] < MAT_MIN:
        flag += '  <-- under %d materials' % MAT_MIN
    if r[6] > r[9] * 1.02:
        flag += '  <-- wider than its parcel'
    print('%-26s %-5s %-13s %5d %4d %7.2f %8.0f %6d%s'
          % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[8], flag))

print('\ncatalogue: %d stamped, %d unverified, %d gate-failed, %d missing'
      % (len(rows), len(unverified), len(failed), len(missing)))
for tag, lst in (('UNVERIFIED (no stamp)', unverified),
                 ('GATE FAILED', failed), ('MISSING', missing)):
    if lst:
        print('  %s: %s' % (tag, ', '.join(lst)))
