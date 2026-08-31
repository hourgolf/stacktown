# Depth & corner — catalogue identity decisions (owner, 2026-08-30)

Raised by the test city's corners (a corner parcel cannot present a real
cross-street elevation at the catalogue's fixed depths), grounded in the
design session's findings: depth is a fixed per-recipe constant (680–860
against 1,500-deep lots — the empty back half is on the code-review
record), depth is absent from the baked identity so deeper variants
would collide, and asset_name's own width argument ("the generator lays
bays out across it; fill means the same tier occupies a different share
of a different parcel") carries verbatim to depth on the other axis.

## The three rulings

1. **DEPTH: DECLARE THE AXIS, SHIP ONE VALUE.** Depth joins the identity
   grammar now; exactly ONE new value ships — the deep/corner variant —
   baked ON DEMAND where the placer sites it. No ladder until placement
   demand proves one (YAGNI-with-a-gate, the placer-schema cut applied
   to the catalogue). recipes._selftest iterates (width, depth) pairs
   from the axis's first day, or it silently stops covering it.

2. **CORNER: JOINS THE IDENTITY, HANDED, ON DEMAND.** corner_side makes
   a corner building handed; both hands are REAL buildings, baked as a
   model-maker would build them — mesh-mirroring rejected on fabrication
   honesty and tangent-space cost. The placer requests only the hands it
   actually sites.

3. **THE 548 STAND.** Absent suffix = implicit default depth. No rename,
   no rebake, no staleness event. The price of the implicit default:
   the name grammar (SM_Bld_<rid>_t<t>_w<w>[_d<depth>][_c<side>]) is
   documented ONCE in asset_name's docstring, and every name-parser in
   the tree is ENUMERATED and updated — census, placer, sweeps that
   split on underscores. The name-collision bug of the same day is why
   parsers are listed, not discovered.

Bake-policy note: deep/corner recipes are look-risky changes on shipped
surfaces — trigger (a) governs when their bakes land. Until they exist,
corners place standard buildings; known limitation, owner-seen.

Implementation is the design session's from here.

---

## The corner protrudes — but its flank is NOT bare

**2026-08-31, `TestCity`, arterial frame `(-6800, 0, 260)` pitch 2.**

**This section originally claimed the protruding corner presented a blank party flank
that filled the street frame. That was wrong on the second half, and the correction
matters more than the finding.**

### What is true

`DEPTH_CORNER = 1500` was chosen so a corner's return reads as a full elevation on the
cross street. It does. Nothing reconciled that depth against the corner's NEIGHBOURS on
its own street, and measured in a built city they are not close:

| | depth (measured actor bounds) |
|---|---|
| `TC_Bld_SW3_vernacular_t5` (corner) | **1,628** |
| `TC_Bld_SW2_contemporary8_t5` (neighbour) | 781 |
| `TC_Bld_SE0_modern8_t2` (corner) | **1,572** |
| `TC_Bld_SE1_vernacular6_t2` (neighbour) | 924 |

So every corner stands **700–850 uu proud** of the building behind it, and that strip is
visible from the street. That much is measured and stands.

### What was wrong

The protruding strip is **not** a blank wall. `step_elevations.freestanding()` already
treats every face of a catalogue model, and its docstring gives the reason: *"a blind
wall is a visible bug the moment a model lands on a corner."* A close capture of `SW3`'s
west flank shows the full vocabulary — piers, band courses, recessed panels, mullions.
The doctrine was already right and the geometry was already built.

**The wall that filled the street frame was four stray `ELEV_T` actors** — leftover
elevation staging geometry standing at world origin, which in `TestCity` is the middle
of the junction. 1,844 × 1,638 × 1,608, and **three of the four were exact duplicates**:
the "standalone re-run stacked a second elevation on the first" duplication that
`step_elevations.run()`'s wipe exists to prevent. That wipe only fires inside `run()`,
so calling `flank()` directly leaves its output behind. Hiding them removed the wall;
destroying them cleared the frame.

**How the error was made, since it is the reusable part:** the row assignment was
inverted. UE is left-handed — looking along +x, **+y is frame RIGHT** — so the wall on
the right was a `+y` object, and the corner I blamed sits at `-y`. The angular arithmetic
that should have caught it was run against the wrong sign and appeared to confirm the
answer. Project a suspect actor's bounds into the frame and check the sign before naming
it.

### Still open

Whether corner depth should be reconciled against neighbour depth at all is now a pure
massing question, not a defect: the protrusion shows a real elevation, so it reads as a
building that is deeper than its neighbour, which is what it is. **No action taken, and
none is now obviously needed.**

One thing worth a look that this did surface: `SW3`'s flank panels render magenta and
teal, well outside the restrained palette the direction calls for. Not chased down —
the material behind it is unconfirmed.
