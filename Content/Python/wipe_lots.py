"""Destroy the actors of named lots, locally - never over MCP, for the reason
wipe_zones.py records.

The lot names arrive in a temp FILE, not an environment variable: rung.sh hands
the script to the editor over remote execution, so the editor process does not
inherit the caller's environment and WIPE_LOTS arrived empty. The assertion
below caught that rather than wiping nothing and reporting success."""
import unreal, os, tempfile

LIST = os.path.join(tempfile.gettempdir(), 'stacktown_wipe_lots.txt')
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
alls = eas.get_all_level_actors()
assert alls, 'enumerated zero actors - the wipe is not looking at the level'
want = set()
if os.path.exists(LIST):
    want = set(n for n in open(LIST).read().split(',') if n.strip())
assert want, 'no lot list at %s - refusing to guess what to destroy' % LIST
n = 0
for a in list(alls):
    l = a.get_actor_label()
    parts = l.split('_')
    if len(parts) > 1 and parts[0] in ('BLD2', 'ELEV', 'CORE') and parts[1] in want:
        eas.destroy_actor(a); n += 1
print('removed %d actors for lots %s (of %d in level)'
      % (n, ','.join(sorted(want)), len(alls)))
