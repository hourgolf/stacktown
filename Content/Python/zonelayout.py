"""The authored layout of a non-building lot, as data.

zones.py drew a forecourt, a lawn, a path cross, two beds and a basin, and
fix4_props.py then planted at uniform random across the whole lot because it
had no idea any of that existed. Trees stood on paving, benches stood on grass.
Same shape of bug as every other one this session: two scripts with separate
ideas about the same ground.

So the layout lives here, the geometry is BUILT from it and the planting is
PLACED into it, and they cannot disagree. Pure functions, no Unreal import -
same reason citygeom.py is pure: it can be exercised and self-tested without an
editor.
"""
import math

FRONT = 62.0          # the line a building's facade would have stood on

# --- the authored layout, as data -------------------------------------------
# zones.py drew a forecourt, a lawn, a path cross, two beds and a basin, and
# fix4_props.py then planted at uniform random across the whole lot because it
# had no idea any of that existed. Trees stood on paving, benches stood on
# grass. Same shape of bug as every other one this session: two scripts with
# separate ideas about the same ground. So the layout is data now, the geometry
# is BUILT from it, and the planting is PLACED into it - they cannot disagree.
#
# Adaptive, because a 610 uu lot is 6 m deep. A full path cross needs about
# 700 uu of lawn to leave usable quadrants; below that it eats the whole thing
# and the beds it implies fall outside the lot, which is exactly what the old
# hard-coded bed B did (authored at cy+150, past the back edge). Shallow lots
# get a single spine instead.
BED_W, BED_D, BED_INSET = 340.0, 220.0, 60.0
BENCH_DEPTH = 67.0


# --- seating, which is a matter of what a bench LOOKS AT ---------------------
# Benches were placed at block yaw +/- 180, two per seat rectangle. In the park
# the seat rectangles were the seven segments of a diagonal desire line, so
# fourteen of them marched down it in a chain at rotations unrelated to
# anything; in the green two faced a wall.
#
# A bench is not a prop you scatter. It has a BACK and a FRONT, and in the real
# world it goes against something and looks at something. So seating is derived
# from the layout's own geometry: an anchor to sit against, a focus to face.
#
# MEASURED, not assumed: SM_bench's backrest sits at mean X -30.6 and its seat
# at +0.8 across 306 vertices, so AT YAW 0 THE BENCH FACES +X. Every yaw here
# is the bearing the sitter looks along, in block-local space; the block's own
# yaw is added when it is placed.
#
# A seat entry is (x0, y0, x1, y1, facing) - a strip alone cannot say which way
# to look, because the north and south sides of a ring are both 'wide' and want
# opposite answers.


def face_yaw(fx, fy, tx, ty):
    return math.degrees(math.atan2(ty - fy, tx - fx))


def _inside(rect, x, y, pad=0.0):
    return (rect[0] + pad <= x <= rect[2] - pad
            and rect[1] + pad <= y <= rect[3] - pad)


def seat_plan(lo):
    """[(lx, ly, local_yaw)] - where seats go and what each one looks at."""
    out = []
    if lo.get('basin'):
        b = lo['basin']
        cx, cy = (b[0] + b[2])/2.0, (b[1] + b[3])/2.0
        r = max(b[2] - b[0], b[3] - b[1])/2.0 + BENCH_DEPTH*1.6
        for bearing in (0.0, 90.0, 180.0, 270.0):
            sx = cx + r*math.cos(math.radians(bearing))
            sy = cy + r*math.sin(math.radians(bearing))
            if _inside(lo.get('paving') or lo.get('lawn') or lo['bounds'],
                       sx, sy, BENCH_DEPTH):
                out.append((sx, sy, face_yaw(sx, sy, cx, cy)))
    for sr in lo.get('seat', []):
        rect, yaw = sr[:4], sr[4]
        wide = (rect[2] - rect[0]) >= (rect[3] - rect[1])
        run = (rect[2] - rect[0]) if wide else (rect[3] - rect[1])
        n = max(1, int(run / 900.0))
        for i in range(n):
            t = (i + 0.5)/n
            if wide:
                out.append((rect[0] + (rect[2] - rect[0])*t,
                            (rect[1] + rect[3])/2.0, yaw))
            else:
                out.append(((rect[0] + rect[2])/2.0,
                            rect[1] + (rect[3] - rect[1])*t, yaw))
    return out


