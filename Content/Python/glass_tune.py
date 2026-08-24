import unreal
F = '/Game/Stacktown/Materials'
L = unreal.MaterialEditingLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
# Back inside the spec's acrylic band. At 0.015 the pane mirrored the bright
# cream backdrop and hid the interior entirely; a model's acrylic glazing
# scatters enough that what is behind it still reads.
for name, rmin, rmax, spec, op in (('MI_glass', 0.055, 0.105, 0.55, 0.42),
                                   ('MI_glass_b', 0.065, 0.115, 0.52, 0.45)):
    p = '%s/%s' % (F, name)
    mi = unreal.EditorAssetLibrary.load_asset(p + '.' + name)
    L.set_material_instance_scalar_parameter_value(mi, 'RoughMin', rmin)
    L.set_material_instance_scalar_parameter_value(mi, 'RoughMax', rmax)
    L.set_material_instance_scalar_parameter_value(mi, 'Specular', spec)
    L.set_material_instance_scalar_parameter_value(mi, 'Opacity', op)
    unreal.EditorAssetLibrary.save_asset(p)
    print('%s rough %.3f-%.3f spec %.2f opacity %.2f' % (name, rmin, rmax, spec, op))
les.save_current_level()
print('saved')
