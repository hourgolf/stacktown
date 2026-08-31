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
