"""Give the catalogue a MAP from key to mesh.

The parallel arrays are fine for data but they make ResolveMesh a twelve-node
graph with a loop, an index and two comparisons - which is a lot of chances to
mis-wire for someone who has not built a Blueprint before. A map turns the same
lookup into ONE node: key in, mesh out.

Key is 'recipe_tier', e.g. 'cottage_2'. The arrays stay: they are the readable
form and the map is the index.
"""
import unreal
import _path  # noqa: F401
import recipes

B = unreal.BlueprintEditorLibrary
RT = '/Game/Stacktown/Runtime'
BAKED = '/Game/Stacktown/Baked'
WID = {'cottage': 820.0, 'walkup': 1420.0}

MAP = ('(PinCategory="string",ContainerType=Map,'
       'PinValueType=(TerminalCategory="object",'
       'TerminalSubCategoryObject="/Script/Engine.StaticMesh"))')
t = unreal.EdGraphPinType()
t.import_text(MAP)

bp = unreal.load_asset('%s/BP_BuildingCatalogue' % RT)
ok = B.add_member_variable(bp, unreal.Name('MeshByKey'), t)
B.set_blueprint_variable_instance_editable(bp, unreal.Name('MeshByKey'), True)
B.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_asset('%s/BP_BuildingCatalogue' % RT, only_if_is_dirty=False)
print('MeshByKey map added: %s' % ok)

da = unreal.load_asset('%s/DA_Catalogue' % RT)
m = {}
for rid in sorted(recipes.RECIPES):
    for tier in range(recipes.tier_count(rid)):
        sm = unreal.load_asset('%s/%s' % (BAKED, recipes.asset_name(rid, tier, WID[rid])))
        if sm:
            m['%s_%d' % (rid, tier)] = sm
da.set_editor_property('MeshByKey', m)
unreal.EditorAssetLibrary.save_asset('%s/DA_Catalogue' % RT, only_if_is_dirty=False)
back = da.get_editor_property('MeshByKey')
print('DA_Catalogue MeshByKey: %d entries  %s'
      % (len(back), ', '.join(sorted(str(k) for k in back))))
