# Real estate office — tier 0 build spec

Derived from the owner's design reference, 2026-08-31. Declaration lives in
`Docs/COREBUILDINGS_DECLARATIONS.md` §2; reference policy is `CANON.md`
governance rule 6 — **this is a design reference, not canon**, and it shapes
this building's geometry only.

Tags: **[REF]** read off the reference · **[PROP]** my proposal, correct freely
· **[OWNER]** needs your call before it can be built.

## Provenance, and the one thing we are not copying

The reference is a photograph of a real estate office of an existing firm,
supplied watermarked. **We are taking the TYPOLOGY, not the identity.** The
sign reads **ELLO**, in the same spirit of letterform — bold condensed sans,
white on a dark board with a white keyline. No real company's name, logo,
colourway-as-brand, or door plate is reproduced. Written down so nobody later
"restores" the original wording from the reference.

**[OWNER]** Please drop the image at `Docs/refs/office/t0_reference.jpg` so it
sits with the declaration; I cannot write a pasted image to disk.

## What the reference actually shows

A **gable-end-on cottage** — and that is the whole reason this is not a street
building. Everything else follows from the end-on gable:

- Steep gable presented to the street, **~45–48°** pitch, with dark barge
  boards standing proud of the wall face on both rakes. **[REF]**
- White horizontal weatherboard (shiplap) cladding, board lines legible.
  **[REF]**
- A **sign board** high on the gable face: dark panel, white keyline inset
  from its edge, bold condensed sans in white. **[REF]**
- Below it a small **hooded plaque** — a date tablet under its own little
  canopy. **[REF]**
- **Two display windows with segmental-arched heads**, dark frames, flanking a
  central door. The arch is the detail that keeps this from reading as a shed.
  **[REF]**
- Behind the glass, a **grid of listing cards** — roughly 3 rows × 4–5
  columns of small pale rectangles. This is "trade visible outside" surviving
  from the earlier storefront soul into the house form. **[REF]**
- Central **panelled door**, dark, with a small sign panel and a brass knob.
  **[REF]**
- **Panelled aprons** below each window: a recessed rectangular panel in the
  white boarding. **[REF]**
- A **raised deck** with a timber walking surface, dark edge fascia, and one
  step down to the ground. **[REF]**

Not carried over: the security cameras on the gable corners, and the
sandwich-board at the kerb. Both are real-world fittings that would read as
clutter at model scale. **[PROP]**

## Proportions, which are the reliable part of a photograph

A photo gives ratios honestly and absolute size only by assumption, so the
ratios are stated first and one scale anchor is a decision:

| | as a fraction of frontage |
|---|---|
| eaves height | 0.60 |
| apex height | 1.15 |
| each window, width | 0.30 |
| door, width | 0.17 |
| sign board, width | 0.42 |

**Scale anchor [PROP]: frontage = 620 uu (6.2 m).** Everything below falls out
of it, and the door lands at 105 × 210 — a correct 2:1 door, which is the check
that the anchor is sane.

    frontage        620        eaves           372
    apex            713        pitch           47 deg
    window          186 w x 240 h (segmental head, rise 40)
    door            105 w x 210 h
    sign board      260 w x  62 h, centred, head at 560
    deck            +36 above grade, one step, 60 deep beyond the face
    depth           780   [PROP - a front-on photo cannot show depth]

## Yard, setback and parcel — the owner's brief, not the reference

The reference building stands on gravel with no yard. **The owner's brief adds
one**, and it is what makes this a house rather than a shopfront:

- **Set back from the road**, in a **fenced yard**, with **a big tree** and
  **flowers and landscaping**. **[REF-owner]**
- **Parcel [PROP]: 2050 uu** (5 × 410, the catalogue's quantum). At 620 wide
  the t0 building claims 30% of its frontage — deliberate, since it grows into
  the parcel across four tiers.
- **Setback [PROP]: 520 uu** from the frontage line — enough to stand a tree
  and a planting bed in front of the building rather than beside it.
- **Fence [PROP]** on the frontage line, low, white, with a gate on the path
  axis. The reference does show a low white fence running off to the left, so
  this is in the building's own language.

**GATE-05 does not object.** It checks only that a model does not EXCEED its
parcel — each side within tolerance, depth within +oversail — and has no fill
requirement. A small building deliberately under-filling a large lot passes.
Checked in `modelgate.py` rather than assumed, because a fill rule here would
have forced the yard out of the design.

## Parts and materials

Role prefixes bind materials automatically through `rolemap.py`, so parts are
named for their role:

| part | role prefix | material | note |
|---|---|---|---|
| weatherboard walls | `Wall_` | **needs white** | `MI_dist_bone` is nearest |
| barge boards, fascia, window frames, door | `Trim_`/`Frame_` | **needs navy** | `MI_dist_slate` is nearest |
| roof planes | `Roof_` | **needs blue** | the declared blue roof |
| display glazing | `Glass_` | `MI_glass_ink` | reads near-black in the reference |
| listing cards | `Frame_` | `MI_card_*` | the `_2S` variants exist |
| deck boards, step | `Timber_` | `MI_wood` | |
| door knob, plaque | `Rail_` | `MI_dark_metal` | brass is not in the library |
| lawn | `Grass_` | `MI_grass` | |
| tree canopy | `Leaf_` | `MI_leaf_card` / `_b` | |
| flowers | `Bloom_` | `MI_bloom_warm` / `_cool` | |
| beds | `Planter_` | `MI_planter` | |
| path | `Gravel_` | `MI_gravel` | |

**[OWNER] Three materials do not exist: white, navy, and the blue roof.** The
library has no white paint and no blue of any kind — the closest are
`MI_dist_bone` and `MI_dist_slate`. Adding instances off `M_StacktownMaster` is
cheap and in-family. Say whether to add `MI_paint_white`, `MI_paint_navy` and
`MI_roof_blue`, or to build t0 in bone/slate and judge the colour on a rendered
frame first.

## Archetype

The declaration left this **open and explicitly not `street`**, and the
reference confirms why: a gable-end-on cottage standing in its own yard is not
an articulated street elevation. Naming it is deferred until the first bake
shows which rules actually misfire — but it **must not reach a bake
undeclared**, because `of_spec` silently defaults to `street`.

Relevant: `ARCHETYPE_DECISIONS` approved a **`stores`** entry, with a scoped
signage amendment, that was never wired. This office is no longer a store, so
it does not want that entry — but the marketplace's relationship to it should
be settled when either is wired, rather than two overlapping entries appearing
by accident.

## Tiers 1–3

Deferred, per the owner: the upgrades are to be **more substantial than a
catalogue tier step** and must read as investment the player can see. The
levers this form offers, in rough order of legibility at block-hero range:
footprint growth toward the parcel, a second storey or a dormer breaking the
roof plane, the roof condition itself, a wing or porch extension, and the
yard's own treatment growing from grass to planting to hard landscaping. Not
designed here.
