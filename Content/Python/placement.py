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

# ROAD TYPES AS MECHANICS (2026-09-06). Docs/MONDAY_DECISIONS.md section 2
# decided the four types on 2026-09-01 - dirt, paved avenue, tree-lined
# boulevard, highway, the highway REFUSING frontage - and left every
# NUMBER open. Docs/NIGHT_PLAN.md's own stated assumption ("assumptions,
# stated so they can be revoked") adopts that section's PROPOSED table as
# tonight's WORKING defaults. The numbers live in econrules.json, never
# here, so the owner changes any cell of that table without touching code
# - the same discipline every other tuned number already follows, and the
# reason this module reads them through econrules.rules() rather than
# carrying a second copy.
ROAD_TYPES = ('dirt', 'avenue', 'boulevard', 'highway')

# 'avenue' IS today's road (MONDAY_DECISIONS section 2 names it "1400
# (today's road)"), so it is what a segment written before this key
# existed must mean: the two built-ins carry no 'width_class' at all, and
# every drawn segment in the owner's real citystate.json carries exactly
# 'avenue'. Same backward-compat shape lot_road_id already established for
# a different missing key - ONE place the fallback rule lives, not one per
# call site.
DEFAULT_ROAD_TYPE = 'avenue'

# VERGE: what lies between the carriageway edge and the facade line -
# pavement, kerb, and the boulevard's own trees. RECOVERED from today's
# road rather than chosen: the avenue is 1400 wide inside a corridor whose
# half is citylayout.HALF = 1130, so the verge is 1130 - 700 = 430 each
# side. Every other type is that SAME verge around its own carriageway,
# which is why road_half() below reduces EXACTLY to ROAD_HALF for an
# avenue - checked in self-test 40, not asserted here.
VERGE = ROAD_HALF - 1400.0 / 2.0


def _rules(rules):
    """econrules.rules() unless the caller already read it. Every road
    helper below takes `rules=None` so that no existing call site had to
    change, but any function that walks EVERY road (resolve_click,
    resolve_road_draw, road_rent_multiplier) reads once and threads the
    dict down: econrules.rules() re-reads the JSON from disk on every
    call BY DESIGN (the bytecode-cache trap its own module records), and
    a per-road re-read would turn one click into a dozen file reads."""
    return econrules.rules() if rules is None else rules


def road_type(road):
    """A road's type, one of ROAD_TYPES. See DEFAULT_ROAD_TYPE for why a
    missing 'width_class' is 'avenue' rather than an error. An UNKNOWN
    name IS an error, loudly: a typo'd type would otherwise silently
    price, rent and render as whatever the fallback happens to be, which
    is exactly the shape of quiet wrong answer this project has paid for
    three times (HANDOFF section 5)."""
    t = road.get('width_class', DEFAULT_ROAD_TYPE)
    if t not in ROAD_TYPES:
        raise ValueError('unknown road type %r (expected one of %s)'
                         % (t, ', '.join(ROAD_TYPES)))
    return t


def road_half(road, rules=None):
    """Centreline to facade line for THIS road - the per-type
    generalization of the ROAD_HALF constant, which stays defined above
    as what it always was: the avenue's own number, and the one the board
    geometry was authored against. A wider road pushes its OWN frontage
    line further out; it does not touch BLOCK_DEPTH, which measures the
    block behind the frontage and has nothing to do with the road."""
    return _rules(rules)['road_width_%s' % road_type(road)] / 2.0 + VERGE


def road_max_reach(road, rules=None):
    """resolve_road's outer claim distance for THIS road - the same sum
    ROAD_MAX_REACH is, with the road's own half in place of the constant,
    so a highway's reach starts where its own pavement ends rather than
    where an avenue's would."""
    return road_half(road, rules) + BLOCK_DEPTH + REACH_SLACK


def road_has_frontage(road, rules=None):
    """False for a road no lot may front - today the highway alone
    (MONDAY_DECISIONS section 2: the highway "REFUSES frontage"). A RULES
    KEY per type, not an `if road_type(road) == 'highway'`, so the owner
    revokes it by editing a number; and read as a flag by every caller,
    so nothing below has to know which type is the special one."""
    return bool(_rules(rules)['road_frontage_%s' % road_type(road)])


def road_length(road):
    """Centreline length. Axis-aligned in this pass, but written as a
    true 2D distance so it is already right when segments stop being."""
    (sx, sy), (ex, ey) = road['start'], road['end']
    return ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5


def road_cost(road, rules=None):
    """What drawing THIS road costs, in the same money citytick spends:
    its type's per-100-uu price times its own length. DERIVED from the
    segment every time, never stored on it - a stored cost is one more
    copy that can disagree with the geometry it prices, the same reason
    _road_dict reads orientation off start/end instead of storing it."""
    r = _rules(rules)
    return (r['road_cost_per_100uu_%s' % road_type(road)]
            * road_length(road) / 100.0)


def path_neighbours(roads, road):
    """The segments of `road`'s own path that JOIN it end to end - the one
    whose end is this segment's start, and the one whose start is its end.
    Found by matching endpoints rather than by id order, so it stays right
    however a path's ids were allocated.

    Exists because of a real collision between two things section 5 of
    ROADS_AS_MECHANIC asks for at once: the curve is sampled at the 410
    WIDTH_QUANTUM, and the narrowest lot in the catalogue is 820 - two
    quanta. So no lot fits inside a single chord's own span, and before this
    every click on a curve was refused with "off-board: snapped span exceeds
    the R3 road" on completely open ground. A lot IS a chord (section 5.4)
    and a chord it is; it simply spans more than one of them, so the bound
    its span is checked against has to be the run of joined chords rather
    than the one it happens to sit on."""
    out = []
    pid = road_path_id(road)
    for other in roads:
        if other['id'] == road['id'] or road_path_id(other) != pid:
            continue
        if (other['end'] == road['start'] or other['start'] == road['end']
                or other['start'] == road['start']
                or other['end'] == road['end']):
            out.append(other)
    return out


def path_span(roads, road, rules=None):
    """(s_min, s_max) - the projection range a lot on `road` may occupy,
    measured in `road`'s own direction: its own span, widened by whatever
    its joined neighbours reach in that direction.

    ONLY THE IMMEDIATE NEIGHBOURS, deliberately. Walking the whole path
    would let a lot's span run round a bend and come out somewhere the pad
    - which is a straight rectangle in this chord's frame - does not go. One
    chord either side is enough for the 820 lot the collision above is
    about, and it is the largest claim that stays honest about the pad being
    straight."""
    frame = road_frame(road)
    ux, uy, s_min = frame[2], frame[3], frame[7]
    s_max = s_min + frame[6]
    for other in path_neighbours(roads, road):
        for pt in (other['start'], other['end']):
            s = pt[0] * ux + pt[1] * uy
            s_min = min(s_min, s)
            s_max = max(s_max, s)
    return s_min, s_max


def road_path_id(road):
    """Which ROAD a segment belongs to. A curve drawn as one gesture is many
    segments (draw_road_path below) that share a 'path'; a straight road is
    its own path, and so is anything written before this key existed - the
    same backward-compat shape lot_road_id established, one place again."""
    return road.get('path', road['id'])


def _catmull_rom(nodes, samples_per_span=64):
    """A uniform Catmull-Rom through `nodes`, densely sampled.

    ROADS_AS_MECHANIC section 5's own shape: "a Catmull-Rom through the
    committed nodes, sampled to a polyline at the 410 quantum". This is the
    dense half; _sample_path below does the arc-length resampling.

    THE END TANGENTS ARE EXTRAPOLATED, not duplicated: the phantom control
    point before the first node is 2*P0 - P1, which continues the line the
    first two nodes make. Duplicating the endpoint instead (the other common
    choice) makes the curve leave its first node along the chord to the
    THIRD, so a road would start off in a direction the player did not draw.
    """
    pts = list(nodes)
    if len(pts) < 2:
        return list(pts)
    ctrl = [(2.0 * pts[0][0] - pts[1][0], 2.0 * pts[0][1] - pts[1][1])]
    ctrl += pts
    ctrl.append((2.0 * pts[-1][0] - pts[-2][0], 2.0 * pts[-1][1] - pts[-2][1]))
    out = [pts[0]]
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = ctrl[i], ctrl[i + 1], ctrl[i + 2], ctrl[i + 3]
        for k in range(1, samples_per_span + 1):
            t = float(k) / samples_per_span
            t2, t3 = t * t, t * t * t
            out.append((
                0.5 * ((2.0 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2.0 * p0[0] - 5.0 * p1[0] + 4.0 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3.0 * p1[0] - 3.0 * p2[0] + p3[0]) * t3),
                0.5 * ((2.0 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2.0 * p0[1] - 5.0 * p1[1] + 4.0 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3.0 * p1[1] - 3.0 * p2[1] + p3[1]) * t3)))
    return out


def sample_path(nodes, spacing=WIDTH_QUANTUM):
    """The curve through `nodes` as a polyline whose vertices are `spacing`
    apart ALONG THE CURVE - 410, the width quantum the whole board is built
    on, so a chord is one lot-width unit of road.

    Arc-length resampling, not parameter-space: a Catmull-Rom's parameter
    runs faster on the outside of a bend, so sampling at even t would give
    long chords through corners and short ones on the straights - the exact
    places where a chord's error against the curve is largest.

    The LAST node is always a vertex, whatever the spacing leaves over. A
    road that stopped 300 uu short of where the player clicked would be a
    different road from the one they drew; a slightly short final chord is
    not. Every vertex is snapped to the position grid, like a lot's own
    span and a straight road's endpoints."""
    dense = _catmull_rom(nodes)
    if len(dense) < 2:
        return [(_snap(p[0]), _snap(p[1])) for p in dense]
    out = [dense[0]]
    carried = 0.0
    for i in range(1, len(dense)):
        ax, ay = dense[i - 1]
        bx, by = dense[i]
        seg = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
        if seg == 0.0:
            continue
        pos = 0.0
        while carried + (seg - pos) >= spacing:
            step = spacing - carried
            pos += step
            t = pos / seg
            out.append((ax + (bx - ax) * t, ay + (by - ay) * t))
            carried = 0.0
        carried += seg - pos
    if out[-1] != dense[-1]:
        out.append(dense[-1])
    # THE LEFTOVER IS MERGED, not left as a stub. Whatever the spacing does
    # not divide evenly comes out as a final chord of anything from 0 to 410,
    # and a 50 uu chord is a road segment with a 2260 uu corridor and no
    # length - a bump on the board and a hole in the frontage. If the last
    # chord is under half a spacing, the vertex before the endpoint is
    # dropped, making one final chord of up to one and a half spacings.
    if len(out) >= 3:
        last = ((out[-1][0] - out[-2][0]) ** 2
                + (out[-1][1] - out[-2][1]) ** 2) ** 0.5
        if last < spacing / 2.0:
            del out[-2]
    snapped = [(_snap(p[0]), _snap(p[1])) for p in out]
    # The snap can collide two vertices that were under a quantum apart.
    deduped = [snapped[0]]
    for p in snapped[1:]:
        if p != deduped[-1]:
            deduped.append(p)
    return deduped


def road_material_name(road):
    """The material instance the engine side loads for this road's
    surface - MI_road_dirt / _avenue / _boulevard / _highway. Formatted
    HERE so the C++ port, the design lane and this module all read the
    same string off the same type rather than each formatting its own."""
    return 'MI_road_%s' % road_type(road)


def _road_dict(seg):
    """A citystate road-segment dict ({'id','start','end','width_class'},
    Docs/ROAD_BUILD_CONTRACT.md) converted into resolve_road's own
    expected shape - +side_plus/side_minus/axis, read off the segment's
    own geometry rather than stored a second time in state (one more
    place a stored copy could drift from the geometry it describes).
    ANY DIRECTION since 2026-09-06 (curved roads, item 11). The names come
    off the NORMAL, not off a same-X / same-Y test: the normal is the
    direction rotated +90 degrees, and whichever of its components
    dominates decides which pair of names applies and its sign decides
    which is `side_plus`. That is not a third convention - it REDUCES
    EXACTLY to the two the built-ins already use (a horizontal road's
    normal is +Y, so plus is north; a vertical one's is -X, so plus is
    west), and it is the only rule that stays correct for a road running
    down and to the right, where the dominant axis of the DIRECTION and
    the side the normal actually points to disagree.

    `axis` is now the dominant axis of the road's run, kept because the
    fixtures and the lot frame still read it; nothing decides geometry
    from it any more."""
    sx, sy = seg['start']
    ex, ey = seg['end']
    dx, dy = ex - sx, ey - sy
    length = (dx * dx + dy * dy) ** 0.5
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux                      # +90 degrees, the same normal
    if abs(ny) >= abs(nx):
        plus, minus = ('north', 'south') if ny >= 0.0 else ('south', 'north')
        axis = 'x'
    else:
        plus, minus = ('east', 'west') if nx >= 0.0 else ('west', 'east')
        axis = 'y'
    return dict(seg, side_plus=plus, side_minus=minus, axis=axis)


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


