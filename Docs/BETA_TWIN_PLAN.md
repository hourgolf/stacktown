# The beta twin — one gameplay, two catalogues (owner decisions, 2026-08-31)

**The premise, from the architecture's luckiest fact: the gameplay layer
resolves meshes by catalogue key and never knows what a building looks
like. Two versions of the same game = two catalogues behind one
pointer.** The flagship miniature and a SECOND, deliberately simpler
art direction (owner-directed — "same basic premise of the full
catalog, much simpler art direction"; owner supplies look examples)
share every line of gameplay, the placer, the parcels, the camera, and
the tick machinery.

## Owner decisions of record

1. **Placeholder economy NOW**, labeled scaffolding, replaced when the
   owner's economy notes land.
2. **The simple version is an ART DIRECTION, not a greybox** — owner
   provides reference examples; a lightweight canon-style intake shapes
   it (same process as the miniature's canon, lighter weight). Until
   examples land, mechanics run on the test-city interim masses,
   explicitly interim.
3. **First beta audience: the owner, in PIE.** Packaging waits until
   outside testers matter.

## The standing guard (ancestral)

This is a MECHANICS INSTRUMENT, never a route around the visual gate.
The look lane is not failing (read #2 passed) and continues untouched:
DESIGN keeps the flagship look (real estate office, polish, corners);
the coordinator takes the gameplay slice. The simple catalogue gets its
own honest direction when the owner's examples arrive — it is a second
product's look, not an escape from the first's.

## Placeholder ruleset v0 (scaffolding — replace with the owner's design)

    money        start balance; the only resource
    parcels      unowned parcels are buyable at price = f(width, tier)
    rent         owned parcels pay rent per CityTick = f(tier)
    growth       an owned parcel tiers UP when cumulative rent crosses
                 a threshold (stop-motion pop per the growth doctrine)
    demand       ONE global dial (the marketplace's placeholder): scales
                 rent; the player reads it at board range
    loop         buy low-tier parcels -> collect -> watch them grow ->
                 buy deeper into the board
    explicitly out: lose conditions, districts, adjacency, traffic -
                 all owner-design territory, not scaffolding

## Build phases (coordinator's lane, PIE-first)

    A. catalogue pointer: ResolveMesh reads the active catalogue from
       ONE swappable table - the two-versions mechanism, built first
    B. selection: focus-as-selection from CAMERA_DESIGN made real -
       pick a parcel from the boom (trace from camera through the
       parcel metadata), HUD shows parcel identity + state
    C. economy tick: ruleset v0 on the existing CityTick machinery;
       tier-ups as mesh pointer swaps; money + demand on the HUD
    D. buy action: the acquisition verb (the real estate office's
       function arrives with DESIGN's building; the verb needn't wait
       for the facade)
    E. owner plays in PIE on the test city; reactions steer mechanics
    F. when owner look-examples land: simple-catalogue intake ->
       simplified generation profile -> second catalogue -> the swap
       demonstrates two games from one build

All Blueprint + Python tooling; no C++, no new plugins; one-writer rule
and announce-before-mutate as always. Editor windows interleave with
DESIGN's look lane.

## Seams and blockers (design-session review, 2026-08-31 — all adopted)

1. **PIE AND BAKING ARE MUTUALLY EXCLUSIVE** — stronger than window
   interleaving: bake_catalogue hard-refuses while PIE is up (by
   design, after two bakes died on leftover play sessions). Protocol:
   **ANNOUNCE-BEFORE-PLAY** — PIE runs in DECLARED BLOCKS with an
   expected duration, announced like any mutation; bakes take
   scheduling priority; every block ends with StopPIE + confirmation.
2. **Phase F is generator territory (design lane's seam), entered only
   on its precedent**: the simple profile is SPEC-LEVEL keys with
   behaviour-preserving defaults, every change PROVED BYTE-IDENTICAL
   for flagship output against a frozen sink sample, and no build_*
   function body is edited. Two products stay free at the look level
   instead of forking the generator.
3. **Direction B will fail the flagship gate BY CONSTRUCTION (fewer
   parts per m2 IS the direction) — the honest mechanism is its OWN
   archetypes.py entries** declaring what good means for it, with
   reasons, exactly as industrial does. NEVER --force. "It's the simple
   direction" is precisely the sentence a future reader would use to
   skip a gate; this paragraph exists so they can't.
4. **Direction B references are NOT canon**: CANON.md is capped at 8
   slots, 5 filled, and defines the flagship's only comparison set.
   Direction B gets its own reference board, never citable for flagship
   work (owner decision recorded when examples land).
5. **The economy respects per-recipe ladders**: the office has FOUR
   deliberately larger tiers (t1-t3 not yet baked, one width). Ruleset
   f(tier) reads ladder length per recipe from the catalogue — never
   assumes 6, never assumes uniform deltas — and a tier-up whose asset
   does not exist BLOCKS LOUDLY ("growth blocked: not baked") instead
   of resolving a null mesh.
Also: all beta tooling that spawns declares intent per genbuild's
record()/live() contract (commit 726be63).
