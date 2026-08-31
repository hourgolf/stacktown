# The re-bake manifest — restoring catalogue trust

Assembled 2026-08-27 by the coordinator from three instruments: the
un-quarantined ladder sweep (548/548, synthetic known-answer), the mode (b)
donor reconciliation (materials-based, known-answer checked against the one
mesh with measured provenance), and the on-disk stamp harvest. One re-bake
wave through the fixed pipeline (canopy fix + working piece() + provenance
stamps) clears every population below.

## Stamp provenance legend (adopt everywhere)

    BakePath/Donors/DonorFails = ''    pre-provenance stamp (old)
    DonorFails = -1                    measured-unknown: nobody has measured
                                       it; an audit may fill it in
    DonorFails = N                     measured
A stamp that guesses is worse than a stamp that abstains.

## Population 1 — falsely certified, oversail (mode a): 4 meshes

Stamped PASS, proven 752-1572 uu over their parcels by the sweep. All four
are the canopy yaw-shadowing bug, now fixed with known-answer 0.0 on all
five affected combos.

    SM_Bld_vernacular_t4_w820      752 uu over
    SM_Bld_vernacular_t4_w1230    1162 uu over
    SM_Bld_vernacular_t4_w1640    1572 uu over
    SM_Bld_vernacular5_t5_w1640   1572 uu over
    (vernacular5 t5 w1230 was refused at bake time - never on disk;
     it joins the wave as a fresh bake)

## Population 2 — donorless, proven by materials (mode b): 2 meshes

Donor records expected, ZERO donor-distinctive materials present:

    SM_Bld_tower_t6_w2460          3 donors missing (its three width
                                   siblings all carry them)
    SM_Bld_vernacular3_t5_w2050    222 donor records, all flowerbed/leaf
                                   materials absent

## Population 3 — undecidable by materials: 20 meshes → re-bake by POLICY

Every expected donor material also arises from box roles, so materials
cannot discriminate. The audit ABSTAINS rather than guesses — verified
against the known answer: SM_Bld_vernacular3_t4_w2050, live-baked and
measured donorless on 2026-08-27 (DonorFails=-1), lands here, not in
DONORS_OK. Sharpening the instrument is not worth it: 20 re-bakes cost
~2 minutes. List in the audit report JSON; includes vernacular2/3/8,
contemporary6/8, modern3 combos.

## Population 4 — verified sound: 268 meshes

DONORS_OK: donor-distinctive materials present. No action; they gain
provenance stamps naturally the next time anything re-bakes them.

## Population 5 — buildable, unbaked: ~257 combos (final list = the
post-canopy-fix ladder JSON, re-running now)

The batch backlog. Fresh bakes, provenance-stamped from birth.

## Population 6 — legacy drafts, EXCLUDED: 6 meshes

The cottage/walkup draft bakes predate the recipe ladder (spec_for does not
know them). Owner decision 2026-08-25 stands: preserved as drafts, not part
of the catalogue, not in the wave.

## S14 — the jitter divergence (recorded, deliberately unfixed)

The hand-tolerance jitter (per-floor percent-off-square) was applied by
seven direct editor calls inside the builders — the same unguarded sites
that made record mode block on the editor (fixed by `_setprops()`, sweep
1635s -> 1s). Consequence: LIVE-baked meshes carry hand tolerance,
FASTBAKED ones do not — the two paths differ in LOOK, not just metadata.
Until S14 is resolved with its own known-answer check, the wave creates two
visual populations: whichever path bakes the wave must be stated in the
pilot report, and a later uniformity pass may be needed so the catalogue
carries ONE fabrication language. Do not read visual A/Bs across
populations without checking BakePath first.

## Wave outcome (2026-08-27)

Interrupted at ~475/548 by an editor crash — and a second crash followed
after recovery. S19 RESOLVED from engine logs: both are METALRHI (GPU)
render-thread assertion failures (MetalCommandList), one before and one
after the 5.8.2 update — persistent Metal instability on this machine,
not Python, not the bake scripts, not memory (the OOM grep hit was a
false positive and the resource-exhaustion hypothesis is falsified), and
not a version regression. MITIGATION, proven in anger: the wave driver is
resumable and stops clean; the provenance stamps make the resume set
exactly computable (63 remaining derived from BakePath after crash 1,
finished in 153s, 0 failures). For long batches: viewport non-realtime —
the fault is the render thread and a fastbake needs no viewport. Post-update verification before
resuming: donor bounds re-measured and diffed — 107 meshes, zero changed;
piece() composite re-verified under 5.8.2; .mcp_sid cleared (the documented
restart trap). No corruption: the wave driver stops clean against a dead
bridge. State: 536 baked, ALL Gate=PASS, DonorFails=0 counted on all
provenance-stamped; BakePath 530 fastbake + 6 pre-provenance. street.py
re-run, 0 broken references (S17 handled).

FALSELY-CERTIFIED ADDITION (S18): the 6 pre-provenance contemporary6
assets. They passed the gate only because their donors were MISSING —
box-only depth 961 fits, real depth with donors 1107 refuses. Untrusted
until contemporary6 is fixed and they re-bake. The remaining 18
contemporary6 combos are outstanding BY DESIGN, not omission.

## MILESTONE — 548 of 548 (2026-08-27)

Every declared combination baked, gated, provenance-stamped: BakePath
fastbake x548, Gate PASS x548, DonorFails=0 counted x548, two-axis sweep
548/548 with known-answer cleared on both axes, street references intact.
THE FALSELY-CERTIFIED LIST IS CLOSED - the 6 pre-provenance contemporary6
assets are re-baked and stamped.

