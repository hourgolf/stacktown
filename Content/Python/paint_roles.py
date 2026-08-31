"""White, navy and a blue roof - the estate office's palette.

The library had no white paint and no blue of ANY kind, which is why the
office's first bake came back monochrome cream: bone walls, slate trim and a
slate roof all sit within a few values of each other, and the reference's
whole character is white boarding against dark trim.

PAINTED BOARD, NOT CARD. These sit just below the card band's roughness -
0.55-0.70 against card's 0.62-0.80 - because a painted weatherboard is a
sealed surface where a cut card edge is not. Specular stays at the doctrine's
0.20 and the paper normal stays on: this is paint ON card, which is what a
model-maker actually has.

Albedo is kept off the extremes on purpose. Pure white and pure black are the
two values a fabricated surface never has, and the master spec's whole
argument is that a narrow band is what unifies mismatched sources.
"""
import unreal

L = unreal.MaterialEditingLibrary
F = '/Game/Stacktown/Materials'
master = unreal.EditorAssetLibrary.load_asset(
    F + '/M_StacktownMaster.M_StacktownMaster')
at = unreal.AssetToolsHelpers.get_asset_tools()

PAINT = {'RoughMin': 0.55, 'RoughMax': 0.70, 'Metallic': 0.0, 'Specular': 0.20,
         'Opacity': 1.0, 'PaperTiling': 0.05, 'PaperNormalAmount': 0.42,
         'EdgeWearWidth': 0.30, 'EdgeWearLift': 1.38, 'SeamSpacing': 380.0,
         'SeamWidth': 6.0, 'SeamDarken': 0.90}

COLS = {
    # off-white, not white: a painted board reads as white against its own
    # shadow, not against the page
    'MI_paint_white': (0.780, 0.780, 0.762),
    # the trim: barge boards, window frames, door
    'MI_paint_navy':  (0.038, 0.055, 0.098),
    # the roof sits LIGHTER than the trim so the two separate at distance -
    # one dark value doing both jobs reads as a single silhouette
    'MI_roof_blue':   (0.072, 0.105, 0.158),
}

for n, c in COLS.items():
    p = '%s/%s' % (F, n)
    mi = (unreal.EditorAssetLibrary.load_asset(p + '.' + n)
          if unreal.EditorAssetLibrary.does_asset_exist(p)
          else at.create_asset(n, F, unreal.MaterialInstanceConstant,
                               unreal.MaterialInstanceConstantFactoryNew()))
    L.set_material_instance_parent(mi, master)
    L.set_material_instance_vector_parameter_value(
        mi, 'BaseColour', unreal.LinearColor(c[0], c[1], c[2], 1.0))
    for k, v in PAINT.items():
        L.set_material_instance_scalar_parameter_value(mi, k, v)
    unreal.EditorAssetLibrary.save_asset(p)
    print('%-16s %.3f %.3f %.3f' % (n, c[0], c[1], c[2]))
