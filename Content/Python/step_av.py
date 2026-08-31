"""Assetsville lot, driven from lots.py rather than hardcoded."""
import unreal, sys, os
import _path  # repo tool paths; replaces a dead scratchpad path
from lots import LOTS

B='/Game/AssetsvilleTown/Meshes/BuildingTilset'
F='/Game/Stacktown/Materials'
SLOT={'Glass':'MI_glass_b','colorPalette':'MI_frame_print'}
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
_m={}
def M(n):
    if n not in _m: _m[n]=unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(F,n,n))
    return _m[n]

spec=[l for l in LOTS if l['kind']=='av'][0]
X0,W,D,FH,FL = spec['x0'],spec['width'],spec['depth'],spec['fl_h'],spec['floors']
BODY=spec['wall']
NB=int(W//400)
n=0
def put(mesh,x,y,z,yaw,tag):
    global n
    sm=unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(B,mesh,mesh))
    if not sm: print('  missing',mesh); return
    a=eas.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,y,z),
                                 unreal.Rotator(0,0,yaw))
    a.set_actor_label('AV_%s%d'%(tag,n))
    c=a.static_mesh_component
    c.set_editor_property('static_mesh',sm)
    for i,s in enumerate(sm.get_editor_property('static_materials')):
        c.set_material(i, M(SLOT.get(str(s.material_slot_name),BODY)))
    n+=1

put('SM_shopFront_01', X0, 0.0, 0.0, 90,'shop')
put('SM_wall_01', X0+800, 0.0, 0.0, 90,'gfwall')
for f in range(1,FL):
    for b in range(NB): put('SM_window_01', X0+b*400, 0.0, f*FH, 90,'win')
for f in range(FL):
    for b in range(NB): put('SM_wall_01', X0+b*400, D, f*FH, 90,'rear')
for x in (X0, X0+W):
    for f in range(FL):
        for yy in (400.0, D): put('SM_wall_01', x, yy, f*FH, 0,'flank')
for b in range(NB): put('SM_wallAttic_01', X0+b*400, 0.0, FL*FH, 90,'attic')
for bx in range(NB):
    for by in range(int(D//400)):
        put('SM_floor_01', X0+200+bx*400, 200.0+by*400, FL*FH, 0,'roof')
print('AV lot: %d modules, X %.0f..%.0f'%(n,X0-15,X0+W+15))
les.save_current_level()
