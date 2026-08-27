# Code review — the catalogue sprint (5197ad1..4d51c4f)

Reviewed 2026-08-27 by a read-only agent at commit 4d51c4f. Findings are
claims to verify per project rules. Ranked most severe first. Triage per
Docs/POLISH_PROTOCOL.md is noted per finding.

## The headline

**The fast bake path's gate is donor-blind, live, and stamping.**
preview.py:67-68 `as_snapshot` silently drops every kind=='mesh' record, so
the gate the preview runs judges boxes only while fastbake BAKES the donors
into the asset. GATE-05 cannot see a donor's bounds, GATE-02 its materials,
GATE-03/09 do not count it. This is byte-for-byte the blind spot that
quarantined the offline width sweep - except this copy CERTIFIES: preview
vernacular5@1230 -> gate PASS -> stamp Gate=PASS on the very mesh the
editor gate refuses at 1162 uu. Stamped SpanX/SpanY exclude donors too, so
the audit inherits the blindness.

**Consequence: any preview-path-stamped mesh containing donors may carry a
false PASS. The catalogue's verified status is partly unverifiable until
the mesh-bounds table exists and those meshes are re-gated.**

**The one fix that heals three tools:** a mesh-bounds table (asset -> local
AABB including pivot offset), read once from disk. It repairs as_snapshot,
un-quarantines the offline width sweep, and gives the audit honest spans.
donorsheet.py is the natural measuring station - the pivot offset is on
screen there and currently goes unrecorded (finding 5). Also: stamps should
record WHICH gate path stamped them, so path provenance is evidence.

## Ranked findings (triage outcome in caps)

1. preview.py:67-68 as_snapshot drops kind=='mesh' - donor-blind gate,
   live and stamping (above). GENERATOR FIX + GATE RULE (a gate self-test
   that plants a donor record and asserts the gate SEES it).
2. catalogue_audit.py:23-28 - audit skips every w2050/w2460 mesh and all
   of deco7 via a stale private CUT={820,1230,1640} (dead `import parcels`),
   while totals look complete. An unstamped w2050 mesh ships and the audit
   prints "0 unverified". GENERATOR FIX: derive widths from recipes.widths;
   delete the third ladder copy.
3. modelgate.py:559-564 - GATE-10's in-front-of-core exemption compares
   WORLD Y against a spec-LOCAL plane; dead at the bake stage (0,60000,0),
   alive at preview's origin stage. The two gate paths disagree the day a
   facade vent lands at core-top height. Same coupling: GATE-05's X test
   works only because stage X happens to be 0. GENERATOR FIX: hand the
   gates parcel-local coordinates (subtract stage origin explicitly).
4. step_foliage.py:32-33 vs rolemap.material_for_slot - the level sweep
   and fastbake already disagree on donor slot matching ('leaf_maple'
   bakes right, goes dark-quad in level). GENERATOR FIX: one matcher, in
   rolemap, used by both.
5. donorsheet.py:89-92 - the vetting sheet renders donors with ONE
   material across slots (the exact defect fastbake fixed) and never
   records actor-location-vs-bounds-center - the pivot offset, the 1162
   class's cause, visible at this station and unrecorded. GENERATOR FIX +
   this is where the mesh-bounds table gets measured.
6. modelgate.py:201-205 - GATE-05 depth is span-only; a rear part can
   trespass the next plot by up to OVERSAIL(130) minus front projections.
   The width check was rewritten per-side for exactly this; depth was not.
   GATE RULE (per-side depth, front oversail only).
7. catalogue_audit.py:56 - audit re-implements parcel fit as
   span_x > width*1.02, the discredited span heuristic, threshold not in
   qc.py, fed donor-blind spans. GENERATOR FIX: judge per-side from the
   bounds table; threshold to qc.py.
8. street.py:155-171 - repaint matches hardcoded material-name strings
   (private copies of rolemap.SHARED) and never checks its match count; a
   rolemap rename silently no-ops. GENERATOR FIX + loud zero-match.
9. parcels.py vs recipes.py - assembly can produce XXXL=2870 parcels no
   recipe declares; nothing asserts recipes.widths are a subset of the
   parcels ladder or that reachable widths have coverage. GATE RULE
   (self-test: ladder membership + coverage or not-offered).
10. Minor: bake_catalogue.py:39 count uses want[0]'s tier count for all;
    blockrig.py:103-104 reads back only intensity. CLOSED-UNLESS-CHEAP.

## Verified sound, said so deliberately

blockrig's inverse-square derivation (flux x ratio^2, emitter scaling, aim
math, Rotator order); cam_street_hero; GATE-09/GATE-10 rules and their
self-tests; cores.setback_at unifying four drifted copies; the per-side
GATE-05 width rewrite; qc.py extraction; ubkit's measured-footprint
self-test - the last is the PATTERN: declaration-vs-declaration self-tests
(recipes fits() vs widths) certify nothing; measured-footprint tests do.

## The recipes.py verdict

The fit rule is the liar: fits() is hand-authored prose that never
consults the generator, and the self-test checks one hand-typed list
against another - structurally incapable of failing for the reason the
gate refused v5@w1230. fits() must become DERIVED - from bake evidence
(per-width stamps) or the recorded-parts + bounds-table envelope.

## Scale hazards (1,000+ buildings)

- Two bake paths with unequal truth; schedule pressure routes everything
  through the fast one - which is the donor-blind one. The bounds table
  equalizes them.
- Per-instance material overrides on shared meshes defeat batching at
  1,000 (fine at 16). MID pooling or per-instance data, later.
- The width ladder lives in three places; recipes should declare ladder
  NAMES with membership self-tests.
- Tier dicts are open flag soup via spec.get with silent fallthrough;
  near-synonyms already exist (mull_step vs mullion_step, both consumed).
  A KNOWN_KEYS registry asserted in recipes._selftest is cheap at 32
  recipes and expensive at 64.
