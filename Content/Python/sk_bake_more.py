"""Bake five more vehicles from the pack.

Separate from sk_bake_batch.py on purpose: that script deletes and recreates
every asset it lists, which would wipe the curvature vertex colours already
baked into the four existing vehicles. This only touches new names.

Baking is asset work on the game thread and is safe to batch - it never puts a
SkeletalMeshComponent in front of the renderer, which is the operation that
crashes the editor.
"""
import unreal, time
GSA = unreal.GeometryScript_AssetUtils
NEW = unreal.GeometryScript_NewAssetUtils
V = '/Game/AssetsvilleTown/Meshes/Vehicles'
JOBS = [(V, 'SK_veh_Van_01',          'SM_Baked_Van'),
        (V, 'SK_veh_Muscle_01',       'SM_Baked_Muscle'),
        (V, 'SK_veh_SportClassic_01', 'SM_Baked_Sport'),
        (V, 'SK_veh_Offroad_01',      'SM_Baked_Offroad'),
        (V, 'SK_veh_VegetableTruck',  'SM_Baked_Veg')]
t0 = time.time()
for folder, src, dst in JOBS:
    sk = unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (folder, src, src))
    if not sk:
        print('  missing', src); continue
    m = unreal.DynamicMesh()
    m, o = GSA.copy_mesh_from_skeletal_mesh(
        sk, m, unreal.GeometryScriptCopyMeshFromAssetOptions(),
        unreal.GeometryScriptMeshReadLOD())
    path = '/Game/Stacktown/Meshes/%s' % dst
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    sm, o2 = NEW.create_new_static_mesh_asset_from_mesh(
        m, path, unreal.GeometryScriptCreateNewStaticMeshAssetOptions())
    unreal.EditorAssetLibrary.save_asset(path)
    print('%-26s -> %-18s %5d tris  %d slots'
          % (src, dst, sm.get_num_triangles(0),
             len(sm.get_editor_property('static_materials'))))
print('baked %d in %.1fs' % (len(JOBS), time.time() - t0))
