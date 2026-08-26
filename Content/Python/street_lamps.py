"""Street lamps, generated rather than acquired.

The canyons were dark because a night street has lamps and this one had none.
That is the one asset gap worth naming - and it is not worth buying. A card
model's lamp column is a pole, an arm and a head: four boxes. A donor lamp
arrives with its own detail tier, its own materials and its own idea of how
much surface a 6 m pole should have, all of which have to be fought back to the
diorama. Every complete donor building tried in this project has been unusable
for exactly that reason; the Assetsville TILESET works because its parts are
modular and its names carry role.

So this generates them, with role-prefix component names like everything else.
Geometry only - lamp_lights.py hangs the light on each one, because a light is
an actor and this runs over MCP where the boxes do.
"""
import _path  # noqa: F401
import ue, json, math, random
from genbuild import mkactor, box
from city import STREETS, AVENUES, BOARD_E, BOARD_S, BOARD_N
import citygeom as G

S = 'editor_toolset.toolsets.scene.SceneTools'
A = 'editor_toolset.toolsets.actor.ActorTools'

POLE = 26.0          # 260 mm square section
HEIGHT = 780.0       # 7.8 m to the arm
ARM = 210.0
SPACING = 1450.0


def wipe():
    # NOTE: this MCP path silently returns nothing in practice - see
    # wipe_lamps.py, which is what the pipeline actually calls. Kept only so a
    # standalone run is not completely unguarded.
    try:
        acts = json.loads(ue.tool(S, 'get_all_level_actors', {}))['returnValue']
    except Exception:
        return 0
    n = 0
    for ref in acts:
        try:
            lbl = json.loads(ue.tool(A, 'get_label', {'actor': ref}))['returnValue']
        except Exception:
            continue
        if str(lbl).startswith('LAMP_'):
            ue.tool(S, 'destroy_actor', {'actor': ref}); n += 1
    return n


def lamp(label, x, y, reach, yaw=0.0):
    """reach: +1 or -1, which way along LOCAL Y the arm leans over the road.

    yaw turns the whole lamp: streets run along X so their arms lean along
    world Y with yaw 0; avenues run along Y, so their arms need yaw -90 to
    lean along world X. Before the yaw existed every avenue arm ran parallel
    to its own kerb."""
    a = mkactor(label, (x, y, 0.0), (0.0, yaw, 0.0))
    h = POLE/2.0
    box(a, 'Frame_Base',   -h-8, h+8, -h-8, h+8, 0, 34)
    box(a, 'Frame_Column', -h,   h,   -h,   h,   34, HEIGHT)
    y0, y1 = (0, ARM) if reach > 0 else (-ARM, 0)
    box(a, 'Frame_Arm',    -9,   9,   y0,   y1,  HEIGHT - 22, HEIGHT)
    ty = ARM*reach
    box(a, 'Frame_Head',   -26,  26,  ty - 34*abs(reach) if reach > 0 else ty,
        ty + 34 if reach > 0 else ty + 34*abs(reach), HEIGHT - 52, HEIGHT - 20)
    return 4


POLE_HALF = 20.0


def clear_of(rects, x, y):
    """A lamp line runs the full width of the board, so a street's pavement
    line crosses every avenue and an avenue's crosses every street. Six lamps
    each way were standing in the middle of a carriageway at a junction -
    "lightposts in the middle of the roads". Reads the same rectangles that
    invariant DRESS-03 checks, so the placement and the check cannot drift."""
    pole = (x - POLE_HALF, y - POLE_HALF, x + POLE_HALF, y + POLE_HALF)
    return not any(G.intersect(r, pole) for r in rects)


def run():
    # The MCP wipe above silently no-ops when the enumeration call returns
    # something unparseable, and the failure is swallowed - it once left 96
    # lamps where 48 were wanted, and did it again here (42 + 46 = 88). Go
    # through rung.sh, which runs locally, and refuse to build on failure.
    import os, subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    rung = os.path.join(os.path.dirname(os.path.dirname(here)), 'Tools', 'rung.sh')
    r = subprocess.run([rung, 'wipe_lamps.py'], capture_output=True, text=True, cwd=here)
    if 'success: True' not in r.stdout:
        raise SystemExit('wipe_lamps.py FAILED - refusing to build on top of '
                         'the old set\n' + (r.stdout[-400:] or r.stderr[-400:]))
    print('  ' + next((l[7:] for l in r.stdout.splitlines() if 'removed' in l),
                      'wipe reported nothing'))
    rnd = random.Random(31337)
    X0, X1 = -300.0, BOARD_E
    n = 0
    for si, (y_far, y_near, walk) in enumerate(STREETS, 1):
        k_far, k_near = y_far + walk, y_near - walk
        # The ROAD is between k_far and k_near, so the pavement is OUTSIDE
        # that span: k_far - 62 and k_near + 62. Adding on both sides put every
        # far-side lamp 62 uu INTO the carriageway, where the cars park - which
        # is why lamp columns were clipping through parked vehicles. The arm
        # then has to reach back toward the road, so the sign flips too.
        for side, ly, reach in (('F', k_far - 62.0, +1), ('N', k_near + 62.0, -1)):
            x = X0 + 900.0 + (si % 2)*SPACING*0.5
            crossing = G.avenue_road_rects()
            while x < X1 - 400.0:
                if clear_of(crossing, x, ly):
                    n += lamp('LAMP_s%d%s_%d' % (si, side, n), x, ly, reach) and 1
                x += SPACING
    for ai, (x_w, x_e, walk) in enumerate(AVENUES, 1):
        k_w, k_e = x_w + walk, x_e - walk
        # W pole west of the road, arm reaches +X over it; E pole mirrored.
        # yaw -90 maps the arm's local +Y onto world +X.
        for side, lx, reach in (('W', k_w - 62.0, +1), ('E', k_e + 62.0, -1)):
            y = BOARD_S + 900.0
            crossing = G.street_road_rects()
            # was `while y < 700.0` - the old board top. The board has grown
            # north twice since; derive the cap like everything else.
            while y < BOARD_N - 400.0:
                if clear_of(crossing, lx, y):
                    n += lamp('LAMP_a%d%s_%d' % (ai, side, n), lx, y, reach,
                              yaw=-90.0) and 1
                y += SPACING
    print('street lamps: %d' % n)
    return n


if __name__ == '__main__':
    run()
