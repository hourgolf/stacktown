#!/usr/bin/env python3
"""THE FIRST WOODEN BOARD: carved blocks at density, on an inlaid board.

    python3 Content/Python/wood_board.py

Everything before this proved materials on isolated objects. DIRECTION_B.md's
reference does not read the way it does because of one block - it reads that
way because of MANY blocks, packed tight, on a board with roads inlaid into
it, throwing shadows into narrow streets. This builds that.

FOUR THINGS, all owner-approved 2026-08-31:
  1. build_mass - carved forms, NOT flagship geometry with the windows off
  2. per-block grain rotation - "each building is its own chunk of wood"
  3. grain scale trimmed toward the reference (see TOOTH below)
  4. the board itself - base plate and inlaid roads, at density

PER-BLOCK GRAIN uses PaperRotate, which already exists and was built for
exactly this fault: "the grain is one world-space field, so every object
samples the SAME sheet at the SAME alignment... No two pieces of card a maker
cuts are like that" (paper_offset.py). It was written as an INSTRUMENT and
never used as the FIX. Here it is the fix.

Rotation is per MATERIAL INSTANCE, so this makes one MI per (species, angle)
actually used - at most 7 x 4. That is right for a demo board and WRONG for a
city: production drives PaperRotate from Custom Primitive Data so a thousand
blocks share seven materials. Recorded so the demo's shortcut cannot become
the architecture.

TOOTH. fabrication's 0.0005 targets 30-100 grain lines across a 1000 uu mass.
Counting rings on the reference's blocks gives more like 5-15, so the field
value is 3-10x too fine. This board uses 0.0025 - one tile per 400 uu, five
times coarser - as the trim the reference asks for. It is a LOOK value tested
here, not a change to the shipped table; fabrication is untouched until the
owner has judged this frame.

Staged at y=60000, removed afterwards with removal VERIFIED by search, level
asserted before every mutating step, TestCity never saved.
"""
import base64
import contextlib
import io
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import _path  # noqa: F401,E402
import genbuild  # noqa: E402
import ue  # noqa: E402

S = 'editor_toolset.toolsets.scene.SceneTools'
A = 'editor_toolset.toolsets.actor.ActorTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
MIT = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
APP = 'EditorToolset.EditorAppToolset'
LEVEL = '/Game/Maps/TestCity'
MATD = '/Game/Stacktown/Materials'
MASTER = '%s/M_StacktownMaster.M_StacktownMaster' % MATD
PROJECT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(PROJECT, 'Saved', 'DirectionB')

# INSIDE THE STUDIO ROOM. The first two boards were staged at y=+60000 -
# OUTSIDE CITY_Room entirely (x +/-37536, y +/-34116), so they were
# photographed against a black void. That is AGENTS.md's founding failure 5
# verbatim: "Everything was captured in a black void, which reads as a render.
# A model photographed in a lit room reads as a model." The room has been
# committed and rerunnable since 2026-08-30 and I staged past it for safety.
BASE_X = 21000.0
BASE_Y = 20000.0
# 0.0005: fabrication's SHIPPED timber value, restored. The 0.0025 override
# was made on a comment whose direction was backwards - the table's own
# measurements read 0.006 as sacking and 0.080 as nearly smooth, so a LOWER
# PaperTiling makes features BIGGER. 0.0025 was therefore five times FINER
# than shipped, not coarser, and measured on the ladder it carried a third of
# the surface detail. Owner's call, 2026-08-31.
TOOTH = 0.0005
ANGLES = (0.0, 90.0, 22.0, 68.0)   # four cuts from the stock
SPECIES = ('maple', 'pine', 'ash', 'oak', 'cherry', 'sapele', 'walnut')

