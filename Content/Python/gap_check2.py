"""Void check, matching each floor to the core segment that covers its Z band.

The previous version kept whichever core actor it found last, so with two
segments per building it compared every floor against the setback band and
reported voids that were not there."""
import unreal, sys
import _path  # repo tool paths; replaces a dead scratchpad path
from city import BLOCKS
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def aabb(c):
    sm=c.static_mesh
    if not sm: return None
    bb=sm.get_bounds(); o=bb.origin; e=bb.box_extent; t=c.get_world_transform()
    lo=[1e18]*3; hi=[-1e18]*3
    for sx in(-1,1):
        for sy in(-1,1):
            for sz in(-1,1):
                w=t.transform_location(unreal.Vector(o.x+sx*e.x,o.y+sy*e.y,o.z+sz*e.z))
                for i,v in enumerate((w.x,w.y,w.z)):
                    lo[i]=min(lo[i],v); hi[i]=max(hi[i],v)
    return lo,hi
worst=0.0; worstwho=''
for b in BLOCKS:
    oy=b['origin'][1]; flip=abs(b['yaw'])>90
    def ly(wy): return (oy-wy) if flip else (wy-oy)
    for spec in b['lots']:
        if spec['kind']!='gen': continue
        nm=spec['name']
        segs=[]
        for a in eas.get_all_level_actors():
            if a.get_actor_label().startswith('CORE_%s'%nm):
                r=aabb(a.static_mesh_component)
                if r: segs.append((r[0][2],r[1][2],min(ly(r[0][1]),ly(r[1][1]))))
        for a in eas.get_all_level_actors():
            l=a.get_actor_label()
            if not l.startswith('BLD2_%s_F'%nm): continue
            back=-1e18; zc=0.0; nz=0
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                r=aabb(c)
                if not r: continue
                back=max(back, ly(r[0][1]), ly(r[1][1]))
                zc+=(r[0][2]+r[1][2])/2.0; nz+=1
            zc/=max(1,nz)
            cand=[f for z0,z1,f in segs if z0-1<=zc<=z1+1]
            if not cand: continue
            gap=min(cand)-back
            if gap>worst: worst, worstwho = gap, '%s %s'%(nm,l.split('_')[-1])
print('worst void behind any facade: %.1f uu  (%s)'%(worst,worstwho))
print('verdict:', 'PASS - no hollow facades' if worst<=6.0 else 'FAIL')
