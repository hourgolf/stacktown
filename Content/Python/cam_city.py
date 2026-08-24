import unreal, math
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label()=='CAM_City': eas.destroy_actor(a)
# three-quarter aerial down the street so both rows and the road between read
t=(2600.0,-800.0,700.0); D,PITCH,ANG=6600.0,-13.0,-89.0  # ON the street centreline
p=math.radians(abs(PITCH)); horiz=D*math.cos(p)
x=t[0]+horiz*math.sin(math.radians(ANG)); y=t[1]-horiz*math.cos(math.radians(ANG))
z=t[2]+D*math.sin(p)
yaw=math.degrees(math.atan2(t[1]-y,t[0]-x))
cam=eas.spawn_actor_from_class(unreal.CineCameraActor,unreal.Vector(x,y,z),
                               unreal.Rotator(0.0,PITCH,yaw))
cam.set_actor_label('CAM_City')
c=cam.get_cine_camera_component()
c.set_editor_property('current_focal_length',70.0)
fb=c.get_editor_property('filmback'); fb.set_editor_property('sensor_width',36.0)
fb.set_editor_property('sensor_height',24.0); c.set_editor_property('filmback',fb)
fs=c.get_editor_property('focus_settings')
fs.set_editor_property('focus_method',unreal.CameraFocusMethod.DISABLE)
c.set_editor_property('focus_settings',fs)
fw=2*D*math.tan(math.radians(28.84/2))
print('CAM_City d=%.0f frame %.0f uu  0.4%% threshold %.0f mm'%(D,fw,fw*0.004*10))
les.save_current_level()
