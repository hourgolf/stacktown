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

## Measured consequence: the corner protrudes and shows a bare party flank

**2026-08-31, `TestCity`, arterial street frame `(-6800, 0, 260)` pitch 2.**

`DEPTH_CORNER = 1500` was chosen so a corner's return reads as a full elevation on
the cross street rather than a stub. It does. But nothing reconciled that depth
against the depth of the corner's NEIGHBOURS on its own street, and measured in a
built city they are not close:

| | depth (measured actor bounds) |
|---|---|
| `TC_Bld_SW3_vernacular_t5` (corner) | **1,628** |
| `TC_Bld_SW2_contemporary8_t5` (neighbour) | 781 |
| `TC_Bld_SE0_modern8_t2` (corner) | **1,572** |
| `TC_Bld_SE1_vernacular6_t2` (neighbour) | 924 |

So every corner stands **700–850 uu proud of the building behind it**, and that
protruding strip is a blank party flank aimed straight down the street. In the
TestCity arterial frame `SW3` presents 847 uu of bare wall, 1,996 uu tall, filling
the frame from centre to right edge — enough that the frame cannot be used to judge
anything else, lighting included.

This is the "big green building with no windows" the owner reported on 2026-08-30,
now with a cause rather than a sighting. It is also the exact subject — the exposed
party flank — ranked first among the proposed on-demand bake references.

**Not decided here.** Two candidate fixes, and they are different kinds of work:

1. **Bake the flank.** A party flank is a real architectural surface (blind brick,
   ghost signage, a few high windows, a downpipe). This is the reference-subject
   route and it makes the protrusion legible rather than hiding it.
2. **Reconcile the depths.** Either bring non-corner depths up toward `DEPTH_CORNER`,
   or make the corner's depth a function of its neighbour so it never protrudes.
   Cheaper to render, but it removes a massing variation the city currently gets
   for free.

Owner/coordinator call. Flagged, not actioned.
