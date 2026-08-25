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


def reset(fstop=4.0, shutter=60.0, iso=800.0):
    """Back to the gate condition: DOF off, base exposure."""
    _run('    st.set_editor_property("override_depth_of_field_focal_distance", False)\n'
         '    st.set_editor_property("depth_of_field_focal_distance", 0.0)\n'
         '    st.set_editor_property("depth_of_field_fstop", %f)\n'
         '    st.set_editor_property("camera_shutter_speed", %f)\n'
         '    st.set_editor_property("camera_iso", %f)\n' % (fstop, shutter, iso))
