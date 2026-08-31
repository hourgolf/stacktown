"""Create the two *_2S instances the vehicles need and nobody had made.

MI_glass_b and MI_interior have no two-sided counterpart, so wiring the
vehicles would have left their glazing and cabin cards still culling. Every
override is copied from the non-2S instance so the two differ ONLY in which
master they point at - that is the entire justification for a 2S variant
existing at all, and it stops being true the moment the values drift.
"""
import unreal

MASTER = unreal.load_asset('/Game/Stacktown/Materials/M_StacktownMaster_2S')
MIL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

# MI_card_lift joined the fleet with the vegetable truck and had no two-sided
# sibling, so step_veh2s reported "2 had no counterpart" and those two slots
# stayed single-sided - i.e. see-through bodywork, the defect this whole
# mechanism exists to fix.
for src_name in ('MI_glass_b', 'MI_interior', 'MI_card_lift'):
    dst_name = src_name + '_2S'
    dst_path = '/Game/Stacktown/Materials/%s' % dst_name
    src = unreal.load_asset('/Game/Stacktown/Materials/%s' % src_name)
    if not src:
        print('MISSING source', src_name); continue
    if unreal.EditorAssetLibrary.does_asset_exist(dst_path):
        dst = unreal.load_asset(dst_path)
    else:
        dst = tools.create_asset(dst_name, '/Game/Stacktown/Materials',
                                 unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew())
    MIL.set_material_instance_parent(dst, MASTER)
    n = 0
    for so in src.get_editor_property('scalar_parameter_values'):
        MIL.set_material_instance_scalar_parameter_value(
            dst, so.parameter_info.name, so.parameter_value); n += 1
    for vo in src.get_editor_property('vector_parameter_values'):
        MIL.set_material_instance_vector_parameter_value(
            dst, vo.parameter_info.name, vo.parameter_value); n += 1
    for to in src.get_editor_property('texture_parameter_values'):
        if to.parameter_value:
            MIL.set_material_instance_texture_parameter_value(
                dst, to.parameter_info.name, to.parameter_value); n += 1
    unreal.EditorAssetLibrary.save_asset(dst_path, only_if_is_dirty=False)
    print('%-18s <- %-14s parent=%s, %d overrides copied'
          % (dst_name, src_name, dst.get_editor_property('parent').get_name(), n))

# prove the pair now differs only in master
for a, b in (('MI_glass_b', 'MI_glass_b_2S'), ('MI_interior', 'MI_interior_2S')):
    A = unreal.load_asset('/Game/Stacktown/Materials/%s' % a)
    B = unreal.load_asset('/Game/Stacktown/Materials/%s' % b)
    da = {s.parameter_info.name: round(s.parameter_value, 5)
          for s in A.get_editor_property('scalar_parameter_values')}
    db = {s.parameter_info.name: round(s.parameter_value, 5)
          for s in B.get_editor_property('scalar_parameter_values')}
    print('  %s vs %s scalars identical: %s' % (a, b, da == db))
