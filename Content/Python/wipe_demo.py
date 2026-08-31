"""Clear the test parcel and the catalogue display pad.

Both were scaffolding: the parcel proved ResolveMesh works and the pad showed
the three tiers side by side. The catalogue is assets now, not a diorama, and
the pad sits where the industrial block is going.
"""
import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
n = 0
for a in list(eas.get_all_level_actors()):
    l = a.get_actor_label()
    if l.startswith('TEST_') or l.startswith('CAT_') or l.startswith('SIM_'):
        eas.destroy_actor(a); n += 1
print('removed %d scaffolding actors' % n)
les.save_current_level()
