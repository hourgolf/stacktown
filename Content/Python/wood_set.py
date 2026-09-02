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

S, A, OBJ, MIT = wb.S, wb.A, wb.OBJ, wb.MIT
APP, MATD, LEVEL = wb.APP, wb.MATD, wb.LEVEL
OUT = wb.OUT

# THE LOOK-STUDY MASSES LIVE APART FROM THE SHIPPED CATALOGUE.
# /Game/Stacktown/BakedWood holds the 36 SM_WMass_* that the game's pointer
# resolves against - shipped content. These 20 are the density rig's own
# vocabulary: rebuilt whenever the board is rebuilt, disposable by design.
# They shared a folder until 2026-09-02 and were separable only by prefix,
# which is the situation folder-over-prefix was adopted to avoid: the first
# cleanup that deleted "the old wooden test assets" would have taken the
# catalogue with them.
BAKED = '/Game/Stacktown/LookStudy'

# THE TOWN IS BUILT FROM THE BAKE TABLE, not from a second hand-written list.
# The six-block version carried its own copy of the footprints, which is two
# places to change one fact - and the footprints ARE the bake's, so they are
# imported from it. mk_woodbake is the single authority on what exists.
import mk_woodbake as MW  # noqa: E402
import woodlayout as WL  # noqa: E402

# STREETS WIDE ENOUGH TO BE STREETS. 460 was chosen against a six-block huddle;
# at twenty, with towers, it is a slot again. 720 keeps the density the owner
# asked for - "tighter, but streets legible" - and lets the key reach a road.
# 720 -> 560, AND THE APRON WIDENED. Separating plot from street changed
# almost nothing visible, and the reason was the geometry, not the tones: the
# plot was proud by 26 uu, so nearly all of it sits under a building and the
# pale expanse in frame was STREET. B1's blocks nearly touch and its roads are
# narrow ribbons; 720 against a ~1600 block is a third of the board.
# STREET / PLOT_OVER / the angle set now live in woodlayout, which owns the
# arithmetic. They were duplicated here while the layout was local; a second
# copy of a number is how the two silently disagree, so the copies are gone
# and this file reads WL.STREET, WL.PLOT_OVER and WL.ANGLES.
# THE GRID IS AN ARGUMENT NOW, not a constant. Density was the last open
# point of the owner's reference comparison and it was gated on the editor,
# because the only way to see a denser board was to BUILD one. woodlayout
# makes the arithmetic headless and self-tested; this file only spawns what
# it is handed. Owner chose 12x9 - 108 blocks, 432 buildings - to see scale.
COLS, ROWS = 12, 9
PER_BLOCK = None        # None = varied block sizes from woodlayout
JAG = 0.35              # breaks the dome; 0 is a pure distance field
BEND = 0.6              # 0 = the straight grid; >0 curves the streets

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



# THE BOARD'S OWN STOCKS, DECLARED HERE so they are not orphans. D10 named
# the board stocks; their TONES were set live over MCP and lived only as
# editor state on the assets - the same fault as GrainGain, which fabrication
# now derives. Declared values, applied every run, are the fix.
#
# THE LADDER IS READ OFF B1. Roads are the BRIGHTEST thing in the reference,
# well above lit timber, which is what lets pale streets carry the eye across
# a board of warm blocks. The PLOT is not the street: block interiors in the
# reference sit under buildings and what shows between blocks is road. With
# one material for both, this board rendered as a single white apron with the
# blocks marooned in it. A plot a step darker and warmer than the street puts
# the ribbons back and gives each block a paved edge to sit on.
BOARD_STOCKS = {
    'MI_board_road':  (0.72, 0.75, 0.73),   # pale cool inlay, brightest
    'MI_board_plot':  (0.53, 0.50, 0.43),   # warm paved apron, a step down
    'MI_model_board': (0.40, 0.36, 0.28),   # the board itself, under both
}


