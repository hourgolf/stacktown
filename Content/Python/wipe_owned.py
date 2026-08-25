"""Destroy everything this build owns. Prefix-gated, like the Portland build's
wipe_owned - it can only ever delete what the block script created.

BLD_ (the reused Stage 1 building), STAGE_, CAM_ and LIGHT_Key/Fill are NOT
owned and are never touched.
"""
import unreal
OWNED=('BLD2_','AV_','CORE_','PARTY_','SUR_','BAKED_','SKT_','LIGHT2_','ELEV_',
       'ZONE_','LAMP_','LAMPLIGHT_')
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
n=0
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith(OWNED):
        eas.destroy_actor(a); n+=1
print('wiped %d owned actors'%n)
les.save_current_level()
