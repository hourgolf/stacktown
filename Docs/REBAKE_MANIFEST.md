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

## The wave

~26 re-bakes + ~257 fresh ≈ 283 bakes ≈ 35 minutes on the fast path.
OWNER DIRECTION: pilot first (vernacular @ w820, running), full wave on
pilot verification of BakePath/Donors/DonorFails and actual donor slots.
Preconditions, all met as of 2026-08-27: canopy fix (known-answer 0.0 x5),
piece() live path working (predictive bounds check), bakers refuse to stamp
on piece_failures(), stamps carry BakePath/Donors/DonorFails.
Post-wave: re-run catalogue_audit (with its width set derived from
recipes.widths — review finding 2) and the ladder sweep once more; the
catalogue is then 548/548 baked, honestly stamped, zero unknowns.
