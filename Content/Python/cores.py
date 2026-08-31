"""Where a building's solid CORE sits, as bands. Pure - no `unreal` import.

A generated commercial building is a FACADE and a roof: piers, band courses,
glazing and thin interior plates behind each opening, with nothing between
them. In a terrace that is invisible, because you only ever see the front.
Give the same model flanks and a rear and stand it on its own and it reads as
a hollow shell of four skins - which is exactly how the first freestanding
vernacular bake came out: you could see straight through it.

step_cores3.py has always fixed this for the city and bake_catalogue never
ran it, which is the same omission as the elevations.

BANDS, not one box. A single core sized from the deepest floor leaves a void
behind every other one - invisible head-on and obvious at an oblique angle.
"""
# THE DETACHED STYLES. A house, a walkup and a works each build one solid
# `Wall_Body` with four real walls of their own - they are buildings, not
# facade shells - so they need no core behind them. step_elevations has always
# known this (it excludes them from flanks, twice) and cores never did, which
# means adding a recipe for any of them would have put a redundant solid core
# inside an already-solid building AND buried its roof, exactly the way the
# core buried every flat roof in the catalogue.
#
# One list, in the module that owns what a core is. step_elevations imports it
# rather than keeping its own copy - the same reason setback_at exists.
DETACHED = ('house', 'walkup', 'works')


def is_detached(spec):
    return spec.get('style') in DETACHED


FACADE_BACK = 60.0
CLEAR = 2.0
OVER_Z = 14.0
OVER_X = 8.0


# CLEARANCE UNDER THE ROOF DECK. `open_roof` first capped the core at exactly
# ztop - and every flat roof in the catalogue puts its deck at ztop-8..ztop,
# its parapet base at ztop, and its top-floor wall boxes ending at ztop. So
# the core's top face sat COPLANAR with three different surfaces at once and
# the depth buffer had nothing to choose between them: jagged white patches
# across every roof, moving frame to frame. That is what the owner had been
# reporting as "flickering", and it was not Lumen at all - Lumen was a
# separate, much smaller drift that sat on top of it.
#
# Two coplanar faces are not a lighting problem and no amount of GI tuning
# will fix one. The core stops CLEAR of the deck instead. The gap is enclosed
# by the facade and covered by the deck, so it is never visible.
# A HALF UNIT, deliberately. 14.0 cleared the deck but landed exactly on
# contemporary4's `Band_StackCap` bottom (ztop-14) and on modern's roof
# coffers - because all hand-authored geometry in this codebase is written in
# whole numbers, so any whole-number clearance can collide with one of them by
# arithmetic accident. A .5 offset cannot: nothing else in the catalogue can
# ever land on it. That is a property, not a lucky value.
ROOF_CLEAR = 17.5


def _cap(spec, ztop, PAR):
    """Top of the core: clear under the roof deck if the style closes its own
    roof, else above the parapet."""
    return (ztop - ROOF_CLEAR) if spec.get('open_roof') else (ztop + PAR + OVER_Z)


def core_top(spec):
    """Where the core actually ends, for anything that must sit above it."""
    ztop = spec['gf_h'] + spec['floors'] * spec['fl_h']
    return _cap(spec, ztop, spec.get('parapet', 0.0))


def setback_at(spec, f, F=None):
    """How far floor `f` sits back from the facade line. THE resolver.

    P12. This formula was written out four separate times - here, in
    build_modern (twice) and in build_contemporary - and the core's copy is
    the one every other copy has to agree with, because the core is the solid
    mass sitting behind the floors. When contemporary first stepped its
    volumes it used a private `shift` key, the core did not step with it, and
    the building's top three storeys came out as a blank slab: the core's
    front face WAS the elevation. One function now, and everything reads it.

    TWO MODES:

      progressive (default) - each stepping floor sits back one more `sb`
        than the floor below, so the mass tapers or ziggurats. Cumulative:
        `setback_floors` of 8 at sb 100 is 800 uu of setback, which is how
        `modern6` drawn as a podium came out 991 deep on an 820-deep building
        and was refused by GATE-05.

      constant - every stepping floor sits back the SAME `sb`. One step, not
        a stair: which is what a PODIUM AND TOWER actually is, and what could
        not be expressed at all before this.
    """
    sb = float(spec.get('setback') or 0.0)
    if not sb:
        return 0.0
    if F is None:
        F = int(spec.get('floors') or 0)
    sbf = max(1, int(spec.get('setback_floors', 1)))
    nsb = min(sbf, F)
    if f < F - nsb:
        return 0.0
    if str(spec.get('setback_mode', 'progressive')) == 'constant':
        return sb
    d = F - 1 - f
    return sb * (sbf - d)


def setback_top(spec, F=None):
    """The largest setback anywhere on the building - what the roof sits at."""
    if F is None:
        F = int(spec.get('floors') or 0)
    return max([0.0] + [setback_at(spec, f, F) for f in range(F)])


