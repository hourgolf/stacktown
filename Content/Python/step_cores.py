"""Solid core behind each GENERATED building, sized from its own facade."""
import unreal, sys
sys.path.insert(0,'/private/tmp/claude-501/-Users-ben-Documents-New-project/c7b8ef13-3903-46ab-bd2b-18279bb95fe6/scratchpad')
from lots import LOTS
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
F='/Game/Stacktown/Materials'
cube=unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
def extent(prefix):
    ymax=-1e9; zmax=-1e9
    for a in eas.get_all_level_actors():
        if not a.get_actor_label().startswith(prefix): continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            nm=c.get_name()
            if nm.startswith('Roof_') or nm.startswith('Wall_Parapet'): continue
            w=c.get_world_location(); e=c.static_mesh.get_bounds().box_extent
            s=c.get_world_scale()
            ymax=max(ymax,w.y+e.y*s.y); zmax=max(zmax,w.z+e.z*s.z)
    return ymax,zmax
for spec in LOTS:
    if spec['kind']!='gen': continue
    who=spec['name']
    ymax,zmax=extent('BLD2_%s'%who)
    if ymax<-1e8: print('  no geometry for',who); continue
    front=ymax+6.0; depth=max(120.0, spec['depth']-front)
    a=eas.spawn_actor_from_class(unreal.StaticMeshActor,
        unreal.Vector(spec['x0']+spec['width']/2.0, front+depth/2.0, zmax/2.0),
        unreal.Rotator(0,0,0))
    a.set_actor_label('CORE_%s'%who)
    a.static_mesh_component.set_editor_property('static_mesh',cube)
    a.set_actor_scale3d(unreal.Vector(spec['width']/100.0, depth/100.0, zmax/100.0))
    a.static_mesh_component.set_material(0,
        unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(F,spec['wall'],spec['wall'])))
    print('CORE_%-7s Y %.0f..%.0f  Z 0..%.0f'%(who,front,front+depth,zmax))
les.save_current_level()
