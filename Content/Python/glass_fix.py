"""Correct the glass recess to fit inside the wall.

Previous attempt pushed the interior back 460 mm, but the facade wall is only
350 mm thick (Y 0..60 uu) and the core mass begins at Y=60. The card ended up
behind the core, so the "interior" the camera saw was bright concrete.

Real depth available: glazing sits at Y=25, core starts at Y=60, so the recess
can be at most ~330 mm. Back wall goes to Y=55 and the room surfaces are
clamped to fit in front of it.
"""
import unreal

F = '/Game/Stacktown/Materials'
L = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

BACK = 55.0          # interior back wall, just in front of the core at Y=60
FRONT = 28.0         # just behind the glazing at Y=25..27

# glass: less transparent than the 0.16 that let the core show through,
# still glassy enough to reflect
for name, op in (('MI_glass', 0.30), ('MI_glass_b', 0.33)):
    p = '%s/%s' % (F, name)
    mi = unreal.EditorAssetLibrary.load_asset(p + '.' + name)
    L.set_material_instance_scalar_parameter_value(mi, 'Opacity', op)
    unreal.EditorAssetLibrary.save_asset(p)
    print('%s opacity %.2f' % (name, op))

fixed = clamped = 0
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith('BLD_Floor_'):
        continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        nm = c.get_name()
        loc = c.get_editor_property('relative_location')
        s = c.get_editor_property('relative_scale3d')
        if nm.startswith('Reveal'):
            # thin back wall at the rear of the recess
            c.set_editor_property('relative_scale3d',
                                  unreal.Vector(s.x, 0.03, s.z))
            c.set_editor_property('relative_location',
                                  unreal.Vector(loc.x, BACK, loc.z))
            fixed += 1
        elif nm.startswith(('RoomFloor', 'RoomCeil', 'RoomSide')):
            # span only the real recess depth
            depth = (BACK - FRONT) / 100.0
            c.set_editor_property('relative_scale3d',
                                  unreal.Vector(s.x, depth, s.z))
            c.set_editor_property('relative_location',
                                  unreal.Vector(loc.x, (FRONT + BACK) / 2.0, loc.z))
            clamped += 1

print('back walls %d, room surfaces clamped %d, recess depth %.0f mm'
      % (fixed, clamped, (BACK - FRONT) * 10))
les.save_current_level()
print('saved')
