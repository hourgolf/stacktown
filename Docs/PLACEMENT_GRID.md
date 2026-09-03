# Placement and the hidden grid — a study, declaration-first, no build

**Status: OWNER'S WORD RECEIVED 2026-09-02, v0 BUILD AUTHORIZED.** Written
by the beta lane on the owner's assignment, folding in roads sections 1
(the pen) and 3 (the 410 collision) since this directive makes them one
problem. Section 8 records the owner's four decisions and the v0
declaration; nothing in sections 1–7 needed to change to accommodate
them — the study's own lean (road-relative) and recommended v0 both
stood as written.

**The owner's brief, near-verbatim, 2026-09-02:** "small plate that grows
but we shouldn't show proposed blocks. players should be able to build
wherever board space is available (we can constrain the board size at
first so they can't travel into the void and drop a building) we just
need to figure out the 'grid' (whether that's squares, hexagons, or
otherwise) behind the scenes so players feel like they have ultimate
control of laying out their city."

**What produced it.** The lighting-control study (design lane) found the
play board is UNDERBUILT, not underlit — density moved local contrast
129%, lighting moved it 0% (that figure and the "14 of [a much larger
theoretical board]" comparison are the design lane's own measurement,
relayed here, not independently re-derived in this study). The owner's
answer to "what should hour one actually look like" is not "bake more
pins" — it's a different placement model entirely: a small board, free
placement anywhere there's room, no pre-drawn proposed-block ghosts, and
a grid the player never has to think about.

---

## 0. The finding this study turns on, same shape as roads' own §0

Read cold, "hidden grid" and "roads as a mechanic" look like two
assignments. They are one. `Docs/ROADS_AS_MECHANIC.md` already worked out
that a curved road cannot give a building a curved frontage — the
catalogue bakes rectangular boxes at five fixed widths — so a drawn road
is served by chord-lots: straight frontage segments, quantized to the
410-uu `WIDTH_QUANTUM`, laid along whatever the player drew. That
mechanism doesn't care whether the road it's serving was drawn a minute
ago or is the paved avenue already running through `TestCity`. **The
"hidden grid" the owner is asking for is the chord-lot model, generalized
from "frontage along a drawn road" to "frontage along any road, drawn or
existing."** Section 1 argues this against the alternatives rather than
asserting it, because the owner should be able to reject it with reasons
on the table, not just this lane's say-so.

---

## 1. The grid

Three candidates, argued, not dismissed.

### 1.1 Square, at the 410-uu quantum

The catalogue's five widths (820/1230/1640/2050/2460) are all multiples
of 410 — `citylayout.py`'s own comment records why: a block length that
isn't a multiple of 410 "cannot be tiled by catalogue buildings at all,"
learned the expensive way when `BLOCK_LEN=4800` produced 800-wide lots
that nothing baked fit. So *some* multiple-of-410 discipline is not
optional — that part is decided already, by scar tissue, not by this
study.

What a **pure square grid** would mean: divide the whole board into a
410×410 (or some multiple) cell grid, let the player place a building
footprint on any run of free cells, independent of any road. This is the
simplest thing that could work, and the honest case for it: zero
dependency on roads existing at all, so it works on turn one before the
player has drawn anything.