def plaza_layout(spec):
    """A civic PLAZA: paving is the ground, a fountain is the focus.

    The opposite emphasis to a green. A green is lawn with a path through it;
    a plaza is a paved room with planting at its edges and something to look at
    in the middle. That is why it needs depth - at 610 uu the Green could only
    ever have been the first of those.
    """
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    Y0, Y1 = FRONT, D
    pav = (x0 + 10.0, Y0 + 10.0, x0 + W - 10.0, Y1 - 10.0)
    cx, cy = (pav[0] + pav[2])/2.0, (pav[1] + pav[3])/2.0
    r = min(pav[2] - pav[0], pav[3] - pav[1])*0.14
    basin = (cx - r - 44.0, cy - r - 44.0, cx + r + 44.0, cy + r + 44.0)

    # TREE PITS, not beds. Three attempts at sizing a corner bed to CONTAIN a
    # canopy all failed, and the reason was a modelling error rather than a
    # number: the smallest crown we own is 348 uu across, and no corner of a
    # 1400 uu square clears the fountain by that much. But a tree in a paved
    # square does not sit inside a bed - it stands in a PIT and overhangs the
    # paving, which is the whole point of a tree pit. So the pit holds the
    # TRUNK and the canopy is free above it; containment is the right rule for
    # a lawn panel and the wrong one here.
    ph = 110.0
    off = min(pav[2] - pav[0], pav[3] - pav[1])*0.28
    pits = [(cx + sx*off - ph, cy + sy*off - ph,
             cx + sx*off + ph, cy + sy*off + ph)
            for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    beds = pits

    # Bench strips run BETWEEN the beds, not across them. The first version
    # inset them a flat 420 from each corner, which put them straight through
    # the corner beds - and since a seat strip is also a keep-off for planting,
    # every tree in the square was rejected and all four beds came out bare.
    # Benches sit on the axes, centred on each side, between the pits.
    m, t = 150.0, BENCH_DEPTH
    seat = [(cx - 260.0, pav[1] + m, cx + 260.0, pav[1] + m + t,  90.0),
            (cx - 260.0, pav[3] - m - t, cx + 260.0, pav[3] - m, -90.0),
            (pav[0] + m, cy - 260.0, pav[0] + m + t, cy + 260.0,   0.0),
            (pav[2] - m - t, cy - 260.0, pav[2] - m, cy + 260.0, 180.0)]

    return dict(bounds=(x0, Y0, x0 + W, Y1), paving=pav, basin=basin,
                fountain=(cx, cy, r), beds=beds, pit=pits,
                tree=[], shrub=[], seat=seat,
                # a rect cannot be both a planting target and a keep-off; the
                # beds were in both, so every tree in the square was rejected
                avoid=[basin] + [e[:4] for e in seat])



def green_layout(spec):
    """A GREEN: lawn-dominant strip. Block-local rectangles. 'tree'/'shrub'/'seat' are where things may go;
    'avoid' is what planting must keep off."""
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    L, R = x0 + 8.0, x0 + W - 8.0
    Y0, Y1 = FRONT, D
    fore = (L, Y0 + 8.0, R, Y0 + 170.0)
    lawn = (L, fore[3], R, Y1 - 8.0)
    depth = lawn[3] - lawn[1]
    cx = x0 + W*0.5
    spine = (cx - 90.0, lawn[1] - 20.0, cx + 90.0, lawn[3])

    if depth >= 700.0:
        cy = (lawn[1] + lawn[3])/2.0
        walk = (L, cy - 90.0, R, cy + 90.0)
        panels = [(L, lawn[1], spine[0], walk[1]), (spine[2], lawn[1], R, walk[1]),
                  (L, walk[3], spine[0], lawn[3]), (spine[2], walk[3], R, lawn[3])]
    else:
        cy = lawn[1] + depth*0.58
        walk = None
        panels = [(L, lawn[1], spine[0], lawn[3]), (spine[2], lawn[1], R, lawn[3])]

    r = min(W, depth)*0.13
    basin = (cx - r - 26.0, cy - r - 26.0, cx + r + 26.0, cy + r + 26.0)

    beds = []
    for i, pn in enumerate(panels):
        if i % 2:                      # every other panel, so it reads as planned
            continue
        bw = min(BED_W, (pn[2] - pn[0]) - 2*BED_INSET)
        bd = min(BED_D, (pn[3] - pn[1]) - 2*BED_INSET)
        if bw < 140.0 or bd < 100.0:   # no room for a bed in this panel
            continue
        bx = pn[0] + BED_INSET
        by = pn[1] + ((pn[3] - pn[1]) - bd)/2.0
        beds.append((bx, by, bx + bw, by + bd))

    # (rect, facing): a seat strip states what its benches look at, because a
    # strip alone cannot say - the north edge of a ring and the south edge want
    # opposite yaws and both are 'wide'.
    seat = [(fore[0] + 40.0, fore[1] + 20.0, fore[2] - 40.0, fore[3] - 20.0, 90.0)]
    if walk:
        seat.append((walk[0] + 40.0, walk[1] + 16.0, walk[2] - 40.0, walk[3] - 16.0, 90.0))

    return dict(bounds=(x0, Y0, x0 + W, Y1), forecourt=fore, lawn=lawn,
                spine=spine, walk=walk, panels=panels, beds=beds, basin=basin,
                tree=panels, shrub=beds, seat=seat,
                avoid=[spine, basin] + beds + ([walk] if walk else []))


RING_W = 130.0        # perimeter walk
SPINE_W = 150.0       # the cross
NODE_R = 270.0        # paved node where the cross meets
STAND_R = 190.0       # the bandstand standing on it


def park_layout(spec):
    """A perimeter walk, a cross, four lawn quadrants and a bandstand.

    The docstring on zones.park has said "a perimeter walk - people circuit
    the edge and cut the middle" since it was written, and the layout built a
    single spine and no ring. The prose was right and the code was not, which
    is why a 346 m2 park came out of the build with five boxes in it and
    scored 0.046 parts/m2 against every other open lot's 0.13-0.17.

    The first version of THIS function was a ring, and it was abandoned
    because at 1280 deep the ring plus two belts left a 318 uu strip too
    narrow to plant. That reasoning was sound for a ring PLUS belts; a ring
    plus a cross leaves four quadrants of about 1135 x 394, which holds the
    348 uu crown measured in SCALE-01 with room to spare.
    """
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    Y0, Y1 = FRONT, D
    outer = (x0 + 10.0, Y0 + 10.0, x0 + W - 10.0, Y1 - 10.0)
    inner = (outer[0] + RING_W, outer[1] + RING_W,
             outer[2] - RING_W, outer[3] - RING_W)
    cx = (inner[0] + inner[2])/2.0
    cy = (inner[1] + inner[3])/2.0
    h = SPINE_W/2.0

    ring = [(outer[0], outer[1], outer[2], inner[1]),      # south
            (outer[0], inner[3], outer[2], outer[3]),      # north
            (outer[0], inner[1], inner[0], inner[3]),      # west
            (inner[2], inner[1], outer[2], inner[3])]      # east
    ns = (cx - h, inner[1], cx + h, inner[3])
    ew = (inner[0], cy - h, inner[2], cy + h)
    node = (cx - NODE_R, cy - NODE_R, cx + NODE_R, cy + NODE_R)
    stand = (cx - STAND_R, cy - STAND_R, cx + STAND_R, cy + STAND_R)

    quads = [(inner[0], inner[1], cx - h, cy - h),
             (cx + h, inner[1], inner[2], cy - h),
             (inner[0], cy + h, cx - h, inner[3]),
             (cx + h, cy + h, inner[2], inner[3])]

    # a bed in each quadrant, pushed to the corner against the ring so the
    # middle of the panel stays open for a tree
    beds = []
    for i, q in enumerate(quads):
        bx = q[0] + BED_INSET if i in (0, 2) else q[2] - BED_INSET - BED_W
        by = q[1] + BED_INSET if i in (0, 1) else q[3] - BED_INSET - BED_D
        beds.append((bx, by, bx + BED_W, by + BED_D))

    # Seating: two on the cross facing across it, two on the ring facing in.
    # Every one looks at lawn, which is what ZONE-02 checks.
    seat = [(ew[0] + 360.0, ew[1], cx - NODE_R - 40.0, cy, -90.0),
            (cx + NODE_R + 40.0, cy, ew[2] - 360.0, ew[3], 90.0),
            (outer[0] + 420.0, outer[1], outer[2] - 420.0, inner[1], 90.0),
            (outer[0] + 420.0, inner[3], outer[2] - 420.0, outer[3], -90.0)]

    return dict(bounds=(x0, Y0, x0 + W, Y1), lawn=outer,
                walks=[ns, ew], ring=ring, node=node, stand=stand,
                centre=(cx, cy), panels=quads, beds=beds,
                tree=quads, shrub=quads, seat=seat,
                avoid=[ns, ew, node] + ring + beds)


# --- the house plan, shared -------------------------------------------------
# build_house draws the house and fix4_props plants the garden, and they need
# the same rectangles or the planting lands in the patio. Same reason the zone
# layout lives here.
HOUSE_GARDEN = 250.0
HOUSE_SIDE = 100.0
HOUSE_DEPTH = 430.0


def house_plan(spec):
    """Block-local rectangles for one house lot."""
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    hx0, hx1 = x0 + HOUSE_SIDE, x0 + W - HOUSE_SIDE
    hy0 = HOUSE_GARDEN
    hy1 = min(D - 60.0, hy0 + HOUSE_DEPTH)
    return dict(house=(hx0, hy0, hx1, hy1),
                front=(x0 + 12.0, 8.0, x0 + W - 12.0, hy0 - 4.0),
                back=(x0 + 12.0, hy1 + 10.0, x0 + W - 12.0, D - 12.0))



# --- the works yard ---------------------------------------------------------
# A yard is not a box with props sprinkled in it. It is a ROUTE with things
# stacked either side of it: a gate, an apron a lorry can turn on, and stores
# pushed back against the boundary. So the apron is authored FIRST and is
# kept clear, and every prop slot below is checked against it by _yard_check.
#
# Panel lengths are measured, not chosen: the chain-link panels are 412 uu and
# cannot be cut, so the gate is what is LEFT OVER after whole panels, rather
# than a width picked first and the fence made to fit it.
FENCE_PANEL = 412.0       # measured: SM_Fence_ChainLink_A01 is 412 x 12 x 144
YARD_INSET = 20.0


def yard_layout(spec):
    """Block-local layout of a works yard.

    Fenced to the street and to the block end; open to its own buildings,
    because a yard does not fence itself off from the shed it serves.
    """
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    i = YARD_INSET
    X0, X1 = x0 + i, x0 + W - i
    Y0, Y1 = FRONT + 10.0, D - i

    # Frontage: whole panels at each end, the gate is the remainder.
    gate = (X0 + FENCE_PANEL, X1 - FENCE_PANEL)
    south = [(X0, Y0, X0 + FENCE_PANEL, Y0, 0.0),
             (X1 - FENCE_PANEL, Y0, X1, Y0, 0.0)]
    # Block end: whole panels from the front, stopping short of the stores.
    n_east = int((Y1 - Y0 - 200.0) // FENCE_PANEL)
    east = [(X1, Y0 + k*FENCE_PANEL, X1, Y0 + (k+1)*FENCE_PANEL, 90.0)
            for k in range(max(1, n_east))]
    post = (X1, Y0 + max(1, n_east)*FENCE_PANEL)

    # The apron: from the gate, north, wide enough to turn on. Kept clear.
    apron = (gate[0] + 18.0, FRONT, gate[1] - 18.0, Y0 + 690.0)

    # Stores along the back, clear of the apron's reach.
    store_y = Y1 - 122.0
    props = [
        ('container_long', X0 + 330.0, store_y,   0.0, 90.0),
        ('container_long', X0 + 950.0, store_y,   0.0, 90.0),
        ('container_short', X0 + 250.0, store_y, 290.0, 90.0),
        ('scaffold', X0 + 130.0, Y0 + 640.0, 0.0, 0.0),
        ('ladder',   X0 + 250.0, Y0 + 640.0, 0.0, 0.0),
        ('lumber_stack', X1 - 230.0, Y0 + 240.0, 0.0, 0.0),
        ('lumber_pile',  X1 - 230.0, Y0 + 560.0, 0.0, 0.0),
        # A STACK, and DRESS-06 counts plan position, not height - three
        # pallets on one spot read to it as three props in the same place.
        # It is also not how a stack sits: they shuffle. Offsetting fixes the
        # rule and the look together.
        ('pallet', X1 - 330.0, Y0 + 740.0,  0.0, 0.0),
        ('pallet', X1 - 318.0, Y0 + 752.0, 12.0, 8.0),
        ('pallet', X1 - 342.0, Y0 + 731.0, 24.0, -6.0),
        ('plywood', X1 - 40.0, Y0 + 880.0, 0.0, 90.0),
    ]
    lo = dict(bounds=(x0, FRONT, x0 + W, D), gate=gate, apron=apron,
              south=south, east=east, post=post, props=props,
              hard=(X0, Y0 - 8.0, X1, Y1), avoid=[apron])
    _yard_check(lo)
    return lo


def _yard_check(lo):
    """Known-answer check: the apron is the whole idea, so prove it is clear.

    Run at layout time, not at review time. A prop standing on the route is the
    single defect that makes a yard read as sprinkled rather than worked, and
    it is invisible from any angle where the yard looks busy.
    """
    ax0, ay0, ax1, ay1 = lo['apron']
    for role, x, y, _z, _yaw in lo['props']:
        if ax0 < x < ax1 and ay0 < y < ay1:
            raise AssertionError(
                'yard_layout: %s at (%.0f, %.0f) stands on the apron %s'
                % (role, x, y, tuple(round(v) for v in lo['apron'])))
    gx0, gx1 = lo['gate']
    if gx1 - gx0 < 400.0:
        raise AssertionError('yard_layout: gate %.0f uu is too narrow to drive'
                             % (gx1 - gx0))


def layout(spec):
    k = spec.get('kind')
    if k == 'green':
        return green_layout(spec)
    if k == 'plaza':
        return plaza_layout(spec)
    if k == 'park':
        return park_layout(spec)
    if k == 'vacant':
        return yard_layout(spec)
    return None


