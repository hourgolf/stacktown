"""Set the sandbox SkyLight intensity. Reads stacktown_sky.json {intensity}.

Exists because turning Lumen off to stop the flicker costs the scene its
indirect bounce - measured at ~20% of frame mean (56.1 -> 44.7). The sky light
is the ambient surrogate that buys it back, and the studio-director skill is
explicit that the room contributing bounce is what separates a model from a
render. So this is not a brightness knob, it is the replacement for the light
Lumen was carrying.
"""
import unreal
import _path  # noqa: F401
import json
import os
import tempfile

job = json.load(open(os.path.join(tempfile.gettempdir(), 'stacktown_sky.json')))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
n = 0
for a in eas.get_all_level_actors():
    for c in a.get_components_by_class(unreal.SkyLightComponent):
        # COLOUR, not just level. LIGHT_Sky is SLS_CAPTURED_SCENE, so its
        # ambient is a capture of a room containing a large tan model board -
        # it is warm by construction. With Lumen on, bounce partly cancelled
        # that; with Lumen off the cast is exposed. Measured on the neutral
        # studio backdrop: R-B was +11.8 with Lumen, +28.4 without.
        col = job.get('color')
        if col:
            c.set_editor_property('light_color', unreal.Color(
                b=int(col[2]), g=int(col[1]), r=int(col[0]), a=255))
            gc = c.get_editor_property('light_color')
            print('  %-14s colour -> (%d,%d,%d)'
                  % (a.get_actor_label(), gc.r, gc.g, gc.b))
        before = c.get_editor_property('intensity')
        c.set_editor_property('intensity', float(job['intensity']))
        got = c.get_editor_property('intensity')
        assert abs(got - float(job['intensity'])) < 1e-3, 'sky did not take'
        print('  %-14s intensity %.2f -> %.2f' % (a.get_actor_label(), before, got))
        n += 1
if not n:
    raise SystemExit('no SkyLight found')
les.save_current_level()
print('skylight: %d set' % n)
