import unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
cam = acts['CAM_Hero_B']
# reset to the approved second-angle transform before every evidence capture
cam.set_actor_location(unreal.Vector(4893.0, -8187.0, 2946.0), False, False)
cam.set_actor_rotation(unreal.Rotator(0.0, -12.0, 118.0), False)
cam.get_cine_camera_component().set_editor_property('current_focal_length', 70.0)
les.pilot_level_actor(cam)
les.editor_set_game_view(True)
unreal.SystemLibrary.execute_console_command(
    ues.get_editor_world(), 'Slate.bAllowThrottling 0')
l, r = cam.get_actor_location(), cam.get_actor_rotation()
print('CAM_Hero_B (%.0f, %.0f, %.0f) pitch %.1f yaw %.1f' % (l.x, l.y, l.z, r.pitch, r.yaw))
