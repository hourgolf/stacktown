"""Place the test city's roads and placeholder masses into TestCity.

RUN THROUGH rung.sh - it mutates. Idempotent: every actor it owns is
destroyed and rebuilt, so running it twice leaves one city, not two.

GEOMETRY COMES FROM citylayout, WHICH IS SELF-TESTED. Nothing here invents a
coordinate. If a number in this file disagrees with the layout module, the
layout module is right and this file is the bug - the same relationship
genbuild has with recipes.

THIS FILE PLACES NO LIGHTS. It once carried a provisional sun and sky so the
bare layout could be looked at; citylight.py owns the rig now, and leaving
them here meant a second DirectionalLight every time placement re-ran.
"""
import unreal
import citylayout as L

CUBE = '/Engine/BasicShapes/Cube.Cube'
# MI_model_board is tan card. It is a defensible look for a model board,
# but it is NOT what the sandbox street stands on - that is STAGE_Ground
# in MI_studio_grey - and it drove the oblique's warm cast to R-B +26.1
# against the sandbox board frame's +8.4. Neutral ground, measured.
M_BOARD = '/Game/Stacktown/Materials/MI_studio_grey.MI_studio_grey'
# step_stage2.py built the hero block's streets and is the precedent:
#   carriageway MI_studio_grey, footway MI_concrete, kerb MI_paint_cream.
# This file used MI_gravel for the carriageway - avkit's SM_rock_01
# material, a scatter prop. The owner saw it as 'gravel roads instead of
# asphalt' and was right; it was never a road surface.
M_ROAD = '/Game/Stacktown/Materials/MI_studio_grey.MI_studio_grey'
M_KERB = '/Game/Stacktown/Materials/MI_paint_cream.MI_paint_cream'
M_WALK = '/Game/Stacktown/Materials/MI_concrete.MI_concrete'
M_MASS = '/Game/Stacktown/Materials/MI_precast_grey.MI_precast_grey'

OWNED = ('TC_Board', 'TC_Road', 'TC_Walk', 'TC_Kerb', 'TC_Mass',
         'TC_PROVISIONAL')

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
            (('board', M_BOARD), ('road', M_ROAD), ('kerb', M_KERB),
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

    # KERBS. step_stage2 places a 14 uu kerb between footway and carriageway
    # and this file had none at all - the footway just fell to the road.
    KERB_W = 14.0
    k = 0
    for sy in (-1, 1):
        for x0, x1 in ((BX0, -H), (H, BX1)):
            _box(eas, cube, mats['kerb'], 'TC_Kerb_A%d' % k,
                 x0, sy * CW, 0.0, x1, sy * (CW + KERB_W), KERB_Z)
            k += 1
    for sx in (-1, 1):
        for y0, y1 in ((BY0, -H), (H, BY1)):
            _box(eas, cube, mats['kerb'], 'TC_Kerb_C%d' % k,
                 sx * CW, y0, 0.0, sx * (CW + KERB_W), y1, KERB_Z)
            k += 1

    made = 0
    for bname in sorted(blocks):
        _, y0, _, y1 = blocks[bname]['env']
        for i, lot in enumerate(L.lots(bname)):
            key, lx0, lx1, _corner = lot
            h = HEIGHTS[i % len(HEIGHTS)]
            _box(eas, cube, mats['mass'], 'TC_Mass_%s' % key,
                 lx0 + 6.0, y0 + 6.0, 0.0, lx1 - 6.0, y1 - 6.0, h)
            made += 1

    # NO LIGHTS HERE. This file used to spawn a provisional sun and sky so
    # the bare layout could be looked at. citylight.py now owns the rig, and
    # re-running placement after it put a SECOND DirectionalLight in the
    # level - the editor said so on screen, burned into a capture:
    # "Multiple directional lights are competing to be the single one used
    # for forward shading". One file owns lighting.

    print('BOARD x %.0f..%.0f y %.0f..%.0f' % (BX0, BX1, BY0, BY1))
    print('ROADS arterial + cross, carriageway half %.0f, %d kerbs' % (CW, k))
    print('MASSES %d placed across %d blocks' % (made, len(blocks)))
    return made


build()
