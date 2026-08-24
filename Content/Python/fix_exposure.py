"""Bring the block hero back inside the exposure criterion.

Blown pixels localise to a vertical stripe at x~2688 repeating every 256 px -
one per floor - which is the interior practicals hitting the reveal box behind
the glass hard enough to clip. Pull them down.

Crushed is the other end: MI_interior at 0.03 albedo is near-black behind the
glazing. Lifting it slightly keeps the room reading as a room rather than a hole
without washing it out.
"""
import unreal
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
L=unreal.MaterialEditingLibrary

n=0
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith(('LIGHT2_','LIGHT_Practical')): continue
    for c in a.get_components_by_class(unreal.LightComponent):
        i=c.get_editor_property('intensity')
        if i<=0: continue
        c.set_editor_property('intensity', i*0.55)
        n+=1
print('practicals scaled x0.55: %d'%n)

p='/Game/Stacktown/Materials/MI_interior'
mi=unreal.EditorAssetLibrary.load_asset(p+'.MI_interior')
old=L.get_material_instance_vector_parameter_value(mi,'BaseColour')
L.set_material_instance_vector_parameter_value(mi,'BaseColour',
    unreal.LinearColor(0.055,0.052,0.048,1.0))
unreal.EditorAssetLibrary.save_asset(p)
print('MI_interior albedo %.3f -> 0.055'%old.r)
les.save_current_level()
