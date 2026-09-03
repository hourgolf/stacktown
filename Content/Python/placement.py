"""Placement declaration: the click -> lot -> BP_Parcel creation contract
for PLACEMENT_GRID.md's authorized v0. Pure Python, no `unreal` import -
self-testable standalone exactly like citytick.py, which this module
EXTENDS rather than replaces: citystate.json's parcel schema,
ensure_parcel, city_buy/city_tick are still the driver's own contract.
This module only adds HOW a brand-new player-created parcel enters that
state, not a second, parallel state model. A parcel this module creates
is indistinguishable to econrules.py from a pinned one once it exists -
tick/buy never need to know which path produced it.

v0 SCOPE, PLACEMENT_GRID.md section 7/8 - deliberately narrow, named as
exactly that rather than silently standing in for the eventual answer:

  - ONE road: the existing arterial. citylayout.py's own blocks() offsets
    y_in = +/-HALF from Y=0 for every quadrant, so Y=0 IS the arterial
    centerline - not re-measured here, reused from the layout that
    already declared it. Multi-road frontage is out of scope entirely,
    not stubbed.
  - A FIXED width (820, the catalogue's narrowest) and a FIXED recipe
    (vernacular, the same safe default mk_testcity_builds.py's own
    original design used) for every placed lot. PLACEMENT_GRID.md left
    "which width, which recipe" an open question on purpose; resolving
    it for real - auto-fit-largest, a player-chosen palette, whatever -
    is follow-on work, not this declaration's job. Fixed-width sidesteps
    auto-fit's own complexity so v0 can test the FEEL of clicking to
    place, which is the actual open question per the owner's brief.
  - NO GROWTH. The owner's word, verbatim: "purchase-fill only at
    first." This module has no plate-expansion logic anywhere in it,
    not even a stub - the plate bounds below are the whole board for as
    long as this ruling stands.
  - The 14-pin starter preset is untouched. This module is additive:
    citystate.json's parcels can hold pinned AND placed entries side by
    side, distinguished only by whether a 'placement' key is present.

WHAT THIS DECLARATION CAN PROVE HEADLESS, AND WHAT IT CANNOT - named
before any code touches the editor, per the coordinator's own ask:
proven here (self-tests below): pid generation, the snap-to-quantum
math, all three refusal conditions, overlap detection on one side vs.
across sides, and that a placed parcel's shape is a strict superset of
ensure_parcel's own pinned-parcel shape (so _sync_parcels needs no
change to keep reading it). NOT provable without a human: whether a
live GetHitResultUnderCursorByChannel trace against the board's ground
plane actually produces (x, y) in this module's own coordinate
convention (arterial at Y=0) rather than some other origin; whether the
spawned actor's mesh/collision resolve correctly once BP_Parcel exists
misc-placed rather than pin-placed; and the feel itself - "does this
feel like ultimate control" is a judgment call this module cannot make
about itself. The owner's own click on empty board is what closes all
three.

STILL NO `unreal` IMPORT, 2026-09-02's empty-mode pass added `citylayout`
as a sibling pure-Python dependency (for PINNED_SPANS below) - citylayout
itself has zero unreal dependency either (city.py/parcelmeta, the same
declare-first family), so this module's headless self-testability is
unchanged, just its declared-geometry vocabulary grew by one import.
"""
import citylayout

WIDTH_QUANTUM = 410.0

# Every PINNED lot's real (x0, x1, side) span, straight from citylayout -
# position has never been citystate.json's to own, pinned or not
# (PARCELIZATION_CONTRACT.md section 2: rid/width are immutable identity
# tracked in state, but a pin's POSITION was always citylayout's alone).
# Computed once, at import, since it's fully static - no randomness, no
# live-world dependency, same as WIDTH_QUANTUM/PLATE_X_MIN above.
# 'N'/'S' as the first letter of a block name is the side directly
# (PARTITIONS' own keys: NE/NW north, SE/SW south) - simpler than going
# through citylayout.blocks()['faces'] and back.
PINNED_SPANS = tuple(
    (x0, x1, 'north' if block_name[0] == 'N' else 'south')
    for block_name in citylayout.blocks()
    for _key, x0, x1, _corner in citylayout.lots(block_name))

