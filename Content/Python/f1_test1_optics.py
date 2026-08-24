"""F1 diagnosis, test 1 — optical signature.

Hypothesis: the frame reads as synthetic because it carries no evidence of a
lens or a sensor. Zero grain, zero vignette, perfectly uniform sharpness edge
to edge. Real photographs always carry some of this.

Gate position: ONE_BUILDING_GATE bans depth of field, bloom and motion blur.
It names those three and nothing else. Grain, vignette and chromatic aberration
are not finishing effects used to flatter weak geometry - they are camera
evidence - and they are not on the banned list. DOF/bloom/motion blur stay off,
so this test does NOT relax the gate.

DOF is deliberately NOT used: with a flat backdrop close behind the subject
there is nothing to defocus, so it would only soften the model itself.
"""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
ppv = acts['LOOK_Post']
s = ppv.get_editor_property('settings')

def setp(name, value, override=None):
    try:
        s.set_editor_property(name, value)
        if override:
            s.set_editor_property(override, True)
        return True
    except Exception as e:
        print('  could not set %s: %s' % (name, str(e)[:70]))
        return False

# sensor grain — the single strongest "a camera took this" cue
setp('film_grain_intensity', 0.80, 'override_film_grain_intensity')
setp('film_grain_intensity_shadows', 0.95, 'override_film_grain_intensity_shadows')
setp('film_grain_intensity_midtones', 0.75, 'override_film_grain_intensity_midtones')
setp('film_grain_intensity_highlights', 0.45, 'override_film_grain_intensity_highlights')
setp('film_grain_texel_size', 1.2, 'override_film_grain_texel_size')
# lens falloff toward the corners
setp('vignette_intensity', 0.42, 'override_vignette_intensity')
# very slight colour fringing at the edges of the frame
setp('scene_fringe_intensity', 0.30, 'override_scene_fringe_intensity')

# explicitly hold the three the gate DOES ban
setp('bloom_intensity', 0.0, 'override_bloom_intensity')
setp('motion_blur_amount', 0.0, 'override_motion_blur_amount')

ppv.set_editor_property('settings', s)
r = ppv.get_editor_property('settings')
print('film grain      %.2f' % r.get_editor_property('film_grain_intensity'))
print('vignette        %.2f' % r.get_editor_property('vignette_intensity'))
print('scene fringe    %.2f' % r.get_editor_property('scene_fringe_intensity'))
print('bloom           %.2f  (gate-banned, held at zero)'
      % r.get_editor_property('bloom_intensity'))
print('motion blur     %.2f  (gate-banned, held at zero)'
      % r.get_editor_property('motion_blur_amount'))
les.save_current_level()
print('saved')
