# Donor meshes: the vetting rule

**No donor mesh enters a building until it has been rendered and looked at.**

Not measured. Not counted. Looked at. `Content/Python/donorsheet.py` puts every
piece in `avkit.PIECES` on a plinth of our own geometry, on lit ground in the
sandbox, and `dontiles.py` crops one labelled tile per piece by projecting its
known world position — so nobody has to squint at a row of blobs and guess
which is which.

## Why this rule exists

This project has now picked the wrong asset by name three times:

| Picked | Because the name said | What it actually was |
|---|---|---|
| `MI_precast_buff` | "precast" sounds like gravel | identical to concrete; the gravel was invisible |
| `SM_roofStand_donut` | "roof stand" sounds like rooftop plant | a stand carrying a **giant donut advert**, sitting in the folder beside `SM_billboard_Donuts_01`. It shipped on the crown of all three towers, where it read as a car tyre |
| `SM_shopAwing_01` | "shop awning" | a market **stall** canopy on four legs that reach the ground. Mounted on a wall its legs hang in mid-air |

A name is not a measurement, and a measurement is not a picture. The donut was
*correctly measured* at 155 x 439 x 543 and *correctly counted* at 328
triangles. Both numbers were in the survey. Neither number says "donut".

## What the sheet also catches

Running it the first time, before any tile was cropped:

- `awning`, `canopy`, `blind` **did not exist at the paths recorded for them** —
  they had been written into `avkit` from a survey without loading one of them.
  Two were real meshes in a different folder; the third is interior dressing.
- `drainpipe_end` was recorded 27 uu wide and measures 47.

The sheet asserts declared size against measured size on every run, so
`avkit`'s own numbers stay honest.

## Rejections are recorded, not deleted

`avkit.REJECTED` keeps the path and the reason for anything thrown out, and a
self-test asserts none of them is reachable through `PIECES`. Deleting a bad
entry just means the next pass re-picks it from the same folder listing for the
same plausible-sounding reason.

A rejection must name what the mesh **is** — "a stand carrying a giant donut
advert", "an 8-triangle cone". A rejection that says a mesh "does not render
properly" is describing our pipeline, not the mesh, and belongs in a bug report
instead. That distinction is exactly what the foliage section below got wrong.

## Boxes are allowed to win

Two donor "awnings" were rendered and both were rejected on what they *are*:
one is a legged stall, the other a slatted louvre that becomes a knife edge at
shopfront size. The canopy went back to two boxes and a painted fascia, which
is what a modelmaker cuts from card anyway.

The fabrication rule cuts both ways: a donor earns its place by doing something
card cannot — a strapped water tank, a lattice mast, a drainpipe shoe, a plant.
It does not earn its place by being a donor.

## CORRECTED: donor foliage binds PER MATERIAL SLOT

**This section previously claimed "alpha-masked foliage does not survive the
fastbake merge". That was wrong, and it was wrong in the most expensive way: a
defect of mine written down as a property of the engine.**

What actually happened: `fastbake` appended every donor mesh with a *single*
material —

```python
GSE.append_mesh_transformed_with_materials(acc, mats, piece, [mi], [local], world)
```

A tree is not one material. `SM_tree_01` carries `testtrunk_01` (bark) and
`testleaf_01` / `testleaf_02` (alpha-masked leaf cards). Give every slot the
same opaque material and the leaf cards render as solid dark quads — which is
exactly what shipped, and what I mistook for the merge destroying the mask.

The project had already solved this and I did not look:

- `mk_leaf_mi.py` builds `MI_leaf_card` / `MI_leaf_card_b` on
  `M_StacktownMaster_Masked`, carrying the pack's **own** leaf textures
  (`T_leaf_01a`, `T_leaf_02`) as the opacity mask.
- `step_foliage.py` bound those **by material slot name** — but only on the
  level sweep, so the bake path could not see the vocabulary.

The fix moves that vocabulary to `rolemap.SLOT` / `rolemap.material_for_slot()`
— one resolver, the same reason `ROLES` lives there — and `fastbake` now builds
a material list per slot. `step_foliage` imports it instead of keeping a copy.

`SM_bush_01` was broken by the same bug and had been kept deliberately small to
hide the damage. It renders properly now. So do the trees, at any scale.

### What this cost, and the lesson

Two workarounds were built on the false finding and then thrown away: trees
made of stacked `SM_grassVerticalSingle` clusters on a box armature, and
shrubs scaled down until the artefact stopped showing. Both were reasonable
responses to the finding. The finding was the problem.

**Before recording that an engine or a pipeline cannot do something, check
whether this repository already does it.** `grep` for the capability first.
The evidence here — a material binding, a slot vocabulary, and a working city
full of trees — was on disk the whole time, and the owner knew it: the
correction came from them asking why the city's trees could not simply be
reused.

## SOLVED: the roof was inside the core

The long-running "the lawn renders as warm paper whatever material it carries"
was never a material fault. **`cores.bands_for` filled the building solid to
`ztop + parapet + OVER_Z`** — above the parapet — so the entire roof void was
inside the core:

| part | z | |
|---|---|---|
| core band | 0 – **1564** | |
| `Roof_Deck` | 1452 – 1460 | inside the core |
| `Timber_Deck` | 1460 – 1469 | inside the core |
| `Grass_Lawn` | 1469 – 1559 | **inside the core** |

So the "roof" every building showed was the core's **top face wearing the wall
material** — which is why roofs took the building's colour, why `roofmat` never
appeared, and why the lawn was invisible at 5, 30 and 90 uu but abruptly
correct at 200, where its top cleared 1564.

`cores.core_top()` now reports the cap, and `open_roof` on a spec stops the
core at the roof line. A style that sets it must close its own roof void —
`build_vernacular` gained a rear parapet, which had never existed because the
core was hiding its absence.

### Why it took so long

Every check I ran was sound and every one asked the wrong question:

- **"Enumerate every box over the lawn"** — I enumerated `genbuild`'s
  *recording*. The core is not in it; `preview.py` adds it afterwards. The
  query was honest and the answer was "nothing covers it".
- **The magenta test** proved the lawn was not in the image. Correct, and I
  read it as "not wearing the material" rather than "not visible".
- **Falsifying edge wear, material, coincident faces, the chamfer, Lumen and
  warm bounce** — all genuinely eliminated, and none of them was ever a
  candidate, because the object was buried.
- Two pixel probes sampled the facade and the backdrop instead of the roof
  and returned confident numbers about the wrong surface.

The tell was in the data the whole time: green at 200 uu, tan at 90. A
threshold that sharp is an *occlusion boundary*, not a shading effect, and I
treated it as a curiosity instead of the measurement it was.

