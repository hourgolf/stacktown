"""Glass rework — give it somewhere to be.

The close-up showed the failure clearly: the interior card sat 2 uu behind the
glazing, so there was no interior at all. A pane with a wall immediately behind
it is a painted dark rectangle, not a window, at any range.

MASTER_MATERIAL_SPEC's glass rule names three requirements: frame depth (have
it), a reflection that responds to an environment, and SOMETHING BEHIND IT.
The third was nominally satisfied and actually wasn't - the card was too close
to read as depth.

Fix: push the interior back to make a real recess, add a floor and ceiling so
light falls off with depth, and retune the glass to actually reflect.
"""
import unreal

F = '/Game/Stacktown/Materials'
L = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# --- glass that behaves like glass ---
for name, opacity in (('MI_glass', 0.16), ('MI_glass_b', 0.19)):
    p = '%s/%s' % (F, name)
    mi = unreal.EditorAssetLibrary.load_asset(p + '.' + name)
    L.set_material_instance_scalar_parameter_value(mi, 'RoughMin', 0.015)
    L.set_material_instance_scalar_parameter_value(mi, 'RoughMax', 0.045)
    L.set_material_instance_scalar_parameter_value(mi, 'Specular', 1.0)
    L.set_material_instance_scalar_parameter_value(mi, 'Opacity', opacity)
    unreal.EditorAssetLibrary.save_asset(p)
    print('%s  rough 0.015-0.045  spec 1.00  opacity %.2f' % (name, opacity))

# --- push interiors back and build a shallow room behind each opening ---
BAYS = [(60.0, 300.0), (420.0, 660.0), (780.0, 1020.0)]
GF_H, FL_H = 420.0, 360.0
BAND_COURSE = 44.0
RECESS = 25.0
DEPTH = 46.0          # interior back wall this far behind the glazing

acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}


interior = unreal.EditorAssetLibrary.load_asset(F + '/MI_interior.MI_interior')
dark = unreal.EditorAssetLibrary.load_asset(F + '/MI_frame_print.MI_frame_print')

moved = added = 0
for n in range(1, 5):
    a = acts.get('BLD_Floor_%d' % n)
    if not a:
        continue
    z0 = GF_H + (n - 1) * FL_H
    z1 = z0 + FL_H
    wz0, wz1 = z0 + BAND_COURSE, z1 - 55
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        nm = c.get_name()
        if not nm.startswith('Reveal'):
            continue
        loc = c.get_editor_property('relative_location')
        s = c.get_editor_property('relative_scale3d')
        # push the back wall from ~27 uu to DEPTH behind the facade
        c.set_editor_property('relative_location',
                              unreal.Vector(loc.x, RECESS + DEPTH, loc.z))
        moved += 1

print('pushed %d interior walls back to %.0f mm' % (moved, DEPTH * 10))
les.save_current_level()
print('saved')
