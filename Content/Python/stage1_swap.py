import unreal

MESH_DIR = '/Game/Stacktown/Meshes'


def asset_name(d):
    return 'SM_Cx_%s' % '_'.join(str(x).replace('.', 'p') for x in d)


eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

swapped = already = skipped = 0
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith(('BLD_', 'STAGE_', 'PROP_')):
        continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.static_mesh
        if sm and 'SM_Cx_' in sm.get_path_name():
            already += 1
            continue
        s = c.get_world_scale()
        dims = (round(s.x * 100, 2), round(s.y * 100, 2), round(s.z * 100, 2))
        path = '%s/%s' % (MESH_DIR, asset_name(dims))
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            skipped += 1
            continue
        mesh = unreal.EditorAssetLibrary.load_asset(path + '.' + asset_name(dims))
        mats = list(c.get_editor_property('override_materials'))
        c.set_editor_property('static_mesh', mesh)
        c.set_editor_property('relative_scale3d', unreal.Vector(1.0, 1.0, 1.0))
        c.set_editor_property('override_materials', mats)
        swapped += 1

print('swapped %d, already chamfered %d, left plain %d'
      % (swapped, already, skipped))

# verify
bad_scale = lost_mat = cham = plain = 0
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith(('BLD_', 'STAGE_', 'PROP_')):
        continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.static_mesh
        if sm and 'SM_Cx_' in sm.get_path_name():
            cham += 1
            s = c.get_world_scale()
            if abs(s.x - 1) > 1e-4 or abs(s.y - 1) > 1e-4 or abs(s.z - 1) > 1e-4:
                bad_scale += 1
        else:
            plain += 1
        m = c.get_editor_property('override_materials')
        if not m or m[0] is None:
            lost_mat += 1
print('verify: chamfered %d, plain %d, wrong scale %d, lost material %d'
      % (cham, plain, bad_scale, lost_mat))
les.save_current_level()
print('saved')
