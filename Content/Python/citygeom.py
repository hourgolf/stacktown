"""World rectangles derived from the city table.

Pure functions over `city.py` - no Unreal import, so they can be exercised from
plain Python and self-tested without an editor. Every rule that needs to ask
"is this thing on the road / in the junction / inside its lot" asks here, so
there is one transform rather than one per script that disagrees at the edges.
"""
import math
import _path
from city import BLOCKS, STREETS, AVENUES, BOARD_S, BOARD_E

CAR_HALF = 270.0          # half a car length; the junction keep-clear margin

Rect = tuple               # (x0, y0, x1, y1), x0<x1 and y0<y1


def norm(x0, y0, x1, y1):
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def board_rect():
    return norm(-300.0, BOARD_S, BOARD_E, 900.0)


def street_road_rects():
    """The carriageway of each east-west street: full board width."""
    bx0, _, bx1, _ = board_rect()
    return [norm(bx0, y_far + w, bx1, y_near - w) for y_far, y_near, w in STREETS]


def avenue_road_rects():
    """The carriageway of each north-south avenue: full board depth."""
    _, by0, _, by1 = board_rect()
    return [norm(x_w + w, by0, x_e - w, by1) for x_w, x_e, w in AVENUES]


def road_rects():
    return street_road_rects() + avenue_road_rects()


def junction_rects():
    """Where a street carriageway crosses an avenue carriageway, grown by half
    a car length so a vehicle parked just short of it still cannot overhang the
    crossing bars."""
    out = []
    for s in street_road_rects():
        for a in avenue_road_rects():
            r = intersect(s, a)
            if r:
                out.append(norm(r[0] - CAR_HALF, r[1] - CAR_HALF,
                                r[2] + CAR_HALF, r[3] + CAR_HALF))
    return out


def lot_rect(blk, spec):
    """World rectangle of one lot, through its block's origin and yaw."""
    ox, oy, _ = blk['origin']
    yaw = math.radians(blk['yaw'])
    c, s = math.cos(yaw), math.sin(yaw)
    xs, ys = [], []
    for lx in (spec['x0'], spec['x0'] + spec['width']):
        for ly in (0.0, spec['depth']):
            xs.append(ox + lx*c - ly*s)
            ys.append(oy + lx*s + ly*c)
    return norm(min(xs), min(ys), max(xs), max(ys))


def lots(kinds=None):
    """[(block name, lot spec, world rect)] over the whole table."""
    out = []
    for blk in BLOCKS:
        for spec in blk['lots']:
            if kinds is None or spec.get('kind') in kinds:
                out.append((blk['name'], spec, lot_rect(blk, spec)))
    return out


# --- rectangle algebra ------------------------------------------------------
def intersect(p, q):
    x0, y0 = max(p[0], q[0]), max(p[1], q[1])
    x1, y1 = min(p[2], q[2]), min(p[3], q[3])
    return (x0, y0, x1, y1) if x1 > x0 and y1 > y0 else None


def contains(outer, inner):
    return (inner[0] >= outer[0] and inner[1] >= outer[1] and
            inner[2] <= outer[2] and inner[3] <= outer[3])


def overhang(outer, inner):
    """How far `inner` sticks out past `outer`, worst side. 0 when contained."""
    return max(0.0, outer[0] - inner[0], outer[1] - inner[1],
                    inner[2] - outer[2], inner[3] - outer[3])
