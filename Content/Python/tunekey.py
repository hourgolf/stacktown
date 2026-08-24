import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
# Stage 0 was 300k lm at ~1830 uu. Stage 1 key sits at 4200 uu, so inverse
# square gives 300k * (4200/1830)^2 = 1.58M. 2.6M was ~65% over and was
# clipping the cream band courses.
for lbl, lm in (('LIGHT_Key', 1580000.0), ('LIGHT_Fill', 210000.0)):
    c = acts[lbl].rect_light_component
    c.set_editor_property('intensity', lm)
    print('%s -> %.0f lm' % (lbl, c.get_editor_property('intensity')))
les.save_current_level()
print('saved')