def ensure_board_mis():
    """Create-or-reuse each board stock and force its declared tone."""
    for name, (r, g, b) in BOARD_STOCKS.items():
        ref = {'refPath': '%s/%s.%s' % (MATD, name, name)}
        try:
            ue.tool(MIT, 'create', {'folder_path': MATD, 'asset_name': name,
                                    'parent': {'refPath': '%s/M_StacktownMaster'
                                               '.M_StacktownMaster' % MATD}})
        except Exception as e:
            if 'already exists' not in str(e):
                raise
        ue.tool(MIT, 'set_vector_parameter',
                {'instance': ref, 'name': 'BaseColour',
                 'value': {'r': r, 'g': g, 'b': b, 'a': 1.0}})
    return len(BOARD_STOCKS)


def catalogue():
    """What mk_woodbake actually baked, as woodlayout wants it.

    The TIER comes from mk_woodbake._FORMS rather than being re-declared, so
    the bake table stays the single authority on what exists and a change to
    what is baked changes the town with no edit here.
    """
    tier_of, i = {}, 0
    for count, _rng, plan in MW._FORMS:
        for _ in range(count):
            tier_of['b%02d' % i] = plan
            i += 1
    return [('SM_Mass_%s' % n, sp, g['width'], g['depth'], tier_of[n])
            for n, sp, g in MW.SET]


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


