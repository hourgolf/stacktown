"""Board and street for two facing blocks.

Block A faces -Y from Y=0; block B faces +Y from Y=-1600. So the road runs
between them and each side needs its own pavement.
"""
import unreal, sys, math
sys.path.insert(0,'/private/tmp/claude-501/-Users-ben-Documents-New-project/c7b8ef13-3903-46ab-bd2b-18279bb95fe6/scratchpad')
from city import BLOCKS, STREET_FACE_A, STREET_FACE_B
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
F='/Game/Stacktown/Materials'
cube=unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
def M(n): return unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(F,n,n))

X0,X1 = -300.0, 4600.0
YB,YT = STREET_FACE_B-1100.0, 900.0        # behind block B .. behind block A
acts={a.get_actor_label():a for a in eas.get_all_level_actors()}

# board
for lbl,names,zc,zt in (('STAGE_ModelBoard',('BoardTop','BoardPlinth'),0,0),):
    for c in acts[lbl].get_components_by_class(unreal.StaticMeshComponent):
        if c.get_name() not in names: continue
        s=c.get_world_scale(); e=c.static_mesh.get_bounds().box_extent
        loc=c.get_world_location()
        c.set_world_scale3d(unreal.Vector((X1-X0)/2.0/e.x, (YT-YB)/2.0/e.y, s.z))
        c.set_world_location(unreal.Vector((X0+X1)/2.0,(YB+YT)/2.0,loc.z),False,False)
        print('%-12s X %.0f..%.0f  Y %.0f..%.0f'%(c.get_name(),X0,X1,YB,YT))

# street: rebuild as owned actors so it is reproducible
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('ROAD_'): eas.destroy_actor(a)
def slab(name,x0,x1,y0,y1,z0,z1,mat):
    a=eas.spawn_actor_from_class(unreal.StaticMeshActor,
        unreal.Vector((x0+x1)/2.0,(y0+y1)/2.0,(z0+z1)/2.0),unreal.Rotator(0,0,0))
    a.set_actor_label('ROAD_'+name)
    a.static_mesh_component.set_editor_property('static_mesh',cube)
    a.set_actor_scale3d(unreal.Vector((x1-x0)/100.0,(y1-y0)/100.0,max(0.02,(z1-z0)/100.0)))
    a.static_mesh_component.set_material(0,M(mat))
KERB_A, KERB_B = STREET_FACE_A-430.0, STREET_FACE_B+430.0
slab('WalkA',X0,X1,STREET_FACE_A-430.0,STREET_FACE_A+40.0,-16,0,'MI_concrete')
slab('WalkB',X0,X1,STREET_FACE_B-40.0,STREET_FACE_B+430.0,-16,0,'MI_concrete')
slab('Road', X0,X1,KERB_B,KERB_A,-30,-16,'MI_studio_grey')
slab('KerbA',X0,X1,KERB_A-14.0,KERB_A,-16,-4,'MI_paint_cream')
slab('KerbB',X0,X1,KERB_B,KERB_B+14.0,-16,-4,'MI_paint_cream')
print('street: road Y %.0f..%.0f between two pavements'%(KERB_B,KERB_A))

# hide the old single-sided street
for a in eas.get_all_level_actors():
    if a.get_actor_label()=='STAGE_Street':
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            c.set_visibility(False,True); c.set_hidden_in_game(True,True)
        print('old STAGE_Street hidden')
les.save_current_level()
