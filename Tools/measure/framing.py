"""Put a lot in the frame, by solving for the standoff instead of guessing.

Camera placement has been the single biggest waste of time in this project. I
have put the camera inside a wall, behind the backdrop, under a lamp, in a
tree, and aimed past the edge of the board, and each one cost a capture cycle
to discover. The information needed to avoid all of that was already known: the
rig pins a 28.84 degree horizontal FOV (70 mm on a 36x24 back) and the live
viewport rectangle is 3:2, so the vertical FOV is 19.48 degrees.

frame() takes the box you want to see and the direction you want to see it
from, and returns the camera transform that just contains it. No iteration by
eye, no magic numbers.
"""
import math

FOV_H = 28.84
ASPECT = 1.5                       # live viewport 2313 x 1542
FOV_V = 2.0*math.degrees(math.atan(math.tan(math.radians(FOV_H/2.0))/ASPECT))


def _corners(rect, z0, z1):
    x0, y0, x1, y1 = rect
    return [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]


def frame(rect, bearing, pitch=-35.0, z0=0.0, z1=400.0, margin=1.12,
          aim=None):
    """Camera location and rotation that contains the box, seen from `bearing`.

    bearing  compass yaw the camera LOOKS ALONG, degrees
    pitch    downward angle, negative
    z0..z1   vertical extent of what must be visible
    margin   >1 leaves air around the subject
    aim      point to centre on; defaults to the box centre
    """
    x0, y0, x1, y1 = rect
    tgt = aim or ((x0 + x1)/2.0, (y0 + y1)/2.0, (z0 + z1)/2.0)
    yr, pr = math.radians(bearing), math.radians(pitch)
    # unit vector the camera looks along
    f = (math.cos(pr)*math.cos(yr), math.cos(pr)*math.sin(yr), math.sin(pr))
    # camera right and up, from the same yaw/pitch
    r = (-math.sin(yr), math.cos(yr), 0.0)
    u = (-math.sin(pr)*math.cos(yr), -math.sin(pr)*math.sin(yr), math.cos(pr))
    th = math.tan(math.radians(FOV_H/2.0))/margin
    tv = math.tan(math.radians(FOV_V/2.0))/margin

    def fits(d):
        cam = (tgt[0] - f[0]*d, tgt[1] - f[1]*d, tgt[2] - f[2]*d)
        for c in _corners(rect, z0, z1):
            v = (c[0] - cam[0], c[1] - cam[1], c[2] - cam[2])
            fwd = v[0]*f[0] + v[1]*f[1] + v[2]*f[2]
            if fwd <= 1.0:
                return False
            if abs(v[0]*r[0] + v[1]*r[1] + v[2]*r[2]) > th*fwd:
                return False
            if abs(v[0]*u[0] + v[1]*u[1] + v[2]*u[2]) > tv*fwd:
                return False
        return True

    lo, hi = 10.0, 200000.0
    if not fits(hi):
        raise ValueError('cannot frame %s from bearing %.0f' % (rect, bearing))
    for _ in range(60):                       # bisect to the nearest ~metre
        mid = (lo + hi)/2.0
        if fits(mid):
            hi = mid
        else:
            lo = mid
    d = hi
    cam = (tgt[0] - f[0]*d, tgt[1] - f[1]*d, tgt[2] - f[2]*d)
    return ({'x': round(cam[0], 1), 'y': round(cam[1], 1), 'z': round(cam[2], 1)},
            {'pitch': pitch, 'yaw': bearing, 'roll': 0.0})


def from_street(rect, side, pitch=-32.0, **kw):
    """Frame a lot from the street on one of its sides.

    side is 'S', 'N', 'W' or 'E' - the side of the lot the camera stands on.
    This is the call that stops a camera being placed inside the block it is
    trying to photograph, which has happened repeatedly.
    """
    bearing = {'S': 90.0, 'N': -90.0, 'W': 0.0, 'E': 180.0}[side]
    return frame(rect, bearing, pitch=pitch, **kw)


def blocked(cam, tgt, blockers, samples=140):
    """Does the sightline pass through anything on the way?

    frame() solves the FOV and nothing else, so it will happily stand the
    camera on the far side of three blocks and photograph their backs - which
    is exactly what it did for the walk-ups. A blocker is (rect, height).
    """
    for i in range(1, samples):
        t = i/float(samples)
        x = cam[0] + (tgt[0] - cam[0])*t
        y = cam[1] + (tgt[1] - cam[1])*t
        z = cam[2] + (tgt[2] - cam[2])*t
        for rect, h in blockers:
            if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3] and z < h:
                return True
    return False


