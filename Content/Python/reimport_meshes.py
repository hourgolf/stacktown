#!/usr/bin/env python3
"""Re-import every chamfered mesh AND SAVE IT.

Bug being fixed: StaticMeshTools.import_file creates the asset in memory but
does not persist it. All 66 meshes were lost on editor restart and every
component referencing one rendered nothing. Import now always pairs with an
explicit save.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ue

MESH_DIR = '/Game/Stacktown/Meshes'
SMT = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'
AST = 'editor_toolset.toolsets.asset.AssetTools'
SRC = ['/Users/ben/Documents/Unreal Projects/StacktownAlpha/Saved/Stage1/obj',
       '/Users/ben/Documents/Unreal Projects/StacktownAlpha/Saved/Stage0/obj']

ue.tool(AST, 'create_folder', {'path': MESH_DIR})
names = []
for d in SRC:
    if not os.path.isdir(d):
        print('missing source dir', d)
        continue
    for f in sorted(os.listdir(d)):
        if not f.endswith('.obj'):
            continue
        nm = f[:-4]
        if nm in names:
            continue
        r = ue.tool(SMT, 'import_file', {
            'folder_path': MESH_DIR, 'asset_name': nm,
            'source_file': os.path.join(d, f),
            'import_materials': False, 'import_textures': False,
            'combine_meshes': True})
        if 'refPath' in r or 'already exists' in r:
            names.append(nm)
        else:
            print('  FAIL', nm, r[:90])

print('imported/present: %d' % len(names))

# save in batches so a single oversized payload cannot fail the lot
saved = 0
for i in range(0, len(names), 12):
    batch = ['%s/%s' % (MESH_DIR, n) for n in names[i:i + 12]]
    r = ue.tool(AST, 'save_assets', {'asset_paths': batch})
    if 'true' in r:
        saved += len(batch)
    else:
        print('  save batch failed:', r[:110])
print('saved: %d' % saved)
