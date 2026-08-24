"""Thin sheet flaps, replacing the 4 uu chamfered blocks.

The first attempt used a 46x4x34 chamfered box on a flat face and it rendered
as a rounded tab stuck to the wall - a sticker, not a lifted edge. Two things
were wrong. It was 40 mm thick, which at 1:300 is a 0.13 mm sheet standing 40 mm
proud; and it sat in the middle of a face, where a lifted edge cannot occur.

1.6 uu is a 16 mm sheet - still thick for card but it reads as a sheet rather
than a slab, and the chamfer clamp (45% of 1.6) keeps the edge crisp.
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

SPECS = [('SM_Flap_V', (44.0, 1.6, 30.0), 0.7),    # thin in Y: vertical faces
         ('SM_Flap_H', (44.0, 30.0, 1.6), 0.7)]    # thin in Z: horizontal faces

made = []
for nm, dims, ch in SPECS:
    p = os.path.join(OUT, nm + '.obj')
    write_obj(p, dims, ch, nm)
    made.append((nm, p))

ok = 0
for nm, p in made:
    if 'true' in ue.tool(AST, 'exists', {'path': '%s/%s' % (MESH_DIR, nm)}):
        ok += 1
        continue
    r = ue.tool(SMT, 'import_file', {
        'folder_path': MESH_DIR, 'asset_name': nm, 'source_file': p,
        'import_materials': False, 'import_textures': False, 'combine_meshes': True})
    ok += 1 if 'refPath' in r else print('  FAIL', nm, r[:100]) or 0
print('imported %d of %d' % (ok, len(made)))
print('saved:', 'true' in ue.tool(AST, 'save_assets',
      {'asset_paths': ['%s/%s' % (MESH_DIR, n) for n, _ in made]}))
