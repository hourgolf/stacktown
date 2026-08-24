"""Bake several skeletal assets to static meshes.

Baking is asset work on the game thread - it never puts a SkeletalMeshComponent
in front of the renderer, which is the operation that crashes. So this is safe
to batch even though spawning skeletal actors is not.
"""
import unreal, time
GSA=unreal.GeometryScript_AssetUtils
NEW=unreal.GeometryScript_NewAssetUtils
JOBS=[('/Game/AssetsvilleTown/Meshes/Vehicles','SK_veh_Pickup_01','SM_Baked_Pickup'),
      ('/Game/AssetsvilleTown/Meshes/Vehicles','SK_veh_PoliceCarSedan_01','SM_Baked_Police'),
      ('/Game/AssetsvilleTown/Meshes/Vehicles','SK_veh_CargoTruckOld','SM_Baked_Truck'),
      ('/Game/AssetsvilleTown/Meshes/Characters','SK_citizen_female_01','SM_Baked_Ped1'),
      ('/Game/AssetsvilleTown/Meshes/Characters','SK_citizen_female_05','SM_Baked_Ped2'),
      ('/Game/AssetsvilleTown/Meshes/Characters','SK_citizen_female_09','SM_Baked_Ped3')]
t0=time.time()
for folder,src,dst in JOBS:
    sk=unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(folder,src,src))
    if not sk:
        print('  missing',src); continue
    m=unreal.DynamicMesh()
    m,o=GSA.copy_mesh_from_skeletal_mesh(sk,m,
        unreal.GeometryScriptCopyMeshFromAssetOptions(),unreal.GeometryScriptMeshReadLOD())
    path='/Game/Stacktown/Meshes/%s'%dst
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    sm,o2=NEW.create_new_static_mesh_asset_from_mesh(m,path,
        unreal.GeometryScriptCreateNewStaticMeshAssetOptions())
    unreal.EditorAssetLibrary.save_asset(path)
    print('%-24s -> %-18s %5d tris  %d slots'%(src,dst,sm.get_num_triangles(0),
          len(sm.get_editor_property('static_materials'))))
print('baked %d in %.1fs'%(len(JOBS),time.time()-t0))
