#!/usr/bin/env python3
"""THE BAKED SIX: direction B's look-judging set, close-framed.

    python3 Content/Python/wood_set.py            build, capture, clean up
    python3 Content/Python/wood_set.py --keep     leave it standing

WHY THIS EXISTS AND THE BOARD DOES NOT ANSWER IT.

wood_board.py builds 35 blocks through genbuild's LIVE sink, which lays every
mass with add_cube - a plain sharp box. The master's edge wear is a
normal-as-curvature proxy, saturate((1-max|n|)/0.30), and on an axis-aligned
face max|n| is exactly 1, so the term is 0.00 on every face of every building
on that board. Edge wear has been switched OFF in every frame the owner has
judged, and D3's patina rides on edge wear. The wear was never weak; it was
absent, and no amount of tuning the material would have shown it.

Chamfers exist only in BAKED geometry - fastbake reports "chamfered N" and
44 tris a part against a sharp box's 12. So the look-judging set is baked,
which is also what the owner approved via the coordinator: the disposable-rig
lock is amended for exactly this purpose.

SIX BLOCKS, NOT THIRTY-FIVE, and that is the second half of the fix. The
owner's standing verdict is "it looks like a render still... a long way to hit
our reference image target". The reference is a PHOTOGRAPH of a woodblock
model: few buildings, close framing, raking light, edges catching. A board
shot from above at 35 blocks answers density, which was last window's
question. This answers edges, light and tolerance, which is this one's.

WHAT IS DELIBERATELY NOT IN THIS FRAME. No wear or dirt layer - that is
hypothesis 3 and stays parked until the owner has judged chamfer plus light
plus hand tolerance on their own. Three variables in one frame is how a look
note becomes unattributable.

THE PLINTHS ARE GONE FROM THE BLOCKS AND BELONG TO THE PLOT. Owner's note on
the last board: 35 individual plinths "tiled the board like trays". The masses
are baked with plinth=0 and the two plots are laid here, shared, which is what
a city block means.

STAGED INSIDE CITY_Room under the approved soft key. The set is centred on the
point LIGHT_BoardKey actually aims at - derived below rather than eyeballed -
so it is raked rather than lit flat. TestCity is never saved.
"""
import base64
import contextlib
import io
import json
import math
import os
import sys
import time
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import _path  # noqa: F401,E402
import genbuild  # noqa: E402
import ue  # noqa: E402
import wood_board as wb  # noqa: E402   mi_for, ANGLES, TOOTH, constants

S, A, OBJ = wb.S, wb.A, wb.OBJ
APP, MATD, LEVEL = wb.APP, wb.MATD, wb.LEVEL
OUT = wb.OUT
BAKED = '/Game/Stacktown/BakedWood'

# THE TOWN IS BUILT FROM THE BAKE TABLE, not from a second hand-written list.
# The six-block version carried its own copy of the footprints, which is two
# places to change one fact - and the footprints ARE the bake's, so they are
# imported from it. mk_woodbake is the single authority on what exists.
import mk_woodbake as MW  # noqa: E402

# STREETS WIDE ENOUGH TO BE STREETS. 460 was chosen against a six-block huddle;
# at twenty, with towers, it is a slot again. 720 keeps the density the owner
# asked for - "tighter, but streets legible" - and lets the key reach a road.
STREET = 720.0
PLOT_OVER = 26.0
COLS, ROWS = 3, 2          # six city blocks; 20 buildings share them out

# WHERE THE KEY ACTUALLY POINTS. board_light puts the rect light at
# (BX+BW/2-2600, BY+BD/2-3400, 5200) with pitch -52 / yaw 58. Rather than
# staging at the board origin and hoping, the aim point on the ground plane is
# solved for here and the town is centred on it. A set lit down its own axis
# reads flat; this one is raked.
KX = wb.BASE_X + 6800.0 / 2.0 - 2600.0
KY = wb.BASE_Y + 4880.0 / 2.0 - 3400.0
KZ = 5200.0
_run = KZ / math.tan(math.radians(52.0))
AIM = (KX + _run * math.cos(math.radians(58.0)),
       KY + _run * math.sin(math.radians(58.0)))

# four cuts from the stock, so no two neighbours show the same face of the log
ANGLE_OF = (0, 2, 1, 3)


