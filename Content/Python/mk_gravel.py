"""MI_gravel - compacted ground for a works yard.

The yard was authored with three surfaces and rendered as one flat tone. The
bindings were all correct; the fault was that I reached for MI_precast_buff
because the NAME sounded tan. Measured, it is (0.745, 0.700, 0.612) against
MI_concrete's (0.700, 0.672, 0.616) - the blue channel differs by 0.004. Two
materials that are the same colour cannot separate two surfaces no matter how
correctly they are bound.

Duplicated from MI_concrete so every other card parameter - paper fibre, seam
chain, wear, specular - matches a ground material that already works, and only
colour and roughness move. The delta against concrete is asserted below,
because "it looks different in the editor" is what got us here.
"""
import unreal

SRC = '/Game/Stacktown/Materials/MI_concrete'
DST = '/Game/Stacktown/Materials/MI_gravel'
COL = (0.430, 0.365, 0.270)      # compacted earth, warmer and clearly darker
# Per-channel, against the surface it must read against. 0.10 was the first
# guess and it PASSED a colour that was invisible in the render - the scene is
# brightly lit and the tonemapper compresses the top end, so a small albedo
# gap disappears. 0.25 is what actually separated the two on screen, proved by
# flagging the material magenta to confirm the surface was rendering at all.
MIN_DELTA = 0.25

if unreal.EditorAssetLibrary.does_asset_exist(DST):
    unreal.EditorAssetLibrary.delete_asset(DST)
if not unreal.EditorAssetLibrary.duplicate_asset(SRC, DST):
    raise SystemExit('could not duplicate %s' % SRC)
mi = unreal.load_asset(DST)
mel = unreal.MaterialEditingLibrary
mel.set_material_instance_vector_parameter_value(
    mi, 'BaseColour', unreal.LinearColor(COL[0], COL[1], COL[2], 1.0))
# loose ground scatters more than a laid slab
mel.set_material_instance_scalar_parameter_value(mi, 'RoughMin', 0.78)
mel.set_material_instance_scalar_parameter_value(mi, 'RoughMax', 0.94)
unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)

src = unreal.load_asset(SRC)
a = mel.get_material_instance_vector_parameter_value(src, 'BaseColour')
b = mel.get_material_instance_vector_parameter_value(mi, 'BaseColour')
d = (abs(a.r-b.r), abs(a.g-b.g), abs(a.b-b.b))
print('MI_concrete (%.3f %.3f %.3f)' % (a.r, a.g, a.b))
print('MI_gravel   (%.3f %.3f %.3f)' % (b.r, b.g, b.b))
print('delta       (%.3f %.3f %.3f)  min required %.2f' % (d + (MIN_DELTA,)))
if min(d) < MIN_DELTA:
    raise AssertionError('MI_gravel does not separate from MI_concrete - '
                         'this is exactly the MI_precast_buff mistake again')
print('OK: the two ground surfaces are measurably different')
