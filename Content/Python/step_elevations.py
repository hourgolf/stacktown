"""Punch a real elevation into the exposed flank of a generated building.

WHERE IT APPLIES, AND WHY NOT EVERYWHERE. Lots tile edge to edge and adjacent
buildings share a party wall, so an interior flank is buried against its
neighbour - a real terrace has blind party walls and only the buildings at the
ends of the block show a side. Punching windows into a party wall would be
wrong architecturally and invisible anyway. So only the two END lots of a block
qualify, and only on their outward side.

Block A declares abuts_low in city.py because its low-x end runs into the
reused Stage 1 building, which is a level actor rather than a lot. Without that
declaration the rule would call Narrow's west flank exposed and punch windows
straight into a party wall. That leaves three flanks: Mid east, Bank east,
Hall west.

FULL FRONT VOCABULARY, at the owner's direction: piers, band course per floor,
recessed glazing, frames, sill and mullions - the same parts the street facade
uses, so the role sweep binds them with no extra work and the two elevations
are made of the same fabrication language.

The re-derived block hero (cam_street_hero.py) sits 2,000-6,000 uu off its
subject, where the 0.4% threshold is 41-123 mm - not the 230 mm of the old
block hero. Window furniture reads at this camera, which is what makes the full
treatment worth its geometry.

Everything is block-local; the block's world placement rides on the actor
transform, exactly as genbuild does it.
"""
import _path  # noqa: F401
import ue, math, random
from city import BLOCKS
from genbuild import mkactor, box

OVER_X = 8.0       # cores carry the band-course overhang; the core face is there
FACADE_T = 60.0    # the elevation is a SLAB standing proud of the core face.
                   # This is not decoration - it is the whole reason the front
                   # elevation works. The core's front is at y 62 and the facade
                   # occupies y 0..60 in front of it, so a window recessed 27 uu
                   # sits in open air. The first version of this file put the
                   # flank's outer face ON the core face and recessed the
                   # glazing INTO the core, where it is solid: the render came
                   # back as a blank wall with two band courses floating on it,
                   # because only the proud parts were outside the mass.
FRONT = 62.0       # facade back / core front
PIER_W = 52.0
BAY_TARGET = 340.0
BITE = 14.0        # how far a flank's inner face pushes PAST the facade line,
#                    so the two meet in an overlap rather than a shared plane


def exposed_flanks(block):
    """(lot, sign) for every building flank with no building against it.
    sign -1 = low-x flank, +1 = high-x flank, in BLOCK-LOCAL space.

    Two ways a flank is exposed. It is at the END of the block, or its
    NEIGHBOUR IS NOT A BUILDING - an open zone leaves the wall beside it on
    show. That second case only started existing when kind dispatch let a lot
    be a plaza, and without it a building fronting the new plaza would have
    kept the blind party wall it was given when a building stood there.
    """
    lots = sorted(block['lots'], key=lambda l: l['x0'])
    out = []
    for i, l in enumerate(lots):
        # detached styles (solid Wall_Body, four real walls of their own)
        # take no commercial elevation slabs - hanging a full-lot-depth pier
        # grid beside a 520-deep walkup built a free-standing wall in its
        # garden
        import cores as _co
        if l['kind'] != 'gen' or l.get('style') in _co.DETACHED:
            continue
        low_free = (i == 0 and not block.get('abuts_low')) or \
                   (i > 0 and lots[i-1]['kind'] not in ('gen', 'av'))
        high_free = (i == len(lots)-1 and not block.get('abuts_high')) or \
                    (i < len(lots)-1 and lots[i+1]['kind'] not in ('gen', 'av'))
        if low_free:  out.append((l, -1))
        if high_free: out.append((l, +1))
    return out


def exposed_rears(block):
    """Lots whose REAR fronts a road rather than a party line.

    Block B's back faced empty board until street 2 was built behind it; now it
    is a frontage and the blank slab reads as one. Block C's two rows meet on a
    rear party line, so they are never listed here.
    """
    if not block.get('rear_street'):
        return []
    return [l for l in block['lots']
            if l['kind'] == 'gen'
            and l.get('style') not in __import__('cores').DETACHED]


