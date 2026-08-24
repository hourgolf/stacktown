"""Build the Assetsville lot as a CLOSED VOLUME from its own tileset.

Replaces CORE_AV - a raw box dropped in as a stopgap, which terminated against
its neighbour with no corner and read as embedded in it even though a 72 uu gap
was measured between them.

Module pivots are corner-based: SM_wall_01 occupies local Y -400..0, Z 0..300,
X -15..15. Under yaw 90 that becomes world X P..P+400, thin in Y. Under yaw 0 it
stays world Y P-400..P, thin in X. Everything below is placed from that.

    lot   X 2020..3220 (3 modules)   depth 800 (2)   height 900 (3 floors)
"""
import unreal

B = '/Game/AssetsvilleTown/Meshes/BuildingTilset'
F = '/Game/Stacktown/Materials'
SLOT = {'Glass': 'MI_glass_b', 'colorPalette': 'MI_frame_print'}
BODY = 'MI_card_sage'
X0, X1, D, FH, FLOORS = 2020.0, 3220.0, 800.0, 300.0, 3

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
_m = {}
def M(n):
    if n not in _m:
        _m[n] = unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (F, n, n))
    return _m[n]

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith(('AV_', 'CORE_AV')):
        eas.destroy_actor(a)

n = 0
def put(mesh, x, y, z, yaw, tag):
    global n
    sm = unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (B, mesh, mesh))
    if not sm:
        print('  missing', mesh); return
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z),
                                   unreal.Rotator(0, 0, yaw))
    a.set_actor_label('AV_%s%d' % (tag, n))
    c = a.static_mesh_component
    c.set_editor_property('static_mesh', sm)
    for i, s in enumerate(sm.get_editor_property('static_materials')):
        c.set_material(i, M(SLOT.get(str(s.material_slot_name), BODY)))
    n += 1

# --- front (faces -Y): yaw 90, module spans X P..P+400 -----------------------
put('SM_shopFront_01', X0, 0.0, 0.0, 90, 'shop')          # 800 wide
put('SM_wall_01', X0 + 800, 0.0, 0.0, 90, 'gfwall')
for f in range(1, FLOORS):
    for b in range(3):
        put('SM_window_01', X0 + b * 400, 0.0, f * FH, 90, 'win')

# --- rear (Y = D) ------------------------------------------------------------
for f in range(FLOORS):
    for b in range(3):
        put('SM_wall_01', X0 + b * 400, D, f * FH, 90, 'rear')

# --- flanks (yaw 0: module spans Y P-400..P, thin in X) ----------------------
for x in (X0, X1):
    for f in range(FLOORS):
        for yy in (400.0, 800.0):
            put('SM_wall_01', x, yy, f * FH, 0, 'flank')

# --- parapet across the front, and a roof cap --------------------------------
for b in range(3):
    put('SM_wallAttic_01', X0 + b * 400, 0.0, FLOORS * FH, 90, 'attic')
for bx in range(3):
    for by in range(2):
        put('SM_floor_01', X0 + 200 + bx * 400, 200.0 + by * 400, FLOORS * FH, 0, 'roof')

print('AV lot rebuilt: %d modules' % n)
les.save_current_level()
