"""Shopfront dressing, from the Deko pack's GEOMETRY and our materials.

"The storefronts look blank" was the first thing said about block C, and it has
been true of every commercial ground floor since. The Deko_MatrixDemo pack is a
shopfront pack - 43 awnings, 59 signs, 36 boards - and it is the right source
for the SHAPES. It is the wrong source for the surfaces: 4.6 GB of textures
authored for a photoreal first-person city, including a 105 MB normal map for
micro-plastic detail, on a model read at 0.4% of frame width.

So this does what place_baked does for the vehicles: donor mesh, our material,
bound by role. The pack stays source material and its textures never ship.

MEASURED before use: the meshes are correctly scaled for 1 uu = 1 cm - the A01
awning is 287 x 101 x 99, a 2.9 m awning with a 1 m projection - and the awning
pivot sits at the WALL with the mesh projecting +Y, so it wants yaw 180 to lean
out over a street that is at -Y in block-local space.
"""
import unreal, math, random
import _path  # noqa: F401
from city import BLOCKS

D = '/Game/Deko_MatrixDemo/City/Meshes'
F = '/Game/Stacktown/Materials'
AWNINGS = ('SM_BLDG_Prop_BA_Awning_A01_N1', 'SM_BLDG_Prop_BA_Awning_C01_N1',
           'SM_BLDG_Prop_BB_Awning_B01_N1', 'SM_BLDG_Prop_CA_Awning_A01_N1')
BOARDS = ('SM_BLDG_Prop_BA_BoardM_A01_N1', 'SM_BLDG_Prop_BB_BoardM_A01_N1',
          'SM_BLDG_Prop_CA_BoardM_A01_N1')
SIGNS = ('SM_BLDG_Prop_BA_Sign_A01_N1', 'SM_BLDG_Prop_BA_Sign_D01_N1',
         'SM_BLDG_Prop_BB_Sign_B01_N1')
CLOTH = ('MI_card_rose', 'MI_card_sage', 'MI_card_ochre', 'MI_canopy_accent')

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

_m = {}
def M(n):
    if n not in _m:
        _m[n] = unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (F, n, n))
    return _m[n]

alls = eas.get_all_level_actors()
assert alls, 'enumerated zero actors - the wipe is not looking at the level'
killed = 0
for a in list(alls):
    if a.get_actor_label().startswith('SHOP_'):
        eas.destroy_actor(a); killed += 1
print('removed %d SHOP_ actors (of %d in level)' % (killed, len(alls)))


def world(blk, lx, ly):
    ox, oy, _ = blk['origin']
    y = math.radians(blk['yaw'])
    return (ox + lx*math.cos(y) - ly*math.sin(y),
            oy + lx*math.sin(y) + ly*math.cos(y))


def put(mesh, wx, wy, wz, yaw, label, colour):
    sm = unreal.load_asset('%s/%s.%s' % (D, mesh, mesh))
    if not sm:
        print('  missing', mesh); return 0
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                   unreal.Vector(wx, wy, wz),
                                   unreal.Rotator(0, 0, yaw))
    a.set_actor_label('SHOP_' + label)
    c = a.static_mesh_component
    c.set_editor_property('static_mesh', sm)
    for i in range(len(sm.get_editor_property('static_materials'))):
        c.set_material(i, M(colour))
    return 1


PIER = 52.0
n = 0
for blk in BLOCKS:
    for spec in blk['lots']:
        if spec.get('kind') != 'gen' or spec.get('style') == 'house':
            continue
        rnd = random.Random(spec.get('seed', 0) + 7717)
        x0, W = spec['x0'], spec['width']
        GF = spec['gf_h']
        sx0, sx1 = x0 + PIER, x0 + W - PIER
        span = sx1 - sx0
        # one awning per ~3 m of shopfront, which is how they actually come
        count = max(1, int(span / 300.0))
        for k in range(count):
            lx = sx0 + span*(k + 0.5)/count
            wx, wy = world(blk, lx, 0.0)
            # MEASURED: the shop glass runs z 40..GF-48 and the bulkhead
            # GF-40..GF, while the awning mesh spans pivot-17 to pivot+82. At
            # GF-52 the awning straddled the glass HEAD and rose above the
            # bulkhead - it hung over nothing. GF-130 puts its top at the glass
            # head, which is where an awning is fixed.
            n += put(rnd.choice(AWNINGS), wx, wy, GF - 130.0,
                     blk['yaw'] + 180.0, '%s_awn%d' % (spec['name'], k),
                     rnd.choice(CLOTH))
        # a fascia board over the bulkhead, and one hanging sign at the end
        wx, wy = world(blk, (sx0 + sx1)/2.0, 0.0)
        n += put(rnd.choice(BOARDS), wx, wy, GF - 18.0,
                 blk['yaw'] + 180.0, '%s_board' % spec['name'], 'MI_frame_print')
        wx, wy = world(blk, sx1 - 40.0, 0.0)
        n += put(rnd.choice(SIGNS), wx, wy, GF + 30.0,
                 blk['yaw'] + 180.0, '%s_sign' % spec['name'], 'MI_dark_metal')
print('shopfront dressing: %d pieces' % n)
les.save_current_level()