The honest case against it: **it produces buildings with no relationship
to a street.** A building's frontage — which face gets the door, the
shopfront, the arcade — is baked into the mesh by recipe (flank_modern,
flank_deco carry the arcade; plain recipes don't). A pure square grid
gives the player no way to *say* which side faces the street, because
there's no street in the model at all — only cells. The player could end
up placing a building backward relative to a road that runs past it, or
placing two buildings frontage-to-frontage with no street between them.
Square-grid city builders (the classic SimCity zone-and-grow model) get
away with this because roads are a SEPARATE layer the player draws
first and zoning snaps to it — which is really the road-relative model
wearing a square skin, not a counterexample.

### 1.2 Hex

Named because the owner asked for it by name, argued honestly rather than
waved off. Hex grids buy uniform adjacency (six equidistant neighbors,
no diagonal-distance ambiguity) and read as more "organic" than a
square lattice — the reason city builders that use hex (rare for
buildings; common for hex-based strategy terrain, e.g. the Civilization
family) reach for it.

The structural problem is specific, not aesthetic: **every baked asset in
this catalogue, flagship and wood both, is a rectangular box.** A hex
*cell* doesn't have a rectangular footprint, so a rectangular building
placed on one either (a) doesn't fill the cell, leaving a hex-shaped gap
around every rectangular box — visually the opposite of the tight,
fitted-piece look B3 already established as the target — or (b) the
building has to be re-baked hex-shaped, which is not a placement-system
change, it's re-authoring the entire catalogue (572+ baked assets on
flagship's side alone) around a new footprint shape. Hex terrain doesn't
have this problem because terrain has no fixed footprint to violate; hex
buildings do, and this project's buildings are already built. **Verdict:
hex is real, and rejected on cost, not on principle** — it would work
for a project that baked hex-footprint buildings from day one, and this
one didn't.

### 1.3 Road-relative (chord-lots) — the lean

Already specified in detail in `ROADS_AS_MECHANIC.md` §0–§1, §3: a road
is a polyline (drawn or pre-existing), lots are straight chords along it
quantized to 410, and the curve — or in a starter board's case, the
existing street geometry — is absorbed by the ribbon and by wedge-shaped
gaps at the joints, which the owner already ruled ARE the look (§6,
decision 3), not a defect to hide.

This is also how the genre actually does it, cited rather than assumed:
SimCity and Cities: Skylines zoning is not free placement on a grid —
it's zone-painting adjacent to a road, subdivided into lots along the
road's length, exactly the chord-lot shape. A pure grid with no road
relationship is closer to city builders nobody points to as "you feel in
control of your city" (Farmville-style placement grids read as a
management-sim UI, not a city). **Frontage-along-a-road is where the
"ultimate control" feeling the owner named actually comes from in this
genre** — the player draws the street, the street decides what's
buildable, and every lot the player sees is legible as "this faces that
road," which a bare cell grid cannot promise.

### 1.4 The verdict this study leans on

**"Grid" and "roads" are one system.** The 410 quantum is the unit both
share; the road (existing arterial or a player-drawn one) is what turns
a bare board into a sequence of legible, frontage-correct lots. A square
grid is what's LEFT when you strip the road relationship out — it still
needs the same 410 discipline, it just loses the thing that makes
placement feel like city-building instead of block-stacking. This
doesn't need to be re-decided from scratch: it's the same mechanism
`ROADS_AS_MECHANIC.md` already specified, pointed at both drawn roads
and the roads already sitting in `TestCity`.

---

## 2. The placement verb

**What the player does:** aim the cursor (already the owner's decision
for road mode, `ROADS_AS_MECHANIC.md` §6 decision 1 — and, separately,
already BUILT and owner-verified for parcel selection this session, so
this isn't a new input mechanism, it's the existing one pointed at a new
target) at a stretch of frontage along a road with free board behind it,
click, and the game resolves the largest or a chosen catalogue width
that fits the click point without crossing a neighboring lot or the
board edge.

**What's picked, and what isn't shown first:** the owner's brief is
explicit that proposed blocks should NOT be shown — no ghost preview of
a specific building before the player commits. That's a real, distinctive
choice worth naming plainly: most placement UIs (Cities: Skylines
included) show a translucent preview of the exact building before you
click. This design instead resolves the recipe and width AFTER the
click, the same way buying an already-placed pin resolves a price and a
mesh after the buy — click commits to "a building goes here," not to
"this specific building goes here." Width still needs to come from
somewhere: either the player picks a size class before clicking (a
minimal palette, not a full ghost-preview), or the game auto-fits the
largest catalogue width the remaining frontage allows. This study
doesn't resolve which — it's a v0-scoping question in section 7, not a
grid question.

