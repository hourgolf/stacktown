"""Inspection cameras aimed at the fabrication marks. Not gate evidence."""
import unreal, math
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith('CAM_Mark_'): eas.destroy_actor(a)
VIEWS=[('CAM_Mark_Canopy',(420.0,-40.0,400.0),900.0, 26.0,-16.0),
       ('CAM_Mark_Parapet',(940.0,-30.0,1930.0),900.0,-30.0,-10.0),
       ('CAM_Mark_Pier',(60.0,-6.0,140.0),700.0, 38.0, -6.0)]
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
    fw=2*d*math.tan(math.radians(28.84/2))
    print('%-18s d=%4.0f uu  frame width %5.0f uu  %.2f px/uu at 4436 px'%(lbl,d,fw,4436/fw))
les.save_current_level()
