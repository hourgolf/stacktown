# Code review — branch city/roads-lighting-invariants @ 374aafb

Reviewed 2026-08-25 by a read-only review agent: all 29 commits vs main,
Python generator stack + QC suite. Findings ranked most severe first.
Findings are the reviewer's claims — each should be verified per project
rules before being treated as fact. Finding 1 was confirmed by the owner
on block F before any fix.

## Fix status (2026-08-25, same day — code fixed, in-editor validation PENDING)

FIXED in code, verified headless (self-tests, known answers, syntax):
  1  window() rebuilt as an applied unit proud of the wall (genbuild.py);
     dormer call now passes the dormer's real front face; true cut-recess
     deferred to each draft recipe's detailing pass by design
  3  step_cores3 excludes all detached styles (house/walkup/works)
  4  lamp_lights side decode fixed (F/N/W/E map); street_lamps avenue arms
     get yaw -90 and reach per side; avenue lamp cap derived from BOARD_N
  5  step_elevations exposed_flanks/rears exclude detached styles
  6  grammar self-check rewritten against live recipes (passes again);
     place_catalogue/fill_runtime/add_map speak vernacular w1230 with
     derived membership; sim_tick keys vernacular, PAD derived from
     BOARD_N, resolve() misses now HALT the benchmark loudly
  7  place_catalogue PAD + sim_tick grid derived from BOARD_N
  8  F==0 gable window guarded (skips when the wall range is inverted);
     F==0 flank windows dropped into the ground floor
  9a ROAD-01 added: building/zone/plot/prop footprints vs carriageways,
     with self-test  (NOTE: will correctly FAIL on block H until the yard
     is re-laid — that is finding 2 reporting, not a false positive)
  9b PROP added to labels.DRESSING (covered by DRESS-04/06)
  9c SNAP-01 added: unread material slots fail the suite
  9f GATE-05 judges per SIDE (8 uu tol): the 22-uu one-sided overhang now
     fails; self-test carries that exact calibration case + a plinth pass
  9g citygeom.zone_layouts classifies every layout key and RAISES on
     unknown ones (fails closed); park/yard keys classified
  9h zone_layouts defaults 'tree' so ZONE-01 cannot KeyError on the yard
  9i bake_catalogue label superset raised to F0..F39, cores b0..b11
  -  modelgate _clean() now passes its own gate (rear parts added; the
     __main__ footer had printed False since the file was written)
  10 yard_props.put() rotates local offsets through the block yaw

AWAITING OWNER DECISION (design changes, not code fixes):
  2  block H straddles the avenue corridor — re-lay block H or move the
     avenue; ROAD-01 will keep failing until decided
  11 BLOCK_B_DEPTH 790 vs Hall 820 — moving either relocates street 2
  9d zero-part entries skipped by DETAIL rules (missing-building policy)
  9e ZONE-02 "faces open ground" semantics

DEFERRED (cleanup, no behavior change):
  12 fastbake_check.py parity evidence missing from the branch
  13 transform/height-formula consolidation, dead code

VALIDATION STILL NEEDED IN-EDITOR (none of the above is DONE until then):
  rebuild blocks F, G, H; rerun street_lamps + lamp_lights; run the
  invariant suite (expect ROAD-01 FAIL on block H, everything else ok);
  re-bake nothing yet; capture block F fronts and LOOK at the windows.

