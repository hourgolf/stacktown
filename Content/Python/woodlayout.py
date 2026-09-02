#!/usr/bin/env python3
"""DIRECTION B's board layout, as pure computation. No editor, no MCP.

    python3 Content/Python/woodlayout.py           self-test + a size table
    python3 Content/Python/woodlayout.py 8 6       lay out 8x6 blocks

WHY THIS IS A MODULE AND NOT MORE OF wood_set.py. The layout lived inside
wood_set with COLS and ROWS as constants, which meant the only way to find out
what a denser board did was to BUILD one - four minutes of live actor
creation, an editor window, and a queue position behind another lane. Density
is the open question and it was gated on the one resource this lane does not
control.

Layout is arithmetic. Arithmetic does not need an editor. Split out, a
hundred-block board can be laid out, measured and self-tested in a second,
and the editor is needed only to LOOK at the answer - which is the right
division, and the one citylayout.py already uses for the flagship.

WHAT IT EMITS: a list of placements, each a dict the caller spawns.
    {'asset','species','angle','x','y','yaw','block','tier'}
Nothing here knows about actors, materials or Unreal.

THE CORE IS GRADED, and that is a finding rather than a preference. An earlier
board dealt buildings round-robin so every block held a tower; the spires
clustered into a central mound and the town read as a pyramid. Contiguous
slices of a form-ordered table accidentally produced a downtown at one end and
low blocks at the other, which read far better. That accident is made
deliberate here: a height field grades tiers from a core outward, so the town
has a middle and an edge the way a city does.
"""
import math
import sys

# the six blocks of the current board, generalised. Street and plot come from
# the committed values wood_set already uses.
STREET = 560.0
PLOT_OVER = 90.0
PLATE_MARGIN = 300.0

# tier names must match mk_woodbake's _FORMS keys, because the bake table is
# the authority on what exists and this module must not invent a tier.
TIERS = ('flat', 'setback1', 'setback2', 'tower')

# four cuts from the stock, so neighbours do not show the same face of the log
ANGLES = (0, 2, 1, 3)


def core_value(c, r, cols, rows):
    """How central a block is: 1.0 at the middle, 0.0 at the rim.

    CHEBYSHEV, not Euclidean, for a reason measured on an earlier board:
    Euclidean distance clamps at the corners and 29 of 35 blocks came out at
    the floor value, median 260. Chebyshev grades a RECTANGLE outward, which
    is what a downtown occupying a few central blocks looks like from above.
    """
    dc = abs(c - (cols - 1) / 2.0) / max(1e-6, (cols - 1) / 2.0) if cols > 1 else 0.0
    dr = abs(r - (rows - 1) / 2.0) / max(1e-6, (rows - 1) / 2.0) if rows > 1 else 0.0
    return (1.0 - max(dc, dr)) ** 1.15


