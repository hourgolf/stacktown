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

# the six, in the two rows they stand in. (block, species, angle, width, depth)
# widths and depths are the baked footprints; see mk_woodbake.SET
ROW_A = [('shed', 'maple', 0, 640.0, 620.0),
         ('low', 'ash', 2, 900.0, 760.0),
         ('midrise', 'oak', 1, 820.0, 800.0)]
ROW_B = [('setback', 'cherry', 3, 880.0, 840.0),
         ('ziggurat', 'sapele', 1, 980.0, 940.0),
         ('tower', 'walnut', 2, 720.0, 700.0)]
# THE STREET HAS TO BE WIDE ENOUGH TO BE A STREET. The first pass used 260,
# carried over from the board where it separated 3x2 blocks of low massing.
# Against a 6,660 uu tower that is a 1:25 slot, not a street: no key at any
# angle reaches its floor, and the owner's own choice was "tighter but streets
# LEGIBLE". 460 keeps it tight and lets light down it.
STREET = 460.0
PLOT_OVER = 26.0

# WHERE THE KEY ACTUALLY POINTS. board_light puts the rect light at
# (BX+BW/2-2600, BY+BD/2-3400, 5200) with pitch -52 / yaw 58. Rather than
# staging the set at the board origin and hoping, the aim point on the ground
# plane is solved for here, and the set is centred on it. A set lit down its
# own axis reads flat; this one is raked.
KX = wb.BASE_X + 6800.0 / 2.0 - 2600.0
KY = wb.BASE_Y + 4880.0 / 2.0 - 3400.0
KZ = 5200.0
_run = KZ / math.tan(math.radians(52.0))
AIM = (KX + _run * math.cos(math.radians(58.0)),
       KY + _run * math.sin(math.radians(58.0)))


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


def _spans():
    """Local extents of the set: x across both rows, y front-to-back."""
    wa = sum(b[3] for b in ROW_A)
    wbw = sum(b[3] for b in ROW_B)
    da = max(b[4] for b in ROW_A)
    db = max(b[4] for b in ROW_B)
    return max(wa, wbw), da, db


