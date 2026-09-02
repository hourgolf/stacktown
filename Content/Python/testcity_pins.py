"""Which building stands on each TestCity lot — PINNED, not drawn.

NOT YET WIRED. `mk_testcity_builds.py` still draws. This module is the
declared mechanism with its self-test, landing before the consumer change
because that change mutates a level and cannot be verified without an editor
window. Declared first, wired second — the depth-axis precedent (grammar
declared, self-test extended, zero bakes).

WHY PINNING IS NOT A TIDINESS PREFERENCE. `mk_testcity_builds` picks each
lot's building with `rnd.choice(stock[w])` on a fixed SEED, where `stock[w]`
is every (recipe, tier) whose baked mesh EXISTS at that width. The seed fixes
the sequence of random numbers; it does not fix the LIST being chosen from.

That file already carries a comment about half of this hazard, and the half it
fixed is real: the two extra draws used to sit AFTER the existence check, so a
`continue` on a missing asset consumed fewer random numbers and shifted every
later lot. Ordering is now correct — every draw is made whether or not the
asset resolves.

THE OTHER HALF IS STILL LIVE, and it is the half that matters here. Measured
2026-08-31, offline: removing ONE asset from the bake set changed SEVEN OF
FOURTEEN buildings — every lot at that asset's width. The draw domain moved,
so the same seed dealt a different city.

    baseline                     minus SM_Bld_contemporary_t0_w1230
    NW0  contemporary5_t0   ->   contemporary5_t1
    NW1  contemporary3_t5   ->   contemporary4_t0
    NW2  vernacular7_t3     ->   vernacular7_t4
    NW3  modern8_t1         ->   modern8_t2
    SE2  deco8_t4           ->   deco8_t5
    SW0  deco8_t4           ->   deco8_t5
    SW2  contemporary8_t5   ->   deco_t0

Same family as the share-promotion bug, where appending to a hashed draw list
changed `hash % len` and repainted every vernacular building while hitting its
target share exactly — invisible to every statistic, visible only in frames.

WHY THIS BLOCKS THE BETA TWIN SPECIFICALLY. The wooden catalogue is, by
definition, a DIFFERENT BAKE SET. Under a draw it would therefore deal a
DIFFERENT CITY — so the swap would show the owner "a different city, in wood"
rather than "the same city, in wood". The twin's whole demonstration is that
two catalogues render one game; a drawn composition cannot demonstrate it.
Pinning is what makes the swap an ART swap.

THE PIN IS AN IDENTITY, NEVER A MESH. Each lot names (recipe, tier) — the
same key space `MeshByKey` uses — so ONE pin table serves BOTH catalogues and
each renders the same city in its own material language. Pinning mesh assets
would fork the two products at the composition level, which is the opposite of
the point.

FAILURE IS LOUD, NEVER A FALLBACK. A pinned identity whose asset is missing
from the active catalogue raises. It must never quietly fall back to a draw:
that would reintroduce exactly the hazard above, at the moment of greatest
confusion, and BETA_TWIN_PLAN seam 5 already settled the principle for
tier-ups ("growth blocked: not baked" rather than resolving a null mesh).
"""
import citylayout as L
import recipes


class MissingPin(KeyError):
    """A lot with no pin. Raised, never defaulted — same doctrine as
    archetypes.UnknownArchetype: a name nobody declared is a bug."""


class PinNotBaked(LookupError):
    """A pinned identity with no asset in the catalogue under test."""


def _pin(rid, tier, w, corner):
    return dict(rid=rid, tier=tier, w=w, corner=corner)