# The plate: the FULL starter board's own extent, not a smaller carve-out.
# v0 shipped at one block's width ([-2460, 2460], BLOCK_LEN) on the
# reasoning that a smaller plate reaches an edge faster - wrong the moment
# a real player clicks the board they can actually SEE. The owner's first
# live click refused off-board on nearly every attempt because of exactly
# this gap (2026-09-02 - PLACEMENT_GRID.md's own docstring named this as
# the one thing v0 could not prove without a human, and the human found it
# on first contact).
#
# FIRST FIX WAS ALSO WRONG, same day: widened to citylayout.blocks()'s
# four-quadrant union ([-6050, 6050]) on the assumption that the
# PROCEDURAL BLOCK MATH defines the legal area. It doesn't - the board's
# actual ground-plane MESH is a separate, hand-scaled asset with its own
# margin beyond the blocks (room framing, sidewalk, whatever the artist
# gave it), and the owner's SECOND round of live clicks refused off-board
# again, this time at x roughly -6300..-6500 - board the player can see
# and stand on, outside citylayout's number, inside the mesh's real one.
# MEASURED DIRECTLY, not derived: EditorToolset.ActorTools.get_actor_bounds
# on the board's own StaticMeshActor (label contains "board",
# StaticMeshActor_489 in TestCity) returned world bounds
# min=(-7650,-4230,-200) max=(7650,4230,0). THAT is the legal area, exactly,
# because "legal" means "the player can see and click it" - not "the
# procedural layout math that happens to produce most of it."
#
# No self-test can re-derive this the way self-test 7 used to (asserting
# equality with citylayout.blocks()) - the board mesh is live editor
# content, unreachable from this module's pure-Python, no-unreal-import
# world, and citylayout was PROVEN to be the wrong authority for this
# number, not just an unverified one. If the board mesh is ever resized,
# re-measure it the same way (get_actor_bounds on the board actor) and
# update these two numbers by hand - there is no automatic check standing
# in for that anymore, which is a real, accepted gap, not an oversight.
PLATE_X_MIN = -7650.0
PLATE_X_MAX = 7650.0

V0_WIDTH = 820.0          # narrowest catalogue width - avoids auto-fit entirely, see module docstring
V0_RECIPE = 'vernacular'  # the project's own long-standing safe default

# THE POOL CAP, 2026-09-02 - not arbitrary, and not permanent. No Python
# API in this UE build spawns an actor into the game/PIE world (checked
# exhaustively, not assumed - see init_unreal.py's placement-channel
# comment), so a placed parcel can only ever ACTIVATE one of a fixed
# number of dormant BP_Parcel actors pre-placed as map content
# (mk_testcity_builds.py). Chosen against the plate's FIRST corrected
# width (12100, citylayout's four-block union): floor(12100/820)=14
# non-overlapping 820-wide lots per side x 2 sides = 28, +2 spare = 30.
#
# STALE AS OF THE PLATE'S SECOND WIDENING (PLATE_X_MIN/MAX above, now
# +/-7650 measured off the real board mesh, span 15300): the true
# physical max at v0's one width is now floor(15300/820)=18 per side x 2
# = 36, ABOVE this cap - meaning POOL_SIZE, not geometry, would now be
# the first thing a determined player hits. Left at 30 deliberately, not
# silently bumped: 30 real dormant actors already exist as saved map
# content (mk_testcity_builds.py's own pool-creation pass) and raising
# the cap means spawning and saving more, a decision for whoever owns
# that map edit, not a side effect of a coordinate fix. REVISIT THE
# MOMENT roads/growth adds frontage or a second placeable width, same as
# before - this whole cap is a v0, single-road, single-width artifact.
POOL_SIZE = 30


def _snap(x):
    """Nearest 410 multiple. A placed lot's edges always land on the
    quantum, never between - the same discipline citylayout.py's own
    partitions and woodmap.py's own width ladder both already hold to."""
    return round(x / WIDTH_QUANTUM) * WIDTH_QUANTUM


