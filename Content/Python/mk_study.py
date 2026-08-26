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
# ROUND 2. Round 1 moved one term each and found only ONE that did measurable
# work at building distance: PaperTiling. Everything else - normal strength,
# seam darkness, edge wear, base colour - moved the render by less than the
# noise. So round 2 sweeps the lever that works instead of re-testing the ones
# that do not.
#
# Panels 0-4 are a pure tiling sweep, one variable. Panel 5 is a COMBINATION
# and is labelled as such: it is a candidate to look at, not a measurement,
# because three terms move at once and nothing it shows can be attributed.
VARIANTS = [
    ('MI_st0_t050', {'PaperTiling': 0.050}, BASE),   # current default
    ('MI_st1_t025', {'PaperTiling': 0.025}, BASE),
    ('MI_st2_t012', {'PaperTiling': 0.012}, BASE),   # round 1 winner
    ('MI_st3_t006', {'PaperTiling': 0.006}, BASE),
    ('MI_st4_t003', {'PaperTiling': 0.003}, BASE),
    ('MI_st5_combo', {'PaperTiling': 0.012, 'SeamDarken': 0.62,
                      'SeamSpacing': 190.0, 'EdgeWearLift': 2.20},
     (0.700, 0.668, 0.600)),
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
