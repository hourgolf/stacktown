import unreal
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
acts={a.get_actor_label():a for a in eas.get_all_level_actors()}
cap=[c for c in acts['BLD_Roof'].get_components_by_class(unreal.StaticMeshComponent)
     if c.get_name()=='ParapetCap'][0]
# Assign the ROLE explicitly. Reading the component's current material breaks
# on a re-run: deleting and re-duplicating the mesh asset drops the component
# back to WorldGridMaterial, and that then gets faithfully re-applied.
mat=unreal.EditorAssetLibrary.load_asset(
    '/Game/Stacktown/Materials/MI_paint_cream.MI_paint_cream')
print('assigning material:', mat.get_name())
sm=unreal.EditorAssetLibrary.load_asset(
    '/Game/Stacktown/Meshes/SM_ParapetCap_Dented.SM_ParapetCap_Dented')
if not sm: raise SystemExit('dented mesh missing')
cap.set_editor_property('static_mesh', sm)
cap.set_material(0, mat)                     # swapping the mesh resets slots
print('cap mesh now %s, material %s, tris %d'
      %(cap.static_mesh.get_name(),
        cap.get_material(0).get_name() if cap.get_material(0) else 'NONE',
        sm.get_num_triangles(0)))
les.save_current_level()
print('level saved')