def main():
    lvl = json.loads(ue.tool(S, 'get_current_level', {}))['returnValue']
    assert lvl == LEVEL, 'level is %s - refusing' % lvl
    width, depth_a, depth_b = _spans()
    # local frame: row A fronts on y=0 and runs back to -depth_a; the street
    # is y 0..STREET; row B fronts on y=STREET and runs to +depth_b
    y_lo, y_hi = -depth_a, STREET + depth_b
    ox = AIM[0] - width / 2.0
    oy = AIM[1] - (y_lo + y_hi) / 2.0
    print('set %.0f x %.0f uu, centred on the key aim point (%.0f, %.0f)'
          % (width, y_hi - y_lo, AIM[0], AIM[1]))

    # a light must be here or the whole point is lost - check, do not assume
    keys = json.loads(ue.tool(S, 'find_actors', {
        'name': 'LIGHT_BoardKey', 'tag': '',
        'collision_channels': []}))['returnValue']
    assert keys, ('LIGHT_BoardKey is not in the level - run '
                  'Content/Python/board_light.py first; this set is a '
                  'lighting judgement and an unlit capture is worthless')

    made = []
    for stale in ('SETB_', 'ZONE_SetB'):
        for a in json.loads(ue.tool(S, 'find_actors', {
                'name': stale, 'tag': '',
                'collision_channels': []}))['returnValue']:
            ue.tool(S, 'remove_from_scene', {'actor': a})

    genbuild.live()
    try:
        g = genbuild.mkactor('ZONE_SetBGround', (ox, oy, 0.0), (0, 0, 0))
        genbuild.box(g, 'Ground_Plate', -420.0, width + 420.0,
                     y_lo - 420.0, y_hi + 420.0, -60.0, 0.0)
        made.append('ZONE_SetBGround')
        rd = genbuild.mkactor('ZONE_SetBRoad', (ox, oy, 0.0), (0, 0, 0))
        genbuild.box(rd, 'Kerbing_Street', -420.0, width + 420.0,
                     0.0, STREET, 0.0, 3.0)
        made.append('ZONE_SetBRoad')
        pl = genbuild.mkactor('ZONE_SetBPlots', (ox, oy, 0.0), (0, 0, 0))
        wa = sum(b[3] for b in ROW_A)
        wbw = sum(b[3] for b in ROW_B)
        # ONE plot per row, not one per building
        genbuild.box(pl, 'Ground_PlotA', -PLOT_OVER, wa + PLOT_OVER,
                     y_lo - PLOT_OVER, PLOT_OVER, 0.0, 24.0)
        genbuild.box(pl, 'Ground_PlotB', -PLOT_OVER, wbw + PLOT_OVER,
                     STREET - PLOT_OVER, y_hi + PLOT_OVER, 0.0, 24.0)
        made.append('ZONE_SetBPlots')
    finally:
        genbuild.live(False)
    print('ground laid: plate, one street, two shared plots')

    placed = []
    for row, front, back in ((ROW_A, 0.0, True), (ROW_B, STREET, False)):
        cx = 0.0
        for name, sp, ang, w, d in row:
            # buildings BUTT - party walls, no gap inside a row
            y = front - d if back else front
            label = 'SETB_%s' % name
            r = json.loads(ue.tool(S, 'add_to_scene_from_asset', {
                'asset_path': '%s/SM_Mass_%s' % (BAKED, name),
                'name': label,
                'xform': {'location': {'x': ox + cx, 'y': oy + y, 'z': 24.0},
                          'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0},
                          'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}}
                ))['returnValue']
            ue.tool(A, 'set_label', {'actor': r, 'label': label})
            placed.append((label, r, sp, ang))
            made.append(label)
            cx += w
    print('%d baked masses placed (chamfered geometry, not add_cube)'
          % len(placed))

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
    for nm, ref in (('ZONE_SetBGround', 'MI_model_board'),
                    ('ZONE_SetBRoad', 'MI_board_road'),
                    ('ZONE_SetBPlots', 'MI_board_road')):
        for a in json.loads(ue.tool(S, 'find_actors', {
                'name': nm, 'tag': '', 'collision_channels': []}))['returnValue']:
            for c in json.loads(ue.tool(A, 'get_components', {
                    'actor': a}))['returnValue']:
                if 'StaticMeshComponent' in c.get('refPath', ''):
                    ue.tool(OBJ, 'set_properties', {'instance': c, 'values':
                            json.dumps({'overrideMaterials': [
                                {'refPath': '%s/%s.%s' % (MATD, ref, ref)}]})})
    print('materials bound (%d timber MIs)' % len(cache))

    ann = {'gridSpacing': 0.0, 'gridExtent': 0.0, 'gridHeight': 0.0,
           'maxLabelDistance': 0.0, 'classFilter': None, 'maxLabels': 0}
    os.makedirs(OUT, exist_ok=True)
    mid_x = ox + width / 2.0
    st_y = oy + STREET / 2.0
    # THREE FRAMINGS, and the two low ones are the point. The owner's "render
    # still" note is partly a FRAMING fact: every previous capture was a
    # god's-eye of the whole board, which is the one view a photographer of a
    # physical model never takes.
    shots = (
        # the whole set, tower included. 9,000 uu back at -17 deg puts the
        # 6,660 tower inside a 58.5 deg vertical field with headroom
        # AIM AT MID-HEIGHT, NOT AT THE BOARD. Targeting z=1900 at -17 deg put
        # the tower's top 45 deg off the view axis against a 29.25 deg half-
        # field, so it clipped. Solved: the top sits 16.6 deg above a target at
        # 3,400 from 11,000 back, and 8 deg of pitch keeps it inside.
        ('SETB_oblique', look_at(mid_x, oy + (y_lo + y_hi) / 2.0, 3400.0,
                                 11000.0, -8.0, 38.0)),
        # IN the street, not at the end of it, and at a height a person would
        # stand rather than a height a camera floats at
        ('SETB_street', look_at(ox + width * 0.72, st_y, 520.0,
                                3000.0, -5.0, 4.0)),
        # across the fronts, the shot that answers the chamfer question -
        # a raking angle is the only one where a 6 uu bevel casts anything
        ('SETB_raking', look_at(ox + width * 0.45, oy - depth_a * 0.35, 2900.0,
                                7000.0, -6.0, 58.0)))
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
