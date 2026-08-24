#!/usr/bin/env python3
"""Chamfered meshes for every unique component size in the generated buildings.

genbuild builds through MCP add_cube, which emits plain Cubes with sharp edges.
Edge wear is a normal-as-curvature proxy - max(|n|) is 1.0 on a flat face and
~0.707 on a 45 degree chamfer - so with no chamfers it has nothing to act on and
the facades read flat at the player zoom. Stage 1 only reads as card up close
because its components were swapped onto chamfered meshes in a later pass.

40 mm chamfer, the card-edge value from MINIATURE_RECIPE. objgen clamps it to
45% of the smallest dimension, so the 2 uu glass planes and 6 uu mullions do not
collapse.
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ue
from objgen import write_obj

HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(HERE,'obj_s2'); os.makedirs(OUT,exist_ok=True)
MESH_DIR='/Game/Stacktown/Meshes'
SMT='editor_toolset.toolsets.static_mesh.StaticMeshTools'
AST='editor_toolset.toolsets.asset.AssetTools'
CHAMFER=4.0

def name_for(d):
    return 'SM_Cw_%s'%'_'.join(str(round(v,1)).replace('.','p') for v in d)

sizes=[tuple(s) for s in json.load(open(os.path.join(HERE,'stage2_sizes.json')))['sizes']]
print('%d unique sizes'%len(sizes))
t=time.time(); made=0; reused=0; failed=[]
for d in sizes:
    nm=name_for(d); path='%s/%s'%(MESH_DIR,nm)
    if 'true' in ue.tool(AST,'exists',{'path':path}):
        reused+=1; continue
    p=os.path.join(OUT,nm+'.obj')
    write_obj(p,d,CHAMFER,nm)
    r=ue.tool(SMT,'import_file',{'folder_path':MESH_DIR,'asset_name':nm,'source_file':p,
        'import_materials':False,'import_textures':False,'combine_meshes':True})
    if 'refPath' in r: made+=1
    else: failed.append((nm,r[:70]))
print('imported %d, reused %d existing, failed %d  (%.0fs)'%(made,reused,len(failed),time.time()-t))
for f in failed[:5]: print('  FAIL',f)
# import_file does NOT persist - saving is mandatory
names=[name_for(d) for d in sizes]
saved=0
for i in range(0,len(names),12):
    batch=['%s/%s'%(MESH_DIR,n) for n in names[i:i+12]]
    if 'true' in ue.tool(AST,'save_assets',{'asset_paths':batch}): saved+=len(batch)
print('saved %d of %d'%(saved,len(names)))
