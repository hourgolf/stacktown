"""Merge one generated actor into a single StaticMesh asset, materials kept.

This is the step that makes the recipe approach affordable. A house is 170-300
boxes; twenty-three buildings is fine and five hundred is not. The recipe stays
the source of truth and the mesh is its cache.

In-engine via GeometryScript rather than the OBJ round trip the vehicles use:
no exporter, no importer, no axis flip to discover, and the material SLOTS
survive - which they must, because step_roles' whole design is role-in-the-name
and a merged mesh has to keep one slot per role.

Reads its job from a temp file; rung.sh hands the script to the editor over
remote execution and the editor does not inherit the caller's environment.
"""
import unreal, os, json, tempfile

JOB = os.path.join(tempfile.gettempdir(), 'stacktown_bake_job.json')
GSA = unreal.GeometryScript_AssetUtils
GSE = unreal.GeometryScript_MeshEdits
GSN = unreal.GeometryScript_NewAssetUtils

job = json.load(open(JOB))
labels, out_path = job['labels'], job['out']
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

acc = unreal.DynamicMesh()
mats = []
parts = 0
for a in eas.get_all_level_actors():
    if a.get_actor_label() not in labels:
        continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.static_mesh
        if not sm or not c.is_visible():
            continue
        piece = unreal.DynamicMesh()
        piece, _ = GSA.copy_mesh_from_static_mesh(
            sm, piece, unreal.GeometryScriptCopyMeshFromAssetOptions(),
            unreal.GeometryScriptMeshReadLOD())
        m = c.get_material(0)
        acc, mats = GSE.append_mesh_transformed_with_materials(
            acc, mats, piece, [m] if m else [],
            [c.get_relative_transform()], unreal.Transform())
        parts += 1

assert parts, 'no visible components found on %s' % labels
tri = unreal.GeometryScript_MeshQueries.get_num_triangle_i_ds(acc)
opts = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
opts.set_editor_property('enable_recompute_normals', False)
opts.set_editor_property('enable_recompute_tangents', True)
sm_new, outcome = GSN.create_new_static_mesh_asset_from_mesh(acc, out_path, opts)
assert sm_new, 'asset not created at %s' % out_path
sm_new.set_editor_property('static_materials',
                           [unreal.StaticMaterial(material_interface=m,
                                                  material_slot_name=unreal.Name(
                                                      m.get_name() if m else 'None'))
                            for m in mats])
unreal.EditorAssetLibrary.save_asset(out_path, only_if_is_dirty=False)
print('BAKED %s  parts %d  tris %d  material slots %d'
      % (out_path.split('/')[-1], parts, tri, len(mats)))
