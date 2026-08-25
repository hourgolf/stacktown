import unreal, json
# Data goes to Saved/data, never Content/ - UE's importer picks up a .json
# there and opens a modal DataTable dialog that blocks the game thread.
_SAVED = __import__('unreal').Paths.convert_relative_path_to_full(
    __import__('unreal').Paths.project_saved_dir()) + 'data/'
__import__('os').makedirs(_SAVED, exist_ok=True)

eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows=[]
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith(('BLD_','STAGE_','PROP_')): continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm=c.static_mesh
        s=c.get_world_scale()
        if sm and 'SM_Cx_' in sm.get_path_name():
            # chamfered mesh authored at true size, scale is 1
            b=sm.get_bounds().box_extent
            rows.append((round(b.x*2,2),round(b.y*2,2),round(b.z*2,2)))
        else:
            rows.append((round(s.x*100,2),round(s.y*100,2),round(s.z*100,2)))
uniq=sorted(set(rows))
work=[d for d in uniq if min(d)>=3.0 and max(d)<=2500.0]
print('components %d  distinct %d  to chamfer %d'%(len(rows),len(uniq),len(work)))
open(_SAVED + 'stage1_sizes_current.json','w').write(json.dumps({'work':work}))
print('wrote sizes')
