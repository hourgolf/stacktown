import unreal
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n=0
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith(('LIGHT2_','LIGHT_Practical')): continue
    for c in a.get_components_by_class(unreal.LightComponent):
        c.set_visibility(False,True); n+=1
print('practicals hidden: %d'%n)
