"""Place LOOK_Feed: the show-side post volume carrying MI_FeedLayer.

Separate from LOOK_Post BY CONSTRUCTION (Docs/CAMERA_DESIGN.md): the
judge path never inherits the feed layer because the feed layer lives
here and only here. Unbound, priority above LOOK_Post so the blendable
composes after the fixed grade. Rerunnable; does not save the level.
"""
import unreal

w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print('level:', w.get_name())
assert w.get_name() == 'Sandbox_Bench', 'wrong level loaded - abort'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == 'LOOK_Feed':
        eas.destroy_actor(a)
        print('removed old LOOK_Feed')
mi = unreal.EditorAssetLibrary.load_asset(
    '/Game/Stacktown/Materials/MI_FeedLayer')
v = eas.spawn_actor_from_class(unreal.PostProcessVolume,
                               unreal.Vector(0, 0, 0))
v.set_actor_label('LOOK_Feed')
v.set_editor_property('unbound', True)
v.set_editor_property('priority', 10.0)
st = v.get_editor_property('settings')
arr = st.get_editor_property('weighted_blendables')
arr.get_editor_property('array').append(
    unreal.WeightedBlendable(weight=1.0, object=mi))
st.set_editor_property('weighted_blendables', arr)
v.set_editor_property('settings', st)
print('LOOK_Feed placed, unbound, priority 10, blendable MI_FeedLayer')
