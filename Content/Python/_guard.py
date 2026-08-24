import unreal, os
_want = '/Users/ben/Documents/Unreal Projects/StacktownAlpha/'
_have = os.path.abspath(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
if os.path.normpath(_have) != os.path.normpath(_want):
    raise SystemExit('WRONG EDITOR: %s (expected %s)' % (_have, _want))
_lvl = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name()
if 'Stage1_Building' not in _lvl:
    raise SystemExit('WRONG LEVEL: %s' % _lvl)
print('[guard] %s  %s' % (os.path.basename(os.path.normpath(_have)), _lvl))
