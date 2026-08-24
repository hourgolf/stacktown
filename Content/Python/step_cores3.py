"""Cores as per-band segments, so nothing is left hollow behind a facade.

A single core box per building was sized from the DEEPEST floor - the setback
one - which left a 70-130 uu void behind every other floor. Invisible head-on,
plainly visible at an oblique angle or a building end, where you look straight
into the slot between the facade and the mass behind it.

genbuild only ever sets back the TOP floor, so two bands suffice:
    band 1  ground + all non-setback floors   front = 62 (piers end at 60)
    band 2  top floor + parapet               front = setback + 62
With no setback it collapses to one band.
"""
import unreal, sys, math
sys.path.insert(0,'/private/tmp/claude-501/-Users-ben-Documents-New-project/c7b8ef13-3903-46ab-bd2b-18279bb95fe6/scratchpad')
from city import BLOCKS
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
F='/Game/Stacktown/Materials'
cube=unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
OVER_X, OVER_Z, CLEAR = 8.0, 14.0, 2.0
FACADE_BACK = 60.0

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('CORE_'): eas.destroy_actor(a)

n=0
for b in BLOCKS:
    ox,oy,oz=b['origin']; yaw=b['yaw']
    c_,s_=math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    for spec in b['lots']:
        if spec['kind']!='gen': continue
        GF,FH,FL,PAR=spec['gf_h'],spec['fl_h'],spec['floors'],spec['parapet']
        setback=spec.get('setback') or 0.0
        ztop=GF+FL*FH
        bands=[]
        if setback>0 and FL>1:
            zsplit=GF+(FL-1)*FH
            bands.append((0.0, zsplit, FACADE_BACK+CLEAR))
            bands.append((zsplit, ztop+PAR+OVER_Z, setback+FACADE_BACK+CLEAR))
        else:
            bands.append((0.0, ztop+PAR+OVER_Z, FACADE_BACK+CLEAR))
        for i,(z0,z1,front) in enumerate(bands):
            depth=max(80.0, spec['depth']-front)
            lx=spec['x0']+spec['width']/2.0
            ly=front+depth/2.0
            wx=ox+lx*c_-ly*s_; wy=oy+lx*s_+ly*c_
            a=eas.spawn_actor_from_class(unreal.StaticMeshActor,
                unreal.Vector(wx,wy,(z0+z1)/2.0), unreal.Rotator(0,0,yaw))
            a.set_actor_label('CORE_%s%s'%(spec['name'],'' if len(bands)==1 else '_b%d'%i))
            a.static_mesh_component.set_editor_property('static_mesh',cube)
            a.set_actor_scale3d(unreal.Vector((spec['width']+2*OVER_X)/100.0,
                                              depth/100.0,(z1-z0)/100.0))
            a.static_mesh_component.set_material(0,
                unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(F,spec['wall'],spec['wall'])))
            n+=1
print('core segments: %d'%n)
les.save_current_level()
