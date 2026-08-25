"""The 'filmed' effects, as a set you can switch off and back on.

Grain was added early to help the photographed look and has outstayed it: at
1.05 with shadows weighted 1.25 it is visible as noise on every flat surface in
every frame, and it costs render time on captures we take twelve of at a time.
It also fights depth of field - blur plus grain reads as a bad scan rather than
as a photograph.

Off for now, to be reconsidered when the DOF and camera work is settled. The
authored values live here so they come back exactly, not approximately.

    ./Tools/rung.sh filmlook.py          -> off
    FILM=on ./Tools/rung.sh filmlook.py  -> back to the authored values
"""
import unreal, os

AUTHORED = {
    'film_grain_intensity': 1.05,
    'film_grain_intensity_shadows': 1.25,
    'film_grain_intensity_midtones': 1.0,
    'film_grain_intensity_highlights': 0.62,
    'vignette_intensity': 0.42,
    'scene_fringe_intensity': 0.30,
}
# Off means grain and fringe at zero. The VIGNETTE stays: it is a lens
# property rather than a film one, it costs nothing, and it is doing real work
# holding the eye inside the board.
OFF = dict(AUTHORED)
OFF['film_grain_intensity'] = 0.0
OFF['scene_fringe_intensity'] = 0.0

want = AUTHORED if os.environ.get('FILM', '').lower() == 'on' else OFF
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
hit = 0
for a in eas.get_all_level_actors():
    if a.get_actor_label() != 'LOOK_Post':
        continue
    st = a.get_editor_property('settings')
    for k, v in want.items():
        st.set_editor_property(k, v)
        st.set_editor_property('override_' + k, True)
    a.set_editor_property('settings', st)
    hit += 1
assert hit == 1, 'expected exactly one LOOK_Post, found %d' % hit
print('film look: grain %.2f  fringe %.2f  vignette %.2f'
      % (want['film_grain_intensity'], want['scene_fringe_intensity'],
         want['vignette_intensity']))
les.save_current_level()