def _in_crossing(roads, x, y, rules=None):
    """True if `(x, y)` falls inside MORE THAN ONE road's own in-corridor
    band (`abs(across) < ROAD_HALF`, standing on that road's pavement,
    not its frontage) with its `along` in-segment - the click is on
    pavement two roads physically share, so no single road's claim is
    the honest answer. Factored out of `resolve_road` so it and
    `resolve_click` (which wants this as its OWN, distinctly-worded
    refusal, not folded into "off-board") can never disagree about the
    rule. NOT the corner-lot question (RESOLVE_ROAD_NOTES.md section 7,
    still open, still unanswered here) - the narrower, unambiguous case
    of standing on the pavement itself where two roads overlap.

    PER-TYPE CORRIDOR since 2026-09-06: the band is the ROAD'S OWN half
    (road_half), not the one avenue constant - a highway is 2000 wide and
    its pavement has to be 2000 wide here too, or a click standing on it
    would be offered frontage on the road it is standing in.

    COUNTED BY PATH, not by segment (curved roads, item 11). A drawn curve
    is many straight segments 410 uu apart whose corridors overlap almost
    everywhere along it - by construction, not by accident - so counting
    segments would make the whole of every curve 'the crossing' and refuse
    every lot on it. Segments of ONE road are one road here. A single
    straight road is its own path (road_path_id), so nothing about the
    two built-ins or a one-segment draw changes."""
    r = _rules(rules)
    seen = set()
    for road in roads:
        along, across, length = _project_to_road(road, x, y)
        if 0.0 <= along <= length and abs(across) < road_half(road, r):
            seen.add(road_path_id(road))
    return len(seen) > 1


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


def _road_distance(road, x, y):
    """(along, across, dist) for one road - the projection above plus the
    point-to-SEGMENT distance resolve_road selects on. Factored out
    2026-09-06 so the frontage check and the no-frontage explanation
    (resolve_click) measure with the ONE function rather than each
    carrying its own copy of the clamp. `dist` is the perpendicular
    offset when the click's `along` falls inside the segment's own
    [0, length], else the distance to whichever endpoint is nearer - a
    click past a short segment's end must not claim frontage on a road
    that does not reach that far."""
    along, across, length = _project_to_road(road, x, y)
    if 0.0 <= along <= length:
        return along, across, abs(across)
    clamped = max(0.0, min(length, along))
    return along, across, ((along - clamped) ** 2 + across ** 2) ** 0.5


def _nearest_no_frontage(roads, x, y, rules=None):
    """The nearest road that REFUSES frontage and whose reach the point
    is inside, or None. Exists only so resolve_click can say WHY a click
    beside a highway is refused - without it the answer is resolve_road's
    generic "not within reach of any road", which is true and useless
    standing on a highway's verge with the highway right there."""
    r = _rules(rules)
    best, best_dist = None, None
    for road in roads:
        if road_has_frontage(road, r):
            continue
        _, _, dist = _road_distance(road, x, y)
        if dist > road_max_reach(road, r):
            continue
        if best_dist is None or dist < best_dist:
            best, best_dist = road, dist
    return best


def resolve_road(roads, x, y, rules=None):
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
    way, before nearest-road selection ever runs.

    TWO CHANGES 2026-09-06, road types (MONDAY_DECISIONS section 2). A
    road that refuses frontage is not a candidate at all - the highway
    carries traffic past the city, and a lot never faces one. And the
    reach bound became the ROAD'S OWN (road_max_reach), applied as a
    FILTER before nearest-road selection rather than as a test on the
    winner afterwards: with one reach for every road the two orders are
    identical (if the nearest is out of reach, all of them are), but with
    per-type reaches a near, narrow road would otherwise win the
    comparison and then fail the bound, hiding a wider road that legally
    reaches the point. Both reduce to the old behaviour exactly while
    every road is an avenue - self-tests 13-19 above are unchanged and
    still pass, which is the check."""
    r = _rules(rules)
    if _in_crossing(roads, x, y, r):
        return None, None
    best = None
    best_dist = None
    for road in roads:
        if not road_has_frontage(road, r):
            continue
        along, across, dist = _road_distance(road, x, y)
        if dist > road_max_reach(road, r):
            continue
        if best_dist is None or dist < best_dist:
            best = (road, along, across)
            best_dist = dist
    if best is None:
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


def lot_quad(lot, roads=ROADS, rules=None):
    """The four world corners of a lot's PAD, for a road of ANY direction
    (2026-09-06, item 11). The band between the lot's two projections
    (x0, x1) and its road's frontage line and block back edge, on the
    lot's own side.

    THE SIDE IS READ OFF THE ROAD'S OWN NAMES, never off the literal
    'north' or 'west': `side_plus` is whichever way the normal points for
    THIS road (_road_dict), so a lot recorded 'north' against a road whose
    plus side is south sits on the minus side - which is the same ground,
    named from the other end."""
    road = _find_road(roads, lot_road_id(lot))
    frame = road_frame(road)
    near = road_half(road, rules)
    far = near + BLOCK_DEPTH
    sign = 1.0 if lot['side'] == road['side_plus'] else -1.0
    return _quad(frame, float(lot['x0']), float(lot['x1']),
                 sign * near, sign * far)


def lot_rect(lot, roads=ROADS, rules=None):
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
    'start' instead of restated as a literal.

    PER-TYPE FRONTAGE LINE 2026-09-06: `near` is the road's OWN half
    (road_half), so a lot on a dirt track sits 880 uu off its centreline
    and one on a highway would sit 1430 - if a highway could be fronted,
    which it cannot. BLOCK_DEPTH is unchanged and deliberately so: the
    block behind a lot is the same block whatever road it faces.

    NOW THE BOUNDING BOX of lot_quad, which is the same rectangle for an
    axis-aligned road and the honest envelope for a diagonal one. Every
    existing caller keeps its four-number answer; the OVERLAP scans moved
    to the quads themselves, because a diagonal lot's bounding box is much
    bigger than the lot and would refuse clicks that are fine."""
    return quad_rect(lot_quad(lot, roads, rules))


def rects_overlap(a, b):
    return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]


def road_frame(road):
    """(ox, oy, ux, uy, nx, ny, length, s0) for a road - its start point, its
    unit direction, its unit normal, its length, and s0, the scalar
    projection of its start onto its own direction.

    s0 IS WHAT MAKES A LOT'S SPAN MEAN SOMETHING ON A DIAGONAL. A placed
    lot stores x0/x1, which have always been world coordinates on the
    road's axis; generalized, they are the scalar projection of the span
    onto the road's unit direction, and a point at projection s sits at
    `start + u * (s - s0)`. For the arterial u is +X and s0 is
    PLATE_X_MIN, so s IS the world x and the recovery is the identity -
    checked in self-test 51, not asserted here. For the cross street u is
    +Y and s is the world y, likewise. So no lot already saved changes
    meaning, which is only true because a drawn segment's endpoints are
    ORDERED (resolve_road_draw): u could otherwise point either way and s
    would be the world coordinate NEGATED on half the roads."""
    ox, oy = road['start']
    ex, ey = road['end']
    dx, dy = ex - ox, ey - oy
    length = (dx * dx + dy * dy) ** 0.5
    ux, uy = dx / length, dy / length
    return ox, oy, ux, uy, -uy, ux, length, ox * ux + oy * uy


def _point_at(frame, s, offset):
    """World point at projection `s` along the road, `offset` off its
    centreline on the +normal side."""
    ox, oy, ux, uy, nx, ny, _length, s0 = frame
    t = s - s0
    return (ox + ux * t + nx * offset, oy + uy * t + ny * offset)


def _quad(frame, s0, s1, off0, off1):
    """The four corners of a band between two projections and two offsets,
    in order round the shape (which SAT needs; a figure-eight is not a
    convex hull and would separate on axes it should not)."""
    return (_point_at(frame, s0, off0), _point_at(frame, s1, off0),
            _point_at(frame, s1, off1), _point_at(frame, s0, off1))


def quad_rect(quad):
    """The axis-aligned bounding box of a quad, in rects_overlap's shape."""
    xs = [p[0] for p in quad]
    ys = [p[1] for p in quad]
    return (min(xs), max(xs), min(ys), max(ys))


def quads_overlap(a, b):
    """Separating-axis test on two convex quads. Touching is NOT
    overlapping, the same strictness rects_overlap has - which is what
    lets a lot sit exactly on its own road's frontage line.

    REDUCES EXACTLY TO rects_overlap for two axis-aligned quads: their
    edge normals are the world axes, the projections are the same numbers,
    and a separation found with >= is the same as rects_overlap's strict
    <. Self-test 50 checks that against the existing lot rectangles rather
    than trusting the argument."""
    for poly in (a, b):
        for i in range(len(poly)):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % len(poly)]
            ax, ay = -(y1 - y0), x1 - x0        # edge normal
            n = (ax * ax + ay * ay) ** 0.5
            if n == 0.0:
                continue
            ax, ay = ax / n, ay / n
            amin = min(p[0] * ax + p[1] * ay for p in a)
            amax = max(p[0] * ax + p[1] * ay for p in a)
            bmin = min(p[0] * ax + p[1] * ay for p in b)
            bmax = max(p[0] * ax + p[1] * ay for p in b)
            if amax <= bmin or bmax <= amin:
                return False
    return True


def resolve_click(state, x, y, pins_active=True, width=V0_WIDTH, rules=None):
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
    `along` snapped directly. The reason on record until 2026-09-06
    ("neither plate minimum is a multiple of WIDTH_QUANTUM") was true
    of the 410 snap and is stale since the snap became POSITION_QUANTUM
    (10) on 2026-09-03: both minima ARE multiples of 10. The order still
    matters, for a different reason: round() is half-to-even, so a tie
    breaks on the parity of the integer part, and snapping in road
    space can land one quantum away from snapping in world space.
    (Found by the engineering seat's mutation pass while porting this
    file to C++.) Converting to world space first makes the arterial
    case reduce EXACTLY to the
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
    r = _rules(rules)
    roads = _all_roads(state)
    road, local = resolve_road(roads, x, y, r)
    if road is None:
        if _in_crossing(roads, x, y, r):
            return False, (
                'in the crossing: (%.1f, %.1f) is pavement shared by '
                'more than one road' % (x, y)), None
        # A refusal a player can act on, rather than the true-but-useless
        # 'off-board' they would otherwise get while standing on a
        # highway's verge with the highway right in front of them.
        near = _nearest_no_frontage(roads, x, y, r)
        if near is not None:
            return False, (
                'no frontage: the %s is a %s and nothing may face it'
                % (near['id'], road_type(near))), None
        return False, (
            'off-board: (%.1f, %.1f) is not within reach of any road'
            % (x, y)), None
    along, across, side = local['along'], local['across'], local['side']
    _, _, length = _project_to_road(road, x, y)
    half = road_half(road, r)
    if 0.0 <= along <= length and abs(across) < half:
        return False, (
            'in the road: |across|=%.0f is inside the %s corridor '
            '(half %.0f)' % (abs(across), road['id'], half)), None
    # PROJECTION SPACE, 2026-09-06 (item 11). x0/x1 have always been world
    # coordinates on the road's axis; generalized, they are the scalar
    # projection of the span onto the road's own unit direction, and the
    # world point at projection s is start + u * (s - s0). For the arterial
    # s0 is PLATE_X_MIN and along is x - PLATE_X_MIN, so s0 + along IS x -
    # the identity self-test 13 already checks, unchanged; for the cross
    # street the same holds in y. So this is one line different from the
    # world_coord it replaces, and no lot already saved changes meaning.
    frame = road_frame(road)
    s_min, s_max = path_span(roads, road, r)
    x0 = _snap(frame[7] + along - width / 2.0)
    x1 = x0 + width
    if x0 < s_min or x1 > s_max:
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
    # A PAD CAN HANG OFF THE PLATE, and this is where the check would go.
    # NOT ADDED TONIGHT, deliberately, and raised on Docs/BOARD.md instead:
    # the span bound above keeps a lot inside its ROAD, and for the two
    # built-ins the road spans the plate so those were the same thing. They
    # are not the same thing for a road drawn near an edge - the first curve
    # drawn along the southern margin put a pad at y = -5740 against a plate
    # that stops at -4230, and self-test 52's own 45 degree lot reaches
    # y = 5150 against a plate that stops at 4230.
    #
    # It is a real, PRE-EXISTING gap (a straight road drawn near an edge does
    # it too), the fix is four comparisons against quad_rect(lot_quad(...)),
    # and it moves where lots may go on boards that already exist - the same
    # reason the frontage-corridor gap above was raised rather than closed.
    # The owner's call, not curved roads'.
    # QUADS, not bounding boxes: a diagonal lot's box is much bigger than the
    # lot and would refuse clicks that are fine. quads_overlap reduces exactly
    # to rects_overlap while everything is axis-aligned (self-test 50).
    mine = lot_quad(candidate, roads, r)
    # NO-FRONTAGE CORRIDORS, added 2026-09-06 with road types. Every
    # other refusal here is reached THROUGH the road a lot faces, so a
    # road nothing may face is unguarded by construction: the highway is
    # not a candidate in resolve_road, is not a lot, and is not a pin, so
    # without this a lot fronting some other road could be laid straight
    # across two thousand uu of motorway.
    #
    # DELIBERATELY NOT ALL ROADS. A lot can also overlap a FRONTAGE road's
    # corridor - self-test 39's own lot does, sitting in the 740 uu the
    # arterial and a road drawn 3000 uu from it leave between their
    # pavements, which is less than BLOCK_DEPTH. That is a real,
    # pre-existing gap, found by widening this check to every road and
    # watching test 39 refuse; fixing it changes where lots may go on
    # boards that already exist, which is the owner's call and not part of
    # road types. RAISED on Docs/BOARD.md, not silently fixed here.
    for other in roads:
        if road_has_frontage(other, r):
            continue
        if quads_overlap(mine, road_quad(other, r)):
            return False, (
                'in the road: [%.1f, %.1f] would run across the %s, a %s'
                % (x0, x1, other['id'], road_type(other))), None
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
        if quads_overlap(mine, lot_quad(lot, roads, r)):
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


