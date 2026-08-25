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


def put(mesh, wx, wy, wz, yaw, label, colour, sx=1.0):
    sm = unreal.load_asset('%s/%s.%s' % (D, mesh, mesh))
    if not sm:
        print('  missing', mesh); return 0
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                   unreal.Vector(wx, wy, wz),
                                   unreal.Rotator(0, 0, yaw))
    a.set_actor_label('SHOP_' + label)
    if sx != 1.0:
        a.set_actor_scale3d(unreal.Vector(sx, 1.0, 1.0))
    c = a.static_mesh_component
    c.set_editor_property('static_mesh', sm)
    for i in range(len(sm.get_editor_property('static_materials'))):
        c.set_material(i, M(colour))
    return 1


PIER = 52.0
# A modern lot's shopfront sits behind a 78 uu arcade, so dressing hung on the
# facade line floats in front of nothing. Push it back to the glass.
ARCADE = {'modern': 78.0, 'deco': 34.0}
BANNERS = ('SM_BLDG_Prop_BA_Banner_A01_N1', 'SM_BLDG_Prop_BB_Banner_B01_N1',
           'SM_BLDG_Prop_CA_Banner_C01_N1')
LAMPS = ('SM_BLDG_Prop_Lamp_Wall_A01_N1', 'SM_BLDG_Prop_Lamp_Wall_B01_N1')

n = 0
for blk in BLOCKS:
    for spec in blk['lots']:
        if spec.get('kind') != 'gen' or spec.get('style') in ('house', 'walkup'):
            continue
        rnd = random.Random(spec.get('seed', 0) + 7717)
        x0, W, GF = spec['x0'], spec['width'], spec['gf_h']
        back = ARCADE.get(spec.get('style'), 0.0)
        sx0, sx1 = x0 + PIER, x0 + W - PIER
        span = sx1 - sx0
        yawf = blk['yaw'] + 180.0          # facing out over the street

        def place(mesh, lx, ly, lz, yaw, tag, colour, sx=1.0):
            wx, wy = world(blk, lx, ly)
            return put(mesh, wx, wy, lz, yaw, '%s_%s' % (spec['name'], tag),
                       colour, sx)

        # WHAT A SHOP HANGS ON ITS FRONT is not one recipe. A row where every
        # unit has the same awning reads as a texture, not as a street.
        # Every commercial unit gets an awning - it is the piece that actually
        # reads at street level, and a 287 uu awning on a 900 uu shopfront read
        # as a stamp rather than as a shop. It is SCALED to fill its slot.
        # Banners and blades are additions on top, not alternatives.
        extra = rnd.choice(('none', 'banner', 'blade', 'blade'))

        if True:
            # Awnings follow the STRUCTURE. Dividing the span by a fixed 340
            # put them across the pilasters on the deco block rather than
            # between them - the lot already knows how many bays it has, so
            # one awning per bay, inset far enough to clear the pier.
            count = max(1, int(spec.get('bays', 3)))
            slot = span/count
            cloth = rnd.choice(CLOTH)       # one shop, one colour
            for k in range(count):
                lx = sx0 + span*(k + 0.5)/count
                # MEASURED: glass runs z 40..GF-48, bulkhead GF-40..GF, and the
                # awning mesh spans pivot-17..pivot+82. GF-130 puts its top at
                # the glass head, which is where an awning is fixed.
                n += place(rnd.choice(AWNINGS), lx, back, GF - 130.0, yawf,
                           'awn%d' % k, cloth, sx=(slot - PIER - 30.0)/287.0)
        if extra == 'banner':
            for k in range(3):
                lx = sx0 + span*(k + 0.5)/3.0
                n += place(rnd.choice(BANNERS), lx, back, GF + 40.0, yawf,
                           'ban%d' % k, rnd.choice(CLOTH))
        elif extra == 'blade':
            # a BLADE sign projects square to the wall, so it reads from down
            # the street rather than only from straight ahead
            side = rnd.choice((-1.0, 1.0))
            lx = sx0 + 60.0 if side < 0 else sx1 - 60.0
            n += place(rnd.choice(SIGNS), lx, back, GF + 6.0,
                       yawf + 90.0*side, 'blade', 'MI_dark_metal')

        # every unit gets a fascia over the bulkhead and a pair of wall lamps
        n += place(rnd.choice(BOARDS), (sx0 + sx1)/2.0, back, GF - 18.0, yawf,
                   'board', 'MI_frame_print')
        for k, lx in enumerate((sx0 + 30.0, sx1 - 30.0)):
            n += place(rnd.choice(LAMPS), lx, back, GF - 96.0, yawf,
                       'lamp%d' % k, 'MI_dark_metal')

print('shopfront dressing: %d pieces' % n)
les.save_current_level()
