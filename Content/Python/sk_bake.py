"""Bake a skeletal mesh to a STATIC mesh via GeometryScripting.

This is the answer to the scaling question, not a workaround for the crash.
A city does not spawn thousands of SkeletalMeshComponents - skeletal is for
animated foreground actors. Background people and parked cars should be static
meshes so they can be instanced, and baking them also removes the render-state
race that has now crashed the editor twice.
"""
import unreal

SRC = '/Game/AssetsvilleTown/Meshes/Vehicles/SK_veh_Sedan_01.SK_veh_Sedan_01'
DST = '/Game/Stacktown/Meshes/SM_Baked_Sedan'
GSA = unreal.GeometryScript_AssetUtils

sk = unreal.EditorAssetLibrary.load_asset(SRC)
print('source skeletal:', sk.get_name())
mats = GSA.get_material_list_from_skeletal_mesh(sk)
print('material list ->', type(mats).__name__)

mesh = unreal.DynamicMesh()
opts = unreal.GeometryScriptCopyMeshFromAssetOptions()
lod = unreal.GeometryScriptMeshReadLOD()
mesh, outcome = GSA.copy_mesh_from_skeletal_mesh(sk, mesh, opts, lod)
print('copy from skeletal:', outcome, 'tris', mesh.get_triangle_count())

new_sm, outcome2 = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
    mesh, DST, unreal.GeometryScriptCreateNewStaticMeshAssetOptions())
print('create static asset:', outcome2)
unreal.EditorAssetLibrary.save_asset(DST)
print('baked: %s  tris %d  slots %d'
      % (new_sm.get_name(), new_sm.get_num_triangles(0),
         len(new_sm.get_editor_property('static_materials'))))