def resolve_click(state, x, y, pins_active=True):
    """(ok, reason, lot). Pure - no state mutation, so a caller can
    preview a refusal (e.g. to decide whether to even attempt place())
    without committing anything. `lot` is None on refusal, else
    {'x0', 'x1', 'side'}.

    Three refusal conditions, per PLACEMENT_GRID.md section 2 exactly:
    off-board, overlap, no legal frontage (folded into off-board here -
    see the note below on why this v0 does not model a separate
    "too far from the road" refusal).

    `pins_active` - MODE-GATED, not a permanent fact about the board
    (found live, 2026-09-02, the session right after empty mode shipped:
    the pinned-span check below applied regardless of EmptyStart, so
    every one of the owner's clicks on an EMPTY board still refused
    against ground the player could not see anything standing on).
    Default True matches every self-test below and every session before
    this fix - the caller (init_unreal.py's placement channel) passes
    the GameInstance's actual EmptyStart-derived value; a placement pool
    actor and a dormant POOL_PIN_ actor never actually conflict (they
    are disjoint pool ranges - see PARCELIZATION_CONTRACT.md's pool
    doctrine), so in empty mode a placed lot may legally land exactly
    where a pin's own footprint sits."""
    if not (PLATE_X_MIN <= x <= PLATE_X_MAX):
        return False, 'off-board: x=%.1f outside plate [%.1f, %.1f]' % (
            x, PLATE_X_MIN, PLATE_X_MAX), None
    side = 'north' if y >= 0 else 'south'
    x0 = _snap(x - V0_WIDTH / 2.0)
    x1 = x0 + V0_WIDTH
    if x0 < PLATE_X_MIN or x1 > PLATE_X_MAX:
        return False, 'off-board: snapped span [%.1f, %.1f] exceeds plate' \
            % (x0, x1), None
    # PINNED lots first - a player must not be able to place across the
    # starter city's own pads once pins and placements share one pool
    # (2026-09-02's empty-mode work), but ONLY while the pins are
    # actually standing (pins_active) - checked before the placed-lot
    # loop below purely for a clearer refusal message (pinned vs.
    # player-made); both loops are otherwise the same span-overlap test.
    if pins_active:
        for pin_x0, pin_x1, pin_side in PINNED_SPANS:
            if pin_side != side:
                continue
            if x0 < pin_x1 and pin_x0 < x1:
                return False, 'overlap: [%.1f, %.1f] crosses a pinned ' \
                    'lot at [%.1f, %.1f]' % (x0, x1, pin_x0, pin_x1), None
    for p in state['parcels'].values():
        lot = p.get('placement')
        if not lot or lot['side'] != side:
            continue
        if x0 < lot['x1'] and lot['x0'] < x1:
            return False, 'overlap: [%.1f, %.1f] crosses an existing lot ' \
                'at [%.1f, %.1f]' % (x0, x1, lot['x0'], lot['x1']), None
    return True, '', {'x0': x0, 'x1': x1, 'side': side}


def _next_pid(state):
    """P1, P2, ... - the first not already in state. Deterministic and
    legible in a log the way 'SW2' currently is, without a pin table to
    draw an id from. Distinct namespace from pinned ids (all letters) by
    construction, so a collision between a future pin and a placed
    parcel is structurally impossible, not just unlikely."""
    n = 1
    while 'P%d' % n in state['parcels']:
        n += 1
    return 'P%d' % n


def place(state, x, y, pins_active=True):
    """One placement attempt. (state, pid, ok, reason) - pid is None on
    refusal. On success, state['parcels'][pid] has EXACTLY the shape
    citytick.ensure_parcel() already produces for a pinned parcel
    ({rid, tier, width, owned, accum}) PLUS one new key, 'placement',
    that pinned parcels never carry. This is deliberate: _sync_parcels
    and econrules.py read the five original keys and were never written
    to care about extra ones, so this is additive by construction, not
    a schema migration - proven in self-test 6 below, not just asserted
    here.

    `pins_active` passes straight through to resolve_click - see its
    docstring for why this is mode-gated, not a permanent board fact."""
    placed = sum(1 for p in state['parcels'].values() if p.get('placement'))
    if placed >= POOL_SIZE:
        return state, None, False, (
            'pool exhausted: %d/%d placed lots already active'
            % (placed, POOL_SIZE))
    ok, reason, lot = resolve_click(state, x, y, pins_active=pins_active)
    if not ok:
        return state, None, False, reason
    pid = _next_pid(state)
    state['parcels'][pid] = {
        'rid': V0_RECIPE, 'tier': 0, 'width': V0_WIDTH,
        'owned': False, 'accum': 0.0,
        'placement': {'x0': lot['x0'], 'x1': lot['x1'], 'side': lot['side']},
    }
    return state, pid, True, ''


