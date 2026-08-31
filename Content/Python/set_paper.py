"""Apply the fabrication stock to every card material. See fabrication.py.

This used to set ONE tooth on all 37 materials at once. That was right about
the tooth being far too fine to read - 0.050 is invisible at any working
distance - and wrong about applying it everywhere: aluminium mullions, brass,
glazing and flock all came out wearing the same cardstock grain, which reads
as a whole model cut from one sheet.

MASTER_MATERIAL_SPEC says what tooth is for - "the tooth of paint or print" -
and says to keep the ROLE set small. So no new roles and no new masters: the
same materials, parameterised to say what a maker would have cut them from.

Direction of the tooth parameter, since it caught this project out once:
a LARGER PaperTiling is MORE UV repeats, i.e. FINER. The earlier note that
"PaperTiling is inert" came from a test that moved it upward, into a range
already below a pixel.
"""
import unreal
import _path  # noqa: F401
import fabrication

L = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
F = '/Game/Stacktown/Materials'

assert fabrication._selftest()
rows, skipped = [], 0
for p in sorted(eal.list_assets(F, recursive=False, include_folder=False)):
    name = p.split('/')[-1].split('.')[0]
    if not name.startswith('MI_'):
        continue
    if name.startswith('MI_st'):          # study panels are meant to differ
        skipped += 1
        continue
    mi = eal.load_asset(p)
    if not mi or not isinstance(mi, unreal.MaterialInstanceConstant):
        continue
    try:
        L.get_material_instance_scalar_parameter_value(mi, 'PaperTiling')
    except Exception:
        continue
    stock = fabrication.stock_for(name)
    for k, v in fabrication.params_for(name).items():
        L.set_material_instance_scalar_parameter_value(mi, k, v)
    eal.save_asset(p.split('.')[0], only_if_is_dirty=False)
    got = L.get_material_instance_scalar_parameter_value(mi, 'PaperTiling')
    want = fabrication.params_for(name)['PaperTiling']
    if abs(got - want) > 1e-6:
        raise SystemExit('%s: tiling did not take (%.4f)' % (name, got))
    rows.append((name, stock))

by = {}
for n, s in rows:
    by.setdefault(s, []).append(n)
for s in sorted(by):
    t, a, lo, hi = fabrication.STOCK[s]
    print('  %-12s tooth %.3f amount %.1f rough %.2f-%.2f  (%d) %s'
          % (s, t, a, lo, hi, len(by[s]), ', '.join(sorted(by[s]))[:70]))
print('%d materials cut from %d stocks; %d study panels skipped'
      % (len(rows), len(by), skipped))