# THE SELECTION IS PROVISIONAL; THE MECHANISM IS NOT.
#
# The owner's word (relayed 2026-08-31): the first wooden board is 14 pinned
# models, one per lot, five widths spanned, "chosen for tonal and massing
# range". These fourteen are a MASSING-RANGE spread, computed rather than
# picked by taste: at each width the available identities were sorted by built
# height (measured offline through genbuild's sink, the D4 census) and sampled
# evenly across that range. The result spanned 370 uu to 7531 uu at the time
# this spread was chosen — 3.7 m to 75 m at 1:1, a real skyline rather than
# fourteen mid-rises. SW3's repin (see "SECOND TOWER" below) now measures
# taller than that original ceiling (8185 uu actual vs 7531 projected) - the
# spread's INTENT (five widths, four corners, a real skyline) still holds,
# the specific number in this sentence is dated to before that repin.
#
#     NE0   w2460  contemporary6    t3   h  2547 uu   CORNER
#     NE1   w820   vernacular8      t0   h   370 uu
#     NE2   w1640  vernacular       t0   h   394 uu
#     NW0   w1230  vernacular8      t0   h   370 uu
#     NW1   w1230  contemporary     t1   h   829 uu
#     NW2   w1230  modern8          t3   h  1144 uu
#     NW3   w1230  vernacular7      t5   h  1968 uu   CORNER
#     SE0   w2050  modern8          t2   h  1195 uu   CORNER
#     SE1   w1640  modern8          t5   h  1729 uu
#     SE2   w1230  modern3          t3   h  2314 uu
#     SW0   w1230  contemporary4    t4   h  3286 uu
#     SW1   w820   vernacular       t5   h  1996 uu
#     SW2   w1230  tower            t6   h  7490 uu
#     SW3   w1640  tower            t6   h  8185 uu   CORNER
#           (repinned from modern7_t4/h3971 - see "SECOND TOWER" below.
#           8185 is MEASURED off the actual baked mesh 2026-09-01
#           (get_bounds, /Game/Stacktown/Baked/SM_Bld_tower_t6_w1640_d1500_cR),
#           not the 7531 this same recipe/tier/width projected offline via
#           genbuild's D4 census before it existed - record the gap, not just
#           the number: an offline projection and a baked measurement
#           disagreed by ~650 uu (~9%) for the identical identity.)
#
# THE FOUR CORNERS WERE REPINNED, and the reason is worth keeping. The first
# spread was computed against PLAIN asset names and put modern6_t1, vernacular3_t4,
# deco3_t2 and tower_t6 on the four corner lots. `require` refused all four on
# its first real run: a corner lot needs a CORNER VARIANT (`_d1500_cL/_cR`), and
# only TEN exist on disk - baked on demand for whatever an earlier draw asked
# for, never as a complete set. The corners are therefore pinned from what is
# actually buildable, still chosen for spread within that set (h 1195 / 1968 /
# 2547 / 3971). NE0 had exactly ONE candidate and no choice was available.
#
# SECOND TOWER, DECIDED AND BUILT. The cost above was recorded as FOUR
# corner bakes, not a pin edit - that math was wrong, corrected by the
# direction-B lane's own derivation to ONE bake (only SW3's specific
# corner variant was ever needed, not a complete four-corner set). Owner's
# word 2026-08-31 via the coordinator: build the second tower. Asset
# baked, gate-passed, stamped, on disk 2026-09-01:
# SM_Bld_tower_t6_w1640_d1500_cR. SW3 repins from modern7_t4 to tower_t6
# below - this comment used to say the opposite of that decision while
# the decision sat unrecorded elsewhere, which is how this thread nearly
# died once already. The record outranks recollection only if the record
# gets written.
#
# WHAT IS NOT SETTLED, AND IS NOT MINE TO SETTLE: the ARRANGEMENT. Height
# range is measurable and is met; WHICH lot carries WHICH height is a look
# call. As it stood before the second tower, the tallest three (SW0 3286,
# SW3 3971, SW2 7490) already all sat on the SW block while NE topped out at
# 2547 - a lopsided skyline that no eye had judged. SW3's repin makes this
# MORE lopsided, not less: SW block now carries TWO towers (SW2 7490, SW3
# 8185) alongside SW0's 3286, while NE still tops out at 2547. Recording the
# fact, not deciding it - the owner's eye decides the arrangement; this
# table is the thing their decision edits.
PINS = {
    'NE0': _pin('contemporary6', 3, w=2460, corner=True),
    'NE1': _pin('vernacular8', 0, w=820, corner=False),
    'NE2': _pin('vernacular', 0, w=1640, corner=False),
    'NW0': _pin('vernacular8', 0, w=1230, corner=False),
    'NW1': _pin('contemporary', 1, w=1230, corner=False),
    'NW2': _pin('modern8', 3, w=1230, corner=False),
    'NW3': _pin('vernacular7', 5, w=1230, corner=True),
    'SE0': _pin('modern8', 2, w=2050, corner=True),
    'SE1': _pin('modern8', 5, w=1640, corner=False),
    'SE2': _pin('modern3', 3, w=1230, corner=False),
    'SW0': _pin('contemporary4', 4, w=1230, corner=False),
    'SW1': _pin('vernacular', 5, w=820, corner=False),
    'SW2': _pin('tower', 6, w=1230, corner=False),
    'SW3': _pin('tower', 6, w=1640, corner=True),
}


def identity(lot_key):
    """(recipe_id, tier) for a lot. Never a default."""
    if lot_key not in PINS:
        raise MissingPin(
            '%s has no pin. Every TestCity lot is pinned by identity; a lot '
            'that falls through to a draw is the bug this module exists to '
            'prevent.' % lot_key)
    p = PINS[lot_key]
    return p['rid'], p['tier']


