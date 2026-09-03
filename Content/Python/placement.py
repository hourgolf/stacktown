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

  - TWO roads as of 2026-09-03: the arterial (Y=0) and the cross street
    (X=0), citylayout.py's own single crossing - resolve_road below picks
    the nearer by point-to-segment distance, RESOLVE_ROAD_NOTES.md. Still
    not the general N-road case: PINNED_SPANS has no cross-street entries
    (section 6, still open), and a second crossing would need a second
    _in_crossing-style check, not assumed to generalize for free.
  - A width PARAMETER (default 820, the catalogue's narrowest) and a
    FIXED recipe (vernacular, the same safe default mk_testcity_builds.py's
    own original design used) for every placed lot. PLACEMENT_GRID.md left
    "which recipe" an open question on purpose; a player-chosen palette is
    follow-on work, not this declaration's job.
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


# POSITION is free along the road (owner, 2026-09-03: "let it slide freely
# along the road" - the 410 snap made the pad land "near" the click, not
# under it). WIDTHS stay on the catalogue ladder; only where a lot sits is
# continuous, rounded to POSITION_QUANTUM to keep spans exact in JSON and
# the overlap scan free of float noise.
POSITION_QUANTUM = 10.0


def _snap(x):
    """Nearest POSITION_QUANTUM (10 uu) - effectively free placement along
    the road. Until 2026-09-03 this was the 410 width quantum, which is
    still what the width ladder itself is built on (woodmap.WIDTHS)."""
    return round(x / POSITION_QUANTUM) * POSITION_QUANTUM


# REACH (2026-09-03, owner: "a parcel showed up 'generally' around the
# click"): v0 snapped ANY click to the arterial's frontage, from any
# distance - a click on the studio floor placed a pad 5000 uu away.
# Two new refusals bound the click to the block the pad will occupy:
# inside the corridor (|y| < ROAD_HALF) is the road itself; beyond the
# block's back edge plus REACH_SLACK is "too far from a road". The pad
# still snaps in X and sits at the frontage in Y; the click only has to
# land on the block it is asking for. The ghost preview (clickdriver.py)
# uses resolve_click too, so what it shows is exactly what a click gets.
ROAD_HALF = citylayout.HALF             # 1130: centreline to facade line
BLOCK_DEPTH = citylayout.BLOCK_DEPTH    # 1500: facade line to back edge
REACH_SLACK = 600.0                     # forgiveness behind the block


# PLATE_Y_MIN/MAX: the same board-mesh measurement PLATE_X_MIN/MAX above
# already cites (get_actor_bounds on the board actor, min=(-7650,-4230,
# -200) max=(7650,4230,0)) - reused here for the cross street's own
# along-bound rather than re-measured, since it is the same one mesh.
PLATE_Y_MIN = -4230.0
PLATE_Y_MAX = 4230.0

# Both roads share ROAD_HALF/BLOCK_DEPTH - citylayout.py's own docstring
# draws exactly this cross ("arterial, CORRIDOR wide" / "cross street,
# CORRIDOR wide", the SAME CORRIDOR both times, one crossing) - not two
# independently-chosen numbers that happen to match.
ARTERIAL = {
    'id': 'arterial', 'start': (PLATE_X_MIN, 0.0), 'end': (PLATE_X_MAX, 0.0),
    'side_plus': 'north', 'side_minus': 'south', 'axis': 'x',
}
CROSS_STREET = {
    'id': 'cross', 'start': (0.0, PLATE_Y_MIN), 'end': (0.0, PLATE_Y_MAX),
    'side_plus': 'west', 'side_minus': 'east', 'axis': 'y',
}
ROADS = (ARTERIAL, CROSS_STREET)

# The same "too far from a road" reach resolve_click already enforces in
# Y for the one-road case, reused here as resolve_road's own outer claim
# distance - see RESOLVE_ROAD_NOTES.md section 5's "no number proposed
# here" left this open; this is the answer, matching the number already
# proven live rather than inventing a second one that could drift from it.
ROAD_MAX_REACH = ROAD_HALF + BLOCK_DEPTH + REACH_SLACK


def _project_to_road(road, x, y):
    """(along, across, length) in `road`'s own frame -
    RESOLVE_ROAD_NOTES.md section 4. `along` is distance from `start`
    toward `end`, unbounded (the caller clamps against `length`);
    `across` is the SIGNED perpendicular offset - positive is the
    `side_plus` side. Pure vector projection, no trig: `direction` is
    the unit vector start->end, `normal` is `direction` rotated +90
    degrees (so along the arterial, whose direction is +X, normal is
    +Y - across>=0 there means y>=0, matching resolve_click's own
    `side='north' if y>=0` exactly, unchanged convention)."""
    sx, sy = road['start']
    ex, ey = road['end']
    dx, dy = ex - sx, ey - sy
    length = (dx * dx + dy * dy) ** 0.5
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux
    tx, ty = x - sx, y - sy
    along = tx * ux + ty * uy
    across = tx * nx + ty * ny
    return along, across, length


def _in_crossing(roads, x, y):
    """True if `(x, y)` falls inside MORE THAN ONE road's own in-corridor
    band (`abs(across) < ROAD_HALF`, standing on that road's pavement,
    not its frontage) with its `along` in-segment - the click is on
    pavement two roads physically share, so no single road's claim is
    the honest answer. Factored out of `resolve_road` so it and
    `resolve_click` (which wants this as its OWN, distinctly-worded
    refusal, not folded into "off-board") can never disagree about the
    rule. NOT the corner-lot question (RESOLVE_ROAD_NOTES.md section 7,
    still open, still unanswered here) - the narrower, unambiguous case
    of standing on the pavement itself where two roads overlap."""
    count = 0
    for road in roads:
        along, across, length = _project_to_road(road, x, y)
        if 0.0 <= along <= length and abs(across) < ROAD_HALF:
            count += 1
    return count > 1


def lot_road_id(lot):
    """A placed lot's road, defaulting to 'arterial' for any lot dict
    that predates this key - v0's placement.py wrote none, so the
    owner's own real citystate.json has entries with no 'road_id' key
    at all (2026-09-03, coordinator: "the owner's real save has four
    such lots"). Three call sites had independently written the exact
    same `.get('road_id', 'arterial')` before this existed - this
    function's own overlap-scan below, clickdriver.py's ghost-box
    frame, and init_unreal.py's _lot_transform - the same drift risk
    ROAD_MAX_REACH's own comment already flagged for a different pair
    of numbers. ONE place this fallback rule lives now; the other two
    call THIS, not their own copy."""
    return lot.get('road_id', 'arterial')


def resolve_road(roads, x, y):
    """(road, local) | (None, None) - RESOLVE_ROAD_NOTES.md section 2.
    `local` is {'along', 'across', 'side'} in the WINNING road's own
    frame; `side` is already relabelled to that road's own
    'side_plus'/'side_minus' names (section 4's 'plus'/'minus' is an
    implementation detail, never returned - a caller should never need
    to know which sign convention a road picked).

    Nearest-road selection, section 5: for each candidate, the distance
    is the perpendicular offset if the click's `along` falls inside the
    segment's own [0, length] span, else the distance to whichever
    endpoint is nearer (point-to-SEGMENT, not point-to-infinite-line -
    a click past a short segment's end must not claim frontage on a
    road that does not reach that far). The nearest candidate wins,
    subject to ROAD_MAX_REACH - beyond every road's reach is (None,
    None), the generalized form of today's single-road off-board
    refusal. Near the crossing (`_in_crossing` above) refuses the same
    way, before nearest-road selection ever runs."""
    if _in_crossing(roads, x, y):
        return None, None
    best = None
    best_dist = None
    for road in roads:
        along, across, length = _project_to_road(road, x, y)
        if 0.0 <= along <= length:
            dist = abs(across)
        else:
            clamped = max(0.0, min(length, along))
            dist = ((along - clamped) ** 2 + across ** 2) ** 0.5
        if best_dist is None or dist < best_dist:
            best = (road, along, across)
            best_dist = dist
    if best is None or best_dist > ROAD_MAX_REACH:
        return None, None
    road, along, across = best
    side = road['side_plus'] if across >= 0.0 else road['side_minus']
    return road, {'along': along, 'across': across, 'side': side}



def lot_rect(lot):
    """World-space footprint (xmin, xmax, ymin, ymax) of a lot's PAD from
    its placement dict, both roads: the span along the road's axis, and
    facade line to block back edge across it, on the lot's side. The ONLY
    geometry the overlap scan compares - spans within one road miss the
    corner, where a cross-street lot and an arterial lot share ground."""
    near, far = ROAD_HALF, ROAD_HALF + BLOCK_DEPTH
    x0, x1 = float(lot['x0']), float(lot['x1'])
    if lot_road_id(lot) == 'cross':
        if lot['side'] == 'west':
            return (-far, -near, x0, x1)
        return (near, far, x0, x1)
    if lot['side'] == 'north':
        return (x0, x1, near, far)
    return (x0, x1, -far, -near)


def rects_overlap(a, b):
    return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]


