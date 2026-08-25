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
    return dict(bounds=(x0, FRONT, x0 + W, D), lawn=lawn, paths=paths,
                tree=[lawn], shrub=[lawn], seat=paths, avoid=paths)


def layout(spec):
    k = spec.get('kind')
    if k == 'plaza':
        return plaza_layout(spec)
    if k == 'park':
        return park_layout(spec)
    return None


