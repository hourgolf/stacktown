"""Cameras for the two open decisions. Not gate evidence."""
import unreal, math
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith('CAM_Judge_'): eas.destroy_actor(a)
VIEWS=[
  # the crisp parapet cap corner - where a real dent would go
  ('CAM_Judge_Corner',(1086.0,-22.0,1944.0),340.0,-42.0,-20.0),
  # looking ALONG the fascia glue run so the repeated section is unmistakable
  ('CAM_Judge_Glue',  (600.0,-221.0, 405.0),520.0, 62.0,-26.0),
]
for lbl,t,d,ang,pitch in VIEWS:
    a=math.radians(ang); p=math.radians(abs(pitch)); horiz=d*math.cos(p)
    x=t[0]+horiz*math.sin(a); y=t[1]-horiz*math.cos(a); z=t[2]+d*math.sin(p)
    yaw=math.degrees(math.atan2(t[1]-y,t[0]-x))
    cam=eas.spawn_actor_from_class(unreal.CineCameraActor,unreal.Vector(x,y,z),
                                   unreal.Rotator(0.0,pitch,yaw))
    cam.set_actor_label(lbl)
    c=cam.get_cine_camera_component()
    c.set_editor_property('current_focal_length',70.0)
    fb=c.get_editor_property('filmback')
    fb.set_editor_property('sensor_width',36.0); fb.set_editor_property('sensor_height',24.0)
    c.set_editor_property('filmback',fb)
    fs=c.get_editor_property('focus_settings')
    fs.set_editor_property('focus_method',unreal.CameraFocusMethod.DISABLE)
    c.set_editor_property('focus_settings',fs)
    print('%-18s d=%4.0f uu  frame width %4.0f uu'%(lbl,d,2*d*math.tan(math.radians(28.84/2))))
les.save_current_level()
