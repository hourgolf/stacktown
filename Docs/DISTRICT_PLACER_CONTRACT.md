# District placer contract — metadata emission (draft)

**STATUS: SCHEMA v0 OWNER-BLESSED, 2026-08-30 — after the design
session's five-finding adversarial pass, all absorbed. This is the
declare-before-geometry contract the placer implements against, known-
answer parcel test first (including the unframeable parcel). Fields
beyond v0 land only WITH their consumers, per the named-futures
paragraph.**

## The adopted decisions, verbatim scope

1. **Metadata-emission is a district-placer REQUIREMENT** — the placer
   emits the gameplay layer in the same pass that places parcels.
2. **CityTick stop-motion traffic prototype** — approved in principle,
   SEQUENCED AFTER the owner's economy notes. Cars reposition between
   placer-emitted parking points on discrete ticks; no plugins, no C++.
3. **PCG doctrine REAFFIRMED unchanged** — re-examined against City
   Sample 2026-08-30; the modern Epic path is PCG-native and nothing we
   want requires it. genbuild remains the shape-grammar engine.

## Why a contract before code (the no-bug-chasing plan)

Every painful week this project has had came from implementation before
declaration. So the placer metadata enters the same way archetypes did:
schema DECLARED and self-tested before the placer emits a single field,
graduated in as PENDING, and versioned so consumers can refuse data they
do not understand.

- **Schema versioned** (`meta_version`), consumers assert on it.
- **Known-answer parcel**: one hand-computed parcel's full emission is
  the schema self-test — every field derivable by hand, checked on every
  placer run (the lever-diff discipline applied to data).
- **Emission is a side effect of placement, never a reason for it** —
  the same side-effect principle as the regression ledger.
- **New fields are PENDING until a consumer exists** — no speculative
  fields ("YAGNI with a gate"): each field lands WITH the system that
  reads it, or not at all. (The first draft tried to soften this with a
  "reservation of names" — the adversarial pass rejected that defence
  with same-day evidence, and the futures now live in a paragraph, not
  the schema.)

## Per-parcel emission (schema v0 — revised after the design
## session's adversarial pass, 2026-08-30; all five findings absorbed)

    meta_version     schema version; every consumer asserts on it
    parcel_id        IDENTITY, defined: (block_name, lot_ordinal_at_
                     first_placement) - the ordinal is ASSIGNED ONCE at
                     first placement and NEVER renumbers on insertion,
                     split, or recipe change (a split mints new ids;
                     the old id retires, never reused). The self-test
                     FAILS on collision or renumber across a
                     re-placement. (Today's detector bug was an
                     identity bug - non-unique names silently returning
                     the wrong geometry; this is the same hazard one
                     level up, closed by definition + test.)
    geometry_head    THE STALENESS STAMP: the catalogue commit every
                     geometry-derived field below was computed against.
                     Consumers REFUSE or RE-DERIVE when it does not
                     match the staleness ledger. (548 meshes changed in
                     one day this weekend; data computed from meshes
                     without a ledger is the S16 shape as data.)
    recipe/tier/width  the catalogue pointer
    frontage         street edge: centre + width, measured from
                     PER-COMPONENT MESH BOUNDS AGAINST WORLD TRANSFORMS
                     - the METHOD is contractual, because the obvious
                     accessor (get_actor_bounds) measurably lies
                     (today's phantom 3,604 uu Depot).
    camera_poi       facade centre + whole-building standoff at the
                     gate optic, OR NULL WITH A REASON CODE when the
                     framing does not exist (unfittable: needed
                     standoff exceeds clear space - the Foundry stack
                     case, measured at 7,494 needed vs 4,506 clear).
                     The known-answer test includes one parcel that
                     CANNOT be framed; a schema tested only on the
                     easy parcel is not tested.
    practicals       anchor points for lit fixtures (consumer: the
                     lighting pass, which exists)

## Named futures (NOT fields - a paragraph, deliberately)

econ hooks, parking/route points, and ambience zones are NOT in schema
v0. Cut by the adversarial pass under the contract's own rule ("each
field lands WITH the system that reads it"): reserving a name fixes a
shape before the consumer can say what shape it needs, and the day this
contract was revised, exactly that failure shipped - preview.py emitted
coplanar_visible as the RAW count while gate_11 judged the exempt
count, and the mismatch reached the regression ledger unnoticed. When
the economy notes land, econ fields land with them; when the traffic
prototype starts, parking lands with it; ambience lands with audio.
This paragraph is their reservation.

## Sequencing (nothing moves before its gate)

    now                this contract circulated; design session
                       co-authors; owner blesses schema v0 names
    unchanged          works-brick -> full wave (+ baseline re-seed)
                       -> read #2   (the adoptions touch NONE of it)
    after economy notes  econ schema fills in; CityTick traffic P0
                       (pure-python tick model + a few resin cars in a
                       sandbox, judged by eyes per house rules)
    when placer work begins  schema v0 implements WITH its known-answer
                       parcel test, PENDING until it survives a full
                       block placement + census

## Explicitly out of scope

Mass/ZoneGraph/MassTraffic adoption; MetaHuman or any moving figures
(breaks the miniature fiction); PCG enablement; importing City Sample
content in any form; any change to bake, gate, or wave machinery.