def resolve_click(state, x, y, pins_active=True, width=V0_WIDTH):
    """(ok, reason, lot) - the click -> lot decision, MULTI-ROAD as of
    2026-09-03 (RESOLVE_ROAD_NOTES.md; resolve_road above, wired in
    rather than standalone now). Road/side selection and the outer
    reach bound are entirely resolve_road's job; this function does
    what resolve_road deliberately leaves unanswered: the in-the-road
    refusal (read off the WINNING road's own corridor, and only when
    the click's `along` actually falls inside THAT road's own segment -
    a click past a road's own end can share its `across` with the
    corridor without standing on it, test 2's off-board case among
    them), snapping back to WORLD space before quantizing, the
    pinned-span check (arterial only - PINNED_SPANS has no cross-street
    entries, RESOLVE_ROAD_NOTES.md section 6, still open), and the
    placed-lot overlap check, now scoped to lots on the SAME road via
    the 'road_id' key place() below writes.

    There is no separate "too far from a road" refusal here distinct
    from resolve_road's own (None, None): any road resolve_road hands
    back is ALREADY within ROAD_MAX_REACH by construction (its own
    outer bound), so that case can only ever surface below as
    'off-board', never re-derived a second time against a number that
    could drift from resolve_road's - see ROAD_MAX_REACH's own comment
    above for why the two are the same number on purpose.

    world_coord = road['start'][axis] + along, THEN snapped - not
    `along` snapped directly. Neither PLATE_X_MIN nor PLATE_Y_MIN is a
    multiple of WIDTH_QUANTUM, so snapping the road-relative offset
    would shift the grid off-quantum silently. Converting to world
    space first makes the arterial case reduce EXACTLY to the
    pre-multi-road math (road['start'][0] is PLATE_X_MIN, along =
    x - PLATE_X_MIN, so world_coord == x always - self-test 13 checks
    this identity directly) while correctly generalizing to the cross
    street's own Y axis.

    `pins_active` gates the PINNED_SPANS check only, unchanged from
    before multi-road - see empty-mode's own caller for why this is
    mode-gated, not a permanent board fact."""
    road, local = resolve_road(ROADS, x, y)
    if road is None:
        if _in_crossing(ROADS, x, y):
            return False, (
                'in the crossing: (%.1f, %.1f) is pavement shared by '
                'more than one road' % (x, y)), None
        return False, (
            'off-board: (%.1f, %.1f) is not within reach of any road'
            % (x, y)), None
    along, across, side = local['along'], local['across'], local['side']
    _, _, length = _project_to_road(road, x, y)
    if 0.0 <= along <= length and abs(across) < ROAD_HALF:
        return False, (
            'in the road: |across|=%.0f is inside the %s corridor '
            '(half %.0f)' % (abs(across), road['id'], ROAD_HALF)), None
    axis_idx = 0 if road['axis'] == 'x' else 1
    world_coord = road['start'][axis_idx] + along
    x0 = _snap(world_coord - width / 2.0)
    x1 = x0 + width
    axis_min = min(road['start'][axis_idx], road['end'][axis_idx])
    axis_max = max(road['start'][axis_idx], road['end'][axis_idx])
    if x0 < axis_min or x1 > axis_max:
        return False, (
            'off-board: snapped span [%.1f, %.1f] exceeds the %s road'
            % (x0, x1, road['id'])), None
    if pins_active and road is ARTERIAL:
        for pin_x0, pin_x1, pin_side in PINNED_SPANS:
            if pin_side != side:
                continue
            if x0 < pin_x1 and pin_x0 < x1:
                return False, (
                    'overlap: [%.1f, %.1f] crosses a pinned lot at '
                    '[%.1f, %.1f]' % (x0, x1, pin_x0, pin_x1)), None
    candidate = {'x0': x0, 'x1': x1, 'side': side, 'road_id': road['id']}
    mine = lot_rect(candidate)
    for p in state['parcels'].values():
        lot = p.get('placement')
        if not lot:
            continue
        # WORLD footprints, every road (2026-09-03): the corner is where a
        # cross-street lot and an arterial lot share ground while their
        # spans never compare (different axes) - the owner placed a lot
        # onto a standing building there. The rectangle test contains the
        # old same-road same-side span test, so nothing it refused is
        # allowed now.
        if rects_overlap(mine, lot_rect(lot)):
            return False, (
                'overlap: [%.1f, %.1f] on the %s crosses an existing lot at '
                '[%.1f, %.1f] on the %s' % (x0, x1, road['id'], lot['x0'],
                                            lot['x1'], lot_road_id(lot))), None
    return True, '', candidate


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


