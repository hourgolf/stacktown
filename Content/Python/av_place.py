"""Assemble an Assetsville facade in the Wide lot, in the block's own light.

Their module is 400 wide x 300 tall x 30 thick, running along local Y and
facing local X - so every piece needs yaw 90 to face our -Y street. 1 uu = 1 cm
in both, so no scaling: their 300 uu floor sits directly against our 330-380.

Materials bind by SLOT NAME, the same mechanism the generated block uses. Their
slots are customMat_NN / colorPalette / Glass, so the mapping is by convention
rather than by role - workable for a tileset where the mesh name carries the
identity, and the reason the four complete buildings (customMat_01..14) are a
worse fit than the kit.
"""
import unreal

B = '/Game/AssetsvilleTown/Meshes/BuildingTilset'
F = '/Game/Stacktown/Materials'
SLOT = {'Glass': 'MI_glass_b', 'colorPalette': 'MI_frame_print'}
DEFAULT = 'MI_card_sage'

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
_m = {}
def M(n):
    if n not in _m:
        _m[n] = unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (F, n, n))
    return _m[n]

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('AV_'):
        eas.destroy_actor(a)

hidden = 0
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith('BLD2_Wide'):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            c.set_visibility(False, True); c.set_hidden_in_game(True, True)
        hidden += 1
print('hid %d BLD2_Wide actors' % hidden)

def place(mesh, x, z, label):
    sm = unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (B, mesh, mesh))
    if not sm:
        print('  MISSING', mesh); return
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                   unreal.Vector(x, 0.0, z), unreal.Rotator(0, 0, 90))   # (roll, pitch, yaw) - yaw is the THIRD arg
    a.set_actor_label('AV_' + label)
    c = a.static_mesh_component
    c.set_editor_property('static_mesh', sm)
    for i, s in enumerate(sm.get_editor_property('static_materials')):
        c.set_material(i, M(SLOT.get(str(s.material_slot_name), DEFAULT)))
    return a

X0 = 2020.0
n = 0
# ground floor: shopfront (800 wide) + one wall module
place('SM_shopFront_01', X0 + 800, 0, 'shop'); n += 1
place('SM_wall_01', X0 + 1000, 0, 'gfwall'); n += 1
# two upper floors of windows, three bays each
for f, z in ((1, 300.0), (2, 600.0)):
    for b in range(3):
        place('SM_window_01', X0 + 200 + b * 400, z, 'w%d_%d' % (f, b)); n += 1
# cornice and a flat roof cap
place('SM_cornice_01', X0 + 800, 900.0, 'cornice'); n += 1
for b in range(3):
    place('SM_roof_01', X0 + 200 + b * 400, 900.0, 'roof%d' % b); n += 1
print('placed %d Assetsville pieces' % n)
les.save_current_level()