def rear(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """A rear elevation runs along X like the FRONT does, mirrored in Y.

    Same depth discipline as everywhere else: the slab stands FACADE_T proud of
    the core's back face, so a window recessed 27 uu sits in open air instead of
    inside solid mass.
    """
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    F, GF, FH, PAR = spec['floors'], spec['gf_h'], spec['fl_h'], spec['parapet']
    YP = D + FACADE_T
    ztop = GF + F * FH
    a = mkactor('ELEV_%s_R' % n, origin, (0.0, yaw, 0.0))
    made = 0

    def b(name, d0, d1, x_0, x_1, z0, z1):
        """d measured INTO the building from the outer face, so y decreases."""
        nonlocal made
        box(a, name, x_0, x_1, YP - d1, YP - d0, z0, z1)
        made += 1

    bays = max(2, int(round(W / 380.0)))
    bw = W / float(bays)
    b('Wall_Plinth', -6, 66, x0 - 6, x0 + W + 6, 0, 30)

    bands = [(0.0, GF)] + [(GF + f * FH, GF + (f + 1) * FH) for f in range(F)]
    for lvl, (z0, z1) in enumerate(bands):
        # THE PIERS DECIDE WHERE THE OPENINGS ARE, and until 29 Aug they did
        # not. The last pier is clamped inward so it cannot overhang the
        # corner, but the opening beside it was still measured off the bay
        # grid - so on every level of every model the last window ran PIER_W uu
        # UNDER that pier, and its right jamb ended flush with the pier's
        # outer face. Two like-facing surfaces at one depth, on a face the
        # camera sees square on: that is the largest single source of visible
        # coplanar pairs in the catalogue, and it is what cold read #1
        # described from the other side as clipping.
        #
        # Deriving both from ONE list of pier positions is the fix. Every bay
        # but the last is unchanged; the last becomes a properly formed
        # narrower window instead of a wide one with its end buried.
        pxs = [min(x0 + k * bw, x0 + W - PIER_W) for k in range(bays + 1)]
        for k, px in enumerate(pxs):
            b('Wall_L%dPier%d' % (lvl, k), 0, 60, px, px + PIER_W, z0, z1 - 34)
        b('Band_L%dCourse' % lvl, -8, 58, x0 - 8, x0 + W + 8, z1 - 34, z1)
        for k in range(bays):
            wx0 = pxs[k] + PIER_W
            wx1 = pxs[k + 1]
            if wx1 - wx0 < 60:
                continue
            wz0, wz1 = z0 + 62, z1 - 66
            b('Glass_L%dB%d' % (lvl, k), 27, 29, wx0 + 6, wx1 - 6, wz0 + 6, wz1 - 6)
            b('Interior_L%dB%d' % (lvl, k), 47, 53, wx0, wx1, wz0, wz1)
            b('Frame_L%dB%dL' % (lvl, k), 19, 29, wx0, wx0 + 6, wz0, wz1)
            b('Frame_L%dB%dR' % (lvl, k), 19, 29, wx1 - 6, wx1, wz0, wz1)
            b('Frame_L%dB%dT' % (lvl, k), 19, 29, wx0, wx1, wz1 - 6, wz1)
            b('Frame_L%dB%dS' % (lvl, k), 13, 29, wx0 - 4, wx1 + 4, wz0 - 6, wz0)
            mx = (wx0 + wx1) / 2.0
            b('Mullion_L%dB%dV' % (lvl, k), 21, 28, mx - 3, mx + 3, wz0, wz1)
            mz = wz0 + (wz1 - wz0) * 0.62
            b('Mullion_L%dB%dH' % (lvl, k), 21, 28, wx0, wx1, mz - 3, mz + 3)
    # RUNS BETWEEN THE FLANK CAPS, which now own the rear corners outright.
    # The bound is DERIVED, not measured off one model and pasted: a flank
    # slab's inner face lands at x0 -+ (OVER_X - BITE), which is the same
    # x0+6 the geometry reported for w820. Writing 6.0 here would have been a
    # constant that happened to be right for one width and silently wrong the
    # day OVER_X or BITE moved.
    cap0, cap1 = ((x0 - OVER_X + BITE, x0 + W + OVER_X - BITE)
                  if has_flank_cap(spec) else (x0 - 10, x0 + W + 10))
    b('Band_RearCap', -10, 60, cap0, cap1, ztop + PAR, ztop + PAR + 14)
    print('  ELEV_%s_R: %d boxes' % (n, made))
    return made


def flank(spec, sign, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """Dispatch on style, exactly as genbuild does. A modern corner wearing a
    vernacular side elevation would be two buildings pretending to be one."""
    # FLAGS FIRST, style only as the fallback. See FLANK_KINDS above.
    k = flank_kind(spec)
    if k:
        return flank_param(spec, sign, origin, yaw, FLANK_KINDS[k])
    st = spec.get('style')
    if st == 'modern':
        return flank_modern(spec, sign, origin, yaw)
    if st == 'deco':
        return flank_deco(spec, sign, origin, yaw)
    if st == 'contemporary':
        return flank_contemporary(spec, sign, origin, yaw)
    return flank_vernacular(spec, sign, origin, yaw)


def flank_vernacular(spec, sign, origin=(0.0, 0.0, 0.0), yaw=0.0):
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    F, GF, FH, PAR = spec['floors'], spec['gf_h'], spec['fl_h'], spec['parapet']
    setback = spec.get('setback') or 0.0
    # outer face of the flank slab, standing FACADE_T proud of the core
    XP = (x0 - OVER_X - FACADE_T) if sign < 0 else (x0 + W + OVER_X + FACADE_T)
    ztop = GF + F * FH
    rnd = random.Random(spec.get('seed', 0) + (7 if sign < 0 else 13))
    face = 'W' if sign < 0 else 'E'
    a = mkactor('ELEV_%s_%s' % (n, face), origin, (0.0, yaw, 0.0))

    def xr(d0, d1):
        """x range between two depths measured INTO the wall from the outer
        face. Negative depth is proud of the face.

        BITE, at the inner end. The flank slab's deepest boxes land at exactly
        x0 - OVER_X, which is exactly where the front's Band_Course starts -
        two coincident planes, and coincident planes z-fight. That is the dark
        vertical streaking down the corner piers: not clipping geometry, two
        surfaces at the same depth arguing about which is in front.
        A few uu of overlap makes it a solid union instead of a coin toss.
        """
        d1 = d1 + BITE if d1 >= FACADE_T - 1.0 else d1
        p, q = XP - sign * d0, XP - sign * d1
        return (p, q) if p <= q else (q, p)

    made = 0

    def b(name, d0, d1, y0, y1, z0, z1):
        nonlocal made
        ax0, ax1 = xr(d0, d1)
        box(a, name, ax0, ax1, y0, y1, z0, z1)
        made += 1

    # plinth: ties the elevation to the pavement, same 30 uu as the front
    b('Wall_Plinth', -6, 66, FRONT - 6, D + 6, 0, 30)

    # ground floor, then each upper floor. genbuild only sets back the TOP
    # floor, so only that band starts further in - the same rule step_cores3
    # uses to segment the core, and it has to agree or the glazing floats.
    bands = [(0.0, GF, FRONT)]
    for f in range(F):
        z0 = GF + f * FH
        bands.append((z0, z0 + FH, FRONT + (setback if f == F - 1 else 0.0)))

    # Component names must be UNIQUE within an actor. genbuild gets away with
    # plain names because it makes a fresh actor per floor; this elevation is
    # one actor for the whole flank, so reusing 'Wall_Pier0' on six bands made
    # UE rename them all to StaticMesh0..N and the role sweep reported 122
    # unresolved components with no material.
    for lvl, (z0, z1, front) in enumerate(bands):
        usable = D - front
        bays = max(1, int(round(usable / BAY_TARGET)))
        bw = usable / float(bays)
        # same clamp, same fix as the front elevation above
        pys = [min(front + k * bw, D - PIER_W) for k in range(bays + 1)]
        for k, py in enumerate(pys):
            b('Wall_L%dPier%d' % (lvl, k), 0, 60, py, py + PIER_W, z0, z1 - 34)
        b('Band_L%dCourse' % lvl, -8, 58, front - 8, D + 8, z1 - 34, z1)
        for k in range(bays):
            wy0 = pys[k] + PIER_W
            wy1 = pys[k + 1]
            if wy1 - wy0 < 60:
                continue                      # too narrow to be a window
            wz0, wz1 = z0 + 62, z1 - 66
            b('Glass_L%dB%d' % (lvl, k), 27, 29, wy0 + 6, wy1 - 6, wz0 + 6, wz1 - 6)
            b('Interior_L%dB%d' % (lvl, k), 47, 53, wy0, wy1, wz0, wz1)
            b('Frame_L%dB%dL' % (lvl, k), 19, 29, wy0, wy0 + 6, wz0, wz1)
            b('Frame_L%dB%dR' % (lvl, k), 19, 29, wy1 - 6, wy1, wz0, wz1)
            b('Frame_L%dB%dT' % (lvl, k), 19, 29, wy0, wy1, wz1 - 6, wz1)
            b('Frame_L%dB%dS' % (lvl, k), 13, 29, wy0 - 4, wy1 + 4, wz0 - 6, wz0)
            my = (wy0 + wy1) / 2.0
            b('Mullion_L%dB%dV' % (lvl, k), 21, 28, my - 3, my + 3, wz0, wz1)
            mz = wz0 + (wz1 - wz0) * 0.62
            b('Mullion_L%dB%dH' % (lvl, k), 21, 28, wy0, wy1, mz - 3, mz + 3)

    # parapet cap, matching the front's Band_ParapetCap so the corner reads
    # CARRIES THROUGH TO THE REAR CAP'S BACK FACE, completing the coping ring.
    # It used to stop at D+10 while Band_RearCap sits behind that plane at
    # YP-60..YP+10, so the two lapped 16x10 uu at each rear corner - 240
    # pairs, the largest roofline mechanism, and part of what the owner saw
    # on the roofs on 29 Aug.
    #
    # THIS ONE GAINS COVERAGE and that is the point, not a side effect. Both
    # simple mitres were tried and PROVEN WRONG by the union check before
    # anything shipped: the two pieces interlock in an L and each covered
    # part of what the other would have given up, so trimming either left a
    # hole - 12,600 cells the first time, 2,240 the second. Carrying the
    # flank through and pulling the rear cap in between the flanks is the
    # only arrangement that removes the lap AND leaves no gap; it closes the
    # outer rear corner the old ring never covered. Owner's call, 29 Aug.
    b('Band_FlankCap', -10, 60, FRONT - 10, D + FACADE_T + 10,
      ztop + PAR, ztop + PAR + 14)

    # ---- a MURAL, on one flank only ---------------------------------------
    # A painted image at 1:87 is mud - the whole facade is 14 mm across on the
    # board. So a mural is built the way you would actually paint one on a
    # card model: a few big offset blocks of colour, which is also how most
    # real gable-end murals read from across a street.
    #
    # One flank, not both. A mural goes on the wall people can see, and a
    # building with the same mural on both sides reads as wallpaper.
    mural = spec.get('mural')
    if mural and sign > 0:
        rr = random.Random(spec.get('seed', 0) + 991)
        my0, my1 = FRONT + 90.0, D - 120.0
        mz0, mz1 = GF + 40.0, ztop - 60.0
        if my1 > my0 + 200.0 and mz1 > mz0 + 200.0:
            # three blocks, each a different card colour, deliberately not
            # aligned to the window grid - paint does not know about bays
            cuts = sorted(rr.uniform(0.28, 0.72) for _ in range(2))
            spans = [(0.0, cuts[0]), (cuts[0], cuts[1]), (cuts[1], 1.0)]
            for i, (t0, t1) in enumerate(spans):
                y0 = my0 + (my1 - my0) * t0
                y1 = my0 + (my1 - my0) * t1
                # each block takes a different slice of the height
                h0 = mz0 + (mz1 - mz0) * rr.uniform(0.0, 0.30)
                h1 = mz1 - (mz1 - mz0) * rr.uniform(0.0, 0.26)
                if h1 <= h0 + 80.0:
                    continue
                b('Mural_%s' % 'ABC'[i], 2, 5, y0 + 8, y1 - 8, h0, h1)

    print('  ELEV_%s_%s: %d boxes' % (n, face, made))
    return made


# MEASURED, not derived: a walkup core built at 1420 with both flanks treated
# spans 1576 - GATE-05 refused all three tiers and reported the number. The
# flank slab's outer face sits at x0 - OVER_X - FACADE_T and its band courses
# overhang a little further, so the allowance is 156 in total and does NOT
# scale with width: every offset is fixed relative to x0 and x0 + W.
#
# In a city this proud-standing is right - only END lots get flanks and their
# outward face looks at a street, so the slab oversails nothing. A catalogue
# model has no such luxury: the parcel is the entire budget, so the CORE is
# built narrower and the flanks bring it back out to the parcel line.
FLANK_W = 156.0


def flank_allowance(spec):
    """How much wider a model gets when both flanks are treated.

    STYLE-DEPENDENT, which the first version got wrong. FLANK_W was measured
    on a walkup - a vernacular flank - and applied to everything. A MODERN
    flank builds its spandrel bands at depth -BAND_PROUD, i.e. 40 uu PROUD of
    the flank face, so it needs that much again on each side. The tower's top
    tier came back 36 uu over the parcel line on BOTH sides and GATE-05 named
    it; the symmetry was the clue that it was an allowance error rather than
    a placement one.
    """
    st = spec.get('style')
    if st == 'house':
        return 0.0
    if st == 'modern':
        import genbuild as _g
        return FLANK_W + 2.0 * _g.BAND_PROUD
    k = flank_kind(spec)
    if k:
        # the parameterised flank stands `proud` off the face on each side,
        # so the allowance follows the SAME table the geometry does
        return FLANK_W + 2.0 * float(FLANK_KINDS[k]['proud'])
    if st == 'contemporary':
        # a curtain-wall flank is FLAT - nothing stands proud of it, so it
        # needs no more than the facade thickness either side
        return FLANK_W
    if st == 'deco':
        # A DECO FLANK CARRIES PILASTERS. They stand DECO_PROUD (50) off the
        # face, and the base cap oversails the pilaster line by another 6 - so
        # each flank is 56 uu wider than a plain vernacular one. GATE-05 named
        # it on every deco tier at once, symmetric on both sides, which is the
        # same signature the tower gave when this function still returned one
        # number for every style.
        import genbuild as _g
        return FLANK_W + 2.0 * (_g.DECO_PROUD + 6.0)
    return FLANK_W


def rear_allowance(spec):
    """How much DEEPER a model gets when the rear is treated.

    The same fault as the flanks, at ninety degrees: rear() puts the slab's
    outer face at D + FACADE_T, so a treated rear pushes 60 uu past the back
    of the plot and into whatever is behind it. GATE-05 refused four of five
    vernacular tiers at 888 uu in a 700 uu plot and named the number.

    The front is different and is NOT deducted: a canopy, a cill and a cornice
    oversail the PAVEMENT, which is what GATE-05's OVERSAIL allowance is for.
    A rear slab oversails the next owner's land, which nothing allows.
    """
    return 0.0 if spec.get('style') == 'house' else FACADE_T


def freestanding(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """Treat EVERY face - for a catalogue model, which has no neighbours.

    exposed_flanks and exposed_rears exist because a city is a terrace: a
    mid-block flank is a party wall buried against the building next door, and
    punching windows into it would be both wrong and invisible. That reasoning
    is sound for a FIXED city and does not survive a catalogue.

    A catalogue mesh is placed wherever the grammar or the player puts it. It
    cannot know whether anything stands beside it, so it has to be correct
    freestanding - and the cost is asymmetric: a blind wall is a visible bug
    the moment a model lands on a corner, while a window hidden behind a
    neighbour costs a few hundred triangles nobody ever sees.

    Skips `house`, which build_house already builds on all four sides - the
    same exclusion exposed_flanks makes, for the same reason.
    """
    if spec.get('style') == 'house':
        return 0
    made = flank(spec, -1, origin, yaw)
    made += flank(spec, +1, origin, yaw)
    made += rear(spec, origin, yaw)
    return made


def run(only=None):
    # Idempotent: wipe our own actors first - THROUGH rung.sh, locally.
    #
    # This used to wipe over MCP with get_all_level_actors, which is the call
    # that returns something unparseable and gets swallowed by the except
    # below. It reported nothing and removed nothing, so a standalone re-run
    # stacked a second elevation on the first and in one case a third. 95
    # duplicated labels were found only because NAME-03 was written to look for
    # them. street_lamps and rebuild_zones were moved off MCP for exactly this;
    # this was the one left.
    import os as _os, subprocess as _sub, tempfile as _tf
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _rung = _os.path.join(_os.path.dirname(_os.path.dirname(_here)),
                          'Tools', 'rung.sh')
    open(_os.path.join(_tf.gettempdir(), 'stacktown_wipe_family.txt'),
         'w').write('ELEV')
    _r = _sub.run([_rung, 'wipe_family.py'], capture_output=True, text=True,
                  cwd=_here)
    if 'success: True' not in _r.stdout:
        raise SystemExit('wipe_family.py FAILED - refusing to build on top of '
                         'the old set\n' + (_r.stdout[-400:] or _r.stderr[-400:]))
    print('  ' + next((l[7:] for l in _r.stdout.splitlines() if 'removed' in l),
                      'wipe reported nothing'))
    total = 0
    for blk in BLOCKS:
        for spec, sign in exposed_flanks(blk):
            if only and spec['name'] != only:
                continue
            total += flank(spec, sign, blk['origin'], blk['yaw'])
        for spec in exposed_rears(blk):
            if only and spec['name'] != only:
                continue
            total += rear(spec, blk['origin'], blk['yaw'])
    print('elevations: %d boxes' % total)
    return total


if __name__ == '__main__':
    import sys
    run(sys.argv[1] if len(sys.argv) > 1 else None)


# ---------------------------------------------------------------------------
# P2: FLANKS DISPATCH ON FEATURE FLAGS, NOT ON STYLE.
#
# `flank()` used to read spec['style'] alone. That was right when a style meant
# one facade. It stopped being right the moment a style carried eight of them:
# a mass-timber block and a glass tower are both style 'contemporary', and the
# timber one was being given a curtain-wall side. Deco hit this first and got
# flank_deco; contemporary hit it and got flank_contemporary; then modern3,
# modern7, contemporary2, contemporary3 and contemporary7 all hit it at once
# and writing a builder per recipe was clearly the wrong answer.
#
# So: ONE parameterised flank, and a table mapping the generator's OWN flags
# onto it. A flank is only ever a few decisions - is it blind, does it read
# vertical or horizontal, how proud do the members stand, how big are the
# openings - and those decisions are what actually differ between eras.
# ---------------------------------------------------------------------------
FLANK_KINDS = {
    #            vert  horiz  proud  open   blind
    'grid':     dict(vert=96.0,  horiz=0.0,   proud=13.0, open=0.62),
    'frame':    dict(vert=210.0, horiz=1.0,   proud=26.0, open=0.50),
    'panel':    dict(vert=190.0, horiz=1.0,   proud=6.0,  open=0.44),
    'fins':     dict(vert=96.0,  horiz=0.0,   proud=74.0, open=0.72),
    'coffer':   dict(vert=250.0, horiz=1.0,   proud=52.0, open=0.40),
    'steel':    dict(vert=118.0, horiz=1.0,   proud=22.0, open=0.66),
    'deck':     dict(vert=0.0,   horiz=1.0,   proud=10.0, open=0.30),
    'banded':   dict(vert=0.0,   horiz=1.0,   proud=14.0, open=0.34),
    'giant':    dict(vert=430.0, horiz=0.0,   proud=30.0, open=0.46),
    'stripe':   dict(vert=0.0,   horiz=1.0,   proud=20.0, open=0.40),
}


def flank_kind(spec):
    """Which flank this spec wants, read from the SAME flags the generator reads.

    Order matters: a spec can carry more than one flag and the most
    face-defining one wins.
    """
    for flag, kind in (('timber', 'frame'), ('brise', 'fins'),
                       ('rainscreen', 'panel'), ('coffer', 'coffer'),
                       ('precast', 'coffer'), ('steel_frame', 'steel'),
                       ('deck_access', 'deck'), ('banded', 'banded'),
                       ('giant_order', 'giant'), ('streamline', 'stripe'),
                       ('stacked', 'grid'), ('green_terrace', 'grid')):
        if spec.get(flag):
            return kind
    return None


def has_flank_cap(spec):
    """Do this spec's flanks carry a Band_FlankCap for the rear cap to meet?

    ONLY flank_vernacular builds one. rear() has to know, because the rear
    cap is trimmed back to the flank caps' inner faces to stop the two
    lapping at the corners - and on a model whose flanks carry no cap that
    same trim is a 2,240-cell hole in the coping, which is exactly what the
    union proof caught on five of eight test models before this existed.

    Written as one function rather than repeating the condition, because the
    two places that need it are 300 lines apart and a copy would rot the
    first time flank() gains a style.
    """
    if flank_kind(spec):
        return False
    return spec.get('style') not in ('modern', 'deco', 'contemporary')


def flank_param(spec, sign, origin, yaw, P):
    """A flank built from a handful of knobs. See FLANK_KINDS."""
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    F, GF, FH, PAR = spec['floors'], spec['gf_h'], spec['fl_h'], spec['parapet']
    XP = (x0 - OVER_X - FACADE_T) if sign < 0 else (x0 + W + OVER_X + FACADE_T)
    ztop = GF + F * FH
    face = 'W' if sign < 0 else 'E'
    a = mkactor('ELEV_%s_%s' % (n, face), origin, (0.0, yaw, 0.0))
    made = 0

    def xr(d0, d1):
        p, q = XP - sign * d0, XP - sign * d1
        return (p, q) if p <= q else (q, p)

    def b(name, d0, d1, y0, y1, z0, z1):
        nonlocal made
        ax0, ax1 = xr(d0, d1)
        box(a, name, ax0, ax1, y0, y1, z0, z1)
        made += 1

    prd = float(P['proud'])
    b('Wall_FlankBase', 0.0, FACADE_T, 0.0, D, 0.0, GF - 14)
    b('Band_FlankBaseCap', -7.0, FACADE_T + 7.0, -9.0, D + 9.0, GF - 14, GF)
    # ONLY IF THERE ARE UPPER FLOORS. ztop is GF + F*FH, so a single-storey
    # model (F=0) asked for a box of zero height on every build - 46 of them
    # across contemporary2. add_cube refused each one and the refusal was
    # discarded. Nothing is missing from those models: there IS no flank body
    # above a ground floor. The box simply should never have been requested.
    if ztop > GF:
        b('Wall_FlankBody', 0.0, FACADE_T, 0.0, D, GF, ztop)
    y0, y1 = 44.0, D - 44.0

    if F >= 1 and P['open'] > 0.0 and (y1 - y0) > 120.0:
        nw = max(2, int(round((y1 - y0) / 300.0)))
        for f in range(F):
            z0, z1 = GF + f * FH, GF + (f + 1) * FH
            for k in range(nw):
                w0 = y0 + (y1 - y0) * k / float(nw)
                w1 = w0 + (y1 - y0) / float(nw) * float(P['open'])
                if w1 - w0 < 42:
                    continue
                b('Wall_FlankRev%d_%d' % (f, k), FACADE_T - prd, FACADE_T + 4,
                  w0 - 10, w1 + 10, z0 + FH * 0.24 - 10, z1 - FH * 0.14 + 10)
                b('Glass_Flank%d_%d' % (f, k), FACADE_T - prd - 3,
                  FACADE_T - prd, w0, w1, z0 + FH * 0.24, z1 - FH * 0.14)
                b('Interior_Flank%d_%d' % (f, k), FACADE_T - prd - 11,
                  FACADE_T - prd - 5, w0, w1, z0 + FH * 0.24, z1 - FH * 0.14)

    if P['vert'] > 0.0:
        nm = max(2, int(round((D - 40.0) / float(P['vert']))))
        for k in range(nm + 1):
            my = 20.0 + (D - 40.0) * k / float(nm)
            mw = 13.0 if (k == 0 or k == nm) else 8.0
            b('Mullion_FlankV%d' % k, FACADE_T - prd - 2, FACADE_T + 2,
              my - mw / 2, my + mw / 2, GF + 3, ztop - 3)

    if P['horiz'] > 0.0 and F >= 1:
        for f in range(F + 1):
            z0 = GF + f * FH
            b('Band_FlankCourse%d' % f, FACADE_T - prd * 0.6, FACADE_T + 3,
              -6.0, D + 6.0, z0 - 12, z0 + 14)

    b('Wall_FlankParapet', 0.0, FACADE_T, 0.0, D, ztop, ztop + PAR - 14)
    b('Band_FlankCoping', -8.0, FACADE_T + 8.0, -10.0, D + 10.0,
      ztop + PAR - 14, ztop + PAR)
    return made


def flank_contemporary(spec, sign, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """A curtain wall turned through 90 degrees.

    It borrowed flank_modern, which is late-modern spandrel-and-ribbon: deep
    horizontal banding. Against a front that is an unbroken VERTICAL grid that
    reads as two different buildings stuck together, and on a plain prism the
    flank is half of what the eye sees. Canon slot 5's towers carry the same
    skin on every face; that is most of why they read as single objects.

    So: the same mullion run, the same slim spandrel, the same corner pier.
    """
    import genbuild as _g
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    F, GF, FH, PAR = spec['floors'], spec['gf_h'], spec['fl_h'], spec['parapet']
    XP = (x0 - OVER_X - FACADE_T) if sign < 0 else (x0 + W + OVER_X + FACADE_T)
    ztop = GF + F * FH
    face = 'W' if sign < 0 else 'E'
    a = mkactor('ELEV_%s_%s' % (n, face), origin, (0.0, yaw, 0.0))
    made = 0

    def xr(d0, d1):
        p, q = XP - sign * d0, XP - sign * d1
        return (p, q) if p <= q else (q, p)

    def b(name, d0, d1, y0, y1, z0, z1):
        nonlocal made
        ax0, ax1 = xr(d0, d1)
        box(a, name, ax0, ax1, y0, y1, z0, z1)
        made += 1

    # ground floor: solid, so the glazed front reads as the entrance side
    b('Wall_FlankBase', 0.0, FACADE_T, 0.0, D, 0.0, GF - 12)
    b('Band_FlankBaseCap', -6.0, FACADE_T + 6.0, -8.0, D + 8.0, GF - 12, GF)
    if F >= 1:
        y0, y1 = 40.0, D - 40.0
        b('Glass_FlankCurtain', FACADE_T - 6.0, FACADE_T - 3.0,
          y0, y1, GF, ztop)
        b('Interior_FlankCurtain', FACADE_T - 15.0, FACADE_T - 9.0,
          y0, y1, GF, ztop)
        MULL = float(spec.get('mullion_step', 88.0))
        nm = max(2, int(round((y1 - y0) / MULL)))
        for k in range(nm + 1):
            my = y0 + (y1 - y0) * k / float(nm)
            mw = 11.0 if (k == 0 or k == nm) else 7.0
            b('Mullion_FlankV%d' % k, FACADE_T - 13.0, FACADE_T + 2.0,
              my - mw / 2, my + mw / 2, GF, ztop)
        for f in range(F):
            z0 = GF + f * FH
            b('Frame_FlankSpand%d' % f, FACADE_T - 4.0, FACADE_T + 4.0,
              y0, y1, z0 - 5, z0 + 20)
    b('Wall_FlankParapet', 0.0, FACADE_T, 0.0, D, ztop, ztop + PAR - 14)
    b('Band_FlankCoping', -7.0, FACADE_T + 7.0, -9.0, D + 9.0,
      ztop + PAR - 14, ztop + PAR)
    return made


def flank_modern(spec, sign, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """Late-modern side elevation: the same spandrel-band-and-ribbon language as
    the front, turned through 90 degrees.

    On a lot flagged corner=True the ground floor is an ARCADE RETURN rather
    than a blind plinth - the shopfront carries round the corner. That single
    move is what makes a corner building read as a corner instead of as two
    buildings meeting; it is why the flag exists.
    """
    import genbuild as _g
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    F, GF, FH, PAR = spec['floors'], spec['gf_h'], spec['fl_h'], spec['parapet']
    XP = (x0 - OVER_X - FACADE_T) if sign < 0 else (x0 + W + OVER_X + FACADE_T)
    ztop = GF + F * FH
    corner = bool(spec.get('corner'))
    face = 'W' if sign < 0 else 'E'
    a = mkactor('ELEV_%s_%s' % (n, face), origin, (0.0, yaw, 0.0))
    made = 0

    def xr(d0, d1):
        p, q = XP - sign * d0, XP - sign * d1
        return (p, q) if p <= q else (q, p)

    def b(name, d0, d1, y0, y1, z0, z1):
        nonlocal made
        ax0, ax1 = xr(d0, d1)
        box(a, name, ax0, ax1, y0, y1, z0, z1)
        made += 1

    Y0, Y1 = FRONT, D
    bays = max(2, int(round((Y1 - Y0) / 380.0)))
    bw = (Y1 - Y0) / float(bays)

    # ---- ground floor ------------------------------------------------------
    if corner:
        col_w = 64.0
        for k in range(bays + 1):
            py = min(Y0 + k * bw, Y1 - col_w)
            # stops at the soffit's UNDERSIDE, not its top face - the same
            # fault fixed on the front elevation's arcade. A column that runs
            # to GF passes through the slab it holds up.
            b('Wall_Col%d' % k, 0, 62, py, py + col_w, 0, GF - 14)
        b('Wall_Soffit', 0, _g.ARCADE, Y0 - 4, Y1 + 4, GF - 14, GF)
        b('Glass_Shop', _g.ARCADE, _g.ARCADE + 2, Y0 + col_w, Y1 - col_w, 26, GF - 20)
        b('Interior_Shop', _g.ARCADE + 16, _g.ARCADE + 22, Y0 + col_w - 6, Y1 - col_w + 6,
          22, GF - 16)
        for k in range(1, bays * 2):
            my = Y0 + col_w + (Y1 - Y0 - 2 * col_w) * k / float(bays * 2)
            b('Mullion_Shop%d' % k, _g.ARCADE - 5, _g.ARCADE + 1, my - 3, my + 3, 26, GF - 20)
    else:
        b('Wall_Plinth', -6, 66, Y0 - 6, Y1 + 6, 0, 30)
        b('Wall_Ground', 0, 60, Y0, Y1, 30, GF)

    # ---- upper floors ------------------------------------------------------
    for f in range(F):
        z0 = GF + f * FH
        z1 = z0 + FH
        sp = FH * _g.SPAND_F
        b('Band_L%dSpandrel' % f, -_g.BAND_PROUD, 20, Y0 - 7, Y1 + 7, z0 + 3, z0 + sp)
        b('Wall_L%dEndF' % f, -_g.BAND_PROUD - 4, 60, Y0 - 10, Y0 + 16, z0, z1)
        b('Wall_L%dEndR' % f, -_g.BAND_PROUD - 4, 60, Y1 - 16, Y1 + 10, z0, z1)
        gz0, gz1 = z0 + sp, z1
        gy0, gy1 = Y0 + 16, Y1 - 16
        b('Glass_L%dRibbon' % f, _g.GLAZE_Y, _g.GLAZE_Y + 2, gy0, gy1, gz0 + 4, gz1 - 4)
        b('Interior_L%dRibbon' % f, _g.GLAZE_Y + 8, _g.GLAZE_Y + 14, gy0, gy1, gz0, gz1)
        b('Frame_L%dRibbonS' % f, _g.GLAZE_Y - 8, _g.GLAZE_Y + 2, gy0 - 4, gy1 + 4, gz0 + 3, gz0 + 9)
        b('Frame_L%dRibbonT' % f, _g.GLAZE_Y - 8, _g.GLAZE_Y + 2, gy0 - 4, gy1 + 4, gz1 - 9, gz1 - 3)
        for k in range(1, bays):
            fy = gy0 + (gy1 - gy0) * k / float(bays)
            b('Wall_L%dFin%d' % (f, k), -_g.FIN_PROUD, _g.GLAZE_Y + 7,
              fy - _g.FIN_W / 2, fy + _g.FIN_W / 2, gz0, gz1)
        mz = gz0 + (gz1 - gz0) * 0.58
        b('Mullion_L%dRibbonH' % f, _g.GLAZE_Y - 9, _g.GLAZE_Y - 3, gy0, gy1, mz - 3, mz + 3)

    b('Wall_Parapet', 0, 40, Y0, Y1, ztop, ztop + PAR - 12)
    b('Band_Coping', -6, 44, Y0 - 6, Y1 + 6, ztop + PAR - 12, ztop + PAR)
    print('  ELEV_%s_%s [modern%s]: %d boxes'
          % (n, face, ', corner' if corner else '', made))
    return made


def flank_deco(spec, sign, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """Deco side elevation: the same pilaster-and-channel language turned 90
    degrees, with the stepped parapet returning round the corner.

    On a corner=True lot the base carries a shopfront return, so the storefront
    turns with the building instead of stopping at the quoin.
    """
    import genbuild as _g
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    F, GF, FH, PAR = spec['floors'], spec['gf_h'], spec['fl_h'], spec['parapet']
    XP = (x0 - OVER_X - FACADE_T) if sign < 0 else (x0 + W + OVER_X + FACADE_T)
    ztop = GF + F * FH
    corner = bool(spec.get('corner'))
    face = 'W' if sign < 0 else 'E'
    a = mkactor('ELEV_%s_%s' % (n, face), origin, (0.0, yaw, 0.0))
    made = 0

    def xr(d0, d1):
        p, q = XP - sign * d0, XP - sign * d1
        return (p, q) if p <= q else (q, p)

    def b(name, d0, d1, y0, y1, z0, z1):
        nonlocal made
        ax0, ax1 = xr(d0, d1)
        box(a, name, ax0, ax1, y0, y1, z0, z1)
        made += 1

    Y0, Y1 = FRONT, D
    bays = max(2, int(round((Y1 - Y0) / 400.0)))
    bw = (Y1 - Y0) / float(bays)
    PW = _g.DECO_PIL_W

    # ---- base --------------------------------------------------------------
    b('Wall_Plinth', -22, 66, Y0 - 8, Y1 + 8, 0, 46)
    # one list, so the corner shopfront bays derive from where the base piers
    # ACTUALLY are rather than from the grid the last one was clamped off.
    BPYS = [min(Y0 + k * bw, Y1 - PW) for k in range(bays + 1)]
    for k in range(bays + 1):
        py = BPYS[k]
        b('Wall_BasePier%d' % k, -_g.DECO_PROUD - 8, 62, py - 8, py + PW + 8, 46, GF - 46)
    # the front and rear caps oversail the corner by 16 in x; the flank
    # butts into them rather than running its own 16 through the same
    # corner. Y0/Y1 are the front and rear caps' inner faces.
    b('Band_BaseCap', -_g.DECO_PROUD - 16, 62, Y0, Y1, GF - 46, GF - 12)
    if corner:
        for k in range(bays):
            sy0, sy1 = BPYS[k] + PW, BPYS[k + 1]
            if sy1 - sy0 < 80: continue
            b('Glass_Shop%d' % k, 34, 36, sy0, sy1, 58, GF - 52)
            b('Interior_Shop%d' % k, 48, 54, sy0 - 6, sy1 + 6, 50, GF - 48)
            for j in (1, 2):
                my = sy0 + (sy1 - sy0) * j / 3.0
                b('Mullion_Shop%d_%d' % (k, j), 28, 35, my - 3, my + 3, 58, GF - 52)
    else:
        b('Wall_BaseInfill', 0, 60, Y0, Y1, 46, GF - 46)

    # ---- pilasters, full height -------------------------------------------
    # THE PILASTERS DECIDE WHERE THE BAYS ARE. Same fault as the front
    # elevation's clamped pier, third construct to carry it: the LAST
    # pilaster is clamped inward so it cannot overhang the corner, and the
    # bay beside it was still measured off the unclamped grid - so every
    # spandrel ran to where the pilaster WOULD have been and shared its far
    # face instead of butting against its near one. 1,044 pairs across 75
    # models, the largest mechanism left.
    pys = [min(Y0 + k * bw, Y1 - PW) for k in range(bays + 1)]
    for k, py in enumerate(pys):
        # end pilasters wrap the corner - see the note on the front face
        b('Wall_Pilaster%d' % k, -_g.DECO_PROUD, 60,
          py - (_g.DECO_CORNER_WRAP if k == 0 else 0.0),
          py + PW + (_g.DECO_CORNER_WRAP if k == bays else 0.0),
          GF - 12, ztop + PAR - 26)
        for j in (1, 2):
            fy = py + PW * j / 3.0
            b('Band_Flute%d_%d' % (k, j), -_g.DECO_PROUD - 9, -_g.DECO_PROUD + 4,
              fy - _g.DECO_FLUTE/2, fy + _g.DECO_FLUTE/2, GF - 4, ztop + PAR - 40)

    # ---- floors ------------------------------------------------------------
    for f in range(F):
        z0, z1 = GF + f * FH, GF + (f + 1) * FH
        for k in range(bays):
            wy0, wy1 = pys[k] + PW, pys[k + 1]
            if wy1 - wy0 < 80: continue
            b('Frame_L%dSpandrel%d' % (f, k), 18, 30, wy0, wy1, z0, z0 + FH * 0.24)
            wz0, wz1 = z0 + FH * 0.24, z1
            b('Glass_L%dB%d' % (f, k), _g.DECO_GLAZE, _g.DECO_GLAZE + 2,
              wy0 + 5, wy1 - 5, wz0 + 5, wz1 - 5)
            b('Interior_L%dB%d' % (f, k), _g.DECO_GLAZE + 10, _g.DECO_GLAZE + 16,
              wy0, wy1, wz0, wz1)
            b('Frame_L%dB%dL' % (f, k), _g.DECO_GLAZE - 6, _g.DECO_GLAZE + 2,
              wy0, wy0 + 5, wz0, wz1)
            b('Frame_L%dB%dR' % (f, k), _g.DECO_GLAZE - 6, _g.DECO_GLAZE + 2,
              wy1 - 5, wy1, wz0, wz1)
            my = (wy0 + wy1) / 2.0
            b('Mullion_L%dB%dV' % (f, k), _g.DECO_GLAZE - 5, _g.DECO_GLAZE + 1,
              my - 3, my + 3, wz0, wz1)

    # ---- stepped parapet returns round the corner --------------------------
    mid = bays // 2
    steps = [PAR * (1.9 if k == mid else (1.35 if abs(k - mid) == 1 else 1.0))
             for k in range(bays)]
    # same clamped-neighbour fault as the front: the pilasters stand on pys,
    # so a segment taken off the raw grid starts on a pilaster's face. Step
    # at the pilaster centre; ends stay on the corners.
    bnd = [Y0] + [pys[k] + PW * 0.5 for k in range(1, bays)] + [Y1]
    for k in range(bays):
        py0, py1 = bnd[k], bnd[k + 1]
        step = steps[k]
        b('Wall_Parapet%d' % k, -18, 34, py0, py1, ztop, ztop + step)
        # oversail only where the cap actually steps. Two caps at the SAME
        # height each reaching 8 past the boundary share both y faces and
        # fight over 16 uu; at a step there is no z overlap to fight over.
        lo = py0 - 8 if (k == 0 or steps[k - 1] != step) else py0
        hi = py1 + 8 if (k == bays - 1 or steps[k + 1] != step) else py1
        b('Band_Cap%d' % k, -28, 42, lo, hi, ztop + step, ztop + step + 16)
    print('  ELEV_%s_%s [deco%s]: %d boxes'
          % (n, face, ', corner' if corner else '', made))
    return made
