"""Remove duplicate actors, keeping one of each label.

A sweep that does not wipe before it builds doubles its own output, and it has
now happened four times: lamps twice, zones once, and elevations plus
practicals here. NAME-03 makes it fail the build; this is the broom.
"""
import unreal, collections
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
alls = eas.get_all_level_actors()
assert alls, 'enumerated zero actors'
seen, killed = set(), 0
for a in list(alls):
    l = a.get_actor_label()
    if l in seen:
        eas.destroy_actor(a); killed += 1
    else:
        seen.add(l)
print('removed %d duplicate actors, %d labels remain' % (killed, len(seen)))
