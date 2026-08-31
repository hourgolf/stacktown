"""One new instance: grass.

Ground surfaces are a genuinely new ROLE - MASTER_MATERIAL_SPEC's list has
concrete, paint, metal, glass, wood, brass and model_board, and none of them is
planting. Paving is just concrete and reuses MI_concrete, so this adds exactly
one asset rather than a family.

Copied from MI_concrete and differing only in BaseColour and a slightly higher
roughness, because in a card model a lawn is painted board, not a lawn: it has
the same tooth as everything else and reads green because it is green, not
because it is grassy. Flock and fibre are what a hobbyist adds LAST, and the
gate is about whether the fabrication reads, not whether the botany does.
"""
import unreal

SRC = 'MI_concrete'
NEW = {'MI_grass': ((0.255, 0.330, 0.212), 0.70, 0.86)}   # colour, roughMin, roughMax

MIL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
src = unreal.load_asset('/Game/Stacktown/Materials/%s' % SRC)
master = src.get_editor_property('parent')

for name, (col, rmin, rmax) in NEW.items():
    path = '/Game/Stacktown/Materials/%s' % name
    mi = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else \
        tools.create_asset(name, '/Game/Stacktown/Materials',
                           unreal.MaterialInstanceConstant,
                           unreal.MaterialInstanceConstantFactoryNew())
    MIL.set_material_instance_parent(mi, master)
    for so in src.get_editor_property('scalar_parameter_values'):
        MIL.set_material_instance_scalar_parameter_value(
            mi, so.parameter_info.name, so.parameter_value)
    MIL.set_material_instance_scalar_parameter_value(mi, 'RoughMin', rmin)
    MIL.set_material_instance_scalar_parameter_value(mi, 'RoughMax', rmax)
    MIL.set_material_instance_vector_parameter_value(
        mi, 'BaseColour', unreal.LinearColor(col[0], col[1], col[2], 1.0))
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    print('%-12s BaseColour (%.3f %.3f %.3f)  rough %.2f-%.2f  parent %s'
          % (name, col[0], col[1], col[2], rmin, rmax, master.get_name()))
