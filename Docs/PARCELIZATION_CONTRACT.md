# Parcelization contract — architecture declaration

**STATUS: SUPERSEDED IN PART, 2026-09-01, by the amendment at the bottom
of this file ("Amendment: wave 1 redesigned for 'play from scratch'").
The original declaration below (§1-§4) is kept intact, not rewritten —
the amendment names exactly what it contradicts rather than silently
editing it. Read the amendment before wiring anything; it is now the
current word on §2 and §3 specifically. §1 and §4 stand, with §4
sharpened from "gated, unscoped" to a verified, itemized bake list.**

How the 14 pinned `TestCity` lots (`Content/Python/testcity_pins.py`)
become interactive `BP_Parcel` instances instead of inert
`StaticMeshActor`s. Written before any conversion code exists, matching
this project's declare-first precedent (`DISTRICT_PLACER_CONTRACT.md`,
`ECONOMY_TICK_CONTRACT.md`).

## 1. Which lots convert

**All 14, in two waves — 10 non-corner lots first, the 4 corner lots
second, gated on §4's catalogue extension.** Not a taste-based subset:
`testcity_pins.PINS` was already deliberately spread across five widths
and a wide tier/height range ("sampled evenly," "spans 370 uu to 7531
uu") specifically so the board has a real gradient to buy up through —
discarding part of that spread would waste already-done design work for
no mechanism-complexity saving (the conversion pattern is identical
per-lot; 14 instances of one pattern isn't costlier than 4). The
non-corner/corner split is real and technical, not arbitrary: the 10
plain lots convert with ZERO changes to the existing catalogue mechanism
(Phase A's `ResolveMesh`/`MeshByKey` already handles them exactly as
proven); the 4 corner lots need §4's key-space extension first. Wave 1
alone already gives more than one buyable parcel at varying price/tier —
enough for a meaningful phase E session on its own.

## 2. Identity reconciliation — two authorities, one boundary

**`testcity_pins.PINS` is the STARTING-identity authority. `citystate.json`
`parcels[pid]` is the CURRENT-identity authority. Once a parcel has an
entry in `citystate.json`, that entry wins — the pin is never consulted
again for that parcel's tier.**

- `RecipeId` and `WidthUU` are immutable — `econrules.tick()` never
  changes `rid` or `width`, only `tier` (`p['tier'] = int(p['tier']) + 1`,
  `citytick.py` unchanged). The pin's `rid`/`w` are correct forever; no
  reconciliation needed for those two fields, ever.
- `Tier` starts at the pin's declared tier but may have GROWN past it via
  `TIER_UP` events in a prior session. Reading the pin for `Tier` after
  the first tick would silently roll back growth — the exact "two
  truths drift" this project's culture exists to prevent.
- **Reconciliation point: a new pure function,
  `citytick.ensure_parcel(state, pid, rid, tier, width)`** — idempotent.
  If `pid` already exists in `state['parcels']`, returns `state`
  unchanged (existing entry, possibly grown, wins). If not, inserts
  `{rid, tier, width, owned: False, accum: 0.0}` seeded from the pin and
  returns the updated state. Exposed through the boundary as
  `CityTickBridge.city_ensure_parcel(state_json, pid, rid, tier, width)`,
  same JSON-in/JSON-out shape as the rest of the bridge.
- **Called once per parcel, at that parcel's OWN `BeginPlay`**, before
  `ResolveMesh` — `BP_Parcel` reads its own `RecipeId`/`Tier`/`WidthUU`
  (set from the pin at spawn time by `mk_testcity_builds.py`, see §3),
  calls `city_ensure_parcel` with those as the seed, then OVERWRITES its
  own `Tier` with whatever the (possibly-reconciled) state actually says
  before resolving its mesh. This makes each parcel self-healing
  regardless of load order or whether this is a fresh session or a
  resumed one — no separate "reconcile everything at level start" pass
  needed, and no risk of one parcel's reconciliation depending on
  another's having already run.

## 3. Conversion mechanics — `mk_testcity_builds.py` emits parcels

**The builder stops placing `StaticMeshActor`s and starts placing
`BP_Parcel` instances directly — not a one-time conversion pass, a
permanent change to what the builder does, so a rebuild can never undo
it.** Same spirit as `testcity_pins.py`'s own "declared first, wired
second" and this project's standing aversion to two code paths that can
drift (a builder that sometimes emits parcels and sometimes doesn't is
exactly that hazard).

- `spawn_actor_from_class(unreal.StaticMeshActor, ...)` becomes
  `spawn_actor_from_class(BP_Parcel_C, ...)` (class ref:
  `/Game/Stacktown/Runtime/BP_Parcel.BP_Parcel_C`).
- The builder sets the new actor's `RecipeId`/`Tier`/`WidthUU` from the
  pin (via `set_editor_property`, same three values `testcity_pins.
  identity()` already returns plus `w` from the pin) — it does NOT set a
  static mesh directly anymore. `ResolveMesh` (Phase A's existing,
  proven mechanism) does that at `BeginPlay`, now via the reconciled
  tier from §2.
- Labels: unchanged format, `'TC_Bld_%s_%s_t%d' % (key, rid, t)`, `t`
  always the PIN's tier (the builder has no other tier to use — it never
  reads `citystate.json`). This is what makes the label a valid, STABLE
  `pid`: same lot, same pin, same label, every rebuild, regardless of how
  far that parcel has actually grown. **Correction to
  `ECONOMY_TICK_CONTRACT.md`'s buy-verb section, found while designing
  this:** that section said `SelectedParcel.GetName()` for `pid` — wrong.
  `GetName()` is the engine's own auto-assigned internal identifier
  (`BP_Parcel_C_0`, `_1`, ...), sequential and NOT stable across a
  destroy-and-respawn rebuild. The ACTOR LABEL is what's deterministic
  (`GetActorLabel()`, matching `ActorTools.get_label`/`set_label` already
  used this session) — `pid` must be the label, not `GetName()`. Fixing
  that section to match. **Boundary note:** `GetActorLabel()` is
  editor-only — actor labels don't exist in a packaged build, the
  function is compiled out. That lands on the same side of the same line
  the Python bridge itself already sits on (`ECONOMY_TICK_CONTRACT.md`
  condition 2), so it costs nothing new for the chartered beta — but a
  packaged port would need its own stable-id story for `pid`, not this
  one (the standard shape: a plain instance-editable string on
  `BP_Parcel`, set by the builder).
- The existing destroy loop (`label.startswith(('TC_Mass', 'TC_Bld'))`)
  needs no change — it already matches `BP_Parcel` actors carrying these
  labels the same as it matched the old `StaticMeshActor`s, so rebuild
  idempotency is unaffected. Combined with §2's reconciliation, a rebuild
  destroys and respawns the ACTORS but never touches `citystate.json` —
  growth survives a rebuild for free.

## 4. The corner wrinkle — real, confirmed, not yet solved

**`DA_Catalogue.MeshByKey` is keyed `"{rid}_{tier}"` only — confirmed
directly in `Content/Python/mk_da_catalogue.py`
(`key_map['%s_%d' % (rid, t)] = asset_ref(name)`), no corner dimension
anywhere.** `ResolveMesh`'s Phase A lookup (`GetMeshByKey ->
Find(RecipeId_Tier)`) would therefore resolve a corner lot to its PLAIN
mesh, not the `_cL`/`_cR` variant `testcity_pins.require()` correctly
picks today — wrong geometry on all 4 corners the moment they're
converted under the current catalogue shape. This is exactly the kind of
thing worth finding on paper: converting a corner lot naively would look
fine in the log (`ResolveMesh` "succeeds," a mesh IS assigned) and wrong
only in a screenshot — the paper-tell-study family of bug, not caught by
any existing self-test.

**Not solved here — options recorded for whoever picks up wave 2:**
- Extend `MeshByKey`'s key space with a corner dimension (e.g.
  `"{rid}_{tier}_c"` for a generic corner entry, or per-side if the two
  sides ever need different meshes) and teach `mk_da_catalogue.py` to
  populate it for corner-eligible baked assets. Architecturally
  consistent with "one pin table serves both catalogues" — corners stay
  inside the swappable mechanism. More work: touches Phase A's catalogue
  population, not just parcelization.
  {leading candidate — keeps the reason the whole mechanism exists}
  intact for the 4 most visually prominent lots, not just the other 10.
- Bypass the catalogue for corner parcels (direct mesh reference, set by
  the builder or read once at `BeginPlay` outside `ResolveMesh`).
  Simpler, but corner lots then wouldn't re-resolve on a catalogue swap
  the way plain lots do — undermines the flagship/wooden-twin
  demonstration for exactly the 4 lots most likely to draw the eye.
  Recorded as the fallback, not the recommendation.

## Explicitly out of scope

Actually wiring any of this (waits on `ECONOMY_TICK_CONTRACT.md`
condition 1); solving §4 (recorded as open, not decided); a dynamic
demand model or anything about `econrules.py` itself (unchanged by this
doc, same as the tick contract's own scope line).

---

## Amendment: wave 1 redesigned for "play from scratch"

**Owner's direction, relayed 2026-09-01, reshaping wave 1 before it's
wired.** Judgment criteria for the next stretch are "selection & camera
feel" and "how the player will build their own city from scratch." FROM
SCRATCH is load-bearing: the first play session starts from an empty (or
near-empty) board — buildings materialize only through the player's buy
actions, not pre-standing from a rebuild. This section is the amended
wave-1 declaration, brought for review before any wiring, per instruction.
It does not silently edit §1-§4 above; it names what it supersedes.

### A0. New finding, more foundational than §4: the catalogue was never
populated for 13 of the 14 pins, and separately, 4 of the 14 are missing
real bakes for their lower growth tiers. Both verified live, not assumed.

Found while checking whether SW3 could safely fold into this window (its
own explicit instruction) as a corner lot under §4's already-flagged gap.
It goes deeper than §4 anticipated:

**Gap 1 — `MeshByKey` population.** Live-read from `DA_Catalogue` today:
6 rows, `vernacular_0`..`vernacular_5`, all at w1230, nothing else.
`mk_da_catalogue.py`'s `WID` dict (`{'vernacular': 1230.0}`) only ever
populated one recipe at one width — this was proven correct for Phase A
because Phase A only ever exercised one live parcel, `PARCEL_Demo0`,
which happens to be `vernacular`. The 14 pins span **nine** recipes
(`contemporary6`, `vernacular8`, `vernacular`, `contemporary`, `modern8`,
`vernacular7`, `modern3`, `contemporary4`, `tower`) and **four of those
nine repeat at more than one width** across different lots
(`vernacular8`: 820 & 1230; `vernacular`: 820 & 1640; `modern8`: 1230,
1640 & 2050; `tower`: 1230 & 1640). `MeshByKey`'s key is `"{rid}_{tier}"`
— no width component — so even growing `WID` to cover all nine recipes
can't serve two different widths of the same recipe at once under the
current key shape. This is the same limitation §4 named for corners
(no corner dimension in the key); it turns out the key is under-specified
on width too, for the same underlying reason. **Recommended fix: extend
the key to `"{rid}_{tier}_{width}"`, with a corner suffix for
corner-eligible entries, in one pass** rather than patching corners and
width separately — `ResolveMesh`'s key construction needs the matching
small update (format width, and corner side where applicable, into the
key it builds). This is data-population work for the catalogue DataAsset,
not new asset creation, for 10 of the 14 lots (see Gap 2) — but it does
touch a shared asset every consumer reads, so it's named here rather than
just run.

**Gap 2 — bake completeness across the full t0-through-declared-tier
range, not just the declared tier alone.** `require()`'s existing dry run
(§ under the original declaration, "14/14 green") only ever checked each
pin's DECLARED tier. Under "buy starts at t0, grows via tick," every pin
needs its FULL range baked at its own width (+corner), because a fresh
purchase is going to try to render t0 first, then t1, etc. Ran the same
check across the whole range, live, against the 567-asset catalogue:

    key   recipe          declared   range coverage
    NE1   vernacular8     t0         FULL
    NE2   vernacular      t0         FULL
    NW0   vernacular8     t0         FULL
    NW1   contemporary    t1         FULL
    NW2   modern8         t3         FULL
    SE1   modern8         t5         FULL
    SE2   modern3         t3         FULL
    SW0   contemporary4   t4         FULL
    SW1   vernacular      t5         FULL
    SW2   tower           t6         FULL
    NE0   contemporary6   t3         MISSING t0, t1, t2   (corner)
    NW3   vernacular7     t5         MISSING t0, t1, t2, t4   (corner)
    SE0   modern8         t2         MISSING t0, t1   (corner)
    SW3   tower           t6         MISSING t0, t1, t2, t3, t4, t5   (corner)

**Every non-corner lot is fully baked across its entire growth range,
zero new assets needed. Every corner lot has a real gap in its lower
tiers — including SW3**, whose repin only ever secured its DECLARED
(top) tier; the corner-specific bake was "on demand for whatever an
earlier draw asked for" (testcity_pins.py's own words, about the original
four), and under the OLD model (appears immediately at declared tier)
nothing ever needed the lower corner tiers to exist. "From scratch" is
what exposes this — it's a real consequence of the redesign, not a
mistake in the SW3 repin work. Concretely: SW3 seeded at tier 0 (see A2)
would try to resolve `SM_Bld_tower_t0_w1640_d1500_cR` on purchase, which
does not exist. That is NOT the graceful "growth blocked, stays at
current tier" case `econrules.tier_up_allowed()` already handles loudly
— it's an unresolved mesh at the FIRST resolution, a code path nothing
has exercised yet. Whether `ResolveMesh` degrades gracefully or not from
an empty `Find()` is unverified and shouldn't be found out live on the
most visually prominent lot on the board.

**Recommendation, flowing from this data:** scope THIS window's wave 1 to
the 10 non-corner lots — they are fully ready for the complete
from-scratch experience the moment Gap 1's data-population fix lands, no
new bakes required. For SW3 specifically, two honest options, not decided
here:
  - **(a, suggested) Place it as a fixed landmark, not part of the
    buyable/from-scratch pool this session** — spawn already-owned, at
    its declared tier, using the one asset that's actually confirmed
    good. This still satisfies "SW3 tower placement... folded into this
    window" literally (it goes into the level, correctly, this window) —
    it just doesn't pretend to support growth it can't back up yet. Given
    it's the tallest building on the board, a fixed anchor while the rest
    of the board demonstrates "build from scratch" isn't a downgrade, it
    may read better.
  - **(b) Bake the missing 6 corner variants** (`tower_t0` through `t5`
    at `w1640_d1500_cR`) this window, then SW3 joins the buyable pool
    fully capable. Real new-asset work, scoped and small (mirrors the
    plain w1640 set that already exists t0-t6 in full), but it's a bake
    turnaround this doc can't schedule for the coordinator.
  - The other three corners (NE0, NW3, SE0) stay deferred to wave 2 as
    §1/§4 already scoped — now with a verified, itemized list (9 assets:
    NE0 needs 3, NW3 needs 4, SE0 needs 2) instead of an open gate.

### A1. Correction to §2: the BeginPlay-time reconciliation call is the
same dead mechanism condition 1 already proved impossible.

§2 says `BP_Parcel` calls `city_ensure_parcel` itself, per-parcel, at its
own `BeginPlay`. That's a Blueprint-to-Python direct call — the exact
shape `ECONOMY_TICK_CONTRACT.md`'s original condition 1 spent two false
starts proving permanently unsatisfiable in this project (Python
UFunctions never reach Blueprint's action database; "Execute Python
Script" is editor-utility-blueprint-only). §2 was written before that was
known. **Fix: reconciliation moves into the same Python-side driver that
already does the economy tick (option b'), not a per-parcel Blueprint
call.** This session verified live, during PIE, that the driver CAN
enumerate individual parcel actors — not just the singleton GameInstance
— via `unreal.GameplayStatics.get_all_actors_of_class(get_game_world(),
BP_Parcel_C)`, and can both read and write their Blueprint variables
directly via `get_editor_property`/`set_editor_property` (tested against
`PARCEL_Demo0`'s `Tier`: read 0, wrote 2, confirmed, restored). This was
the load-bearing risk for this whole amendment and it's now proven, not
assumed.

### A2. Correction to §2: seeding `Tier` from the pin's declared value
contradicts "appears at t0 on purchase, then grows via the tick."

As written, `ensure_parcel(state, pid, rid, tier, width)` seeds a new
parcel's live `tier` from the pin's DECLARED tier — e.g. SW2 would be
seeded at tier 6 immediately, even unowned. Combined with a
purchase-reveals-the-current-tier design, buying SW2 would instantly show
the full 75 m tower, not start small and grow — directly against the
owner's own words. **Fix: `ensure_parcel` seeds `tier=0` always,
regardless of the pin's declared tier.** The pin's `tier` field doesn't
disappear — it keeps meaning what §1's massing-range paragraph already
uses it for (the intended eventual massing for that lot, and the bar
`require()`'s existence check verifies against) — it just stops being a
live-state seed. `econrules.buy()` is unchanged by this (it already only
sets `owned=True` and resets `accum`, never touches `tier` — confirmed by
reading it, not assumed). Considered and rejected: recording the pin's
tier as a live "growth ceiling" enforced by `tick()` — real scope
creep beyond what shipping "from scratch" needs, touches `econrules.py`
(out of scope per both contracts' own scope lines), and nothing about
"from scratch" actually asked for a ceiling — growth today already stops
on its own the moment a tier's asset isn't baked/catalogued.

### A3. Correction to §3: the builder no longer sets the pinned mesh's
tier as the spawn-time state.

§3's builder sets `RecipeId`/`Tier`/`WidthUU` from the pin at spawn,
`Tier` being the pin's declared value — under A2 that's now wrong.
**Fix: `mk_testcity_builds.py` still sets `RecipeId`/`WidthUU` from the
pin unchanged (those two are correct, immutable identity, per §2's
original and still-correct reasoning) but sets `Tier=0` and `Owned=False`
explicitly at spawn**, rather than the pin's declared tier. This is the
whole mechanical difference between "board arrives built" and "board
arrives empty" — one field's source changes, nothing else about the
builder's role does. The label scheme, the destroy loop, and the
rebuild-idempotency argument in §3 are all unaffected and still correct.

### A4. New: the empty-lot placeholder.

Must be as selectable/traceable as a built parcel — real collision — since
selection & camera feel is the thing being judged, and most of the board
starts in this state. Must be visually distinct from a built parcel (the
player needs to see what's buyable) without attempting real "look" design
— that's explicitly not this window's job. **Recommended: a stock engine
primitive (e.g. `/Engine/BasicShapes/Plane` or `Cube`), scaled to the
lot's own footprint (`WidthUU` already carried on the actor, depth from
the same `citylayout` constant the builder already uses), assigned the
same way `ResolveMesh` already assigns any other mesh** — no new asset
authoring, no new bake, matching the "selection feedback > HUD
completeness > tuning" priority order below. **Naming the seam, not
answering it**: direction B's B2 already parked a "white proposed
-building block" idea for the same conceptual slot (an unbuilt lot's
look). Don't build that version here — this placeholder is functional
scaffolding for the beta twin specifically, not a look decision, and each
product should get to answer "what does an empty lot look like" in its
own material language later. [[stacktown-direction-b]] is the pointer for
whoever picks that up.

### A5. New: `ResolveMesh` becomes state-aware; reaction is Blueprint
-native, not Python-invoked.

`ResolveMesh` gates on `Owned` first: not owned → the A4 placeholder,
sized to `WidthUU`; owned → the existing `MeshByKey` lookup, unchanged
mechanism, now keyed by the extended (width [+corner]) key from A0.
Small, surgical change to an already-proven function.

**Reaction mechanism, deliberately chosen to stay inside proven
capability:** the driver pushes typed `Owned`/`Tier` values onto each
parcel actor (A1/A6), but this session has only proven Python can
read/write actor PROPERTIES during PIE, not call a Blueprint FUNCTION on
a live instance — that's a different, unproven capability, and there's no
need to risk it. **`BP_Parcel`'s own `EventTick` (confirmed empty this
session) does a cheap change-check** against two new cached variables
(`_LastOwned`/`_LastTier`) and calls `ResolveMesh` again only when either
differs from last tick — reacts within one frame of the driver's push
(far tighter than the 2 s economy-tick interval, which matters for how
"live" a purchase feels), costs nothing on the vastly more common
no-change frame, and uses only the already-proven Python↔Blueprint
surface (property read/write), not a new one.

### A6. New: the driver's per-tick parcel responsibility.

Folds into the SAME throttled pass `city_tick` already runs on (no new
timer): each tick, enumerate `BP_Parcel` actors via
`GameplayStatics.get_all_actors_of_class`; for any actor not yet in
`citystate.json['parcels']`, call `ensure_parcel` seeded from ITS OWN
`RecipeId`/`WidthUU` vars with `tier=0` (A2); for every tracked actor,
push `state['parcels'][pid]['owned']`/`['tier']` onto the actor (skip the
write when unchanged, cheap enough not to bother measuring at 14 actors).
**Recommend the very first call after PIE start not be throttled** — run
it immediately once, then fall into the normal 2 s cadence — so there's
no up-to-2-s window where a just-loaded board shows authored defaults
before the driver's first reconciliation. Free to add, avoids a cosmetic
but avoidable wrong-first-frame flash on exactly the moment (session
start) selection & camera feel is first being judged.

### A7. Buy verb: mechanically unchanged; what's new is that its effect
is visible for the first time.

The `BuyRequestPID` channel, `econrules.buy()`, the whole wiring
`ECONOMY_TICK_CONTRACT.md` already declared and proved — none of it
changes. What's new is downstream: until now every parcel was already
"owned"-equivalent by being pre-built, so buying didn't change anything
visually. A4-A6 are what make that channel's effect observable for the
first time — this is completing a mechanism that was already built, not
inventing a new one. `ECONOMY_TICK_CONTRACT.md` needs no rewrite; its
buy-verb section stays accurate as written. It should gain one
cross-reference to A6 (the driver's per-tick responsibilities grew), not
a rewrite.

### A8. `require()` itself: no change recommended.

It still checks the pin's DECLARED tier is baked — keep that bar. It's
already satisfied (14/14, unchanged by this amendment) and it's a useful
forward guarantee: if a lot is ever grown all the way to its declared
massing, the asset needs to already exist. A0's Gap-2 audit (full
t0-through-declared-tier, not just the declared tier) is a stricter,
different check that belongs alongside `require()`, not instead of it —
worth promoting from a scratchpad script to a standing one (e.g. next to
`testcity_pins.py`'s own self-test) rather than a one-off, since Gap 2 is
exactly the class of thing that stays invisible until a screenshot.

### Priority order, restated for this window specifically

Owner's own ordering: **selection feedback > HUD completeness >
tuning.** Concretely: A4's placeholder is functional, not designed; A0's
catalogue fix is scoped to exactly what the 10 non-corner lots need, not
an exhaustive repopulation; economy numbers stay rough scaffolding, same
as `ECONOMY_TICK_CONTRACT.md` already chose. Don't spend this window's
budget on any of those beyond what A1-A6 need to work correctly.

### What this amendment contradicts — scannable list

- §2, "called once per parcel at its own `BeginPlay`" → **A1**: moves to
  the Python driver, per-tick, not a per-parcel Blueprint call.
- §2, `ensure_parcel` seeds `tier` from the pin's declared value → **A2**:
  seeds `tier=0` always.
- §3, builder sets `Tier` from the pin at spawn → **A3**: builder sets
  `Tier=0`, `Owned=False` explicitly; `RecipeId`/`WidthUU` unchanged.
- §1/§4, "10 non-corner lots need zero catalogue changes, already proven"
  → **A0**: only ever proven for one recipe (`vernacular`) via
  `PARCEL_Demo0`; needs the same data-population fix as everything else,
  just no new bakes.
- §4, "corner gap, gated on wave 2, unscoped" → **A0**: sharpened to a
  verified, itemized 9-asset list (NE0, NW3, SE0) plus SW3's own 6-asset
  gap, with a named decision point (landmark vs. bake) for SW3
  specifically.

### Sequencing — needs review before any wiring starts

Per instruction, nothing in A1-A8 gets built until this comes back
reviewed. Specific decisions that need a yes/no, not just a read:
1. A2's semantic change (pin's tier stops being a live-state seed).
2. SW3: landmark-not-buyable (a) vs. bake the missing 6 (b) vs. defer it
   to wave 2 with the other three corners after all.
3. A0's key-space extension approach (width [+corner] folded into one
   key change) — and whether the other three corners' now-itemized
   9-asset list should get queued for bake now even though wave 2 isn't
   starting, so it's ready when it is.

### STATUS UPDATE 2026-09-01: A1-A7 wired and live-verified; A0's key
space extension shipped WIDER than declared above; one new bug found and
fixed mid-wire, not by re-reading this doc but by testing the buy verb
live.

All three review points came back approved (coordinator for #1/#3, the
owner directly for #2: bake SW3's growth stages, not the landmark
option). Wired in one window: `BP_Parcel` gained `Owned`/`CornerSide`/
`LastOwned`/`LastTier`; `ResolveMesh` is state-aware (empty-lot
placeholder vs. catalogue lookup) and `EventTick` does the change-detect
-then-reresolve dance from A5, both confirmed correct via raw graph
inspection, not just the (sometimes lossy) DSL summary. `mk_testcity_builds.py`
now spawns `BP_Parcel` directly (the actual §3 conversion — confirmed
this session it had NEVER been done; the file still spawned plain
`StaticMeshActor`s until this rewrite, contradicting an earlier
summary that assumed it already had). `init_unreal.py`'s driver gained
`_sync_parcels` (A6), proven live: discovers all 15 parcel actors,
registers new ones via `ensure_parcel` (ALWAYS tier=0, confirmed via a
live buy that grew a fresh purchase from 0 up, never starting anywhere
else), pushes Owned/Tier every throttled tick.

**Real bug found live, not anticipated in A0:** catalogue population was
scoped to "t0 through each pin's declared tier," reasoning growth
wouldn't exceed it in one session. A live buy on NE1 (pin declares t0)
grew it to tier 1 within one throttled tick — `econrules.tick()` has no
concept of a pin's declared tier as a ceiling, nothing asked it to.
`SM_Bld_vernacular8_t1_w820` existed on disk (6 tiers baked, both
widths); it just wasn't catalogued. `Map|Find` returned nothing,
`SetStaticMesh` silently cleared the mesh — caught by testing the buy
verb, not by re-deriving the design. Fixed: `mk_da_catalogue.py` now
populates each pinned recipe's FULL declared tier range at its pinned
width(s), not just up to the pin's own tier. Re-verified live after the
fix: the same parcel grew to tier 5 and resolved correctly at every
step. 67 rows now live in `DA_Catalogue` (up from the original 6).

**A second real bug, unrelated to A0-A8, found trying to get a visual
check:** `/Engine/BasicShapes/Cube`'s own default material is
`WorldGridMaterial`, not opaque — the placeholder was completely
invisible despite every property (mesh, transform, scale, visibility)
reading back correct. Fixed with an explicit `SetMaterial` to
`/Engine/BasicShapes/BasicShapeMaterial`. Full story, including the
`CaptureViewport`/PIE-world tooling limitation that made this harder to
confirm than it should have been, is in `HANDOFF.md` §5.

**Defensive addition, 2026-09-01, after the report above:** `ResolveMesh`'s
owned-branch now wraps the catalogue lookup in `Utilities|IsValid` — a
miss (uncatalogued key) leaves the mesh/scale/location exactly as they
were rather than clearing to nothing. Prompted by sharpening the
already-known wave-2 corner gap: NE0/NW3/SE0 are each missing their OWN
t0 corner bake (confirmed via the full-range audit), so buying any of
them today would hit this exact failure at the very first resolution,
not eventually. This doesn't make those three correct — they'd still
show the empty-lot placeholder forever rather than growing — but it
means a purchase on an uncatalogued lot degrades to "visibly unchanged"
instead of "building vanishes," which is the safer failure for a first
play session. Same fix protects SW3 too, for the window between its
bakes landing and `mk_da_catalogue.py` being rerun.

**Not yet done:** the 6 SW3 corner-growth bakes (offline pre-gate passed,
control tier matched the known-good asset exactly; live bake commands
were blocked by this session's own permission classifier and need the
owner's direct sign-off, not a peer relay — asked, not yet answered).
`require()`/self-test extension: not needed beyond what already exists
(A8's reasoning held — `require()` itself needed no change). **True
visual acceptance — someone actually looking at a rendered PIE frame —
has NOT happened.** Everything above is verified at the data level
(property reads, `get_actor_bounds`, live growth across real ticks) to a
degree this session had time to be thorough about, but data-correct and
render-correct are provably different claims (see the WorldGridMaterial
bug, which was invisible to every property check that mattered). The
owner's own stated top priority — selection & camera feel — is
inherently a visual judgment this session could not close out alone.

## Layout note, 2026-09-01 — a lot pad overlaps a painted road strip

Found during the owner's own play session, flagged without alarm
("maybe not a problem since we're developing a road building tool").
Recorded here as a layout fact for that future work to inherit as a
known condition, not rediscover as a bug — **not fixed tonight, on
purpose**, per the same disposition.

Not root-caused to a specific constant this session — that would need
its own look — but the STRUCTURAL reason is already visible from how the
two systems are built: a lot's footprint comes from `citylayout.py`'s
`blocks()`/`lots()` (block envelopes seeded from `HALF`, partitioned
along the arterial frontage), while the road strip is painted by a
separate system (`city.py`'s `ROAD_W`/`WALK_W` corridor). Nothing
cross-validates the two — `HALF` is presumably meant to leave exactly
enough clearance for the road-plus-walkway corridor, but nothing asserts
`HALF == ROAD_W/2 + WALK_W` (or whatever the intended relationship is),
so a drift between them would produce exactly this symptom: a pad
correct by its own layout math, encroaching on a road correct by its
own. Worth checking that specific relationship first if this becomes a
real problem instead of an accepted one — see
`Docs/ROADS_AS_MECHANIC.md` §3.1, which already names `citylayout.py`'s
hard-coded grid as something drawn roads will displace as a source of
truth regardless.

## Pool doctrine, 2026-09-02 — a parcel actor is pooled, not spawned

**A `BP_Parcel` instance is now a pooled, pre-placed object. Placement
ACTIVATES one; reset DEACTIVATES it back. Nothing in this project spawns
a `BP_Parcel` at runtime, and nothing should — the capability doesn't
exist to spawn one.** This amends §3/A3 above in one specific way: the
builder (`mk_testcity_builds.py`) now emits TWO kinds of `BP_Parcel`
content, not one — the 14 pinned lots exactly as A3 already describes,
PLUS a fixed-size pool of dormant actors (`placement.POOL_SIZE`, 30 as
of this writing) with no identity, hidden, collision off, labelled
`POOL_00`..`POOL_29`.

**Why, found live, not designed in advance:** `PLACEMENT_GRID.md`'s v0
(free placement over the pinned board) was built assuming a runtime
spawn call existed, the same way `mk_testcity_builds.py` already spawns
the 14 pins at editor time via `EditorActorSubsystem.
spawn_actor_from_class`. The owner's first live click proved that
assumption wrong: `unreal.World` has no spawn method in this build,
`GameplayStatics` has none for generic actors (only decal/sound/emitter/
dialogue), and the only `spawn_actor_from_class` in the entire `unreal`
Python module lives on `EditorActorSubsystem`/`EditorLevelLibrary` —
both editor-world only, the same world-split trap `_sync_parcels`
already has to avoid (`HANDOFF.md` §5). Confirmed exhaustively (a
module-wide scan for every class exposing anything named `spawn_actor*`)
before landing on the pool, not assumed after one failed guess. A
Blueprint-side reverse-request channel (Python validates, a Blueprint
already ticking in the game world calls the native Spawn-Actor-From-
-Class node) was checked too — the node itself IS placeable via the DSL
(`Game|SpawnActorfromClass`, confirmed via `get_node_type_pins`) — but
was passed over for the pool: every pool operation (`set_actor_location_
and_rotation`, property writes, `set_actor_hidden_in_game`, `set_actor_
enable_collision`) was already proven live this session, where the
reverse-channel path would have been new DSL-graph surface with its own
unresolved ordering risk (a plain, non-deferred spawn runs `BeginPlay`
before a `then`-branch could set identity).

**The mechanics:**
- `placement.POOL_SIZE` (currently 30) is the ONE authority for pool
  size — declared in `placement.py` itself, with the derivation (v0's
  physical max at its one fixed width, `floor(12100/820)=14` per side x
  2 sides = 28, plus 2 spare) written where the constant lives.
  `mk_testcity_builds.py` imports it rather than holding a second copy.
- `placement.place()` refuses once `POOL_SIZE` placed lots already exist
  in `citystate.json` (counted by the `'placement'` key, independent of
  the live pool) — the count check is pure Python, no live-actor
  visibility needed, and in practice the OVERLAP/off-board geometry
  checks refuse first (~28 max), making the count check a backstop for
  when geometry changes (a second width, more frontage) outpaces it.
- Activation (`init_unreal.py`'s placement channel): finds the lowest-
  numbered live actor labelled `POOL_*`, sets location/rotation →
  identity (`RecipeId`/`WidthUU`/`Tier=0`/`Owned=False`/`CornerSide`) →
  label (the `pid`) → hidden off → collision on, in that order, so the
  actor is never visible or solid while half-configured. The actor's
  own `EventTick` change-detection (A5) is what actually resolves the
  placeholder mesh — activation is not a special case of that mechanism,
  it's the same one every tier-up already uses.
- Deactivation (the reset channel): every live actor whose label is `P`
  + digits only (a placed `pid`, by `_next_pid`'s own construction —
  pinned labels are always a compass prefix + digit, e.g. `SW2`, never
  bare `P`) gets hidden, collision off, and relabelled to a pool slot
  number not already in use by another dormant actor.
- Exhaustion (no dormant actor found for an accepted placement) and
  activation/deactivation count mismatches both log a warning AND show
  the player an on-screen message — loud on both sides, not just the
  log, after the first live click's silent refusal read as "nothing
  happens."

**Revisit the moment roads/growth adds frontage or a second placeable
width** — the whole cap, and the assumption that one fixed-size pool
covers v0's entire legal area, is provably a v0 artifact the day either
changes.

### Extension, 2026-09-02 — empty mode: the 14 pins join the same pool

**A pinned lot is now ALSO a pooled, pre-placed object — not a second
mechanism alongside the placement pool, the same one.** The owner's own
four-decision brief (`[[stacktown-roads-mechanic]]`) named both a
starter-preset start and an empty-board start; this is that decision,
realized with zero new activation machinery. `GameInstance.EmptyStart`
(bool, instance-editable, CDO default `TRUE`) gates whether the 14 pins
activate at session start — `false` shows the board every session before
this one ran on; `true` opens fully empty, the placement pool the only
way anything appears.

**Why the pins are PRE-POSITIONED at build time rather than positioned
by the driver at reactivation, and why that's not a shortcut:**
`mk_testcity_builds.py`'s own street rhythm (randomized gap/setback,
seeded, advancing by each candidate's REAL baked bounding box —
`built_w`, read via `sm.get_bounding_box()`) is EDITOR-ONLY math; the
driver has no equivalent read. Two honest options existed: duplicate
that math in Python (two copies of one algorithm, guaranteed to drift
the first time either one changes without the other), or let the
builder — which already computes the correct rhythm-adjusted transform
for every other purpose — bake that transform into the dormant actor's
initial position, leaving ONLY identity/visibility/collision for
reactivation to decide. The second option is what shipped: each pin's
dormant actor is spawned at build time at its exact rhythm-adjusted
transform, labelled `POOL_PIN_<key>` (e.g. `POOL_PIN_NE0`) for that
SPECIFIC key, hidden, non-colliding, no identity. **Do not "simplify"
this into computing position at reactivation time** — that reintroduces
the exact two-copies-of-one-algorithm hazard this design exists to
avoid, for a rhythm that was never state, only ever build-time
placement.

**Reactivation is a direct label lookup, not `plan_reactivation`'s
sorted allocation.** A placed lot can claim ANY dormant pool slot
(`POOL_00`..`POOL_29`, fungible); a pin cannot — it has exactly ONE
predetermined slot, the one build labelled for it. `init_unreal.py`'s
`_reactivate_pinned_parcels` therefore just checks "does `POOL_PIN_<key>`
exist" per pin and activates it (identity from `testcity_pins` directly
— `RecipeId`/`WidthUU`/`Tier=0`/`Owned=False`/`CornerSide` from
`citylayout.cross_street_end` — then label → hidden off → collision on,
same order as placement activation), never allocates. `POOL_PIN_*`
labels are excluded everywhere the placement pool searches for a
claimable slot (the click-driven activation, the reset-deactivation
loop's `used_nums` count) — a pin's reserved slot is never fungible with
the general 30, in either direction.

**The overlap scan now checks pinned spans too.** Once pins and
placements share a pool, a player placing across a pinned pad became
reachable for the first time — `placement.PINNED_SPANS` (computed once
from `citylayout.blocks()`/`lots()`, independent of whether any pin is
currently activated) is checked in `resolve_click` before the placed-lot
loop, with a distinct "crosses a pinned lot" message. This is unrelated
to `EmptyStart`: the pins' GROUND is reserved even when they're not
currently shown, because `EmptyStart` is a per-session display choice,
not a redefinition of where the starter city's lots physically sit.
