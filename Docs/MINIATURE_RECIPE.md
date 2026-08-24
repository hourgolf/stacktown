# The Miniature Recipe

**Derived 2026-08-23 from Stage 0 and Stage 1, both measured in this project.**
This is the specification the gate asks for on passing: reveal depths, material
parameters, light rig, camera, exposure. Every number here was measured, not
assumed. Where a number was assumed and turned out wrong, that is recorded too,
because the wrong ones cost the most time.

---

## The rule that governs every other number

**A feature must subtend roughly 0.4% of frame width to read.**

Everything else follows from this. Required depth is a function of camera
distance, not an absolute, and this is the single most transferable finding in
the project.

| Framing | Distance | Scale | 250 mm reads as |
|---|---|---|---|
| Stage 0 — three bays fill frame | ~24 m | 2.616 px/uu | ~13 px, clearly |
| Stage 1 — building fills 60% height | ~95 m | 0.671 px/uu | ~3.5 px, barely |

The consequence, which is not obvious: **at building scale, per-window recess
cannot carry the reveal.** It has to be carried by metre-scale features.

| Feature | Reads at 95 m |
|---|---|
| 250 mm window recess | 3.5 px — weak |
| 600 mm floor-band offset | 8.4 px — reads |
| 1 m band offset | 13.9 px — reads well |
| 1.5 m canopy | 20.9 px — strong |

## Geometry

| Parameter | Value | Note |
|---|---|---|
| Window recess | 250 mm | at bay framing. 75 mm is a hairline and effectively vanishes |
| Sill | 40 mm proud, 60 mm thick | its FRONT face dominates the near read, and is independent of recess |
| Spandrel recess | 40 mm | the secondary plane that gives the layered read |
| Floor-band offset | 550–680 mm, uneven | the primary depth carrier at building scale |
| Canopy projection | 2.2 m | 1.5 m read as only a ~20-level tonal step; the shadow it throws is what sells it |
| Edge chamfer | 40 mm | 2.5 mm was wrong absolutely AND proportionally. A 300 mm facade standing in for ~1 mm card puts this near 1:300, where a crushed cut edge is tens of mm. 40 mm reads ~11 px at 9 m and 0.27 px at the hero — visible when you walk up, invisible before |

**Never put a variant on the camera axis.** Its jamb reveal is zero by
construction. This alone made the first three-bay comparison unrankable.

## Hand-made tolerance

**Model tolerances, not building tolerances.** The reference model's stacked
sections are misaligned by 1–2% of its width. Applying real construction
accuracy (0.15–0.4%) is invisible and is part of what makes a build read as
machined.

  Floor sections   100–250 mm lateral offset, 0.7–1.1 deg yaw, 0.5–0.9 deg roll
  Fitted elements  1.3–1.9 deg (canopy, balcony, fire escape)

## Materials

One master, instanced per role. Do not add a second master.

| | Painted styrene (original) | **Printed card (correct for this direction)** |
|---|---|---|
| Roughness band | 0.35–0.55 | **0.62–0.80** |
| Specular | 0.50 | **0.20** |

Roughness and specular are among the very few material properties that still
read at 95 m. Keep the band NARROW (~0.18 wide) — that rule holds regardless of
which material you are tuning for.

  Glass          0.055–0.105 rough, spec 0.55, opacity 0.42
                 Below ~0.02 it mirrors the environment and hides the interior.
                 The spec's "acrylic, not optical glass" is load-bearing.
  Card albedo    warm off-white 0.70/0.67/0.62 — pure neutral white reads as
                 painted plaster
  Base           kraft 0.43/0.34/0.21 — the strongest single "this is a model
                 sitting on card" cue available
  Micro-normal   tileable paper fibre, world-projected XZ, one 512 px tile per
                 20 uu = 0.39 mm/texel

**No large-scale albedo variation.** Uniform in colour, varied in sheen and at
edges. This is the trap and it stays a trap.

## Fabrication marks

  Edge wear     no curvature data on these meshes, but the geometry is
                axis-aligned boxes with 45 deg chamfers, so the world normal IS
                a curvature proxy: max(|n|) = 1.0 flat, ~0.707 chamfer, ~0.577
                corner. wear = saturate((1 - max(|n|)) / 0.30), albedo lift 1.42
  Edge chamfer  40 mm, not 2.5 mm - see the correction under Geometry
  Panel seams   VERTICAL ONLY, spacing 380 uu, width 6 uu, darken ceiling
                0.86-0.90, card roles only
  Glue bead     12 uu section, rough 0.34-0.46, spec 0.34, overlapping runs.
                Radius must VARY along the length - a constant section reads as
                a rail whatever it is made of
  Peeled facing tapering sheet AT a cut edge - never a box, never mid-face
  Dent          boolean subtraction, GeometryScripting, flat normals

