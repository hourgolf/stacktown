"""Turn off practicals belonging to hidden buildings.

practicals.py derived light positions from BLD2_ geometry. BLD2_Wide is hidden
and its lot is now the Assetsville building, so those lights sit inside the new
walls and wash them out - the 0.268% blown highlights.
"""
import unreal
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
hidden=set()
for a in eas.get_all_level_actors():
    l=a.get_actor_label()
    if l.startswith('BLD2_'):
        vis=any(c.is_visible() for c in a.get_components_by_class(unreal.StaticMeshComponent))
        if not vis: hidden.add(l.split('_')[1])
print('hidden buildings:',sorted(hidden))
off=0
for a in eas.get_all_level_actors():
    l=a.get_actor_label()
    if not l.startswith('LIGHT2_'): continue
    who=l.split('_')[1]
    if who in hidden:
        for c in a.get_components_by_class(unreal.LightComponent):
            c.set_visibility(False,True)
            c.set_editor_property('intensity',0.0)
        off+=1
print('practicals disabled: %d'%off)
les.save_current_level()
