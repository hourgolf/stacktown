"""Assign every BLD2_/AV_ component by role prefix; wall colour comes from the
city table so a new block needs no edit here."""
import unreal, sys
sys.path.insert(0,'/private/tmp/claude-501/-Users-ben-Documents-New-project/c7b8ef13-3903-46ab-bd2b-18279bb95fe6/scratchpad')
from city import BLOCKS
F='/Game/Stacktown/Materials'
WALL={l['name']: l['wall'] for b in BLOCKS for l in b['lots']}
SHARED={'Glass_':'MI_glass_b','Interior_':'MI_interior','Frame_':'MI_frame_print',
        'Mullion_':'MI_frame_print','Accent_':'MI_canopy_accent','Roof_':'MI_concrete'}
_m={}
def M(n):
    if n not in _m: _m[n]=unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(F,n,n))
    return _m[n]
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
done=0; unresolved=[]
for a in eas.get_all_level_actors():
    l=a.get_actor_label()
    if not l.startswith('BLD2_'): continue
    who=l.split('_')[1]
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        nm=c.get_name()
        role=next((r for r in SHARED if nm.startswith(r)),None)
        if role: c.set_material(0,M(SHARED[role]))
        elif nm.startswith('Wall_') or nm.startswith('Band_'):
            c.set_material(0,M(WALL.get(who,'MI_paint_cream')))
        else: unresolved.append(nm); continue
        done+=1
print('assigned %d slots; unresolved %s'%(done,sorted(set(unresolved))[:6]))
les.save_current_level()
