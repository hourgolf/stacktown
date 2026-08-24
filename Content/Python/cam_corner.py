import unreal, math
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label()=='CAM_Corner': eas.destroy_actor(a)
# the end of block A: Mid's outer corner, the view that showed the fin
t=(4150.0,-260.0,900.0); D,PITCH,ANG=2600.0,-8.0,58.0
p=math.radians(abs(PITCH)); horiz=D*math.cos(p)
x=t[0]+horiz*math.sin(math.radians(ANG)); y=t[1]-horiz*math.cos(math.radians(ANG))
z=t[2]+D*math.sin(p)
yaw=math.degrees(math.atan2(t[1]-y,t[0]-x))
cam=eas.spawn_actor_from_class(unreal.CineCameraActor,unreal.Vector(x,y,z),
                               unreal.Rotator(0.0,PITCH,yaw))
cam.set_actor_label('CAM_Corner')
c=cam.get_cine_camera_component()
c.set_editor_property('current_focal_length',70.0)
fb=c.get_editor_property('filmback'); fb.set_editor_property('sensor_width',36.0)
fb.set_editor_property('sensor_height',24.0); c.set_editor_property('filmback',fb)
fs=c.get_editor_property('focus_settings')
fs.set_editor_property('focus_method',unreal.CameraFocusMethod.DISABLE)
c.set_editor_property('focus_settings',fs)
print('CAM_Corner placed at block A end')
les.save_current_level()
