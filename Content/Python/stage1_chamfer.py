#!/usr/bin/env python3
"""Generate + import chamfered replacements for every Stage 1 box size.

Same approach as Stage 0 Phase 4: Geometry Script's bevel library is not exposed
to Python in UE 5.8, so the chamfered geometry is authored as OBJ on disk and
imported through StaticMeshTools.import_file.
"""
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ue
from objgen import write_obj, asset_name

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'obj1')
MESH_DIR = '/Game/Stacktown/Meshes'
CHAMFER = 0.25            # 2.5 mm world - fabrication-plausible card edge
SMT = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'

sizes = json.load(open(os.path.join(HERE, 'stage1_sizes.json')))['work']
os.makedirs(OUT, exist_ok=True)

made = []
for d in sizes:
    d = tuple(d)
    nm = asset_name(d)
    p = os.path.join(OUT, nm + '.obj')
    write_obj(p, d, CHAMFER, nm)
    made.append((nm, p, d))
print('generated %d OBJ files' % len(made))

ok = skipped = failed = 0
for nm, p, d in made:
    exists = 'true' in ue.tool('editor_toolset.toolsets.asset.AssetTools',
                               'exists', {'path': '%s/%s' % (MESH_DIR, nm)})
    if exists:
        skipped += 1
        continue
    r = ue.tool(SMT, 'import_file', {
        'folder_path': MESH_DIR, 'asset_name': nm, 'source_file': p,
        'import_materials': False, 'import_textures': False,
        'combine_meshes': True})
    if 'refPath' in r:
        ok += 1
    else:
        failed += 1
        print('  FAIL %s %s' % (nm, r[:100]))
print('imported %d, already present %d, failed %d' % (ok, skipped, failed))

# CRITICAL: import_file creates the asset in memory but does NOT persist it.
# Skipping this save cost every chamfered mesh on the next editor restart -
# 194 components silently rendered nothing because their mesh reference had
# been nulled on load. Never import without saving.
names = [nm for nm, _, _ in made]
saved = 0
for i in range(0, len(names), 12):
    batch = ['%s/%s' % (MESH_DIR, n) for n in names[i:i + 12]]
    r = ue.tool('editor_toolset.toolsets.asset.AssetTools',
                'save_assets', {'asset_paths': batch})
    if 'true' in r:
        saved += len(batch)
    else:
        print('  save batch FAILED:', r[:110])
print('saved to disk: %d of %d' % (saved, len(names)))
