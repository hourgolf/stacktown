"""One sweep assigns every BLD2_ component by its name prefix.

This is the piece that has to scale. Stage 1 wired materials per component by
hand; at metropolis scale that is the whole job. Here the role lives in the
component name, so adding a building costs nothing in material work.
"""
import unreal

F = '/Game/Stacktown/Materials'
_cache = {}
def M(n):
    if n not in _cache:
        _cache[n] = unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (F, n, n))
        if not _cache[n]:
            raise SystemExit('missing material %s' % n)
    return _cache[n]

# wall colour is per building; everything else is shared
WALL = {'Narrow': 'MI_card_ochre', 'Wide': 'MI_card_sage', 'Mid': 'MI_card_rose'}
SHARED = {'Glass_': 'MI_glass_b', 'Interior_': 'MI_interior',
          'Frame_': 'MI_frame_print', 'Mullion_': 'MI_frame_print',
          'Accent_': 'MI_canopy_accent', 'Roof_': 'MI_concrete'}

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assigned, unresolved = 0, []
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if not lbl.startswith('BLD2_'):
        continue
    who = lbl.split('_')[1]
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        nm = c.get_name()
        role = next((r for r in SHARED if nm.startswith(r)), None)
        if role:
            c.set_material(0, M(SHARED[role]))
        elif nm.startswith('Wall_') or nm.startswith('Band_'):
            c.set_material(0, M(WALL.get(who, 'MI_paint_cream')))
        else:
            unresolved.append(nm)
            continue
        assigned += 1
print('assigned %d slots; unresolved %s' % (assigned, sorted(set(unresolved))[:8]))
les.save_current_level()
print('saved')