def main():
    lvl = json.loads(ue.tool(S, 'get_current_level', {}))['returnValue']
    assert lvl == LEVEL, 'level is %s - refusing' % lvl
    cat = catalogue()
    L = WL.lay(cat, COLS, ROWS, PER_BLOCK, jag=JAG, bend=BEND)
    cw, rd = L['cw'], L['rd']
    town_w, town_d = L['town_w'], L['town_d']
    ox = AIM[0] - town_w / 2.0
    oy = AIM[1] - town_d / 2.0
    print('town %.0f x %.0f uu: %d blocks, %d buildings, %.0f uu streets'
          % (town_w, town_d, COLS * ROWS, len(L['placements']), WL.STREET))

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

    genbuild.live()
    try:
        g = genbuild.mkactor('ZONE_SetBGround', (ox, oy, 0.0), (0, 0, 0))
        # THE PLATE MUST COVER THE BENT CITY, not the straight one it was
        # sized for. The arc pushes whole columns thousands of uu in +y, and a
        # plate sized to town_d leaves the curve hanging over the edge - the
        # board equivalent of the black-void staging fault: correct geometry,
        # photographed off its own surface.
        _dys = [L['bend_at'](c)[0] for c in range(COLS)]
        _lo, _hi = min(_dys + [0.0]), max(_dys + [0.0])
        genbuild.box(g, 'Ground_Plate', -WL.PLATE_MARGIN, town_w + WL.PLATE_MARGIN,
                     _lo - WL.PLATE_MARGIN, town_d + _hi + WL.PLATE_MARGIN,
                     -60.0, 0.0)
        made.append('ZONE_SetBGround')
        rdz = genbuild.mkactor('ZONE_SetBRoad', (ox, oy, 0.0), (0, 0, 0))
        bend_at = L['bend_at']
        # NORTH-SOUTH STREETS run at a fixed column, so the bend displaces
        # them but does not curve them: one straight ribbon each, offset.
        for c in range(COLS + 1):
            x0 = sum(cw[:c]) + c * WL.STREET
            dy, _th = bend_at(min(c, COLS - 1))
            genbuild.box(rdz, 'Kerbing_RoadV%d' % c, x0, x0 + WL.STREET,
                         dy, town_d + dy, 0.0, 3.0)
        # EAST-WEST STREETS cross every column, so their centreline follows
        # the curve - and this is the roads study's prediction made real:
        # a curved street CANNOT be one ribbon, because the catalogue is five
        # fixed widths and frontage must stay quantized. So it is emitted as
        # STRAIGHT CHORDS, one per column, each square to its own stretch.
        # The gaps that open between chords on the outside of the curve are
        # the WEDGES the owner ruled are the look (D14 / roads section 3).
        for r in range(ROWS + 1):
            y0 = sum(rd[:r]) + r * WL.STREET
            for c in range(COLS):
                x0 = sum(cw[:c]) + c * WL.STREET
                x1 = sum(cw[:c + 1]) + (c + 1) * WL.STREET
                dy0, _ = bend_at(c)
                dy1, _ = bend_at(min(c + 1, COLS - 1))
                # each chord is square to itself; the curve lives in the STEP
                # between one chord and the next
                genbuild.box(rdz, 'Kerbing_RoadH%d_%d' % (r, c),
                             x0, x1, y0 + dy0, y0 + dy0 + WL.STREET, 0.0, 3.0)
        made.append('ZONE_SetBRoad')
        # PLOTS follow their block: one actor per block carrying the block's
        # own yaw, so a plot stays square to the buildings standing on it.
        for bi in range(COLS * ROWS):
            c, r = bi % COLS, bi // COLS
            bx = WL.STREET + sum(cw[:c]) + c * WL.STREET
            by = WL.STREET + sum(rd[:r]) + r * WL.STREET
            b_dy, b_th = bend_at(c)
            pa = genbuild.mkactor('ZONE_SetBPlots%03d' % bi,
                                  (ox + bx, oy + by + b_dy, 0.0),
                                  (0, math.degrees(b_th), 0))
            genbuild.box(pa, 'Ground_Plot%d' % bi,
                         -WL.PLOT_OVER, L['bw'][bi] + WL.PLOT_OVER,
                         -WL.PLOT_OVER, L['bd'][bi] + WL.PLOT_OVER, 0.0, 24.0)
            made.append('ZONE_SetBPlots%03d' % bi)
    finally:
        genbuild.live(False)
    print('ground laid: plate, %d streets, %d shared plots'
          % (COLS + ROWS + 2, COLS * ROWS))

    # TWO MCP CALLS PER BUILDING, NOT FOUR. At 432 placements the round trip
    # IS the build time - measured at 0.667 s, four calls each is 19 minutes
    # and two is under ten. Both savings were verified on a probe actor
    # rather than assumed:
    #   - add_to_scene_from_asset's `name` already sets the label, so the
    #     set_label call was redundant (find_actors sees it either way);
    #   - the mesh component path is derivable as <actor>.StaticMeshComponent0.
    # The derivation is PROVEN ONCE PER RUN against get_components and then
    # trusted, so a future asset with a differently-named component fails
    # loudly on the first building instead of silently binding nothing - the
    # exact fault this file already carries an assertion for.
    cache = {}
    placed = 0
    verified = False
    t0 = time.time()
    for p in L['placements']:
        r = json.loads(ue.tool(S, 'add_to_scene_from_asset', {
            'asset_path': '%s/%s' % (BAKED, p['asset']),
            'name': 'SETB_%03d' % placed,
            'xform': {'location': {'x': ox + p['x'], 'y': oy + p['y'],
                                   'z': 24.0},
                      'rotation': {'pitch': 0.0, 'yaw': p['yaw'],
                                   'roll': 0.0},
                      'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}}
            ))['returnValue']
        comp = {'refPath': r['refPath'] + '.StaticMeshComponent0'}
        if not verified:
            got = [c['refPath'] for c in json.loads(ue.tool(A, 'get_components', {
                'actor': r}))['returnValue']
                if 'StaticMeshComponent' in c.get('refPath', '')]
            assert got and got[0] == comp['refPath'], (
                'derived component path %r does not match the actor\'s real '
                'one %r - the fast path would bind nothing, silently'
                % (comp['refPath'], got[0] if got else None))
            verified = True
        ue.tool(OBJ, 'set_properties', {'instance': comp, 'values': json.dumps(
            {'overrideMaterials': [wb.mi_for(p['species'], p['angle'], cache)]})})
        placed += 1
        if placed % 100 == 0:
            print('  %d/%d placed (%.0fs)' % (placed, len(L['placements']),
                                              time.time() - t0))
    made.append('SETB_')
    print('%d baked masses placed in %.0fs, chamfered at %.0f uu'
          % (placed, time.time() - t0, MW.CHAMFER))

    ensure_board_mis()
    ground = 0
    for nm, ref in (('ZONE_SetBGround', 'MI_model_board'),
                    ('ZONE_SetBRoad', 'MI_board_road'),
                    ('ZONE_SetBPlots', 'MI_board_plot')):
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
        assert hit, ('%s bound 0 components to %s - the board would render as '
                     'the master default' % (nm, ref))
        ground += hit
    print('materials bound (%d timber MIs, %d ground components)'
          % (len(cache), ground))

    ann = {'gridSpacing': 0.0, 'gridExtent': 0.0, 'gridHeight': 0.0,
           'maxLabelDistance': 0.0, 'classFilter': None, 'maxLabels': 0}
    os.makedirs(OUT, exist_ok=True)
    cx_t = ox + town_w / 2.0
    cy_t = oy + town_d / 2.0
    # the middle north-south street, for the shot taken from inside the town
    st_x = ox + sum(cw[:1]) + 1 * WL.STREET + WL.STREET / 2.0
    # FOUR FRAMINGS, and the pair at the top is the owner's answer on scale:
    # "player should be able to zoom out to see most if not all of the
    # gameboard, but the main view would be closer in as you describe to sell
    # the scale." So SURVEY exists to prove the board is big, and OBLIQUE is
    # the view the game is actually played from - a crop, with city running
    # off the frame, which is what B1 is and why B1 reads as a city rather
    # than as a model of one.
    shots = (
        # SURVEY - the zoom-out. 23,000 uu of depth needs roughly 20,000 of
        # distance in a 58.5 deg vertical field, and the oblique needs more
        # again, so this is solved from the town size rather than guessed.
        ('SETB_survey', look_at(cx_t, cy_t, 1500.0,
                                max(town_w, town_d) * 1.25, -30.0, 38.0)),
        # OBLIQUE - the main view. Deliberately INSIDE the board's extent, so
        # the city leaves the frame on at least two sides.
        ('SETB_oblique', look_at(ox + town_w * 0.38, oy + town_d * 0.42,
                                 3400.0, 13000.0, -15.0, 38.0)),
        # STANDING IN A STREET, looking along it. The god's-eye of a whole
        # board is the one view a photographer of a physical model never
        # takes, and every frame before the set was that view.
        ('SETB_street', look_at(st_x, cy_t, 560.0, 4200.0, -3.0, 90.0)),
        # raking across the near frontages - the angle where a 14 uu arris
        # actually casts something and the chamfer can be judged
        ('SETB_raking', look_at(ox + town_w * 0.30, oy + town_d * 0.26,
                                1500.0, 8000.0, -7.0, 56.0)))
    # THE LADDER MUST SHOOT THIS EXACT FRAME. lighting_ab.py varies one
    # lighting variable and compares frames; if it re-derived the camera it
    # would be comparing two framings as well as two lights. Writing the
    # transform out means the study and the board cannot disagree about where
    # the camera was.
    json.dump(dict(shots)['SETB_oblique'],
              open(os.path.join(OUT, 'ab_camera.json'), 'w'), indent=1)

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
        print('\n--keep: THE SET IS STANDING at (%.0f, %.0f).' % (ox, oy))
        print('CLEAR IT BEFORE THE EDITOR SHUTS DOWN. TestCity is not saved '
              'by this script, but UE PROMPTS TO SAVE ON QUIT and on '
              '2026-09-01 that prompt persisted 23 rig actors into the map '
              'every lane loads. "Unsaved" is not a property of the rig, it '
              'is a property of nobody having clicked Save yet.')
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
