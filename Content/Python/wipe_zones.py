"""Destroy every ZONE_ actor, through the LOCAL editor API.

rebuild_zones.py first tried this over MCP with get_all_level_actors, which
returned something unparseable and was swallowed - it reported "removed 0" and
then built a second set on top of the first. street_lamps.wipe() failed exactly
this way once before and left 96 lamps where 48 were wanted. A wipe that cannot
prove it enumerated anything is worse than no wipe, so this one runs locally
and asserts it saw actors at all.
"""
import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
all_actors = eas.get_all_level_actors()
assert all_actors, 'enumerated zero actors - the wipe is not looking at the level'
n = 0
for a in list(all_actors):
    if a.get_actor_label().startswith('ZONE_'):
        eas.destroy_actor(a)
        n += 1
print('removed %d ZONE_ actors (of %d in level)' % (n, len(all_actors)))