## 1. genbuild.py:99-131 — window() recesses INTO the wall; glazing buried in solid Wall_Body (house/walkup/works)
`d = -outward; g = plane + d*24` puts glass/frames/sill/mullions 8-26 uu behind
the wall face. Correct for pier-and-gap facades (vernacular/modern/deco) where
the recess is open air; wrong for the styles that build one solid Wall_Body box
and call window() against its face: build_house (940, calls 969-995),
build_walkup (1190, calls 1216-1295), build_works (1346, calls 1372-1383).
Dormers worse: window at 1133 uses plane hy0-8, glass 20 uu behind the 8-uu
Wall_DormerF. Renders: blank walls with only proud trim visible. Matches the
recorded symptoms that retired the cottage ("blank front and blank dormers
after three rounds of detail") and the walkup's blank rear on the contact
sheet. GATE-03/DETAIL-01 count the invisible parts as detail.

## 2. city.py:247-258 — Block H straddles the avenue corridor
Block H spans X 1200..6200; avenue corridor X 4400..6660 (carriageway
4830..6230). Depot crosses the west frontage by 300 uu; the Yard lot
(4700..6200) sits almost entirely in the carriageway. step_stage2.py:75-80
paves the avenue over the full board, so the next roads rebuild lays road
through the yard; fence gate (~X 5132..5768) and both containers (X~5050/5670,
Y~4098) stand in the carriageway. No invariant relates lot/zone/prop
footprints to G.road_rects() (see 9a). Also silently rejects the street-0/
avenue signal corners via footprint_free.

## 3. step_cores3.py:34 — cores exclude only style=='house'; walkups and works entombed
Block G walkups: core from local Y 62..1500 at width W+16 while the body sits
Y 130..650 — core face 68 uu in FRONT of the front wall (buries windows,
balcony tips poke from a flat slab), rear filled to the lot line (the likely
literal "blank rear" on Rowan). Block H: core front 62 vs body front 90 buries
shutters/docks; core top pokes through sawtooth slopes. build_blocks.py:56
runs unconditionally. cores.py:73 repeats the house-only exclusion (moot for
now — no detached recipes in catalogue).

## 4. lamp_lights.py:34 — F/N decoding inverted vs street_lamps.py
street_lamps.py:101: side F = reach +1 (over road), N = -1. lamp_lights maps
F to -1.0 — opposite on both sides: every street lamp's light hangs 420 uu on
the wrong side (over pavement, not under head). DRESS-05 pairs by name suffix
only, so passes. Avenue arms additionally run parallel to the kerb (no yaw on
arm, street_lamps.py:110-115).

## 5. step_elevations.py:64,85 — exposed_flanks/rears exclude only 'house'
Commercial party-wall flank slabs hung beside detached walkups/works: block G
Alder/Hazel get free-standing flank_vernacular slabs 138 uu off the building,
full 1500 lot depth over a 520-deep building; Depot high flank + Foundry low
end same. run() (344) iterates the city table where blocks G/H remain.

## 6. Retiring cottage/walkup broke the committed runtime-slice path
- grammar.py:47-56 self-check asserts candidates(820,1500,'residential') ==
  ['cottage'] -> now throws; pick(...,'residential') returns None.
- place_catalogue.py:52 rid='cottage' -> KeyError in recipes.tier_count.
- fill_runtime.py:14,48 / add_map.py:18 WID[rid] KeyError('vernacular'),
  swallowed by blanket except -> "catalogue step FAILED", exits successfully.
- sim_tick.py:59-60 parcels keyed cottage/walkup -> every resolve() LUT
  lookup MISSES, unchecked -> the benchmark's 500-parcel timing measured
  ticks that never assigned a mesh. The recorded first tick number is suspect.
- RUNTIME_SLICE.md:56,77,130 still specifies the cottage/walkup catalogue.

## 7. Stale board constants after northward growth
- place_catalogue.py:14 PAD=(6200,1500,9600,2900) now sits across street 0
  (carriageway Y 1230..2630); parked cars and street-0 trees land in the pad.
- sim_tick.py:15 same stale origin for the 500-parcel grid.
- street_lamps.py:113 `while y < 700.0` caps avenue lamps at the old board
  top; 2,600+ uu of avenue unlit.

## 8. genbuild.py:974-976 — F==0 gable window inverted Z
z0=194 > z1=166; abs() masks it; 28-uu window lands over the door/fanlight
instead of in the gable. Flank windows float above the eaves for F==0.

## 9. Invariant/gate-suite gaps
a. No road-conflict rule (footprints vs G.road_rects()) — why finding 2
   passes 18 rules clean. Rectangles already exist in citygeom.py.
b. labels.py:61 PROP not in DRESSING and double-booked (Stage 1 tree + yard
   props): DRESS-04/DRESS-06 never see a container; failed wipe stacks dupes.
c. snapshot.py:64 unread_material_slots counted, never consumed; MAT-01/
   BAKE-01/GATE-02 iterate empty mats lists without complaint.
d. detail_01/detail_02 skip zero-part entries; missing-building check lives
   only in check_block.py (manual) — a wiped building passes the suite.
e. ZONE-02 "bench faces open ground" only tests look-point inside bounds —
   bench staring into fountain basin/bandstand passes.
f. modelgate.py:159-183 GATE-05 tolerance pw*1.02 + inset far side: a
   one-sided 22-uu overhang (its own comment's example) passes. Self-test
   too coarse (1.5x width).
g. citygeom.py:90-111 zone_layouts() fails open on unknown keys: park keys
   (ring/node/stand/centre) and yard keys (apron/hard/gate) pass through
   UNTRANSFORMED (block-local) — block E is yaw-180. Should raise.
h. invariants.py:551-576 ZONE-01 KeyError on yard zone actors ('vacant'
   layout has no 'tree') — crashes the suite run.
i. bake_catalogue.py:86 label superset stops at F11; >=12 floors silently
   excluded from gate AND merge.

## 10. yard_props.py:67-78 — put() adds block origin without rotating offset
Docstring claims yaw-safety; only the actor rotation carries yaw. On a
yaw-180 block every prop lands mirrored outside the lot; PROP_ invisible to
DRESS-04 (9b) so nothing flags. Use citygeom.to_world.

## 11. city.py:30 vs 188-190 — BLOCK_B_DEPTH=790 vs Hall depth 820
Hall's rear elevation slab reaches ~90 uu into street 2's footway; block D
same class (760+60 crosses 790 by 30). Nothing verifies lot depths against
block-depth constants.

## 12. fastbake.py:15-16 cites fastbake_check.py as parity evidence — never committed
The branch's stated proof of slow/fast geometry parity cannot be run.

## 13. Duplication / dead code
- Six hand-rolled copies of the yaw transform (citygeom.lot_rect/to_world,
  fix4_props x3, check_block.lot_world_x, step_shopfronts.world,
  yard_props.put — the unshared copy is the buggy one).
- Height formula gf_h+floors*fl_h+parapet in four places.
- Core bands: cores.bands_for vs step_cores3 (latter ignores setback_floors).
- snapshot._aabb vs check_block.world_aabb identical.
- Dead: zones._surround, genbuild build_walkup dead z0, made+=0,
  lamp_lights `if True: pass`, street_lamps.wipe() no-op, 34*abs(reach),
  DRESS-07 missing break (dupe reports only).

## Reviewer's architecture assessment
Core ideas good and consistently applied (block-local coords, derived roads,
role-in-name, pure-data self-testing modules, shared thresholds via qc.py).
Structural weaknesses: rule-set coverage is unmanaged (rules added per past
failure; whole categories have no rule, and "18/18 ok" reads broader than it
is); style dispatch grows detached styles while downstream sweeps still
hard-code the old 'house' exclusion; the yaw transform and height formula
are re-typed per script instead of imported — where the one real transform
bug lives. Parts-per-m2 counts components, not VISIBLE surface — it has now
twice passed geometry that renders blank.
