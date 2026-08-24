"""Retarget the BLD_Marks components onto the real meshes and materials.

add_cube leaves a Cube scaled to the requested dimensions, so scale MUST be
reset to 1 after the mesh swap or the chamfered profile is squashed.
"""
import unreal, json

TABLE = ('/private/tmp/claude-501/-Users-ben-Documents-New-project/'
         'c7b8ef13-3903-46ab-bd2b-18279bb95fe6/scratchpad/marks_table.json')
marks = {m['name']: m for m in json.load(open(TABLE))}

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
a = acts['BLD_Marks']

mesh_cache, mat_cache = {}, {}
def mesh(n):
    if n not in mesh_cache:
        mesh_cache[n] = unreal.EditorAssetLibrary.load_asset(
            '/Game/Stacktown/Meshes/%s.%s' % (n, n))
    return mesh_cache[n]
def mat(n):
    if n not in mat_cache:
        mat_cache[n] = unreal.EditorAssetLibrary.load_asset(
            '/Game/Stacktown/Materials/%s.%s' % (n, n))
    return mat_cache[n]

done, missing = 0, []
for c in a.get_components_by_class(unreal.StaticMeshComponent):
    m = marks.get(c.get_name())
    if not m:
        missing.append(c.get_name())
        continue
    sm = mesh(m['mesh'])
    if not sm:
        missing.append(m['mesh'])
        continue
    c.set_editor_property('static_mesh', sm)
    c.set_material(0, mat(m['mat']))
    c.set_world_location(unreal.Vector(*m['loc']), False, False)
    c.set_world_rotation(unreal.Rotator(m['rot'][2], m['rot'][0], m['rot'][1]), False, False)
    sc = float(m.get('scale', 1.0))
    c.set_world_scale3d(unreal.Vector(sc, sc, sc))
    done += 1
print('retargeted %d components' % done)
if missing:
    print('UNRESOLVED:', missing)

for c in a.get_components_by_class(unreal.StaticMeshComponent)[:3]:
    l = c.get_world_location(); s = c.get_world_scale()
    print('  %-16s %-11s scale %.2f  at (%.0f,%.0f,%.0f)'
          % (c.get_name(), c.static_mesh.get_name(), s.x, l.x, l.y, l.z))
les.save_current_level()
print('level saved')
