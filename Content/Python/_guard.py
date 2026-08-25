import unreal, os, sys
_want = '/Users/ben/Documents/Unreal Projects/StacktownAlpha/'
_have = os.path.abspath(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
if os.path.normpath(_have) != os.path.normpath(_want):
    raise SystemExit('WRONG EDITOR: %s (expected %s)' % (_have, _want))
_lvl = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name()
# Stage 2 moved the work to Stage2_Block. The repo copy of this guard still
# named only Stage1_Building, so anything run through the repo's own rung.sh
# refused to run at all - which is why a scratchpad copy had quietly become the
# real guard. Keep this list current; it is the whole point of the file.
_ALLOWED = ('Stage1_Building', 'Stage2_Block')
if not any(k in _lvl for k in _ALLOWED):
    raise SystemExit('WRONG LEVEL: %s (allowed: %s)' % (_lvl, ', '.join(_ALLOWED)))
# Put the repository's own script and tool directories on sys.path. rung.sh
# executes a TEMP COPY of the script, so Content/Python is not on the path and
# `import _path` (or anything else next to it) would fail. Doing it here means
# every guarded script gets working imports for free, and none of them needs to
# know where the project lives.
# Purge the dead scratchpad, both from sys.path and from the import cache.
# The editor's Python session persists across remote-exec calls, so a module
# imported earlier from /private/tmp stays in sys.modules and keeps being
# returned no matter what is put on the path afterwards - `from city import
# STREETS` failed with the new constant sitting in the repo copy, because the
# process was still holding the scratchpad's city.py from an earlier session.
sys.path[:] = [p for p in sys.path if '/private/tmp/' not in p]
# Drop every cached module that came from the dead scratchpad OR from this
# project, so each guarded run imports the CURRENT source. Without this the
# editor happily serves a city.py it read minutes ago: step_stage2.py was
# still printing street positions from the previous version of the table after
# the file on disk had been edited, which is indistinguishable from the edit
# not working.
for _n in [n for n, m in list(sys.modules.items())
           if getattr(m, '__file__', None)
           and ('/private/tmp/' in str(m.__file__)
                or os.path.normpath(_have) in os.path.normpath(str(m.__file__)))]:
    del sys.modules[_n]

sys.path.insert(0, os.path.join(_have, 'Content', 'Python'))
sys.path.insert(0, os.path.join(_have, 'Tools', 'measure'))

print('[guard] %s  %s' % (os.path.basename(os.path.normpath(_have)), _lvl))