def bands_for(spec, arcade=0.0):
    """[(z0, z1, front)] for one building. `front` is the core's front plane.

    A DETACHED style gets no bands at all - see DETACHED above.

    OPEN ROOF. The core normally tops out at ztop + parapet + OVER_Z so that
    nothing shows through the parapet from an oblique angle. The side effect
    is that it fills the ROOF VOID solid: Roof_Deck (ztop-8..ztop), the garden
    deck, and everything standing on them are inside the core and invisible.
    Every roof in the catalogue was the core's top face wearing the WALL
    material, which is why roofs took the building's colour and why `roofmat`
    never showed. A 90 uu roof lawn was swallowed whole; at 200 uu it cleared
    the core and abruptly "worked", which is what made the bug look like a
    material fault for so long.

    `open_roof` caps the core at ztop instead. A style that sets it MUST close
    its own roof void - a rear parapet as well as front and sides - or the
    building is see-through from behind at roof level.
    """
    GF = spec['gf_h']
    FH = spec['fl_h']
    FL = spec['floors']
    PAR = spec.get('parapet', 0.0)
    sb = spec.get('setback') or 0.0
    # setback_floors did not exist when this was written: step_cores3 assumed
    # only the TOP floor ever set back and two bands sufficed. A stepped crown
    # needs one band per stepped floor, or the core stands proud of the floors
    # it is supposed to sit behind.
    if is_detached(spec):
        return []
    sbf = max(1, int(spec.get('setback_floors', 1)))
    ztop = GF + FL * FH
    out = []
    z = 0.0
    if arcade:
        out.append((0.0, GF, FACADE_BACK + CLEAR + arcade))
        z = GF
    if sb > 0 and FL > 0:
        nsb = min(sbf, FL)
        zsplit = GF + (FL - nsb) * FH
        if zsplit > z:
            out.append((z, zsplit, FACADE_BACK + CLEAR))
        for k in range(nsb):
            f = FL - nsb + k
            back = setback_at(spec, f, FL)
            z0 = GF + f * FH
            z1 = (GF + (f + 1) * FH) if k < nsb - 1 else _cap(spec, ztop, PAR)
            out.append((max(z0, z), z1, back + FACADE_BACK + CLEAR))
    else:
        out.append((z, _cap(spec, ztop, PAR), FACADE_BACK + CLEAR))
    return [(a, b, c) for a, b, c in out if b > a]


def build_core(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """Build the core bands as an ACTOR AT THE ORIGIN with local boxes.

    The first version spawned StaticMeshActors at world positions, the way
    step_cores3 does for the city. bake_merge appends each component by its
    RELATIVE transform - which is local for a genbuild actor and effectively
    WORLD for a root StaticMeshComponent - so the merged mesh came out
    1230 x 60758 uu: the core sat 60,000 away at the staging origin.

    Built through genbuild's own mkactor/box so a core is the same kind of
    thing as every other part of the building, and the component carries a
    ROLE name so the one sweep binds it like everything else.
    """
    from genbuild import mkactor, box          # imported here: cores.py must
    #                                            stay importable without an
    #                                            editor for its self-test
    if spec.get('style') == 'house':
        return 0
    arcade = 0.0
    if spec.get('style') == 'modern':
        import genbuild as _g
        arcade = _g.ARCADE
    a = mkactor('CORE_%s' % spec['name'], origin, (0.0, yaw, 0.0))
    x0, W = spec['x0'], spec['width']
    made = 0
    for i, (z0, z1, front) in enumerate(bands_for(spec, arcade)):
        depth = max(80.0, spec['depth'] - front)
        box(a, 'Wall_Core%d' % i, x0 - OVER_X, x0 + W + OVER_X,
            front, front + depth, z0, z1)
        made += 1
    return made


def _selftest():
    """Known answers, because a core in the wrong place is invisible until an
    oblique angle finds it."""
    flat = dict(gf_h=340.0, fl_h=280.0, floors=2, parapet=45.0)
    b = bands_for(flat)
    assert len(b) == 1, b
    assert abs(b[0][2] - (FACADE_BACK + CLEAR)) < 1e-6, b

    one = dict(flat, floors=3, setback=90.0)          # legacy: top floor only
    b = bands_for(one)
    assert len(b) == 2, b
    assert abs(b[1][2] - (90.0 + FACADE_BACK + CLEAR)) < 1e-6, b

    two = dict(flat, floors=4, setback=90.0, setback_floors=2)
    b = bands_for(two)
    assert len(b) == 3, b                              # base + two stepped
    assert abs(b[1][2] - (90.0 + FACADE_BACK + CLEAR)) < 1e-6, b
    assert abs(b[2][2] - (180.0 + FACADE_BACK + CLEAR)) < 1e-6, b
    assert b[1][0] < b[1][1] <= b[2][0], b             # stacked, no overlap
    return True


if __name__ == '__main__':
    print('cores self-test:', _selftest())
