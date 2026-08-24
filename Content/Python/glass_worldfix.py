"""Place the window interiors in WORLD space.

Bug: the recess was computed in component-local space, but the C3 imperfection
pass gave each floor actor its own offset and rotation. Floor 2's back wall had
local y=55 but WORLD y=70.19 - behind the core mass, which starts at y=60. So
the camera was looking through the glass at bright concrete.

Local-space placement is unsafe once the parent actors are deliberately askew.
Everything here is positioned by world Y against the fixed core plane.
"""
import unreal

F = '/Game/Stacktown/Materials'
L = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

CORE_FACE = 60.0
BACK = CORE_FACE - 4.0        # back wall just in front of the core
ROOM_FRONT = BACK - 13.0      # ~130 mm of visible interior depth

# restore the diagnostic colours
for name, c in (('MI_interior', (0.030, 0.030, 0.033)),
                ('MI_concrete', (0.700, 0.672, 0.616))):
    p = '%s/%s' % (F, name)
    mi = unreal.EditorAssetLibrary.load_asset(p + '.' + name)
    L.set_material_instance_vector_parameter_value(
        mi, 'BaseColour', unreal.LinearColor(c[0], c[1], c[2], 1.0))
    unreal.EditorAssetLibrary.save_asset(p)
print('diagnostic colours restored')

back = room = 0
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith('BLD_Floor_'):
        continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        nm = c.get_name()
        w = c.get_world_location()
        if nm.startswith('Reveal'):
            c.set_world_location(unreal.Vector(w.x, BACK, w.z), False, False)
            back += 1
        elif nm.startswith(('RoomFloor', 'RoomCeil', 'RoomSide')):
            c.set_world_location(
                unreal.Vector(w.x, (ROOM_FRONT + BACK) / 2.0, w.z), False, False)
            s = c.get_editor_property('relative_scale3d')
            c.set_editor_property('relative_scale3d',
                                  unreal.Vector(s.x, (BACK - ROOM_FRONT) / 100.0, s.z))
            room += 1

print('back walls %d -> world y=%.0f, room surfaces %d spanning %.0f..%.0f'
      % (back, BACK, room, ROOM_FRONT, BACK))

# verify against the core plane
bad = 0
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith('BLD_Floor_'):
        continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if c.get_name().startswith('Reveal'):
            if c.get_world_location().y >= CORE_FACE:
                bad += 1
print('back walls still behind the core: %d (must be 0)' % bad)
les.save_current_level()
print('saved')
