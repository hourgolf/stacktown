#!/usr/bin/env python3
"""Regenerate chamfers at card scale so edge wear has somewhere to live.

2.5 mm was chosen as "fabrication-plausible" in absolute terms and is sub-pixel
at every range a player uses - it never paid for itself. Proportionally it is
also wrong: the 300 mm facade standing in for ~1 mm card puts this build near
1:300, where a crushed cut edge is tens of millimetres.

40 mm reads ~11 px at the 9 m close-up and stays invisible at the 95 m hero
(0.27 px), which is the correct behaviour - card edges should show when you
walk up and not before.

Thin parts are protected by the generator's existing clamp (chamfer never
exceeds 45% of the smallest dimension), so mullions do not collapse.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ue
from objgen import write_obj

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'obj_w')
MESH_DIR = '/Game/Stacktown/Meshes'
CHAMFER = 4.0                      # 40 mm
SMT = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'
AST = 'editor_toolset.toolsets.asset.AssetTools'


def name_w(d):
    return 'SM_Cw_%s' % '_'.join(str(x).replace('.', 'p') for x in d)


sizes = json.load(open(os.path.join(HERE, 'stage1_sizes_current.json')))['work']
os.makedirs(OUT, exist_ok=True)

made = []
for d in sizes:
    d = tuple(d)
    nm = name_w(d)
    p = os.path.join(OUT, nm + '.obj')
    write_obj(p, d, CHAMFER, nm)
    made.append((nm, p))
print('generated %d OBJ at %.0f mm chamfer' % (len(made), CHAMFER * 10))

ok = 0
for nm, p in made:
    if 'true' in ue.tool(AST, 'exists', {'path': '%s/%s' % (MESH_DIR, nm)}):
        ok += 1
        continue
    r = ue.tool(SMT, 'import_file', {
        'folder_path': MESH_DIR, 'asset_name': nm, 'source_file': p,
        'import_materials': False, 'import_textures': False,
        'combine_meshes': True})
    if 'refPath' in r:
        ok += 1
    else:
        print('  FAIL', nm, r[:90])
print('imported/present %d' % ok)

# import_file does NOT persist - saving is mandatory
saved = 0
names = [n for n, _ in made]
for i in range(0, len(names), 12):
    batch = ['%s/%s' % (MESH_DIR, n) for n in names[i:i + 12]]
    if 'true' in ue.tool(AST, 'save_assets', {'asset_paths': batch}):
        saved += len(batch)
print('saved to disk %d of %d' % (saved, len(names)))
