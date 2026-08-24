"""Close the party-wall gaps either side of the Assetsville lot.

82% of the block's crushed pixels were in a single 96 px column at frame centre:
the 17 uu slot between the Assetsville building (X 2005) and Narrow (X 1988),
looking through to black. Party-walled buildings should touch.

Shifts the AV lot to butt against Narrow, then fills the remainder to Mid with a
party wall rather than leaving a 74 uu slot.
"""
import unreal
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
F='/Game/Stacktown/Materials'

SHIFT=-17.0
n=0
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith('AV_'): continue
    p=a.get_actor_location()
    a.set_actor_location(unreal.Vector(p.x+SHIFT,p.y,p.z),False,False)
    n+=1
print('shifted %d AV modules by %.0f uu -> lot now butts Narrow'%(n,SHIFT))

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label()=='PARTY_AV_Mid': eas.destroy_actor(a)
cube=unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
x0,x1 = 3218.0, 3292.0        # AV right edge after shift .. Mid left edge
a=eas.spawn_actor_from_class(unreal.StaticMeshActor,
    unreal.Vector((x0+x1)/2.0, 400.0, 450.0), unreal.Rotator(0,0,0))
a.set_actor_label('PARTY_AV_Mid')
a.static_mesh_component.set_editor_property('static_mesh',cube)
a.set_actor_scale3d(unreal.Vector((x1-x0)/100.0, 8.0, 9.0))
a.static_mesh_component.set_material(0,
    unreal.EditorAssetLibrary.load_asset(F+'/MI_card_sage.MI_card_sage'))
print('party wall X %.0f..%.0f  Y 0..800  Z 0..900'%(x0,x1))
les.save_current_level()
