"""Save the current level, explicitly and loudly - never as a side effect."""
import unreal
ok = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('level saved: %s' % ok)
