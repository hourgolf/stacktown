"""Room set follows its floor in Y, clamped to stay in front of the core.

First attempt used the floor-1-bay-0 relationship (reveal front = glass + 21.85)
unclamped. That is right where the facade sits forward and wrong where it has
drifted back: on floor 4 it put the reveal front at 68.18, behind the core's
front face at Y=60, so every top-floor window showed the core's cream
MI_concrete instead of a dark room.

Two constraints, not one:
    front > glass Y        or the reveal's outer face swallows the window
    front < 60             or the core shows through instead of the interior

So: front = clamp(glass Y + 21.85, 39.50, 56.00). 39.50 is the authored plane,
56.00 leaves 4 uu of clearance on the core. Bays that never drifted keep their
exact original numbers; only the drifted ones move.
"""
import unreal

AUTHORED_GAP = 21.85     # floor 1 bay 0: reveal front - glass
FRONT_MIN, FRONT_MAX = 39.50, 56.00
REVEAL_HALF, ROOM_OFFSET = 16.50, 10.00
CORE_FRONT = 60.0

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
ROOMS = ('RoomFloor', 'RoomCeil', 'RoomSideL', 'RoomSideR')

moved = 0
for f in range(1, 5):
    a = acts['BLD_Floor_%d' % f]
    cs = {c.get_name(): c for c in a.get_components_by_class(unreal.StaticMeshComponent)}
    for b in range(3):
        g = cs.get('Glass%d' % b)
        if not g:
            continue
        gy = g.get_world_location().y
        front = min(max(gy + AUTHORED_GAP, FRONT_MIN), FRONT_MAX)
        for base, y in [('Reveal', front + REVEAL_HALF)] + \
                       [(r, front + ROOM_OFFSET) for r in ROOMS]:
            c = cs.get('%s%d' % (base, b))
            if not c:
                continue
            l = c.get_world_location()
            if abs(l.y - y) > 0.01:
                c.set_world_location(unreal.Vector(l.x, y, l.z), False, False)
                moved += 1
print('moved %d room components' % moved)

fails = []
for f in range(1, 5):
    a = acts['BLD_Floor_%d' % f]
    cs = {c.get_name(): c for c in a.get_components_by_class(unreal.StaticMeshComponent)}
    for b in range(3):
        rv, gl, mh = cs.get('Reveal%d' % b), cs.get('Glass%d' % b), cs.get('MulH%d' % b)
        if not (rv and gl and mh):
            continue
        e = rv.static_mesh.get_bounds().box_extent.y * rv.get_world_scale().y
        front = rv.get_world_location().y - e
        gy, my = gl.get_world_location().y, mh.get_world_location().y
        if front <= gy or front <= my:
            fails.append((f, b, 'reveal in front of window', round(front - gy, 2)))
        if front >= CORE_FRONT:
            fails.append((f, b, 'core shows through', round(front, 2)))
        print('  f%d b%d  front %6.2f  glass %6.2f  room depth %5.2f  core clear %5.2f'
              % (f, b, front, gy, front - gy, CORE_FRONT - front))
print('FAILURES:', fails if fails else 'NONE')
les.save_current_level()
print('level saved')
