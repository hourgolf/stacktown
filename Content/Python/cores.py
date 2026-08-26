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
FACADE_BACK = 60.0
CLEAR = 2.0
OVER_Z = 14.0
OVER_X = 8.0


def bands_for(spec, arcade=0.0):
    """[(z0, z1, front)] for one building. `front` is the core's front plane."""
    GF = spec['gf_h']
    FH = spec['fl_h']
    FL = spec['floors']
    PAR = spec.get('parapet', 0.0)
    sb = spec.get('setback') or 0.0
    # setback_floors did not exist when this was written: step_cores3 assumed
    # only the TOP floor ever set back and two bands sufficed. A stepped crown
    # needs one band per stepped floor, or the core stands proud of the floors
    # it is supposed to sit behind.
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
            d = FL - 1 - f
            back = sb * (sbf - d)
            z0 = GF + f * FH
            z1 = (GF + (f + 1) * FH) if k < nsb - 1 else (ztop + PAR + OVER_Z)
            out.append((max(z0, z), z1, back + FACADE_BACK + CLEAR))
    else:
        out.append((z, ztop + PAR + OVER_Z, FACADE_BACK + CLEAR))
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