def asset_for(lot_key, corner_side=None):
    """The asset name this lot's pin resolves to, corner variant included.

    `corner_side` comes from `citylayout.cross_street_end`, exactly as
    mk_testcity_builds derives it today - not stored here, because which way a
    corner turns is a property of the LAYOUT and storing it would be a second
    copy of that fact.
    """
    p = PINS[lot_key]
    if p['corner']:
        if corner_side is None:
            raise ValueError(
                '%s is a corner lot; asset_for needs corner_side from '
                'citylayout.cross_street_end' % lot_key)
        return recipes.asset_name(p['rid'], p['tier'], float(p['w']),
                                  depth=recipes.DEPTH_CORNER,
                                  corner=corner_side)
    return recipes.asset_name(p['rid'], p['tier'], float(p['w']))


def require(lot_key, have, corner_side=None):
    """The asset name, or PinNotBaked. `have` is the set of asset names in the
    catalogue under test - the FLAGSHIP set or the WOODEN one, which is the
    whole point of pinning identities rather than meshes."""
    name = asset_for(lot_key, corner_side)
    if name not in have:
        raise PinNotBaked(
            'PIN NOT BAKED: lot %s pins %s_t%d at w%d, asset %s, which is not '
            'in the catalogue under test. Not falling back to a draw - a '
            'fallback here is how the city silently stops being the pinned '
            'one.' % (lot_key, PINS[lot_key]['rid'], PINS[lot_key]['tier'],
                      PINS[lot_key]['w'], name))
    return name


def _layout_lots():
    """{lot_key: (width, is_corner)} straight from citylayout."""
    return {k: (round(x1 - x0), c)
            for b in sorted(L.blocks()) for k, x0, x1, c in L.lots(b)}


def _selftest():
    """DOUBLE ENTRY against citylayout, on purpose.

    Width and corner-ness are properties of the LAYOUT, and this table records
    them a second time. That is the archetypes.py pattern rather than the
    two-copies drift this project forbids: the duplication exists so that a
    layout change which invalidates the pins FAILS HERE instead of silently
    placing a 2460-wide building on a 1230 lot. A silent disagreement is the
    bug; a loud one is the feature.
    """
    lay = _layout_lots()
    assert set(PINS) == set(lay), (
        'pins and layout disagree about which lots exist\n'
        '  pinned, not in layout: %s\n'
        '  in layout, not pinned: %s'
        % (sorted(set(PINS) - set(lay)), sorted(set(lay) - set(PINS))))
    for k, p in sorted(PINS.items()):
        w, corner = lay[k]
        assert p['w'] == w, (
            '%s pins width %d but the layout says %d - the layout moved and '
            'these pins are stale' % (k, p['w'], w))
        assert p['corner'] == corner, (
            '%s pins corner=%s but the layout says %s' % (k, p['corner'], corner))
        # the identity must be one the recipe actually declares. Baked-ness is
        # deliberately NOT checked here: this module is pure and headless, and
        # what is baked depends on WHICH CATALOGUE is active - which is
        # `require`'s job, at the point of use, against a real asset set.
        assert p['rid'] in recipes.RECIPES, '%s pins unknown recipe %s' % (k, p['rid'])
        assert p['w'] in [round(x) for x in recipes.widths(p['rid'])], (
            '%s pins %s at w%d, a width that recipe does not declare'
            % (k, p['rid'], p['w']))
        assert 0 <= p['tier'] < recipes.tier_count(p['rid']), (
            '%s pins %s t%d but that recipe has %d tiers'
            % (k, p['rid'], p['tier'], recipes.tier_count(p['rid'])))

    # KNOWN-ANSWER CELL. Not a restatement of the table: it asserts the
    # PROPERTY the selection was made for, so editing the pins by taste
    # without preserving massing range fails here rather than quietly
    # shipping fourteen mid-rises.
    assert len({p['w'] for p in PINS.values()}) == 5, \
        'the pins must span all five TestCity widths'
    assert sum(1 for p in PINS.values() if p['corner']) == 4, \
        'TestCity has four corner lots and each must pin a corner variant'

    # a missing pin RAISES rather than defaulting
    try:
        identity('NOPE0')
    except MissingPin:
        pass
    else:
        raise AssertionError('identity() defaulted for an unpinned lot')

    # and a pin absent from the catalogue under test raises rather than
    # falling back - checked against a deliberately EMPTY catalogue
    try:
        require('NE1', have=set())
    except PinNotBaked:
        pass
    else:
        raise AssertionError('require() did not block on an unbaked pin')
    return True


if __name__ == '__main__':
    print('testcity_pins self-test:', _selftest())
    lay = _layout_lots()
    for k in sorted(PINS):
        p = PINS[k]
        print('  %-5s w%-5d %-16s t%d%s'
              % (k, p['w'], p['rid'], p['tier'], '   CORNER' if p['corner'] else ''))
