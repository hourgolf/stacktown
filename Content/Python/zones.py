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
from zonelayout import (green_layout, plaza_layout, park_layout,  # noqa: F401
                        yard_layout, layout, seat_plan)

FRONT = 62.0          # the line a building's facade would have stood on



def build(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    k = spec.get('kind')
    if k == 'green':
        return green(spec, origin, yaw)
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


def green(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """A GREEN: LAWN first, paving second.

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
    LO = green_layout(spec)
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

    print('%s [green]: %d boxes' % (n, made))
    return made


def fountain(a, cx, cy, r, z0, tag='Fount'):
    """Generated, not acquired - the same call the street lamps got. A donor
    fountain arrives with its own detail tier and its own materials, and every
    complete donor object tried in this project has had to be fought back to
    the diorama. A card-model fountain is a rim, a pool, a plinth, a bowl and a
    jet. Four rectangles of varying aspect read as a round pool from above,
    which is how the existing basin is built."""
    made = 0
    for i in range(4):
        ang = math.pi*i/4.0
        hw, hh = abs(r*math.cos(ang)), abs(r*math.sin(ang))
        box(a, 'Kerbing_%sRim%d' % (tag, i), cx - hw - 30, cx + hw + 30,
            cy - hh - 30, cy + hh + 30, z0, z0 + 44); made += 1
    box(a, 'Glass_%sPool' % tag, cx - r*0.94, cx + r*0.94,
        cy - r*0.94, cy + r*0.94, z0 + 26, z0 + 34); made += 1
    box(a, 'Ground_%sPlinth' % tag, cx - r*0.30, cx + r*0.30,
        cy - r*0.30, cy + r*0.30, z0, z0 + 96); made += 1
    box(a, 'Ground_%sBowl' % tag, cx - r*0.54, cx + r*0.54,
        cy - r*0.54, cy + r*0.54, z0 + 96, z0 + 130); made += 1
    box(a, 'Glass_%sBowlPool' % tag, cx - r*0.46, cx + r*0.46,
        cy - r*0.46, cy + r*0.46, z0 + 122, z0 + 128); made += 1
    box(a, 'Kerbing_%sJet' % tag, cx - 15, cx + 15, cy - 15, cy + 15,
        z0 + 130, z0 + 242); made += 1
    return made


def plaza(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """A civic square: paving is the ground, a fountain is the focus."""
    n = spec['name']
    a = mkactor('ZONE_%s' % n, origin, (0.0, yaw, 0.0))
    LO = plaza_layout(spec)
    KERB = 16.0
    made = 0

    def slab(name, r, z0, z1):
        box(a, name, r[0], r[2], r[1], r[3], z0, z1)

    slab('Kerbing_Edge', LO['bounds'], 0, KERB); made += 1
    slab('Ground_Paving', LO['paving'], 0, KERB + 3); made += 1

    # three steps down to the footway, so the square meets the street the way a
    # block does rather than reading as a hole
    b = LO['bounds']
    for i in range(3):
        z = KERB*(2 - i)/3.0
        box(a, 'Ground_Step%d' % i, b[0] + 300, b[2] - 300,
            b[1] - 26 - i*22, b[1] - 4 - i*22, 0, z); made += 1

    for i, bed in enumerate(LO['beds']):
        slab('Kerbing_Bed%d' % i, bed, KERB + 3, KERB + 40); made += 1
        slab('Grass_Bed%d' % i, (bed[0] + 18, bed[1] + 18, bed[2] - 18, bed[3] - 18),
             KERB + 3, KERB + 46); made += 1

    cx, cy, r = LO['fountain']
    made += fountain(a, cx, cy, r, KERB + 3)
    print('%s [plaza]: %d boxes' % (n, made))
    return made


def park(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """Lawn with a perimeter walk - people circuit the edge and cut the middle.

    The prose above was already here while the layout built a single spine and
    no ring, and the park came out with five boxes over 346 m2. It now builds
    what it says: a ring, a cross, four quadrants, four beds, and a bandstand
    on the node where the cross meets. DETAIL-02 is the rule that caught it.
    """
    n = spec['name']
    a = mkactor('ZONE_%s' % n, origin, (0.0, yaw, 0.0))
    LO = park_layout(spec)
    made = 0

    def slab(name, r, z0, z1):
        box(a, name, r[0], r[2], r[1], r[3], z0, z1)

    slab('Kerbing_Edge', LO['bounds'], 0, 18); made += 1
    slab('Grass_Lawn', LO['lawn'], 0, 22); made += 1
    for i, r in enumerate(LO['ring']):
        slab('Ground_Ring%d' % i, r, 0, 26); made += 1
    for i, w in enumerate(LO['walks']):
        slab('Ground_Walk%d' % i, w, 0, 24); made += 1
    slab('Ground_Node', LO['node'], 0, 28); made += 1
    # kerbed edging where each quadrant meets its walk, so it reads as built
    for i, pn in enumerate(LO['panels']):
        slab('Kerbing_Panel%d' % i, pn, 0, 20); made += 1
    # planting beds, kerb first so the soil sits inside a built edge
    for i, b in enumerate(LO['beds']):
        slab('Kerbing_Bed%d' % i, b, 22, 46); made += 1
        slab('Bloom_Bed%d' % i, (b[0]+14, b[1]+14, b[2]-14, b[3]-14), 40, 62)
        made += 1

    # the bandstand: plinth, ring of posts, roof, finial. A park this size
    # wants one thing to look at from the ring walk, and it is the only piece
    # of built structure in the lot.
    cx, cy = LO['centre']
    st = LO['stand']
    r = (st[2] - st[0])/2.0
    slab('Ground_Plinth', (st[0], st[1], st[2], st[3]), 28, 76); made += 1
    slab('Frame_Deck', (st[0]+22, st[1]+22, st[2]-22, st[3]-22), 76, 88)
    made += 1
    posts = 8
    for i in range(posts):
        th = 2.0*math.pi*i/posts
        px, py = cx + (r-46)*math.cos(th), cy + (r-46)*math.sin(th)
        box(a, 'Frame_Post%d' % i, px-13, px+13, py-13, py+13, 88, 300)
        made += 1
    # The roof was two stacked boxes named Roof_, and Roof_ maps to MI_concrete
    # - the same pale grey as a commercial deck - so a bandstand read as a
    # white block. Tile_ is the role that already means "pitched roof, take the
    # lot's shingle", which is what this always was. A box builder cannot make
    # a cone, so it is a taper: at 1:87 a seven-step taper in shingle reads as
    # a conical roof, which two boxes never could.
    slab('Tile_Eaves', (st[0]-30, st[1]-30, st[2]+30, st[3]+30), 300, 316)
    made += 1
    STEPS, APEX = 7, 436.0
    for i in range(STEPS):
        t0, t1 = i/float(STEPS), (i+1)/float(STEPS)
        h0 = (r + 30.0)*(1.0 - t0) + 20.0*t0
        z0 = 316.0 + (APEX - 316.0)*t0
        z1 = 316.0 + (APEX - 316.0)*t1 + 3.0      # overlap, or the steps gap
        box(a, 'Tile_Step%d' % i, cx-h0, cx+h0, cy-h0, cy+h0, z0, z1)
        made += 1
    box(a, 'Frame_Finial', cx-11, cx+11, cy-11, cy+11, APEX, APEX + 56.0)
    made += 1
    print('%s [park]: %d boxes' % (n, made))
    return made


def _fence(a, tag, r, made):
    """Post-and-rail fence, ours, from a layout run.

    The donor chain-link panels are gone. Their mask texture
    (T_Fence_ChainLink_A01_M) carries GRAFFITI TAGS as well as wire, so using
    its alpha as an opacity cut printed someone else's tags across the yard -
    their texture shipping in all but name, which is the one thing the donor
    rule forbids. Two panels also rendered inconsistently because the wire and
    the frame are separate material slots and only one of them was masked.

    At 1:87 the wire is not the readable part of a fence anyway. Posts and
    rails are, and authored from the SAME layout run the plinth was built
    from, they cannot drift out of alignment with it.
    """
    x0, y0, x1, y1 = r[0], r[1], r[2], r[3]
    horiz = abs(x1 - x0) >= abs(y1 - y0)
    L = abs(x1 - x0) if horiz else abs(y1 - y0)
    H, T = 150.0, 6.0
    n = max(2, int(round(L/340.0)) + 1)
    for i in range(n):
        t = i/float(n - 1)
        px, py = x0 + (x1 - x0)*t, y0 + (y1 - y0)*t
        box(a, '%s_P%d' % (tag, i), px - 9, px + 9, py - 9, py + 9, 12, H)
        made += 1
    for j, (z0, z1) in enumerate(((H - 15, H - 3), (H*0.54, H*0.54 + 9),
                                  (30.0, 39.0))):
        if horiz:
            box(a, '%s_R%d' % (tag, j), min(x0, x1), max(x0, x1),
                y0 - T, y0 + T, z0, z1)
        else:
            box(a, '%s_R%d' % (tag, j), x0 - T, x0 + T,
                min(y0, y1), max(y0, y1), z0, z1)
        made += 1
    return made


def vacant(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """A WORKS YARD: hardstanding, a gated frontage, and a kept-clear apron.

    Was two boxes - a slab and a hoarding - and nothing in the invariant suite
    covered it, because DETAIL-01 only looks at kind='gen'. So the one lot no
    rule watched is the one that stayed bare. DETAIL-02 now covers open lots.

    The apron is the idea: a lorry comes in at the gate, turns, and backs onto
    the stores. Nothing is built or stacked on it, which is what makes the
    props read as worked rather than sprinkled. yard_props.py places the donor
    meshes into the SAME layout, so the two cannot disagree.
    """
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    LO = yard_layout(spec)
    a = mkactor('ZONE_%s' % n, origin, (0.0, yaw, 0.0))
    made = 0

    def slab(name, r, z0, z1):
        box(a, name, r[0], r[2], r[1], r[3], z0, z1)

    # THREE surfaces, because every box here was Ground_ and Ground_ is one
    # material - so a yard that had a concrete apron, compacted ground and a
    # spoil heap in the data rendered as one flat pale tone. The apron and the
    # container pad are laid concrete; everything else is compacted ground.
    box(a, 'Ground_Slab', x0, x0 + W, FRONT, D, 0, 12); made += 1
    slab('Gravel_Hard', LO['hard'], 12, 20); made += 1
    slab('Ground_Apron', LO['apron'], 20, 26); made += 1
    # a container stands on a pad, not on dirt - and the pad is what tells you
    # the stores were placed rather than dropped
    hx0, hy0, hx1, hy1 = LO['hard']
    box(a, 'Ground_Pad', hx0 + 20, hx0 + 1310, hy1 - 300, hy1, 20, 27); made += 1

    # kerb along the frontage, DROPPED across the gate - a crossover is how a
    # yard entrance actually reads, and it is the only thing that says which
    # gap in the fence is the gate.
    gx0, gx1 = LO['gate']
    box(a, 'Kerbing_West', x0, gx0, FRONT - 8, FRONT + 8, 0, 26); made += 1
    box(a, 'Kerbing_Cross', gx0, gx1, FRONT - 8, FRONT + 8, 0, 10); made += 1
    box(a, 'Kerbing_East', gx1, x0 + W, FRONT - 8, FRONT + 8, 0, 26); made += 1

    # gate piers, one either side of the opening
    for i, gx in enumerate((gx0, gx1)):
        box(a, 'Frame_Pier%d' % i, gx - 14, gx + 14, FRONT + 2, FRONT + 30,
            0, 190); made += 1

    # the fence itself, plus a low plinth for it to stand on
    for i, (fx0, fy0, fx1, fy1, _fy) in enumerate(LO['south'] + LO['east']):
        box(a, 'Kerbing_Fence%d' % i, min(fx0, fx1) - 8, max(fx0, fx1) + 8,
            min(fy0, fy1) - 8, max(fy0, fy1) + 8, 12, 30); made += 1
        made = _fence(a, 'Rail_F%d' % i, (fx0, fy0, fx1, fy1), made)

    # A notice board on the gate pier. The donor parking sign stood free in the
    # middle of the yard as a grey slab - it is a STREET asset, and a yard gate
    # wants a nameplate on the pier, not a car park sign on the ground.
    box(a, 'Accent_Notice', gx0 - 17, gx0 + 17, FRONT - 3, FRONT + 3, 104, 168)
    made += 1
    box(a, 'Rail_NoticeBack', gx0 - 4, gx0 + 4, FRONT + 3, FRONT + 8, 120, 152)
    made += 1

    # spoil, in the corner the apron does not reach
    box(a, 'Gravel_Spoil', hx0 + 40, hx0 + 250, hy0 + 690, hy0 + 900, 20, 52)
    made += 1
    box(a, 'Gravel_Spoil2', hx0 + 250, hx0 + 400, hy0 + 730, hy0 + 880, 20, 38)
    made += 1
    print('%s [yard]: %d boxes' % (n, made))
    return made
