"""Call the owner-wired ResolveMesh and see whether it does what it should.

Python cannot AUTHOR a Blueprint graph in this build but it can CALL one, so
the wiring can be tested without adding a temporary BeginPlay wire that would
then have to be unpicked.

Place a parcel, point it at the catalogue, resolve at tier 0, read the mesh
back, upgrade to tier 2, resolve again, read it back. If the two differ and
both are the expected assets, the graph works.
"""
import unreal
RT = '/Game/Stacktown/Runtime'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('TEST_Parcel'):
        eas.destroy_actor(a)

bp = unreal.load_asset('%s/BP_Parcel' % RT)
cat = unreal.load_asset('%s/DA_Catalogue' % RT)
assert bp and cat, 'runtime assets missing'

a = eas.spawn_actor_from_class(bp.generated_class(),
                               unreal.Vector(7000.0, 2200.0, 0.0), unreal.Rotator())
a.set_actor_label('TEST_Parcel')
a.set_editor_property('Catalogue', cat)
a.set_editor_property('RecipeId', unreal.Name('cottage'))
a.set_editor_property('WidthUU', 820.0)


def mesh_now():
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.static_mesh
        return m.get_name() if m else None
    return '<no component>'


print('before anything:      %s' % mesh_now())
for tier in (0, 2, 1):
    a.set_editor_property('Tier', tier)
    a.call_method('ResolveMesh', ())
    print('after ResolveMesh t%d: %s' % (tier, mesh_now()))
