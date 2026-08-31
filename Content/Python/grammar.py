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
    """Every recipe the grammar may CHOOSE for this parcel.

    Not the same set as "every recipe that could physically stand here".
    CIVIC recipes are excluded outright (owner, 2026-08-31): a core gameplay
    landmark is sited deliberately, by explicit request, and must never be
    sprinkled onto a parcel because its dimensions happened to fit. The
    office fits a 1640..2460 band and appears in none of these lists.

    The filter reads `recipes.AUTO_PLACED` rather than testing for 'civic',
    so the role vocabulary has exactly one authority.
    """
    out = []
    for rid, r in sorted(recipes.RECIPES.items()):
        if r['role'] not in recipes.AUTO_PLACED:
            continue
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
    # --- CIVIC IS NEVER AUTO-PICKED (owner, 2026-08-31) -------------------
    #
    # THE KNOWN-ANSWER PAIR, and the second half is the sharp one. Asserting
    # that office is absent from a parcel it does not FIT would prove nothing
    # - `fits` would be doing the work and the role filter could be deleted
    # without this test noticing. So the width below sits INSIDE the office's
    # own declared band (1640..2460) at a depth it accepts, which is exactly
    # the case where the two rules disagree: it fits, and it must still never
    # be offered.
    assert recipes.RECIPES['office']['fits'](2050.0, 1600.0), \
        'the sharp case has gone blunt: office no longer fits its own band, ' \
        'so the assertion below would pass for the wrong reason'
    assert 'office' not in candidates(2050.0, 1600.0), \
        'a civic recipe was auto-picked'
    assert 'office' not in candidates(2050.0, 1600.0, 'mixed'), \
        'a civic recipe was auto-picked in its own district'
    # and the positive half: an ordinary parcel still resolves normally
    assert pick(2050.0, 1600.0) is not None, \
        'excluding civic must not empty an ordinary parcel'
    print('grammar.py self-check: pass')
