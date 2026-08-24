"""Meshes for the fabrication-marks pass: glue beads, fibre flaps, a crush block.

Scale comes from the recipe's 1:300 — a 300 mm facade standing in for ~1 mm of
card. So a physical 0.4 mm glue squeeze-out is ~120 mm here, and the 12 uu bead
section below is 120 mm. That reads ~8 px at the 95 m hero (present, not
legible) and ~115 px at the 9 m close-up (obvious), which is the behaviour we
want: evidence of making that only appears when the player walks up.

Chamfer 5.0 on a 12 uu section is close to the generator's 45% clamp, giving an
almost round bead profile. The flap clamps to 1.8 on its 4 uu thickness.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ue
from objgen import write_obj

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'obj_marks')
MESH_DIR = '/Game/Stacktown/Meshes'
SMT = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'
AST = 'editor_toolset.toolsets.asset.AssetTools'

SPECS = [
    ('SM_Glue_L', (200.0, 12.0, 12.0), 5.0),
    ('SM_Glue_S', (90.0, 12.0, 12.0), 5.0),
    ('SM_Glue_V', (12.0, 12.0, 120.0), 5.0),   # vertical run
    ('SM_Flap',   (46.0, 4.0, 34.0), 4.0),
    ('SM_Flap_S', (28.0, 4.0, 22.0), 4.0),
    ('SM_Ding',   (44.0, 44.0, 14.0), 4.0),
]

os.makedirs(OUT, exist_ok=True)
made = []
for nm, dims, ch in SPECS:
    p = os.path.join(OUT, nm + '.obj')
    write_obj(p, dims, ch, nm)
    made.append((nm, p))
print('generated %d OBJ' % len(made))

ok = 0
for nm, p in made:
    if 'true' in ue.tool(AST, 'exists', {'path': '%s/%s' % (MESH_DIR, nm)}):
        ok += 1
        continue
    r = ue.tool(SMT, 'import_file', {
        'folder_path': MESH_DIR, 'asset_name': nm, 'source_file': p,
        'import_materials': False, 'import_textures': False, 'combine_meshes': True})
    if 'refPath' in r:
        ok += 1
    else:
        print('  FAIL', nm, r[:110])
print('imported/present %d of %d' % (ok, len(made)))

# import_file does NOT persist - saving is mandatory (66 meshes were lost to this)
paths = ['%s/%s' % (MESH_DIR, n) for n, _ in made]
print('saved:', 'true' in ue.tool(AST, 'save_assets', {'asset_paths': paths}))
