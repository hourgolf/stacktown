"""Does any core protrude past its own facade, toward the street?"""
import unreal, sys, math
sys.path.insert(0,'/private/tmp/claude-501/-Users-ben-Documents-New-project/c7b8ef13-3903-46ab-bd2b-18279bb95fe6/scratchpad')
from city import BLOCKS
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def aabb(c):
    sm=c.static_mesh
    if not sm: return None
    b=sm.get_bounds(); o=b.origin; e=b.box_extent; t=c.get_world_transform()
    lo=[1e18]*3; hi=[-1e18]*3
    for sx in(-1,1):
        for sy in(-1,1):
            for sz in(-1,1):
                w=t.transform_location(unreal.Vector(o.x+sx*e.x,o.y+sy*e.y,o.z+sz*e.z))
                for i,v in enumerate((w.x,w.y,w.z)):
                    lo[i]=min(lo[i],v); hi[i]=max(hi[i],v)
    return lo,hi
def group(pred):
    lo=[1e18]*3; hi=[-1e18]*3; found=False
    for a in eas.get_all_level_actors():
        if not pred(a.get_actor_label()): continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            r=aabb(c)
            if not r: continue
            found=True
            for i in range(3):
                lo[i]=min(lo[i],r[0][i]); hi[i]=max(hi[i],r[1][i])
    return (lo,hi) if found else None
print('%-8s %-6s %10s %10s %10s %10s  %s'%('lot','block','facadeY','coreY','facadeX','coreX','verdict'))
bad=0
for b in BLOCKS:
    faces_neg = abs(b['yaw'])<90          # yaw 0 -> facade faces -Y
    for spec in b['lots']:
        if spec['kind']!='gen': continue
        nm=spec['name']
        f=group(lambda l,n=nm: l.startswith('BLD2_%s_'%n))
        c=group(lambda l,n=nm: l=='CORE_%s'%n)
        if not f or not c: continue
        if faces_neg:
            fedge, cedge = f[0][1], c[0][1]        # min Y is the street side
            protrude = fedge - cedge               # >0 means core is in front
        else:
            fedge, cedge = f[1][1], c[1][1]        # max Y is the street side
            protrude = cedge - fedge
        dx = max(c[0][0]-f[0][0], f[1][0]-c[1][0]) # core narrower/offset in X
        v='ok'
        if protrude > 1.0: v='CORE PROTRUDES %.0f uu'%protrude; bad+=1
        elif abs(c[0][0]-f[0][0])>60 or abs(c[1][0]-f[1][0])>60:
            v='X offset %.0f/%.0f'%(c[0][0]-f[0][0], c[1][0]-f[1][0]); bad+=1
        print('%-8s %-6s %10.0f %10.0f %6.0f..%-6.0f %6.0f..%-6.0f  %s'%(
            nm,b['name'],fedge,cedge,f[0][0],f[1][0],c[0][0],c[1][0],v))
print('\nproblem cores: %d'%bad)