# THE BOARD. CITY BLOCKS, not isolated lots (owner, 2026-09-01: "fix the
# plinths and party walls").
#
# The first boards gave every building its own lot with road on all four
# sides, so nothing ever touched anything and 35 individual plinths tiled the
# board like trays. A real city block is a GROUP of buildings that SHARE PARTY
# WALLS, sitting on one plot, with street only at the group's edge - which is
# also why the reference's gaps read as slots rather than margins.
#
# So: parcels butt inside a block, streets run only between blocks, and the
# plinth belongs to the BLOCK rather than to each building. That is one change
# fixing both notes, because they were the same fault seen twice.
PARCEL = 640.0          # one building footprint
BLK_W, BLK_D = 3, 2     # parcels per city block
ROAD = 260.0            # street, only between blocks
COLS, ROWS = 3, 3       # city blocks across the board
PLINTH_OVER = 26.0      # the block's shared plot, proud of its buildings


def _cap(h, rnd):
    """A rooftop cap, VARIED. Owner, 2026-09-01: "the tops are getting
    repetitive, the details matter here since the materials are simpler."

    Exactly right, and it is a property of this direction rather than an
    oversight: when a surface carries no windows, bands or reveals, the
    SILHOUETTE is doing all the work, and a repeated cap is therefore far more
    visible here than the same repetition would be on a flagship facade. At 20
    blocks one centred cap read as variety; at 35 it read as a stamp.

    Five outcomes rather than one, weighted so bare tops are common - a flat
    top IS the commonest thing on a carved block, and making every building
    wear a hat is its own kind of repetition.
    """
    if h < 900:
        return 0.0                      # low blocks stay bare
    r = rnd.random()
    if r < 0.34:
        return 0.0                      # bare, and deliberately the plurality
    if r < 0.62:
        return 70.0 + 60.0 * rnd.random()          # the small centred cap
    if r < 0.80:
        return 150.0 + 90.0 * rnd.random()         # a taller lift housing
    if r < 0.92:
        return 44.0 + 26.0 * rnd.random()          # a low broad plinth-cap
    return 240.0 + 140.0 * rnd.random()            # a rare slender mast block


def assert_level():
    lvl = json.loads(ue.tool(S, 'get_current_level', {}))['returnValue']
    assert lvl == LEVEL, 'level is %s - refusing' % lvl
    return lvl


def mi_for(species, angle_idx, cache):
    """One MI per (species, angle) actually used. Demo-scale; see docstring."""
    key = (species, angle_idx)
    if key in cache:
        return cache[key]
    name = 'MI_wood_%s_a%d' % (species, angle_idx)
    ref = {'refPath': '%s/%s.%s' % (MATD, name, name)}
    src = {'refPath': '%s/MI_wood_%s.MI_wood_%s' % (MATD, species, species)}
    # RERUNNABLE. create refuses to overwrite, and a second run of this script
    # is normal - the first board's angle instances are still on disk. They
    # are children of MI_wood_<species>, so a palette change on the PARENT
    # propagates and reusing them is not just tolerable, it is correct.
    try:
        ue.tool(MIT, 'create', {'folder_path': MATD, 'asset_name': name,
                                'parent': src})
    except Exception as e:
        if 'already exists' not in str(e):
            raise
    ue.tool(MIT, 'set_scalar_parameter',
            {'instance': ref, 'name': 'PaperRotate',
             'value': float(ANGLES[angle_idx])})
    ue.tool(MIT, 'set_scalar_parameter',
            {'instance': ref, 'name': 'PaperTiling', 'value': TOOTH})
    cache[key] = ref
    return ref


