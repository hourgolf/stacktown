"""Give BP_Parcel a mesh component and fill the catalogue, if Python can.

Every step done here is a step the owner does not have to do by hand in the
editor, so it is worth trying before writing the walkthrough. Both are
attempted defensively and what fails is REPORTED, not hidden - a walkthrough
that assumes a step already happened is worse than one that includes it.
"""
import unreal
import _path  # noqa: F401
import recipes

RT = '/Game/Stacktown/Runtime'
BAKED = '/Game/Stacktown/Baked'
WID = {'cottage': 820.0, 'walkup': 1420.0}

# ---- 1. a StaticMeshComponent on BP_Parcel --------------------------------
try:
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    bp = unreal.load_asset('%s/BP_Parcel' % RT)
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    root = handles[0]
    params = unreal.AddNewSubobjectParams(
        parent_handle=root, new_class=unreal.StaticMeshComponent, blueprint_context=bp)
    handle, fail = sds.add_new_subobject(params)
    if str(fail):
        print('  component NOT added: %s' % fail)
    else:
        sds.rename_subobject(handle, unreal.Text('Building'))
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_asset('%s/BP_Parcel' % RT, only_if_is_dirty=False)
        print('  BP_Parcel: StaticMeshComponent "Building" added')
except Exception as e:
    print('  component step FAILED: %s' % str(e)[:140])

# ---- 2. an instance of the catalogue, filled ------------------------------
try:
    cls = unreal.load_asset('%s/BP_BuildingCatalogue' % RT).generated_class()
    path = '%s/DA_Catalogue' % RT
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    f = unreal.DataAssetFactory()
    f.set_editor_property('data_asset_class', cls)
    da = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        'DA_Catalogue', RT, None, f)
    ids, tiers, widths, meshes, names = [], [], [], [], []
    for rid in sorted(recipes.RECIPES):
        w = WID[rid]
        for t in range(recipes.tier_count(rid)):
            p = '%s/%s' % (BAKED, recipes.asset_name(rid, t, w))
            sm = unreal.load_asset(p)
            if not sm:
                print('  missing baked mesh %s' % p); continue
            ids.append(unreal.Name(rid)); tiers.append(t); widths.append(w)
            meshes.append(sm); names.append(recipes.tier_name(rid, t))
    for prop, val in (('RecipeIds', ids), ('Tiers', tiers), ('Widths', widths),
                      ('Meshes', meshes), ('TierNames', names)):
        da.set_editor_property(prop, val)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    print('  DA_Catalogue: %d rows  (%s)' % (len(ids), ', '.join(
        '%s t%d' % (i, t) for i, t in zip(ids, tiers))))
except Exception as e:
    print('  catalogue step FAILED: %s' % str(e)[:140])
