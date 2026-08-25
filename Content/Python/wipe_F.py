"""Destroy block F's actors, locally - never over MCP, for the reason
wipe_zones.py records."""
import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
alls = eas.get_all_level_actors()
assert alls, 'enumerated zero actors - the wipe is not looking at the level'
names = ('Elm', 'Maple', 'Cedar', 'Birch', 'Willow')
n = 0
for a in list(alls):
    l = a.get_actor_label()
    if l.startswith('BLD2_') and l.split('_')[1] in names:
        eas.destroy_actor(a); n += 1
print('removed %d block F actors (of %d in level)' % (n, len(alls)))
