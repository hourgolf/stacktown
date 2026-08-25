"""Lots that are not buildings.

THE PRIMITIVE CHANGED. city.py said a block is a list of lots and a lot has
floors, bays and a parapet. A plaza has none of those. So `kind` now dispatches
the way `style` already dispatches within kind='gen':

    gen     a building        -> genbuild.build, which then dispatches on style
    av      the tileset lot   -> step_av.py
    plaza   paved public open space
    park    planted open space
    vacant  a cleared site

Everything here emits ZONE_ actors with the same role-prefix component names as
buildings, so the one role sweep binds them and adding a zone costs nothing in
material work - the property HANDOFF.md 4.2 calls the most important scaling
behaviour in the codebase.

Block-local coordinates throughout; the block transform rides on the actor,
exactly as genbuild does it.
"""
import _path  # noqa: F401
import ue, json, math, random
from genbuild import mkactor, box
from zonelayout import plaza_layout, park_layout, layout  # noqa: F401

FRONT = 62.0          # the line a building's facade would have stood on



def build(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    k = spec.get('kind')
    if k == 'plaza':
        return plaza(spec, origin, yaw)
    if k == 'park':
        return park(spec, origin, yaw)
    if k == 'vacant':
        return vacant(spec, origin, yaw)
    raise SystemExit('zones.build: unknown kind %r' % k)


def _surround(a, spec, made, deck_z, surface='Ground_'):
    """Kerbed edge and steps down to the pavement. Shared by every open zone -
    an open lot still has to meet the street the way its neighbours do, or it
    reads as a hole in the block rather than a space in it."""
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    box(a, 'Ground_Deck', x0 + 6, x0 + W - 6, FRONT + 6, D - 6, 0, deck_z); made += 1
    box(a, 'Kerbing_Edge', x0, x0 + W, FRONT, D, deck_z - 6, deck_z + 4); made += 1
    # three steps down to the footway on the street side
    for i in range(3):
        z = deck_z * (2 - i) / 3.0
        box(a, 'Ground_Step%d' % i, x0 + 40, x0 + W - 40,
            FRONT - 26 - i*22, FRONT - 4 - i*22, 0, z); made += 1
    return made


def plaza(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """A city square: LAWN first, paving second.

    The first version was a raised concrete deck with two small planters, and
    it read as a sand pit - because that is what it was. A square reads as a
    square when the green is the ground and the paving is the route across it,
    not the other way round. So: lawn over most of the lot, a paved forecourt
    where it meets the pavement, a cross path, planted beds at the flanks and a
    basin on the crossing.

    Trees and benches are placed by fix4_props.py, which owns the footprint
    test - a plaza is a place props go, not a thing that carries its own.
    """
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    a = mkactor('ZONE_%s' % n, origin, (0.0, yaw, 0.0))
    made = 0
    LO = plaza_layout(spec)
    KERB, LAWN = 16.0, 12.0
    deck = KERB + LAWN

    def slab(name, r, z0, z1):
        box(a, name, r[0], r[2], r[1], r[3], z0, z1)

    slab('Kerbing_Edge', LO['bounds'], 0, KERB); made += 1
    slab('Ground_Forecourt', LO['forecourt'], 0, KERB + 2); made += 1
    slab('Grass_Lawn', LO['lawn'], 0, deck); made += 1
    slab('Ground_PathNS', LO['spine'], 0, deck + 2); made += 1
    if LO['walk']:
        slab('Ground_PathEW', LO['walk'], 0, deck + 2); made += 1

    for i, bed in enumerate(LO['beds']):
        slab('Kerbing_Bed%d' % i, bed, deck, deck + 34); made += 1
        slab('Grass_Bed%d' % i, (bed[0] + 16, bed[1] + 16, bed[2] - 16, bed[3] - 16),
             deck, deck + 40); made += 1

    bs = LO['basin']
    bcx, bcy = (bs[0] + bs[2])/2.0, (bs[1] + bs[3])/2.0
    r = (bs[2] - bs[0])/2.0 - 26.0
    for i in range(4):
        ang = math.pi*i/4.0
        hw, hh = abs(r*math.cos(ang)), abs(r*math.sin(ang))
        box(a, 'Ground_Basin%d' % i, bcx - hw - 26, bcx + hw + 26,
            bcy - hh - 26, bcy + hh + 26, deck, deck + 46); made += 1
    box(a, 'Glass_Water', bcx - r*0.9, bcx + r*0.9, bcy - r*0.9, bcy + r*0.9,
        deck + 30, deck + 38); made += 1

    print('%s [plaza]: %d boxes' % (n, made))
    return made


def park(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """Planted open space: lawn, a path across it, low kerbing."""
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    a = mkactor('ZONE_%s' % n, origin, (0.0, yaw, 0.0))
    made = 0
    box(a, 'Kerbing_Edge', x0, x0 + W, FRONT, D, 0, 18); made += 1
    box(a, 'Grass_Lawn', x0 + 10, x0 + W - 10, FRONT + 10, D - 10, 0, 20); made += 1
    # a diagonal desire line, because nobody walks the perimeter
    steps = 7
    for i in range(steps):
        t0, t1 = i/float(steps), (i + 1)/float(steps)
        px0 = x0 + 40 + (W - 200)*t0
        px1 = x0 + 40 + (W - 200)*t1 + 160
        py = FRONT + (D - FRONT - 120)*t0
        box(a, 'Ground_Path%d' % i, px0, px1, py, py + 120, 0, 22); made += 1
    print('%s [park]: %d boxes' % (n, made))
    return made


def vacant(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """A cleared site: hoarding to the street, rough ground behind."""
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    a = mkactor('ZONE_%s' % n, origin, (0.0, yaw, 0.0))
    made = 0
    box(a, 'Ground_Slab', x0, x0 + W, FRONT, D, 0, 12); made += 1
    box(a, 'Frame_Hoarding', x0 - 4, x0 + W + 4, FRONT - 8, FRONT + 10, 0, 210); made += 1
    print('%s [vacant]: %d boxes' % (n, made))
    return made
