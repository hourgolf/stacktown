import unreal
eus = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lvl = eus.get_editor_world().get_path_name()
n = len(eas.get_all_level_actors())
print('OPEN LEVEL: %s   (%d actors)' % (lvl, n))
