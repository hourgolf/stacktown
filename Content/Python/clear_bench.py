"""Remove benchmark and study furniture from whatever level is open.

Safe anywhere: these families are workshop furniture and never belong to a
city block. In Stage2_Block this is the cleanup; in the sandbox it is what
bench.py does before it rebuilds.
"""
import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
PREFIX = ('BENCH_', 'STAND_', 'STUDY_', 'BPCOUNT_')
gone = []
for a in list(eas.get_all_level_actors()):
    n = a.get_actor_label()
    if n.startswith(PREFIX):
        eas.destroy_actor(a)
        gone.append(n)
print('removed %d workshop actors: %s'
      % (len(gone), ', '.join(sorted(gone)) if gone else '(none)'))
les.save_current_level()
