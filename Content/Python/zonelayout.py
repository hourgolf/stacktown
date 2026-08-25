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


def plaza_layout(spec):
    """Block-local rectangles. 'tree'/'shrub'/'seat' are where things may go;
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

    seat = [(fore[0] + 40.0, fore[1] + 20.0, fore[2] - 40.0, fore[3] - 20.0)]
    if walk:
        seat.append((walk[0] + 40.0, walk[1] + 16.0, walk[2] - 40.0, walk[3] - 16.0))

    return dict(bounds=(x0, Y0, x0 + W, Y1), forecourt=fore, lawn=lawn,
                spine=spine, walk=walk, panels=panels, beds=beds, basin=basin,
                tree=panels, shrub=beds, seat=seat,
                avoid=[spine, basin] + beds + ([walk] if walk else []))


def park_layout(spec):
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    lawn = (x0 + 10.0, FRONT + 10.0, x0 + W - 10.0, D - 10.0)
    paths = []
    steps = 7
    for i in range(steps):
        t0, t1 = i/float(steps), (i + 1)/float(steps)
        paths.append((x0 + 40.0 + (W - 200.0)*t0,
                      FRONT + (D - FRONT - 120.0)*t0,
                      x0 + 40.0 + (W - 200.0)*t1 + 160.0,
                      FRONT + (D - FRONT - 120.0)*t0 + 120.0))
    # NO SEATING until this block is redesigned. seat=paths put one bench on
    # every segment of the diagonal desire line, so fourteen of them marched
    # down the park in a chain at rotations unrelated to anything. A path is
    # not a seating plan. The replacement is a designed park with a focus, and
    # until it exists an empty lawn is the honest answer.
    return dict(bounds=(x0, FRONT, x0 + W, D), lawn=lawn, paths=paths,
                tree=[lawn], shrub=[lawn], seat=[], avoid=paths)


# --- seating, which is a matter of what a bench LOOKS AT ---------------------
# Benches were placed at block yaw +/- 180 and spaced two per seat rectangle.
# In the park, seat rectangles were the seven segments of the diagonal desire
# line, so fourteen benches marched down it in a chain at rotations unrelated
# to anything - and in the green two of them faced a wall.
#
# A bench is not a prop you scatter. It has a BACK and a FRONT, and in the real
# world it goes against something and looks at something: back to a path edge,
# a hedge or a wall, front to the lawn, the water or the view. So seating is
# derived from the layout's own geometry - an anchor to sit against, and a
# focus to face.
#
# MEASURED, not assumed: SM_bench's backrest sits at mean X -30.6 and its seat
# at +0.8 across 306 vertices, so AT YAW 0 THE BENCH FACES +X. Every yaw below
# is the compass bearing of the direction the sitter looks, in block-local
# space, and the block's own yaw is added when it is placed.
BENCH_DEPTH = 67.0


def face_yaw(fx, fy, tx, ty):
    """Local yaw for a bench at (fx,fy) looking at (tx,ty)."""
    return math.degrees(math.atan2(ty - fy, tx - fx))


def seat_plan(lo):
    """[(lx, ly, local_yaw)] - where seats go and what each one looks at."""
    out = []
    if 'basin' in lo and lo.get('basin'):
        # A fountain or basin is a focus: benches ring it and look AT it, set
        # back far enough not to crowd it.
        b = lo['basin']
        cx, cy = (b[0] + b[2])/2.0, (b[1] + b[3])/2.0
        r = max(b[2] - b[0], b[3] - b[1])/2.0 + BENCH_DEPTH*1.6
        for bearing in (0.0, 90.0, 180.0, 270.0):
            sx = cx + r*math.cos(math.radians(bearing))
            sy = cy + r*math.sin(math.radians(bearing))
            if _inside(lo.get('lawn') or lo['bounds'], sx, sy, BENCH_DEPTH):
                out.append((sx, sy, face_yaw(sx, sy, cx, cy)))
    for sr in lo.get('seat', []):
        # A seat strip is paving. Sit against its long edge, look across the
        # SHORT axis toward whatever is deeper into the lot.
        wide = (sr[2] - sr[0]) >= (sr[3] - sr[1])
        n = max(1, int((sr[2] - sr[0] if wide else sr[3] - sr[1]) / 900.0))
        for i in range(n):
            t = (i + 0.5)/n
            if wide:
                sx = sr[0] + (sr[2] - sr[0])*t
                sy = sr[1] + BENCH_DEPTH*0.5
                out.append((sx, sy, 90.0))          # look deeper into the lot
            else:
                sx = sr[0] + BENCH_DEPTH*0.5
                sy = sr[1] + (sr[3] - sr[1])*t
                out.append((sx, sy, 0.0))
    return out


def _inside(rect, x, y, pad=0.0):
    return (rect[0] + pad <= x <= rect[2] - pad
            and rect[1] + pad <= y <= rect[3] - pad)


def layout(spec):
    k = spec.get('kind')
    if k in ('plaza', 'green'):
        return plaza_layout(spec)
    if k == 'park':
        return park_layout(spec)
    return None