def _blocks():
    """Share the baked masses out into city blocks.

    A BLOCK IS A GROUP THAT SHARES PARTY WALLS, sitting on one plot, with
    street only at the group's edge. Six blocks of three or four buildings
    reads as a town; two butted rows of three read as one object, which is
    what the owner saw in the first set.
    """
    items = [(n, sp, g['width'], g['depth']) for n, sp, g in MW.SET]
    # CONTIGUOUS SLICES, AND THIS IS A REVERSAL WITH A REASON. The bake table
    # is ordered by form, so slicing it gives the first blocks every low
    # building and the last blocks every tower. That looked like a bug, so it
    # was changed to deal round-robin like cards - and the frame got WORSE.
    # Every block then held a tower, the spires clustered into one central
    # mound, and the town read as a pyramid instead of a settlement.
    #
    # Sliced, the same table gives a quarter of low buildings at one end and a
    # dense tall quarter at the other, which is what a city actually looks
    # like: a downtown and an edge. The ordering was doing useful work by
    # accident, and it is kept on purpose now. Judged by looking at both
    # frames, not by reasoning about the table.
    per = [len(items) // (COLS * ROWS)] * (COLS * ROWS)
    for i in range(len(items) - sum(per)):
        per[i] += 1
    out, k = [], 0
    for n in per:
        out.append(items[k:k + n])
        k += n
    return out


def look_at(tx, ty, tz, dist, pitch, yaw):
    """Camera transform that frames (tx,ty,tz) from `dist` away.

    The first pass hand-placed camera positions and every frame cut the tower
    off at the top - the subject is 6,660 uu tall and the offsets were guessed.
    Solving backwards from the point being looked at cannot make that mistake.
    """
    p, y = math.radians(pitch), math.radians(yaw)
    fx = math.cos(p) * math.cos(y)
    fy = math.cos(p) * math.sin(y)
    fz = math.sin(p)
    return {'location': {'x': tx - dist * fx, 'y': ty - dist * fy,
                         'z': tz - dist * fz},
            'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': 0.0},
            'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}


def _rows(blk):
    """Split a block into a FRONT and BACK row, backs together.

    A block laid as one row is a strip: its width is the sum of three or four
    buildings and its depth is one, so six of them tile a town 3:1 and the
    thing reads as a shelf rather than a settlement. Real blocks are built on
    both sides with the backs meeting in the middle, which is also what makes
    the street a street rather than a gap between two shelves.
    """
    half = (len(blk) + 1) // 2
    return blk[:half], blk[half:]


def _spans(blocks):
    """Per-block footprint, then the town's own extent."""
    bw = [max(sum(b[2] for b in f), sum(b[2] for b in k)) or 1.0
          for f, k in map(_rows, blocks)]
    bd = [(max([b[3] for b in f] or [0]) + max([b[3] for b in k] or [0]))
          for f, k in map(_rows, blocks)]
    cw = [max(bw[c::COLS]) for c in range(COLS)]      # column widths
    rd = [max(bd[r * COLS:(r + 1) * COLS]) for r in range(ROWS)]
    town_w = sum(cw) + STREET * (COLS + 1)
    town_d = sum(rd) + STREET * (ROWS + 1)
    return bw, bd, cw, rd, town_w, town_d


def main():
    lvl = json.loads(ue.tool(S, 'get_current_level', {}))['returnValue']
    assert lvl == LEVEL, 'level is %s - refusing' % lvl
    blocks = _blocks()
    bw, bd, cw, rd, town_w, town_d = _spans(blocks)
    ox = AIM[0] - town_w / 2.0
    oy = AIM[1] - town_d / 2.0
    print('town %.0f x %.0f uu: %d blocks, %d buildings, %.0f uu streets'
          % (town_w, town_d, len(blocks), sum(len(b) for b in blocks), STREET))

    # a light must be here or the whole point is lost - check, do not assume
    keys = json.loads(ue.tool(S, 'find_actors', {
        'name': 'LIGHT_BoardKey', 'tag': '',
        'collision_channels': []}))['returnValue']
    assert keys, ('LIGHT_BoardKey is not in the level - run '
                  'Content/Python/board_light.py first; this is a lighting '
                  'judgement and an unlit capture is worthless')

    made = []
    for stale in ('SETB_', 'ZONE_SetB'):
        for a in json.loads(ue.tool(S, 'find_actors', {
                'name': stale, 'tag': '',
                'collision_channels': []}))['returnValue']:
            ue.tool(S, 'remove_from_scene', {'actor': a})

    # block origins on the grid, streets between and around
    org = []
    for r in range(ROWS):
        by = STREET + sum(rd[:r]) + r * STREET
        for c in range(COLS):
            bx = STREET + sum(cw[:c]) + c * STREET
            org.append((bx, by))

    genbuild.live()
    try:
        g = genbuild.mkactor('ZONE_SetBGround', (ox, oy, 0.0), (0, 0, 0))
        genbuild.box(g, 'Ground_Plate', -300.0, town_w + 300.0,
                     -300.0, town_d + 300.0, -60.0, 0.0)
        made.append('ZONE_SetBGround')
        # ROADS ON THE BLOCK GRID. Streets exist between blocks and nowhere
        # inside them - that is what a party wall means, and it is why the
        # gaps read as streets rather than as margins around objects.
        rdz = genbuild.mkactor('ZONE_SetBRoad', (ox, oy, 0.0), (0, 0, 0))
        for c in range(COLS + 1):
            x0 = sum(cw[:c]) + c * STREET
            genbuild.box(rdz, 'Kerbing_RoadV%d' % c, x0, x0 + STREET,
                         0.0, town_d, 0.0, 3.0)
        for r in range(ROWS + 1):
            y0 = sum(rd[:r]) + r * STREET
            genbuild.box(rdz, 'Kerbing_RoadH%d' % r, 0.0, town_w,
                         y0, y0 + STREET, 0.0, 3.0)
        made.append('ZONE_SetBRoad')
        pl = genbuild.mkactor('ZONE_SetBPlots', (ox, oy, 0.0), (0, 0, 0))
        for i, (bx, by) in enumerate(org):
            genbuild.box(pl, 'Ground_Plot%d' % i, bx - PLOT_OVER,
                         bx + bw[i] + PLOT_OVER, by - PLOT_OVER,
                         by + bd[i] + PLOT_OVER, 0.0, 24.0)
        made.append('ZONE_SetBPlots')
    finally:
        genbuild.live(False)
    print('ground laid: plate, %d streets, %d shared plots'
          % (COLS + ROWS + 2, len(org)))

    placed = []
    for i, blk in enumerate(blocks):
        bx, by = org[i]
        front, back = _rows(blk)
        fd = max([b[3] for b in front] or [0])
        for row, y0, yaw in ((front, 0.0, 0.0), (back, fd, 180.0)):
            cx = 0.0
            for j, (name, sp, w, d) in enumerate(row):
                # buildings BUTT inside a row - party walls, no gap. The back
                # row is turned 180 so its FRONT faces the far street, which
                # is what puts a frontage on both sides of every road.
                label = 'SETB_%s' % name
                px = ox + bx + cx + (w if yaw else 0.0)
                py = oy + by + y0 + (d if yaw else 0.0)
                r = json.loads(ue.tool(S, 'add_to_scene_from_asset', {
                    'asset_path': '%s/SM_Mass_%s' % (BAKED, name),
                    'name': label,
                    'xform': {'location': {'x': px, 'y': py, 'z': 24.0},
                              'rotation': {'pitch': 0.0, 'yaw': yaw,
                                           'roll': 0.0},
                              'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}}
                    ))['returnValue']
                ue.tool(A, 'set_label', {'actor': r, 'label': label})
                placed.append((label, r, sp,
                               ANGLE_OF[(i + j) % len(ANGLE_OF)]))
                made.append(label)
                cx += w
    print('%d baked masses placed, chamfered at %.0f uu'
          % (len(placed), MW.CHAMFER))

    cache = {}
    for label, r, sp, ang in placed:
        mi = wb.mi_for(sp, ang, cache)
        n = 0
        for c in json.loads(ue.tool(A, 'get_components', {
                'actor': r}))['returnValue']:
            if 'StaticMeshComponent' in c.get('refPath', ''):
                ue.tool(OBJ, 'set_properties', {'instance': c, 'values':
                        json.dumps({'overrideMaterials': [mi]})})
                n += 1
        assert n, 'no mesh component bound on %s' % label
    # THE GROUND IS NOT A SPAWNED STATIC MESH ACTOR. Buildings are, so their
    # component's refPath contains "StaticMeshComponent" and the test above
    # works. The ground is built by genbuild, whose components are named for
    # their ROLE - Ground_Plate, Kerbing_RoadV0 - so that same test matched
    # nothing here and this loop did nothing at all, silently, for every run
    # since it was written. The board has never had a material: what looked
    # like a dark grey plate was the master's default.
    #
    # wood_board's bind() already knew this and tested the role prefixes; the
    # knowledge was there and did not travel. The assertion is the real fix -
    # a binding loop that can match zero components must say so.
    ground = 0
    for nm, ref in (('ZONE_SetBGround', 'MI_model_board'),
                    ('ZONE_SetBRoad', 'MI_board_road'),
                    ('ZONE_SetBPlots', 'MI_board_road')):
        hit = 0
        for a in json.loads(ue.tool(S, 'find_actors', {
                'name': nm, 'tag': '', 'collision_channels': []}))['returnValue']:
            for c in json.loads(ue.tool(A, 'get_components', {
                    'actor': a}))['returnValue']:
                leaf = c.get('refPath', '').rsplit('.', 1)[-1]
                if ('StaticMeshComponent' in c.get('refPath', '')
                        or leaf.startswith(('Ground_', 'Kerbing_'))):
                    ue.tool(OBJ, 'set_properties', {'instance': c, 'values':
                            json.dumps({'overrideMaterials': [
                                {'refPath': '%s/%s.%s' % (MATD, ref, ref)}]})})
                    hit += 1
        assert hit, ('%s bound 0 components to %s - the board would render '
                     'as the master default and the road value, which is the '
                     'whole point of this pass, would be silently absent'
                     % (nm, ref))
        ground += hit
    print('materials bound (%d timber MIs, %d ground components)'
          % (len(cache), ground))

    ann = {'gridSpacing': 0.0, 'gridExtent': 0.0, 'gridHeight': 0.0,
           'maxLabelDistance': 0.0, 'classFilter': None, 'maxLabels': 0}
    os.makedirs(OUT, exist_ok=True)
    cx_t = ox + town_w / 2.0
    cy_t = oy + town_d / 2.0
    # the middle north-south street, for the shot taken from inside the town
    st_x = ox + sum(cw[:1]) + 1 * STREET + STREET / 2.0
    shots = (
        # the whole town. Aimed at mid-height rather than at the board, so the
        # tallest block stays inside the vertical field instead of clipping.
        ('SETB_oblique', look_at(cx_t, cy_t, 3200.0, 15000.0, -14.0, 38.0)),
        # STANDING IN A STREET, looking along it. The god's-eye of a whole
        # board is the one view a photographer of a physical model never
        # takes, and every frame before the set was that view.
        ('SETB_street', look_at(st_x, cy_t, 560.0, 4200.0, -3.0, 90.0)),
        # raking across the near frontages - the angle where a 14 uu arris
        # actually casts something and the chamfer can be judged
        ('SETB_raking', look_at(cx_t, oy + town_d * 0.30, 1500.0,
                                8000.0, -7.0, 56.0)))
    for tag, cam in shots:
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
        print('\n--keep: THE SET IS STANDING at (%.0f, %.0f). TestCity is NOT '
              'saved and it vanishes on reload.' % (ox, oy))
        return 0
    for nm in made:
        for a in json.loads(ue.tool(S, 'find_actors', {
                'name': nm, 'tag': '',
                'collision_channels': []}))['returnValue']:
            ue.tool(S, 'remove_from_scene', {'actor': a})
    left = json.loads(ue.tool(S, 'find_actors', {
        'name': 'SETB_', 'tag': '', 'collision_channels': []}))['returnValue']
    left += json.loads(ue.tool(S, 'find_actors', {
        'name': 'ZONE_SetB', 'tag': '',
        'collision_channels': []}))['returnValue']
    assert not left, 'cleanup incomplete: %d left' % len(left)
    print('level clean; %s NOT saved' % LEVEL)
    return 0


if __name__ == '__main__':
    sys.exit(main())
