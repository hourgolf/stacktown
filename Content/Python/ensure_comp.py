"""Ensure BP_Parcel has exactly ONE StaticMeshComponent named Building.

Idempotent and it VERIFIES, because the last attempt reported removing one
duplicate and then reported zero components left - a count taken after a
compile is not the same count as before it.
"""
import unreal
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
FL = unreal.SubobjectDataBlueprintFunctionLibrary
P = '/Game/Stacktown/Runtime/BP_Parcel'


def mesh_comps(bp):
    out = []
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        d = sds.k2_find_subobject_data_from_handle(h)
        try:
            o = FL.get_object(d)
        except Exception:
            continue
        if isinstance(o, unreal.StaticMeshComponent):
            out.append((h, o.get_name()))
    return out


bp = unreal.load_asset(P)
have = mesh_comps(bp)
print('before: %s' % [n for _h, n in have])
if not have:
    root = sds.k2_gather_subobject_data_for_blueprint(bp)[0]
    params = unreal.AddNewSubobjectParams(
        parent_handle=root, new_class=unreal.StaticMeshComponent, blueprint_context=bp)
    h, fail = sds.add_new_subobject(params)
    assert not str(fail), 'add failed: %s' % fail
    sds.rename_subobject(h, unreal.Text('Building'))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(P, only_if_is_dirty=False)
    bp = unreal.load_asset(P)
print('after:  %s' % [n for _h, n in mesh_comps(bp)])
# and prove it from the far side: spawn one and look for the component
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
a = eas.spawn_actor_from_class(bp.generated_class(), unreal.Vector(0, 0, -50000))
got = [c.get_name() for c in a.get_components_by_class(unreal.StaticMeshComponent)]
eas.destroy_actor(a)
print('a spawned BP_Parcel reports mesh components: %s' % got)
