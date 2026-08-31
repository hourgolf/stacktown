"""Set the depth-of-field on LOOK_Post, from the local process.

The gate is evaluated with DOF off, and off here means focal_distance = 0 with
its override cleared. Turning it on means overriding the distance; turning it
back off means clearing that override again, which reset() does.

Sensor width matters: the rig's framing maths assumes 70 mm on a 36 mm back,
and LOOK_Post shipped with 24.576, so the blur would not have matched the
field of view it was drawn with.
"""
import os, subprocess, tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))


def _run(body):
    src = ('import unreal\n'
           'eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)\n'
           'for a in eas.get_all_level_actors():\n'
           '    if a.get_actor_label() != "LOOK_Post":\n'
           '        continue\n'
           '    st = a.get_editor_property("settings")\n'
           + body +
           '    a.set_editor_property("settings", st)\n'
           '    print("LOOK_Post updated")\n')
    f = os.path.join(tempfile.gettempdir(), '_dof.py')
    open(f, 'w').write(src)
    r = subprocess.run(['python3', os.path.join(_HERE, 'uepy.py'), f],
                       capture_output=True, text=True)
    if 'LOOK_Post updated' not in r.stdout:
        raise SystemExit('dof: LOOK_Post not updated\n' + r.stdout[-400:])


def set_dof(fstop, focus, blades=8, sensor=36.0, shutter=None, iso=None):
    b = ('    st.set_editor_property("depth_of_field_fstop", %f)\n'
         '    st.set_editor_property("override_depth_of_field_fstop", True)\n'
         '    st.set_editor_property("depth_of_field_focal_distance", %f)\n'
         '    st.set_editor_property("override_depth_of_field_focal_distance", True)\n'
         '    st.set_editor_property("depth_of_field_sensor_width", %f)\n'
         '    st.set_editor_property("override_depth_of_field_sensor_width", True)\n'
         '    st.set_editor_property("depth_of_field_blade_count", %d)\n'
         '    st.set_editor_property("override_depth_of_field_blade_count", True)\n'
         % (fstop, focus, sensor, blades))
    if shutter is not None:
        b += ('    st.set_editor_property("camera_shutter_speed", %f)\n'
              '    st.set_editor_property("override_camera_shutter_speed", True)\n' % shutter)
    if iso is not None:
        b += ('    st.set_editor_property("camera_iso", %f)\n'
              '    st.set_editor_property("override_camera_iso", True)\n' % iso)
    _run(b)


# THE HERO LOOK, chosen from the 25 Aug contact sheet. A 400 mm back at f/2 is
# the knee: the foreground goes soft while the subject plane still carries the
# awning scallops, the window reveals and the glazing bars. 150 is too polite;
# 1000 dissolves the model and stops it being a photograph of THIS town.
#
# Shutter pays for the aperture so the exposure matches the DOF-off condition -
# measured at 157.9..158.5 mean across five stops.
#
# The LEVEL'S SAVED STATE STAYS DOF-OFF. Building and grading need the geometry
# visible, and the gate amendment of 25 Aug keeps every A-E line judged with
# depth of field off. hero() is something you turn on for a frame and reset().
#
# f/2 -> f/2.8, 29 Aug, ON READER EVIDENCE. Shown the block frame in both lens
# modes, a reader said the BRICK TEXTURE was more convincing in judge and the
# LENSWORK was preferred in show - against what they called judge's "infinite
# focus". Not a vote against the lens: a vote against THIS MUCH BLUR. f/2 was
# chosen when every surface underneath was one paper texture and there was
# nothing to lose to defocus; there is now - brick coursing, three stocks,
# resin vehicles.
#
# Measured on the block frame with EXPOSURE HELD CONSTANT (ISO scaled by
# (N/N0)^2, because UE's post volume is a physical camera and f-stop drives
# exposure as well as defocus - the first run of that sweep changed the stop
# alone and produced a brightness ladder wearing a depth-of-field label):
#     f/2.0  ISO 800   brick detail 0.996   <- what the reader saw
#     f/2.8  ISO 1568  brick detail 1.300   <- chosen
#     f/4.0  ISO 3200  brick detail 1.536
#     f/5.6  ISO 6272  brick detail 1.889   nearly sharp throughout
# Brick legibility roughly doubles across the ladder; f/5.6 loses the miniature
# falloff the reader explicitly wanted. f/2.8 is where both halves survive.
#
# ISO RISES WITH THE STOP and that is physical, not a bug: 1568 at f/2.8. If a
# future rig treats ISO as a grain source rather than a number, this trade
# stops being free.
HERO = dict(fstop=2.8, sensor=400.0, blades=8, shutter=240.0, iso=1568.0)


def hero(focus):
    """The default hero look, focused at `focus` uu from the camera."""
    # every key from HERO, ISO included. Dropping iso here left the shot at
    # whatever ISO was current - 800 after a reset(), ~a stop under the 1568
    # the hero look is specified at. Same fault lensrig carried with a
    # literal 800; if a key is in HERO it gets passed, no exceptions.
    set_dof(HERO['fstop'], focus, blades=HERO['blades'],
            sensor=HERO['sensor'], shutter=HERO['shutter'],
            iso=HERO['iso'])


def reset(fstop=4.0, shutter=60.0, iso=800.0):
    """Back to the gate condition: DOF off, base exposure."""
    _run('    st.set_editor_property("override_depth_of_field_focal_distance", False)\n'
         '    st.set_editor_property("depth_of_field_focal_distance", 0.0)\n'
         '    st.set_editor_property("depth_of_field_fstop", %f)\n'
         '    st.set_editor_property("camera_shutter_speed", %f)\n'
         '    st.set_editor_property("camera_iso", %f)\n' % (fstop, shutter, iso))
