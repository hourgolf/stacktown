"""Destroy every actor of one label family, locally. Family arrives in a temp
file, for the reason wipe_lots.py records."""
import unreal, os, tempfile
LIST = os.path.join(tempfile.gettempdir(), 'stacktown_wipe_family.txt')
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
alls = eas.get_all_level_actors()
assert alls, 'enumerated zero actors - the wipe is not looking at the level'
fam = open(LIST).read().strip() if os.path.exists(LIST) else ''
assert fam, 'no family at %s - refusing to guess what to destroy' % LIST
n = 0
for a in list(alls):
    if a.get_actor_label().split('_')[0] == fam:
        eas.destroy_actor(a); n += 1
print('removed %d %s_ actors (of %d in level)' % (n, fam, len(alls)))
