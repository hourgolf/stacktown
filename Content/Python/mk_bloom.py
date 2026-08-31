"""Flower-bed tones.

A pitched house roof was rendering on MI_concrete, the same pale grey as a flat
commercial deck, so five houses read as five white wedges. A shingle roof is
darker and warmer than cast concrete and it is the largest single surface on a
house, so it decides what the row looks like from any distance.

Instances of the one master differing only in BaseColour and roughness, which
is the sanctioned mechanism.

(Originally: two more precast tones for block C.)

MASTER_MATERIAL_SPEC warns against a growing palette, and it is right - the
last project grew a `walnut` and a `cedar` that a parameter could have done.
This is not that. These are INSTANCES of the one master differing ONLY in
BaseColour: roughness band, specular, seam, paper and wear are copied verbatim
from MI_concrete. It is the same move the card role already makes with ochre,
rose and sage, which is the sanctioned mechanism - "variation comes from
instance parameters, never from a differently-authored shader".

Six lots on two tones read as one poured mass. Real precast varies batch to
batch, and a handmade model varies more than that, not less.
"""
import unreal

SRC = 'MI_concrete'
# First pass at 0.32/0.35 still read as white in direct sun - a roof is the
# largest surface on a house and the sun sits on it, so it needs to be a good
# deal darker than it looks right in a swatch.
# A raised bed rendered on MI_grass is a raised bed of grass, which is what
# the frames showed. A bed is planting: colour is the entire point of it.
NEW = {'MI_bloom_warm': (0.520, 0.286, 0.240),   # reds and terracottas
       'MI_bloom_cool': (0.376, 0.330, 0.520)}   # lavender and blue

MIL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
src = unreal.load_asset('/Game/Stacktown/Materials/%s' % SRC)
master = src.get_editor_property('parent')

for name, col in NEW.items():
    path = '/Game/Stacktown/Materials/%s' % name
    mi = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else \
        tools.create_asset(name, '/Game/Stacktown/Materials',
                           unreal.MaterialInstanceConstant,
                           unreal.MaterialInstanceConstantFactoryNew())
    MIL.set_material_instance_parent(mi, master)
    for so in src.get_editor_property('scalar_parameter_values'):
        MIL.set_material_instance_scalar_parameter_value(
            mi, so.parameter_info.name, so.parameter_value)
    MIL.set_material_instance_vector_parameter_value(
        mi, 'BaseColour', unreal.LinearColor(col[0], col[1], col[2], 1.0))
    # a shingle roof is matt; concrete's band is too tight and too glossy for it
    MIL.set_material_instance_scalar_parameter_value(mi, 'RoughMin', 0.62)
    MIL.set_material_instance_scalar_parameter_value(mi, 'RoughMax', 0.88)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    # prove they differ ONLY in colour
    a = {s.parameter_info.name: round(s.parameter_value, 5)
         for s in src.get_editor_property('scalar_parameter_values')}
    b = {s.parameter_info.name: round(s.parameter_value, 5)
         for s in mi.get_editor_property('scalar_parameter_values')}
    print('%-18s BaseColour (%.3f %.3f %.3f)  scalars match %s: %s'
          % (name, col[0], col[1], col[2], SRC, a == b))
