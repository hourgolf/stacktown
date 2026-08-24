import unreal
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
removed=shown=0
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label()=='BAKE_Narrow':
        eas.destroy_actor(a); removed+=1
    elif a.get_actor_label().startswith('BLD2_Narrow'):
        a.set_actor_hidden_in_game(False)
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            c.set_visibility(True, True); c.set_hidden_in_game(False, True)
        shown+=1
print('removed %d bake actors, restored %d component actors'%(removed,shown))
les.save_current_level()
