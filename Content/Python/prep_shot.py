"""Put the viewport into the hero state immediately before a capture.

The editor is in a FourPanes2x2 layout, and in that layout piloting a
CineCameraActor moves the viewport to the camera but does NOT adopt its FOV -
the pane stays at the default 90 deg, which renders the model at about a
quarter size. Saving the level resets it again, so this has to run immediately
before every shot rather than once at setup.

Aspect is the pane's 1.560, not the camera's 3:2 - noted, not corrected here.
"""
import unreal
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
acts={a.get_actor_label():a for a in eas.get_all_level_actors()}
cam=acts['CAM_Hero']
cam.set_actor_location(unreal.Vector(540.0,-9272.0,2946.0),False,False)
cam.set_actor_rotation(unreal.Rotator(0.0,-12.0,90.0),False)
if les.get_pilot_level_actor()!=cam:
    les.pilot_level_actor(cam)
les.editor_set_game_view(True)
k=les.get_active_viewport_config_key()
les.set_level_viewport_fov(29.939,k)  # matches the authored 19.454 VFOV in a 1.560 pane
unreal.SystemLibrary.execute_console_command(ues.get_editor_world(),'stat none')
print('viewport ready: %s FOV %.2f'%(k,les.get_level_viewport_fov(k)))