def plan_reactivation(pids, pool_labels):
    """Pure planning step for session-start reactivation (2026-09-02):
    placed lots must persist across a fresh PIE session exactly like
    purchases already do - the owner's own "persist with reset" ruling
    for the economy, inherited here rather than re-decided. Without
    this, a placed lot's citystate.json entry outlives a PIE restart but
    the pool always boots dormant (map-saved content, untouched by a
    prior session's runtime-only activations), and the ghost entry keeps
    refusing real clicks at its own span with nothing visible there to
    explain why - found live, the exact shape the owner's repeated
    "can't build here" reports would take the moment a session restarts
    without a reset in between.

    GENERIC over WHICH pids, not just placed ones (widened the same day
    empty mode needed it, self-tests 9/10/12 below): pairs whatever pid
    collection the caller passes with a dormant pool label to claim,
    both sorted for determinism, lowest-numbered pid to lowest-numbered
    slot. Returns (pairs, unmatched): `pairs` is a list of (pid,
    pool_label) ready for init_unreal.py to execute (identical location/
    identity/label/hidden/collision sequence the click path already
    uses - never a second mechanism); `unmatched` is any pid left over
    with no pool label to claim - more pids than dormant actors, a
    state/pool desync that should refuse loudly, not silently drop the
    lot. Touches neither state nor live actors - purely a decision, same
    discipline as resolve_click/place above.

    ONE caller as of this writing - init_unreal.py's placed-lot
    reactivation (pids = citystate.json entries carrying a 'placement'
    key, sorted-allocation genuinely needed since any dormant slot can
    serve any placement). Pin reactivation turned out NOT to need this:
    each pin has a PREDETERMINED slot (mk_testcity_builds.py labels a
    pin's dormant actor POOL_PIN_<key> for that specific key, not a
    fungible pool member), so it's a direct label lookup, not an
    allocation problem. Left generic anyway (self-test 12 proves it
    could serve a pin-key pid namespace too) rather than narrowed back
    to placement-only - a real, if currently unused, capability, not
    speculative scope."""
    pids = sorted(pids)
    labels = sorted(pool_labels)
    pairs = list(zip(pids, labels))
    unmatched = pids[len(labels):]
    return pairs, unmatched


