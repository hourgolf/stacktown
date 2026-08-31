"""MI_planter - card at PROP scale, for kit beds and pots.

A bed is hand-sized. On card_heavy's 0.006 tooth - tuned for a 12 m wall - it
comes out as sacking; measured against 0.030 and 0.080 side by side, 0.030 is
the one that reads as card at this size. fabrication.card_prop carries that.
"""
import unreal
import _path  # noqa: F401
import fabrication

L = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
F = '/Game/Stacktown/Materials'
P = '%s/MI_planter' % F
if eal.does_asset_exist(P):
    eal.delete_asset(P)
if not eal.duplicate_asset('%s/MI_dist_buff' % F, P):
    raise SystemExit('could not duplicate MI_dist_buff')
mi = eal.load_asset(P)
for k, v in fabrication.params_for('MI_planter').items():
    L.set_material_instance_scalar_parameter_value(mi, k, v)
eal.save_asset(P, only_if_is_dirty=False)
got = L.get_material_instance_scalar_parameter_value(mi, 'PaperTiling')
want = fabrication.params_for('MI_planter')['PaperTiling']
assert abs(got - want) < 1e-6, (got, want)
assert fabrication.stock_for('MI_planter') == 'card_prop'
print('  MI_planter  stock=card_prop  tooth %.3f (wall stock is %.3f)'
      % (got, fabrication.STOCK['card_heavy'][0]))
