"""Turn the street lamps off in daylight.

lamp_lights.py knows nothing about the rig mode, so 48 sodium pools were
burning on a sunlit street. Visibility rather than deletion, so switching back
to night costs nothing.
"""
import unreal, json
ON = json.loads(ARGS).get('on', True) if 'ARGS' in dir() else True
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = 0
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith('LAMPLIGHT_'):
        continue
    for c in a.get_components_by_class(unreal.RectLightComponent):
        c.set_visibility(ON, True)
    n += 1
print('lamp lights %s: %d' % ('on' if ON else 'off', n))
