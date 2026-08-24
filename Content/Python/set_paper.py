"""Working paper amplitude on every card role.

Measured response: amount 0.55 -> sd 0.48, amount 3.00 -> sd 2.07. It is the
only lever that moves; PaperTiling is inert (0.05 -> 0.20 changed sd 0.48 ->
0.45) even though T_PaperNormal and T_PaperDetail are bound on both master and
instance, so the tiling parameter is not reaching those samplers' UVs.

2.0 is a real improvement without being an extreme normal. Closing the gap
properly is a graph job, not a parameter."""
import unreal
L=unreal.MaterialEditingLibrary
F='/Game/Stacktown/Materials'
for n in ('MI_card_ochre','MI_card_sage','MI_card_rose','MI_paint_cream','MI_concrete'):
    p='%s/%s'%(F,n)
    mi=unreal.EditorAssetLibrary.load_asset(p+'.'+n)
    if not mi: continue
    L.set_material_instance_scalar_parameter_value(mi,'PaperNormalAmount',2.0)
    L.set_material_instance_scalar_parameter_value(mi,'PaperTiling',0.05)
    unreal.EditorAssetLibrary.save_asset(p)
    print('%-16s paperNormal -> 2.00'%n)
