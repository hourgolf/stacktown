import unreal
MESH_DIR='/Game/Stacktown/Meshes'
def name_w(d): return 'SM_Cw_%s'%'_'.join(str(x).replace('.','p') for x in d)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
swapped=skipped=0
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith(('BLD_','STAGE_','PROP_')): continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm=c.static_mesh
        if sm and 'SM_Cw_' in sm.get_path_name():
            continue
        if sm and 'SM_Cx_' in sm.get_path_name():
            b=sm.get_bounds().box_extent
            dims=(round(b.x*2,2),round(b.y*2,2),round(b.z*2,2))
        else:
            s=c.get_world_scale()
            dims=(round(s.x*100,2),round(s.y*100,2),round(s.z*100,2))
        p='%s/%s'%(MESH_DIR,name_w(dims))
        if not unreal.EditorAssetLibrary.does_asset_exist(p):
            skipped+=1; continue
        mesh=unreal.EditorAssetLibrary.load_asset(p+'.'+name_w(dims))
        mats=list(c.get_editor_property('override_materials'))
        c.set_editor_property('static_mesh',mesh)
        c.set_editor_property('relative_scale3d',unreal.Vector(1,1,1))
        c.set_editor_property('override_materials',mats)
        swapped+=1
print('swapped %d to 40mm chamfer, left %d'%(swapped,skipped))
cw=lost=0
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith(('BLD_','STAGE_','PROP_')): continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm=c.static_mesh
        if sm and 'SM_Cw_' in sm.get_path_name(): cw+=1
        m=c.get_editor_property('override_materials')
        if not m or m[0] is None: lost+=1
print('verify: 40mm meshes %d, lost materials %d'%(cw,lost))
les.save_current_level()
print('saved')