if __name__ == '__main__':
    # KNOWN ANSWERS, hand-computed, same discipline as citytick.py's own
    # __main__ block. A THROWAWAY state dict each time - never touches
    # citystate.json, a self-test that writes production state is a bug.
    # FIXED 2026-09-03 (isolation pass, HANDOFF.md): the two ensure_parcel
    # calls below were the one thing that DIDN'T honour this comment - no
    # state_path passed, so a real insert (both do insert) would have
    # saved this test's fabricated state onto the shared citystate.json.
    # _SELFTEST_PATH matches citytick.py's own TEST_PATH pattern exactly.
    import os
    import citytick
    _SELFTEST_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '_selftest_citystate_placement.json')
    if os.path.exists(_SELFTEST_PATH):
        os.remove(_SELFTEST_PATH)

    # 1. A clean click just off the plate's centre places at (-820, 0),
    #    hand-computed: x=-410, width 820 -> x0 = snap(-410 - 410) =
    #    snap(-820) = -820, x1 = -820 + 820 = 0. y=100 (>=0) -> 'north'.
    #    NOT x=0 (the original, pre-empty-mode version of this test) -
    #    a lot centred on the crossing would be adjacent-testable in
    #    test 5 only by reaching to x=1230, which is REAL pin territory
    #    (NE0 starts at 1130) the moment pins joined the overlap scan.
    #    Shifted the whole 1/3/4/5 sequence toward the NW quadrant's
    #    clear cross-street gap instead - same relative shape (one lot,
    #    an overlap probe, an opposite-side non-overlap, one adjacent
    #    lot), just off-centre so neither end ever reaches a real pin.
    s = citytick.seed_state()
    s, pid, ok, reason = place(s, -410.0, 100.0)
    assert ok and pid == 'P1' and reason == '', (pid, ok, reason)
    assert s['parcels']['P1'] == {
        'rid': 'vernacular', 'tier': 0, 'width': 820.0,
        'owned': False, 'accum': 0.0,
        'placement': {'x0': -820.0, 'x1': 0.0, 'side': 'north'},
    }, s['parcels']['P1']

    # 2. Off-board: x beyond PLATE_X_MAX is refused, no parcel added.
    #    8000 is beyond the four-block board's own 6050 edge, not just
    #    beyond the old one-block 2460 - must still be a genuine miss
    #    after the plate widened to match the real board.
    s2, pid2, ok2, reason2 = place(s, 8000.0, 0.0)
    assert not ok2 and pid2 is None and 'off-board' in reason2, (
        pid2, ok2, reason2)
    assert 'P2' not in s2['parcels'], 'refused placement must not register'

    # 3. Overlap on the SAME side is refused: P1 spans [-820, 0] north;
    #    a click at x=-500 (snap(-500-410)=snap(-910)=-820, same span as
    #    P1 exactly) crosses it.
    s3, pid3, ok3, reason3 = place(s, -500.0, 50.0)
    assert not ok3 and pid3 is None and 'overlap' in reason3, (
        pid3, ok3, reason3)
    assert 'P2' not in s3['parcels']

    # 4. The SAME x, opposite side (y<0, 'south') is NOT an overlap -
    #    frontage sides are independent spans.
    s4, pid4, ok4, reason4 = place(s, -410.0, -50.0)
    assert ok4 and pid4 == 'P2', (pid4, ok4, reason4)
    assert s4['parcels']['P2']['placement']['side'] == 'south'
    assert s4['parcels']['P2']['placement'] == {
        'x0': -820.0, 'x1': 0.0, 'side': 'south'}

    # 5. A second, non-overlapping north placement gets the next pid in
    #    sequence, not a reused one, and its span is adjacent, not
    #    overlapping: click at x=410 -> snap(410-410)=snap(0)=0, span
    #    [0, 820] - touches P1's [-820,0] at the boundary, does not cross
    #    it (x0 < lot.x1 and lot.x0 < x1 is false when x0 == lot.x1
    #    exactly), and stays well clear of NE0's real span (1130..3590).
    s5, pid5, ok5, reason5 = place(s4, 410.0, 60.0)
    assert ok5 and pid5 == 'P3', (pid5, ok5, reason5)
    assert s5['parcels']['P3']['placement'] == {
        'x0': 0.0, 'x1': 820.0, 'side': 'north'}

    # 6. Compatibility with the EXISTING driver contract, not just
    #    self-consistency: ensure_parcel's own pinned-parcel shape is a
    #    strict subset of what place() produces, key for key.
    pinned_state, inserted = citytick.ensure_parcel(
        citytick.seed_state(), 'SW9', 'vernacular', 820, _SELFTEST_PATH)
    pinned_keys = set(pinned_state['parcels']['SW9'])
    placed_keys = set(s5['parcels']['P1'])
    assert pinned_keys < placed_keys, (pinned_keys, placed_keys)
    assert placed_keys - pinned_keys == {'placement'}, placed_keys

    # 7. NOT an equality check against citylayout anymore - that WAS
    #    self-test 7 once, and it was wrong: the owner's second live click
    #    proved the board's real, visible extent is wider than
    #    citylayout.blocks()'s procedural union (measured directly via
    #    get_actor_bounds on the board mesh - see the PLATE_X_MIN/MAX
    #    comment above). What's still true, and still worth checking, is
    #    CONTAINMENT: whatever the plate's real bounds are, they must be
    #    at least as wide as the blocks they're supposed to contain, or a
    #    pinned lot could sit outside the legally-placeable area - a
    #    weaker but honest invariant, not a number this module can
    #    re-derive on its own.
    import citylayout
    xs = []
    for b in citylayout.blocks().values():
        x0, _y0, x1, _y1 = b['env']
        xs += [x0, x1]
    assert PLATE_X_MIN <= min(xs) and max(xs) <= PLATE_X_MAX, (
        (PLATE_X_MIN, PLATE_X_MAX), (min(xs), max(xs)))

    # 8. Pool exhaustion refuses regardless of geometry, once POOL_SIZE
    #    lots are already active. Built directly (POOL_SIZE synthetic
    #    entries, not POOL_SIZE real clicks) because real clicks at
    #    V0_WIDTH overlap-refuse around 28, before the count ever reaches
    #    30 - this isolates the count check from the geometry check it
    #    would otherwise never outlive.
    full = citytick.seed_state()
    for i in range(POOL_SIZE):
        full['parcels']['ZZ%d' % i] = {
            'rid': V0_RECIPE, 'tier': 0, 'width': V0_WIDTH, 'owned': False,
            'accum': 0.0,
            'placement': {'x0': 0.0, 'x1': 0.0, 'side': 'north'},
        }
    s8, pid8, ok8, reason8 = place(full, 0.0, 100.0)
    assert not ok8 and pid8 is None and 'pool exhausted' in reason8, (
        pid8, ok8, reason8)

    # 9. plan_reactivation, enough pool slots: every placed pid gets a
    #    label, lowest pid to lowest label, nothing left unmatched.
    s9 = citytick.seed_state()
    s9, _ = citytick.ensure_parcel(
        s9, 'SW9', V0_RECIPE, 820, _SELFTEST_PATH)  # pinned
    for pid, x0 in (('P1', 0.0), ('P2', 820.0), ('P3', 1640.0)):
        s9['parcels'][pid] = {
            'rid': V0_RECIPE, 'tier': 0, 'width': V0_WIDTH, 'owned': False,
            'accum': 0.0,
            'placement': {'x0': x0, 'x1': x0 + V0_WIDTH, 'side': 'north'},
        }
    placed_pids9 = [pid for pid, p in s9['parcels'].items()
                    if p.get('placement')]
    pairs9, unmatched9 = plan_reactivation(
        placed_pids9, {'POOL_04', 'POOL_00', 'POOL_02', 'POOL_01', 'POOL_03'})
    assert pairs9 == [('P1', 'POOL_00'), ('P2', 'POOL_01'),
                       ('P3', 'POOL_02')], pairs9
    assert unmatched9 == [], unmatched9

    # 10. plan_reactivation, too few pool slots: as many pairs as labels
    #     allow, the rest reported unmatched rather than silently
    #     dropped - the state/pool desync case, built directly since real
    #     play can't easily reach it (the pool only shrinks if actors are
    #     destroyed outside this system).
    pairs10, unmatched10 = plan_reactivation(
        placed_pids9, {'POOL_00', 'POOL_01'})
    assert pairs10 == [('P1', 'POOL_00'), ('P2', 'POOL_01')], pairs10
    assert unmatched10 == ['P3'], unmatched10

    # 11. A click on a PINNED lot's own span refuses as overlap, and says
    #     so distinctly - the empty-mode gap named when pins and
    #     placements started sharing one pool. NE0 spans x 1130..3590
    #     (citylayout's own known-answer cell, EMISSION-END-TO-END) - a
    #     click at its centre, 2360, must refuse before ever reaching the
    #     placed-lot loop (fresh seed_state, nothing placed yet).
    s11 = citytick.seed_state()
    ok11, reason11, lot11 = resolve_click(s11, 2360.0, 100.0)
    assert not ok11 and lot11 is None and 'pinned lot' in reason11, (
        ok11, reason11, lot11)

    # 11b. The SAME click, pins_active=False (empty mode): accepts. Found
    #      live the session right after empty mode shipped - the pinned
    #      -span check applied regardless of EmptyStart, so a dormant
    #      pin's ground kept refusing real clicks on a board with
    #      nothing standing on it. NE0's centre, same 2360/100 as 11,
    #      only the mode differs.
    ok11b, reason11b, lot11b = resolve_click(
        s11, 2360.0, 100.0, pins_active=False)
    assert ok11b and reason11b == '' and lot11b is not None, (
        ok11b, reason11b, lot11b)
    assert lot11b['side'] == 'north'

    # 12. plan_reactivation is genuinely generic, not placement-specific
    #     despite its name and history: a pin-key pid namespace (letters
    #     only, no 'P'+digits) plans identically. Not actually how
    #     init_unreal.py's pin-reactivation works (each pin has a
    #     PREDETERMINED slot label, POOL_PIN_<key>, so it's a direct
    #     lookup there, not an allocation) - this proves the function
    #     COULD serve that shape, a real capability kept rather than
    #     narrowed back to one caller's exact needs.
    pairs12, unmatched12 = plan_reactivation(
        ['NE0', 'NE1', 'SW3'],
        {'POOL_PIN_NE0', 'POOL_PIN_NE1', 'POOL_PIN_SW3'})
    assert pairs12 == [('NE0', 'POOL_PIN_NE0'), ('NE1', 'POOL_PIN_NE1'),
                        ('SW3', 'POOL_PIN_SW3')], pairs12
    assert unmatched12 == [], unmatched12

    print('placement self-check: 13/13 pass (pure-Python click->lot->state '
          'contract, plate bounds measured off the real board mesh and '
          'contain citylayout\'s block union, session-start reactivation '
          'planning for both placed and pinned lots, pinned-span overlap '
          'refusal mode-gated on pins_active; live cursor-trace coordinates, '
          'actor spawn/resolve, '
          'and the feel itself are NOT provable here - see module '
          'docstring, and PLACEMENT_GRID.md section 8 - the owner\'s own '
          'click on empty board is the real acceptance test)')
    if os.path.exists(_SELFTEST_PATH):
        os.remove(_SELFTEST_PATH)
