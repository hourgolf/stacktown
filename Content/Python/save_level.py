"""Save the current level, unconditionally, and prove it reached disk.

DO NOT guard this on get_dirty_map_packages(). Measured on 2026-08-24:
component.set_material() changes the component and the viewport but does NOT
mark the map package dirty. The dirty list came back EMPTY while four vehicles
carried unsaved material overrides, and a save guarded on that check skipped
them in silence. Forcing the save grew Stage2_Block.umap from 880,776 to
881,708 bytes, which is what the changes weigh.

The size and timestamp are printed rather than assumed. "save returned True" is
not evidence that anything was written.
"""
import unreal, os

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
pkg = w.get_outermost().get_name()
path = unreal.Paths.convert_relative_path_to_full(
    unreal.Paths.project_content_dir()) + pkg.replace('/Game/', '') + '.umap'

before = (os.path.getsize(path), os.path.getmtime(path)) if os.path.exists(path) else (0, 0)
ok = les.save_current_level()
after = (os.path.getsize(path), os.path.getmtime(path)) if os.path.exists(path) else (0, 0)
print('%s\n  save_current_level -> %s' % (pkg, ok))
print('  %d bytes -> %d bytes   (mtime moved: %s)'
      % (before[0], after[0], after[1] > before[1]))
if after[1] <= before[1]:
    print('  WARNING: the file did not change. Either there was nothing to '
          'save, or the save did not reach disk.')
