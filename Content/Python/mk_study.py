"""Material study variants: one parameter moved per panel, from one baseline.

The card look was authored on a material sphere and fails at building
distance: at a 3,100 uu standoff a 0.05-tiled paper normal is sub-pixel, and
a 0.78-luminance cream against a 0.75-luminance backdrop has no tonal
separation left to carry it. That is a hypothesis; this is how it gets tested.

Six panels, each differing from MI_paint_cream in exactly ONE term, so
whatever the capture shows can be attributed. Anything else is six new looks
and no information.
"""
import unreal

SRC = '/Game/Stacktown/Materials/MI_paint_cream'
BASE = (0.780, 0.748, 0.678)
VARIANTS = [
    ('MI_st0_base',   {},                                   BASE),
    ('MI_st1_darker', {},                                    (0.615, 0.585, 0.520)),
    ('MI_st2_paper',  {'PaperNormalAmount': 6.0},            BASE),
    ('MI_st3_coarse', {'PaperTiling': 0.012},                BASE),
    ('MI_st4_seams',  {'SeamDarken': 0.62, 'SeamSpacing': 190.0}, BASE),
    ('MI_st5_wear',   {'EdgeWearLift': 2.20, 'EdgeWearWidth': 0.60}, BASE),
]

mel = unreal.MaterialEditingLibrary
for name, scal, col in VARIANTS:
    path = '/Game/Stacktown/Materials/%s' % name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    if not unreal.EditorAssetLibrary.duplicate_asset(SRC, path):
        raise SystemExit('could not duplicate %s' % SRC)
    mi = unreal.load_asset(path)
    mel.set_material_instance_vector_parameter_value(
        mi, 'BaseColour', unreal.LinearColor(col[0], col[1], col[2], 1.0))
    for k, v in scal.items():
        mel.set_material_instance_scalar_parameter_value(mi, k, v)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    what = ', '.join('%s=%g' % kv for kv in sorted(scal.items())) or 'baseline'
    print('  %-14s (%.3f %.3f %.3f)  %s' % (name, col[0], col[1], col[2], what))
print('%d study variants' % len(VARIANTS))
