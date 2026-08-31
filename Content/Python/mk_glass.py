"""Tinted curtain-wall glass, one instance per district glass colour.

CANON SLOT 5 (highrise), blessed for the highrise city read and for
"kit-family coherence - wildly different buildings cohering because one
fabrication family made them". Its towers are teal, green, black and cream:
each tower is ONE colour and the variety lives BETWEEN buildings. Our glass
was a single dark grey on every tower, which throws away the one thing that
image says carries a highrise skyline.

Built on the same master and the same optical numbers as MI_glass_b - only
BaseColour moves. That is the fabrication-family rule: one recipe, many
colours, so a teal tower and a bronze tower are obviously siblings.
"""
import unreal

MASTER = '/Game/Stacktown/Materials/M_StacktownMaster'
# name: BaseColour. Values sit in the same range as MI_glass_b (0.06-0.11)
# so they read as GLASS - a saturated tint at wall brightness reads as
# painted card, which is the trap.
GLASS = [
    ('MI_glass_teal',   (0.048, 0.092, 0.098)),
    ('MI_glass_green',  (0.052, 0.094, 0.066)),
    ('MI_glass_bronze', (0.108, 0.080, 0.050)),
    ('MI_glass_ink',    (0.055, 0.058, 0.068)),
    ('MI_glass_sky',    (0.062, 0.086, 0.118)),
]
OPTICS = {'RoughMin': 0.040, 'RoughMax': 0.120, 'Metallic': 0.0,
          'Specular': 0.520, 'Opacity': 0.450, 'SeamDarken': 1.0,
          'PaperNormalAmount': 0.0, 'PaperTiling': 0.0}

tools = unreal.AssetToolsHelpers.get_asset_tools()
master = unreal.load_asset(MASTER)
MEL = unreal.MaterialEditingLibrary
made = 0
for name, col in GLASS:
    path = '/Game/Stacktown/Materials/%s' % name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mi = unreal.load_asset(path)
    else:
        mi = tools.create_asset(name, '/Game/Stacktown/Materials',
                                unreal.MaterialInstanceConstant,
                                unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, master)
    for k, v in OPTICS.items():
        MEL.set_material_instance_scalar_parameter_value(mi, k, v)
    MEL.set_material_instance_vector_parameter_value(
        mi, 'BaseColour', unreal.LinearColor(col[0], col[1], col[2], 1.0))
    unreal.EditorAssetLibrary.save_asset(path)
    got = MEL.get_material_instance_vector_parameter_value(mi, 'BaseColour')
    ok = all(abs(g - c) < 1e-3 for g, c in ((got.r, col[0]), (got.g, col[1]),
                                            (got.b, col[2])))
    print('  %-18s (%.3f,%.3f,%.3f) %s' % (name, got.r, got.g, got.b,
                                           'ok' if ok else '*** NOT SET ***'))
    assert ok, name
    made += 1
print('mk_glass: %d instances' % made)
