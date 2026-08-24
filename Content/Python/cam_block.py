import unreal, math
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label()=='CAM_Block': eas.destroy_actor(a)
# from Saved/Stage2/STAGE2_BUDGET.md: block centre (2140,0,1100), d=11168, pitch -12
D, PITCH = 11168.0, -12.0
cx, cz = 2140.0, 1100.0
horiz=D*math.cos(math.radians(abs(PITCH)))
cam=eas.spawn_actor_from_class(unreal.CineCameraActor,
    unreal.Vector(cx, -horiz, cz + D*math.sin(math.radians(abs(PITCH)))),
    unreal.Rotator(0.0, PITCH, 90.0))
cam.set_actor_label('CAM_Block')
c=cam.get_cine_camera_component()
c.set_editor_property('current_focal_length',70.0)
fb=c.get_editor_property('filmback')
fb.set_editor_property('sensor_width',36.0); fb.set_editor_property('sensor_height',24.0)
c.set_editor_property('filmback',fb)
fs=c.get_editor_property('focus_settings')
fs.set_editor_property('focus_method',unreal.CameraFocusMethod.DISABLE)
c.set_editor_property('focus_settings',fs)
print('CAM_Block at',cam.get_actor_location(),'frame width %.0f uu'%(2*D*math.tan(math.radians(28.84/2))))
les.save_current_level()
