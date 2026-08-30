# District placer contract — metadata emission (draft)

**STATUS: owner-adopted DIRECTION, 2026-08-30 (all three City Sample
research recommendations, Docs/RESEARCH_CITYSAMPLE.md). This document is
the declare-before-geometry contract for the district placer's metadata
layer. DRAFT — co-authorship invited from the design session; nothing
here is implemented, and nothing here touches the current wave, works-
brick, or read #2.**

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
  reads it, or not at all. The schema below is therefore a RESERVATION
  of names, not a build list.

## Reserved per-parcel emission (draft schema, v0)

    parcel_id        stable identity (block, index)
    recipe/tier/width  already planned - the catalogue pointer
    frontage         street edge, MEASURED centre + width (corner-origin
                     lesson: centres are computed from extents, never
                     assumed)
    econ             {} - RESERVED, schema arrives with the owner's
                     economy notes; parcels carry hooks, never logic
    camera_poi       facade centre + whole-building standoff at the
                     gate optic (pre-computed so framings are measured,
                     not authored - the reel/precast lesson as data)
    practicals       anchor points for lit fixtures (nightlight canon)
    parking          list of stand points on the parcel's frontage -
                     the traffic prototype's substrate
    ambience         zone tag (street / yard / rooftop) - soundscape
                     consumer, far future

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
