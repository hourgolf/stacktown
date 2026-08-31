"""Remove lamp actors before regenerating them.

street_lamps.py tried to do this over MCP with SceneTools.get_all_level_actors
and destroy_actor. That path silently returned nothing - the wipe reported no
removals, the rebuild ran anyway, and the level ended up with 96 lamps and 384
components where 48 and 192 were intended. A wipe that cannot fail loudly has
to be somewhere it can, so it is an editor script.
"""
import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = 0
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith(('LAMP_', 'LAMPLIGHT_')):
        eas.destroy_actor(a); n += 1
print('removed %d lamp actors' % n)
