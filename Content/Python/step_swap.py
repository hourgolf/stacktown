"""Swap generated Cube components onto their chamfered equivalents.

The chamfered mesh is authored at true size, so the component's scale must go
back to 1 - leaving the old scale on would multiply the chamfer along with
everything else.
"""
import unreal
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
MESH='/Game/Stacktown/Meshes'
cache={}
def mesh_for(d):
    nm='SM_Cw_%s'%'_'.join(str(round(v,1)).replace('.','p') for v in d)
    if nm not in cache:
        cache[nm]=unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(MESH,nm,nm))
    return nm,cache[nm]
swapped=0; missing=set()
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith('BLD2_'): continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm=c.static_mesh
        if not sm or sm.get_name()!='Cube': continue
        s=c.get_world_scale()
        d=(round(s.x*100,1),round(s.y*100,1),round(s.z*100,1))
        nm,new=mesh_for(d)
        if not new: missing.add(nm); continue
        mats=[c.get_material(i) for i in range(max(1,len(sm.get_editor_property('static_materials'))))]
        c.set_editor_property('static_mesh',new)
        c.set_world_scale3d(unreal.Vector(1.0,1.0,1.0))
        if mats and mats[0]: c.set_material(0,mats[0])
        swapped+=1
print('swapped %d components onto chamfered meshes'%swapped)
if missing: print('missing meshes:',sorted(missing)[:6])
les.save_current_level()
