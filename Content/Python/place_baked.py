"""Place the baked statics - safe to batch, unlike their skeletal originals."""
import unreal
F='/Game/Stacktown/Materials'; M='/Game/Stacktown/Meshes'
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
_m={}
def mat(n):
    if n not in _m: _m[n]=unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(F,n,n))
    return _m[n]
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith(('SKT_','BAKED_')): eas.destroy_actor(a)
def put(mesh,x,y,yaw,label,colour):
    sm=unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(M,mesh,mesh))
    if not sm: print('  missing',mesh); return
    a=eas.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,y,0.0),
                                 unreal.Rotator(0,0,yaw))
    a.set_actor_label('BAKED_'+label)
    c=a.static_mesh_component
    c.set_editor_property('static_mesh',sm)
    for i in range(len(sm.get_editor_property('static_materials'))):
        c.set_material(i, mat(colour))
n=0
for i,(mesh,col) in enumerate((('SM_Baked_Sedan','MI_card_rose'),
                               ('SM_Baked_Pickup','MI_card_sage'),
                               ('SM_Baked_Police','MI_paint_cream'),
                               ('SM_Baked_Truck','MI_card_ochre'))):
    put(mesh, 600+i*1150, -690.0, -88+i*5, 'veh%d'%i, col); n+=1
for i,mesh in enumerate(('SM_Baked_Ped1','SM_Baked_Ped2','SM_Baked_Ped3')):
    put(mesh, 1250+i*1000, -285.0, 150+i*40, 'ped%d'%i, 'MI_frame_print'); n+=1
print('placed %d baked statics'%n)
les.save_current_level()
