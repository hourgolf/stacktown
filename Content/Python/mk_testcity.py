"""Place the test city's roads and placeholder masses into TestCity.

RUN THROUGH rung.sh - it mutates. Idempotent: every actor it owns is
destroyed and rebuilt, so running it twice leaves one city, not two.

GEOMETRY COMES FROM citylayout, WHICH IS SELF-TESTED. Nothing here invents a
coordinate. If a number in this file disagrees with the layout module, the
layout module is right and this file is the bug - the same relationship
genbuild has with recipes.

THE LIGHTING HERE IS PROVISIONAL AND LABELLED SO. Read #2 found that the
lighting reads "somewhat render-like", and the plan folds that investigation
into deriving this board's rig. A rig inherited by accident from a placement
script would smuggle the thing under investigation in as a default, so these
two actors exist ONLY so the layout can be looked at, carry PROVISIONAL in
their names, and are expected to be deleted by the rig work.
"""
import unreal
import citylayout as L

CUBE = '/Engine/BasicShapes/Cube.Cube'
M_BOARD = '/Game/Stacktown/Materials/MI_model_board.MI_model_board'
M_ROAD = '/Game/Stacktown/Materials/MI_gravel.MI_gravel'
M_WALK = '/Game/Stacktown/Materials/MI_concrete.MI_concrete'
M_MASS = '/Game/Stacktown/Materials/MI_precast_grey.MI_precast_grey'

OWNED = ('TC_Board', 'TC_Road', 'TC_Walk', 'TC_Mass', 'TC_PROVISIONAL')

# board margin beyond the outermost facade line
MARGIN = 1600.0
ROAD_Z = 4.0            # carriageway slab, proud of the board
KERB_Z = 16.0           # footway, proud of the carriageway - a real kerb

# placeholder massing. Deterministic and documented: heights cycle so the
# layout reads as a street rather than a slab, WITHOUT implying a look. The
# recipes replace these; nothing here is a design decision.
HEIGHTS = (1200.0, 1800.0, 900.0, 2400.0, 1500.0, 1050.0)


def _box(eas, cube, mat, label, x0, y0, z0, x1, y1, z1):
    a = eas.spawn_actor_from_object(
        cube, unreal.Vector((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0),
        unreal.Rotator(0, 0, 0))
    a.set_actor_label(label)
    a.set_actor_scale3d(unreal.Vector((x1 - x0) / 100.0, (y1 - y0) / 100.0,
                                      (z1 - z0) / 100.0))
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        c.set_material(0, mat)
    return a


def build():
    if not (L.parcelmeta.selftests(verbose=False) and L.selftests(verbose=False)):
        raise SystemExit('layout self-tests failed - placing nothing')
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    cube = unreal.load_asset(CUBE)
    mats = {k: unreal.load_asset(v) for k, v in
            (('board', M_BOARD), ('road', M_ROAD),
             ('walk', M_WALK), ('mass', M_MASS))}
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label().startswith(OWNED):
            eas.destroy_actor(a)

    blocks = L.blocks()
    xs = [v for b in blocks.values() for v in (b['env'][0], b['env'][2])]
    ys = [v for b in blocks.values() for v in (b['env'][1], b['env'][3])]
    BX0, BX1 = min(xs) - MARGIN, max(xs) + MARGIN
    BY0, BY1 = min(ys) - MARGIN, max(ys) + MARGIN
    H = L.HALF                      # 1130 - facade line to centreline
    CW = _c_half = L.CORRIDOR / 2.0 - 430.0   # carriageway half width = 700

    _box(eas, cube, mats['board'], 'TC_Board', BX0, BY0, -200.0, BX1, BY1, 0.0)
    # arterial runs east-west, cross street north-south; both full width of
    # the board so the city sits ON a road network rather than beside one
    _box(eas, cube, mats['road'], 'TC_Road_Arterial',
         BX0, -CW, 0.0, BX1, CW, ROAD_Z)
    _box(eas, cube, mats['road'], 'TC_Road_Cross',
         -CW, BY0, 0.0, CW, BY1, ROAD_Z)
    # footways stop at the corridor so the intersection stays carriageway
    n = 0
    for sy in (-1, 1):
        for x0, x1 in ((BX0, -H), (H, BX1)):
            _box(eas, cube, mats['walk'], 'TC_Walk_A%d' % n,
                 x0, sy * CW, 0.0, x1, sy * H, KERB_Z)
            n += 1
    for sx in (-1, 1):
        for y0, y1 in ((BY0, -H), (H, BY1)):
            _box(eas, cube, mats['walk'], 'TC_Walk_C%d' % n,
                 sx * CW, y0, 0.0, sx * H, y1, KERB_Z)
            n += 1

    made = 0
    for bname in sorted(blocks):
        _, y0, _, y1 = blocks[bname]['env']
        for i, lot in enumerate(L.lots(bname)):
            key, lx0, lx1, _corner = lot
            h = HEIGHTS[i % len(HEIGHTS)]
            _box(eas, cube, mats['mass'], 'TC_Mass_%s' % key,
                 lx0 + 6.0, y0 + 6.0, 0.0, lx1 - 6.0, y1 - 6.0, h)
            made += 1

    # PROVISIONAL - see the module note. Deleted by the rig derivation.
    # unreal.Rotator is (ROLL, PITCH, YAW). Passing (-52, 45, 0) as if it
    # were (pitch, yaw, roll) aimed the only light 45 degrees UP and the
    # first capture came back pure black.
    sun = eas.spawn_actor_from_class(unreal.DirectionalLight,
                                     unreal.Vector(0, 0, 9000),
                                     unreal.Rotator(0.0, -52.0, 45.0))
    sun.set_actor_label('TC_PROVISIONAL_Sun')
    sky = eas.spawn_actor_from_class(unreal.SkyLight,
                                     unreal.Vector(0, 0, 9000),
                                     unreal.Rotator(0, 0, 0))
    sky.set_actor_label('TC_PROVISIONAL_Sky')

    print('BOARD x %.0f..%.0f y %.0f..%.0f' % (BX0, BX1, BY0, BY1))
    print('ROADS arterial + cross, carriageway half %.0f, kerb %.0f' % (CW, KERB_Z))
    print('MASSES %d placed across %d blocks' % (made, len(blocks)))
    print('LIGHTING PROVISIONAL - 2 actors, TC_PROVISIONAL_*, to be replaced')
    return made


build()