**Orientation:** always toward the nearest road, not player-chosen —
frontage direction is what makes the road-relative model legible in the
first place, and a building facing away from its own street is exactly
the failure mode section 1.1 named against a pure grid.

**What the game refuses, and says so:** off-board (outside the current
plate — see section 3), overlapping an existing parcel, and no legal
frontage (a click too far from any road's chord line to resolve a lot).
Refusal needs to be loud, not a silent no-op — this project's whole
ledger is built around "failure is loud, never a fallback"
(`testcity_pins.require()`, `mk_da_catalogue.py`'s missing-asset report,
`woodmap.resolve()`'s refuse-rather-than-round) and a placement verb that
silently eats an invalid click would be the first thing in this codebase
to break that discipline.

---


### 2.1 Amendment, 2026-09-03 — reach, the road band, and the ghost (owner: "go ahead with the ghost pad")

The owner's first full session (04:38) showed why v0 read as "a parcel
showed up generally around the click": `resolve_click` bounded x to the
plate and snapped everything else, so a click on the studio floor at
(4671, 6954) placed a pad at (4100, 1880), five thousand units away.
Two refusals now bound the click to the block it asks for, both in
`placement.resolve_click` (the pure resolver, so the ghost and the click
can never disagree):

- **in the road** — `|y| < ROAD_HALF` (1130, `citylayout.HALF`): the
  click is on the carriageway or footway. Screen text: "That's the
  road - click the block beside it".
- **too far from a road** — `|y| > ROAD_HALF + BLOCK_DEPTH + REACH_SLACK`
  (1130 + 1500 + 600 = 3230): behind the block's back edge with 600 uu
  of forgiveness. Screen text: "Too far from a road".

The **ghost**: while the cursor rests on empty plate, `clickdriver.py`
runs the same resolver and draws the footprint a click would get - a
green box with "click to place", or a red box (on overlap, the refused
span) or a red label with the refusal - as a debug box for v0; a
translucent pad mesh is later polish. Cached per 20-uu cell so the
resolver is not re-run every frame.

**Measured, not assumed (my own PIE, 2026-09-03):** an activated pad is
the `Building` component itself - a cube scaled to width x 1500 x 30,
centred on the actor - so at `_PAD_CENTER_Y` = 1880 its front edge sits
exactly on the facade line (1130); the "stretched into the road" note
from 2026-09-02 was the old 1130-centred placement and is resolved. A
BOUGHT lot's mass (SM_WMass_w820_setback2) spans y = 1879..2579: front
at the pad's centre line, 750 uu behind the facade. Whether that is the
catalogue's intended setback (the mass name says two quanta, 820) or a
double setback is a design-lane question - not touched here.

### 2.1a Width cycle — spec, NOT wired (2026-09-03, PLAYABLE_PLAN.md §2.2)

The player chooses the ghost's width before clicking, instead of every
placed lot defaulting to `V0_WIDTH` (820). This section specs the wiring
precisely enough to build in one pass in `clickdriver.py`; it does not
touch `placement.py` or `clickdriver.py` itself - both stay exactly as
2.1 left them until this is built.

**The ladder, and its source.** `woodmap.WIDTHS = (820.0, 1230.0, 1640.0,
2050.0, 2460.0)` - five widths, "RE-BAKED ON THE FLAGSHIP WIDTH LADDER"
per `woodmap.py`'s own section-1 docstring (the wood catalogue reuses the
flagship's five widths rather than a second, independent ladder). This
is the correct source, not `recipes.py`'s own width table: `BP_
StacktownGameInstance.ActiveCatalogue` is the wood catalogue for this
slice (HANDOFF §2, "swapped flagship->wood, 2026-09-01"), and only
`woodmap.WIDTHS` is proven baked for it (`woodmap.asset_name` raises on
any width off this exact ladder). `V0_WIDTH` (820.0) is already
`WIDTHS[0]` - the cycle's own default state should start there, so a
session that never touches the keys places identically to today.

**The keys.** Primary: mouse scroll wheel. Fallback: Q/E. Both follow
`clickdriver.py`'s own established key idiom exactly (`_KEY` dict,
`unreal.Key()` + `set_editor_property('key_name', <name>)`, polled via
`pc.is_input_key_down(key)` with an edge computed against the previous
tick's `_st['down']` - see `_tick`'s existing `edges` loop, which this
extends rather than replaces):

    unreal Key names to add to _KEY: 'MouseScrollUp', 'MouseScrollDown', 'Q', 'E'

`MouseScrollUp`/`MouseScrollDown` are real, distinct `FKey`s in this
engine (not an axis read) - each wheel notch registers as a one-tick
`IsInputKeyDown` pulse, so the SAME edge-detection the B/N keys already
use (`down and not previously-down`) is the whole mechanism; no new
polling shape needed. Scroll up -> widen (index + 1); scroll down ->
narrow (index - 1); clamp to `[0, len(WIDTHS)-1]`, no wraparound (an
owner cycling past the top should land ON the top, not snap back to the
bottom - the same "loud, specific, not surprising" discipline the
refusal messages already hold to). Q mirrors scroll-down, E mirrors
scroll-up - the direction PLACEMENT_GRID.md's own brief implies by
listing them as one fallback for one gesture ("Scroll wheel (or Q/E)"),
not independently chosen here.

**NAMED CONFLICT, not resolved here:** Q and E are ALSO the zoom-ladder
step keys in `BP_LensRig`'s own `EventTick`/`TickBody` (camera focal
stops) - a Blueprint graph, FROZEN, and this session never confirmed
whether that camera code is still the live path post-freeze or whether
it moved with the click chain. If it is still live, binding Q/E in
`clickdriver.py` too means one press does BOTH a camera zoom step AND a
width-cycle step, simultaneously, from two different systems that do
not know about each other. Verify which is true (a measured PIE
check, not an assumption) before wiring Q/E; scroll wheel alone has no
such conflict and could ship first, with Q/E added only once the
camera question is answered - splitting a two-key feature into "ship the
unambiguous half now" is cheaper than guessing wrong on a frozen graph.

**State: where the chosen width lives.** One new key in `clickdriver.py`'s
existing `_st` dict, next to `n_acc`/`selected`: `_st['width_index']`,
integer, default `0` (-> `WIDTHS[0]` = 820, today's behaviour exactly).
Persists for the whole PIE session the same way `_st['selected']`
already does - a per-session choice, not per-hover and not saved to
`citystate.json` (the CHOICE is input state, not city state; only the
placed lot's resulting `width` value becomes state, same as `rid`/`tier`
today).

**How it flows into `resolve_click`.** One new parameter, appended so
every existing call site (including all 19 self-tests) keeps working
unchanged:

    def resolve_click(state, x, y, pins_active=True, width=V0_WIDTH):
        ...
        x0 = _snap(x - width / 2.0)
        x1 = x0 + width
        ...

Every place `V0_WIDTH` appears inside `resolve_click`'s OWN body becomes
`width` (the parameter); `V0_WIDTH` the module constant stays, now
serving only as the parameter's default and as `WIDTHS[0]`'s value in
the cycle above - not removed, since it is still the correct default for
any caller that does not care (exactly today's 13 arterial/pinned-
overlap self-tests, none of which need to pass a width to prove what
they prove). `place(state, x, y, pins_active=True, width=V0_WIDTH)`
takes the same new parameter, passes it straight through to
`resolve_click`, and writes it into the new parcel's dict in place of
the literal `V0_WIDTH` (`'width': width` instead of `'width': V0_WIDTH`)
- the one line that currently hardcodes it.

**The two callers that need the width threaded through, concretely:**

- `clickdriver.py`'s `_preview` (the ghost): reads
  `WIDTHS[_st['width_index']]` once per call, passes it to
  `placement.resolve_click(..., width=that_value)` - today's call site
  already computes a box from `lot['x0']`/`lot['x1']`, which already
  reflects whatever width `resolve_click` used internally, so the box
  drawing code itself needs no change, only the extra argument.
- `clickdriver.py`'s `click_at_hit`'s off-parcel branch: today writes
  `PlaceRequestX/Y` only, and the DRIVER (`init_unreal.py`'s placement
  channel) is what actually calls `placement.place()` - so the chosen
  width has to cross that same channel. Simplest: one more
  request-and-clear field on `BP_StacktownGameInstance`, `PlaceRequest
  Width` (a variable-flag edit, not a graph write - same category as the
  queued `SelectedParcel` one), written alongside `PlaceRequestX/Y` and
  read by the driver's existing placement-channel code the same tick it
  reads X/Y, passed to `place(..., width=that_value)` in place of the
  implicit default. Not a new channel shape, one more field on an
  existing one.

**Proof, once built:** three pads placed in a row at three different
scroll positions, `citystate.json`'s three `width` values matching the
three chosen ladder entries exactly, plus a capture showing the ghost's
box resizing live as the wheel turns - PLAYABLE_PLAN.md §2.2's own
proof bar, unchanged.

## 3. Board growth

**The plate starts small and constrained**, per the owner's own words —
this is explicitly NOT the full `citylayout.py` four-quadrant envelope
from turn one; it's something smaller, with a hard edge the player can
reach and be refused at ("can't travel into the void and drop a
building"). This study does not size the starter plate — that's a
massing/pacing call for whoever owns the economy's early-game feel, not
a grid-shape question.

**Three growth triggers, not mutually exclusive:**

1. **Purchase-driven fill.** The plate's own free lots get bought and
   built, same verb as today, no board expansion — this is "growth" in
   the sense the current 14-pin board already has, just without the
   pins.
2. **Road-drawing reaching an edge.** If the player draws a road toward
   the plate boundary, the act of the road reaching the edge is a
   natural trigger to extend the plate in that direction — the road
   mechanic and the growth mechanic share a verb for free, since roads
   are already how frontage gets created in section 1's model.
3. **An explicit expand verb.** A dedicated purchase or action that
   grows the plate without requiring a road to already be headed that
   way — the fallback for a player who wants more room before they've
   drawn anything new.

None of these are decided here; they're named as the candidate space so
the owner can pick without this study pretending to have picked for
them.

**Hard requirement, from the design lane's D20, relayed as a requirement
and endorsed here as one, not a preference this study is free to soften:
a plate piece must be a whole number of 410-uu quanta AND must contain
complete blocks — a seam running through a building is the one thing the
fitted-inlay-piece language cannot survive.** This constrains all three
triggers above to the same granularity: growth adds whole blocks, never
a partial one, regardless of which trigger fires it. Their proposal, not
yet a decision — **one piece = one city block plus its bounding
streets** — is the natural unit under this constraint, since it's
exactly the shape `citylayout.py`'s own `blocks()` already produces
(section 4's starter preset is four such pieces, already fitted
together). This study defers to that proposal rather than inventing a
competing one; it's a fabrication-side constraint on a data-model
question this lane owns, and the two lanes agree on the unit.

**How growth reads to the player, without UI — see section 6** for the
design lane's own answer (D20): a new piece arrives pale and ages into
the board, and the growing frontier shows raw end grain rather than an
invisible wall. Named here only as the pointer; the visual language
itself belongs in the twin-rule section where the rest of each lane's
fabrication language already lives.

**Two questions the design lane is queuing to the owner alongside this
study — left open here on purpose, not pre-answered:**
1. Is fitting a new piece onto the board itself a player-facing verb (an
   action the player takes), or does it happen automatically when a
   growth trigger fires?
2. When the plate's rim needs to move, does it move automatically, or is
   there a player TRIM verb that shapes the frontier deliberately?

Both bear directly on section 2's placement verb and section 3's growth
triggers above, but this study takes no position on either — they go to
the owner as options, alongside everything else here.

**The camera consequence is real and this lane owns that math** — the
boom's current defaults are hardcoded, not derived: `BoardCentre` is a
`BP_LensRig` instance value, currently `(0,0,0)`, "measured, never
authored" per `TESTCITY_PLAN.md`; the zoom ladder's `Reach` stops
(19000/11168/3500/1350/800) and the W/S key clamp (300..40000) are fixed
constants sized to the CURRENT 14-lot board. A plate that grows changes
what "the board" means under the boom's own orbit math
(`Location = BoardCentre + polar(Reach, Azimuth) at Height`, confirmed
live this session): `BoardCentre` would need to become the plate's own
running centroid (or a player-chosen focus) rather than a fixed point,
and the outer `Reach` clamp would need to grow with the plate rather
than stay pinned to a board sized for 14 lots. Neither is a hard
problem — both are already instance-editable, runtime-settable values,
not baked constants — but it is real, scoped work this study is flagging
for whenever growth actually gets built, not solving now.

---

## 4. What happens to the pinned city

**The 14 pins become the starter preset, not the game's parcel model.**
This is not a new decision this study is making — `ROADS_AS_MECHANIC.md`
§6 decision 4 already settled it for the roads redesign generally: "GAME
START: BOTH — a new game offers an empty board... or the starter preset.
The 14-lot board survives as that preset." Free placement inherits that
decision rather than re-opening it: the pinned board is one of (at least)
two ways to start a game, not the only shape a city can take.

**The seam, named, not solved:** `PARCELIZATION_CONTRACT.md`'s entire
identity model is pin-as-identity — a parcel's `rid`/`width`/`corner`
are declared once in `testcity_pins.PINS`, spawned once by
`mk_testcity_builds.py`, and `citytick.ensure_parcel()` only ever
registers what a pin already declared. Free placement is
placement-as-identity: there is no pin, no pre-authored table entry —
the player's own click is where `rid`/`width`/position/frontage first
come from. These are two different sources of truth for the same three
facts, and the migration from one to the other is real, non-trivial
work — not named here as something this study is deciding how to do,
only that it must happen, and that the starter preset keeps the OLD
model alive as one loadable option even after the NEW model exists as
the general case.

---

## 5. Data model

**What changes, concretely, from today's shape:**

`citystate.json`'s `parcels[pid]` today is `{rid, tier, width, owned,
accum}` — no position, because position was never state; it's the
actor's own transform, set once at spawn by the pin-driven builder and
read by nothing at runtime. Free placement needs position (and frontage
— which road, which side) to become real state, not something implicit
in a pre-placed actor: `citystate.json`'s parcels need a new shape,
something like `{rid, tier, width, owned, accum, position, road_id,
frontage_side}` — named here as a shape, not a committed schema.

**`pid` generation changes character.** Today it's
`actor.get_actor_label()`, deterministic because `mk_testcity_builds.py`
names every actor from its pin at editor-authoring time. Under
placement, there is no editor-authoring step — a `pid` has to be
generated at the moment of a runtime click: a counter, a GUID, or a
position-derived key (`"P_<road_id>_<offset>"` reads legible in a debug
log the way `"SW2"` currently does, which is worth keeping if it costs
nothing).

**The driver's own responsibility changes in kind, not just degree.**
`_sync_parcels` today only DISCOVERS pre-existing `BP_Parcel` actors
already sitting in the level and registers new ones into
`citystate.json` — it has never spawned an actor, only found one.
Free placement needs the reverse direction too: a click has to SPAWN a
new `BP_Parcel` at runtime, at the clicked transform, with its identity
set from the click rather than a pin — and that spawn has to go through
the same proven path `_sync_parcels` already uses to register a parcel
into state (`ensure_parcel`), not a second, parallel mechanism. This is
new capability, not a variation on anything built this session — every
buy-and-grow mechanism proven tonight assumed the actor already existed
before a player ever touched it. Runtime actor spawning driven by a
click is a real, unbuilt piece, named here as exactly that.

---

## 6. The twin rule

**One mechanic, two fabrications — restated, not re-decided.**
`ROADS_AS_MECHANIC.md` already settled this for roads and it carries
over unchanged: "The DATA MODEL: nodes, segments, type, elevation, and
the intersection graph. Both products must agree on what a road IS...
Only the MESHING and the MATERIAL fork." Free placement is the same
shape of split.

**Wood board:** grows as fitted inlay pieces — B3's own language, "many
fitted inlay pieces making the landscape," already the direction-B
lane's declared look and not this lane's to re-specify. A newly placed
wooden lot should read as another carved piece dropped into the board,
consistent with how `ROADS_AS_MECHANIC.md` §2.1 already described a
drawn road's fabrication for direction-B.

Two specific answers from the design lane's D20, both about making
growth legible without any UI: **a new piece arrives PALE and ages into
the board** — reusing D16's Age scalar, the same material-level patina
mechanism already declared for ordinary wear, repurposed here so a
freshly added piece visibly belongs to "just now" and settles into the
board's existing tone over time, exactly the way a real inlay piece cut
from fresher stock would read next to older ones. And **the plate's
growing frontier shows raw end grain** — a sawn edge, not a wall — so
section 3's "can't travel into the void" constraint reads as *a board
still being built*, not an invisible boundary the player bounces off.
Both are the design lane's own proposals, named here as the answer to
"how does growth look," not re-argued by this lane.

**Flagship board:** how the card board visually grows under free
placement is genuinely undecided — this study does not answer it, the
same way `ROADS_AS_MECHANIC.md` §2.2 left the flagship's road fabrication
"deliberately thin... named here only to hold the seam open." Whoever
owns flagship's look makes that call; this study only asserts that
whatever it is, it reads from the SAME shared data model (position,
road relationship, width, tier), not a fork of the state itself.

---

## 7. Recommended v0 — the smallest thing that answers the feel question

Mirroring `ROADS_AS_MECHANIC.md` §5's own discipline: the smallest
placement that tells the owner whether this feels like "ultimate
control" or like fighting a hidden ruleset.

1. **One road, already in the board** (the existing arterial/cross
   street in `TestCity`, or a single drawn road once that mechanic
   exists) — no new road-drawing needed to test placement itself.
2. **A small, hard-edged plate** — a handful of buildable chord-lot
   slots along that one road, board-edge refusal proven at a boundary
   the player can actually reach in under a minute.
3. **Click-to-place, no ghost preview** — resolve width/recipe after the
   click, exactly per the owner's brief; no proposed-block dressing at
   all, not even a faint one.
4. **No growth yet.** Purchase-fills-the-plate is enough to answer "does
   free placement feel good" without also building road-triggered or
   explicit-expand growth in the same pass — section 3's three triggers
   stay a menu for later, not a v0 requirement.
5. **The starter-preset path stays exactly as it is today** — the 14-pin
   board is not touched by this v0; it is the OTHER way to start a game,
   proven and owner-played already.

**What v0 deliberately does not answer:** board growth, the
placement-as-identity data-model migration in full, runtime `BP_Parcel`
spawning (section 5's real, unbuilt piece), road-drawing itself (still
the roads study's own v0, not duplicated here), or either fabrication
lane's actual look for a freshly placed lot. All real, all later, all
gated on the owner's read of this document first — nothing here is
authorized to build.

---

## 8. The owner's word, 2026-09-02 — v0 build authorized

Four decisions, relayed through the coordinator with attribution, none
of which required section 1–7 to change — the study's own lean and its
own recommended v0 both stood as written, which is worth stating
plainly rather than quietly taking credit for.

1. **THE GRID: road-relative, section 1's lean, chosen over a square
   grid.** Lots are frontage along roads — drawn or already standing —
   at widths on the 410 quantum. Grid and roads are one mechanic, not
   two systems that happen to share a number.
2. **v0 BUILD: AUTHORIZED — "Build it."** Not the whole study; the
   scope is exactly section 7's five points, unchanged: runtime
   `BP_Parcel` creation from a click along the EXISTING arterial, on a
   small hard-edged plate, no ghost preview, board-edge refusal
   reachable in under a minute, starter-preset board untouched. This is
   section 5's genuinely unbuilt piece — nothing built this session
   already does runtime actor spawning from a player action, every
   buy-and-grow mechanism proven tonight assumed the actor existed
   first.
3. **GROWTH: "purchase-fill only at first."** No plate expansion in
   early versions — buying fills the small plate, full stop.
   Road-reaches-edge and explicit-expand (section 3's other two
   triggers) stay a menu for later; this closes off building either one
   now, not just deprioritizes them.
4. **PIECE & RIM: "both automatic."** Closes D20's two queued
   questions: fitting a new piece is not a player verb, and the rim
   moves on its own when growth eventually exists — the board is the
   container, not something the player operates. Recorded here for the
   written record; the coordinator is relaying the same closure to the
   design lane directly.

**Camera consequence (section 3's `BoardCentre`/`Reach` math) is this
lane's to build, but not now** — it's scoped to when growth actually
ships, and decision 3 means growth isn't in this pass.

### v0's proof discipline — the headless half is DONE, not just planned

`Content/Python/placement.py` is written and self-tested, same shape
`citytick.py`'s own `__main__` block already uses: pure Python, no
`unreal` import, hand-computed known answers, 6/6 passing as of this
writing. It declares the full click → lot → state contract before any
of it touches the editor:

- **The plate:** a bounded stretch of the existing arterial, `[-2460,
  2460]` along X — 12 quanta wide, matching one `citylayout.py` block's
  own proven-tileable `BLOCK_LEN`, reachable edge-to-edge well inside a
  minute. Y=0 is the arterial centerline (`citylayout.py`'s own
  `blocks()` convention, reused not re-measured); a click's sign of Y
  is which side of the street it's on.
- **v0's own named simplifications:** every placed lot is a FIXED 820
  width (the catalogue's narrowest, sidesteps auto-fit entirely) and a
  FIXED `vernacular` recipe (the project's long-standing safe default).
  Both are explicitly not the eventual answer — section 2 left "which
  width, which recipe" open on purpose, and this v0 doesn't resolve it,
  it defers it so the click-to-place feel can be tested without also
  building a width/recipe picker in the same pass.
- **All three section-2 refusals are real code, not a description of
  intent:** off-board (outside the plate), overlap (checked per side —
  north and south are independent spans, proven by test 4), and the
  snap-to-410 discipline itself (test 1's hand-computed span).
- **Compatibility with the live driver, proven not assumed** (test 6):
  a placed parcel's state shape is a strict superset of what
  `ensure_parcel` already produces for a pinned one — the five original
  keys plus one new `placement` key. `_sync_parcels`/`econrules.py`
  need no change to keep reading a placed parcel exactly as they read a
  pinned one today.
- **`pid` generation** is `P1`, `P2`, ... — deterministic, sequential,
  and structurally disjoint from every pinned id (all letters), so a
  future collision between the two namespaces is impossible by
  construction, not just unlikely.

**What this half cannot prove, named plainly rather than glossed over:**
whether a live `GetHitResultUnderCursorByChannel` trace against the
board's ground plane actually reports `(x, y)` in this module's own
coordinate convention; whether a `BP_Parcel` spawned at runtime resolves
its mesh and collision the same way a pre-placed one does; and the feel
itself, which is not a headless question at all. All three need the
editor and, for the last one, the owner's own hand — this is the
"budget for what only a human hand can verify" the coordinator asked
this declaration to state outright, not the exception to the proof
discipline but the other half of it.

**The owner's own click on a spot with no lot in it is the acceptance
test.** Self-tests and read-back verification prove the machinery; that
click proves the feel — the same standing rule this whole session has
run on.

Editor work starts only after a wiring-window announcement with its own
scope and a grant issued against a checked PIE state, same serial
discipline as every shared-editor task tonight.
