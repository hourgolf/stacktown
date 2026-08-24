"""Block geometry check.

Two corrections over the previous version:

  SELF-CHECK FROM THE LOT TABLE. The constants were hardcoded for the old
  Assetsville position and went stale the moment the lot moved, reporting
  MISMATCH against a block that was fine. A check that has to be hand-edited
  when the data changes is a second source of truth.

  ADJACENCY ALLOWANCE. Party-walled buildings SHARE a wall - demanding zero
  overlap between neighbours is architecturally wrong, and the earlier
  zero-gap criterion is what left a 17 uu slot showing black at frame centre.
  Neighbours may overlap up to PARTY; non-neighbours may not overlap at all.
"""
import unreal, sys
sys.path.insert(0,'/private/tmp/claude-501/-Users-ben-Documents-New-project/c7b8ef13-3903-46ab-bd2b-18279bb95fe6/scratchpad')
from lots import LOTS, STAGE1_END

PARTY = 40.0
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def world_aabb(c):
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

# --- self-check: an AV flank sits at the lot edge, +/- its 15 uu thickness ---
av=[l for l in LOTS if l['kind']=='av'][0]
expect_lo, expect_hi = av['x0']-15.0, av['x0']+15.0
got=None
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith('AV_flank'):
        r=world_aabb(a.static_mesh_component)
        if r and abs(r[0][0]-expect_lo)<2:
            got=r; break
print('SELF-CHECK  AV flank X %.1f..%.1f  expected %.1f..%.1f  %s'%(
    got[0][0],got[1][0],expect_lo,expect_hi,
    'OK' if got and abs(got[0][0]-expect_lo)<2 else 'MISMATCH') if got
    else 'SELF-CHECK  no AV flank found at the lot edge  MISMATCH')

# --- group AABBs -------------------------------------------------------------
G={}
for a in eas.get_all_level_actors():
    l=a.get_actor_label(); k=None
    if l.startswith('BLD2_'):   k=l.split('_')[1]
    elif l.startswith('AV_'):   k='AV'
    elif l.startswith('BLD_'):  k='Stage1'
    if not k: continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if not c.is_visible(): continue
        r=world_aabb(c)
        if not r: continue
        g=G.setdefault(k,[list(r[0]),list(r[1])])
        for i in range(3):
            g[0][i]=min(g[0][i],r[0][i]); g[1][i]=max(g[1][i],r[1][i])

order=['Stage1']+[l['name'] for l in LOTS]
present=[k for k in order if k in G]
print()
for k in present:
    lo,hi=G[k]
    print('%-8s X %7.0f..%7.0f  Y %7.0f..%7.0f  Z %6.0f..%6.0f'%(k,lo[0],hi[0],lo[1],hi[1],lo[2],hi[2]))
print()
fail=0
for i in range(len(present)):
    for j in range(i+1,len(present)):
        a,b=G[present[i]],G[present[j]]
        ov=[min(a[1][n],b[1][n])-max(a[0][n],b[0][n]) for n in range(3)]
        if not all(v>1.0 for v in ov): continue
        adjacent = (j==i+1)
        if adjacent and ov[0]<=PARTY:
            print('party wall  %-8s / %-8s  shares %.0f uu  OK'%(present[i],present[j],ov[0]))
        else:
            print('FAIL        %-8s / %-8s  overlap X%.0f Y%.0f Z%.0f  %s'%(
                present[i],present[j],ov[0],ov[1],ov[2],
                'too deep' if adjacent else 'NON-ADJACENT'))
            fail+=1
print()
print('geometry check: %s (%d failures)'%('PASS' if fail==0 else 'FAIL',fail))
