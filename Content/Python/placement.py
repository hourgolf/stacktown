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
2026-09-03 added `econrules` the same way, for PERFORMANCE_NEUTRAL alone
- place()'s own 'performance' default reads it directly rather than
carrying a second, hardcoded copy of the same neutral value that could
drift from econrules.py's own choice.
"""
import citylayout
import econrules

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


def _road_dict(seg):
    """A citystate road-segment dict ({'id','start','end','width_class'},
    Docs/ROAD_BUILD_CONTRACT.md) converted into resolve_road's own
    expected shape - +side_plus/side_minus/axis, read off the segment's
    own geometry rather than stored a second time in state (one more
    place a stored copy could drift from the geometry it describes).
    ORIENTATION IS AXIS-ALIGNED ONLY in this pass (a segment's start/end
    share either their X or their Y - draw_road below is what actually
    enforces this before a segment ever reaches state; this function
    trusts that already holds, it does not re-check it) - a horizontal
    segment (same Y) gets the arterial's own north/south convention, a
    vertical one (same X) gets the cross street's own west/east
    convention: NOT two conventions this function invents, the same two
    every self-test already exercises against the two built-ins,
    extended to whichever road a segment's own shape says it matches."""
    sx, sy = seg['start']
    ex, ey = seg['end']
    if sy == ey:
        return dict(seg, side_plus='north', side_minus='south', axis='x')
    return dict(seg, side_plus='west', side_minus='east', axis='y')


def _all_roads(state):
    """Every road resolve_click (and draw_road below) should consider:
    the two built-ins PLUS whatever the player has drawn (Docs/
    ROAD_BUILD_CONTRACT.md task b, 2026-09-04). state.get('roads', {})
    is defensive - a state predating this key (the owner's real save)
    simply has none, same backward-compat discipline lot_road_id
    already established for a different missing key. A FRESH tuple
    every call, never cached: roads can be drawn between calls, and
    this module holds no state of its own to go stale."""
    drawn = tuple(_road_dict(seg) for seg in state.get('roads', {}).values())
    return ROADS + drawn


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



def _find_road(roads, road_id):
    """The road dict named road_id within `roads` - KeyError if absent,
    loud rather than a silent None a caller might not check. `roads` is
    always a full candidate list (ROADS, or ROADS + drawn segments via
    _all_roads below) - never searched by identity, always by the same
    'id' string every lot's own road_id already carries."""
    for road in roads:
        if road['id'] == road_id:
            return road
    raise KeyError(road_id)


