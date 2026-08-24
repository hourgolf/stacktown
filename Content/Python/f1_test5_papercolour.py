"""F1 test 5 — paper / cardboard albedo.

Test 4 fixed the surface RESPONSE (matte, low specular). This fixes the
COLOUR. Pure neutral white reads as painted plaster; paper is warm off-white
and cardboard is kraft buff. Card stock also never reaches the brightness we
were using - real white card sits around 0.72-0.80, not 0.85+.

This is a palette change (per-role base values), not the large-scale albedo
VARIATION that MASTER_MATERIAL_SPEC forbids. Each surface stays uniform.

Board moved to kraft/chipboard, which is the strongest single "this is a model
sitting on a piece of card" cue available at this distance.
"""
import unreal

F = '/Game/Stacktown/Materials'
L = unreal.MaterialEditingLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

PAPER = {
    # warm off-white card, not neutral plaster white
    'MI_concrete':      (0.700, 0.672, 0.616),
    'MI_paint_cream':   (0.780, 0.748, 0.678),
    # kraft / chipboard base the model sits on
    'MI_model_board':   (0.430, 0.336, 0.212),
    # room beyond stays neutral so it reads as a place, not more card
    'MI_studio_grey':   (0.300, 0.292, 0.280),
    # printed ink, slightly warm rather than pure grey
    'MI_frame_print':   (0.250, 0.238, 0.222),
    'MI_interior':      (0.030, 0.030, 0.033),
    # printed greens / accents on card read duller than paint
    'MI_paint_accent':  (0.300, 0.372, 0.244),
    'MI_canopy_accent': (0.372, 0.132, 0.104),
    'MI_wood':          (0.360, 0.268, 0.176),
}
for name, c in PAPER.items():
    p = '%s/%s' % (F, name)
    if not unreal.EditorAssetLibrary.does_asset_exist(p):
        print('  missing', name)
        continue
    mi = unreal.EditorAssetLibrary.load_asset(p + '.' + name)
    L.set_material_instance_vector_parameter_value(
        mi, 'BaseColour', unreal.LinearColor(c[0], c[1], c[2], 1.0))
    unreal.EditorAssetLibrary.save_asset(p)
    print('%-18s %.3f %.3f %.3f' % (name, c[0], c[1], c[2]))

les.save_current_level()
print('saved')
