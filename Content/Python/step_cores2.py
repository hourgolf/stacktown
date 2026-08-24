"""Cores in BLOCK-LOCAL space, spawned with the block transform.

The previous version measured world extents, which only works for an
unrotated block. Deriving the core from the lot spec and letting the actor
carry the block yaw works for any block."""
import unreal, sys
sys.path.insert(0,'/private/tmp/claude-501/-Users-ben-Documents-New-project/c7b8ef13-3903-46ab-bd2b-18279bb95fe6/scratchpad')
from city import BLOCKS
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
F='/Game/Stacktown/Materials'
cube=unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
n=0
for b in BLOCKS:
    ox,oy,oz=b['origin']; yaw=b['yaw']
    for spec in b['lots']:
        if spec['kind']!='gen': continue
        # the band course runs x0-8 .. x0+W+8 and the parapet cap sits 14 uu
        # above ztop, so a core cut to exactly (width, height) leaves the facade
        # overhanging it. At a block END that reads as a thin fin standing away
        # from a blank slab - which is what it looked like.
        OVER_X, OVER_Z = 8.0, 14.0
        h=spec['gf_h']+spec['floors']*spec['fl_h']+spec['parapet']+OVER_Z
        front=max(130.0,(spec.get('setback') or 0.0)+70.0)
        depth=max(120.0,spec['depth']-front)
        lx=spec['x0']+spec['width']/2.0
        ly=front+depth/2.0
        import math
        c=math.cos(math.radians(yaw)); s=math.sin(math.radians(yaw))
        wx=ox+lx*c-ly*s; wy=oy+lx*s+ly*c
        a=eas.spawn_actor_from_class(unreal.StaticMeshActor,
            unreal.Vector(wx,wy,h/2.0), unreal.Rotator(0,0,yaw))
        a.set_actor_label('CORE_%s'%spec['name'])
        a.static_mesh_component.set_editor_property('static_mesh',cube)
        a.set_actor_scale3d(unreal.Vector((spec['width']+2*OVER_X)/100.0,
                                          depth/100.0, h/100.0))
        a.static_mesh_component.set_material(0,
            unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(F,spec['wall'],spec['wall'])))
        n+=1
print('cores: %d'%n)
les.save_current_level()