def place(state, x, y, pins_active=True, width=V0_WIDTH, rules=None):
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
    ok, reason, lot = resolve_click(state, x, y, pins_active=pins_active,
                                    width=width, rules=rules)
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


def road_quad(road, rules=None):
    """The four world corners of a road's own corridor - its half either
    side of its centreline, for its full length, at any direction."""
    frame = road_frame(road)
    half = road_half(road, rules)
    length, s0 = frame[6], frame[7]
    return _quad(frame, s0, s0 + length, -half, half)


def road_rect(road, rules=None):
    """World-space footprint (xmin, xmax, ymin, ymax) of a road's OWN
    corridor - road_half either side of its centreline (its own type's,
    since 2026-09-06: a dirt track's footprint is narrower than an
    avenue's and a highway's is wider), for its full length. Same rectangle shape lot_rect returns, so rects_overlap
    compares a candidate road against an existing road OR an existing
    lot with the one comparison function, nothing road-specific in
    rects_overlap itself."""
    return quad_rect(road_quad(road, rules))


def _next_road_id(state):
    """R1, R2, ... - the first not already in state['roads'], mirroring
    _next_pid exactly: deterministic, and a namespace ('R' + digits)
    distinct by construction from 'arterial'/'cross' (the built-ins),
    'P' + digits (placed lots), and letters (pins)."""
    n = 1
    while 'R%d' % n in state.get('roads', {}):
        n += 1
    return 'R%d' % n


def _rect_distance(a, b):
    """Shortest distance between two axis-aligned rectangles, 0.0 when
    they touch or overlap. The gap on each axis (negative where the spans
    already intersect, clamped to zero), then the hypotenuse of the two -
    so a diagonal neighbour is measured corner to corner rather than
    along whichever axis happens to be larger."""
    dx = max(0.0, a[0] - b[1], b[0] - a[1])
    dy = max(0.0, a[2] - b[3], b[2] - a[3])
    return (dx * dx + dy * dy) ** 0.5


def road_rent_multiplier(state, lot, rules=None):
    """What the roads around a lot do to its rent - MONDAY_DECISIONS
    section 2's own "the part that makes a type a planning decision
    rather than a price".

    TWO MECHANISMS, because that table describes two. A lot's OWN road
    multiplies by its type (dirt 0.75, avenue 1.0, boulevard 1.25). A
    road that refuses frontage - today the highway alone - multiplies
    every lot within road_highway_reach of its PAVEMENT by its own
    figure. That second one has to be proximity rather than frontage:
    the highway refuses frontage, so no lot ever fronts one, and a
    frontage-only reading would leave road_rent_mult_highway dead in the
    rules file. Written against the frontage FLAG, never the name
    'highway', so nothing here has to know which type is the special one.

    THEY MULTIPLY. A dirt track beside a motorway is 0.75 * 1.1 = 0.825;
    a boulevard beside one is 1.375. FLAGGED FOR THE OWNER (Docs/
    BOARD.md): "every lot within 2,000 uu of it rents at 1.1x" can also
    be read as an absolute that REPLACES the road's own figure, which
    would let a dirt lot beside a highway out-earn a boulevard lot away
    from one. Multiplying composes and keeps the type ordering intact, so
    it is what is built - one word from the owner changes it.

    DISTANCE IS PAVEMENT TO PAD, rectangle to rectangle, zero when they
    touch. "Within 2,000 uu of it" reads as how far the lot is from the
    road you can see; measuring from the centreline instead would spend
    1,430 of the 2,000 crossing the highway's own corridor before it
    reached the first lot at all.

    NOT APPLIED HERE, and that is deliberate: citytick.tick() is the
    coordinator's tonight (2026-09-06 relay, "do not touch it"), so this
    is the pure, tested function rent gets multiplied by, left un-wired
    rather than wired by two hands at once."""
    r = _rules(rules)
    roads = _all_roads(state)
    own = _find_road(roads, lot_road_id(lot))
    mult = r['road_rent_mult_%s' % road_type(own)]
    reach = r['road_highway_reach']
    mine = lot_rect(lot, roads, r)
    for road in roads:
        if road_has_frontage(road, r):
            continue
        if _rect_distance(mine, road_rect(road, r)) <= reach:
            mult *= r['road_rent_mult_%s' % road_type(road)]
    return mult


