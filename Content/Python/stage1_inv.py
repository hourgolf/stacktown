import unreal, json
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows = []
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if not lbl.startswith(('BLD_', 'STAGE_', 'PROP_')):
        continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        s = c.get_world_scale()
        rows.append((round(s.x * 100, 2), round(s.y * 100, 2), round(s.z * 100, 2)))
uniq = sorted(set(rows))
print('components: %d   distinct sizes: %d' % (len(rows), len(uniq)))
tiny = [d for d in uniq if min(d) < 3.0]
big = [d for d in uniq if max(d) > 2500.0]
print('sizes with a dimension < 3 uu (skip - chamfer would eat them): %d' % len(tiny))
print('sizes with a dimension > 2500 uu (skip - edges off-frame): %d' % len(big))
work = [d for d in uniq if d not in tiny and d not in big]
print('sizes to chamfer: %d' % len(work))
out = '/private/tmp/claude-501/-Users-ben-Documents-New-project/c7b8ef13-3903-46ab-bd2b-18279bb95fe6/scratchpad/stage1_sizes.json'
open(out, 'w').write(json.dumps({'work': work, 'skip_tiny': tiny, 'skip_big': big}))
print('wrote', out)
