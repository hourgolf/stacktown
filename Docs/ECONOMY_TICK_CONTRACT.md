# Economy tick contract — architecture declaration

**STATUS: ARCHITECTURE IS (b'), CONFIRMED AND WIRED 2026-09-01. Condition
1 as originally written is CLOSED NEGATIVELY — see "History" below for
why, and read it before touching this area, because the failure mode is
non-obvious and already cost two restart cycles.**

This is the declare-before-wiring contract for how `econrules.py` drives
the live `CityTick` at runtime, per `Docs/BETA_LANE.md` phase C.

## History (read this before assuming Blueprint can call Python here)

The original decision was: a `CityTick` Blueprint event calls a
Python-defined, `@unreal.uclass()`-decorated Blueprint-callable function
wrapping `econrules.tick()`/`buy()` directly. Two restructure attempts
(`unreal.Object` → `unreal.BlueprintFunctionLibrary`; adding
`meta=dict(BlueprintCallable=True)`) were tried across two separate
editor restarts to make the resulting node discoverable in Blueprint's
own node search, because this session's own `find_node_types`/
`create_node` tooling could never find it. The owner then checked the
REAL Blueprint palette directly and reported success — "city tick"
visible under Call Function, top hit — and condition 1 was declared
closed on that report.

**It was a false positive.** The owner's second, more careful check
(Context Sensitive off, bare "city" search, full result list read)
found the truth: "City Tick" was categorized under **BP Parcel**, not
under any economy-related category — it was `BP_Parcel`'s own legacy
phase-A tutorial event (`Docs/RUNTIME_SLICE.md`'s Level-float→Tier
round-off, a NAME COLLISION with the wrapper this contract was trying to
place, not the wrapper itself). No City Load, City Buy, or City Reset
existed anywhere in the palette. **This session's `find_node_types` was
right all along** — it correctly found nothing, because there was
nothing to find. The name collision sat exactly where the economy's own
vocabulary lives, which is precisely why it fooled a name-only check.

**Confirmed, now on solid ground:** Python-defined
`BlueprintFunctionLibrary` UFunctions do not reach Blueprint's action
database in this project's setup — both restructure attempts were
chasing a symptom that was never the cause. The documented fallback,
"Execute Python Script," is ALSO dead for this purpose: it is an
editor-utility-blueprint-only node, unavailable in Actor/Pawn graphs
(consistent with the owner finding nothing for "execute python" in
`BP_Parcel` either). **Condition 1, as the original contract defined it
— a Blueprint node calling into Python — cannot be satisfied in this
project. This is a closed, negative result, not an open question.**

## The decision: option (b') — in-process Python driver, zero BP calls

`Content/Python/init_unreal.py` registers a
`unreal.register_slate_post_tick_callback` at editor startup. Whenever a
PIE world exists, the callback reads `CityStateJSON` off the live
`GameInstance`, runs `citytick.py`/`econrules.py`, writes the result
back — entirely in-process, running automatically whenever the editor
runs (the owner presses Play and it just ticks; no agent, no external
process — this is NOT the earlier-rejected "Python drives BP state from
the editor side," which meant an external process pushing ticks in and
would have failed self-containment the same way). Blueprint makes NO
call into Python at all, for tick OR buy: BP's whole job is reading
`CityStateJSON` (display) and writing one string, `BuyRequestPID` (the
buy verb) — both ordinary Blueprint variable operations, zero
cross-language calls, zero node-placement risk anywhere in the design.

**Why (b') over reimplementing the arithmetic in Blueprint (option a):**
single authority preserved — `econrules.py` stays the one executed
logic, zero duplication-drift risk, matching the reasoning that ranked
(a) worst from the very first version of this argument (`recipes.py`'s
ladder logic and the baked-asset existence check would ALSO need
re-deriving in BP, not just price/rent). (b')'s hard technical risk —
can Python find and mutate PIE-live state — is proven with evidence
(below), not assumed; (a)'s duplication cost is unchanged and ongoing
(every future econrules.py tuning needs both sides updated and
re-verified).

**The one genuinely new mechanism — tested live before committing, not
assumed:** can Python find the ACTIVE PIE world and read/write a
Blueprint property on its `GameInstance`, from code running in the same
process a Slate callback would run in. Two real dead ends hit and
reported honestly first: `UnrealEditorSubsystem.get_editor_world()`
returns `None` during PIE (this broke even `rung.sh`'s own `_guard.py`,
which calls exactly that — had to bypass by calling
`Tools/measure/uepy.py` directly instead of through `rung.sh` for any
PIE-time Python test); `EditorActorSubsystem.get_all_level_actors()`
also returned empty via bare Python during PIE (unlike through the MCP
bridge toolset, which clearly has its own undocumented PIE-context
resolution that raw Python doesn't get for free). **Found via
introspecting the class, not guessing further:**
`UnrealEditorSubsystem.get_game_world()` — a separate method from
`get_editor_world()` — works completely. Full proof, verbatim:

    get_game_world(): /Game/Maps/UEDPIE_0_TestCity.TestCity
    GameplayStatics.get_game_instance(that world): <...BP_StacktownGameInstance_C_0...>
    CityStateJSON before: ''
    CityStateJSON after write: 'PROBE_WRITE_OK'
    ROUND TRIP WORKS: True

One more snag on the way, also diagnosed to its real cause rather than
blamed on PIE: `set_editor_property` initially refused with "cannot be
edited on instances" — not a PIE restriction, but that `add_variable`
does not mark a new Blueprint variable instance-editable by default.
Fixed with `set_variable_instance_editable`; recompiled WHILE PIE was
still running (hot-reloaded correctly, no restart needed for a variable
-flag change).

## Driver hygiene (designed, not assumed)

- **Double-registration guard.** `init_unreal.py` can be imported more
  than once per editor process (confirmed: repeated manual imports via
  `rung.sh` this session). A bare module-level flag would NOT survive
  this — `_guard.py` purges every cached module that came from this
  project on each `rung.sh` run, which resets a module's own namespace.
  The guard therefore lives as an attribute on the `unreal` module
  itself (native/compiled, never purged by that logic):
  `unreal._stacktown_driver_registered`. Proven: re-running the
  registration script after the driver was already live correctly logged
  "already registered, skipping" and did not double the heartbeat rate.
- **Clean no-op with no game world.** The callback runs on every editor
  frame regardless of PIE state (Slate ticks continuously) — returns
  immediately if `get_game_world()` is `None`.
- **Exceptions caught and logged ONCE per incident class**, never
  allowed to spam every tick or silently kill the callback (an
  unregistered exception inside a Slate callback would end it with no
  further warning to anyone).
- **Tick cadence accumulated Python-side** using real elapsed seconds
  (`time.time()`), not frame count — stable regardless of editor
  framerate. 2.0s between economy ticks.
- **Proven in isolation before economy logic rode it** (this contract's
  own condition, honored): a trivial heartbeat (log line only, touches
  no state) was registered and confirmed firing on a clean ~5s cadence,
  10 consecutive beats, before the real tick/buy logic was ever deployed
  on the same callback.

## Buy verb — simplified under (b')

No hand-placed node, no cross-language call at all. Blueprint's entire
job: on `WasInputKeyJustPressed "B"` (matching the existing E/Q
edge-triggered pattern in `EventTick`), check `IsValid(SelectedParcel)`
— nothing selected is a normal case, prints its own message — then write
`SelectedParcel.GetActorLabel()` to `GameInstance.BuyRequestPID`. The
driver consumes and clears the string on its next tick and logs
`ok`/`reason` itself (`unreal.log`/`log_warning`), the same pattern
`city_tick`'s events already used before this rewrite.

**WIRED 2026-09-01 — this section was declared, not built, until now.**
Checking `BP_LensRig` while preparing the owner's first session found the
"B" key (and, separately, any player-facing reset trigger) had never
actually been added to `EventTick` — same class of gap as
`mk_testcity_builds.py` never really emitting `BP_Parcel` (see
`PARCELIZATION_CONTRACT.md`'s amendment): declared here, not checked
against the live graph until it mattered. Two corrections made while
wiring it for real: `GetActorLabel()` isn't Blueprint-callable at all
(editor-only, matches the existing HANDOFF §5 note on it) —
`Utilities|GetDisplayName(Object)` is the Blueprint-reachable equivalent
and returns the same value in an editor/PIE build (falls back to
`GetName()` only in a packaged build, which is already out of scope per
condition 2). And `WasInputKeyJustPressed "N"` was added alongside "B",
same pattern, writing `GameInstance.ResetRequested = true` — the reset
channel had the identical "designed, never keyed" gap.

## State home and schema (unchanged by the b'/a-vs-b' decision)

`BP_StacktownGameInstance` — the same pattern as `ActiveCatalogue`
(`Docs/BETA_LANE.md` phase A: the one swappable pointer). State lives as
ONE opaque JSON string, `CityStateJSON`, never decomposed into typed BP
variables — Blueprint reads/writes the whole string, never interprets
its shape; only Python ever parses or constructs it. `BuyRequestPID`
(String) is the only other GameInstance variable this contract adds.

**Parcel identity:** the `BP_Parcel` actor's own LABEL
(`GetActorLabel()` — explicitly not `GetName()`, the engine's unstable
auto-assigned identifier; corrected in this doc and in
`PARCELIZATION_CONTRACT.md` §3 after being caught mid-design). Declared
seam: identity migrates to `DISTRICT_PLACER_CONTRACT.md`'s
`(block_name, lot_ordinal)` scheme WHEN that placer lands — `pid` stays
an opaque key either way.

**Persistence — owner's direct word, confirmed twice: persist across
sessions, with a loud reset.** `Content/Python/citystate.json`
(sibling to `econrules.json`, live state instead of constants) —
written after every tick/buy, read once to seed `CityStateJSON` when a
GameInstance first has none. Survives PIE stop/start AND editor restarts
via the same disk-file pattern `econrules.py` already uses for
constants. `city_reset()` wipes and reseeds from `money_start`, loud in
the log by design (the owner's condition for accepting persistence at
all).

**Known-answer self-tests:** `Content/Python/citytick.py`'s own
`__main__` block, 6/6 pass headless (mirrors `econrules.py`'s 7/7
pattern) — a fresh state ticked and bought against matches hand
-computed values, survives a `citystate.json` round-trip unchanged, and
one `GROWTH_BLOCKED` case survives the same round-trip.

## HUD — still an open design question, unchanged by b'/a

Blueprint still can't cheaply pull individual fields (`money`, `demand`)
out of `CityStateJSON` for a pretty print without its own JSON parsing
(unconfirmed whether this project's Blueprint environment has that —
not worth resolving for an interim HUD). First pass: print the raw
state JSON directly wherever a display is needed — ugly, in keeping
with the interim HUD's existing character (`ParcelHUD`'s prints aren't
pretty either), satisfies "money + demand on the HUD" literally with
zero parsing. Parcel "state" beyond identity (phase B's own HUD ask —
`owned`/`accum`, which live only in `CityStateJSON.parcels[pid]`, never
duplicated onto `BP_Parcel`) needs the same raw-JSON treatment for now:
`SelectTick`'s success branch prints whatever chunk of the state string
is relevant, not a parsed/formatted field. Pretty-printing is later,
optional polish once JSON-parsing availability is actually checked.

## Parcelization wave 1 — wired under (b'), 2026-09-01

Done, not just designed. `ensure_parcel(state, pid, rid, width)` (the
`tier` parameter dropped — it always seeds 0 now, see
`PARCELIZATION_CONTRACT.md`'s amendment A2) runs Python-side inside the
same driver callback, via a new `_sync_parcels(gw, gi)` called every
throttled tick right after `city_tick`. Per tick, the driver now does
three things instead of two: reads `CityStateJSON`, evaluates
`city_tick`, and — new — enumerates every live `BP_Parcel` actor
(`GameplayStatics.get_all_actors_of_class` against the PIE game world),
`ensure_parcel`s any it hasn't seen yet, and pushes each one's current
`Owned`/`Tier` onto the actor directly. `BP_Parcel` never parses JSON;
`ResolveMesh` only ever reads its own simple Blueprint variables. Proven
live: a real buy grew a parcel from an empty lot through several tiers,
each one resolving the correct catalogue mesh, with the state surviving
a PIE stop/start exactly as this contract's own live-proof block already
established for the tick alone. Full story, including a real catalogue
-population bug this caught, is in `PARCELIZATION_CONTRACT.md`'s
amendment.

## Growth model — RETIRED 2026-09-03, see "Growth contract" below

The open question this section raised is answered by the owner's own
2026-09-03 word: not automatic (current), not a hybrid — player-initiated
upgrades, gated on performance. Kept below, unedited, as the record of the
question being asked; do not read it as still open.

## Growth model — open design question, raised by the owner 2026-09-01

The owner's own words, watching their first bought lot climb tiers
unattended: "buildings seem to just keep growing and growing through
their tiers." Not a bug report — flagged as a gameplay-mechanics
question. It is `econrules.tick()` working exactly as scaffolded:
automatic tier-up once `accum` crosses a threshold, no player action
between purchase and the top of the ladder, no way to stop it. That was
never designed AS a final mechanic, only as the simplest thing that let
buy-and-grow be provable at all — and until tonight nobody had watched
it run long enough in one sitting to notice it has no brake.

Open, not decided here: automatic growth (current), player-paid
upgrades (a second verb, real choice, more UI), or a hybrid (grows to
some floor automatically, needs a purchase past it). This is the
owner's economy-design call, not something to resolve from inside this
contract — `econrules.py` is what it says, this contract is how it gets
called (see "Explicitly out of scope" below, unchanged principle,
same file). Decide it with the owner's own economy notes when that pass
happens, not by inference from tonight's session.

## Economy pacing table — RETIRED 2026-09-03, see "Growth contract" below

Both options below assumed growth stays a TIMER and only argued over its
constants. The owner's own 2026-09-03 word retires that premise entirely
— growth is not automatic at any speed; it is player-initiated and
performance-gated. Neither option was ever applied (`Content/Python/
pacing_option_b.patch`, prepared and self-tested for Option B, is deleted
— its own patched self-test line never reached the owner: a from-scratch
run of the applied patch failed, the transcribed number did not match a
real run, and it does not matter now regardless, since the mechanic it
was pacing no longer exists). Kept below, unedited, as the record of the
question being asked and the two answers that were on the table before
the owner reframed the question itself; do not read either option as
still live.

`econrules.py` and `econrules.json` are untouched by this section — numbers
and rationale only, for the owner to read before anything here lands.
Answers PLAYABLE_PLAN.md §2.3's pacing brief. **Assumes growth stays
AUTOMATIC** (the "Growth model" section directly above is still open and
this table does not resolve it) — this is a speed change to the current
mechanic, not an answer to whether it should be automatic at all.

### Today's numbers, and why they feel like they do

    money_start        100
    price_base           50
    price_per_100uu       2
    price_per_tier       25
    rent_per_tier         10
    growth_threshold      40
    demand_default       1.0
    tick interval          2.0 s  (init_unreal.py _TICK_INTERVAL_S, not
                                   in econrules.json — unchanged by this
                                   proposal either way)

**A structural fact worth stating before any numbers, because it explains
the "every 8 seconds" complaint precisely:** `tick()`'s formulas are both
linear in `(tier+1)` — `growth_threshold*(tier+1)` needed, `rent_per_tier*
(tier+1)*demand` earned per tick — so the `(tier+1)` factor cancels
exactly. **Every tier-up costs the identical number of ticks, regardless
of which tier it's climbing from.** Today that's `40/(10*1.0) = 4` ticks =
8 seconds, matching the owner's own log exactly (P4: tier 1 at :15, tier 2
at :23, tier 3 at :32 — 8s apart each time, not accelerating or slowing).
Confirmed by simulation, not just algebra: at today's constants a fresh
vernacular lot (6 tiers) tops out in **40 seconds total.** A second lot is
affordable **6.6 seconds** after the first purchase.

### Option A — retune the existing constants, no code change

The linear-cancellation above means constants alone can hit ONE pacing
target precisely but not both at once for a 6-tier ladder: pinning the
first tier-up to 2–3 minutes forces the full ladder (5 tier-ups, all
equal-length) to 10–15 minutes, short of the 20–30 minute target.
Proposed, prioritizing the target that defines a new player's first few
minutes:

    rent_per_tier        2     (was 10)
    growth_threshold    150     (was 40)
    price_base           80     (was 50)
    price_per_100uu       2     (unchanged)
    price_per_tier        25     (unchanged)
    money_start          100     (unchanged)

Simulated result (vernacular, 6 tiers, width 820 — placement.py's V0):
first tier-up **150s (2.5 min)**, every subsequent tier-up also 150s (the
cancellation still holds), full ladder **750s (12.5 min)**. Second lot:
buying the first (820uu, tier 0) costs 96.4, leaving 3.6 of the starting
100 — affording a second identical lot needs 92.8 more seconds (**1.55
min**) of rent at the new, much slower income rate. That is the "second
lot is a decision" target hit directly: waiting on a fresh purchase now
competes on the clock with waiting on the first lot's own tier-up.

### Option B — one-line code change, hits both pacing targets exactly

Requires changing `tick()`'s threshold term from `growth_threshold *
(tier+1)` to `growth_threshold * (tier+1)**2` (rent stays linear — a
higher-tier building earning proportionally more rent is the part of
today's shape worth keeping). This breaks the cancellation on purpose:
ticks-to-advance becomes `k*(tier+1)` where `k =
growth_threshold/rent_per_tier` — each successive tier-up costs more than
the last, the "harder as you build higher" shape city-builders usually
have and today's formula doesn't.

    rent_per_tier          2     (was 10)
    growth_threshold      120     (was 40)
    price_base              80     (was 50)
    (price_per_100uu, price_per_tier, money_start unchanged, same as A)

Simulated (vernacular, 6 tiers): tier-up times 120s, 240s, 360s, 480s,
600s (2, 4, 6, 8, 10 minutes — each one exactly 2 minutes longer than the
last). First tier-up **120s = 2.0 min** (the target window's own lower
edge). Full ladder **1800s = 30.0 min** (the target window's own upper
edge) — `k=60` is the unique ratio that pins both bounds at once for a
6-tier ladder; there is no slack either direction, which is worth the
owner knowing rather than discovering as "it only barely fits." Second
lot: identical to option A (same price/rent-at-tier-0 constants), 92.8s.

### Recipes with a different tier count

Contemporary (7 tiers) and office (4 tiers) shift under either option
because total ladder time scales with tier count. Not simulated here
pending the owner's choice of option — `rent_per_tier`/`growth_threshold`
are global constants (`econrules.json`), not per-recipe, so whichever
option is chosen applies uniformly and the office ladder (the shortest)
finishes fastest by construction. Worth a second simulation pass once
A vs. B is decided, not before — no reason to hand-compute seven
recipes' worth of numbers for an option that might not be chosen.

### What this does not touch

The buy-price-vs-tier-price interaction (`price_per_tier`, buying an
ALREADY-grown unowned lot) is unchanged from today in both options —
this pass only tuned the fresh-purchase and growth-speed numbers PLAYABLE
_PLAN.md named. `demand_default` also unchanged; demand as a dial (rather
than a fixed 1.0) is its own open surface, not touched here.

## Patina's Age channel — declared 2026-09-02, blocking the wear window

The design lane's wear system reads CPD channel 0 (`Age`, `cpdmap.py` —
"oxidises along THIS species curve") per parcel. This contract declares
the semantic before the driver wires it, per the design lane's own ask.

**Age = ticks-since-last-tier-change, normalized, RESET TO 0 ON TIER-UP.**
`Age = min(1.0, age_ticks / AGE_MATURE_TICKS)`, `AGE_MATURE_TICKS = 150`
(5 minutes at the 2s tick throttle — a tunable constant, not a measured
or final number, changeable in one place if it reads too fast or slow
live).

**Corrected 2026-09-02, same day it was first declared wrong: this is
locked owner doctrine, not this lane's call.** `Docs/DIRECTION_B.md` B3,
verbatim: "PATINA MECHANIC: LOCKED. New/upgraded buildings start pale
and age toward the board's honey tone over game time." UPGRADED, not
just new — a tier-up is exactly the event this resets on. The first
version of this declaration argued Age should stay monotonic (cumulative
oxidation, D3's "does not repaint itself" read as being about wear too)
— coherent on its own terms, and wrong: it argued against the owner's
own intake words without checking them first, the repo-outranks
-consensus lesson applied to a design doc instead of a code claim. D3 is
about TONE (species/colour never changing with tier); B3 is the actual
patina-over-time mechanic, and B3 governs Age. `Attention` (channel 4)
still layers on top of this, not instead of it — D16's nuance refines
what a *settled* building's edges look like, it doesn't override B3's
own reset-on-upgrade rule.

**Where this state lives, and why not in `citystate.json`'s core
schema:** `age_ticks` is tracked and persisted by `_sync_parcels`
directly, NOT by `econrules.tick()`/`citytick.city_tick()`. Both of
those have their own proven self-tests asserting EXACT state equality
against known answers (`citytick.py`'s own `__main__`, `assert s ==
direct_s2`); adding a field inside the tick pipeline itself would break
those assertions for a change that has nothing to do with the economy
they're proving. `_sync_parcels` already reads and writes
`citystate.json` independently of tick/buy (it's where Price/Accum
already get pushed) — `age_ticks` is one more additive field down that
same, already-proven side door, incremented once per throttled sync for
every currently-owned parcel, never touched by `econrules.py` at all.

**The other three wear channels (`Attention`, `Failure`, `Scorch`) stay
at 0 in this pass** — their own mechanics don't exist yet, and 0 is
already each one's correct neutral/inert value per `cpdmap.py`'s own
table (`Attention` is -1..+1 with 0 = "today"; `Failure`/`Scorch` are
0..1 with 0 = untouched).

## Growth contract — proposal for the owner, 2026-09-03, NOT APPLIED

Like the pacing table above, this crosses the "out of scope" line at the
bottom of this document (`econrules.py`'s own rules, not the calling
architecture) — kept here anyway, same precedent that section already
set, because it is a proposal awaiting the owner's word, not decided
architecture yet. Nothing in this section is implemented; no code was
written.

**The owner's own word, verbatim, watching growth run unattended a second
time:** "building should grow substantially slower...like days if
anything...their growth is supposed to be a factor of game performance
(trading success/failure) and user initiated upgrades/modifications."
This retires automatic growth at ANY speed (both options in the pacing
table above) and reframes the "Growth model" question above from "how
fast" to "driven by what."

### 1. The upgrade verb

A lot's tier changes ONLY on a player-initiated UPGRADE action — the same
shape as the existing buy verb (`BuyRequestPID`), not a new architecture:
a key + HUD prompt, shown when a lot is selected and eligible; costs
money (its own price — open question 1 below); refused loudly and
harmlessly when unaffordable, the same "insufficient funds" shape `buy()`
already has. `econrules.tick()` stops advancing tier on its own — accum
either stops existing as a concept or becomes an input to performance
(open question 2) rather than a growth countdown.

### 2. Performance — what it measures, what it gates

**What exists today, precisely, not assumed:** `demand` is a single
global scalar, seeded once from `demand_default` (1.0) and never written
again anywhere in this codebase (checked by grep, not recalled) — read by
`rent()`, pushed to the HUD, otherwise inert. It is not yet the "dial"
the module docstring calls it. Rent is tier-linear and per-lot; there is
no occupancy concept anywhere today. In short: today's model has nothing
that measures one lot's performance against another's — everything that
exists is either global (demand) or a pure function of tier (rent).

**Proposed, as a starting shape for the owner to react to, not a final
answer:** a per-lot performance score, accrued each tick a lot is owned,
from the gap between rent actually earned and that lot's own tier-scaled
expectation — a lot earning at or above expectation gains score, below it
loses score, `demand` (if it ever becomes a real dial rather than a fixed
1.0) weighting the expectation so a citywide downturn is felt lot-by-lot
rather than only in the aggregate number. This is ONE shape; open
question 2 below asks the owner to confirm or replace it.

**What performance does:** gates or discounts the upgrade verb above (a
hard floor below which upgrading refuses, a cost surcharge/discount
scaling with score, or both — open question 3); on sustained failure,
either pushes CPD channel 5 (`Failure`, `cpdmap.py` — 0→0.6 weathers
toward the species' own grey, 0.6→1 chars) or downgrades the lot's tier
outright (open question 4). Failure is a real, already-reserved channel
— `cpdmap.py`'s own table declares it, and ECONOMY_TICK_CONTRACT.md's
"Patina's Age channel" section above already named it inert ("stays at 0
in this pass — its own mechanics don't exist yet"). This proposal would
be that mechanic's first real use, not a retrofit of something already
wired to anything.

### 3. Passive time

A single constant, e.g. `PASSIVE_DAYS_TO_X` (name and unit open), gating
whatever small drift happens with no player action at all — the owner's
own "like days if anything" sets the scale and explicitly allows zero.
At zero: growth is purely the upgrade verb plus performance, no passive
component of any kind. Nonzero: some slow, day-scale drift alongside the
verb (performance recovering slightly on its own, say) — the owner's
call, not decided here. Either way this needs its own definition of a
"day," since ticks today run in real wall-clock seconds (2.0s each) with
no day/session/calendar concept anywhere in `citytick.py`/`econrules.py`
— a genuinely new piece of vocabulary this proposal introduces rather
than reuses (open question 5).

### 4. Age (patina), unchanged mechanic, changed rhythm

Not a new rule — `Docs/DIRECTION_B.md` B3, locked owner doctrine, quoted
already in this file's "Patina's Age channel" section above: **"New/
upgraded buildings start pale and age toward the board's honey tone over
game time."** `Age = ticks-since-last-tier-change`, reset to 0 on a
tier-change — which is now the upgrade verb firing, not an automatic
threshold-cross. Nothing here changes that rule; it changes how OFTEN it
fires. Worth naming as a consequence, not a new mechanic: under automatic
growth, tier-ups happened every few minutes at worst, so Age rarely
travelled far before resetting. Under player-initiated upgrades, a lot
the player never upgrades just keeps aging, uninterrupted, for the whole
session — Age finally gets to show its full pale-to-honey range in
ordinary play, something the automatic-growth model was quietly
suppressing the whole time.

### Open questions for the owner

1. **Upgrade price** — the same formula shape as purchase price
   (`price_base` + per-100uu + per-tier), an independent formula, or a
   function of the performance score itself?
2. **Performance score** — confirm or replace the shape in section 2
   (earned-vs-expected rent, demand-weighted), or name a different
   signal entirely (occupancy, something else)?
3. **Does performance GATE or DISCOUNT** the upgrade verb — a hard floor
   below which upgrading refuses, a cost surcharge/discount, or both?
4. **On failure** — does channel 5 climb and recover on its own once
   performance improves, only via a player action, or is a tier
   downgrade a separate, harder threshold below that?
5. **Passive time** — zero, or a days-scale value? If nonzero, what does
   a "day" mean in tick terms — this needs a definition that does not
   exist in the codebase today.

## Explicitly out of scope

Packaged/shippable builds — `PythonScriptPlugin` is editor-only, so (b')
covers the entire chartered beta (PIE sessions for the owner) and stops
at the packaging line; a shippable demo would need option (a)'s BP
arithmetic port, `econrules.py` demoted to known-answer oracle, because
C++ is a hard stop in this project (`AGENTS.md`). A dynamic demand model
(`demand` is a flat input today, not simulated). Anything that changes
`econrules.py` itself — this contract is about how it gets called, not
what it says.
