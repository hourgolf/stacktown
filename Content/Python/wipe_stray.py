"""Remove actors whose label is an engine default - debris from a script that
errored before it could name what it spawned. NAME-01 finds these; this is the
broom."""
import unreal, re
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
STRAY = re.compile(r'^(StaticMeshActor|Actor|CineCameraActor)\d*$')
n = 0
for a in list(eas.get_all_level_actors()):
    if STRAY.match(a.get_actor_label()):
        print('  removing %s at %s' % (a.get_actor_label(), a.get_actor_location()))
        eas.destroy_actor(a); n += 1
print('removed %d unnamed actors' % n)
