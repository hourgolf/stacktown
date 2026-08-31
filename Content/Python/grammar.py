"""Which recipe belongs on this parcel?

The owner's call was a mix: certain buildings the player places directly, and
zoned or organic areas where a GRAMMAR picks something that fits the
neighbourhood. This is that grammar, and it is deliberately small - it answers
one question, "what could stand here", and ranks the answers.

Pure functions, no Unreal import, so it can be exercised and self-tested
without an editor. Same reason citygeom, zonelayout and paths are pure.
"""
import random
import recipes


def candidates(width, depth, district=None):
    """Every recipe that could physically stand on this parcel."""
    out = []
    for rid, r in sorted(recipes.RECIPES.items()):
        if district and district not in r['district']:
            continue
        if r['fits'](width, depth):
            out.append(rid)
    return out


def pick(width, depth, district=None, level=0.0, seed=0):
    """(recipe id, tier) for a parcel.

    `level` is how developed this part of the city is, 0..1. It selects the
    TIER, not the recipe: a neighbourhood does not swap its houses for
    different houses as it grows, it grows the ones it has. That is the same
    property the tier system exists to protect.
    """
    c = candidates(width, depth, district)
    if not c:
        return None
    rnd = random.Random(seed)
    rid = c[rnd.randrange(len(c))]
    n = recipes.tier_count(rid)
    tier = min(n - 1, max(0, int(round(level*(n - 1)))))
    return rid, tier


if __name__ == '__main__':
    # KNOWN ANSWERS against the CURRENT recipe set. A grammar that returns
    # something for everything is not a grammar, so the negative case matters
    # as much as the positive. The previous answers asserted the retired
    # cottage/walkup rows and threw on every run - a self-check that cannot
    # pass is a self-check nobody is running.
    assert candidates(1230.0, 700.0, 'commercial') == ['vernacular'], \
        candidates(1230.0, 700.0, 'commercial')
    assert candidates(1230.0, 700.0, 'residential') == [], \
        'no residential recipe is live; the drafts are parked'
    assert candidates(400.0, 400.0) == [], candidates(400.0, 400.0)
    assert candidates(1230.0, 500.0) == [], 'a shallow parcel fits nothing'
    # level drives the tier, not the recipe (vernacular has 6 tiers, t0..t5)
    assert pick(1230.0, 700.0, 'commercial', level=0.0)[1] == 0
    assert pick(1230.0, 700.0, 'commercial', level=1.0)[1] == 5
    rid_lo = pick(1230.0, 700.0, 'commercial', level=0.0, seed=7)[0]
    rid_hi = pick(1230.0, 700.0, 'commercial', level=1.0, seed=7)[0]
    assert rid_lo == rid_hi, 'growing a parcel must not change what stands on it'
    print('grammar.py self-check: pass')
