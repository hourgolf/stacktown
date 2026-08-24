"""Stage 1 polish: glazing colour + deliberate stacking misalignment (gate C3).

The reference model's sections do not line up perfectly - that is a large part
of why it reads as hand-assembled. Each floor actor is nudged a few tens of mm
laterally so the stacked bands sit slightly out of true.
"""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}

# --- glazing colour: cool blue-grey, as in the reference photo ---
g = unreal.EditorAssetLibrary.load_asset(
    '/Game/Stacktown/Materials/MI_glass.MI_glass')
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    g, 'BaseColour', unreal.LinearColor(0.055, 0.085, 0.105, 1.0))
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    g, 'Opacity', 0.30)
unreal.EditorAssetLibrary.save_asset('/Game/Stacktown/Materials/MI_glass')
print('glazing recoloured cool blue-grey')

# --- C3: stacked sections slightly out of true ---
OFFSETS = {'BLD_Floor_1': (3.5, -1.5),
           'BLD_Floor_2': (-2.5, 1.0),
           'BLD_Floor_3': (4.5, -2.0),
           'BLD_Floor_4': (-1.5, 2.5)}
for lbl, (dx, dy) in OFFSETS.items():
    a = acts.get(lbl)
    if not a:
        print('  missing', lbl)
        continue
    l = a.get_actor_location()
    a.set_actor_location(unreal.Vector(dx, dy, l.z), False, False)
    print('  %s nudged (%+.0f, %+.0f) mm' % (lbl, dx * 10, dy * 10))

les.save_current_level()
print('saved')
