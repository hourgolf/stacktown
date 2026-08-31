"""Make the Blueprint variables instance-editable.

add_member_variable creates a variable that is private to the Blueprint, so
setting it on a placed actor raises "cannot be edited on instances" - which is
what happened the first time the tick ran. Every one of these is meant to be
set per parcel, which is the entire point of a parcel.
"""
import unreal
B = unreal.BlueprintEditorLibrary
RT = '/Game/Stacktown/Runtime'
WANT = {'BP_Parcel': ('RecipeId', 'Tier', 'Level', 'WidthUU', 'DepthUU', 'Catalogue'),
        'BP_BuildingCatalogue': ('RecipeIds', 'Tiers', 'Widths', 'Meshes', 'TierNames')}
for name, vars_ in WANT.items():
    bp = unreal.load_asset('%s/%s' % (RT, name))
    for v in vars_:
        B.set_blueprint_variable_instance_editable(bp, unreal.Name(v), True)
        B.set_blueprint_variable_expose_on_spawn(bp, unreal.Name(v), True)
    B.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset('%s/%s' % (RT, name), only_if_is_dirty=False)
    print('  %-22s %d variables now instance-editable' % (name, len(vars_)))