contemporary6's root cause: never too deep - a donor scaled on the WRONG
AXIS (height-indexed scale on a wide flat ground-cover card left a 236x227
footprint in a 22-uu bed; random yaw swung the diagonal to 328). Fixed
with a fit donor plus fit_scale() (height target under a plan budget, so
the class cannot recur silently). The axis lesson twice in one day: once
in the instrument, once in the generator. S21 fixed alongside (jitter
bounded by PROJECTED cost, budget 2.0 uu against deco6's 3-uu margin).

S20 CLOSED (coordinator, 2026-08-27). The parcel-frame contract landed in
both suppliers together: as_snapshot composes every corner through its
parent actor's transform (corners BEFORE the AABB - an AABB-of-AABB
over-bounds and deco6 holds a 3 uu margin by design) and subtracts a
declared stage; gate_run subtracts job['stage'] from the world snapshot,
which also revives GATE-10's dead exemption; bake_catalogue declares its
stage in the gate job. Three-plant self-test (identity, planted jittered
actor - whose first version proved nothing and failed honestly, sign
matters - and stage subtraction) wired to run before any gate use.
Catalogue-scale verification: ALL 548 combos re-judged through the fixed
record path - 548 PASS, 0 FAIL, in full agreement with the wave's stamps
and the two-axis sweep. modelgate rule bodies untouched, as predicted.

Original open note, for the record: S20 WAS (coordinator's): the record-path gate (as_snapshot)
judges in ACTOR-LOCAL frame and never composes the actor transform where
S14's jitter now lives - deco6 reads 867 in gate frame, 887 in world.
Mitigation in force: the two-axis sweep COMPOSES actor rotation, so the
full 548 has independent correct-frame validation. The fix is a
parcel-frame contract: as_snapshot composes actor loc/rot (records stage
at origin, so composition IS the parcel frame); the live path subtracts
its stage origin - which also revives GATE-10's dead exemption (review
finding 3). Lands with a planted jittered-actor known answer, verified by
sweep agreement across the catalogue.

## Post-wave reconciliation — FINAL (2026-08-27)

Mode (b) re-run over the harvested 542 assets:
  DONORLESS: 0        (both former hits healed - vernacular3_t5_w2050 now
                       carries its 222 donors, tower_t6_w2460 its 3)
  DONORS_OK: 503      UNDECIDABLE: 33      legacy EMIT_FAIL: 6 (by design)
  Provenance: 530 BakePath=fastbake, ALL DonorFails=0 COUNTED, zero
  contradictions; 12 pre-provenance ('') = 6 contemporary6 + 6 legacy.

A REGISTERED PREDICTION FAILED, recorded per the doctrine: UNDECIDABLE was
expected to collapse once donors carried roles. It did not (20 -> 33,
tracking catalogue growth) - because roles changed NAMES, not MATERIALS
(zero-repaint was the requirement), and material-overlap ambiguity is
structural to material-based auditing. The resolution is better than the
prediction: for provenance-stamped meshes, BakePath + counted DonorFails
IS the donor evidence, superseding material inference. Mode (b) was the
instrument for the unprovenanced past; provenance retires it going
forward.

The 6 pre-provenance contemporary6 assets clarified: they are NOT
donorless - three even show donor materials. They are DEPTH-cheats:
fastbaked when the fast gate was donor-blind (review finding 1), so their
depth was judged box-only. S18's falsely-certified listing stands, for the
corrected reason.

REMAINING to the honest-catalogue milestone: the Y axis in the ladder
sweep, the contemporary6 depth fix, its 18 bakes + 6 re-bakes. Then the
milestone commit.

## The wave as RUN (2026-08-27, supersedes the plan below)

ALL 548 through FASTBAKE, ~63 min at 6.9s/mesh. Why the change: the live
pilot passed every number and FAILED the visual - the live merge drops
masked slots (leaf cards -> dark quads; see HANDOFF traps). S14 resolved
first (hand tolerance folded into recorded actor transforms, ladder
regression clean 548/548), so fastbake now carries the jitter and uniform
BakePath=fastbake provenance beats a mixed population. 8-mesh re-pilot:
8/8 PASS, DonorFails counted 0, leaf slots present, visuals confirmed by
eye. POST-WAVE SEQUENCE: (1) street.py re-run FIRST - S17 nulls every
placed ST_ actor - before any capture; (2) catalogue_audit (CUT now derived
from recipes.widths); (3) coordinator re-runs mode (b) - expect UNDECIDABLE
to collapse and DONORLESS to zero; (4) final ladder sweep; (5) commit the
honest-catalogue milestone.

## The wave (original plan, for the record)

~26 re-bakes + ~257 fresh ≈ 283 bakes ≈ 35 minutes on the fast path.
OWNER DIRECTION: pilot first (vernacular @ w820, running), full wave on
pilot verification of BakePath/Donors/DonorFails and actual donor slots.
Preconditions, all met as of 2026-08-27: canopy fix (known-answer 0.0 x5),
piece() live path working (predictive bounds check), bakers refuse to stamp
on piece_failures(), stamps carry BakePath/Donors/DonorFails.
Post-wave: re-run catalogue_audit (with its width set derived from
recipes.widths — review finding 2) and the ladder sweep once more; the
catalogue is then 548/548 baked, honestly stamped, zero unknowns.