def resolve_road_draw(state, x0, y0, x1, y1, width_class='avenue',
                       pins_active=True, rules=None):
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

    ANY DIRECTION since 2026-09-06 (item 11). The axis-aligned limit this
    docstring used to name is gone, and what removed it was
    resolve_click's world recovery moving into PROJECTION SPACE: a lot's
    x0/x1 are the scalar projection of its span onto the road's own unit
    direction, and the point at projection s is start + u * (s - s0),
    which is a correct world point at any angle. That change is
    backward-compatible only because a drawn segment's endpoints are
    ORDERED (below) - u could otherwise point either way.

    The 3x dominance test survives as a SNAP THRESHOLD rather than a
    refusal: a click-pair close to horizontal or vertical SNAPS to exactly
    that (the minor coordinate set equal to the start point's own, then
    both endpoints rounded to
    POSITION_QUANTUM same as a lot's own snap), because a player aiming
    down a street should get a straight one and not a road two degrees
    out; a click-pair with neither axis dominant is now taken AS DRAWN,
    which is the whole of item 11's first half.

    TYPE AND PRICE 2026-09-06 (MONDAY_DECISIONS section 2). `width_class`
    was already carried on every segment and its one existing value,
    'avenue', is already one of the four type names - so it IS the type
    now and no schema changed. Two refusals joined the list: an
    unrecognised type (a boundary check here, not road_type's internal
    raise - a bad string arriving from a UI deserves a reason, not a
    traceback), and one the city can feel, "can't afford". Cost is
    checked LAST, after every geometric refusal: a road that crosses a
    building is illegal whatever the balance, and quoting the price of a
    road that could never have been drawn is noise."""
    r = _rules(rules)
    if width_class not in ROAD_TYPES:
        return False, (
            'unknown road type %r: expected one of %s'
            % (width_class, ', '.join(ROAD_TYPES))), None
    dx, dy = x1 - x0, y1 - y0
    # ANY DIRECTION since 2026-09-06 (item 11). What used to be a REFUSAL is
    # now a SNAP THRESHOLD, at the same 3x dominance (about 18 degrees off an
    # axis): a drag that close to horizontal or vertical still snaps to exactly
    # that, because a player aiming down a street should get a straight one and
    # not a road two degrees out. Anything else is now the road they drew,
    # instead of a refusal telling them the version cannot do it.
    #
    # The snap branches are UNCHANGED, which is what keeps every case from 28
    # on answering exactly as before; only the else arm moved from a refusal to
    # a free-direction road.
    if abs(dx) >= 3.0 * abs(dy):
        sx0, sy0, sx1, sy1 = _snap(x0), _snap(y0), _snap(x1), _snap(y0)
    elif abs(dy) >= 3.0 * abs(dx):
        sx0, sy0, sx1, sy1 = _snap(x0), _snap(y0), _snap(x0), _snap(y1)
    else:
        sx0, sy0, sx1, sy1 = _snap(x0), _snap(y0), _snap(x1), _snap(y1)
    # CANONICAL DIRECTION, 2026-09-06. Which WAY the player dragged must not
    # change where the road's lots go, and until this line it did - badly.
    # resolve_click recovers a lot's world position as
    # `road['start'][axis] + along`, and `along` is measured along the
    # segment's own direction, so a road drawn east-to-west put every lot at
    # 2 * start_x - x: a MIRROR IMAGE about the start point. The same drag
    # also flipped the side names, because the normal is the direction rotated
    # +90 degrees, so a click south of an east-to-west road came back 'north'.
    # Found while generalizing this function to arbitrary directions (item 11),
    # where the sign of the direction stops being an edge case; reachable
    # today by dragging right to left, and silent whenever the mirrored span
    # still lands on the road.
    #
    # Ordering the endpoints is the fix at the SOURCE rather than at each of
    # the three places that read the direction. It changes nothing else: the
    # length is an absolute value, road_rect takes min/max, and _road_dict
    # reads orientation off the shape. The player gets the road they drew.
    if (sx1, sy1) < (sx0, sy0):
        sx0, sy0, sx1, sy1 = sx1, sy1, sx0, sy0
    length = ((sx1 - sx0) ** 2 + (sy1 - sy0) ** 2) ** 0.5
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
    mine = road_quad(_road_dict(candidate), r)
    for road in roads:
        if quads_overlap(mine, road_quad(road, r)):
            return False, (
                'crosses: the drawn road would cross the %s road'
                % road['id']), None
    for p in state['parcels'].values():
        lot = p.get('placement')
        if not lot:
            continue
        if quads_overlap(mine, lot_quad(lot, roads, r)):
            return False, (
                'overlap: the drawn road would cross an existing lot at '
                '[%.1f, %.1f] on the %s'
                % (lot['x0'], lot['x1'], lot_road_id(lot))), None
    if pins_active:
        for pin_x0, pin_x1, pin_side in PINNED_SPANS:
            pin_lot = {'x0': pin_x0, 'x1': pin_x1, 'side': pin_side,
                       'road_id': 'arterial'}
            if quads_overlap(mine, lot_quad(pin_lot, roads, r)):
                return False, (
                    'overlap: the drawn road would cross a pinned lot at '
                    '[%.1f, %.1f]' % (pin_x0, pin_x1)), None
    cost = road_cost(candidate, r)
    if state['money'] < cost:
        return False, (
            "can't afford: a %.0f uu %s costs %.2f, money is %.2f"
            % (length, width_class, cost, state['money'])), None
    return True, '', candidate


def draw_road(state, x0, y0, x1, y1, width_class='avenue', pins_active=True,
               rules=None):
    """One road-drawing attempt. (state, road_id, ok, reason) - road_id
    is None on refusal, mirroring place()'s own return shape exactly.
    On success, state['roads'][road_id] is the SAME dict
    resolve_road_draw already validated, inserted unchanged - not
    re-derived, the same discipline place() already holds for a lot.

    THE MONEY MOVES HERE, and only here: resolve_road_draw decides
    whether the city can pay (so the ghost preview can say "can't
    afford" without spending anything), and this function is what
    actually spends it. Deducted from the SAME candidate that was
    priced, through the same road_cost, so the amount charged cannot
    differ from the amount quoted. The rules dict is read once and
    threaded into both, or a quote and its charge could straddle an edit
    to econrules.json mid-click."""
    r = _rules(rules)
    ok, reason, road = resolve_road_draw(state, x0, y0, x1, y1, width_class,
                                          pins_active=pins_active, rules=r)
    if not ok:
        return state, None, False, reason
    state['money'] -= road_cost(road, r)
    state.setdefault('roads', {})[road['id']] = road
    return state, road['id'], True, ''


def _next_path_id(state):
    """C1, C2, ... - the first not already claimed by a segment in state.
    A namespace distinct by construction from the segment ids (R + digits),
    the placed lots (P + digits) and the pins (letters)."""
    taken = {road_path_id(seg) for seg in state.get('roads', {}).values()}
    n = 1
    while 'C%d' % n in taken:
        n += 1
    return 'C%d' % n


def resolve_road_path(state, nodes, width_class='avenue', pins_active=True,
                       rules=None):
    """(ok, reason, segments) - a CURVED road as one decision.

    ROADS_AS_MECHANIC section 5's shape, built: a Catmull-Rom through the
    committed nodes, sampled at the 410 quantum into straight segments, each
    of which is an ordinary road afterwards. The player draws one gesture and
    gets one road; the segments are how it is stored and drawn, not what it
    is.

    ONE ROAD, SO ONE DECISION. Every segment is checked against the board -
    the plate, existing roads, placed lots, pinned lots - and ANY failure
    refuses the WHOLE path, naming the segment. A path that half-built where
    it first hit something would leave the player with a road they did not
    draw and a bill for it. The length and the price are the path's, not each
    chord's: a 410 uu chord is under the 820 a lot needs, and refusing every
    curve for that would be measuring the wrong thing.

    IT DOES NOT CROSS ITSELF BY DEFINITION. Consecutive chords share an
    endpoint, so their corridors always overlap; segments a few apart on a
    bend overlap too, because the corridor is 2260 wide and the chords are
    410 long. Checking a path against its own segments would refuse every
    curve ever drawn. So the crossing check runs against the board only, and
    the segments carry a shared 'path' so that everything downstream -
    _in_crossing above, and the next road's own crossing check - treats them
    as the one road they are.

    WHAT THAT LEAVES OPEN, named rather than hidden: a path that loops back
    over itself is accepted, because this version cannot tell that apart from
    a tight bend. Section 5 says "a single open-ended road" and defers
    intersections; a self-crossing curve is the same question and waits with
    them."""
    r = _rules(rules)
    if width_class not in ROAD_TYPES:
        return False, (
            'unknown road type %r: expected one of %s'
            % (width_class, ', '.join(ROAD_TYPES))), None
    if len(nodes) < 2:
        return False, 'a road needs at least two nodes', None

    pts = sample_path(nodes)
    if len(pts) < 2:
        return False, (
            'too short: the nodes are inside one %.0f uu grid step of each '
            'other' % POSITION_QUANTUM), None

    length = sum(((pts[i + 1][0] - pts[i][0]) ** 2
                  + (pts[i + 1][1] - pts[i][1]) ** 2) ** 0.5
                 for i in range(len(pts) - 1))
    if length < MIN_ROAD_LENGTH:
        return False, (
            'too short: %.0f uu is under the %.0f uu a single lot needs'
            % (length, MIN_ROAD_LENGTH)), None

    for px, py in pts:
        if not (PLATE_X_MIN <= px <= PLATE_X_MAX and
                PLATE_Y_MIN <= py <= PLATE_Y_MAX):
            return False, (
                'off-board: the curve leaves the plate at [%.0f, %.0f]'
                % (px, py)), None

    path_id = _next_path_id(state)
    segments = []
    n = 1
    taken = set(state.get('roads', {}).keys())
    for i in range(len(pts) - 1):
        while 'R%d' % n in taken:
            n += 1
        segments.append({'id': 'R%d' % n, 'start': pts[i], 'end': pts[i + 1],
                         'width_class': width_class, 'path': path_id})
        taken.add('R%d' % n)

    roads = _all_roads(state)
    for k, seg in enumerate(segments):
        mine = road_quad(_road_dict(seg), r)
        for road in roads:
            if quads_overlap(mine, road_quad(road, r)):
                return False, (
                    'crosses: the curve would cross the %s road at its %d%s '
                    'chord' % (road['id'], k + 1, _ordinal(k + 1))), None
        for p in state['parcels'].values():
            lot = p.get('placement')
            if not lot:
                continue
            if quads_overlap(mine, lot_quad(lot, roads, r)):
                return False, (
                    'overlap: the curve would cross an existing lot at '
                    '[%.1f, %.1f] on the %s'
                    % (lot['x0'], lot['x1'], lot_road_id(lot))), None
        if pins_active:
            for pin_x0, pin_x1, pin_side in PINNED_SPANS:
                pin_lot = {'x0': pin_x0, 'x1': pin_x1, 'side': pin_side,
                           'road_id': 'arterial'}
                if quads_overlap(mine, lot_quad(pin_lot, roads, r)):
                    return False, (
                        'overlap: the curve would cross a pinned lot at '
                        '[%.1f, %.1f]' % (pin_x0, pin_x1)), None

    # ONE PRICE, for the whole gesture, charged from the polyline's own length
    # rather than summed per chord - the same number either way, said once.
    cost = r['road_cost_per_100uu_%s' % width_class] * length / 100.0
    if state['money'] < cost:
        return False, (
            "can't afford: a %.0f uu %s costs %.2f, money is %.2f"
            % (length, width_class, cost, state['money'])), None
    return True, '', segments


def _ordinal(n):
    if 10 <= n % 100 <= 20:
        return 'th'
    return {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')


def draw_road_path(state, nodes, width_class='avenue', pins_active=True,
                    rules=None):
    """One curve-drawing gesture. (state, path_id, ids, ok, reason) - path_id
    and ids are None on refusal, mirroring draw_road's own shape.

    The segments go in EXACTLY as resolve_road_path validated them, and the
    money moves here and only here, once, for the whole path - the same
    discipline draw_road holds for a straight road."""
    r = _rules(rules)
    ok, reason, segments = resolve_road_path(state, nodes, width_class,
                                              pins_active=pins_active, rules=r)
    if not ok:
        return state, None, None, False, reason
    length = sum(road_length(seg) for seg in segments)
    state['money'] -= (r['road_cost_per_100uu_%s' % width_class] * length
                       / 100.0)
    roads = state.setdefault('roads', {})
    for seg in segments:
        roads[seg['id']] = seg
    return (state, road_path_id(segments[0]),
            [seg['id'] for seg in segments], True, '')


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
    #     FUNDED 2026-09-06, road types: roads cost money now, and a
    #     1400 uu avenue at $10/100 uu is $140 against the $100 a fresh
    #     city starts with. These tests are about GEOMETRY, so they are
    #     given a balance that cannot be the reason they refuse; the
    #     price itself is tested on its own in 44 below, on a state left
    #     at money_start deliberately.
    s31['money'] = 1000.0
    ok31, reason31, road31 = resolve_road_draw(s31, 6200.0, 3000.0, 7600.0, 3000.0)
    assert ok31 and reason31 == '', (ok31, reason31)
    assert road31 == {'id': 'R1', 'start': (6200.0, 3000.0),
                       'end': (7600.0, 3000.0), 'width_class': 'avenue'}, road31

    # 32. DIAGONAL, and no longer refused (2026-09-06, item 11). dx=1000,
    #     dy=800 reaches neither 3x, so before curves this was the
    #     'too diagonal' refusal; the version limit it named is gone. The
    #     OLD coordinates still refuse - they start on the cross street's
    #     own centreline - but for the REASON THEY SHOULD, which is the
    #     assertion that proves the gate opened rather than moved.
    ok32, reason32, road32 = resolve_road_draw(s31, 0.0, 3000.0, 1000.0, 3800.0)
    assert not ok32 and road32 is None, (ok32, reason32)
    assert 'too diagonal' not in reason32, reason32
    assert 'crosses' in reason32 and 'cross' in reason32, reason32
    #     A 45 degree road on clear ground draws, unsnapped, exactly as the
    #     player drew it - neither endpoint pulled onto an axis.
    ok32b, reason32b, road32b = resolve_road_draw(s31, 6200.0, 2500.0, 7200.0, 3500.0)
    assert ok32b and reason32b == '', (ok32b, reason32b)
    assert road32b == {'id': 'R1', 'start': (6200.0, 2500.0),
                        'end': (7200.0, 3500.0), 'width_class': 'avenue'}, road32b

    # 33. TOO SHORT: a valid horizontal orientation, but only 500 uu -
    #     under MIN_ROAD_LENGTH (820, one lot's own narrowest width).
    ok33, reason33, road33 = resolve_road_draw(s31, 6200.0, 3000.0, 6700.0, 3000.0)
    assert not ok33 and road33 is None and 'too short' in reason33, (
        ok33, reason33)
    #     A DIAGONAL IS MEASURED ALONG ITS CENTRELINE (2026-09-06, item 11),
    #     which only shows up here: 500 by 500 is 707 uu long and under the
    #     820 a lot needs, while the sum of the two deltas is 1000 and would
    #     let it through. The two ways of measuring agree on every
    #     axis-aligned road, so nothing before this could tell them apart.
    ok33b, reason33b, road33b = resolve_road_draw(s31, 6200.0, 3000.0, 6700.0, 3500.0)
    assert not ok33b and road33b is None and 'too short' in reason33b, (
        ok33b, reason33b)
    assert '707 uu' in reason33b, reason33b

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
    s38['money'] = 1000.0   # see 31 - geometry test, not a price test
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
    s39['money'] = 1000.0   # see 31 - geometry test, not a price test
    s39, _, _, _ = draw_road(s39, 6200.0, 3000.0, 7600.0, 3000.0)
    s39, pid39, ok39, reason39 = place(s39, 6900.0, 1700.0)
    assert ok39 and pid39 == 'P1' and reason39 == '', (pid39, ok39, reason39)
    assert s39['parcels']['P1']['placement'] == {
        'x0': 6490.0, 'x1': 7310.0, 'side': 'south', 'road_id': 'R1'
    }, s39['parcels']['P1']['placement']
    assert lot_rect(s39['parcels']['P1']['placement'], _all_roads(s39)) == (
        6490.0, 7310.0, 370.0, 1870.0)


    # ---- ROAD TYPES AS MECHANICS, 2026-09-06 (40-47) -------------------
    # MONDAY_DECISIONS section 2's four types, its PROPOSED table adopted
    # as tonight's working defaults in econrules.json. Every number below
    # is hand-computed from that table and the ONE recovered constant
    # (VERGE = 430), never read back out of the same rules dict the code
    # reads - a test that asks the code for its own answer proves nothing.
    R = econrules.rules()

    # 40. road_half per type, and the reduction that makes this change
    #     safe: an avenue - and a road with no 'width_class' at all, which
    #     is what both built-ins are - is EXACTLY the old ROAD_HALF
    #     constant, so every one of tests 1-39 above measures the same
    #     board it always did. dirt 900/2+430=880, avenue 1400/2+430=1130,
    #     boulevard 1700/2+430=1280, highway 2000/2+430=1430.
    #     THE BOULEVARD'S MEDIAN IS 300 uu (coordinator, 2026-09-06 21:52,
    #     deciding the question this table left open: MONDAY_DECISIONS
    #     section 2 says "1400 + median" and never says how wide). So its
    #     carriageway is 1700 and it is the one type whose corridor differs
    #     from the avenue's - it is a shape now, not only a price.
    assert road_type(ARTERIAL) == 'avenue' and road_type(CROSS_STREET) == 'avenue'
    assert road_half(ARTERIAL, R) == ROAD_HALF == 1130.0
    _halves = {'dirt': 880.0, 'avenue': 1130.0, 'boulevard': 1280.0,
               'highway': 1430.0}
    for _t, _h in _halves.items():
        assert road_half({'width_class': _t}, R) == _h, (_t, _h)
    assert road_max_reach(ARTERIAL, R) == ROAD_MAX_REACH == 3230.0
    assert road_max_reach({'width_class': 'highway'}, R) == 3530.0
    try:
        road_type({'width_class': 'motorway'})
        raise AssertionError('unknown road type must raise, not fall back')
    except ValueError as e:
        assert 'motorway' in str(e), str(e)

    # 41. Price and material name, both derived from type and geometry,
    #     neither stored. A 1400 uu road at the table's own per-100-uu
    #     prices: dirt 5*14=70, avenue 10*14=140, boulevard 20*14=280,
    #     highway 30*14=420. Length is the centreline's, so a vertical
    #     road prices identically to a horizontal one of the same span.
    _seg = lambda t, n: {'id': 'X', 'start': (0.0, 0.0), 'end': (n, 0.0),
                         'width_class': t}
    assert road_length(_seg('avenue', 1400.0)) == 1400.0
    assert road_length({'id': 'X', 'start': (0.0, 100.0),
                        'end': (0.0, 1500.0), 'width_class': 'avenue'}) == 1400.0
    for _t, _c in (('dirt', 70.0), ('avenue', 140.0), ('boulevard', 280.0),
                   ('highway', 420.0)):
        assert abs(road_cost(_seg(_t, 1400.0), R) - _c) < 1e-9, (_t, _c)
        assert road_material_name(_seg(_t, 1400.0)) == 'MI_road_%s' % _t
    assert abs(road_cost(_seg('dirt', 700.0), R) - 35.0) < 1e-9

    # 42. THE HIGHWAY REFUSES FRONTAGE - the one mechanic section 2 states
    #     as a rule rather than a number. The SAME segment, x=7500 running
    #     y 1500..4230, drawn twice: as a highway, a click 2300 uu to its
    #     west is refused with a reason a player can act on ('no frontage'
    #     naming the type), NOT the true-but-useless 'off-board' the
    #     generic path would give; as an avenue, the identical click
    #     places a lot on its west side. Both built-ins are out of reach
    #     from there (arterial 3800 > 3230, cross street 5200 > 3230), so
    #     the drawn road is the only thing that can answer, which is what
    #     makes the pair a clean A/B.
    assert road_has_frontage({'width_class': 'highway'}, R) is False
    for _t in ('dirt', 'avenue', 'boulevard'):
        assert road_has_frontage({'width_class': _t}, R) is True, _t
    s42 = citytick.seed_state()
    s42['money'] = 2000.0
    s42, hid42, ok42, reason42 = draw_road(s42, 7500.0, 1500.0, 7500.0, 4230.0,
                                            'highway')
    assert ok42 and hid42 == 'R1', (hid42, ok42, reason42)
    ok42b, reason42b, lot42b = resolve_click(s42, 5200.0, 3800.0)
    assert not ok42b and lot42b is None, (ok42b, lot42b)
    assert 'no frontage' in reason42b and 'highway' in reason42b, reason42b
    #     And 'no frontage' is bounded by the highway's OWN reach, not
    #     handed out board-wide: (-7000, -4000) is outside every road's
    #     reach including this one's, and gets the plain 'off-board'.
    ok42e, reason42e, _ = resolve_click(s42, -7000.0, -4000.0)
    assert not ok42e and 'off-board' in reason42e, reason42e
    assert 'no frontage' not in reason42e, reason42e
    s42c = citytick.seed_state()
    s42c['money'] = 2000.0
    s42c, _, ok42c, _ = draw_road(s42c, 7500.0, 1500.0, 7500.0, 4230.0, 'avenue')
    assert ok42c
    ok42d, reason42d, lot42d = resolve_click(s42c, 5200.0, 3800.0)
    assert ok42d and reason42d == '', (ok42d, reason42d)
    assert lot42d == {'x0': 3390.0, 'x1': 4210.0, 'side': 'west',
                       'road_id': 'R1'}, lot42d

    # 43. AND NOTHING MAY BE LAID ACROSS ONE. Refusing frontage is not
    #     enough on its own: a lot fronting some OTHER road can still run
    #     straight through a highway's corridor, and every other refusal
    #     in resolve_click is reached through the road a lot faces, so a
    #     road nothing faces is unguarded by construction. A vertical
    #     highway at x=7500 (corridor 6070..8930) against an arterial
    #     north lot at x=7000 (span 6590..7410, y 1130..2630): the two
    #     rectangles genuinely intersect. The SAME click on a board with
    #     no highway places normally, which is what proves the refusal is
    #     the highway's doing and not the coordinates'.
    s43 = citytick.seed_state()
    s43['money'] = 2000.0
    s43, _, ok43, reason43 = draw_road(s43, 7500.0, 1500.0, 7500.0, 4230.0,
                                        'highway')
    assert ok43, reason43
    ok43b, reason43b, lot43b = resolve_click(s43, 7000.0, 1500.0)
    assert not ok43b and lot43b is None, (ok43b, lot43b)
    assert 'across the R1' in reason43b and 'highway' in reason43b, reason43b
    s43c = citytick.seed_state()
    ok43c, reason43c, lot43c = resolve_click(s43c, 7000.0, 1500.0)
    assert ok43c and lot43c == {'x0': 6590.0, 'x1': 7410.0, 'side': 'north',
                                 'road_id': 'arterial'}, (reason43c, lot43c)

    # 44. ROADS COST MONEY, on a state left at money_start (100) on
    #     purpose - the funding note at test 31 explains why the geometry
    #     tests are not. The 1400 uu east-margin road from test 31: as an
    #     avenue it is $140 and refuses; as a dirt track it is $70 and
    #     draws, leaving exactly $30. The refusal spends nothing, which is
    #     the property that lets the ghost preview call the same function
    #     every frame.
    s44 = citytick.seed_state()
    assert s44['money'] == 100.0, s44['money']
    ok44, reason44, road44 = resolve_road_draw(s44, 6200.0, 3000.0, 7600.0,
                                                3000.0, 'avenue')
    assert not ok44 and road44 is None, (ok44, road44)
    assert "can't afford" in reason44 and '140.00' in reason44, reason44
    s44, rid44, ok44b, reason44b = draw_road(s44, 6200.0, 3000.0, 7600.0,
                                              3000.0, 'avenue')
    assert not ok44b and rid44 is None and s44['money'] == 100.0, s44['money']
    s44, rid44c, ok44c, reason44c = draw_road(s44, 6200.0, 3000.0, 7600.0,
                                               3000.0, 'dirt')
    assert ok44c and rid44c == 'R1', (rid44c, ok44c, reason44c)
    assert abs(s44['money'] - 30.0) < 1e-9, s44['money']
    assert s44['roads']['R1']['width_class'] == 'dirt'

    # 45. A NARROWER ROAD PULLS ITS OWN FRONTAGE LINE IN. The dirt road
    #     just drawn has corridor half 880, so its footprint is
    #     y 2120..3880 (not 1870..4130) and a lot on its south side sits
    #     at y 620..2120 (not 370..1870). Same click, same road geometry,
    #     different type - the whole point of the type being a mechanic.
    assert road_rect(s44['roads']['R1'], R) == (6200.0, 7600.0, 2120.0, 3880.0)
    s45 = citytick.seed_state()
    s45['money'] = 2000.0
    s45, _, ok45, reason45 = draw_road(s45, 6200.0, 3000.0, 7600.0, 3000.0,
                                        'dirt')
    assert ok45, reason45
    s45, pid45, ok45b, reason45b = place(s45, 6900.0, 2000.0)
    assert ok45b and pid45 == 'P1', (pid45, ok45b, reason45b)
    assert lot_rect(s45['parcels']['P1']['placement'], _all_roads(s45), R) == (
        6490.0, 7310.0, 620.0, 2120.0)

    # 46. THE RENT MULTIPLIER, the part that makes a type a planning
    #     decision. Own-road type first (dirt 0.75, avenue 1.0, boulevard
    #     1.25), then the highway's proximity bonus, which is a SEPARATE
    #     mechanism and MULTIPLIES - see road_rent_multiplier's own
    #     docstring for the flag raised on that reading. Synthetic states
    #     here rather than drawn ones: this function is pure over (state,
    #     lot), and building the exact adjacency by hand is the only way
    #     to test the 2,000 uu edge from both sides.
    _lot46 = {'x0': 6490.0, 'x1': 7310.0, 'side': 'south', 'road_id': 'D'}
    def _s46(dirt_type, extra=None):
        roads = {'D': {'id': 'D', 'start': (6200.0, 3000.0),
                        'end': (7600.0, 3000.0), 'width_class': dirt_type}}
        if extra:
            roads['HW'] = extra
        return {'money': 0.0, 'parcels': {}, 'roads': roads}
    for _t, _m in (('dirt', 0.75), ('avenue', 1.0), ('boulevard', 1.25)):
        assert abs(road_rent_multiplier(_s46(_t), _lot46, R) - _m) < 1e-9, _t
    #     The dirt lot's own footprint is (6490, 7310, 620, 2120). A
    #     highway running y 1500..4230 at x=7500 has corridor
    #     (6070, 8930, 1500, 4230) - the two rectangles touch, distance 0,
    #     well inside the 2,000 reach: 0.75 * 1.1 = 0.825.
    _near = {'id': 'HW', 'start': (7500.0, 1500.0), 'end': (7500.0, 4230.0),
             'width_class': 'highway'}
    assert abs(road_rent_multiplier(_s46('dirt', _near), _lot46, R)
               - 0.825) < 1e-9
    #     The SAME highway moved south of the lot, corridor top edge at
    #     y=-1500, is 620-(-1500) = 2120 uu away - 120 uu outside reach,
    #     and the bonus is gone. A near miss on purpose: an off-by-a-lot
    #     reach would pass a test written at 10,000 uu.
    _far = {'id': 'HW', 'start': (7500.0, -4230.0), 'end': (7500.0, -1500.0),
            'width_class': 'highway'}
    assert abs(road_rent_multiplier(_s46('dirt', _far), _lot46, R) - 0.75) < 1e-9
    assert abs(_rect_distance((6490.0, 7310.0, 620.0, 2120.0),
                              road_rect(_far, R)) - 2120.0) < 1e-9

    # 47. An unrecognised type is REFUSED at the boundary with a reason,
    #     not raised through it - a bad string arriving from a UI is a
    #     refusal a player can read, while road_type's own raise stays for
    #     a caller inside this module getting it wrong. Nothing is spent
    #     and no road is created either way.
    s47 = citytick.seed_state()
    s47['money'] = 2000.0
    ok47, reason47, road47 = resolve_road_draw(s47, 6200.0, 3000.0, 7600.0,
                                                3000.0, 'motorway')
    assert not ok47 and road47 is None, (ok47, road47)
    assert 'unknown road type' in reason47 and 'motorway' in reason47, reason47
    s47, rid47, ok47b, _ = draw_road(s47, 6200.0, 3000.0, 7600.0, 3000.0,
                                      'motorway')
    assert not ok47b and rid47 is None and s47['money'] == 2000.0
    assert s47.get('roads') == {}, s47.get('roads')

    # 48. _in_crossing measures each road's OWN pavement. A point 1,300
    #     uu from a highway's centreline is standing ON it (half 1,430)
    #     and would not be on an avenue (half 1,130) - so whether that
    #     point is "pavement shared by more than one road" depends on the
    #     type, and nothing else in tests 40-47 reaches this line.
    #
    #     A DIRECT UNIT TEST, on a road list built by hand, and the
    #     honest reason why: resolve_road_draw refuses any candidate
    #     whose corridor overlaps an existing one, so no state reachable
    #     through draw_road can have two corridors sharing ground at all
    #     - the only crossing that exists is ARTERIAL x CROSS_STREET,
    #     both avenues, where the constant and the per-type half agree.
    #     The per-type half is still what belongs here: the built-ins are
    #     never validated against that rule, and a wider road drawn
    #     against a rule that ever softens (an underpass, a bridge) would
    #     otherwise offer frontage on pavement a player is standing in.
    #     Called with an explicit list rather than a state, which is
    #     exactly what makes it testable while it is unreachable.
    _hw48 = _road_dict({'id': 'HW', 'start': (7500.0, -4230.0),
                         'end': (7500.0, 4230.0), 'width_class': 'highway'})
    _av48 = dict(_hw48, width_class='avenue')
    #     (6200, 500): 500 from the arterial's centreline (inside its
    #     1,130) and 1,300 from the vertical road's (inside a highway's
    #     1,430, outside an avenue's 1,130).
    assert _in_crossing([ARTERIAL, _hw48], 6200.0, 500.0, R) is True
    assert _in_crossing([ARTERIAL, _av48], 6200.0, 500.0, R) is False
    assert _in_crossing([ARTERIAL, CROSS_STREET], 0.0, 0.0, R) is True

    # 49. WHICH WAY THE PLAYER DRAGGED MUST NOT MATTER - a bug fix, found
    #     while generalizing resolve_road_draw to arbitrary directions and
    #     reachable today by dragging right to left. resolve_click recovers a
    #     lot's world position as road['start'][axis] + along, and `along` runs
    #     along the SEGMENT'S OWN direction, so an east-to-west road put every
    #     lot at 2 * start_x - x - a mirror image about the start point - and
    #     flipped its side name with it (the normal is the direction rotated
    #     +90 degrees). Silent whenever the mirrored span still landed on the
    #     road; test 31's own road, drawn the other way, put a south click's lot
    #     at [7890, 8710] instead of [6490, 7310].
    #
    #     Both axes, and both the SEGMENT and the LOT, because the two failed
    #     differently: the stored segment was already fine (road_rect takes
    #     min/max), and the lot was not.
    for _c0, _c1, _click, _want in (
            ((6200.0, 3000.0), (7600.0, 3000.0), (6900.0, 1700.0),
             {'x0': 6490.0, 'x1': 7310.0, 'side': 'south', 'road_id': 'R1'}),
            ((7300.0, -4230.0), (7300.0, -3000.0), (5500.0, -3600.0),
             {'x0': -4010.0, 'x1': -3190.0, 'side': 'west', 'road_id': 'R1'})):
        _seen = []
        for _a, _b in ((_c0, _c1), (_c1, _c0)):
            _s = citytick.seed_state()
            _s['money'] = 2000.0
            _s, _rid, _ok, _why = draw_road(_s, _a[0], _a[1], _b[0], _b[1])
            assert _ok, (_a, _b, _why)
            _s, _pid, _ok2, _why2 = place(_s, _click[0], _click[1])
            assert _ok2, (_a, _b, _why2)
            _seen.append((_s['roads'][_rid]['start'], _s['roads'][_rid]['end'],
                          _s['parcels'][_pid]['placement'], _s['money']))
        assert _seen[0] == _seen[1], _seen
        assert _seen[0][2] == _want, _seen[0][2]

    # ---- ROADS AT ANY DIRECTION, 2026-09-06 (50-53) --------------------
    # Item 11's first half. The resolver, the lot frame and the overlap scans
    # generalize off the road's own unit direction; the axis-aligned cases
    # above are the same numbers they always were, which is the check that
    # matters and is asserted rather than argued.

    # 50. quads_overlap REDUCES EXACTLY TO rects_overlap while everything is
    #     axis-aligned. Not an argument about separating axes - the two
    #     functions are run against each other on real lot geometry: an
    #     overlapping pair, a pair that only TOUCHES (which must be a miss,
    #     because a lot sits exactly on its own road's frontage line), one
    #     clear, and the corner case where an arterial lot and a cross-street
    #     lot share ground while their spans never compare.
    _r50 = _all_roads(citytick.seed_state())
    _lots50 = (
        ({'x0': 100.0, 'x1': 900.0, 'side': 'north', 'road_id': 'arterial'},
         {'x0': 500.0, 'x1': 1300.0, 'side': 'north', 'road_id': 'arterial'}),
        ({'x0': 100.0, 'x1': 900.0, 'side': 'north', 'road_id': 'arterial'},
         {'x0': 900.0, 'x1': 1700.0, 'side': 'north', 'road_id': 'arterial'}),
        ({'x0': 100.0, 'x1': 900.0, 'side': 'north', 'road_id': 'arterial'},
         {'x0': 100.0, 'x1': 900.0, 'side': 'south', 'road_id': 'arterial'}),
        ({'x0': 1640.0, 'x1': 2460.0, 'side': 'north', 'road_id': 'arterial'},
         {'x0': 1130.0, 'x1': 2630.0, 'side': 'west', 'road_id': 'cross'}),
    )
    for _a, _b in _lots50:
        _qa, _qb = lot_quad(_a, _r50), lot_quad(_b, _r50)
        assert quads_overlap(_qa, _qb) == rects_overlap(
            lot_rect(_a, _r50), lot_rect(_b, _r50)), (_a, _b)
    #     and the touching pair really is a miss, not both-true by accident
    assert not quads_overlap(lot_quad(_lots50[1][0], _r50),
                             lot_quad(_lots50[1][1], _r50))
    assert quads_overlap(lot_quad(_lots50[0][0], _r50),
                         lot_quad(_lots50[0][1], _r50))

    # 51. THE PROJECTION IDENTITY, the generalization of test 13's own. A
    #     lot's x0/x1 are the scalar projection of its span onto the road's
    #     unit direction; for the two built-ins that IS the world coordinate
    #     they have always been, so no lot already saved changes meaning.
    #     s0 + along == the world coordinate, exactly, for both.
    for _road, _pts in ((ARTERIAL, (-7000.0, -410.0, 0.0, 2350.0, 7000.0)),
                        (CROSS_STREET, (-4000.0, -410.0, 0.0, 1500.0, 4000.0))):
        _f = road_frame(_road)
        _idx = 0 if _road['axis'] == 'x' else 1
        for _w in _pts:
            _p = (_w, 3000.0) if _idx == 0 else (3000.0, _w)
            _along, _across, _len = _project_to_road(_road, _p[0], _p[1])
            assert abs((_f[7] + _along) - _w) < 1e-9, (_road['id'], _w,
                                                       _f[7] + _along)
        # and the road's own span in projection space is its plate bounds
        assert abs(_f[7] - min(_road['start'][_idx], _road['end'][_idx])) < 1e-9
        assert abs((_f[7] + _f[6]) - max(_road['start'][_idx],
                                          _road['end'][_idx])) < 1e-9

    # 52. A LOT ON A 45 DEGREE ROAD, end to end through place(). The road is
    #     stored exactly as drawn (no endpoint pulled onto an axis), the lot
    #     resolves and snaps in PROJECTION space, and its pad is a rotated
    #     quad whose corners are the road frame's - which is the whole point:
    #     before this, resolve_click recovered a world position as
    #     start[axis] + along and could not have produced these at all.
    #     Both sides of the same span are placeable (they share no ground);
    #     the SAME span twice on the SAME side is refused.
    s52 = citytick.seed_state()
    s52['money'] = 5000.0
    s52, rid52, ok52, why52 = draw_road(s52, 6200.0, 2500.0, 7200.0, 3500.0)
    assert ok52 and rid52 == 'R1', (rid52, ok52, why52)
    assert s52['roads']['R1'] == {'id': 'R1', 'start': (6200.0, 2500.0),
                                   'end': (7200.0, 3500.0),
                                   'width_class': 'avenue'}, s52['roads']['R1']
    #     AND IT IS PRICED BY ITS TRUE LENGTH. sqrt(1000^2 + 1000^2) = 1414.21,
    #     so an avenue costs 141.42 - not the 200 a manhattan length would
    #     charge. The two only differ on a diagonal, which is why no case
    #     before this one could tell them apart.
    assert abs(s52['money'] - (5000.0 - 141.4213562373095)) < 1e-9, s52['money']
    s52, pid52, ok52b, why52b = place(s52, 5639.4, 4060.6)
    assert ok52b and pid52 == 'P1', (pid52, ok52b, why52b)
    assert s52['parcels']['P1']['placement'] == {
        'x0': 6450.0, 'x1': 7270.0, 'side': 'north', 'road_id': 'R1'
    }, s52['parcels']['P1']['placement']
    _q52 = lot_quad(s52['parcels']['P1']['placement'], _all_roads(s52))
    _want52 = ((5611.81, 3509.87), (6191.64, 4089.70),
               (5130.98, 5150.36), (4551.15, 4570.53))
    for _got, _exp in zip(_q52, _want52):
        assert abs(_got[0] - _exp[0]) < 0.01 and abs(_got[1] - _exp[1]) < 0.01, \
            (_got, _exp)
    s52b, pid52b, ok52c, why52c = place(s52, 7760.6, 1939.4)
    assert ok52c and s52b['parcels'][pid52b]['placement'] == {
        'x0': 6450.0, 'x1': 7270.0, 'side': 'south', 'road_id': 'R1'
    }, (ok52c, why52c)
    _, _, ok52d, why52d = place(s52, 5639.4, 4060.6)
    assert not ok52d and 'overlap' in why52d, (ok52d, why52d)

    # 53. THE SIDE NAMES COME OFF THE NORMAL, not off the dominant axis of
    #     the road's run - the one case where the two disagree, and the
    #     reason _road_dict is written the way it is. (6800, 4230) ->
    #     (7650, 2530) runs down and to the right at a 2:1 slope: its
    #     direction is Y-dominant, so a dominant-axis rule would call the
    #     plus side 'west', but the normal points EAST (+0.894, +0.447) and
    #     east is where those lots actually are. A road at 2:1 also stays
    #     inside the 3x snap threshold, so it is not quietly straightened.
    s53 = citytick.seed_state()
    s53['money'] = 5000.0
    s53, rid53, ok53, why53 = draw_road(s53, 6800.0, 4230.0, 7650.0, 2530.0)
    assert ok53, why53
    _d53 = _road_dict(s53['roads'][rid53])
    assert _d53['side_plus'] == 'east' and _d53['side_minus'] == 'west', _d53
    _f53 = road_frame(_d53)
    assert abs(_f53[4] - 0.8944) < 1e-3 and abs(_f53[5] - 0.4472) < 1e-3, _f53
    #     THE OTHER SIGN, tested directly on a hand-built segment because
    #     resolve_road_draw's endpoint ordering makes it unreachable through
    #     the draw path: a canonical segment always has ux >= 0, so the
    #     normal's y component (which IS ux) is never negative and the
    #     'south'-plus branch cannot be reached from a player's drag. It is
    #     still the correct answer for a segment handed in the other way
    #     round - the built-ins are never canonicalized either - so it is
    #     written, and tested here rather than left as a claim.
    _rev53 = _road_dict({'id': 'X', 'start': (7200.0, 3500.0),
                          'end': (6200.0, 2500.0), 'width_class': 'avenue'})
    assert _rev53['side_plus'] == 'south' and _rev53['side_minus'] == 'north', _rev53
    _revv53 = _road_dict({'id': 'X', 'start': (3000.0, 4230.0),
                           'end': (3000.0, 2000.0), 'width_class': 'avenue'})
    assert _revv53['side_plus'] == 'east' and _revv53['side_minus'] == 'west', _revv53

    #     and the two built-ins still get exactly the names they always had
    assert _road_dict(ARTERIAL)['side_plus'] == 'north'
    assert _road_dict(ARTERIAL)['side_minus'] == 'south'
    assert _road_dict(CROSS_STREET)['side_plus'] == 'west'
    assert _road_dict(CROSS_STREET)['side_minus'] == 'east'

    # 54. TWO HOUSES ALONG A DIAGONAL STREET - the case that makes the
    #     overlap scan's choice of QUAD rather than bounding box a player
    #     -facing fact rather than a nicety. A 45 degree lot's pad is an
    #     820 x 1500 rectangle turned 45 degrees; its bounding box is about
    #     1640 square, and the empty corners are most of it. Two lots along
    #     the same street, spans well apart, have boxes that overlap and
    #     pads that do not - so a bounding-box scan refuses the second
    #     click on visibly empty ground.
    #
    #     Empty mode, because the pinned frontage is wall to wall from
    #     |x| 1130 to 6050 and a diagonal long enough for two lots cannot
    #     avoid it on this board. That is the same mode gate the click path
    #     already has, not a special case invented for this test.
    s54 = citytick.seed_state()
    s54['money'] = 9000.0
    s54, rid54, ok54, why54 = draw_road(s54, 5700.0, 2000.0, 7650.0, 3950.0,
                                         pins_active=False)
    assert ok54, why54
    _f54 = road_frame(_road_dict(s54['roads'][rid54]))
    _pids54 = []
    for _t in (0.20, 0.80):
        _al = _f54[6] * _t
        _px = _f54[0] + _f54[2] * _al + _f54[4] * 1500.0
        _py = _f54[1] + _f54[3] * _al + _f54[5] * 1500.0
        s54, _pid, _ok, _why = place(s54, _px, _py, pins_active=False)
        assert _ok, (_t, _why)
        _pids54.append(_pid)
    assert _pids54 == ['P1', 'P2'], _pids54
    assert s54['parcels']['P1']['placement'] == {
        'x0': 5590.0, 'x1': 6410.0, 'side': 'north', 'road_id': 'R1'
    }, s54['parcels']['P1']['placement']
    assert s54['parcels']['P2']['placement'] == {
        'x0': 7240.0, 'x1': 8060.0, 'side': 'north', 'road_id': 'R1'
    }, s54['parcels']['P2']['placement']
    #     and the DISCRIMINATION itself, stated rather than implied: the pads
    #     miss, the boxes do not.
    _qa54 = lot_quad(s54['parcels']['P1']['placement'], _all_roads(s54))
    _qb54 = lot_quad(s54['parcels']['P2']['placement'], _all_roads(s54))
    assert not quads_overlap(_qa54, _qb54)
    assert rects_overlap(quad_rect(_qa54), quad_rect(_qb54))

    # 55. THE OTHER THREE SCANS ALSO COMPARE PADS, not boxes. 54 proves it
    #     for the lot-vs-lot scan; there are three more call sites, and a
    #     diagonal's bounding box is so much bigger than the thing inside it
    #     that each one would refuse real ground if it compared boxes. All
    #     three are the SAME shape of case: something axis-aligned standing in
    #     one of a diagonal's empty box corners. Empty mode throughout, for
    #     the reason 54 gives.

    #     (a) A DRAWN ROAD vs an existing LOT. An arterial lot at
    #     [6590, 7410]; a 45 degree road from (4400, 3600) whose box reaches
    #     x 6699 - over the lot - while its corridor stays west of it.
    _a55 = citytick.seed_state()
    _a55['money'] = 40000.0
    _a55, _p55, _ok55, _why55 = place(_a55, 7000.0, 1500.0, pins_active=False)
    assert _ok55, _why55
    _lot55 = _a55['parcels'][_p55]['placement']
    _ok55, _why55, _road55 = resolve_road_draw(_a55, 4400.0, 3600.0, 5900.0,
                                                2100.0, pins_active=False)
    assert _ok55, _why55
    _q55 = road_quad(_road_dict(_road55))
    _ql55 = lot_quad(_lot55, _all_roads(_a55))
    assert not quads_overlap(_q55, _ql55)
    assert rects_overlap(quad_rect(_q55), quad_rect(_ql55))

    #     (b) A DRAWN ROAD vs another ROAD. The same diagonal, drawn; then a
    #     short vertical road at x=2500 standing in its box's west corner.
    _b55 = citytick.seed_state()
    _b55['money'] = 40000.0
    _b55, _rb55, _ok55, _why55 = draw_road(_b55, 4400.0, 3600.0, 5900.0, 2100.0,
                                            pins_active=False)
    assert _ok55, _why55
    _ok55, _why55, _road55b = resolve_road_draw(_b55, 2500.0, 1200.0, 2500.0,
                                                 2100.0, pins_active=False)
    assert _ok55, _why55
    _qa55 = road_quad(_road_dict(_b55['roads'][_rb55]))
    _qb55 = road_quad(_road_dict(_road55b))
    assert not quads_overlap(_qa55, _qb55)
    assert rects_overlap(quad_rect(_qa55), quad_rect(_qb55))

    #     (c) A LOT vs a HIGHWAY's corridor - the no-frontage scan, which is a
    #     refusal rather than a nicety. Test 54's diagonal street and its
    #     first lot, plus a vertical HIGHWAY at x=2600 whose corridor
    #     (1170..4030) clips the lot's box (which starts at 3943) and misses
    #     the pad entirely. The click must still place, with the highway
    #     standing there.
    _c55 = citytick.seed_state()
    _c55['money'] = 40000.0
    _c55, _rc55, _ok55, _why55 = draw_road(_c55, 5700.0, 2000.0, 7650.0, 3950.0,
                                            pins_active=False)
    assert _ok55, _why55
    _f55 = road_frame(_road_dict(_c55['roads'][_rc55]))
    _al55 = _f55[6] * 0.20
    _px55 = _f55[0] + _f55[2] * _al55 + _f55[4] * 1500.0
    _py55 = _f55[1] + _f55[3] * _al55 + _f55[5] * 1500.0
    _ok55, _why55, _lotc55 = resolve_click(_c55, _px55, _py55, pins_active=False)
    assert _ok55 and _lotc55 == {'x0': 5590.0, 'x1': 6410.0, 'side': 'north',
                                  'road_id': 'R1'}, (_ok55, _why55, _lotc55)
    _c55, _rh55, _ok55, _why55 = draw_road(_c55, 2600.0, 1800.0, 2600.0, 3000.0,
                                            'highway', pins_active=False)
    assert _ok55, _why55
    _qh55 = road_quad(_road_dict(_c55['roads'][_rh55]))
    _qlc55 = lot_quad(_lotc55, _all_roads(_c55))
    assert not quads_overlap(_qlc55, _qh55)
    assert rects_overlap(quad_rect(_qlc55), quad_rect(_qh55))
    _ok55, _why55, _again55 = resolve_click(_c55, _px55, _py55, pins_active=False)
    assert _ok55 and _again55 == _lotc55, (_ok55, _why55, _again55)

    # ---- CURVED MULTI-NODE ROADS, 2026-09-06 (56-60) -------------------
    # ROADS_AS_MECHANIC section 5's shape: a Catmull-Rom through the committed
    # nodes, sampled at the 410 quantum into straight segments, each of which
    # is an ordinary road afterwards. The player draws one gesture and gets ONE
    # road; the segments are how it is stored and drawn, not what it is.
    _CURVE = [(2000.0, -4000.0), (4000.0, -2600.0), (6000.0, -4000.0)]

    # 56. THE SAMPLER. Vertices are one WIDTH_QUANTUM apart ALONG THE CURVE,
    #     not in parameter space - a Catmull-Rom's parameter runs faster round
    #     the outside of a bend, so even-t sampling gives long chords through
    #     corners, which is exactly where a chord's error against the curve is
    #     largest. The first and last nodes are always vertices: a road that
    #     stopped short of where the player clicked would be a different road.
    _pts56 = sample_path(_CURVE)
    assert _pts56[0] == (_snap(_CURVE[0][0]), _snap(_CURVE[0][1])), _pts56[0]
    assert _pts56[-1] == (_snap(_CURVE[-1][0]), _snap(_CURVE[-1][1])), _pts56[-1]
    assert len(_pts56) >= 10, len(_pts56)
    for _p in _pts56:
        assert _p == (_snap(_p[0]), _snap(_p[1])), _p
    _ch56 = [((_pts56[i + 1][0] - _pts56[i][0]) ** 2
              + (_pts56[i + 1][1] - _pts56[i][1]) ** 2) ** 0.5
             for i in range(len(_pts56) - 1)]
    #     Every chord is within a snap step of the quantum, EXCEPT the last,
    #     which carries whatever the spacing did not divide evenly and is
    #     merged rather than left as a stub - so it runs up to one and a half
    #     quanta. A 50 uu chord is a road segment with a 2260 uu corridor and
    #     no length: a bump on the board and a hole in the frontage.
    for _c in _ch56[:-1]:
        assert abs(_c - WIDTH_QUANTUM) <= 20.0, (_c, _ch56)
    assert WIDTH_QUANTUM / 2.0 <= _ch56[-1] <= WIDTH_QUANTUM * 1.5, _ch56[-1]
    #     THE CURVE LEAVES ITS FIRST NODE ALONG THE FIRST CHORD. The phantom
    #     control point before node 0 is 2*P0 - P1, which continues the line
    #     the first two nodes make; DUPLICATING the endpoint instead - the
    #     other common choice - makes the curve leave node 0 along the chord
    #     to the THIRD node, so the road starts off in a direction the player
    #     did not draw. Measured as the angle between the first sampled step
    #     and the first node-to-node direction. THE MARGIN IS NARROW ON
    #     PURPOSE and worth knowing: duplicating an endpoint leaves the
    #     TANGENT DIRECTION alone (the Catmull-Rom tangent at P1 is
    #     (P2 - P0)/2, so P0 = 2*P1 - P2 gives P2 - P1 and P0 = P1 gives half
    #     of it) and changes its MAGNITUDE, which changes the curve's shape
    #     and so where arc-length sampling puts the first vertex. Measured:
    #     0.9986 as written, 0.9944 with the endpoint duplicated, so the
    #     bound sits between them with about the same room either side.
    def _ang56(a, b):
        _n1 = (a[0] ** 2 + a[1] ** 2) ** 0.5
        _n2 = (b[0] ** 2 + b[1] ** 2) ** 0.5
        _d = (a[0] * b[0] + a[1] * b[1]) / (_n1 * _n2)
        return max(-1.0, min(1.0, _d))
    _step56 = (_pts56[1][0] - _pts56[0][0], _pts56[1][1] - _pts56[0][1])
    _chord56 = (_CURVE[1][0] - _CURVE[0][0], _CURVE[1][1] - _CURVE[0][1])
    assert _ang56(_step56, _chord56) > 0.997, _ang56(_step56, _chord56)
    #     and the same at the far end, where the phantom is 2*Pn - Pn-1
    _stepE56 = (_pts56[-1][0] - _pts56[-2][0], _pts56[-1][1] - _pts56[-2][1])
    _chordE56 = (_CURVE[-1][0] - _CURVE[-2][0], _CURVE[-1][1] - _CURVE[-2][1])
    assert _ang56(_stepE56, _chordE56) > 0.997, _ang56(_stepE56, _chordE56)

    #     Two nodes is a straight line through them, not a curve.
    _str56 = sample_path([(0.0, 0.0), (1000.0, 0.0)])
    assert _str56[0] == (0.0, 0.0) and _str56[-1] == (1000.0, 0.0), _str56
    assert all(_p[1] == 0.0 for _p in _str56), _str56

    # 57. ONE GESTURE, ONE ROAD, ONE PRICE. The segments share a 'path', so
    #     everything downstream treats them as the one road they are, and the
    #     money moves once for the whole polyline rather than per chord.
    s57 = citytick.seed_state()
    s57['money'] = 40000.0
    s57, path57, ids57, ok57, why57 = draw_road_path(s57, _CURVE,
                                                      pins_active=False)
    assert ok57, why57
    assert path57 == 'C1' and len(ids57) == len(_pts56) - 1, (path57, ids57)
    assert ids57 == ['R%d' % (i + 1) for i in range(len(ids57))], ids57
    assert {s57['roads'][_i]['path'] for _i in ids57} == {'C1'}
    assert {s57['roads'][_i]['width_class'] for _i in ids57} == {'avenue'}
    #     The chords are the sampled polyline, joined end to end, unchanged.
    for _k, _i in enumerate(ids57):
        assert s57['roads'][_i]['start'] == _pts56[_k], (_i, _k)
        assert s57['roads'][_i]['end'] == _pts56[_k + 1], (_i, _k)
    _len57 = sum(_ch56)
    assert abs(s57['money'] - (40000.0 - 10.0 * _len57 / 100.0)) < 1e-9, s57['money']

    # 58. AND IT IS ONE ROAD TO EVERYTHING DOWNSTREAM. Consecutive chords
    #     share an endpoint so their corridors always overlap, and chords a
    #     few apart overlap too on a bend - the corridor is 2260 wide and the
    #     chords are 410 long. Counting SEGMENTS in _in_crossing would make
    #     the whole of every curve "the crossing" and refuse every lot on it;
    #     counting PATHS is what makes a curve buildable at all.
    _mid58 = s57['roads'][ids57[len(ids57) // 2]]
    _f58 = road_frame(_road_dict(_mid58))
    _on58 = (_f58[0] + _f58[2] * _f58[6] * 0.5, _f58[1] + _f58[3] * _f58[6] * 0.5)
    assert not _in_crossing(_all_roads(s57), _on58[0], _on58[1]), _on58
    #     AT A JOINT is the case that separates counting paths from counting
    #     segments: the shared endpoint has `along` in range for BOTH chords
    #     (its end, and the next one's start), so segment-counting calls every
    #     joint of every curve "the crossing" - and there is one every 410 uu.
    #     The joints are SEARCHED rather than assumed: a shared endpoint is
    #     exactly on both chords' lines, but `along <= length` is a
    #     floating-point comparison against a length that came out of a square
    #     root, so at some joints the earlier chord misses its own end by a
    #     hair. Asserting a particular joint would be asserting the rounding.
    _roads58 = _all_roads(s57)

    def _chords_at(x, y):
        _n = 0
        for _rd in _roads58:
            _al, _ac, _ln = _project_to_road(_rd, x, y)
            if 0.0 <= _al <= _ln and abs(_ac) < road_half(_rd):
                _n += 1
        return _n
    _shared58 = [s57['roads'][_i]['end'] for _i in ids57[:-1]
                 if _chords_at(*s57['roads'][_i]['end']) > 1]
    assert _shared58, 'no joint sits in more than one chord - the case is gone'
    for _j in _shared58:
        assert not _in_crossing(_roads58, _j[0], _j[1]), _j
    #     and a lot really does front a chord of the curve
    _place58 = None
    for _k in range(len(ids57)):
        _f = road_frame(_road_dict(s57['roads'][ids57[_k]]))
        _m = (_f[0] + _f[2] * _f[6] * 0.5, _f[1] + _f[3] * _f[6] * 0.5)
        _s, _p, _o, _w = place(s57, _m[0] + _f[4] * 1500.0, _m[1] + _f[5] * 1500.0,
                               pins_active=False)
        if _o and _s['parcels'][_p]['placement']['road_id'] in ids57:
            _place58 = _s['parcels'][_p]['placement']
            break
    assert _place58 is not None, 'no lot could front any chord of the curve'
    assert _place58['x1'] - _place58['x0'] == V0_WIDTH, _place58

    # 59. ONE DECISION: ANY chord failing refuses the WHOLE path, and nothing
    #     is added or spent. A path that half-built where it first hit
    #     something would leave the player a road they did not draw and a bill
    #     for it.
    s59 = citytick.seed_state()
    s59['money'] = 40000.0
    _hits = [(2000.0, -3300.0), (4000.0, -2100.0), (6000.0, -3300.0)]
    s59, path59, ids59, ok59, why59 = draw_road_path(s59, _hits, pins_active=False)
    assert not ok59 and path59 is None and ids59 is None, (ok59, path59)
    assert 'crosses' in why59 and 'arterial' in why59 and 'chord' in why59, why59
    assert s59['money'] == 40000.0 and s59['roads'] == {}, (s59['money'], s59['roads'])
    #     and the resolver hands back NO segments, not the ones it had built
    #     before it hit something - a caller that took them would half-build.
    _ok59e, _why59e, _segs59e = resolve_road_path(s59, _hits, pins_active=False)
    assert not _ok59e and _segs59e is None, (_ok59e, _segs59e)
    #     TWO NODES IS A ROAD - the straight case through the same door.
    s59f = citytick.seed_state()
    s59f['money'] = 40000.0
    s59f, path59f, ids59f, ok59f, why59f = draw_road_path(
        s59f, [(2000.0, -4000.0), (5000.0, -4000.0)], pins_active=False)
    assert ok59f and path59f == 'C1' and len(ids59f) >= 2, (ok59f, why59f, ids59f)
    assert s59f['roads'][ids59f[0]]['start'] == (2000.0, -4000.0)
    assert s59f['roads'][ids59f[-1]]['end'] == (5000.0, -4000.0)
    #     and the price is the PATH's, refused once, on a fresh city's balance
    s59b = citytick.seed_state()
    _ok59b, _why59b, _segs59b = resolve_road_path(s59b, _CURVE, pins_active=False)
    assert not _ok59b and _segs59b is None, _ok59b
    assert "can't afford" in _why59b, _why59b
    #     AT THE BOUNDARY, so a price that is merely WRONG is caught and not
    #     just a price that is absent: one uu under the quote refuses and the
    #     exact quote draws.
    _cost59 = 10.0 * _len57 / 100.0
    s59g = citytick.seed_state()
    s59g['money'] = _cost59 - 1.0
    _ok59g, _why59g, _ = resolve_road_path(s59g, _CURVE, pins_active=False)
    assert not _ok59g and "can't afford" in _why59g, _why59g
    s59h = citytick.seed_state()
    s59h['money'] = _cost59
    _ok59h, _why59h, _ = resolve_road_path(s59h, _CURVE, pins_active=False)
    assert _ok59h, _why59h
    s59h, _p59h, _i59h, _o59h, _w59h = draw_road_path(s59h, _CURVE,
                                                       pins_active=False)
    assert _o59h and abs(s59h['money']) < 1e-9, (_o59h, s59h['money'])
    #     an unknown type is refused at the boundary here too
    _ok59c, _why59c, _ = resolve_road_path(s57, _CURVE, 'motorway',
                                            pins_active=False)
    assert not _ok59c and 'unknown road type' in _why59c, _why59c
    #     and fewer than two nodes is not a road
    _ok59d, _why59d, _ = resolve_road_path(s57, [(0.0, 0.0)], pins_active=False)
    assert not _ok59d and 'two nodes' in _why59d, _why59d
    #     THE WHOLE PATH must be long enough to hold a lot - measured on the
    #     polyline, not per chord, because a 410 chord never is and refusing
    #     every curve for that would be measuring the wrong thing.
    _ok59i, _why59i, _ = resolve_road_path(
        s57, [(3000.0, -4000.0), (3300.0, -3800.0)], pins_active=False)
    assert not _ok59i and 'too short' in _why59i, _why59i
    #     AND IT MUST STAY ON THE PLATE, checked on the SAMPLED POLYLINE
    #     rather than on the nodes. A Catmull-Rom reaches past its own nodes
    #     on a bend - measured below, 20 uu past the lowest node for one set
    #     of three - so nodes that are all inside are not a proof that the
    #     road is.
    s59j = citytick.seed_state()
    s59j['money'] = 40000.0
    _ok59j, _why59j, _ = resolve_road_path(
        s59j, [(2000.0, -4000.0), (4000.0, -4400.0), (6000.0, -4000.0)],
        pins_active=False)
    assert not _ok59j and 'off-board' in _why59j, _why59j
    _over59 = sample_path([(2000.0, -4000.0), (2600.0, -4150.0),
                            (6000.0, -3600.0)])
    assert min(_p[1] for _p in _over59) < -4150.0, min(_p[1] for _p in _over59)
    #     and the case that separates the two: EVERY NODE on the plate, and
    #     the curve reaching 30 uu past its edge between them. Checking the
    #     nodes would accept this and put a road off the board.
    _nodes59k = [(2000.0, -4000.0), (2600.0, -4229.0), (5000.0, -3200.0)]
    for _nx, _ny in _nodes59k:
        assert PLATE_X_MIN <= _nx <= PLATE_X_MAX, _nx
        assert PLATE_Y_MIN <= _ny <= PLATE_Y_MAX, _ny
    assert min(_p[1] for _p in sample_path(_nodes59k)) < PLATE_Y_MIN
    s59k = citytick.seed_state()
    s59k['money'] = 40000.0
    _ok59k, _why59k, _ = resolve_road_path(s59k, _nodes59k, pins_active=False)
    assert not _ok59k and 'off-board' in _why59k, _why59k

    #     A CURVE MAY NOT BE DRAWN THROUGH A STANDING BUILDING either - the
    #     placed-lot scan, which a curve needs as much as a straight road and
    #     which nothing else here exercises.
    s59l = citytick.seed_state()
    s59l['money'] = 40000.0
    s59l, _pl59, _ol59, _wl59 = place(s59l, 4000.0, -2000.0, pins_active=False)
    assert _ol59, _wl59
    _lot59 = s59l['parcels'][_pl59]['placement']
    _ok59l, _why59l, _ = resolve_road_path(
        s59l, [(3000.0, -3000.0), (4000.0, -2400.0), (5000.0, -3000.0)],
        pins_active=False)
    assert not _ok59l, (_ok59l, _lot59)
    assert 'overlap' in _why59l and 'existing lot' in _why59l, _why59l

    # 60. A LOT SPANS MORE THAN ONE CHORD, which it has to: the curve is
    #     sampled at 410 and the narrowest lot in the catalogue is 820. Before
    #     path_span every click on a curve was refused with "off-board:
    #     snapped span exceeds the R3 road" on completely open ground - the
    #     bound was the chord's own range, and no lot fits in 410 uu.
    _seg60 = _road_dict(s57['roads'][_place58['road_id']])
    _f60 = road_frame(_seg60)
    assert _f60[6] < V0_WIDTH, _f60[6]          # the chord is shorter than a lot
    _lo60, _hi60 = path_span(_all_roads(s57), _seg60)
    assert _hi60 - _lo60 > _f60[6], (_lo60, _hi60, _f60[6])
    assert _lo60 <= _place58['x0'] and _place58['x1'] <= _hi60, (_place58, _lo60, _hi60)
    #     STILL BOUNDED, only by the joined run rather than the one chord: the
    #     widening is the immediate neighbours and nothing further, so a span
    #     cannot run round a bend and come out where the pad does not go.
    _ends60 = [r for r in _all_roads(s57) if r['id'] in (ids57[0], ids57[-1])]
    for _e in _ends60:
        _l, _h = path_span(_all_roads(s57), _e)
        _fe = road_frame(_e)
        assert _h - _l < 3.0 * WIDTH_QUANTUM, (_e['id'], _l, _h)

    print('placement self-check: 60/60 pass (pure-Python click->lot->state '
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
          'road lot does, proven end to end PLUS road types as mechanics, '
          '2026-09-06 (40-48, MONDAY_DECISIONS section 2): width_class IS '
          'the type and every number comes from econrules.json, so the '
          'owner retunes the table without touching code; road_half/'
          'road_max_reach reduce EXACTLY to the ROAD_HALF and '
          'ROAD_MAX_REACH constants for an avenue and for a road carrying '
          'no type at all, which is what makes 1-39 above still measure '
          'the board they always did; the highway refuses frontage with a '
          'reason a player can act on AND refuses to be built across; '
          'roads are priced per 100 uu by type, refused when unaffordable '
          'without spending anything, and charged once, by draw_road, '
          'from the same candidate that was quoted; the rent multiplier '
          'is pure and TESTED BUT NOT WIRED - citytick.tick() is the '
          'coordinator\'s and applying it there is one line, deliberately '
          'left; PLUS the drag-direction fix, 2026-09-06 (49): ordering a '
          'drawn segment\'s endpoints at the source, because a road drawn '
          'right to left mirrored every lot placed on it about the start '
          'point and flipped its side name - a real defect reachable today, '
          'found while generalizing the resolver to arbitrary directions; '
          'PLUS roads at ANY DIRECTION, 2026-09-06 (50-53, item 11 first '
          'half): the resolver works in PROJECTION space (a lot\'s x0/x1 '
          'are the scalar projection of its span onto the road\'s unit '
          'direction, which for both built-ins IS the world coordinate '
          'already stored, asserted as an identity), lot and road '
          'footprints are quads with a separating-axis test that reduces '
          'exactly to rects_overlap while everything is axis-aligned '
          '(checked against it, not argued), side names come off the '
          'NORMAL rather than the dominant axis of the run - the case '
          'where the two disagree is tested - and the "too diagonal" '
          'refusal is gone: a 45 degree road draws unsnapped and a lot '
          'placed on it gets a rotated pad, priced by its true length, and '
          'two lots along one diagonal street both stand where a '
          'bounding-box scan would have refused the second on empty '
          'ground - and the same for the road-vs-lot, road-vs-road and '
          'lot-vs-highway scans, each shown against the box test that '
          'would have refused it PLUS curved multi-node roads, 2026-09-06 '
          '(56-60, ROADS_AS_MECHANIC section 5): a Catmull-Rom through the '
          'committed nodes, resampled by ARC LENGTH at the 410 quantum with '
          'the leftover merged rather than left as a stub, drawn as ONE road '
          '- one decision, one price, one path id - whose chords are ordinary '
          'roads afterwards; _in_crossing counts PATHS, without which every '
          'curve would be "the crossing" end to end and carry no lots at '
          'all; and a lot spans the joined run of chords rather than the one '
          'it sits on, because the curve is sampled at 410 and the narrowest '
          'lot is 820; live cursor-trace '
          'coordinates, actor spawn/resolve, and the feel itself are NOT '
          'provable here - see module docstring, and PLACEMENT_GRID.md '
          'section 8 - the owner\'s own click on empty board is the real '
          'acceptance test)')

    if os.path.exists(_SELFTEST_PATH):
        os.remove(_SELFTEST_PATH)
