import unreal, json
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sizes={}
n=0
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith('BLD2_'): continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm=c.static_mesh
        if not sm or sm.get_name()!='Cube': continue
        s=c.get_world_scale()
        d=(round(s.x*100,1), round(s.y*100,1), round(s.z*100,1))
        sizes[d]=sizes.get(d,0)+1
        n+=1
print('cube components: %d   unique sizes: %d'%(n,len(sizes)))
print('smallest dim overall: %.1f'%min(min(k) for k in sizes))
open('/private/tmp/claude-501/-Users-ben-Documents-New-project/c7b8ef13-3903-46ab-bd2b-18279bb95fe6/scratchpad/stage2_sizes.json','w').write(
    json.dumps({'sizes':[list(k) for k in sizes]}))
print('written stage2_sizes.json')
