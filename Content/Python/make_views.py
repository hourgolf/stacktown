"""Exploratory camera set — other angles plus player-zoom close-ups.

NOT gate evidence. The approved cameras remain CAM_Hero and CAM_Hero_B; these
exist to judge how the build holds up at ranges a player would actually see,
where things that are sub-pixel at 95 m (chamfers, surface response, the
2.5 mm cut edges) become legible.
"""
import unreal, math

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith('CAM_View_'):
        eas.destroy_actor(a)

# (label, target, distance, plan angle deg, pitch deg)
VIEWS = [
    ('CAM_View_Approach',  (540.0, 0.0, 700.0), 3500.0,  30.0,  -5.0),
    ('CAM_View_Steep',     (540.0, 0.0, 975.0), 4000.0,   8.0, -35.0),
    ('CAM_View_Shopfront', (540.0, 0.0, 210.0), 1500.0,  -8.0,  -3.0),
    ('CAM_View_Windows',   (540.0, 0.0, 980.0),  900.0,  14.0,  -8.0),
    ('CAM_View_Corner',    (210.0, 0.0, 480.0),  950.0, -34.0, -10.0),
]

for lbl, t, d, ang, pitch in VIEWS:
    a = math.radians(ang)
    p = math.radians(abs(pitch))
    horiz = d * math.cos(p)
    x = t[0] + horiz * math.sin(a)
    y = t[1] - horiz * math.cos(a)
    z = t[2] + d * math.sin(p)
    yaw = math.degrees(math.atan2(t[1] - y, t[0] - x))
    cam = eas.spawn_actor_from_class(
        unreal.CineCameraActor, unreal.Vector(x, y, z),
        unreal.Rotator(0.0, pitch, yaw))
    cam.set_actor_label(lbl)
    c = cam.get_cine_camera_component()
    c.set_editor_property('current_focal_length', 70.0)
    fb = c.get_editor_property('filmback')
    fb.set_editor_property('sensor_width', 36.0)
    fb.set_editor_property('sensor_height', 24.0)
    c.set_editor_property('filmback', fb)
    fs = c.get_editor_property('focus_settings')
    fs.set_editor_property('focus_method', unreal.CameraFocusMethod.DISABLE)
    c.set_editor_property('focus_settings', fs)
    frame_w = 2 * d * math.tan(math.radians(28.84 / 2))
    print('%-20s d=%5.0f uu (%4.1f m)  frame width %5.0f uu (%4.1f m)  pitch %+.0f'
          % (lbl, d, d / 100, frame_w, frame_w / 100, pitch))

les.save_current_level()
print('saved')
