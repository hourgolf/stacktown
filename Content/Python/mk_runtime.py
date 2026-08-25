"""Author the runtime assets: a catalogue DataAsset and a parcel Actor.

Approved 2026-08-25: Blueprint authoring and a catalogue DataAsset, narrowly -
not C++, not AllToolsets, not PCG.

WHAT PYTHON CAN AND CANNOT DO HERE, established by probe rather than by
assumption. BlueprintEditorLibrary can create a class against a parent, add
typed member variables and compile. It CANNOT author graph nodes, and
UserDefinedStructEditorLibrary is not exposed in this build - so a DataTable
with a custom row struct is out and a PrimaryDataAsset with parallel arrays is
in. Ugly next to a struct, but authorable and reproducible, which a
hand-made struct is not.

The consequence is stated plainly rather than worked around: the DATA layer is
generated here and the GRAPH is editor work. Docs/RUNTIME_SLICE.md specifies
exactly what to wire.
"""
import unreal
import _path  # noqa: F401
import recipes

B = unreal.BlueprintEditorLibrary
OUT = '/Game/Stacktown/Runtime'


def pin(spec):
    """EdGraphPinType has no settable properties in this build - it is a struct
    with import_text and export_text and nothing else. So the type is built
    from its TEXT form, which is what the engine serialises anyway. Probed
    rather than assumed; all six of these round-trip."""
    t = unreal.EdGraphPinType()
    t.import_text(spec)
    return t


NAME = '(PinCategory="name")'
INT = '(PinCategory="int")'
REAL = '(PinCategory="real",PinSubCategory="double")'
STR = '(PinCategory="string")'


def arr(spec):
    return spec[:-1] + ',ContainerType=Array)'


def obj(cls):
    return '(PinCategory="object",PinSubCategoryObject="%s")' % cls


def make(name, parent, members):
    path = '%s/%s' % (OUT, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    bp = B.create_blueprint_asset_with_parent(path, parent)
    assert bp, 'could not create %s' % path
    ok = 0
    for mname, mtype in members:
        ok += 1 if B.add_member_variable(bp, unreal.Name(mname), mtype) else 0
    B.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    print('  %-22s parent %-18s %d/%d members'
          % (name, parent.__name__, ok, len(members)))
    return bp


make('BP_BuildingCatalogue', unreal.PrimaryDataAsset, [
    ('RecipeIds', pin(arr(NAME))),
    ('Tiers',     pin(arr(INT))),
    ('Widths',    pin(arr(REAL))),
    ('Meshes',    pin(arr(obj('/Script/Engine.StaticMesh')))),
    ('TierNames', pin(arr(STR))),
])

make('BP_Parcel', unreal.Actor, [
    ('RecipeId',  pin(NAME)),
    ('Tier',      pin(INT)),
    ('Level',     pin(REAL)),
    ('WidthUU',   pin(REAL)),
    ('DepthUU',   pin(REAL)),
    ('Catalogue', pin(obj('/Script/Engine.PrimaryDataAsset'))),
])

# what the catalogue would hold, printed so the numbers are on the record
rows = 0
for rid in sorted(recipes.RECIPES):
    for t in range(recipes.tier_count(rid)):
        w = 820.0 if rid == 'cottage' else 1420.0
        p = '/Game/Stacktown/Baked/%s' % recipes.asset_name(rid, t, w)
        rows += 1 if unreal.EditorAssetLibrary.does_asset_exist(p) else 0
print('catalogue rows with a baked mesh on disk: %d' % rows)
