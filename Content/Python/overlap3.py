"""Exact world AABBs: transform the 8 local corners by each component's world
transform. Two previous attempts were wrong -
  v1 added LOCAL mesh bounds to world location, ignoring rotation
  v2 used get_actor_bounds, which includes the actor's root component at the
     origin and reported every building as starting at -128
so this one carries a self-check against two placements whose answer is known.
"""
import unreal
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def world_aabb(c):
    sm=c.static_mesh
    if not sm: return None
    b=sm.get_bounds(); o=b.origin; e=b.box_extent
    t=c.get_world_transform()
    lo=[1e18]*3; hi=[-1e18]*3
    for sx in (-1,1):
        for sy in (-1,1):
            for sz in (-1,1):
                p=unreal.Vector(o.x+sx*e.x, o.y+sy*e.y, o.z+sz*e.z)
                w=t.transform_location(p)
                for i,v in enumerate((w.x,w.y,w.z)):
                    lo[i]=min(lo[i],v); hi[i]=max(hi[i],v)
    return lo,hi

CHECK={'AV_flank17':(2005.0,2035.0),'AV_win2':(2020.0,2420.0)}
G={}
for a in eas.get_all_level_actors():
    l=a.get_actor_label()
    k=None
    if l.startswith('BLD2_'):   k=l.split('_')[1]
    elif l.startswith('CORE_'): k='CORE_'+l.split('_')[1]
    elif l.startswith('AV_'):   k='AV'
    elif l.startswith('BLD_'):  k='Stage1'
    if not k: continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if not c.is_visible(): continue
        r=world_aabb(c)
        if not r: continue
        lo,hi=r
        if l in CHECK:
            exp=CHECK[l]
            print('CHECK %-12s X %.1f..%.1f   expected %.1f..%.1f   %s'%(
                l,lo[0],hi[0],exp[0],exp[1],
                'OK' if abs(lo[0]-exp[0])<2 and abs(hi[0]-exp[1])<2 else 'MISMATCH'))
        g=G.setdefault(k,[list(lo),list(hi)])
        for i in range(3):
            g[0][i]=min(g[0][i],lo[i]); g[1][i]=max(g[1][i],hi[i])
print()
for k in sorted(G):
    lo,hi=G[k]
    print('%-12s X %7.0f..%7.0f  Y %7.0f..%7.0f  Z %6.0f..%6.0f'%(k,lo[0],hi[0],lo[1],hi[1],lo[2],hi[2]))
print()
ks=sorted(G); bad=0
for i in range(len(ks)):
    for j in range(i+1,len(ks)):
        if ks[j]=='CORE_'+ks[i] or ks[i]=='CORE_'+ks[j]: continue
        a,b=G[ks[i]],G[ks[j]]
        ov=[min(a[1][n],b[1][n])-max(a[0][n],b[0][n]) for n in range(3)]
        if all(v>1.0 for v in ov):
            print('OVERLAP %-11s x %-11s  X%.0f Y%.0f Z%.0f'%(ks[i],ks[j],ov[0],ov[1],ov[2])); bad+=1
print('cross-building overlaps: %d'%bad)
