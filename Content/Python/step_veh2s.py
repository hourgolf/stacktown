"""Bind the two-sided card materials to the baked shell actors.

WHY these actors and not others. Every SM_Baked_* mesh is an OPEN SHELL - the
sedan has 12,004 open border edges against 6,064 triangles - because it came
from a skeletal mesh authored to be seen from outside only. M_StacktownMaster
is two_sided=False, so binding a card role to a shell culls its backfaces and
the road shows through the bodywork. That is defect 2 in the Stage 2 audit. The
2S master was created for it and then never wired to anything: counted against
the level before this script ran, ZERO components bound any *_2S material.

The mapping is by name: whatever a slot currently holds, use the *_2S sibling
if one exists. That keeps the palette decision where it already lives - in the
non-2S instance - instead of restating it here, so a vehicle recoloured later
does not need this file edited.

Slot NAMES are gone on these meshes (the skeletal bake keeps the count and
drops the names: 'Material_0', 'None', 'None'), so this works positionally,
which is the documented way to handle them.

Reversible: restore=True strips the overrides back to the non-2S instances.
Does not save the level.
"""
import unreal, json

PREFIXES = ('BAKED_veh',)          # pass {"prefixes": [...]} to widen

# GLAZING IS DELIBERATELY LEFT SINGLE-SIDED, and this is the one interesting
# decision in the file.
#
# Both masters are BLEND_OPAQUE, so MI_glass_b's Opacity 0.42 does nothing.
# Single-sided, the windscreen's outward faces are culled, it renders as
# nothing, and you see the modelled dashboard and the street beyond - which
# looks like working glass but is the culling bug wearing a disguise.
# Two-sided, it is drawn, and being opaque it becomes a flat dark slab that
# hides the interior entirely. Tested both ways on BAKED_veh0.
#
# Neither is glass. Sidedness is the wrong axis for this: vehicle glazing needs
# a TRANSLUCENT master, the same argument that justified the masked variant for
# foliage. Until that exists, the single-sided version is the better-looking of
# two wrong answers and it keeps the interior card visible, which
# MASTER_MATERIAL_SPEC's glass rule asks for. Pass {"glass": true} to include
# it and see for yourself.
SKIP = ('MI_glass',)

def apply(prefixes=PREFIXES, restore=False, glass=False):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    changed = missing = 0
    for a in eas.get_all_level_actors():
        if not a.get_actor_label().startswith(tuple(prefixes)): continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.get_editor_property('static_mesh')
            if not m: continue
            for i in range(len(m.get_editor_property('static_materials'))):
                cur = c.get_material(i)
                if not cur: continue
                name = cur.get_name()
                if not glass and name.startswith(SKIP):
                    if name.endswith('_2S'):          # undo a previous run
                        c.set_material(i, unreal.load_asset(
                            '/Game/Stacktown/Materials/%s' % name[:-3]))
                        print('   glazing left single-sided: %s slot %d'
                              % (a.get_actor_label(), i))
                    continue
                if restore:
                    if not name.endswith('_2S'): continue
                    tgt = '/Game/Stacktown/Materials/%s' % name[:-3]
                else:
                    if name.endswith('_2S'): continue
                    tgt = '/Game/Stacktown/Materials/%s_2S' % name
                asset = unreal.load_asset(tgt)
                if not asset:
                    print('   NO COUNTERPART for %s on %s slot %d'
                          % (name, a.get_actor_label(), i))
                    missing += 1
                    continue
                c.set_material(i, asset)
                changed += 1
    print('%s %d slots (%d had no counterpart)'
          % ('restored' if restore else 'bound to 2S', changed, missing))
    return missing

if __name__ == '__main__':
    args = json.loads(ARGS) if 'ARGS' in dir() else {}
    apply(args.get('prefixes', PREFIXES), args.get('restore', False),
          args.get('glass', False))
