"""Empty the benchmark sandbox down to its stage and lights. RUN ONCE.

Sandbox_Bench was made by duplicating Stage1_Building, so it arrives carrying
that building. This clears everything that is not stage or lighting, leaving a
lit, floored, empty room for the benchmark model to stand in.

DESTRUCTIVE, and deliberately its own script rather than a silent step inside
bench.py - a script that quietly empties a level the first time you run it is
the kind of thing that costs somebody a rebuild.

Refuses to run anywhere but the sandbox. Stage1_Building and Stage2_Block are
both real work; this must never be pointed at either.
"""
import unreal

SANDBOX = 'Sandbox_Bench'
KEEP = ('STAGE_', 'LIGHT_', 'BENCH_', 'STAND_', 'STUDY_')

eus = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
lvl = eus.get_editor_world().get_path_name()
if SANDBOX not in lvl:
    raise SystemExit('refusing to empty %s - this only ever runs in %s'
                     % (lvl, SANDBOX))

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
kept, killed = [], 0
for a in list(eas.get_all_level_actors()):
    n = a.get_actor_label()
    if n.startswith(KEEP) or isinstance(
            a, (unreal.DirectionalLight, unreal.SkyLight, unreal.SkyAtmosphere,
                unreal.PostProcessVolume, unreal.ExponentialHeightFog,
                unreal.RectLight)):
        kept.append(n)
        continue
    eas.destroy_actor(a)
    killed += 1
les.save_current_level()
print('emptied the sandbox: removed %d actors, kept %d' % (killed, len(kept)))
print('  kept: %s' % ', '.join(sorted(kept)[:12]))
