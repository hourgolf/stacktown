# Road build contract — v0 of drawn roads, within today's constraints

Dispatched 2026-09-04, answering the owner's own live report: "we're
still on a pre-built intersection. how do we build roads?" — nothing is
built yet. This is v0 of `Docs/ROADS_AS_MECHANIC.md`'s drawn-road
mechanic, narrower even than that study's own section 5 "recommended
v0": straight chords only, no curve fitting, no intersections created.
Parts (a) and (b) below are built and self-tested this pass
(`placement.py`, 39/39). Parts (c) and (d) are specs for later windows
— the click-driver input (the coordinator's own) and the dormant-actor
pool (an editor window granted later) — not code.

## 0. Scope relative to `ROADS_AS_MECHANIC.md`

This is the data model and the `resolve_click` integration underneath
that study's own vision, not the vision itself. What carries forward
from the owner's four settled decisions there:

- **A cursor, in road mode only** — section 4 below names the mode
  toggle and the keys it must never collide with.
- **Road types are mechanics, not skins** — `width_class` exists as a
  field (task a) but v0 has exactly ONE class, `'avenue'`; the
  four-mechanic palette (dirt/avenue/boulevard/highway, the highway's
  frontage refusal) is real, future work this field makes room for,
  not built here.
- **The wedge gaps are the look** — not yet relevant. Wedges are what
  happens when straight lots meet a CURVING road; v0 has no curves, so
  there is nothing to dress yet. Worth remembering once curves land.
- **Game start: both** — untouched by this pass.

## 1. What's built and tested (tasks a/b)

**State** (`citytick.seed_state`): `state['roads']` — a dict of
`{road_id: {'id', 'start': (x,y), 'end': (x,y), 'width_class'}}`,
straight chords, persisted exactly like `state['parcels']` (the same
`save_state`/`load_state`, no special-casing). Empty by default;
`draw_road` is the only writer. A state predating this key (the
owner's real save) simply lacks it — every reader uses
`state.get('roads', {})`, the same backward-compat discipline
`lot_road_id` already established for a different missing key, not a
migration this pass performs.

**`placement.ROADS` is dynamic** (task b): `_road_dict(seg)` converts a
state segment into `resolve_road`'s own expected shape (+`side_plus`/
`side_minus`/`axis`, read off the segment's own geometry, never stored
twice); `_all_roads(state)` returns the two built-ins plus every drawn
segment, fresh each call. `resolve_click` changed in exactly the way
the task asked to be named: every place that used to read the
module-level `ROADS` constant (`resolve_road(...)`, `_in_crossing(...)`,
both `lot_rect(...)` calls in the overlap scan) now calls
`resolve_road(_all_roads(state), ...)` etc. instead. Nothing in
`resolve_road`, `_in_crossing`, or `lot_rect` themselves changed shape —
they already took a `roads` argument generically; only what
`resolve_click` passes them did.

**A real bug found and fixed while wiring this, not after**: `lot_rect`
used to hard-code "the road is either `'cross'` or it's arterial-style"
— correct for two roads, silently wrong the moment a THIRD, ARBITRARY
road exists, since a drawn road's own axis has nothing to do with the
string `'cross'`. Generalized to look up the lot's own road by id
(`_find_road`) and read ITS axis and centreline, checked (not assumed)
to reduce to exactly today's math for both built-ins — self-test 28.

**`resolve_road_draw` / `draw_road`** — the same two-function
architecture `resolve_click`/`place` already established for a lot: a
pure decision function (`resolve_road_draw`, callable by both a future
ghost preview and the real verb, so they can never disagree) and a thin
state-mutating wrapper (`draw_road`, mirrors `place()`'s own
`(state, id, ok, reason)` return shape exactly).

Self-test line: `placement self-check: 39/39 pass` (tests 28-39 are
this pass's own addition).

## 2. The axis-alignment limit — named, not hidden

`resolve_click`'s own world-coordinate recovery
(`road['start'][axis_idx] + along`) only recovers a correct WORLD POINT
when a road's direction actually IS one world axis. A true diagonal
road would need `along` recovered as a full 2D point along the road's
own direction vector — nothing in `resolve_click` does that today, and
teaching it to is real, separate work this pass does not attempt
(section 6 restates this as explicitly deferred).

**So v0 roads are axis-aligned only.** `resolve_road_draw` decides
orientation from whichever delta dominates the two click points (≥3x
the other — a deadzone roughly 18-72° off each axis where neither
wins): close to horizontal or vertical SNAPS to exactly that (the minor
coordinate forced equal to the start point's own, both endpoints then
rounded to `POSITION_QUANTUM`); a genuinely diagonal click-pair REFUSES
("too diagonal...") rather than silently reinterpreting a gesture the
player did not draw as something straight.

**What lifting this limit would need**, for whoever picks it up next:
`x0`/`x1` becoming an along-road distance plus a perpendicular offset
instead of world scalars everywhere they are used today — `resolve_
click`'s own snap step, `lot_rect`, and `init_unreal._lot_transform`
(the driver's own world-transform math) would all need the same
generalization, not just this module.

## 3. What a drawn road does to existing lots, and its own refusals (task e)

`resolve_road_draw` refuses, in order: too diagonal (section 2);
**too short** (`MIN_ROAD_LENGTH = V0_WIDTH`, 820 — a road that cannot
hold even one lot answers no question a player would ask it to);
**off-board** (outside the measured plate, same `PLATE_X/Y_MIN/MAX`
every lot click already uses); **crosses any EXISTING road** — checked
against the two built-ins AND every already-drawn segment via a new
`road_rect(road)` (the same rectangle shape `lot_rect` returns, so one
`rects_overlap` call compares a candidate against a road OR a lot with
no third function). **No new intersections in v0** — matches `ROADS_AS
_MECHANIC.md`'s own section 5 scope note directly; the one existing
arterial×cross crossing is not re-litigated, only NEW ones are refused.
**Overlaps an existing lot** — placed (`state['parcels']`, via
`lot_rect`) OR **pinned** (`PINNED_SPANS`, via the same `lot_rect`
generalization, wrapping each pin as a lot-shaped dict). The pinned
check is a real gap found WHILE writing this function's own
self-tests, not assumed from `resolve_click`'s shape: a pin carries no
`'placement'` key at all (`ensure_parcel` never adds one — only
`place()` does), so the placed-lot loop silently skips every pin by
construction; a separate check was needed, mode-gated on `pins_active`
exactly like `resolve_click`'s own `PINNED_SPANS` check.

**Once accepted**, a road is immediately buildable-against — no
separate activation step the way a LOT needs a dormant pool actor
(section 5). Proven end to end, not just at `resolve_road`'s own layer
(self-test 39): `place()` against a drawn road resolves, snaps, and
computes its world footprint through the exact same path a built-in
road lot does.

**What does NOT change**: nothing about any existing lot. A road can
never be drawn where it would overlap one, so no existing lot's own
state or footprint is ever touched by a road being added.

## 4. Input contract (task c) — for the click driver, not built here

**A road MODE toggle key, first click = start, second click = end**,
calling `resolve_road_draw` for the ghost preview exactly as the
existing lot ghost already calls `resolve_click` — same shared-
authority architecture, so the preview can never show something the
real verb would refuse. Refusals (crossings, overlaps, too-diagonal,
too-short, off-board) surface via the exact reason strings
`resolve_road_draw` already returns, same as the lot ghost's own
message classifier does today.

**RESERVED KEYS — confirmed live in `BP_LensRig`'s own graph
(`Docs/LENSRIG_P0.md`), 2026-09-04, never rebind any of these to a road
(or any other) verb:**

    A / D       camera arc
    W / S       camera reach (zoom), proportional
    R / F       camera pedestal (height)
    Q / E       camera zoom ladder (tighter / wider)
    arrow keys  camera pan / tilt

Also already taken by economy verbs: `B` (buy), `H` (repair — moved off
`R` this same session for exactly this collision), `N` (reset). `U`
(upgrade) per `ECONOMY_TICK_CONTRACT.md`. `MouseScrollUp`/
`MouseScrollDown` (width cycle, ghost). Left mouse button (select /
place). What's left and unclaimed: `M`, `G`, `T`, `Y`, most letters
past this list — a specific pick is the coordinator's own call when
they wire this, not decided here.

**Request shape**: given upgrade/repair were wired as Python-side
`unreal` module attributes rather than GameInstance properties (proven
simpler, both drivers already in-process — the coordinator's own
finding this session), the natural shape here is the same: four floats
(`x0,y0,x1,y1`) plus the mode flag, not a new GameInstance property
pair. Left as the coordinator's own call, not decided here.

## 5. The visual (task d) — spec only, editor window granted later

**Mesh: a scaled cube with the road material** — the task's own
suggestion, and consistent with what the placeholder pad already uses
for an unbuilt lot (a stock engine cube, scaled). No new asset needed
for v0.

**Segment → transform, derived, not guessed:**

    center = ((start.x + end.x) / 2, (start.y + end.y) / 2, some fixed Z)
    yaw = degrees(atan2(end.y - start.y, end.x - start.x))
    scale.x = length (|end - start|) / cube's own unscaled edge length
    scale.y = CORRIDOR (citylayout.CORRIDOR, verified this pass = 2260.0,
              = 2 * ROAD_HALF) / cube's own unscaled edge length
    scale.z = a fixed, thin height (a road is not a building; a small
              constant, not derived from anything else)

A road segment is symmetric along its own length (unlike a lot, which
has a distinct front) — ONE yaw per segment, not the two side-dependent
yaws `_lot_transform` computes for a lot facing a road.

**Pool size**: v0 is "the smallest thing that answers the question"
(`ROADS_AS_MECHANIC.md`'s own words for its own v0) — propose **10**
dormant road-segment actors, not calibrated against a board width the
way `POOL_SIZE=30` was for lots; a genuinely provisional number for
whoever builds the pool to revise once real play shows the actual
rate roads get drawn at.

**Activation**: exactly like a parcel — `mk_testcity_builds.py` places
the dormant pool (hidden, non-colliding, labelled `POOL_ROAD_NN` or
similar to keep the namespace distinct from `POOL_NN`'s own parcel
pool); the driver claims the lowest-numbered free one on a successful
`draw_road`, sets its transform from the math above, sets it visible
and collidable, labels it with the road's own id (`R1`, `R2`, ...) —
the identical location/identity/label/hidden/collision sequence the
lot-placement channel already uses, not a second mechanism.

## 6. What's not built, deliberately

- `init_unreal.py` consumption of a draw-road request — the same
  caution `ECONOMY_TICK_CONTRACT.md`'s upgrade/repair section already
  named: that file is under active concurrent edit by other lanes, and
  the exact request shape is the coordinator's own call once they wire
  section 4's input path.
- The dormant pool itself (`mk_testcity_builds.py`) — an editor window,
  granted later, not this pass's to touch.
- Arbitrary-angle roads (section 2), curves, wedge-dressing,
  intersections created by a new road, bridges, elevation, and the
  three-more-than-avenue type palette — all already named open in
  `ROADS_AS_MECHANIC.md` itself; nothing here closes any of them, only
  `width_class` existing as a field is new groundwork for the palette
  question specifically.

  **The type palette closed on 2026-09-06** (section 7 below). The rest
  of that list is still open; curves and arbitrary angles are the next
  item.

## 6a. A defect this contract's own v0 shipped, fixed 2026-09-06

**A road drawn right to left mirrored every lot placed on it.**
`resolve_click` recovers a lot's world position as
`road['start'][axis] + along`, and `along` runs along the *segment's own*
direction — so an east-to-west road put every lot at `2 * start_x - x`,
a mirror image about the start point, and flipped its side name with it
(the normal is the direction rotated +90°, so a click *south* of an
east-to-west road came back `'north'`).

Reachable today by dragging right to left. Silent whenever the mirrored
span still landed on the road; test 31's own road, drawn the other way,
put a south click's lot at `[7890, 8710]` instead of `[6490, 7310]`.

Found while generalizing `resolve_road_draw` to arbitrary directions,
where the sign of the direction stops being an edge case. **Fixed at the
source** — the endpoints are ordered when the segment is created — rather
than at each of the three places that read the direction. Nothing else
changes: the length is an absolute value, `road_rect` takes min/max, and
`_road_dict` reads orientation off the shape. The player gets the road
they drew.

It also buys something for section 5's curves: with a canonical
direction, a lot's `x0`/`x1` are exactly the scalar projection of its
span onto the road's unit direction — which for an axis-aligned road IS
the world coordinate it already stores. The arbitrary-direction
generalization is therefore backward-compatible with every lot already
saved, which it would not have been while the direction could point
either way.

## 6b. Roads at any direction (2026-09-06) — section 2's limit lifted

Section 2 named the axis-alignment limit honestly and said what it would
take to remove: *"a true diagonal road would need `along` recovered as a
full 2D point, along the road's own direction vector, which nothing in
`resolve_click` does today."* That is exactly what changed.

**The resolver works in projection space.** A lot's `x0`/`x1` have always
been world coordinates on its road's axis. Generalized, they are the
**scalar projection of the span onto the road's own unit direction**, and
the world point at projection `s` is `start + u * (s - s0)`, where `s0`
is the projection of the road's start onto itself. For the arterial `u`
is `+X` and `s0` is `PLATE_X_MIN`, so `s0 + along` **is** the world `x` —
the identity self-test 13 already checked, unchanged — and the same holds
in `y` for the cross street. One line different from the `world_coord` it
replaces, and **no lot already saved changes meaning**.

That backward compatibility is only true because §6a ordered a drawn
segment's endpoints. With the direction free to point either way, `s`
would be the world coordinate *negated* on half the roads.

**Footprints are quads, compared by a separating-axis test.** A 45° lot's
pad is an 820 × 1500 rectangle turned 45°; its bounding box is about 1640
square and the empty corners are most of it. A box scan therefore refuses
real ground — two houses along one diagonal street have boxes that
overlap and pads that do not. `quads_overlap` reduces **exactly** to
`rects_overlap` while everything is axis-aligned (touching is a miss,
matching the strict `<`), and that reduction is checked against the old
function on real lot pairs rather than argued. All five scans compare
pads: lot-vs-lot, road-vs-lot, road-vs-road, road-vs-pin, and
lot-vs-highway-corridor.

**Side names come off the normal.** Not off a same-X / same-Y test, and
not off the dominant axis of the *run*: whichever component of the normal
dominates picks the pair of names and its sign picks which is
`side_plus`. This reduces exactly to the two conventions the built-ins
already use, and it is the only rule that stays right for a road running
down and to the right at, say, 2:1 — whose direction is Y-dominant (so a
dominant-axis rule says "west") while its normal points **east**, which
is where those lots are.

**"Too diagonal" is gone.** The 3× dominance test survives as a *snap
threshold* rather than a refusal: a drag within about 18° of an axis
still snaps to exactly that axis, because a player aiming down a street
should get a straight one and not a road two degrees out. Anything else
is now the road they drew.

**Length is the centreline's.** Axis-aligned roads gave the same answer
as the sum of the two deltas; a diagonal does not, and it is the
centreline that a lot must fit along and that the type prices. A 500 × 500
drag is 707 uu — under the 820 a lot needs — where the sum says 1000.

**The pad poses.** `LotFrame::Pose` takes its anchor and yaw off the
road's own frame, and reduces exactly to the four axis-aligned cases it
replaced. Without it a diagonal lot would resolve correctly and still
stand in the wrong place.

## 6c. Curved multi-node roads (2026-09-06) — section 5's v0, built

`DrawRoadPath(nodes)`. A Catmull-Rom through the committed nodes,
resampled by **arc length** at the 410 quantum into straight chords,
drawn as **one road**: one decision, one price, one path id. The chords
are how a curve is stored and drawn, not what it is.

**Arc length, not parameter space.** A Catmull-Rom's parameter runs
faster round the outside of a bend, so even-`t` sampling gives long
chords through corners — exactly where a chord's error against the curve
is largest. The end tangents are **extrapolated** (`2*P0 - P1`), not
duplicated: duplicating halves the tangent and changes the curve's shape
near its ends, so the road would leave its first node along a curve the
player did not draw. The last node is always a vertex, and a leftover
shorter than half a spacing is **merged** into the chord before it — a
50 uu chord is a road segment with a 2260 uu corridor and no length.

**One decision.** Every chord is checked against the board and any
failure refuses the whole path, naming the chord. Nothing is added and
nothing is spent: a path that half-built where it first hit something
would leave the player a road they did not draw and a bill for it. The
length, the minimum and the price are the **path's** — a 410 chord is
under the 820 a lot needs, and refusing every curve for that would
measure the wrong thing. The plate check runs on the **sampled
polyline**, not the nodes, because the curve reaches past its own nodes
on a bend.

**A path is one road to everything downstream**, and it has to be. Two
things break otherwise, and both were found by building it:

1. **`_in_crossing` must count paths, not chords.** Consecutive chords
   share an endpoint, so the shared point has `along` in range for both
   — and there is one every 410 uu. Counting chords makes the whole of
   every curve "pavement shared by more than one road", and no lot can
   front a curve at all.
2. **A lot's span must be the joined run, not one chord.** The curve is
   sampled at 410 and the narrowest lot in the catalogue is 820, so a
   lot never fits inside a single chord: every click on a curve came
   back `off-board: snapped span exceeds the R3 road` on open ground.
   `path_span` widens the bound by the immediate neighbours only — one
   chord either side — because the pad is a straight rectangle in this
   chord's frame and a span that ran further could come out where the
   pad does not go.

It **does not cross itself**, by definition: consecutive corridors
always overlap and chords a few apart overlap on a bend, so the crossing
check runs against the board only. **What that leaves open, named rather
than hidden:** a path that loops back over itself is accepted, because
this version cannot tell that from a tight bend. Section 5 says "a
single open-ended road" and defers intersections; a self-crossing curve
is the same question and waits with them.

**A second pre-existing gap found on the way, and raised rather than
closed:** a lot's pad can hang off the plate. The span bound keeps a lot
inside its *road*, and for the two built-ins the road spans the plate so
those were the same thing; they are not the same thing for a road drawn
near an edge. The first curve along the southern margin put a pad at
y = −5740 against a plate that stops at −4230, and self-test 52's own
45° lot reaches y = 5150. The fix is four comparisons against
`quad_rect(lot_quad(...))` and it moves where lots may go on boards that
already exist — the owner's call, like the frontage-corridor gap in §7.

**Still not built:** intersections. Two roads still refuse to cross, and
a path is exempt only from itself.

## 7. Road types as mechanics (2026-09-06)

`MONDAY_DECISIONS.md` section 2 decided the four types on 2026-09-01 —
dirt, paved avenue, tree-lined boulevard, highway, the highway
**refusing frontage** — and left every number open. `NIGHT_PLAN.md`
adopts that section's proposed table as working defaults. They live in
`econrules.json` as seventeen `road_*` keys, so the owner retunes any
cell without a code change or a rebuild.

**`width_class` IS the type. No new field.** The queue item proposed a
`type` beside `width_class`; the coordinator's 20:22 note settled it the
other way, and it is the better answer: the field already existed on
every segment, its one existing value (`'avenue'`) is already one of the
four names, and a segment written before types existed means the avenue
by that fallback alone. No saved city needs migrating and no two fields
can disagree.

What each type decides:

| | dirt | avenue | boulevard | highway |
|---|---|---|---|---|
| carriageway | 900 | 1400 | 1400 | 2000 |
| corridor half | 880 | **1130** | 1130 | 1430 |
| cost / 100 uu | $5 | $10 | $20 | $30 |
| rent | 0.75x | 1.0x | 1.25x | 1.1x, by proximity |
| may be fronted | yes | yes | yes | **no** |

The corridor half is `carriageway / 2 + VERGE`, and **VERGE = 430 is
recovered, not chosen**: today's avenue is 1400 wide inside a corridor
whose half is `citylayout.HALF` = 1130. So an avenue — and a road
carrying no type at all, which is what both built-ins are — measures
*exactly* the constant the board was authored against. That is what
lets every test written before this one keep measuring the same board.
It is a literal rather than `road_width_avenue / 2`, deliberately: it
records how wide the road was when the board was authored and must not
move when the owner retunes the avenue.

Three refusals are new, and each names what a player can do about it:

- **`no frontage`** — a click whose nearest reaching road refuses
  frontage. Without it the answer is "not within reach of any road",
  which is true and useless standing on a highway's verge. Bounded by
  the highway's *own* reach: a click outside every road's reach still
  gets `off-board`.
- **`in the road: … would run across the R1, a highway`** — a lot
  fronting some *other* road may not be laid across a highway's
  corridor. Refusing frontage is not enough on its own: every other
  refusal is reached *through* the road a lot faces, so a road nothing
  faces is unguarded by construction.
- **`can't afford`** — checked last, after every geometric refusal (a
  road that crosses a building is illegal whatever the balance), and
  checked in the resolver so the ghost preview can say it without
  spending anything. `DrawRoad` is the only thing that spends, and it
  charges the same segment that was quoted through the same function.

**The rent multiplier is built, tested and NOT wired.** `Tick()` was the
coordinator's on the night this landed. `RoadRentMultiplier(Board,
State, Lot)` is the pure function rent is multiplied by; applying it is
one line in the economy loop.

Two open questions for the owner, both raised rather than assumed:

1. **The boulevard's median.** The table says "1400 + median" and does
   not say how wide the median is, so `road_width_boulevard` is 1400 —
   the same corridor as an avenue. Its rent and cost already differ; its
   *width* does not, and will not until the number exists.
2. **How the highway's bonus combines.** "Every lot within 2,000 uu of
   it rents at 1.1x" reads either as a multiplier or as an absolute.
   Built as a multiplier (dirt beside a motorway is 0.75 × 1.1 = 0.825),
   because that composes and keeps the type ordering intact; read as an
   absolute, a dirt lot beside a highway would out-earn a boulevard lot
   away from one. One word changes it.

**That gap is closed as of 2026-09-07** (§7a below); until then the check
was scoped to frontage-refusing roads and the gap was named here.

## 7a. A lot may not overlap any road's corridor (2026-09-07)

Decided as a working default by the coordinator's 23:37 note; the owner
reverts it with a word.

The case is the one self-test 39 **used to be**: a road drawn 3,000 uu
from the arterial leaves 740 uu between their pavements, which is less
than `BLOCK_DEPTH` — so its south frontage band ran 760 uu into the
arterial's own road surface. A lot stood in the road and nothing was
looking, because every other refusal in `resolve_click` is reached
*through* the road a lot faces.

**Its own road is not a crossing, and for a curve that is not free
arithmetic.** On a straight road the pad's near edge *is* `road_half` and
`quads_overlap` is strict, so a lot touches its own corridor without
overlapping it. On a curve it does not: a lot fronting one chord
necessarily overlaps the corridors of the chords either side, because
they are 410 uu apart and 2260 uu wide and the pad starts at the frontage
line of the one it faces. Comparing by **path** rather than by chord is
what keeps curves buildable — the first run of this check refused a lot
on all twelve chords of a curve, every one of them against the curve
itself.

**What it costs, measured rather than guessed:** on a three-node curve
probed at both sides of every chord, 4 clicks placed before and 2 after.
The two it refuses were being laid across the arterial's and the cross
street's pavement — the loss is the bug, not collateral.

Two self-tests moved to make room, and the reason is worth recording:
test 39 and test 45 both drew a road at y=3000 and placed a lot on its
south side. Both were placing lots *in the arterial*. They now draw at
y=3800, which leaves 1170..2670 and clears the arterial's 1130 by 40 uu.
