"""Place the baked building and hide the component version for comparison.

StaticMeshActor can be spawned straight from Python, so a baked building costs
ZERO MCP round trips - not one. Materials bind by slot NAME, which is the same
role vocabulary the component sweep uses.
"""
import unreal

ROLE = {'Wall': 'MI_card_ochre', 'Band': 'MI_card_ochre', 'Glass': 'MI_glass_b',
        'Interior': 'MI_interior', 'Frame': 'MI_frame_print',
        'Mullion': 'MI_frame_print', 'Roof': 'MI_concrete',
        'Accent': 'MI_canopy_accent'}
F = '/Game/Stacktown/Materials'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label() == 'BAKE_Narrow':
        eas.destroy_actor(a)

sm = unreal.EditorAssetLibrary.load_asset(
    '/Game/Stacktown/Meshes/SM_BakeN4.SM_BakeN4')
act = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                 unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
act.set_actor_label('BAKE_Narrow')
comp = act.static_mesh_component
comp.set_editor_property('static_mesh', sm)
slots = sm.get_editor_property('static_materials')
for i, s in enumerate(slots):
    nm = str(s.material_slot_name)
    mat = unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (F, ROLE[nm], ROLE[nm]))
    comp.set_material(i, mat)
print('placed BAKE_Narrow, %d slots bound' % len(slots))

hidden = 0
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith('BLD2_Narrow'):
        a.set_actor_hidden_in_game(True)
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            c.set_visibility(False, True)
            c.set_hidden_in_game(True, True)
        hidden += 1
print('hid %d component-version actors' % hidden)
les.save_current_level()
