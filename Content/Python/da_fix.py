"""Repair DA_Catalogue IN PLACE, and report BP_Parcel's component state.

fill_runtime.py recreates the DataAsset by delete + create, which fails when
the asset is loaded or referenced - create_asset returns None and the blanket
report says FAILED while the OLD rows stay. This sets the arrays on the
existing asset instead, which is what the situation actually needs.

It also REPORTS BP_Parcel's subobjects rather than deleting any: fill_runtime
run twice adds a second StaticMeshComponent, and removing a Blueprint
subobject is an editor action the owner should see, not a silent script one.
"""
import unreal
import _path  # noqa: F401
import recipes

RT = '/Game/Stacktown/Runtime'
BAKED = '/Game/Stacktown/Baked'
WID = {'vernacular': 1230.0}

# ---- 1. report BP_Parcel components ---------------------------------------
bp = unreal.load_asset('%s/BP_Parcel' % RT)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sds.k2_gather_subobject_data_for_blueprint(bp)
names = []
for h in handles:
    d = sds.k2_find_subobject_data_from_handle(h)
    o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(d)
    if o:
        names.append(o.get_name())
print('BP_Parcel subobjects: %s' % ', '.join(names))
dup = [n for n in names if n.startswith('Building') and n != 'Building']
if dup:
    print('DUPLICATE mesh component(s) present: %s - delete in the editor '
          '(Components panel), the runtime slice wants exactly one.' % dup)

# ---- 2. set the catalogue arrays on the EXISTING asset --------------------
path = '%s/DA_Catalogue' % RT
da = unreal.load_asset(path)
assert da, 'DA_Catalogue missing entirely - run fill_runtime.py'
ids, tiers, widths, meshes, tnames = [], [], [], [], []
for rid in sorted(recipes.RECIPES):
    if rid not in WID:
        print('no baked width declared for %s - skipped' % rid)
        continue
    w = WID[rid]
    for t in range(recipes.tier_count(rid)):
        p = '%s/%s' % (BAKED, recipes.asset_name(rid, t, w))
        sm = unreal.load_asset(p)
        if not sm:
            print('missing baked mesh %s' % p)
            continue
        ids.append(unreal.Name(rid)); tiers.append(t); widths.append(w)
        meshes.append(sm); tnames.append(recipes.tier_name(rid, t))
for prop, val in (('RecipeIds', ids), ('Tiers', tiers), ('Widths', widths),
                  ('Meshes', meshes), ('TierNames', tnames)):
    da.set_editor_property(prop, val)
unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
back = [str(x) for x in da.get_editor_property('RecipeIds')]
print('DA_Catalogue arrays: %d rows (%s) - read back, not assumed'
      % (len(back), ', '.join('%s t%d' % (r, t) for r, t in zip(back, tiers))))