def main():
    print('level:', assert_level())
    rnd = random.Random(20260831)
    blk_w = BLK_W * PARCEL
    blk_d = BLK_D * PARCEL
    board_w = COLS * blk_w + (COLS + 1) * ROAD
    board_d = ROWS * blk_d + (ROWS + 1) * ROAD
    plan, plots = [], []
    for br in range(ROWS):
        for bc in range(COLS):
            bx = ROAD + bc * (blk_w + ROAD)
            by = ROAD + br * (blk_d + ROAD)
            plots.append((bx, by, blk_w, blk_d))
            dc = abs(bc - (COLS - 1) / 2.0) / max(1e-6, (COLS - 1) / 2.0)
            dr = abs(br - (ROWS - 1) / 2.0) / max(1e-6, (ROWS - 1) / 2.0)
            core = (1.0 - max(dc, dr)) ** 1.15
            for pr in range(BLK_D):
                for pc in range(BLK_W):
                    # PARCELS BUTT. No gap inside a block - adjacent buildings
                    # share a party wall, which is what makes a block read as
                    # a block instead of six objects near each other.
                    x = bx + pc * PARCEL
                    y = by + pr * PARCEL
                    lot = rnd.random()
                    spike = 1.0 if lot > 0.90 else (0.55 if lot > 0.72 else 0.0)
                    f = max(core, spike * (0.35 + 0.65 * core))
                    h = 260.0 + f * 6400.0 * (0.62 + 0.55 * rnd.random())
                    stages = ([(0.58, 0.0), (0.42, PARCEL * 0.11)] if h > 2600
                              else [(0.72, 0.0), (0.28, PARCEL * 0.09)]
                              if h > 1200 else [(1.0, 0.0)])
                    plan.append(dict(
                        x=x, y=y, w=PARCEL, d=PARCEL, h=h, stages=stages,
                        cap=_cap(h, rnd), sp=SPECIES[rnd.randrange(len(SPECIES))],
                        ang=rnd.randrange(len(ANGLES))))
    made = []
    genbuild.live()
    t0 = time.time()
    try:
        # the BOARD: base plate, then roads inlaid slightly proud of nothing -
        # flush, as an inlay is
        b = genbuild.mkactor('ZONE_BoardPlate', (BASE_X, BASE_Y, 0.0), (0, 0, 0))
        genbuild.box(b, 'Ground_Plate', -240.0, board_w + 240.0,
                     -240.0, board_d + 240.0, -60.0, 0.0)
        made.append('ZONE_BoardPlate')
        rd = genbuild.mkactor('ZONE_BoardRoads', (BASE_X, BASE_Y, 0.0), (0, 0, 0))
        # roads run on the BLOCK grid now, not the parcel grid - streets
        # exist between city blocks and nowhere inside them, which is what
        # party walls mean
        for c in range(COLS + 1):
            rx = c * (blk_w + ROAD)
            genbuild.box(rd, 'Kerbing_RoadV%d' % c, rx, rx + ROAD,
                         0.0, board_d, 0.0, 3.0)
        for r in range(ROWS + 1):
            ry = r * (blk_d + ROAD)
            genbuild.box(rd, 'Kerbing_RoadH%d' % r, 0.0, board_w,
                         ry, ry + ROAD, 0.0, 3.0)
        made.append('ZONE_BoardRoads')
        pl = genbuild.mkactor('ZONE_BoardPlots', (BASE_X, BASE_Y, 0.0), (0, 0, 0))
        for i, (px, py, pw, pd) in enumerate(plots):
            genbuild.box(pl, 'Ground_Plot%d' % i, px - PLINTH_OVER,
                         px + pw + PLINTH_OVER, py - PLINTH_OVER,
                         py + pd + PLINTH_OVER, 0.0, 24.0)
        made.append('ZONE_BoardPlots')
        print('board laid: %.0f x %.0f uu' % (board_w, board_d))

        for i, p in enumerate(plan):
            spec = dict(style='mass', name='B%02d' % i, x0=p['x'],
                        width=p['w'], depth=p['d'], height=p['h'],
                        stages=p['stages'], cap=p['cap'], seed=i,
                        plinth=0.0,
                        # D12: direction B is hand-laid; the flagship is not
                        hand_tolerance=True)
            with contextlib.redirect_stdout(io.StringIO()):
                genbuild.build(spec, origin=(BASE_X, BASE_Y + p['y'], 0.0), yaw=0.0)
            made.append('BLD2_B%02d_M' % i)
        print('%d blocks built in %.0fs' % (len(plan), time.time() - t0))
    finally:
        genbuild.live(False)

    # materials: board, roads, then every block in its own timber at its own
    # grain angle
    cache = {}
    def bind(actor_name, mat_ref):
        n = 0
        for a in json.loads(ue.tool(S, 'find_actors', {
                'name': actor_name, 'tag': '', 'collision_channels': []}))['returnValue']:
            for c in json.loads(ue.tool(A, 'get_components', {'actor': a}))['returnValue']:
                if 'StaticMeshComponent' in c.get('refPath', '') or \
                        c.get('refPath', '').rsplit('.', 1)[-1].startswith(
                            ('Wall_', 'Band_', 'Ground_', 'Kerbing_')):
                    ue.tool(OBJ, 'set_properties', {'instance': c, 'values': json.dumps(
                        {'overrideMaterials': [mat_ref]})})
                    n += 1
        return n

    bind('ZONE_BoardPlate', {'refPath': '%s/MI_model_board.MI_model_board' % MATD})
    bind('ZONE_BoardPlots', {'refPath': '%s/MI_board_road.MI_board_road' % MATD})
    # D11: the board's own stock. MI_dist_slate was DISTRICT PAINT borrowed
    # for being nearby, and it read as blue-grey plastic in frame.
    bind('ZONE_BoardRoads', {'refPath': '%s/MI_board_road.MI_board_road' % MATD})
    tb = time.time()
    for i, p in enumerate(plan):
        bind('BLD2_B%02d_M' % i, mi_for(p['sp'], p['ang'], cache))
    print('materials bound in %.0fs (%d timber MIs)' % (time.time() - tb, len(cache)))

    ann = {'gridSpacing': 0.0, 'gridExtent': 0.0, 'gridHeight': 0.0,
           'maxLabelDistance': 0.0, 'classFilter': None, 'maxLabels': 0}
    os.makedirs(OUT, exist_ok=True)
    cx, cy = BASE_X + board_w / 2.0, BASE_Y + board_d / 2.0
    for tag, cam in (
        ('BOARD_oblique',
         {'location': {'x': cx - board_w * 0.75, 'y': cy - board_d * 1.15,
                       'z': board_d * 0.85},
          'rotation': {'pitch': -26.0, 'yaw': 52.0, 'roll': 0.0},
          'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}),
        ('BOARD_street',
         {'location': {'x': cx - PARCEL * 1.6, 'y': cy - board_d * 0.52,
                       'z': 620.0},
          'rotation': {'pitch': -6.0, 'yaw': 74.0, 'roll': 0.0},
          'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}})):
        ue.tool(APP, 'SetCameraTransform', {'transform': cam})
        time.sleep(10)
        for i in range(3):
            r = json.loads(ue.tool(APP, 'CaptureViewport', {
                'captureTransform': cam, 'annotations': ann,
                'bShowUI': False}))['returnValue']
            open(os.path.join(OUT, '%s_%d.png' % (tag, i)), 'wb').write(
                base64.b64decode(r['image']['data']))
            time.sleep(1.6)
        print('captured', tag)

    if '--keep' in sys.argv:
        print('\n--keep: THE BOARD IS LEFT STANDING at (%.0f, %.0f) inside '
              'CITY_Room.' % (BASE_X, BASE_Y))
        print('TestCity is NOT saved - the board exists only in the open '
              'editor session and vanishes if the level is reloaded without '
              'saving. Re-run without --keep to remove it and verify clean.')
        return 0
    assert_level()
    for nm in made:
        for a in json.loads(ue.tool(S, 'find_actors', {
                'name': nm, 'tag': '', 'collision_channels': []}))['returnValue']:
            ue.tool(S, 'remove_from_scene', {'actor': a})
    left = json.loads(ue.tool(S, 'find_actors', {
        'name': 'BLD2_B', 'tag': '', 'collision_channels': []}))['returnValue']
    left += json.loads(ue.tool(S, 'find_actors', {
        'name': 'ZONE_Board', 'tag': '', 'collision_channels': []}))['returnValue']
    print('\nleft in level:', len(left))
    assert not left, 'cleanup incomplete'
    print('level clean; %s NOT saved' % LEVEL)
    return 0


if __name__ == '__main__':
    sys.exit(main())
