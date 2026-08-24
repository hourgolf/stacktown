import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
cam = acts['CAM_Hero']
# Approved Stage 1 camera. Piloting moves the ACTOR, so navigating while
# piloted silently edits this. Reset before every evidence capture.
cam.set_actor_location(unreal.Vector(540.0, -9272.0, 2946.0), False, False)
cam.set_actor_rotation(unreal.Rotator(0.0, -12.0, 90.0), False)
c = cam.get_cine_camera_component()
c.set_editor_property('current_focal_length', 70.0)
l, r = cam.get_actor_location(), cam.get_actor_rotation()
print('CAM_Hero reset -> loc=(%.0f, %.0f, %.0f) pitch=%.1f yaw=%.1f roll=%.1f focal=%.0f'
      % (l.x, l.y, l.z, r.pitch, r.yaw, r.roll, c.current_focal_length))
les.pilot_level_actor(cam)
les.editor_set_game_view(True)
les.save_current_level()
print('piloted, game view on, saved')