**A regular XZ seam grid reads as cladding panels on a building.** This is the
single most useful thing learned about seams. Folding both world X and world Z
into the seam profile and combining with Max is the obvious implementation and
it produces bathroom tile. Softening it does not help; it stays a grid.

Two things fix it. Drop the horizontal set entirely - floor-band mouldings are
geometry, throw real shadows, and already carry the horizontal division. And
make the spacing irregular: offset world X by sin(2*pi*X/900) * 55 before the
frac, which keeps every line perfectly vertical because the offset depends on X
alone. Vary joint strength with a second sine (period 1700, range 0.36-1.00) so
the joints are not all the same weight.

Seams belong on card only. On the backdrop and ground - which are the room, not
the model - they are immediately readable as tiling.

Depth check: at the hero, joints measured 34 levels below a detrended local
baseline against a per-pixel grain floor of sd 4.8. Detrend before judging a
seam present or absent; the facade's own lighting falloff swings wider than any
seam, and a raw column mean will tell you a working feature is missing.

## Light rig

  Key    Rect, 4500 K, 45 deg off camera axis in plan, 35 deg elevation
  Fill   Rect, 7200 K, ~1/8 key, opposite side
  Practicals  2700–3000 K behind glazing, deliberately uneven between floors

Intensity scales with the inverse square of rig distance. Stage 0 used 300k lm
at 1830 uu; Stage 1 at 4200 uu needs 300k x (4200/1830)^2 = 1.58M. Getting this
wrong by 65% clipped the cream band courses while everything else looked fine.

**Attenuation radius must exceed the throw.** The default 1000 uu against a
1830 uu rig distance rendered the entire first scene black.

## Camera and exposure

  70 mm on a 36 x 24 full-frame back    -12 deg pitch, looking down
  Fixed manual exposure, EV100 6.91     ISO 800, f/4, 1/60
  Bloom, DOF, motion blur               OFF

Looking down is the strongest free miniature cue and the elevated frame was the
most convincing of the five shown at the cold read.

## Optical signature

Not banned by the gate, which names only DOF, bloom and motion blur. These are
evidence a camera existed rather than flattery.

  Film grain   sd 4.8 measured on a flat patch. Response is strongly
               non-linear: intensity 0.45 gave sd 0.93 (imperceptible),
               1.45 gave sd 8.89 (heavy). 1.05 is the useful setting.
  Vignette     0.42
  Fringing     0.30 — higher put visible colour on centre-frame mullions

Grain reanimates per frame and crawls in the viewport. Irrelevant for stills,
will matter for the game.

## What the recipe does NOT solve

**The illusion is object-scale, not surface-scale.** It holds while the viewer
sees the whole thing as an object on a board and breaks once they are close
enough to read one surface. Everything above is satisfied and the break happens
somewhere none of these numbers look: mm-scale evidence of making — cut marks,
glue, crushed edges, fibre lifting at a corner.

Edge wear, a 40 mm chamfer and vertical panel seams are now built and close
part of it. The 9 m close-up still shows a flat, featureless expanse of wall
between windows, and seams are sparse by design at that range (frame width
463 uu against 380 uu spacing puts at most one joint in frame), so they are not
the answer to it. What is still missing there is glue, deliberate small damage,
and fibre lifting at a corner.

Glue and peeled facing are now built. Two rules came out of them and both are
about SHAPE, not material:

  A chamfered box cannot be a lifted edge. It has no taper, so it reads as a
  tab stuck to the wall at any thickness. A peel needs to go to nothing where
  it is still attached, and it needs to be at an actual cut edge.

  Additive geometry cannot make a dent. A block at a corner reads as an extra
  piece, not a crushed one. Deliberate damage needs subtractive geometry.
  Now built: two scaled spheres subtracted at a corner, centred mostly OUTSIDE
  the surface so only their lower cap enters.

  SIZE THE TOOL AGAINST THE MATERIAL, NOT THE OBJECT. The parapet cap is 1100
  long and 12 thick. A radius-21 sphere is modest against 1100 and catastrophic
  against 12 - it cut straight through. Radius 9 removes 2 uu of 12.

  Keep normals FLAT after any boolean. recompute_normals averages across the
  box faces and turns crisp card into a soft ribbon; card has hard edges.

That is the next question. It is not a gate failure.