def _noise(c, r, seed):
    """Deterministic per-block noise in 0..1. No numpy, no random state.

    A hash rather than random() because the layout must be reproducible from
    its inputs alone - the same grid and seed give the same city, which is the
    same contract genbuild_identity holds the generator to.
    """
    h = (c * 73856093) ^ (r * 19349663) ^ (seed * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def _rank_key(c, r, cols, rows, seed=0, jag=0.0):
    """How central, with a TIE-BREAK on the weaker axis.

    Chebyshev grades a rectangle, which is what a downtown is - but on a thin
    grid it erases the other axis entirely. At 3x2 both rows are edge rows, so
    max(dc, dr) is 1.0 for every block, all six tie, and the tallest tier goes
    to whichever block the sort happened to reach first. The self-test caught
    that; the middle COLUMN is plainly more central than the edges even when
    no row is.

    So: rank by the Chebyshev core first, and break ties by the summed
    distance, which keeps the weaker axis informative without disturbing the
    rectangular grading on grids that have a real middle.
    """
    dc = abs(c - (cols - 1) / 2.0) / max(1e-6, (cols - 1) / 2.0) if cols > 1 else 0.0
    dr = abs(r - (rows - 1) / 2.0) / max(1e-6, (rows - 1) / 2.0) if rows > 1 else 0.0
    core = core_value(c, r, cols, rows)
    # JAG: the pure distance field grades too evenly and the skyline came out
    # as a DOME - a smooth radial swell to a peak in the middle. Real
    # downtowns, and B1's, have a harder and more irregular profile: a cluster
    # of tall things with abrupt edges, and low blocks surviving inside the
    # core. Noise blended into the RANK (not into the tier) keeps the core
    # central while breaking its outline, so some rim blocks reach up and some
    # core blocks stay low.
    core = core * (1.0 - jag) + _noise(c, r, seed) * jag
    return (core, -(dc + dr))


def assign_tiers(cols, rows, mix, seed=0, jag=0.35):
    """Tier per block, by RANK rather than by threshold.

    A threshold on the raw core value fails on small or thin grids and fails
    silently: at 3x2 EVERY block is on the rim, because with two rows both
    rows are edge rows, so a distance threshold grades the whole board to the
    lowest tier and the town quietly loses its towers. The self-test caught
    exactly that on its first run.

    Ranking is robust at any grid size: sort the blocks by how central they
    are and slice that ordering by the catalogue's own tier proportions. The
    centre always gets the tallest tier because it is the most central, not
    because it cleared a number.

    `mix` is {tier: count} from the bake table, so THE TOWN'S TIER MIX MIRRORS
    THE CATALOGUE'S. No tier is starved and none is over-used, and a change to
    what gets baked changes the town without anyone editing this file.
    """
    order = sorted(((_rank_key(bi % cols, bi // cols, cols, rows, seed, jag),
                     -bi) for bi in range(cols * rows)), reverse=True)
    total = float(sum(mix[t] for t in TIERS)) or 1.0
    n = cols * rows
    want = []
    for t in reversed(TIERS):              # tallest first: the core
        want.append((t, int(round(n * mix[t] / total))))
    # rounding must not lose or invent blocks
    short = n - sum(k for _, k in want)
    if short:
        want[-1] = (want[-1][0], want[-1][1] + short)
    out = {}
    i = 0
    for t, k in want:
        for _ in range(max(0, k)):
            if i >= len(order):
                break
            out[-order[i][1]] = t
            i += 1
    for bi in range(n):                    # any remainder is rim, so lowest
        out.setdefault(bi, TIERS[0])
    return out


def _rows_of(block):
    """Split a block's buildings into a front and back row, backs together."""
    half = (len(block) + 1) // 2
    return block[:half], block[half:]


# HOW MANY BUILDINGS A BLOCK HOLDS. Uniform 4 made every block the same size
# and the survey frame read as a chessboard - B1's blocks vary considerably,
# and that variation is part of why it looks surveyed rather than generated.
# citylayout solved the same problem for the flagship with per-block
# PARTITIONS; this is the wooden board's version.
BLOCK_SIZES = (3, 4, 4, 5, 6, 4, 3, 5)


def lay(catalogue, cols, rows, per_block=None, seed=20260901, jag=0.35,
        bend=0.0):
    """Place `cols` x `rows` blocks of `per_block` buildings.

    `catalogue` is [(asset, species, width, depth, tier)] - what mk_woodbake
    actually baked. This module never invents a building; it only arranges
    what exists, which is why density costs placements and not bakes.
    """
    import random
    rnd = random.Random(seed)
    by_tier = {t: [c for c in catalogue if c[4] == t] for t in TIERS}
    for t in TIERS:
        if not by_tier[t]:
            raise ValueError('catalogue has no building at tier %r - the bake '
                             'table and this layout disagree' % t)

    mix = {t: len(by_tier[t]) for t in TIERS}
    tier_of = assign_tiers(cols, rows, mix, seed=seed, jag=jag)
    blocks, i = [], 0
    for r in range(rows):
        for c in range(cols):
            t = tier_of[r * cols + c]
            pool = by_tier[t]
            n_here = (per_block if per_block is not None else
                      BLOCK_SIZES[int(_noise(c, r, seed + 7) *
                                      len(BLOCK_SIZES)) % len(BLOCK_SIZES)])
            blk = [pool[(i + k) % len(pool)] for k in range(n_here)]
            rnd.shuffle(blk)
            blocks.append(blk)
            i += n_here

    # block extents, then column widths and row depths, then the town
    bw, bd = [], []
    for blk in blocks:
        f, k = _rows_of(blk)
        bw.append(max(sum(b[2] for b in f), sum(b[2] for b in k)) or 1.0)
        bd.append(max([b[3] for b in f] or [0]) + max([b[3] for b in k] or [0]))
    cw = [max(bw[c::cols]) for c in range(cols)]
    rd = [max(bd[r * cols:(r + 1) * cols]) for r in range(rows)]
    town_w = sum(cw) + STREET * (cols + 1)
    town_d = sum(rd) + STREET * (rows + 1)

    # THE BEND. Not a road system - a probe. The roads study predicts that a
    # curved street cannot give a building a curved frontage, because the
    # catalogue is five fixed widths, so a curve must be served by STRAIGHT
    # CHORDS with the curve absorbed by the ribbon and by wedge-shaped gaps at
    # the joints. That prediction has never been LOOKED at. This bends the
    # grid so the geometry exists to look at: blocks stay rectangular, their
    # origins follow an arc, and each rotates to the local tangent.
    #
    # What it should expose, and what the frames are for:
    #   - do the wedges read as B3's fitted piecing, or as error?
    #   - how big do they get before they stop looking deliberate?
    #   - what happens where two curving streets meet?
    def _bend_at(c):
        if not bend:
            return 0.0, 0.0
        u = c / float(max(1, cols - 1))
        span = sum(cw) + STREET * (cols + 1)
        amp = bend * span * 0.18
        dy = amp * math.sin(math.pi * u)
        # tangent from the derivative, so blocks turn WITH the street rather
        # than sitting square on a curve like a fence
        dydx = amp * math.pi * math.cos(math.pi * u) / max(1.0, span)
        return dy, math.atan(dydx)

    out = []
    for bi, blk in enumerate(blocks):
        c, r = bi % cols, bi // cols
        bx = STREET + sum(cw[:c]) + c * STREET
        by = STREET + sum(rd[:r]) + r * STREET
        b_dy, b_th = _bend_at(c)
        front, back = _rows_of(blk)
        fd = max([b[3] for b in front] or [0])
        for row, y0, yaw in ((front, 0.0, 0.0), (back, fd, 180.0)):
            cx = 0.0
            for j, (asset, sp, w, d, tier) in enumerate(row):
                # local position within the block, then rotated to the
                # street's tangent and carried to the bent block origin
                lx = cx + (w if yaw else 0.0)
                ly = y0 + (d if yaw else 0.0)
                ct, st_ = math.cos(b_th), math.sin(b_th)
                out.append({
                    'asset': asset, 'species': sp, 'tier': tier,
                    'angle': ANGLES[(bi + j) % len(ANGLES)],
                    # the 180 row is placed from its far corner, so its FRONT
                    # faces the far street - frontage on both sides of a road
                    'x': bx + lx * ct - ly * st_,
                    'y': by + b_dy + lx * st_ + ly * ct,
                    'yaw': yaw + math.degrees(b_th), 'block': bi})
                cx += w
    return {'placements': out, 'blocks': blocks, 'bw': bw, 'bd': bd,
            'cw': cw, 'rd': rd, 'town_w': town_w, 'town_d': town_d,
            'cols': cols, 'rows': rows, 'bend': bend, 'bend_at': _bend_at}


# --- self-tests, run on import of __main__ ---------------------------------

def _selftest():
    cat = [('SM_Mass_b%02d' % i, 'oak', 600.0 + 50 * (i % 9),
            560.0 + 30 * (i % 5), TIERS[min(3, i // 6)]) for i in range(20)]

    # 1. THE CORE IS CENTRAL - stated two ways, because JAG deliberately
    #    breaks the exact version.
    #
    #    With jag=0 the field is pure distance and the tallest tier lands on
    #    the most central block, exactly. With jag>0 that is NO LONGER TRUE
    #    and must not be asserted: noise in the rank is precisely what stops
    #    the skyline being a smooth dome, so some rim blocks reach up and some
    #    core blocks stay low. What survives is the STATISTICAL claim - the
    #    tall tier is still, on average, more central than the low one.
    #
    #    Two earlier versions of this test were wrong and both failed loudly,
    #    which is the only reason they were not shipped: a distance THRESHOLD
    #    flattened thin grids silently, and "middle block beats corner block"
    #    was overspecified because at 3x2 four of six blocks are equivalent.
    mix = {t: len([c for c in cat if c[4] == t]) for t in TIERS}
    for cols, rows in ((3, 2), (4, 3), (8, 6), (14, 10)):
        tof = assign_tiers(cols, rows, mix, seed=0, jag=0.0)
        ranked = sorted(range(cols * rows),
                        key=lambda bi: _rank_key(bi % cols, bi // cols,
                                                 cols, rows, 0, 0.0),
                        reverse=True)
        assert tof[ranked[0]] == TIERS[-1], (
            'with jag=0 the most central block at %dx%d got %s, not %s'
            % (cols, rows, tof[ranked[0]], TIERS[-1]))

    for cols, rows in ((8, 6), (14, 10)):
        tof = assign_tiers(cols, rows, mix, seed=3, jag=0.35)
        def _mean_core(tier):
            v = [core_value(bi % cols, bi // cols, cols, rows)
                 for bi, t in tof.items() if t == tier]
            return sum(v) / float(len(v)) if v else 0.0
        hi, lo = _mean_core(TIERS[-1]), _mean_core(TIERS[0])
        assert hi > lo, (
            'jagged core is not central at %dx%d: mean core %.3f for %s vs '
            '%.3f for %s' % (cols, rows, hi, TIERS[-1], lo, TIERS[0]))
        # and the jag must actually DO something, or the dome is still a dome
        exact = assign_tiers(cols, rows, mix, seed=3, jag=0.0)
        moved = sum(1 for bi in tof if tof[bi] != exact[bi])
        assert moved >= (cols * rows) // 8, (
            'jag moved only %d of %d blocks at %dx%d - the skyline is still a '
            'dome' % (moved, cols * rows, cols, rows))

    # 2. NO TWO BUILDINGS OVERLAP. The layout's one real correctness claim,
    #    and the one a live build would only reveal as a visible collision.
    for cols, rows in ((3, 2), (6, 5)):
        L = lay(cat, cols, rows)
        boxes = []
        for p in L['placements']:
            w = next(c[2] for c in cat if c[0] == p['asset'])
            d = next(c[3] for c in cat if c[0] == p['asset'])
            x0 = p['x'] - (w if p['yaw'] else 0.0)
            y0 = p['y'] - (d if p['yaw'] else 0.0)
            boxes.append((x0, y0, x0 + w, y0 + d))
        for a in range(len(boxes)):
            ax0, ay0, ax1, ay1 = boxes[a]
            for b in range(a + 1, len(boxes)):
                bx0, by0, bx1, by1 = boxes[b]
                ox = min(ax1, bx1) - max(ax0, bx0)
                oy = min(ay1, by1) - max(ay0, by0)
                assert not (ox > 1.0 and oy > 1.0), (
                    'placements %d and %d overlap by %.0f x %.0f uu at %dx%d'
                    % (a, b, ox, oy, cols, rows))

    # 2b. A BENT LAYOUT MUST NOT COLLIDE EITHER. The AABB test above is only
    #     valid for axis-aligned blocks, so bent grids are checked by block
    #     CENTRE separation instead - crude, but it catches a bend amplitude
    #     that folds one block through its neighbour, which is the failure
    #     mode worth catching before a ten-minute build.
    for bendv in (0.5, 1.0):
        L = lay(cat, 8, 6, bend=bendv)
        cen = {}
        for p in L['placements']:
            cen.setdefault(p['block'], []).append((p['x'], p['y']))
        mids = {b: (sum(x for x, _ in v) / len(v), sum(y for _, y in v) / len(v))
                for b, v in cen.items()}
        for b in range(8 * 6 - 1):
            if b % 8 == 7:
                continue
            ax, ay = mids[b]
            bx2, by2 = mids[b + 1]
            gap = math.hypot(bx2 - ax, by2 - ay)
            assert gap > 400.0, (
                'bend %.1f folds blocks %d and %d to %.0f uu apart'
                % (bendv, b, b + 1, gap))

    # 3. counts scale as blocks x per_block, so "density" is a number the
    #    caller sets rather than an emergent surprise
    for cols, rows, per in ((3, 2, 4), (10, 8, 4), (12, 10, 6)):
        L = lay(cat, cols, rows, per_block=per)
        assert len(L['placements']) == cols * rows * per, (
            '%dx%d x%d gave %d placements' % (cols, rows, per,
                                              len(L['placements'])))
    return True


def main():
    args = [a for a in sys.argv[1:] if a.isdigit()]
    cat = [('SM_Mass_b%02d' % i, 'oak', 600.0 + 50 * (i % 9),
            560.0 + 30 * (i % 5), TIERS[min(3, i // 6)]) for i in range(20)]
    _selftest()
    print('woodlayout self-test: core graded, no overlaps, counts exact')
    print()
    print('%-9s %8s %9s %9s %8s' % ('grid', 'blocks', 'buildings',
                                    'town (uu)', 'vs 3x2'))
    base = None
    grids = [(int(args[0]), int(args[1]))] if len(args) >= 2 else \
            [(3, 2), (5, 4), (8, 6), (12, 9), (16, 12)]
    for cols, rows in grids:
        L = lay(cat, cols, rows)
        n = len(L['placements'])
        if base is None:
            base = n
        print('%-9s %8d %9d %5.0fx%-5.0f %7.1fx'
              % ('%dx%d' % (cols, rows), cols * rows, n,
                 L['town_w'], L['town_d'], n / float(base)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