def from_street_clear(rect, side, blockers, pitches=None, **kw):
    """Frame from the street, steepening the pitch until the view is clear.

    A shallow angle is the nicer picture, so try shallow first and only climb
    when something is in the way. Returns (loc, rot, pitch_used) and raises if
    nothing works, rather than silently handing back a photograph of a wall.
    """
    for p in (pitches or (-26.0, -32.0, -40.0, -48.0, -56.0, -64.0, -72.0, -82.0)):
        loc, rot = from_street(rect, side, pitch=p, **kw)
        cam = (loc['x'], loc['y'], loc['z'])
        tgt = ((rect[0] + rect[2])/2.0, (rect[1] + rect[3])/2.0,
               kw.get('z1', 400.0)/2.0)
        mine = [b for b in blockers if not (b[0][0] <= tgt[0] <= b[0][2]
                                            and b[0][1] <= tgt[1] <= b[0][3])]
        # test the CORNERS as well as the centre. Clearing only the centre
        # leaves a foreground block sitting across the bottom of the frame -
        # the sightline was clean and the picture was not.
        aims = [tgt] + [(x, y, tgt[2]) for x in (rect[0], rect[2])
                                        for y in (rect[1], rect[3])]
        if not any(blocked(cam, t, mine) for t in aims):
            return loc, rot, p
    raise ValueError('no clear pitch onto %s from %s' % (rect, side))


if __name__ == '__main__':
    # KNOWN ANSWER: a flat 1000 x 1000 square seen head-on from due south at
    # pitch 0. The binding corners are on the NEAR edge, not at the centre, so
    # the standoff is half-width/tan PLUS half-depth. The first version of this
    # assertion left the half-depth off and the solver was right.
    want = (1000.0/2.0)/(math.tan(math.radians(FOV_H/2.0))/1.12) + 500.0
    loc, rot = frame((0.0, 0.0, 1000.0, 1000.0), 90.0, pitch=0.0, z0=0.0, z1=0.0)
    got = 500.0 - loc['y']
    assert abs(got - want) < 3.0, (got, want)
    assert abs(loc['x'] - 500.0) < 0.5 and rot['yaw'] == 90.0
    # a TALLER subject must push the camera further back, not nearer
    near, _ = frame((0.0, 0.0, 1000.0, 1000.0), 90.0, pitch=0.0, z0=0.0, z1=0.0)
    far, _ = frame((0.0, 0.0, 1000.0, 1000.0), 90.0, pitch=0.0, z0=0.0, z1=2000.0)
    assert far['y'] < near['y'], (near['y'], far['y'])
    # from_street must stand OUTSIDE the lot on the named side
    loc, rot = from_street((0.0, 0.0, 1000.0, 1000.0), 'S', pitch=-30.0)
    assert loc['y'] < 0.0, loc
    assert loc['z'] > 0.0, loc
    loc, _ = from_street((0.0, 0.0, 1000.0, 1000.0), 'N', pitch=-30.0)
    assert loc['y'] > 1000.0, loc
    # KNOWN ANSWER for occlusion: a wall between camera and subject must be
    # seen at a shallow angle and cleared by a steep one.
    tgt_rect = (0.0, 0.0, 1000.0, 1000.0)
    # the wall must be BETWEEN camera and subject; the first version of this
    # test put it at y -3000, which is behind a camera that stands at ~ -2700,
    # so nothing was blocked and the assertion failed for the wrong reason
    wall = [((-2000.0, -1500.0, 3000.0, -1400.0), 1200.0)]
    lo, _ = from_street(tgt_rect, 'S', pitch=-26.0, z1=400.0)
    assert blocked((lo['x'], lo['y'], lo['z']), (500.0, 500.0, 200.0), wall)
    loc, rot, used = from_street_clear(tgt_rect, 'S', wall, z1=400.0)
    assert used < -26.0, used
    assert not blocked((loc['x'], loc['y'], loc['z']), (500.0, 500.0, 200.0), wall)
    print('framing.py self-check: pass  (FOV_H %.2f  FOV_V %.2f, cleared at %.0f)'
          % (FOV_H, FOV_V, used))
