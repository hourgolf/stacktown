"""Static-only survey: trees and street props on the block's sidewalk.

Skeletal meshes are deliberately excluded here. Spawning them and assigning the
DEPRECATED `skeletal_mesh` property tripped
    Assertion failed: VertexFactory->IsReadyForStaticMeshCaching()
    [SkeletalRenderGPUSkin.cpp:2071]
and killed the editor on the next frame. The correct call is
`set_skinned_asset_and_update()`; that gets tested separately, one asset at a
time, so a repeat costs one mesh rather than a session.
"""
import unreal

M = '/Game/AssetsvilleTown/Meshes'
F = '/Game/Stacktown/Materials'
SLOT = {'Glass': 'MI_glass_b', 'colorPalette': 'MI_frame_print'}
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
_m = {}
def mat(n):
    if n not in _m:
        _m[n] = unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (F, n, n))
    return _m[n]

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('SUR_'):
        eas.destroy_actor(a)

def put(folder, name, x, y, yaw, label, colour, scale=1.0):
    sm = unreal.EditorAssetLibrary.load_asset('%s/%s/%s.%s' % (M, folder, name, name))
    if not sm:
        print('  missing', name); return
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, 0),
                                   unreal.Rotator(0, 0, yaw))
    a.set_actor_label('SUR_' + label)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    c = a.static_mesh_component
    c.set_editor_property('static_mesh', sm)
    for i, s in enumerate(sm.get_editor_property('static_materials')):
        c.set_material(i, mat(SLOT.get(str(s.material_slot_name), colour)))
    return a

n = 0
for i, nm in enumerate(('SM_tree_01', 'SM_tree_03', 'SM_treeLowPoly_01', 'SM_tree_02')):
    put('Nature', nm, 420 + i * 1080, -300.0, -20 + i * 37, 'tree%d' % i, 'MI_card_sage'); n += 1
for i, nm in enumerate(('SM_Bicycle_01', 'SM_barrel_1', 'SM_airCondition_01',
                        'SM_Water_Tank_01', 'SM_bush_01')):
    folder = 'Nature' if nm == 'SM_bush_01' else 'StreetProps'
    put(folder, nm, 900 + i * 700, -160.0, 15 + i * 44, 'prop%d' % i,
        'MI_frame_print' if i < 3 else 'MI_concrete'); n += 1
print('placed %d static survey items' % n)
les.save_current_level()
