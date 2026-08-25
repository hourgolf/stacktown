"""Assign every BLD2_/AV_ component by role prefix; wall colour comes from the
city table so a new block needs no edit here."""
import unreal, sys
import _path  # repo tool paths; replaces a dead scratchpad path
import labels
from city import BLOCKS
F='/Game/Stacktown/Materials'
# .get, not [] - an open zone has no wall colour and indexing it directly threw
# KeyError, which took the whole role sweep down and left 7000 components
# unassigned while every other step reported ok.
WALL={l['name']: l['wall'] for b in BLOCKS for l in b['lots'] if l.get('wall')}
# A pitched roof is the largest surface on a house and it was rendering on
# MI_concrete - the same pale grey as a flat commercial deck - so five houses
# read as five white wedges. Per lot, like the wall colour.
ROOF={l['name']: l.get('roofmat', 'MI_shingle_grey')
      for b in BLOCKS for l in b['lots'] if l.get('style') in ('house', 'walkup')}
SHARED={'Glass_':'MI_glass_b','Interior_':'MI_interior','Frame_':'MI_frame_print',
        'Mullion_':'MI_frame_print','Accent_':'MI_canopy_accent','Roof_':'MI_concrete',
        # ground roles, for zones that are not buildings
        'Ground_':'MI_concrete','Grass_':'MI_grass','Kerbing_':'MI_paint_cream'}
# Some families want a different material for the SAME role. A lamp column is
# dark painted metal, not the window-frame print - both are 'Frame_' because
# both are a frame, and role-in-the-name is about what a part IS, not what it
# is painted. Family wins over SHARED where it has an opinion.
FAMILY={'LAMP': {'Frame_':'MI_dark_metal'}}
_m={}
def M(n):
    if n not in _m: _m[n]=unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(F,n,n))
    return _m[n]
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
done=0; unresolved=[]
for a in eas.get_all_level_actors():
    l=a.get_actor_label()
    # ELEV_ carries the flank elevations and uses the same role prefixes, so
    # it binds here for free - which is the whole point of role-in-the-name.
    # LAMP_ is here because lamps are built AFTER this sweep normally runs, so
    # nothing ever bound them: all 54 sat on WorldGridMaterial, which is gate
    # line B1, and no check had ever looked. The build now calls this a second
    # time once the lamps exist rather than growing a second binder.
    if not l.startswith(('BLD2_', 'ELEV_', 'ZONE_', 'LAMP_')): continue
    fam=FAMILY.get(labels.family(l), {})
    who=l.split('_')[1]
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        nm=c.get_name()
        fam_role=next((r for r in fam if nm.startswith(r)),None)
        role=next((r for r in SHARED if nm.startswith(r)),None)
        if fam_role: c.set_material(0,M(fam[fam_role]))
        elif role: c.set_material(0,M(SHARED[role]))
        elif nm.startswith('Tile_'):
            c.set_material(0, M(ROOF.get(who, 'MI_shingle_grey')))
        elif nm.startswith('Wall_') or nm.startswith('Band_'):
            c.set_material(0,M(WALL.get(who,'MI_paint_cream')))
        else: unresolved.append(nm); continue
        done+=1
print('assigned %d slots; unresolved %s'%(done,sorted(set(unresolved))[:6]))
les.save_current_level()
