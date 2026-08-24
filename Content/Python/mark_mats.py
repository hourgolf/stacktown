"""Two role instances for the fabrication-marks pass.

MI_glue — dried PVA squeeze-out. The whole point is that it breaks the card's
material band: card is 0.62-0.78 rough at 0.20 specular, glue is 0.26-0.38 at
0.42. Roughness and specular are the two properties the recipe says still read
at range, so a glossier, slightly yellower bead is legible as a DIFFERENT
substance rather than a lump of the same card. Paper normal drops to 0.10
because glue soaks into and fills the fibre. Seams off — glue is not a sheet.

MI_card_lift — card whose cut edge has lifted. Same colour family, but the
exposed core is lighter and the fibre is rougher and more pronounced, so
EdgeWearLift goes 1.42 -> 1.62 and PaperNormalAmount 0.55 -> 0.78. Seams off:
a lifted flap is a torn edge, not a joint.
"""
import unreal

L = unreal.MaterialEditingLibrary
F = '/Game/Stacktown/Materials'
master = unreal.EditorAssetLibrary.load_asset(
    '/Game/Stacktown/Materials/M_StacktownMaster.M_StacktownMaster')
at = unreal.AssetToolsHelpers.get_asset_tools()

SPECS = {
    'MI_glue': (
        (0.740, 0.700, 0.598),
        {'RoughMin': 0.26, 'RoughMax': 0.38, 'Metallic': 0.0, 'Specular': 0.42,
         'Opacity': 1.0, 'PaperTiling': 0.05, 'PaperNormalAmount': 0.10,
         'EdgeWearWidth': 0.30, 'EdgeWearLift': 1.00,
         'SeamSpacing': 380.0, 'SeamWidth': 6.0, 'SeamDarken': 1.0}),
    'MI_card_lift': (
        (0.812, 0.782, 0.712),
        {'RoughMin': 0.66, 'RoughMax': 0.84, 'Metallic': 0.0, 'Specular': 0.20,
         'Opacity': 1.0, 'PaperTiling': 0.05, 'PaperNormalAmount': 0.78,
         'EdgeWearWidth': 0.30, 'EdgeWearLift': 1.62,
         'SeamSpacing': 380.0, 'SeamWidth': 6.0, 'SeamDarken': 1.0}),
}

for name, (col, scalars) in SPECS.items():
    path = '%s/%s' % (F, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mi = unreal.EditorAssetLibrary.load_asset(path + '.' + name)
    else:
        mi = at.create_asset(name, F, unreal.MaterialInstanceConstant,
                             unreal.MaterialInstanceConstantFactoryNew())
    L.set_material_instance_parent(mi, master)
    L.set_material_instance_vector_parameter_value(
        mi, 'BaseColour', unreal.LinearColor(col[0], col[1], col[2], 1.0))
    for k, v in scalars.items():
        L.set_material_instance_scalar_parameter_value(mi, k, v)
    unreal.EditorAssetLibrary.save_asset(path)
    print('%-14s rough %.2f-%.2f spec %.2f  wear %.2f  seams %s'
          % (name, scalars['RoughMin'], scalars['RoughMax'], scalars['Specular'],
             scalars['EdgeWearLift'],
             'off' if scalars['SeamDarken'] == 1.0 else 'on'))
