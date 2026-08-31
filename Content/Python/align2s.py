"""Align each *_2S instance's paper amplitude with its non-2S counterpart.

The 2S instances still carried PaperNormalAmount 0.55, the value the main
instances were pushed off in Stage 2 when 0.55 proved too faint to read at the
player zoom. They are unused today, so this changes nothing on screen - the
point is that whoever binds them next gets the value that was actually chosen
rather than the one that was left behind.
"""
import unreal
MIL = unreal.MaterialEditingLibrary
pairs = [('MI_card_ochre_2S','MI_card_ochre'), ('MI_card_rose_2S','MI_card_rose'),
         ('MI_card_sage_2S','MI_card_sage'), ('MI_paint_cream_2S','MI_paint_cream'),
         ('MI_frame_print_2S','MI_frame_print')]
for two, one in pairs:
    a = unreal.load_asset('/Game/Stacktown/Materials/%s' % two)
    b = unreal.load_asset('/Game/Stacktown/Materials/%s' % one)
    if not a or not b: print('MISSING', two, one); continue
    want = MIL.get_material_instance_scalar_parameter_value(b, 'PaperNormalAmount')
    got  = MIL.get_material_instance_scalar_parameter_value(a, 'PaperNormalAmount')
    if abs(want - got) > 1e-4:
        MIL.set_material_instance_scalar_parameter_value(a, 'PaperNormalAmount', want)
    print('  %-20s %.2f -> %.2f   (from %s)' % (two, got,
          MIL.get_material_instance_scalar_parameter_value(a,'PaperNormalAmount'), one))
    unreal.EditorAssetLibrary.save_asset('/Game/Stacktown/Materials/%s' % two, only_if_is_dirty=False)
