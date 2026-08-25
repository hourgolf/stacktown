"""The block hero, re-derived for a street with TWO facing rows.

WHY THE OLD ONE IS WRONG. CAM_Block and CAM_Hero sit at y about -10,000 looking
toward +Y. Block A's facades face -Y and block B's face +Y, so from down there
the camera is BEHIND block B and the frame is filled by its unarticulated rear
elevations - three blank slabs. Measured from the level: block B's mass runs
y -1662..-2420 and its facade plane is -1662, on the far side from those
cameras.

WHY IT HAS TO BE A CANYON SHOT. The two rows face each other. There is no
viewpoint outside the street from which both facades are visible - to see both
you have to stand between them. So the hero looks ALONG the street, which is
what the Stage 3 record already concluded ("both rows read as facades from a
camera on the street centreline") without the hero ever being re-derived.

WHY IT TILTS DOWN. Looking along the street puts the vanishing point at the end
of the board, where the backdrop does not reach and there is black void. Pitch
-26 pushes that out of frame and brings the road and both pavements in, which
also reads as a model on a table rather than a street with a hole in it.

Additive: CAM_Block and CAM_Hero are left exactly where they are, so every
earlier capture stays reproducible.
"""
import unreal, math

NAME = 'CAM_Street_Hero'
LOC = (-3200.0, -860.0, 3400.0)
ROT = (0.0, -26.0, 2.0)              # roll, pitch, yaw - Rotator order, see AGENTS traps
FOCAL, SENSOR_W, SENSOR_H = 70.0, 36.0, 24.0

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label() == NAME:
        eas.destroy_actor(a)

cam = eas.spawn_actor_from_class(unreal.CineCameraActor,
                                 unreal.Vector(*LOC), unreal.Rotator(*ROT))
cam.set_actor_label(NAME)
c = cam.get_cine_camera_component()
c.set_editor_property('current_focal_length', FOCAL)
fb = c.get_editor_property('filmback')
fb.set_editor_property('sensor_width', SENSOR_W)
fb.set_editor_property('sensor_height', SENSOR_H)
c.set_editor_property('filmback', fb)
fs = c.get_editor_property('focus_settings')
fs.set_editor_property('focus_method', unreal.CameraFocusMethod.DISABLE)   # gate section E
c.set_editor_property('focus_settings', fs)

hfov = 2.0*math.degrees(math.atan(SENSOR_W/(2.0*FOCAL)))
print('%s at (%.0f,%.0f,%.0f) pitch %.0f yaw %.0f  %.0fmm  HFOV %.2f deg'
      % (NAME, LOC[0], LOC[1], LOC[2], ROT[1], ROT[2], FOCAL, hfov))
# 0.4% of frame width is the threshold a feature must subtend to read at all
for d in (2000.0, 4000.0, 6000.0):
    fw = 2.0*d*math.tan(math.radians(hfov/2.0))
    print('   at %5.0f uu: frame %6.0f uu, 0.4%% threshold %5.1f uu (%.0f mm)'
          % (d, fw, fw*0.004, fw*0.004*10))