def place(state, x, y, pins_active=True, width=V0_WIDTH):
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
    ok, reason, lot = resolve_click(state, x, y, pins_active=pins_active, width=width)
    if not ok:
        return state, None, False, reason
    pid = _next_pid(state)
    state['parcels'][pid] = {
        'rid': V0_RECIPE, 'tier': 0, 'width': width,
        'owned': False, 'accum': 0.0,
        'placement': {'x0': lot['x0'], 'x1': lot['x1'], 'side': lot['side'],
                      'road_id': lot['road_id']},
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
    # OUTSIDE Content/ (2026-09-03): the editor's auto-reimport treats any
    # JSON under Content/ as a DataTable source, fired a reimport on this
    # artifact mid-self-test and stalled the game thread on a prompt.
    _SELFTEST_DIR = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))), 'Saved', 'SelfTest')
    os.makedirs(_SELFTEST_DIR, exist_ok=True)
    _SELFTEST_PATH = os.path.join(_SELFTEST_DIR, '_selftest_citystate_placement.json')
    if os.path.exists(_SELFTEST_PATH):
        os.remove(_SELFTEST_PATH)

    # 1. A clean click near the plate's WEST edge places just inside it.
    #    RELOCATED 2026-09-03, multi-road integration: the old point
    #    (x=-410) sat only 410 uu from the cross street's own centreline
    #    but 1500 uu from the arterial's - once resolve_click offers BOTH
    #    roads, the cross street legitimately wins there now (self-test
    #    15 proves this exact point resolves to CROSS_STREET when both
    #    roads are offered), so asserting arterial-frontage placement at
    #    that x would be asserting something now false, not a regression.
    #    Needed a point where |x| clearly beats |y| (arterial nearer) AND
    #    lands on an UNPINNED span - queried PINNED_SPANS directly rather
    #    than re-deriving citylayout's table by hand: north/south frontage
    #    is WALL-TO-WALL pinned from 1130..6050 (both signs) with no gap
    #    of its own, so the only open ground left is the two edge margins,
    #    PLATE_X_MIN..-6050 and 6050..PLATE_X_MAX, each 1600 uu wide.
    #    x=-7000, width 820: x0 = -7000-410 = -7410 (position is FREE on
    #    a 10 uu grid since 2026-09-03, the owner's "let it slide freely
    #    along the road"), x1 = -7410+820 = -6590, clear of the pin at
    #    -6050 by 540 uu.
    #    y=1500 (>=0) -> 'north'; cross-street distance there is 7000,
    #    arterial wins by a wide margin, no ambiguity.
    s = citytick.seed_state()
    s, pid, ok, reason = place(s, -7000.0, 1500.0)
    assert ok and pid == 'P1' and reason == '', (pid, ok, reason)
    assert s['parcels']['P1'] == {
        'rid': 'vernacular', 'tier': 0, 'width': 820.0,
        'owned': False, 'accum': 0.0,
        'placement': {'x0': -7410.0, 'x1': -6590.0, 'side': 'north',
                       'road_id': 'arterial'},
    }, s['parcels']['P1']

    # 2. Off-board: x beyond PLATE_X_MAX is refused, no parcel added.
    #    8000 is beyond the four-block board's own 6050 edge, not just
    #    beyond the old one-block 2460 - must still be a genuine miss
    #    after the plate widened to match the real board. Also proves
    #    resolve_click's in-the-road check is gated on `along` actually
    #    being IN the winning road's own segment: at y=0 across=0 always,
    #    which would misfire as "in the road" if checked blind - along
    #    here is 350 uu PAST the arterial's own east end, so that check
    #    is correctly skipped and this falls through to off-board instead.
    s2, pid2, ok2, reason2 = place(s, 8000.0, 0.0)
    assert not ok2 and pid2 is None and 'off-board' in reason2, (
        pid2, ok2, reason2)
    assert 'P2' not in s2['parcels'], 'refused placement must not register'

    # 3. Overlap on the SAME side is refused: P1 spans [-7380, -6560]
    #    north; a click at x=-7050 (snap(-7050-410)=snap(-7460)=-7380,
    #    same span as P1 exactly) crosses it.
    s3, pid3, ok3, reason3 = place(s, -7050.0, 1500.0)
    assert not ok3 and pid3 is None and 'overlap' in reason3, (
        pid3, ok3, reason3)
    assert 'P2' not in s3['parcels']

    # 4. The SAME x, opposite side (y<0, 'south') is NOT an overlap -
    #    frontage sides are independent spans.
    s4, pid4, ok4, reason4 = place(s, -7000.0, -1500.0)
    assert ok4 and pid4 == 'P2', (pid4, ok4, reason4)
    assert s4['parcels']['P2']['placement']['side'] == 'south'
    assert s4['parcels']['P2']['placement'] == {
        'x0': -7410.0, 'x1': -6590.0, 'side': 'south', 'road_id': 'arterial'}

    # 5. A second, non-overlapping north placement gets the next pid in
    #    sequence, not a reused one. NOT adjacent to P1 this time (a real,
    #    measured constraint, not a simplification of convenience): the
    #    west margin is exactly 1600 uu wide and two 820-wide lots need
    #    1640 - they cannot both fit, let alone touch, in the same margin.
    #    Placed on the EAST margin instead (x=7000, mirroring test 1):
    #    x0 = snap(7000-410) = snap(6590) = 6560, x1 = 6560+820 = 7380,
    #    clear of the pin at 4410..6050 by 510 uu, same shape as P1's own
    #    clearance. Proves the second-placement/next-pid path without
    #    claiming an adjacency the geometry cannot actually support.
    s5, pid5, ok5, reason5 = place(s4, 7000.0, 1500.0)
    assert ok5 and pid5 == 'P3', (pid5, ok5, reason5)
    assert s5['parcels']['P3']['placement'] == {
        'x0': 6590.0, 'x1': 7410.0, 'side': 'north', 'road_id': 'arterial'}

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
    s8, pid8, ok8, reason8 = place(full, 0.0, 1500.0)
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
    ok11, reason11, lot11 = resolve_click(s11, 2360.0, 1500.0)
    assert not ok11 and lot11 is None and 'pinned lot' in reason11, (
        ok11, reason11, lot11)

    # 11b. The SAME click, pins_active=False (empty mode): accepts. Found
    #      live the session right after empty mode shipped - the pinned
    #      -span check applied regardless of EmptyStart, so a dormant
    #      pin's ground kept refusing real clicks on a board with
    #      nothing standing on it. NE0's centre, same 2360/100 as 11,
    #      only the mode differs.
    ok11b, reason11b, lot11b = resolve_click(
        s11, 2360.0, 1500.0, pins_active=False)
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

    # 13. resolve_road REDUCES TO TODAY'S MATH on the arterial alone -
    #     RESOLVE_ROAD_NOTES.md section 4's own claim, checked, not
    #     asserted. Same four points resolve_click's own tests already
    #     use above: side must match resolve_click's y>=0 rule exactly,
    #     and recovering x from `along` (start=(PLATE_X_MIN,0), so
    #     x = along + PLATE_X_MIN, direction is +X) must reproduce the
    #     original x - a single-road candidate list is the "alone" this
    #     claim is about; test 16 below is what changes once a second
    #     road can outcompete it.
    for x, y, want_side in ((-410.0, 1500.0, 'north'),
                             (-410.0, -1500.0, 'south'),
                             (2360.0, 1500.0, 'north'),
                             (0.0, 50.0, 'north')):
        road13, local13 = resolve_road([ARTERIAL], x, y)
        assert road13 is ARTERIAL, (x, y, road13)
        assert local13['side'] == want_side, (x, y, local13)
        assert abs(local13['across'] - y) < 1e-9, (x, y, local13)
        assert abs((local13['along'] + PLATE_X_MIN) - x) < 1e-9, (
            x, y, local13)

    # 14. The cross street alone, same reduction shape, its own axis:
    #     `across` reduces to -x (direction is +Y so the unit normal
    #     points -X - see resolve_road's own docstring), and positive x
    #     is 'east' the same way positive y is 'north' for the arterial -
    #     both conventions fall out of the math, neither is asserted
    #     independently of it.
    for x, y, want_side in ((1500.0, -410.0, 'east'),
                             (-1500.0, -410.0, 'west'),
                             (1500.0, 2360.0, 'east')):
        road14, local14 = resolve_road([CROSS_STREET], x, y)
        assert road14 is CROSS_STREET, (x, y, road14)
        assert local14['side'] == want_side, (x, y, local14)
        assert abs(local14['across'] - (-x)) < 1e-9, (x, y, local14)
        assert abs((local14['along'] + PLATE_Y_MIN) - y) < 1e-9, (
            x, y, local14)

    # 15. Nearest-road selection actually disambiguates: (-410, 1500) is
    #     1500 uu from the arterial's centreline but only 410 uu from the
    #     cross street's - with both roads offered, the cross street
    #     must win, even though test 13 above (arterial ALONE) resolves
    #     this exact point to the arterial - the whole point of the
    #     "alone" qualifier in RESOLVE_ROAD_NOTES.md section 4's claim.
    road15, local15 = resolve_road(ROADS, -410.0, 1500.0)
    assert road15 is CROSS_STREET, (road15, local15)
    assert abs(local15['across'] - 410.0) < 1e-9, local15
    assert local15['side'] == 'west', local15

    # 16. REFUSES NEAR THE CROSSING: a click inside BOTH roads' own
    #     ROAD_HALF corridor (standing on pavement common to both, not
    #     legal frontage for either) - the origin itself and three more
    #     points scaled up to just inside ROAD_HALF (1130), each on the
    #     diagonal so both roads' `across` share the same magnitude.
    #     This is the narrow, unambiguous case RESOLVE_ROAD_NOTES.md
    #     section 2's docstring names, NOT the still-open corner-lot
    #     question (section 7) - a click merely NEAR a corner but inside
    #     only one corridor still resolves (test 17).
    for x, y in ((0.0, 0.0), (100.0, 100.0), (500.0, 500.0),
                 (1000.0, 1000.0)):
        road16, local16 = resolve_road(ROADS, x, y)
        assert road16 is None and local16 is None, (x, y, road16, local16)

    # 17. Just past the crossing ambiguity zone (both `across` magnitudes
    #     exceed ROAD_HALF), resolve_road picks a winner again rather
    #     than refusing forever - proves 16 is a narrow band, not a
    #     dead zone swallowing the whole quadrant near the origin.
    road17, local17 = resolve_road(ROADS, 2000.0, 2000.0)
    assert road17 is not None and local17 is not None, (road17, local17)

    # 18. Point-to-SEGMENT, not point-to-infinite-line (RESOLVE_ROAD_NOTES
    #     .md section 5's own distinction): 5000 uu past the arterial's
    #     own east end, sitting exactly ON its infinite centreline
    #     (y=0) - an infinite-line distance would read 0 and wrongly
    #     accept; the finite segment's own end makes this "too far",
    #     same refusal shape as test 19's real off-board click.
    road18, local18 = resolve_road([ARTERIAL], PLATE_X_MAX + 5000.0, 0.0)
    assert road18 is None and local18 is None, (road18, local18)

    # 19. Too far from EITHER road, both roads offered - includes the
    #     owner's own logged bad click (PLAYABLE_PLAN.md section 1:
    #     "a click at (4671, 6954) - on the studio floor, off the board
    #     entirely - placed P1 at (4100, 1880), five thousand units
    #     away") - the exact point that motivated REACH existing at all,
    #     now checked against the multi-road resolver too, not just the
    #     single-road one resolve_click already refuses it against.
    for x, y in ((4671.0, 6954.0), (100000.0, 100000.0)):
        road19, local19 = resolve_road(ROADS, x, y)
        assert road19 is None and local19 is None, (x, y, road19, local19)

    # 20. resolve_road INTEGRATED into resolve_click, 2026-09-03: a click
    #     on the cross street's WEST side succeeds and gets road_id='cross'.
    #     x=-1500, y=2500 - along=py+4230=6730 (in [0,8460]), across=1500
    #     (>=0 -> side_plus='west'), well clear of both ROAD_HALF (1130)
    #     and any arterial competition (arterial dist there is 2500, cross
    #     dist is 1500, cross wins). world_coord recovers y exactly (2500,
    #     the cross street's own axis), same identity test 14 already
    #     proves for resolve_road alone: x0=snap(2500-410)=snap(2090)=2050,
    #     x1=2870. Fresh state - PINNED_SPANS never applies off the
    #     arterial, so no pin geometry to clear here.
    s20 = citytick.seed_state()
    s20, pid20, ok20, reason20 = place(s20, -1500.0, 2500.0)
    assert ok20 and pid20 == 'P1' and reason20 == '', (pid20, ok20, reason20)
    assert s20['parcels']['P1']['placement'] == {
        'x0': 2090.0, 'x1': 2910.0, 'side': 'west', 'road_id': 'cross'
    }, s20['parcels']['P1']

    # 21. The EAST side of the cross street, same state (proves the two
    #     sides are independent spans on this road too, same shape as
    #     test 4 for the arterial): x=1500, y=2500 -> across=-1500
    #     (<0 -> side_minus='east'), same x0/x1 as test 20 (only side
    #     sign differs, `across`'s magnitude and `along` are unchanged).
    s21, pid21, ok21, reason21 = place(s20, 1500.0, 2500.0)
    assert ok21 and pid21 == 'P2', (pid21, ok21, reason21)
    assert s21['parcels']['P2']['placement'] == {
        'x0': 2090.0, 'x1': 2910.0, 'side': 'east', 'road_id': 'cross'
    }, s21['parcels']['P2']

    # 22. In-the-road, ARTERIAL frame: x=3000, y=500 - arterial across=500
    #     (<1130), along=10650 (in-segment) -> refused. Not a crossing
    #     (cross across there is -3000, |3000|>1130) and arterial
    #     unambiguously nearest (500 < cross's 3000) - a clean single-road
    #     in-the-road case, message must name the arterial specifically.
    ok22, reason22, lot22 = resolve_click(citytick.seed_state(), 3000.0, 500.0)
    assert not ok22 and lot22 is None, (ok22, reason22, lot22)
    assert 'in the road' in reason22 and 'arterial' in reason22, reason22

    # 23. In-the-road, CROSS-STREET frame - the case that did NOT exist
    #     before multi-road integration, and the one a blind `abs(y)`
    #     check (the old single-road shape) could never produce: x=200,
    #     y=3000. Cross across=-200 (<1130), arterial across=3000 (not a
    #     candidate - not <1130 either, so still no crossing ambiguity),
    #     cross wins nearest-road (200 < 3000). Message must name 'cross',
    #     proving the refusal is read off the WINNING road's own frame,
    #     not hard-coded to the arterial the way it used to be.
    ok23, reason23, lot23 = resolve_click(citytick.seed_state(), 200.0, 3000.0)
    assert not ok23 and lot23 is None, (ok23, reason23, lot23)
    assert 'in the road' in reason23 and 'cross' in reason23, reason23

    # 24. The crossing refusal is reachable through resolve_click itself,
    #     not just resolve_road directly (test 16's own check) - same four
    #     points test 16 already uses, now proven at the layer the click
    #     driver actually calls.
    for x, y in ((0.0, 0.0), (100.0, 100.0), (500.0, 500.0),
                 (1000.0, 1000.0)):
        ok24, reason24, lot24 = resolve_click(citytick.seed_state(), x, y)
        assert not ok24 and lot24 is None, (x, y, ok24, reason24, lot24)
        assert 'crossing' in reason24, (x, y, reason24)

    # 25. lot_road_id's own backward-compat contract, added 2026-09-03 to
    #     replace three independently-written copies of the same
    #     `.get('road_id', 'arterial')` (this module's own overlap-scan,
    #     clickdriver.py's ghost-box frame, init_unreal.py's
    #     _lot_transform) with one shared function all three now call: a
    #     dict with the key present returns it unchanged; a dict WITHOUT
    #     it defaults to 'arterial'.
    assert lot_road_id({'x0': 0.0, 'x1': 820.0, 'side': 'north'}) == 'arterial'
    assert lot_road_id({'x0': 0.0, 'x1': 820.0, 'side': 'north',
                         'road_id': 'arterial'}) == 'arterial'
    assert lot_road_id({'x0': 0.0, 'x1': 820.0, 'side': 'west',
                         'road_id': 'cross'}) == 'cross'

    # 26. SURVIVES A RESTART - the part of "session-start reactivation for
    #     cross-street lots" this module can actually prove headless
    #     (2026-09-03, coordinator's ask). A state carrying a cross-street
    #     placed lot AND a LEGACY placed lot with no 'road_id' key at all
    #     (the owner's own real save has four such lots, predating this
    #     key entirely) round-trips through citytick's own
    #     save_state/load_state - the SAME persistence functions a PIE
    #     restart's _read_state ultimately calls, not a bare
    #     json.dumps/loads standing in for them.
    #
    #     What this does NOT reach, named plainly rather than implied:
    #     _reactivate_placed_parcels itself (init_unreal.py, `unreal`-only
    #     - GameInstance.CityStateJSON, live pool actors,
    #     set_actor_location_and_rotation) and whether a reactivated
    #     actor's mesh/collision/label actually resolve right on screen -
    #     the same live-only gap this module's docstring has named since
    #     v0. plan_reactivation itself needs no new proof here: its own
    #     signature is (pids, pool_labels) - bare strings - it never
    #     receives a placement dict at all, so it is oblivious to road_id
    #     by construction, not merely untested against it (self-test 12
    #     already proves this genericity a different way, a pin-key
    #     namespace instead of a road-id split).
    s26 = citytick.seed_state()
    s26['parcels']['P1'] = {
        'rid': V0_RECIPE, 'tier': 2, 'width': V0_WIDTH, 'owned': True,
        'accum': 12.5,
        'placement': {'x0': 2050.0, 'x1': 2870.0, 'side': 'west',
                      'road_id': 'cross'},
    }
    s26['parcels']['P2'] = {
        'rid': V0_RECIPE, 'tier': 0, 'width': V0_WIDTH, 'owned': False,
        'accum': 0.0,
        'placement': {'x0': -7380.0, 'x1': -6560.0, 'side': 'north'},
    }  # legacy shape: no 'road_id' key, exactly the owner's real four
    citytick.save_state(s26, _SELFTEST_PATH)
    loaded26 = citytick.load_state(_SELFTEST_PATH)
    assert loaded26['parcels']['P1']['placement']['road_id'] == 'cross', (
        loaded26['parcels']['P1'])
    assert lot_road_id(loaded26['parcels']['P1']['placement']) == 'cross'
    assert loaded26['parcels']['P1']['tier'] == 2, loaded26['parcels']['P1']
    assert loaded26['parcels']['P1']['owned'] is True, loaded26['parcels']['P1']
    assert 'road_id' not in loaded26['parcels']['P2']['placement'], (
        loaded26['parcels']['P2'])
    assert lot_road_id(loaded26['parcels']['P2']['placement']) == 'arterial'
    if os.path.exists(_SELFTEST_PATH):
        os.remove(_SELFTEST_PATH)

    # 27. THE CORNER (2026-09-03, owner: "it allowed me to place where a
    #     building already existed, and they just grew into a morphed
    #     building"). A cross-street lot and an arterial lot share ground
    #     at the corner while their spans live on different axes, so the
    #     per-road span scan never compared them. The overlap scan now
    #     compares WORLD footprints (lot_rect) across every lot: an
    #     arterial south lot at x [1640, 2460] refuses a cross-street east
    #     click whose span would be y [-2460, -1640] (x 1130..2630 both) -
    #     and the mirror case, a standing cross lot refusing the arterial
    #     click - while a click one lot further along the cross street,
    #     clear of the corner, still resolves. The rectangle test contains
    #     the old span test: the same-road adjacent-lot refusal (case 3)
    #     is unchanged above.
    s27 = citytick.seed_state()
    s27['parcels']['A'] = {
        'rid': V0_RECIPE, 'tier': 0, 'width': V0_WIDTH, 'owned': False,
        'placement': {'x0': 1640.0, 'x1': 2460.0, 'side': 'south',
                      'road_id': 'arterial'},
    }
    ok27, reason27, lot27 = resolve_click(s27, 1500.0, -1900.0, pins_active=False)
    assert not ok27 and lot27 is None and 'overlap' in reason27 and 'cross' in reason27, (
        ok27, reason27, lot27)
    s27b = citytick.seed_state()
    s27b['parcels']['C'] = {
        'rid': V0_RECIPE, 'tier': 0, 'width': V0_WIDTH, 'owned': False,
        'placement': {'x0': -2460.0, 'x1': -1640.0, 'side': 'east',
                      'road_id': 'cross'},
    }
    ok27b, reason27b, lot27b = resolve_click(s27b, 1900.0, -1500.0, pins_active=False)
    assert not ok27b and lot27b is None and 'overlap' in reason27b, (
        ok27b, reason27b, lot27b)
    assert lot_rect(s27['parcels']['A']['placement']) == (1640.0, 2460.0, -2630.0, -1130.0)
    assert lot_rect(s27b['parcels']['C']['placement']) == (1130.0, 2630.0, -2460.0, -1640.0)
    print('placement self-check: 27/27 pass (pure-Python click->lot->state '
          'contract, plate bounds measured off the real board mesh and '
          'contain citylayout\'s block union, session-start reactivation '
          'planning for both placed and pinned lots, pinned-span overlap '
          'refusal mode-gated on pins_active, resolve_road MULTI-ROAD '
          'FRONTAGE NOW WIRED INTO resolve_click per RESOLVE_ROAD_NOTES.md '
          '- reduces to today\'s math on either road alone, nearest-road '
          'disambiguation, crossing refusal (reachable both directly and '
          'through resolve_click), point-to-segment not point-to-line, the '
          'owner\'s own logged off-board click, cross-street placement on '
          'both sides, in-the-road refused on whichever road actually won, '
          'lot_road_id\'s backward-compat default now the single source, '
          'CORNER overlap refused across roads by world footprint '
          'three call sites share, a cross-street lot AND a legacy '
          'road_id-less lot both surviving a real save_state/load_state '
          'round-trip intact; live cursor-trace coordinates, actor '
          'spawn/resolve, and the feel itself are NOT provable here - see '
          'module docstring, and PLACEMENT_GRID.md section 8 - the '
          'owner\'s own click on empty board is the real acceptance test)')
    if os.path.exists(_SELFTEST_PATH):
        os.remove(_SELFTEST_PATH)
