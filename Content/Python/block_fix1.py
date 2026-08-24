"""Two fixes: hue separation, and give the block depth.

COLOUR. Measured off the render, the four facades came out R160/200/196/223 -
they differed in BRIGHTNESS, not hue, and 'sage' read R200 G192 B178, which is
warm. Two causes: the albedos were only ~0.04 apart per channel, and a 4500K key
swamps what little separation there is. Pushed apart, and the sage pushed cooler
to survive the warm key. All three stay in the card band (0.62-0.80 rough,
0.20 spec) - the recipe's warning is about albedo variation WITHIN a surface,
not between roles.

DEPTH. Every facade sat on Y=0, so the block read as one flat wall with
different heights. Real frontage steps. The budget puts a plane break at 3.9x
the 230 mm block-hero threshold, so these are all comfortably legible.
"""
import unreal

L = unreal.MaterialEditingLibrary
F = '/Game/Stacktown/Materials'
COLS = {'MI_card_ochre': (0.760, 0.585, 0.330),
        'MI_card_sage':  (0.470, 0.585, 0.470),
        'MI_card_rose':  (0.740, 0.520, 0.500)}
for n, c in COLS.items():
    mi = unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (F, n, n))
    L.set_material_instance_vector_parameter_value(
        mi, 'BaseColour', unreal.LinearColor(c[0], c[1], c[2], 1.0))
    unreal.EditorAssetLibrary.save_asset('%s/%s' % (F, n))
    print('%-15s %.3f %.3f %.3f' % (n, c[0], c[1], c[2]))

# -Y is toward the camera. Steps of 700 and 550 mm.
STEP = {'Wide': -70.0, 'Mid': 55.0, 'Narrow': 0.0}
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
moved = 0
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if not lbl.startswith('BLD2_'):
        continue
    who = lbl.split('_')[1]
    dy = STEP.get(who)
    if not dy:
        continue
    p = a.get_actor_location()
    a.set_actor_location(unreal.Vector(p.x, dy, p.z), False, False)
    moved += 1
print('stepped %d building actors' % moved)
les.save_current_level()
