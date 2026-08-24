"""F1 test 2b — hand-cut imperfection at the CORRECT magnitude.

Test 2a applied 15-45 mm of misalignment to a 10.8 m building: 0.15-0.4% of
width. Invisible at 95 m. The reference photo's stacked paper sections are
misaligned by roughly 1-2% of the model's width. Matching that proportion on
this building means 100-250 mm, not 15-45 mm.

That is the finding: a hand-made model is not built to building tolerances.
Applying real-world construction accuracy is what makes it read as machined.

Values are SET, not accumulated, so this is reproducible from any state.
"""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}

# (dx, dy, yaw, roll) — ~1-2% of the 1080 uu facade width
FLOORS = {
    'BLD_Floor_1': (14.0, -5.0, 0.75, -0.55),
    'BLD_Floor_2': (-19.0, 7.0, -1.10, 0.70),
    'BLD_Floor_3': (22.0, -8.0, 0.95, -0.85),
    'BLD_Floor_4': (-11.0, 5.0, -0.70, 0.60),
}
for lbl, (dx, dy, yaw, roll) in FLOORS.items():
    a = acts.get(lbl)
    if not a:
        continue
    l = a.get_actor_location()
    a.set_actor_location(unreal.Vector(dx, dy, l.z), False, False)
    a.set_actor_rotation(unreal.Rotator(roll, 0.0, yaw), False)
    print('%s  offset (%+.0f, %+.0f) mm  yaw %+.2f  roll %+.2f'
          % (lbl, dx * 10, dy * 10, yaw, roll))

# elements a maker fits by hand and never gets square
FITTED = {
    'BLD_Canopy':     (0.0, 0.0, -1.40, 1.15),
    'BLD_Balcony':    (0.0, 0.0, 1.90, -1.30),
    'BLD_FireEscape': (0.0, 0.0, -1.55, 1.70),
    'BLD_Roof':       (6.0, -3.0, 0.55, -0.45),
    'PROP_Tree':      (0.0, 0.0, 9.0, 3.2),
}
for lbl, (dx, dy, yaw, roll) in FITTED.items():
    a = acts.get(lbl)
    if not a:
        continue
    l = a.get_actor_location()
    if dx or dy:
        a.set_actor_location(unreal.Vector(l.x + dx, l.y + dy, l.z), False, False)
    a.set_actor_rotation(unreal.Rotator(roll, 0.0, yaw), False)
    print('%s  yaw %+.2f  roll %+.2f' % (lbl, yaw, roll))

les.save_current_level()
print('saved')