def lot_rect(lot, roads=ROADS):
    """World-space footprint (xmin, xmax, ymin, ymax) of a lot's PAD from
    its placement dict, ANY axis-aligned road (generalized 2026-09-04,
    Docs/ROAD_BUILD_CONTRACT.md - drawn roads are no longer just 'cross
    vs everything else'): the span along the road's own axis, and
    facade line to block back edge across it, on the lot's side. Looks
    the lot's own road up in `roads` by id (_find_road) to read its
    axis and centreline, rather than special-casing the id string
    'cross' the way this function used to - 'cross' is simply whichever
    road happens to be vertical, no longer structurally different from
    any OTHER vertical road a player might draw.

    `roads=ROADS` (the two built-ins only) is the default so every
    EXISTING caller/self-test that never passed one keeps working
    unchanged; a caller with drawn roads in play passes _all_roads
    (state) explicitly. REDUCES TO TODAY'S MATH for both built-ins,
    checked not assumed (self-test): ARTERIAL's centreline is Y=0 and
    CROSS_STREET's is X=0, so the offset below is exactly the constant
    this function used to hard-code, recovered from the road's own
    'start' instead of restated as a literal."""
    road = _find_road(roads, lot_road_id(lot))
    near, far = ROAD_HALF, ROAD_HALF + BLOCK_DEPTH
    x0, x1 = float(lot['x0']), float(lot['x1'])
    if road['axis'] == 'y':
        cx = road['start'][0]
        if lot['side'] == 'west':
            return (cx - far, cx - near, x0, x1)
        return (cx + near, cx + far, x0, x1)
    cy = road['start'][1]
    if lot['side'] == 'north':
        return (x0, x1, cy + near, cy + far)
    return (x0, x1, cy - far, cy - near)


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
    mode-gated, not a permanent board fact.

    ROADS BECAME DYNAMIC 2026-09-04 (Docs/ROAD_BUILD_CONTRACT.md task
    b): every call below that used to read the module-level ROADS
    constant now calls _all_roads(state) instead - the two built-ins
    plus whatever the player has drawn. resolve_road/_in_crossing/
    lot_rect all already took a roads argument generically; nothing in
    THEIR code changed, only what this function passes them did."""
    roads = _all_roads(state)
    road, local = resolve_road(roads, x, y)
    if road is None:
        if _in_crossing(roads, x, y):
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
    mine = lot_rect(candidate, roads)
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
        if rects_overlap(mine, lot_rect(lot, roads)):
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
    ({rid, tier, width, owned, accum, failed, performance}) PLUS one new
    key, 'placement', that pinned parcels never carry. This is
    deliberate: _sync_parcels and econrules.py read the seven original
    keys and were never written to care about extra ones, so this is
    additive by construction, not a schema migration - proven in
    self-test 6 below, not just asserted here. 'failed'/'performance'
    (task C/D, 2026-09-03) come from econrules.py's own defaults, not a
    second hardcoded copy of the same neutral value - kept in sync with
    ensure_parcel's identical choice by construction, not by convention.

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
        'owned': False, 'accum': 0.0, 'failed': False,
        'performance': econrules.PERFORMANCE_NEUTRAL,
        'placement': {'x0': lot['x0'], 'x1': lot['x1'], 'side': lot['side'],
                      'road_id': lot['road_id']},
    }
    return state, pid, True, ''


# DRAWN ROADS (2026-09-04, Docs/ROAD_BUILD_CONTRACT.md task a/b). A
# road's own "lot" for reach/reuse purposes: it must be long enough to
# hold at least one lot, or drawing it answers no question a player
# would ask it to.
MIN_ROAD_LENGTH = V0_WIDTH


def road_rect(road):
    """World-space footprint (xmin, xmax, ymin, ymax) of a road's OWN
    corridor - ROAD_HALF either side of its centreline, for its full
    length. Same rectangle shape lot_rect returns, so rects_overlap
    compares a candidate road against an existing road OR an existing
    lot with the one comparison function, nothing road-specific in
    rects_overlap itself."""
    sx, sy = road['start']
    ex, ey = road['end']
    if sy == ey:
        return (min(sx, ex), max(sx, ex), sy - ROAD_HALF, sy + ROAD_HALF)
    return (sx - ROAD_HALF, sx + ROAD_HALF, min(sy, ey), max(sy, ey))


def _next_road_id(state):
    """R1, R2, ... - the first not already in state['roads'], mirroring
    _next_pid exactly: deterministic, and a namespace ('R' + digits)
    distinct by construction from 'arterial'/'cross' (the built-ins),
    'P' + digits (placed lots), and letters (pins)."""
    n = 1
    while 'R%d' % n in state.get('roads', {}):
        n += 1
    return 'R%d' % n


def resolve_road_draw(state, x0, y0, x1, y1, width_class='avenue',
                       pins_active=True):
    """(ok, reason, road) - the click-click -> road decision, the same
    role resolve_click plays for a lot: the ONE place a drawn road is
    accepted or refused, called by both the ghost preview and draw_road
    below so they can never disagree (task c's own "the ghost shows the
    chord and refuses crossings/overlaps" needs exactly this shared
    authority - the same discipline the lot ghost already uses against
    resolve_click).

    PINNED LOTS ARE CHECKED TOO, found while writing this function's own
    self-tests, not assumed from resolve_click's shape: a pin is
    registered into state['parcels'] with no 'placement' key at all
    (ensure_parcel never adds one - only place() does, for a
    player-created lot), so the placed-lot loop below silently skips
    every pin by construction. Without a SEPARATE check a drawn road
    could cross straight through an existing pinned building - the same
    reason resolve_click keeps PINNED_SPANS as its own check, not folded
    into the placed-lot scan. `pins_active` mirrors resolve_click's own
    mode gate exactly, for the same empty-mode reason.

    AXIS-ALIGNED ONLY in this pass - a named v0 limit, not an oversight.
    resolve_click's own world-coordinate recovery (`road['start']
    [axis_idx] + along`) only recovers a correct WORLD POINT when a
    road's direction actually IS one world axis; a true diagonal road
    would need `along` recovered as a full 2D point, along the road's
    own direction vector, which nothing in resolve_click does today.
    Solving that is real, separate work (Docs/ROAD_BUILD_CONTRACT.md
    names it) - not attempted here, so this function does not accept
    input that would need it. Orientation is decided from whichever
    delta dominates (>= 3x the other, a deadzone roughly 18-72 degrees
    off each axis where neither wins): a click-pair close to horizontal
    or vertical SNAPS to exactly that (the minor coordinate set equal
    to the start point's own, then both endpoints rounded to
    POSITION_QUANTUM same as a lot's own snap); a click-pair with
    neither axis dominant REFUSES rather than silently reinterpreting a
    genuinely diagonal gesture as a straight one the player did not
    draw."""
    dx, dy = x1 - x0, y1 - y0
    if abs(dx) >= 3.0 * abs(dy):
        sx0, sy0, sx1, sy1 = _snap(x0), _snap(y0), _snap(x1), _snap(y0)
    elif abs(dy) >= 3.0 * abs(dx):
        sx0, sy0, sx1, sy1 = _snap(x0), _snap(y0), _snap(x0), _snap(y1)
    else:
        return False, (
            'too diagonal: roads must run close to north-south or '
            'east-west in this version'), None
    length = abs(sx1 - sx0) + abs(sy1 - sy0)  # axis-aligned: one term is 0
    if length < MIN_ROAD_LENGTH:
        return False, (
            'too short: %.0f uu is under the %.0f uu a single lot needs'
            % (length, MIN_ROAD_LENGTH)), None
    if not (PLATE_X_MIN <= sx0 <= PLATE_X_MAX and
            PLATE_X_MIN <= sx1 <= PLATE_X_MAX and
            PLATE_Y_MIN <= sy0 <= PLATE_Y_MAX and
            PLATE_Y_MIN <= sy1 <= PLATE_Y_MAX):
        return False, 'off-board: the drawn road would leave the plate', None
    candidate = {'id': _next_road_id(state), 'start': (sx0, sy0),
                 'end': (sx1, sy1), 'width_class': width_class}
    roads = _all_roads(state)
    mine = road_rect(_road_dict(candidate))
    for road in roads:
        if rects_overlap(mine, road_rect(road)):
            return False, (
                'crosses: the drawn road would cross the %s road'
                % road['id']), None
    for p in state['parcels'].values():
        lot = p.get('placement')
        if not lot:
            continue
        if rects_overlap(mine, lot_rect(lot, roads)):
            return False, (
                'overlap: the drawn road would cross an existing lot at '
                '[%.1f, %.1f] on the %s'
                % (lot['x0'], lot['x1'], lot_road_id(lot))), None
    if pins_active:
        for pin_x0, pin_x1, pin_side in PINNED_SPANS:
            pin_lot = {'x0': pin_x0, 'x1': pin_x1, 'side': pin_side,
                       'road_id': 'arterial'}
            if rects_overlap(mine, lot_rect(pin_lot, roads)):
                return False, (
                    'overlap: the drawn road would cross a pinned lot at '
                    '[%.1f, %.1f]' % (pin_x0, pin_x1)), None
    return True, '', candidate


def draw_road(state, x0, y0, x1, y1, width_class='avenue', pins_active=True):
    """One road-drawing attempt. (state, road_id, ok, reason) - road_id
    is None on refusal, mirroring place()'s own return shape exactly.
    On success, state['roads'][road_id] is the SAME dict
    resolve_road_draw already validated, inserted unchanged - not
    re-derived, the same discipline place() already holds for a lot."""
    ok, reason, road = resolve_road_draw(state, x0, y0, x1, y1, width_class,
                                          pins_active=pins_active)
    if not ok:
        return state, None, False, reason
    state.setdefault('roads', {})[road['id']] = road
    return state, road['id'], True, ''


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
        'owned': False, 'accum': 0.0, 'failed': False,
        'performance': econrules.PERFORMANCE_NEUTRAL,
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
    # ---- DRAWN ROADS, 2026-09-04 (Docs/ROAD_BUILD_CONTRACT.md task a/b)
    # every number below verified against a real interpreter run before
    # being written here, not hand-derived - the wall-to-wall pinned
    # frontage this session already measured (north/south pins fill
    # x 1130..6050 both signs, no gap) makes several of these points
    # genuinely easy to get wrong by a quick estimate.

    # 28. lot_rect REDUCES TO TODAY'S MATH, checked directly - both
    #     built-ins have centreline 0 in the relevant axis, so the
    #     generalized axis-lookup below must reproduce exactly the
    #     hard-coded constants this function used to return.
    assert lot_rect({'x0': 100.0, 'x1': 500.0, 'side': 'north',
                      'road_id': 'arterial'}) == (100.0, 500.0, 1130.0, 2630.0)
    assert lot_rect({'x0': 200.0, 'x1': 600.0, 'side': 'west',
                      'road_id': 'cross'}) == (-2630.0, -1130.0, 200.0, 600.0)

    # 29. _road_dict reads orientation off the segment's own geometry -
    #     horizontal (same Y) gets the arterial's north/south
    #     convention, vertical (same X) gets the cross street's
    #     west/east convention, neither stored a second time.
    horiz = {'id': 'H', 'start': (0.0, 100.0), 'end': (500.0, 100.0),
             'width_class': 'avenue'}
    vert = {'id': 'V', 'start': (300.0, 0.0), 'end': (300.0, 900.0),
            'width_class': 'avenue'}
    assert _road_dict(horiz)['side_plus'] == 'north'
    assert _road_dict(horiz)['side_minus'] == 'south'
    assert _road_dict(horiz)['axis'] == 'x'
    assert _road_dict(vert)['side_plus'] == 'west'
    assert _road_dict(vert)['side_minus'] == 'east'
    assert _road_dict(vert)['axis'] == 'y'

    # 30. _all_roads: the two built-ins alone on a fresh state, PLUS a
    #     drawn segment once one exists - a fresh tuple each call, not
    #     a cached list that could go stale between draws. Own fixture
    #     with id='R1' matching its own dict key, the same invariant
    #     draw_road always holds (state['roads'][road['id']] = road) -
    #     not the id='H' fixture above, which would prove nothing about
    #     key/id agreement.
    s30 = citytick.seed_state()
    assert [r['id'] for r in _all_roads(s30)] == ['arterial', 'cross']
    s30['roads']['R1'] = {'id': 'R1', 'start': (0.0, 100.0),
                           'end': (500.0, 100.0), 'width_class': 'avenue'}
    assert [r['id'] for r in _all_roads(s30)] == ['arterial', 'cross', 'R1']

    # 31. resolve_road_draw, HAPPY PATH: a horizontal road on the east
    #     edge margin, y=3000 (clear of the arterial's own corridor -
    #     its far edge is y=1130, and this road's OWN corridor only
    #     reaches down to y=1870, no overlap) and x 6200..7600 (clear
    #     of the north-pin frontage's own wall-to-wall span, which ends
    #     at 6050, and clear of the cross street's corridor at x=0).
    s31 = citytick.seed_state()
    ok31, reason31, road31 = resolve_road_draw(s31, 6200.0, 3000.0, 7600.0, 3000.0)
    assert ok31 and reason31 == '', (ok31, reason31)
    assert road31 == {'id': 'R1', 'start': (6200.0, 3000.0),
                       'end': (7600.0, 3000.0), 'width_class': 'avenue'}, road31

    # 32. TOO DIAGONAL: dx=1000, dy=800 - neither delta reaches 3x the
    #     other (1000 < 3*800=2400; 800 < 3*1000=3000), so this refuses
    #     rather than silently picking an axis the player did not draw.
    ok32, reason32, road32 = resolve_road_draw(s31, 0.0, 3000.0, 1000.0, 3800.0)
    assert not ok32 and road32 is None and 'too diagonal' in reason32, (
        ok32, reason32)

    # 33. TOO SHORT: a valid horizontal orientation, but only 500 uu -
    #     under MIN_ROAD_LENGTH (820, one lot's own narrowest width).
    ok33, reason33, road33 = resolve_road_draw(s31, 6200.0, 3000.0, 6700.0, 3000.0)
    assert not ok33 and road33 is None and 'too short' in reason33, (
        ok33, reason33)

    # 34. OFF-BOARD: past PLATE_X_MAX (7650).
    ok34, reason34, road34 = resolve_road_draw(s31, 7000.0, 3000.0, 8000.0, 3000.0)
    assert not ok34 and road34 is None and 'off-board' in reason34, (
        ok34, reason34)

    # 35. CROSSES AN EXISTING (BUILT-IN) ROAD: a horizontal candidate
    #     directly on the arterial's own centreline, y=0.
    ok35, reason35, road35 = resolve_road_draw(s31, 6200.0, 0.0, 7600.0, 0.0)
    assert not ok35 and road35 is None and 'crosses' in reason35 \
        and 'arterial' in reason35, (ok35, reason35)

    # 36. CROSSES A PINNED LOT - the real gap found WHILE writing this
    #     function's own self-tests, not assumed from resolve_click's
    #     shape (its own docstring explains why): y=2900 is clear of
    #     the arterial's corridor (far edge 1130, this candidate's own
    #     near edge is 2900-1130=1770) but squarely inside a north
    #     pin's own Y-band (1130..2630), and x 2000..3000 sits inside
    #     the wall-to-wall pinned frontage. Refuses with pins_active=
    #     True (the default); pins_active=False accepts the SAME
    #     coordinates - the same mode-gate resolve_click already has,
    #     extended here rather than reinvented.
    ok36, reason36, road36 = resolve_road_draw(s31, 2000.0, 2900.0, 3000.0, 2900.0)
    assert not ok36 and road36 is None and 'pinned lot' in reason36, (
        ok36, reason36)
    ok36b, reason36b, road36b = resolve_road_draw(
        s31, 2000.0, 2900.0, 3000.0, 2900.0, pins_active=False)
    assert ok36b and reason36b == '', (ok36b, reason36b)
    assert road36b == {'id': 'R1', 'start': (2000.0, 2900.0),
                        'end': (3000.0, 2900.0), 'width_class': 'avenue'}, road36b

    # 37. VERTICAL HAPPY PATH: x=3000 (clear of the cross street's own
    #     corridor at x=0 and of the north-pin frontage's own span, both
    #     nowhere near 3000 in the RELEVANT sense here since this is a
    #     vertical candidate), y 3400..4230 (=PLATE_Y_MAX exactly, length
    #     830, over the 820 minimum) - proves the SAME function handles
    #     the other axis, not just horizontal.
    ok37, reason37, road37 = resolve_road_draw(s31, 3000.0, 3400.0, 3000.0, 4230.0)
    assert ok37 and reason37 == '', (ok37, reason37)
    assert road37 == {'id': 'R1', 'start': (3000.0, 3400.0),
                       'end': (3000.0, 4230.0), 'width_class': 'avenue'}, road37

    # 38. draw_road END TO END: R1 lands in state['roads'] unchanged from
    #     what resolve_road_draw validated; a SECOND, non-crossing road
    #     gets R2 (sequencing mirrors _next_pid exactly); a candidate
    #     that would cross R1 SPECIFICALLY (not a built-in - isolated by
    #     staying clear of both corridors: x=6900 is inside R1's own
    #     x-span 6200..7600, y 2000..4230 stays clear of the arterial's
    #     far edge at 1130) is refused by name.
    s38 = citytick.seed_state()
    s38, rid38, ok38, reason38 = draw_road(s38, 6200.0, 3000.0, 7600.0, 3000.0)
    assert ok38 and rid38 == 'R1' and reason38 == '', (rid38, ok38, reason38)
    assert s38['roads']['R1'] == {
        'id': 'R1', 'start': (6200.0, 3000.0), 'end': (7600.0, 3000.0),
        'width_class': 'avenue'}, s38['roads']['R1']
    ok38x, reason38x, _ = resolve_road_draw(s38, 6900.0, 2000.0, 6900.0, 4230.0)
    assert not ok38x and 'crosses' in reason38x and 'R1' in reason38x, (
        ok38x, reason38x)
    s38, rid38b, ok38b, reason38b = draw_road(s38, 3000.0, 3400.0, 3000.0, 4230.0)
    assert ok38b and rid38b == 'R2' and reason38b == '', (
        rid38b, ok38b, reason38b)
    assert set(s38['roads'].keys()) == {'R1', 'R2'}, s38['roads'].keys()

    # 39. FULL INTEGRATION: a lot placed AGAINST a drawn road, through
    #     place() itself (task b's own point - resolve_click must
    #     resolve against a drawn road exactly as it does the built-ins).
    #     Click at (6900, 1700): 1700 is on R1's SOUTH frontage (across=
    #     -1300, |across| > ROAD_HALF=1130, within block-depth reach),
    #     nearer to R1 (1300) than to the arterial (1700) or anything
    #     else. x0/x1 snap around 6900 exactly as they would on the
    #     arterial; road_id is 'R1', not a built-in string. lot_rect
    #     (via _all_roads, since R1 is not in the default ROADS-only
    #     lookup) proves the axis-generalization end to end, not just in
    #     isolation: south of a horizontal road with centre y=3000 means
    #     y in [3000-2630, 3000-1130] = [370, 1870], read off R1's own
    #     'start' the same way it is for the arterial.
    s39 = citytick.seed_state()
    s39, _, _, _ = draw_road(s39, 6200.0, 3000.0, 7600.0, 3000.0)
    s39, pid39, ok39, reason39 = place(s39, 6900.0, 1700.0)
    assert ok39 and pid39 == 'P1' and reason39 == '', (pid39, ok39, reason39)
    assert s39['parcels']['P1']['placement'] == {
        'x0': 6490.0, 'x1': 7310.0, 'side': 'south', 'road_id': 'R1'
    }, s39['parcels']['P1']['placement']
    assert lot_rect(s39['parcels']['P1']['placement'], _all_roads(s39)) == (
        6490.0, 7310.0, 370.0, 1870.0)

    print('placement self-check: 39/39 pass (pure-Python click->lot->state '
          'contract; resolve_road multi-road frontage; cross-street and '
          'corner-overlap coverage; save/load round-trip; free placement '
          'along the road (1-27, prior sessions) PLUS drawn roads, '
          '2026-09-04 (28-39): lot_rect generalized off any road\'s own '
          'axis and reduces to today\'s math for both built-ins; '
          '_road_dict/_all_roads make placement.ROADS dynamic per state '
          '(task b); resolve_road_draw refuses off-board, too-diagonal, '
          'too-short, crossing any existing road (built-in or drawn) and '
          'crossing a pinned lot (mode-gated, the gap found while writing '
          'these tests, not assumed from resolve_click\'s own shape); '
          'draw_road persists unchanged and sequences R1/R2 like _next_pid; '
          'a lot placed against a drawn road resolves, snaps and computes '
          'its world footprint through the exact same path a built-in '
          'road lot does, proven end to end; live cursor-trace '
          'coordinates, actor spawn/resolve, and the feel itself are NOT '
          'provable here - see module docstring, and PLACEMENT_GRID.md '
          'section 8 - the owner\'s own click on empty board is the real '
          'acceptance test)')

    if os.path.exists(_SELFTEST_PATH):
        os.remove(_SELFTEST_PATH)
