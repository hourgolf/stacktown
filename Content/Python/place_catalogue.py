"""Place baked catalogue meshes on a display pad, and upgrade one in place.

This is the end of the vertical slice: recipe -> bake -> PLACE -> upgrade ->
swap. Placement is one StaticMeshActor per building, which is what a runtime
city needs; the 131-to-201 boxes each of these was generated from are gone.

The pad sits north of the board on its own slab. It is a catalogue, not part of
the city, and it is labelled so the invariants can tell the difference.
"""
import unreal, os, sys, json, tempfile
import _path  # noqa: F401
import recipes, grammar
from city import BOARD_N

# North of the CURRENT board top, sized for however many tiers the display
# recipe has. The old literal pad predated the northward growth and sat
# across street 0, collecting that street's parked cars and trees.
RID, W = 'vernacular', 1230.0
_PITCH = W + 320.0
PAD = (6200.0, BOARD_N + 700.0,
       6200.0 + 500.0*2 + recipes.tier_count(RID)*_PITCH, BOARD_N + 2400.0)
OUT = '/Game/Stacktown/Baked'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

n = 0
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('CAT_'):
        eas.destroy_actor(a); n += 1
print('removed %d CAT_ actors' % n)


def put(mesh_path, label, x, y, yaw=0.0):
    sm = unreal.load_asset(mesh_path)
    if not sm:
        print('  MISSING %s' % mesh_path); return 0
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                   unreal.Vector(x, y, 0.0),
                                   unreal.Rotator(0, 0, yaw))
    a.set_actor_label('CAT_' + label)
    a.static_mesh_component.set_editor_property('static_mesh', sm)
    return 1


# the pad itself
slab = eas.spawn_actor_from_class(
    unreal.StaticMeshActor,
    unreal.Vector((PAD[0]+PAD[2])/2.0, (PAD[1]+PAD[3])/2.0, -6.0),
    unreal.Rotator(0, 0, 0))
slab.set_actor_label('CAT_Pad')
cube = unreal.load_asset('/Engine/BasicShapes/Cube.Cube')
slab.static_mesh_component.set_editor_property('static_mesh', cube)
slab.set_actor_scale3d(unreal.Vector((PAD[2]-PAD[0])/100.0,
                                     (PAD[3]-PAD[1])/100.0, 0.12))
slab.static_mesh_component.set_material(
    0, unreal.load_asset('/Game/Stacktown/Materials/MI_model_board.MI_model_board'))

# every tier of one recipe, side by side: the SAME building, grown
rid = RID
placed = 0
for t in range(recipes.tier_count(rid)):
    x = PAD[0] + 500.0 + t*_PITCH
    placed += put('%s/%s' % (OUT, recipes.asset_name(rid, t, W)),
                  '%s_t%d' % (rid, t), x, PAD[1] + 700.0)
print('placed %d catalogue buildings (%s tiers %s)'
      % (placed, rid, ', '.join(recipes.tier_name(rid, t)
                                for t in range(recipes.tier_count(rid)))))

# and what the grammar would choose for that parcel at three levels
for lvl in (0.0, 0.5, 1.0):
    print('  grammar: parcel %dx%d commercial level %.1f -> %s'
          % (W, 700, lvl, grammar.pick(W, 700.0, 'commercial', level=lvl, seed=3)))
les.save_current_level()
