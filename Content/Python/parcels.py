"""Parcel widths, assembly, and which tiers a parcel can reach. Pure data.

THE MECHANIC. A building grows vertically only as far as its land allows. Past
that it has to grow HORIZONTALLY first - which means acquiring the parcel next
door and knocking down what stands on it. Owner's direction, 2026-08-26: "not
all buildings grow vertically in real life".

That turns a tier ladder into a decision. A tower on an M parcel tops out as a
low block; reaching landmark means assembling up to XXL, and the neighbour is
somebody's building.

THE MODULE MAKES IT WORK. Widths are multiples of 410, and lots tile edge to
edge, so merging two adjacent lots always lands EXACTLY on another ladder
width - no offcuts, no special cases:

    S + S = L        S + M = XL       M + M = XXL
    S + L = XXL      M + L = XXXL     S + XL = XXXL

That is checked below rather than asserted in prose.
"""
MODULE = 410.0

LADDER = [
    ('S',    2),
    ('M',    3),
    ('L',    4),
    ('XL',   5),
    ('XXL',  6),
    ('XXXL', 7),
]
WIDTH = {n: k * MODULE for n, k in LADDER}
NAME = {v: k for k, v in WIDTH.items()}
ORDER = [n for n, _ in LADDER]


def width_of(name):
    return WIDTH[name]


def name_of(width):
    """Ladder name for a width, or None if it is not on the ladder."""
    for n, w in WIDTH.items():
        if abs(w - width) < 0.5:
            return n
    return None


def merges_to(name):
    """[(a, b)] pairs of adjacent parcels that assemble into `name`."""
    k = dict(LADDER)[name]
    out = []
    for a, ka in LADDER:
        for b, kb in LADDER:
            if b < a or ka + kb != k:
                continue
            out.append((a, b))
    return out


def can_reach(recipe, parcel_width, tier):
    """Does a parcel of this width support this tier of this recipe?"""
    tiers = recipe['tiers']
    if tier >= len(tiers):
        return False
    need = tiers[tier].get('needs')
    return True if not need else parcel_width + 0.5 >= WIDTH[need]


def max_tier(recipe, parcel_width):
    """The highest tier this parcel can carry. -1 if it cannot carry any."""
    best = -1
    for t in range(len(recipe['tiers'])):
        if can_reach(recipe, parcel_width, t):
            best = t
        else:
            break
    return best


def acquire_options(recipe, parcel_width):
    """What could I buy NEXT DOOR, and what would it unlock?

    The first version answered the wrong question. Asked what an M parcel
    needs, it replied "L, assembled from S+S" - true, and useless to somebody
    who already holds an M. The player's question is which NEIGHBOUR to take.

    Note assembly OVERSHOOTS, and that is a real consequence of the module
    rather than a flaw: the smallest lot on the ladder is 2 modules, so an M
    (3) cannot become an L (4) at all - the smallest neighbour it can take is
    an S, which lands it on XL (5) and skips a rung. Land comes in lots, not
    in slices.
    """
    out = []
    for n, k in LADDER:
        merged = parcel_width + WIDTH[n]
        if not name_of(merged):
            continue                      # off the top of the ladder
        t = max_tier(recipe, merged)
        if t > max_tier(recipe, parcel_width):
            out.append(dict(acquire=n, acquire_uu=WIDTH[n],
                            becomes=name_of(merged), becomes_uu=merged,
                            unlocks_tier=t,
                            unlocks=recipe['tiers'][t]['name']))
    return out


def blocked_by(recipe, parcel_width):
    """(next tier, the width it needs, and what to acquire) or None if maxed."""
    t = max_tier(recipe, parcel_width) + 1
    if t >= len(recipe['tiers']):
        return None
    need = recipe['tiers'][t].get('needs')
    return dict(tier=t, name=recipe['tiers'][t]['name'], needs=need,
                needs_uu=WIDTH[need] if need else 0.0, have=parcel_width,
                acquire=acquire_options(recipe, parcel_width))


def _selftest():
    # the module's whole promise: two lots always merge onto the ladder
    for a, ka in LADDER:
        for b, kb in LADDER:
            s = (ka + kb) * MODULE
            if (ka + kb) <= LADDER[-1][1]:
                assert name_of(s), 'merge %s+%s = %.0f is off-ladder' % (a, b, s)
    assert merges_to('L') == [('S', 'S')]
    assert ('M', 'M') in merges_to('XXL')
    assert name_of(2460.0) == 'XXL'
    assert name_of(1000.0) is None

    demo = dict(tiers=[dict(name='a'), dict(name='b', needs='M'),
                       dict(name='c', needs='L'), dict(name='d', needs='XXL')])
    assert max_tier(demo, WIDTH['S']) == 0
    assert max_tier(demo, WIDTH['M']) == 1
    assert max_tier(demo, WIDTH['L']) == 2
    assert max_tier(demo, WIDTH['XXL']) == 3
    b = blocked_by(demo, WIDTH['M'])
    assert b['tier'] == 2 and b['needs'] == 'L', b
    assert blocked_by(demo, WIDTH['XXL']) is None
    # M cannot become L: the smallest neighbour is S, which overshoots to XL
    opts = acquire_options(demo, WIDTH['M'])
    assert opts, 'an M parcel must have some way forward'
    assert all(o['becomes'] != 'L' for o in opts), opts
    assert opts[0]['acquire'] == 'S' and opts[0]['becomes'] == 'XL', opts[0]
    # a maxed parcel offers nothing
    assert acquire_options(demo, WIDTH['XXL']) == []
    return True


if __name__ == '__main__':
    print('parcels self-test:', _selftest())
    for n, k in LADDER:
        m = merges_to(n)
        print('  %-5s %5.0f uu (%4.1f m)   assemble from: %s'
              % (n, WIDTH[n], WIDTH[n]/100.0,
                 ', '.join('%s+%s' % p for p in m) or '(base lot)'))
