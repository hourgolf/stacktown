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
