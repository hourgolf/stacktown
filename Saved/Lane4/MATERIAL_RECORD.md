# Lane 4 — master material and surface treatment

Worked 2026-08-24 against `/Game/Maps/Stage2_Block`. Three items were assigned.
Items 1 and 3 are done. Item 2 is done and the owner has approved the look.

A fourth thing was found on the way in and is the most urgent line in this file,
so it goes first.

---

## 0. `PaperNormalAmount` had been silently disconnected — FIXED

`triplanar.py` rebuilt `MP_Normal` as a vertex-normal-weighted sum of three
`PaperNormal` samples and did not carry the amplitude control across. The
parameter survived in the graph as an **orphan expression**. Every card
instance still set it to 2.0 and it had reached nothing since that script ran.

This directly undid the Stage 2 result *"Set to amplitude 2.0 on all card
roles, which makes the fibre plainly visible at the player zoom."* That was
true when it was measured. `triplanar.py` ran afterwards and it stopped being
true, with nothing to say so.

Measured on a flat pier face of the Narrow building, high-pass SD, idle
repeatability sd 0.034:

| | before the fix | after the fix |
|---|---|---|
| `PaperNormalAmount` 2.0 → 0.0 | −0.046 = **1.4 sigma** | −3.149 = **92.6 sigma** |
| `PaperNormalAmount` 2.0 → 8.0 | −0.011 = **0.3 sigma** | +5.143 = **151.3 sigma** |
| `PaperTiling` 0.05 → 0.40 (control) | −1.313 = 38.6 sigma | −3.061 = 90.0 sigma |
| `PaperTiling` 0.05 → 0.02 (control) | +3.427 = 100.8 sigma | +4.738 = 139.3 sigma |

`PaperTiling` feeds the *same three samplers*, so a live tiling and a dead
amplitude isolates the amplitude input specifically rather than the paper chain
at large. One variable moved between the two columns: the material graph.

Fixed in `Content/Python/fix_amp.py` by lerping from a flat tangent normal
`(0,0,1)` to the triplanar sum by `PaperNormalAmount` — which is the construct
`M_StacktownMaster_2S` still carries, so the two masters agree again.

**`M_StacktownMaster_2S` never got the triplanar rewrite at all.** Fixed in a
later pass the same day — see section 4. And it is *not* used by the vehicle
and pedestrian shells, which is what I assumed here and was wrong about; see
section 5.

---

## 1. Edge wear now reads baked curvature — DONE

    BEFORE   wear = saturate((1 - max|PixelNormalWS|) / EdgeWearWidth)
    AFTER    wear = saturate((1 - VertexColor.R)      / EdgeWearWidth)

Only the source of the term changed. The OneMinus / Divide / Saturate chain and
`EdgeWearWidth` are reused untouched, so every instance value keeps its
meaning, and the edit is one wire.

### The defect, shown rather than argued

`EdgeWearLift` is a multiplier on BaseColour inside the worn side of a Lerp, so
driving it to 8.0 paints the wear mask onto the surface in white. Rendered on
the material's own preview **sphere** — an object with no edges at all:

- `sphere_wear_OLD_proxy.jpg` — almost the entire sphere is painted. Only six
  small spots survive, at ±X, ±Y and ±Z where one normal component approaches 1.
- `sphere_wear_NEW_curvature.jpg` — clean, indistinguishable from unworn.

At the authored `EdgeWearLift` 1.42 the old term was therefore applying a ~1.4x
albedo lift across most of any curved or non-axis-aligned surface. That is
worse than "does nothing on imported geometry" — it was doing the wrong thing
to all of it.

### What is baked

`Content/Python/curvebake.py`. A **facet** is a maximal group of triangles
joined across edges shallower than 12 degrees. A facet is a **bevel** if its
narrowest in-plane extent is at most `BAND` (6 uu) and it has at least one
convex crease on its boundary. Bevel facets are painted with a hard colour seam
so the mask cannot bleed onto the faces they join.

Strength `s = 1 - dot(n1, n2)` across the crease, stored as `R = 1 - s`.

**`R = 1 - s` and not `s`, deliberately.** An unbaked mesh keeps whatever vertex
colour it already had, and white is the common case. Under this convention
white reads as "no crease", so a mesh nobody has baked looks exactly as it does
today instead of turning fully worn. Meshes carrying black vertex colour do
exist here — `SM_Baked_Sedan` is one — and those would read as fully worn, so
they are reported rather than assumed.

A 45-degree chamfer has `s = 0.293`, so with `EdgeWearWidth` 0.30 it lands on
**0.977** — which is what the old proxy computed for the same chamfer.
Geometry the old term got right does not move; only the cases it got wrong do.

### Results

104 meshes baked, **zero problems**: material slot names preserved on every
one, triangle counts unchanged, winding self-check passed on every one.

Painted area, which is the meaningful number — triangle *count* is a bad proxy,
since a building is mostly small mullion boxes by count and mostly wall by area:

| mesh | what it is | painted area |
|---|---|---|
| `SM_Cw_456p0_3p0_332p0` | a large glass pane | **2.1%** |
| `SM_Cw_52p0_60p0_296p0` | a pier | **12.8%** |
| `SM_Bake_Narrow` | a whole baked building | **10.9%** |
| `SM_Cw_6p0_7p0_202p0` | a 60 x 70 mm mullion | **100%** |

The mullion at 100% is correct, not a failure: a 60 mm stick of card is all
edge.

### It works on imported geometry — read-only analysis

| mesh | painted area | note |
|---|---|---|
| `SM_window_01` | **15.1%** | the old proxy gave this essentially nothing |
| `SM_shopFront_01` | 9.8% | |
| `SM_Water_Tank_01` | 11.2% | a **cylinder** — the old proxy gave it 0.98 at its 45-degree points |
| `SM_wall_01` | **0.0%** | a flat 4-triangle quad. No edges, no wear. Correct. |
| `SM_tree_01` | 0.7% | leaf cards are flat |

**Nothing was written to any of these.** They are licensed marketplace content
that is not even in this repository, and `AGENTS.md` routes donor assets through
`Content/Stacktown/Source/<provider>/` before they are modified. `curvebake.py`
refuses to write outside `/Game/Stacktown/` for the same reason — the level also
contains 454 components on `/Engine/BasicShapes/Cube`, and baking into engine
content would be worse still.

**Open, and it is an asset-intake decision rather than a material one:** the
Assetsville tileset gets no wear until those meshes are normalised into
`Content/Stacktown/Source/` and baked. The measurements above say what it is
worth.

### Wear is live, and it lands where it should

Diffing wear-off against wear-on at the player zoom and locating the changed
pixels — rather than trusting a scalar, which is the method that beat adjusting
by eye every time it was used in Stage 2:

    pixels moved: 445,346 of 3,153,996 = 14.12% of frame
    horizontal run lengths: median 1 px, p90 10 px, max 1318 px
    (frame is 2218 px wide; a painted FACE would run to the hundreds)

Thin bands, not faces. `wearmask_OLD_proxy.jpg` vs `wearmask_NEW_curvature.jpg`
is the same comparison by eye.

---

## 2. Masked foliage variant — DONE, look approved

`M_StacktownMaster_Masked`, plus `MI_leaf_card` and `MI_leaf_card_b`.

Duplicated from the master rather than authored fresh, so the card band, the
seam chain, the triplanar paper and the curvature wear are identical by
construction. Blend mode `BLEND_MASKED`, two-sided, clip 0.33, with a `LeafMask`
texture parameter driving `MP_OpacityMask` from the donor pack's own leaf alpha.

`MASTER_MATERIAL_SPEC` forbids a second master "just for this one thing", and
that rule is about architecture: variation between architectural surfaces must
come from instance parameters. **Blend mode is not an instance parameter in
Unreal.** An alpha-tested surface cannot be expressed as an instance of an
opaque master however it is authored, which is the same reason
`M_StacktownMaster_2S` exists. This is a third blend mode of one material, not
a second look.

Wear is switched off on the leaf instances (`EdgeWearLift` 1.0) and seams too
(`SeamDarken` 1.0). The tree meshes are donor content that has not been
curvature-baked; `SM_tree_01` carries `(1,1,1)` and `SM_tree_03` carries
`(1,0,0)`. Both happen to have `R = 1` so wear would be zero anyway, but
"happens to be safe" is not a reason to leave a term reading a channel the pack
authored for its own purposes.

`Content/Python/step_foliage.py` assigns by **material slot name**
(`testleaf_01`, `testleaf_02`, `testtrunk_01`), which is how imported assets
carry role. It is reversible — `restore=True` puts the pack's materials back —
and it does not save the level.

### One correction to the brief

The brief says *"Opaque card fills the gaps between alpha-cut leaf cards and
turns a canopy into a solid cone; the asset pack's own materials give correct
leaves but clash with the diorama. Neither currently works."*

The second half is right and the first half is worth restating precisely. In
`tree_pack_material.jpg` the pack's material cuts the leaves correctly — there
is no solid cone. What it does is put an **acid yellow-green** into a muted card
palette. So the deliverable was never "make the mask work"; it was "keep their
cut, replace their fabrication", which is what the masked master does:
the shape is the pack's, the material is ours.

### A measured side effect

Same camera, same scene, only the leaf material differing:

| leaf material | frame-to-frame difference over 6 captures |
|---|---|
| pack `MI_Leaf_01a` (`MSM_SUBSURFACE`) | **8.5**, never quiets in 12 captures |
| `MI_leaf_card` (`MSM_DEFAULT_LIT`) | **3.68**, at the 3.87 noise floor |

The pack's foliage does not converge temporally at this framing; the card
version settles in three captures. Measured twice.

### The look was put to the owner and approved

Shown `tree_pack_material.jpg` against `tree_card_material.jpg`, the owner's
verdict on 2026-08-24 was that the tree reads better. Both judgement calls
inside the change therefore stand: the invented leaf greens
`(0.300, 0.420, 0.215)` / `(0.335, 0.445, 0.230)`, and the trunk moving from the
pack's `MI_matteBrown` to `MI_wood`.

**This is the owner's approval, not the gate's cold read.** `HANDOFF.md` §3
reserves the illusion question for a human who has *not* seen the project, and
the owner has. What this settles is that the change stays; the gate line is
untouched by it. Worth being precise about, because treating a favourable
signal as a gate pass is the documented way both predecessors died.

### It already generalises to the rest of the pack

Checked rather than assumed. Across the eleven meshes in
`/Game/AssetsvilleTown/Meshes/Nature`, exactly two leaf slot names exist and
they cover **every tree and the bush**:

    testleaf_01     SM_bush_01, SM_tree_01, SM_tree_02
    testleaf_02     SM_tree_03, SM_tree_04
    testtrunk_01    SM_bush_01, SM_tree_01, SM_tree_02, SM_tree_03, SM_tree_04

So `step_foliage.py` needs no change to pick up the two trees and the bush that
are not placed yet. Adding a tree costs nothing in material work, which is the
foliage equivalent of the property `HANDOFF.md` §4.2 calls the most important
scaling property in the codebase.

**One mesh is outside this and cannot be brought in safely.**
`SM_treeLowPoly_01` binds a slot called `colorPalette` that it *shares with*
`SM_background_Mountains_01`. Role-keying on that name would repaint the
backdrop mountains as foliage. It needs a per-actor override or a normalised
copy, not a slot rule.

---

## 3. `PaperDetail` traced — DONE, and it contributes almost nothing

It is the **alpha of a Lerp between `RoughMin` and `RoughMax` feeding
`MP_Roughness`, and nothing else.** It touches no other output.

Quantified two independent ways that agree:

**From the texture.** `T_PaperDetail` is 512x512, luma mean 126.76, sd 5.789,
range 107..147. As a 0-1 alpha that is 0.497 +/- 0.023, full range 0.42..0.58.
Against the authored card band `RoughMin` 0.62 / `RoughMax` 0.80:

    roughness = 0.62 + 0.18 * alpha
    mean 0.7095,  sd 0.0041,  full range 0.695 .. 0.725

**Four thousandths of roughness.** That is its entire contribution.

**From the frame.** Collapsing `RoughMin == RoughMax == 0.71` removes
`PaperDetail`'s only path to the image. High-pass SD on the pier moved
**0.1 sigma**. (Widening to 0.40/1.00 moved 40.5 sigma, so the roughness path
itself is very much alive — it is the authored 0.18 band that makes
`PaperDetail` invisible.)

So `PaperDetail` is **wired, live, and below any visible threshold by design**.
It is not a second `PaperTiling`. The narrow roughness clamp that hides it is
`MASTER_MATERIAL_SPEC`'s central instruction — *"Fabricated surfaces occupy a
much tighter roughness band than real ones"* — so this is the art direction
working, not a bug. Deleting it would cost nothing visible; widening the band to
make it show would break the clamp.

Two structural notes:

- its UVs are `WorldPosition.RB * PaperTiling` — an **XZ planar projection**,
  not the triplanar one the normal received. On a face whose normal is X the X
  coordinate does not vary, so what little it does is anisotropic. If the
  roughness band is ever widened, this needs the triplanar treatment first.
- the **`Noise` node at Scale 1** that Stage 2 flagged as untraced is an orphan
  in **both** masters. It drives nothing. That question is closed.

---

## Measurement — what went wrong before it went right

Three of my own measurements were wrong first, in the way this project keeps
recording. They are here because the numbers above are only worth anything if
the instrument is.

**The first capture after a material edit is a transient.** Two captures of an
identical scene, `PaperTiling` 0.25 on both visits, read mean 179.12 and 142.98
— a mean-abs-diff of 47.5 between two frames that should have been the same.
Taking one shot after a change and calling the difference an effect produces a
confident, entirely fabricated answer. Everything above is captured through
`Tools/measure/settle.py`, which requires **two consecutive** frames within the
noise floor before it measures.

**Whole-frame mean-abs-diff is the wrong question for surface work.** It scored
**4.1 against a 3.9 floor** on a `PaperTiling` change that is obvious at a
glance — and 43.96 on a known albedo positive control, which is exactly why the
control validated it and the real test did not. Plane-detrended patch SD missed
it too, moving 0.15 on 20.2, because a facade's structure is not a plane. The
statistic that works is high-pass SD on a flat sub-patch: idle repeatability
sd **0.034**, and it registered the same change at 38.6 sigma.

I caught this by cropping the pier and *looking at it*. The number said nothing
had happened; the two crops were plainly different.

**The winding.** `curvebake.py` reported **0 creases on a chamfered box with 48
of them**, and reported it cleanly, with no error. Unreal is left-handed and its
front faces wind clockwise, so the outward normal is `cross(c-a, b-a)`; with the
other order every normal on a closed mesh points inward and every convex edge
tests as concave.

What caught it was checking against answers known in advance. A chamfered box
must have 6 + 12 + 8 = **26 facets** and a dihedral histogram of **24 edges at
45 degrees and 24 at 35.26 degrees** — and 24 unique positions, 66 edges, 44
triangles, `V - E + F = 2`. The topology came out exactly right, which is what
localised the fault to the sign.

The self-check itself then had to be fixed twice:

- *"normals point away from the centroid"* is only true of a convex shell. It
  failed `SM_Bake_Narrow` — 136 boxes in one mesh — at 3100/5984 while the
  winding was perfectly consistent.
- *signed volume* is only meaningful on a closed mesh, and the generated
  buildings are hollow facades, so it read 1.84e9 on a mesh with no interior.
  It also compared against `GetMeshVolumeArea`'s first return value, which is
  the surface **area**, not the volume.

What survives is comparing our geometric normals against **Unreal's own** face
normals on a sample. It works on open, closed, convex and compound meshes alike
and it tests the one thing that actually went wrong.

Two more, smaller:

- **`CaptureViewport`'s `annotations` argument is required, and there is no
  `bShowActorLabels` key.** Passing one is accepted and silently ignored, and
  the capture comes back with white label boxes over the exact surfaces being
  measured. The off switch is `maxLabelDistance: 0` and `maxLabels: 0`.
- **`ObjectTools.get_properties` returns `{}` for the WHOLE call** if any
  requested name does not exist on that class. The first graph dumper reported
  every parameter in the material as nameless.

---

## Repository hygiene fixed on the way past

**`rung.sh` was not in the repository.** The only copy,
`Saved/Stage2/data/rung.sh`, `cd`s into an agent scratchpad under
`/private/tmp` belonging to a session that has ended. It therefore ran a
*different* `_guard.py` than the one in the repo — and the repo's guard had gone
stale, still naming only `Stage1_Building`, so it would have refused every
script run against the current level.

The guard is the thing standing between several editors on this machine and a
script writing into the wrong one. Having its real copy live in a temp directory
is the failure waiting to happen.

- `Tools/rung.sh` — resolves its own location, uses the repo's guard.
- `Content/Python/_guard.py` — now allows `Stage1_Building` and `Stage2_Block`,
  and says which are allowed when it refuses. Verified it still refuses
  `OneBuildingTest` and `/Temp/Untitled`.

---

## 4. `M_StacktownMaster_2S` brought up to the main master — DONE

Its normal was still `Lerp(flat, PaperNormal on WorldPosition.XZ,
PaperNormalAmount)` — the single-plane projection `triplanar.py` existed to
remove. `Content/Python/triplanar2s.py` rewires only the Lerp's **B** input to a
triplanar sum, leaving the amplitude Lerp exactly where it was, so the two
masters now have the identical normal chain and differ only in sidedness.

Measured on `BLD_Roof/RoofDeck`, a 1080 x 800 deck whose normal is Z, viewed
from straight above. One variable moves: the Lerp's B input is swapped between
the old single sampler — still in the graph, now orphaned — and the new sum.

| | mean abs dx | mean abs dy | ratio | patch mean |
|---|---|---|---|---|
| 2S, single-plane (pre-fix) | 3.605 | 5.893 | **1.63** | 171.6 |
| 2S, triplanar (post-fix) | 4.041 | 4.939 | **1.22** | 172.4 |
| `MI_card_ochre`, main master *(control)* | 4.023 | 4.926 | **1.22** | 172.4 |

The control is the point. `MI_card_ochre`'s master was already triplanar, so its
number is the known answer for this patch, and the fixed 2S lands on it — not
approximately, but to within 0.5% on both axes.

**This does not reproduce the 13.5x the original `triplanar.py` reported, and I
am not claiming it does.** That figure came from a block end wall at a different
framing. This patch carries other detail — chamfer wear, lighting, grain — that
both axes share and that dilutes the ratio, which is why 1.22 rather than 1.00
is the isotropic floor here. What the table supports is narrower and sufficient:
a directional bias existed, it is gone, and the result matches a surface whose
projection was already known to be correct.

### The settle threshold did not transfer between views

`settle.settled()` was not used for this test and must not be. Its floor of 4.3
was measured on the zoom view; this top-down roof view has a floor of **4.56**
and a mean that climbs about 1 per capture without ever converging. A threshold
measured somewhere else is a threshold you invented.

It does not matter here, and that is by design: anisotropy is a **within-frame**
ratio, so a slow global brightening moves both axes together and cancels. The
patch mean is in the table so the drift stays visible instead of hidden.

### Instance amplitudes aligned

The `*_2S` instances still carried `PaperNormalAmount` 0.55 — the value the main
instances were pushed off in Stage 2 for being too faint at the player zoom.
`Content/Python/align2s.py` copies each one's value from its non-2S counterpart:
rose, sage and paint_cream went 0.55 -> 2.0; frame_print stays 0.55 because its
counterpart does. Nothing on screen changes, because nothing binds them.

---

## 5. A regression I introduced, and the assumption behind it

`curvebake.py` excluded every `SM_Baked_*` mesh, and the comment I wrote into
the code gave the reason as fact: *"those are single-sided shells on
M_StacktownMaster_2S, which does not read vertex colour."*

**That is false.** Counted directly against the level:

    components bound to any *_2S material: 0

The vehicles and pedestrians are on `MI_card_rose`, `MI_card_sage`,
`MI_paint_cream`, `MI_card_ochre` — the **main** master, the one now reading
`VertexColor.R`. And six of the seven baked meshes carry **black** vertex
colour:

    SM_Baked_Sedan/Police/Truck/Ped1/Ped2/Ped3   R = 0.0  ->  wear 1.0
    SM_Baked_Pickup                              R = 1.0  ->  wear 0.0

So every car and every pedestrian in the level was rendering **fully worn** — a
1.42x albedo lift over its entire body — from the moment the wear rewire landed
until this was found. `vehicle_wear_regression.jpg` against
`vehicle_wear_fixed.jpg`: the bonnet and grille are washed flat in the first and
read again in the second. Whole-frame difference 7.76 against a 3.87 floor.

Fixed by baking the seven meshes, which were always eligible — they live under
`/Game/Stacktown/`:

| mesh | painted area |
|---|---|
| `SM_Baked_Sedan` | 20.8% |
| `SM_Baked_Pickup` | 13.5% |
| `SM_Baked_Police` | 21.8% |
| `SM_Baked_Truck` | 29.7% |
| `SM_Baked_Ped1/2/3` | 53.7% / 40.9% / 52.6% |

**What actually went wrong.** The Stage 2 record says the vehicles *"need a
two-sided variant of the master for shell geometry."* I read a stated need as a
completed fact, wrote it into a code comment, and used it to exclude seven
meshes from a bake — without once counting what the level was actually using. It
took one query to disprove and I ran that query only because a later task
brought me back to the 2S master. The convention that saved this from being
worse is `R = 1 - s`: had the wear been stored the other way round, every
*unbaked* mesh in the project would have failed the same way instead of just the
black-vertex ones.

### Two things this surfaced that are NOT mine

- **The two-sided fix was built and never wired.** Now wired — see section 6.
- **The pedestrians are in a T-pose.** `pedestrian_after.jpg` — arms straight
  out. The skeletal-to-static bake captured the reference pose. Pre-existing,
  plainly visible at street level, and worth someone's attention.

---

## 6. The two-sided materials are wired to the vehicles — DONE

Every `SM_Baked_*` mesh is an **open shell**: the sedan has 12,004 open border
edges against 6,064 triangles, because it came from a skeletal mesh authored to
be seen from outside only. `M_StacktownMaster` is `two_sided=False`, so binding
a card role to a shell culls its backfaces and the road shows through the
bodywork. That is defect 2 from the Stage 2 audit, unfixed since.

Three things were needed, not one:

1. **The 2S master's wear still read `PixelNormalWS`.** Wiring 2S materials onto
   curved bodywork while its wear was still the orientation proxy would have put
   the vehicles straight back into the state section 5 describes. `fix_wear.py`
   now takes a material path and was run against the 2S master first.
2. **`MI_glass_b` and `MI_interior` had no two-sided counterpart.**
   `mk_2s_missing.py` creates them by copying every override from the non-2S
   instance, so the pair differs *only* in which master it points at — verified
   by comparing the scalar dictionaries, which match.
3. `step_veh2s.py` maps each slot to its `_2S` sibling by name, so the palette
   decision stays in the non-2S instance and a vehicle recoloured later needs no
   edit here. Slot names are gone on these meshes (`Material_0`, `None`,
   `None`) because the skeletal bake drops them, so it works positionally.

14 slots bound across four vehicles, zero without a counterpart. Oblique view in
`vehicle_2s_oblique.jpg`: solid rose bodywork, no road through it, interior card
and steering wheel visible through the glazing.

### Glazing is deliberately left single-sided

This is the one interesting decision, and it was tested rather than assumed.
Both masters are `BLEND_OPAQUE`, so `MI_glass_b`'s `Opacity 0.42` does nothing.

- **Two-sided** (`vehicle_2s_opaque_glass.jpg`): the windscreen is drawn, and
  being opaque it becomes a flat dark slab that hides the whole interior.
- **Single-sided**: the outward faces are culled, the glazing renders as
  nothing, and the modelled dashboard and street beyond are visible — which
  looks like working glass but is the culling bug wearing a disguise.

Isolated on `BAKED_veh0` by reverting **only** the glass slot and leaving the
other three on 2S. Neither is glass. **Sidedness is the wrong axis for this
problem:** vehicle glazing needs a TRANSLUCENT master, which is the same
argument that justified the masked variant for foliage — blend mode is not an
instance parameter. Until that exists, single-sided is the better-looking of two
wrong answers, and it keeps the interior visible, which
`MASTER_MATERIAL_SPEC`'s glass rule explicitly asks for. `step_veh2s.py` skips
it by default; pass `{"glass": true}` to see the other one.

### The pedestrians have the identical defect and were NOT touched

`SM_Baked_Ped1/2/3` are open shells too — 4,132 open border edges on 1,784
triangles. They were left alone because the request was the vehicles. One
command does them:

    step_veh2s.py with {"prefixes": ["BAKED_ped"]}

### A trap that nearly lost the whole change

**`component.set_material()` does not mark the map package dirty.**

`get_dirty_map_packages()` came back **empty** while all four vehicles carried
unsaved material overrides. My own save helper guarded `save_current_level()` on
that check and skipped the level in silence, reporting `dirty maps: 0` as though
everything were safe. Forcing the save grew `Stage2_Block.umap` from **880,776
to 881,708 bytes**.

Caught by looking at the file's timestamp rather than believing the dirty list —
the same failure shape as every other entry in the measurement section: a check
that asked the wrong question and answered "ok".

Verified on disk afterwards, which is the bar that should have been used all
along:

    MI_card_rose_2S      in Stage2_Block.umap: yes
    MI_interior_2S       in Stage2_Block.umap: yes
    MI_frame_print_2S    in Stage2_Block.umap: yes
    MI_glass_b_2S        in Stage2_Block.umap: NO    <- correct, glazing skipped
    MI_leaf_card         in Stage2_Block.umap: yes

`Content/Python/save_level.py` now saves unconditionally and prints the file
size and timestamp either side. "Save returned True" is not evidence that
anything was written.

---

## 7. I wiped the block, and what that exposed

I ran `wipe_owned.py` as a throwaway smoke test for the guard's new `sys.path`
bootstrap. It is destructive and it saves the level, so it deleted both blocks —
187 actors down to 47. Picking the one script in the directory whose entire
purpose is deletion, to test something unrelated, is the mistake; the guard
was never the risk.

Recovered with `build_block.py` + `build_blockB.py`.
`Saved/Lane4/backup/Stage2_Block_Auto7.umap` was kept as a fallback and not
needed. The rebuild came back *better* than the autosave, because the vehicle
and foliage steps are now in the pipeline and applied themselves.

### The pipeline could not have run at all

Recovering forced the first honest test of `build_block.py`, and it was broken
four ways — all the same root cause, the toolchain living in a dead agent
scratchpad:

- **16 scripts** hardcoded `/private/tmp/.../c7b8ef13-.../scratchpad` on `sys.path`.
- **`ue.py`**, the MCP client every generator imports, existed **only** there.
  `from genbuild import build` raised `ModuleNotFoundError: No module named 'ue'`
  before a single box was placed.
- **`build_block.py` and `build_blockB.py` invoked `./rung.sh`** with
  `cwd=Content/Python`, where no such file exists.
- **step 9 called `fix6_vehmats2.py`**, which is not in the repository at all,
  so that step had been reporting FAILED on every run.

So criterion 1 of the block milestone — *"one script reproduces the block from
empty"* — recorded as **PASS**, was not true in a fresh checkout. It is now, and
the run above is the evidence.

Fixed: `Content/Python/_path.py` locates the project from its own `__file__`;
`_guard.py` puts `Content/Python` and `Tools/measure` on `sys.path` for every
guarded script, since rung.sh executes a temp copy; both build scripts resolve
`Tools/rung.sh` from the repo root. Four scripts that wrote JSON into the
scratchpad now write to `Saved/data/` — never `Content/`, which is the
DataTable-modal trap.

`build_block.py` step 4 also used `assign_roles.py`, whose wall map is
hardcoded `{'Narrow','Wide','Mid'}` — a lot that no longer exists, no block B,
no ELEV_. Switched to `step_roles.py`, which reads the city table.

---

## 8. Pedestrians removed, and the framing re-derived

**Pedestrians** are gone from the level and commented out of
`place_baked.py`, with the two things to fix before they return recorded there:
the reference-pose arms, and the open-shell material.

**The block hero was pointing at the backs of block B.** Block A's facades face
-Y and block B's face +Y; `CAM_Block` and `CAM_Hero` sit at y about -10,000
looking toward +Y, which puts them *behind* block B. Three blank rear
elevations filled the frame — `rears_blank_old_hero.jpg`. Same root cause the
Stage 3 record already logged for the lights: *"the rig was derived for a single
row facing -Y and needs re-deriving for a street."* The camera was never
re-derived either.

Two facing rows can only both be seen from **inside** the canyon, so the hero
has to look along the street — which is what Stage 3 concluded and never acted
on. `cam_street_hero.py` adds `CAM_Street_Hero` at (-3200, -860, 3400),
pitch -26, yaw 2. The downward pitch pushes the uncovered end of the board out
of frame and brings the road and both pavements in. Additive: `CAM_Block` and
`CAM_Hero` are untouched, so every earlier capture stays reproducible.

**This changes the depth budget.** At the old block hero the 0.4% threshold was
230 mm. At this one it is **41 mm at 2,000 uu, 82 mm at 4,000, 123 mm at
6,000** — window furniture now reads at the hero, where before only mass did.

---

## 9. Exposed flanks are real elevations now

`Content/Python/step_elevations.py`. Full front vocabulary at the owner's
direction: plinth, piers, a band course per floor, recessed glazing, frames,
sill and cross mullions — the same parts the street facade uses, so the role
sweep binds them for nothing.

**Where it applies is decided from the data, not by eye.** Lots tile edge to
edge and neighbours share a party wall, so an interior flank is buried and a
real terrace shows a side only at the ends of the block. Only the two end lots
qualify, on their outward face:

    Mid   east   122 boxes
    Bank  east   102 boxes
    Hall  west    82 boxes
                 306 boxes total

`city.py` now declares `abuts_low` on block A, because its low-x end runs into
the reused Stage 1 building — a level actor, not a lot. Without that the rule
would have called Narrow's west flank exposed and punched windows into a party
wall. The result agrees with an independent survey of world AABBs taken off the
level before any of this was written.

Checks after: **1,027 slots assigned, zero unresolved; geometry check PASS with
its self-check OK; no hollow facades, worst void 2.0 uu.**
`flank_corner_after.jpg` is the corner of Mid where the new flank meets the
street facade — band courses continue round, piers align, same window family.

### Two mistakes worth writing down

**Component names must be unique within an actor.** genbuild gets away with
plain names because it makes a fresh actor per floor; this elevation is one
actor for a whole flank, so reusing `Wall_Pier0` on six bands made UE silently
rename all of them to `StaticMesh0..N`. The role sweep reported **122
unresolved components** and the flank rendered with no materials. Caught by
reading the sweep's own output, which is the only reason it has one.

**The elevation has to stand PROUD of the core.** The first version put the
flank's outer face on the core face and recessed the glazing 27 uu — straight
into solid mass. The render came back a blank wall with two band courses
floating on it, because only the proud parts were outside the core. This is the
whole reason the front elevation works: the core's front is at y 62 and the
facade occupies y 0..60 in front of it. The flank is now a 60 uu slab against
the core, exactly parallel.

### Still open here

- **Stage1's west flank is still blank.** It is the fourth exposed flank, but
  Stage1 is a hand-built level actor rather than a lot, so genbuild cannot
  reach it. It needs its own pass or to be re-expressed as a lot.
- ~~Flank interiors are unlit.~~ Fixed — see section 10.
- **The rears are untouched**, per the owner's call to fix the framing instead.
  With the hero inside the canyon they no longer face any approved camera.

---

## 10. Every practical in the project was pointing at the ceiling

Reported by the owner as *"a horizontal bar of light casting upwards"*. It was
exactly that, and the cause is a trap this repository already documents.

`practicals.py` spawned every light with `unreal.Rotator(0, 90, 0)`, meaning
"yaw 90". **Rotator takes (roll, PITCH, yaw)**, so it set pitch. Measured on the
level before touching anything:

    LIGHT2_Narrow_Shop0        rot(roll 0 pitch 90 yaw 0)   forward(0.00, 0.00, 1.00)
    LIGHT2_Narrow_Interior_B0  rot(roll 0 pitch 90 yaw 0)   forward(0.00, 0.00, 1.00)
    ... all 43 identical

Forward `(0,0,1)` is straight up. Forty-three rect lights, every one aimed at
the ceiling, each reading from the street as a bright bar with a wash up the
underside of the window head. `HANDOFF.md` section 5 names this exact mistake —
*"Passing Rotator(0,90,0) for 'yaw 90' sets pitch and lays everything flat"* —
and the code did it anyway.

### What a lit window should be

Not a visible lamp. In a card model a lit window is a diffusing panel behind the
glazing: an evenly glowing rectangle with no source in view. So the practical
now sits in the void BETWEEN the glass and the interior card, aimed INWARD at
the card, with its source sized to the opening rather than to a fixture. The
card is what you see; the lamp is edge-on behind the glass and never appears.

`practicals_fixed.jpg` against the owner's screenshot: the bar and the upward
wash are gone, and the openings read as warm panels. Intensity 2310-3960 and
temperature 2750-3050 K stay randomised per window, and only 42% of rooms are
lit, so the block still reads as occupied rather than as an office block at
night.

### Aim is derived, not tabulated

Each interior card is paired with its own glass by name suffix — `Interior_B0`
with `Glass_B0`, `Interior_L2B1` with `Glass_L2B1` — and the light points along
the vector between them.

That is the whole reason this works unchanged on **block B**, which faces the
opposite way, and on the **flank elevations**, whose windows face +/-X. A table
of facing directions would have needed an entry for every one of them and a new
edit for every block added. 47 practicals placed, **0 skipped for want of a
paired glass**.

Flank interiors are now lit exactly like the facade glazing, which was the
owner's other request — `flank_lit.jpg`. 100 interior cards in the level (70
facade, 30 flank), 47 lit.

---

## 11. Block C — an island block, late-modern

Six buildings in two rows back to back, on a new street. `blockC_board.jpg`.

    block CN  origin (4150, -4050)  yaw 180   Tower / Slab / Plaza   faces +Y onto street 2
    block CS  origin (0,    -5330)  yaw   0   Annex / Court / Civic  faces -Y onto street 3

The rows meet on a party line at y -4690, so **neither rear is ever seen and
neither needs an elevation** — which is the argument for building this instead
of going back to articulate block A's backs.

    generated                6 buildings
    flank elevations         4 corners (Tower, Plaza, Annex, Civic)
    material slots           2020 assigned, ZERO unresolved
    cores                    14 segments
    practicals               93, 0 skipped
    geometry check           PASS, self-check OK
    hollow facades           PASS, worst void 2.0 uu

### The style is a parameter, not a second generator

`genbuild.build()` dispatches on `spec['style']` to `build_vernacular` or
`build_modern`. `step_elevations.flank()` does the same, because a modern corner
wearing a vernacular side elevation would be two buildings pretending to be one.

Late-60s/70s comes from **rhythm and proportion**, not more detail — which is
why it suits card better than Main Street does. There is no ornament to
approximate, only planes to place:

    vertical bay rhythm  ->  continuous horizontal ribbon
    punched window       ->  glazing 880 mm behind a proud spandrel band
    masonry pier         ->  precast fin, 340 mm wide and 460 proud
    projecting cornice   ->  flat coping over a shadow gap
    shopfront in a frame ->  recessed arcade under an overhanging mass

**No new palette.** `MI_concrete`, `MI_paint_cream`, `MI_dark_metal`,
`MI_glass_b` — all existing roles, re-proportioned. MASTER_MATERIAL_SPEC's
warning about a palette growing a `walnut` and a `cedar` applies exactly here.

One thing is emergent and worth keeping: because the glazing is continuous, a
lit floor reads as **one glowing ribbon band**, where the vernacular next door
reads as separate lit windows. The era difference shows up in the lighting for
free.

I revised the fins once. At `BAYS*2` they subdivided the ribbon into six panes
and read as *mullions* — the vernacular rhythm, the exact thing this style is
not. Fewer and deeper now.

### Corners return the shopfront

`corner=True` on the four end lots. Their flank's ground floor is an **arcade
return** rather than a blind plinth: columns, soffit, recessed glazing and
mullions carrying round. That single move is what makes a corner read as a
corner instead of as two buildings meeting.

### The board and streets now come from the table

`step_stage2.py` hardcoded block A's and block B's facade lines, so a third
street could not exist without editing it. `city.py` now carries a `STREETS`
list and the board sizes itself to cover them:

    street 1  y -1170 .. -430    between blocks A and B
    street 2  y -3620 .. -2880   behind block B, in front of block C north
    street 3  y -6150 .. -5580   a narrower service street, block C south
    board     X -300..4600  Y -6700..900

### Two more stale-state traps

**The editor's Python caches modules across remote-exec calls.** `from city
import STREETS` failed with the constant sitting in the repo copy, because the
process was still holding the dead scratchpad's `city.py` from an earlier
session. Then it happened again with the *repo* copy: `step_stage2.py` printed
street positions from the previous version of the table after the file on disk
had been edited — indistinguishable from the edit not working. `_guard.py` now
drops every cached module loaded from `/private/tmp` **or from this project**,
so each guarded run imports current source.

**The capture rig never pinned the viewport FOV.** `CaptureViewport` renders at
the VIEWPORT's field of view, and saving the level resets it — the trap
`prep_shot.py` exists for. Every script that saves silently rescaled every
capture taken afterwards. A/B pairs taken back to back were unaffected, but
absolute framings across a save were not comparable, and several captures this
session were at a wider FOV than the project's 70 mm. `Tools/measure/cap2.py`
now sets it immediately before every capture.

### The depth budget, overrun twice

Owner's first-pass review: *"the storefronts look blank and there is more
clipping on the windows from zoomed out."* Both, measured against the core
front at block-local Y 62:

    Glass_Shop       Y  78 .. 80    INSIDE CORE            -> blank storefront
    Interior_Shop    Y  94 .. 100   INSIDE CORE
    Interior_Ribbon  Y  60 .. 66    STRADDLES CORE FACE    -> z-fight at range

One cause. Geometry past 62 is inside solid mass: invisible if fully behind,
and **z-fighting if it straddles**, which is what "clipping, worse zoomed out"
is — depth precision falling off with distance. The storefront was not blank,
it was buried, and what showed was the core's own face.

This is the second time in two sessions I have overrun this budget. The first
was the flank elevation, where the fix was to stand the slab proud of the core.
The comment naming the budget now sits at the top of the modern style block.

Fixed two ways:

- `Interior_Ribbon` moved to `GLAZE_Y+8 .. +14` (52..58), inside the budget.
- **The arcade recess now exists in the CORE.** A modern building gets a
  separate ground band at `FACADE_BACK + CLEAR + ARCADE` = 140, using exactly
  the mechanism step_cores3 already had for setbacks. Verified: `CORE_Tower_b0`
  spans local Y 140..640, `CORE_Tower_b1` spans 62..640.

`blockC_arcade.jpg` — glazing with a lit interior card where there was blank
wall.

**The probe that found this is now asking the wrong question.** It compares
against a hardcoded 62 and does not know about the arcade band, so it still
reports Glass_Shop as INSIDE CORE when the ground band starts at 140. It found
the bug and is no longer evidence; it needs the per-band front before it is
trusted again.

## 12. The four follow-ups

### The check was blind to three quarters of the city

`check_block.py` imported `LOTS` from `lots.py` — block A alone. It printed
"geometry check: PASS (0 failures)" throughout the construction of blocks B and
C and that PASS covered **none of them**. Same shape as `core_check`, which
compared only street-side edges and passed five hollow buildings.

Rewritten against the city table. Adjacency comes from the data: lots
consecutive by x0 within a block are neighbours; lots in different blocks are
not. Two self-checks, both derived rather than hardcoded — the Assetsville
flank at its lot edge, and **a block C lot's world X through the yaw-180
transform**, which is where a coordinate bug would actually hide.

It found four real overlaps on its first run. Three were block C's rows
touching at their shared rear party line, which the check had no way to know
about — declared with `island_with` in `city.py`. The fourth was mine: raising
Plaza and Annex to 660 deep put them 1320 apart across a 1280 gap. The rows'
facade lines are 1280 apart, so for any pair overlapping in X,
`depth_N + depth_S` must not exceed that.

    geometry check: PASS (0 failures) over 13 buildings in 4 blocks

### Props on every street

`fix4_props.py` was hardcoded to block A's lots and a single
`BUILDING_FRONT = -60`. Now driven by `STREETS`, with trees down both pavements
of all three and rooftop units distributed across every block at 55%.

The footprint test had to be rewritten **twice**. One half-plane per block was
no better than one hardcoded line: a half-plane has no back, so every prop
behind a block counted as inside it and the first street-wide run placed
**0 of 24**. A lot is a rectangle from its facade line to its depth. 26 placed,
2 rejected.

### Massing, not colour

At board range the 0.4% rule says only mass reads, so the variation is height,
setback and depth rather than tone: floors 2 to 7, three lots set back, depths
610-640. Height spread **1860 uu against a ~55 uu threshold**.

Adding setbacks exposed that **`build_modern` ignored `setback` entirely**.
`step_cores3` banded the core back 140 uu because the spec said so; the facade
did not move. `gap_check2` measured a **142 uu void behind Tower F6** — caught
by a check, not by eye. The modern builder now offsets its top floor like the
vernacular one does.

### Block B's rear is a frontage now

It faced empty board when it was built. Street 2 changed that, and a blank slab
on one side of a road reads as exactly what it is. `rear_street=True` on block
B; `step_elevations.rear()` emits the front vocabulary along X, mirrored in Y,
standing `FACADE_T` proud of the core's back face — the same depth discipline
that had already caught me twice. 463 boxes over three buildings.
`street2_both_sides.jpg`.

**This reverses the earlier decision not to articulate rears, and correctly:**
that call was made when nothing faced them. The city grew and the answer
changed.

### The editor axis gizmo was in a capture

`bShowUI: False` does not suppress it. `AGENTS.md` section 6 lists precisely
this among the evidenced failures inherited from the bakeoff — *"an uncomposed
viewport grab with the editor axis gizmo still visible"* — and it was sitting in
the corner of the board render. `cap2.py` now forces `editor_set_game_view(True)`
and `stat none` alongside the FOV pin.

    final: 4574 slots, 0 unresolved | 23 cores | 218 practicals, 0 skipped
           geometry PASS over 13 buildings in 4 blocks | worst void 2.0 uu

### Known limits of this block

All four of these were fixed - see section 12. The three follow-ups after that
are section 13. What is left:

~~The lighting is now the blocking item.~~ Fixed - see section 15.

**Still open:** The key/fill rig was derived for a

- Block D's rear elevations use the vernacular vocabulary. For a 1930s
  building's back that is arguably right - plain punched brick - but it was not
  a decision, it is what `rear()` emits for anything that is not modern.
- No cold read since block C.

---

## 13. Trees, fleet, precast

### The trees read as a hedge

Two species alternating on a fixed 1120 uu grid down both pavements of all
three streets. Three things changed, and only one of them is spacing:

- **Species picked for the footway.** `SM_tree_03` and `SM_tree_04` are ~450 uu
  across and suit a 430 uu pavement. `SM_tree_01` at 656 is occasional,
  `SM_tree_02` at **1223** would swallow the footway and appears rarely, and
  `SM_bush_01` fills. Weighted 6/6/3/1/3.
- **Spacing** ~1900 uu with +/-420 jitter, and the two sides offset by half a
  step so they never line up across the road. Street 3 is a service road and
  gets 55% density.
- **Scale** +/-15% per tree. A handmade model's trees are not stamped from one
  part; MINIATURE_RECIPE's hand-tolerance rule is 1-2% on buildings and much
  looser than that on planting.

26 props down to 18, and the canyon opens up.

### Nine vehicles instead of four

Only four of the pack's eighteen skeletal vehicles had ever been baked.
`sk_bake_more.py` adds Van, Muscle, SportClassic, Offroad and VegetableTruck -
**separate from `sk_bake_batch.py` on purpose**, because that script deletes and
recreates everything it lists and would have wiped the curvature vertex colours
off the four existing vehicles. All five then curvature-baked: 13.9-31.6%
painted, slots kept, winding verified.

`place_baked.py` hardcoded four cars at fixed X on block A's kerb, so streets 2
and 3 had none. Now driven by `STREETS`: both kerbs of every street wide enough
for two-sided parking, ~760 uu pitch with jitter and a 28% skip rate, because a
kerb filled end to end at a regular pitch reads as a car park. **20 vehicles,
nine types.**

`step_veh2s` then reported **"2 had no counterpart"** - `MI_card_lift` arrived
with the vegetable truck and had no two-sided sibling, so those two slots would
have stayed single-sided, which is see-through bodywork: exactly the defect the
whole mechanism exists to fix. The script said so plainly and the fix was one
line in `mk_2s_missing.py`. Now 0 without a counterpart.

### Three precast tones, not two

`MI_precast_buff` (0.745, 0.700, 0.612) and `MI_precast_grey`
(0.620, 0.612, 0.596), copied from `MI_concrete` and differing **only** in
BaseColour - roughness band, specular, seam, paper and wear are identical, and
the script asserts it. That is the same move the card role already makes with
ochre, rose and sage, and it is what MASTER_MATERIAL_SPEC means by "variation
comes from instance parameters, never from a differently-authored shader".

Spread so no two adjacent lots share a tone and neither row reads as one batch:

    Tower  concrete    Slab   buff        Plaza  grey
    Annex  buff        Court  concrete    Civic  grey

Final: **4574 slots 0 unresolved | geometry PASS over 13 buildings in 4 blocks
| 20 vehicles | 18 street props**.

---

## 14. The first intersection, and a third architecture

### The avenue

`city.py` grew an `AVENUES` list in the same shape as `STREETS` - two frontage
lines and a pavement width - so one builder handles both and an intersection is
simply where one crosses the other. Board out to X 10400. Three intersections
where the avenue crosses streets 1, 2 and 3.

**Roads cannot both run through.** Two coplanar slabs at z -30..-16 meeting at
a crossing z-fight. The streets run through and the **avenue yields**, built in
spans between them; pavements and kerbs break over the other road's width the
same way. `spans(lo, hi, gaps)` does it, and it is the reason the junction
renders clean.

80 crossing bars over the three intersections, and 12 mast-arm signals - four
per junction, each arm aimed over the crossing it governs rather than pointed
at random, which is what makes it read as a signalled junction instead of four
poles standing nearby.

### Block D - Art Deco, 1930s

Chosen because it is the **opposite** of the late-modern block rather than a
variation on it:

    vernacular   bay rhythm, punched windows       1900s-20s
    modern       horizontal ribbon behind a band   late 60s-70s
    deco         unbroken vertical pilasters       1930s

Deco is also flat. Its ornament is fluting, setbacks and stepped parapets -
geometry, not moulding - so cut card can do all of it. Full-height pilasters
standing 500 mm proud, glazing recessed into continuous channels between them,
dark spandrel panels set back, two flutes per pilaster face, and a **stepped
parapet** with the centre bay 1.9x the outer ones. Marquee is 9 floors at the
avenue corner; the tallest thing on the board.

    Empire  7 floors  h 3000   Bijou 5 floors h 2230   Marquee 9 floors h 3630

Fluting takes `Band_` (the wall colour) and not `Accent_`: it reads as carved
stone, which is what it is. Spandrels take `Frame_`, the dark metal that sat
between deco windows.

**One jitter for the whole building.** The other styles jitter each floor
independently, which is fine when every floor is a separate plane - but a deco
pilaster is one piece running the full height, and floors sliding under it
would tear the shaft apart.

    generated        16 buildings in 5 blocks
    slots            7156 assigned, ZERO unresolved
    elevations       2083 boxes - 4 corners, 6 rear elevations
    practicals       336, 0 skipped
    geometry check   PASS (0 failures) over 16 buildings in 5 blocks
    hollow facades   PASS, worst void 6.0 uu
    45 vehicles | 49 street props | 12 signals

### A capture that came back pure black

Two junction framings read **mean 0.000** - not dark, black. Both had the
camera at y +1900 or +4600, north of the board's y 900 edge and **behind the
studio backdrop**. Worth knowing before reading a black frame as a lighting
failure: check the camera is inside the board footprint first.

---

## 15. The light rig, re-derived from the board

Two rect lights and nothing else - no SkyLight, no directional. A rect falls off
with the INVERSE SQUARE of distance and `LIGHT_Key` sat off the corner where the
first block used to be. That covered a 4900 x 3600 board. It is now
**10700 x 7600**, so the far end got roughly a twelfth of the near end.

`Content/Python/light_rig.py` derives the rig from the board:

    LIGHT_Sky       SkyLight, cool, ambient from every direction
    LIGHT_Moon      DirectionalLight, 7200K, 45 off axis / 35 elevation
    LIGHT_MoonFill  DirectionalLight, 8200K, opposite side, NO shadows
    LIGHT_Key       rect, re-centred over the BOARD, I x (d/d0)^2
    LIGHT_Fill      rect, likewise

**Directionals do the covering** because they do not attenuate: the far corner
of a 10700 uu board gets the same illuminance as the near one. The rects stay
for modelling, re-centred and rescaled by the inverse square of the new
distance - the one line of MINIATURE_RECIPE that makes a rig portable between
board sizes. Exposure is untouched; the gate fixes it and the rig moves to meet
it.

    view        mean   blown%   crushed%
    zoom       182.4   0.0000     0.0000
    board      118.4   0.0000     0.7702
    deco        75.5   0.0000     3.0983
    streetC     64.8   0.0161     2.7539
    spread 2.82x, was 5.2x with the far end effectively black

**Blown is inside the gate everywhere.** Crushed passes at the hero framings
and fails in the street canyons - that is genuinely dark geometry at night, not
a rig fault, and the 0.05% criterion was written for a lit block seen head on.

### Three ways this measurement lied before it told the truth

**A skylight that contributes black, twice.** `SLS_SPECIFIED_CUBEMAP` with
nothing assigned has nothing to sample. `SLS_CAPTURED_SCENE` with real-time
capture needs a SkyAtmosphere, a VolumetricCloud or an IsSky mesh, and printed
a warning saying so **across the render**. Every "sky" reading before that was
measuring nothing. It now samples a neutral grey cubemap tinted cool - even
ambient, no sky dome drawn.

**Two directionals fighting.** "Multiple directional lights are competing to be
the single one used for forward shading" - also burned into the frame. Fixed
with `forward_shading_priority`.

Both warnings were IN the evidence frames, which is the same class of defect as
the editor axis gizmo and is why AGENTS.md section 6 lists that one.

**Raising a light made the scene darker - twice.** Not possible, so the
measurement was wrong. The convergence curve explains it: mean rises 39.09 to
41.17 over ~16 frames and then oscillates 37-39. A "two consecutive quiet
frames" settle test fires at frame 3, partway up that curve, so each sweep
sampled a different point on it. The rig sweep was measuring Lumen convergence,
not light. `spread.py` now takes a **median over a long burst**, which is the
only statistic here that repeats.

---

## 16. `kind` dispatch, and the first zone

`city.py` said a block is a list of lots and a lot has floors, bays and a
parapet. A plaza has none of those, so `kind` now dispatches the way `style`
already dispatches inside `kind='gen'`:

    gen     a building        -> genbuild.build, which dispatches on style
    av      the tileset lot   -> step_av.py
    plaza   paved public open space   } Content/Python/zones.py
    park    planted open space        }
    vacant  a cleared site            }

Zones emit `ZONE_` actors using the same role-prefix component names, so the
one role sweep binds them and adding a zone costs nothing in material work.

**One new material instance, not a family.** `MI_grass`, copied from
MI_concrete and differing only in colour and a slightly higher roughness -
because in a card model a lawn is painted board, with the same tooth as
everything else. Paving is just concrete. Two new role prefixes, `Ground_` and
`Grass_`.

### Block C's Slab lot is now a plaza

Renamed Forecourt, and the building beside it renamed Terrace, because a lot
called Plaza next to an actual plaza is a name collision waiting to mislead
somebody. The hole in the street wall IS the period: a 1970s superblock sets
its tower back behind public open space.

### Which exposed a better exposure rule

`exposed_flanks` only knew about the ENDS of a block. With a zone in the middle
of a row, the buildings either side of it have walls on show that used to be
party walls. The rule is now: a flank is exposed if it is at the end of the
block **or its neighbour is not a building**. Tower and Terrace each gained a
second elevation the moment the plaza existed.

### The role sweep went down and everything else said ok

`WALL={l['name']: l['wall'] ...}` indexes `wall` directly, and an open zone has
no wall colour, so it raised **KeyError and took the whole sweep with it** -
8916 components left unassigned while cores, practicals and both geometry
checks all reported ok. Only the pipeline's own `FAILED` on that one line caught
it. `.get` now.

    15 buildings, 1 zone, 5 blocks | 8916 slots, 0 unresolved
    geometry PASS | no hollow facades, worst void 6.0 uu | 422 practicals

---

## 17. Street lamps - generated, not bought

The owner offered budget and an agent to scour FAB. Both declined, for reasons
worth writing down:

**A scouting agent can only bring back marketing screenshots**, and AGENTS.md
says candidates are evaluated "using actual meshes in Unreal, never marketing
screenshots". A report that cannot be evaluated is a shopping list, not a tool.

**And the one real gap did not need buying.** A card model's lamp column is a
pole, an arm and a head - four boxes. A donor lamp arrives with its own detail
tier, its own materials and its own idea of how much surface a 6 m pole should
carry, all of which then has to be fought back to the diorama. Every complete
donor BUILDING tried here has been unusable for exactly that reason; the
Assetsville tileset works because its parts are modular and its names carry
role.

`street_lamps.py` places 48 columns down every street and avenue pavement, 192
components, role-prefixed like everything else. `lamp_lights.py` hangs a
downward rect light under each head at 2100-2400 K - sodium, and the pool on
the pavement is what reads, not the lamp.

Own prefixes (`LAMP_`, `LAMPLIGHT_`) because `practicals.py` wipes every
`LIGHT2_` actor it finds and would have taken them with it. Both added to
`wipe_owned.py`'s ownership gate, along with `ZONE_`.

`street_at_night.jpg` - the canyon that was a dark trench now reads as a street.

**What would justify buying:** something hard to generate and easy to get
wrong. Signage with legible type, period vehicles, a foliage pack with real
alpha cards. Not buildings - that is where the generator is strongest and donor
assets weakest.

---

## 18. The bake fidelity gap was a mirrored mesh

Stage 2 measured the baked building against the component original at **29.9
mean absolute luma against a 6.31 grain floor** and eliminated five causes -
missing geometry, winding, chamfer, slot binding, floor pivot - each by
measuring PIXELS. It stayed open.

**It was never a rendering problem.** Comparing the two meshes' BOUNDING BOXES
instead of their renders found it in one step:

    BAKED   X 1096.2..2006.3   Y  -700.0..  14.0   tris 5984
    COMPS   X 1072.0..1948.0   Y   -14.0.. 700.0   tris 6528

`-700..14` is the exact negation of `-14..700`. The baked mesh is **mirrored in
Y**. Winding was checked in Stage 2 and fixed; handedness was not.

### Exporter or importer

    OBJ AS WRITTEN   Y  -27.3 .. 700.0     correct, matches the components
    IMPORTED MESH    Y -700.0 ..  14.0     mirrored

`bakegen.py` writes correct geometry. **Unreal's OBJ importer mirrors it**,
because OBJ is a right-handed format and the importer applies a handedness
conversion. Nothing in objgen or bakegen accounts for it.

That also explains the one visual symptom on record - *"the component version
shows a crisp cross in every window, the baked version does not"*. A Y-mirrored
building has its window reveals cut on the far side of the facade slab, so the
mullion crosses sit behind the glass instead of in front of it.

### Fixed and verified round-trip

Y is now negated at write, normals with it. Winding needs no change: the
importer reverses it as part of the same conversion, which is why the imported
mesh's normals already agreed with Unreal's own on 200 of 200 sampled
triangles.

    IMPORTED (fixed)  Y  -27.3 .. 700.0   tris 5984, 7 named slots
    COMPONENT BUILD   Y  -14.0 .. 700.0

### What is still not equal

X differs by 34 uu - the bake spans 1056.2..1966.2 against the components'
1072.0..1948.0 - and Y min by 13. Both are inside the hand-tolerance envelope:
each floor is jittered by up to +/-19 uu in X and rotated up to 0.9 degrees
about the world origin, which at x~1500 displaces a floor by ~24 uu in Y. The
two builds are drawing the same seed but not landing on the same numbers, so
the random sequences have diverged. **That is the remaining work, and it is a
much smaller thing than a mirror.**

### objgen was another dead-scratchpad casualty

`bakegen.py` does `from objgen import polys`, and objgen.py existed only in the
agent scratchpad - so bakegen could not be imported at all, exactly like ue.py.
`Content/Python/objgen.py` is now objgen_chamfer.py under the name the code
asks for. The fidelity gap could not have been investigated by anyone with a
clean checkout.

### Method note

Five eliminations over two sessions were all pixel comparisons. A pixel
difference conflates geometry, material and lighting - it can tell you
something differs, never what. Comparing the geometry directly took one probe.

---

## 19. Daylight, and three defects from the owner's screenshot

### Vehicles broadside across the road - FIXED

They were correctly AT the kerb - 126 to 167 uu, consistently. But the mesh's
long axis is local **X** (SM_Baked_Sedan is 540 x 252) and they were rotated
+/-90, so every car sat across the carriageway. The wrong number came from
`get_actor_bounds`, which includes the actor ROOT at the origin - the trap
HANDOFF.md section 5 records. `static_mesh.get_bounding_box()` is mesh-local
and correct. Yaw 0 and 180 now.

### Lamp columns through parked cars - FIXED

Measured: street 1's road spans Y -1170..-430 and the far-side lamps were at
Y -1108. The road is BETWEEN the kerbs, so the pavement is outside that span -
`k_far - 62`, not `k_far + 62`. Every far-side lamp stood 62 uu inside the
carriageway, where the cars park. Sign error, the same shape as the vehicle one.

The rebuild also exposed that `street_lamps.wipe()` - which does its own
deletion over MCP - **silently returns nothing**. The wipe reported no removals,
the rebuild ran anyway, and the level ended up with 96 lamps and 384 components
where 48 and 192 were intended. `wipe_lamps.py` is an editor script now, where
a failure is visible.

### Daylight

`light_rig.py` takes `mode='day'`: a SkyAtmosphere, a sun on the same 45/52
geometry, a real-time-capture SkyLight - valid now that there IS a sky to
capture - and the two studio rects parked at zero.

**Tuned on the APERTURE, not the lights.** Sun and sky sweeps produced nonsense
twice more: reducing the sun raised the frame mean. The cause is Lumen and the
sky capture re-converging after every change, the same instability recorded in
section 15. f-stop is post-process, so it moves the image without touching the
lighting state, and the sweep came out monotonic immediately - f/8 128.4,
f/13 55.1, f/18 25.6. **That is now three separate occasions this session where
a light sweep measured convergence rather than light.**

ISO 800 and 1/60 are the gate's own numbers; only the aperture moves between
night and day. The sun here is a studio lamp, not the sun, which keeps the
"one camera photographing a model" reading intact.

### UNRESOLVED: Lumen's cached exposure ceiling

At the exposure daylight needs (8.9) Lumen prints across the viewport: *"Cached
lighting in Lumen and real-time sky capture lighting is going to be clipped...
Safe exposure range: [-12.0, ..."*. Its ceiling is between 6.9 and 8.9.

Dimming the sun two stops and opening the aperture two stops silences it and
gives an identical exposure VALUE of 6.9 - but the resulting image is dusk, not
daylight, because the scene is two stops darker in absolute terms. The cvar the
message names is a pre-exposure **multiplier**: setting it to 14.9 brightened
the frame eight stops rather than moving a cache range.

Left at the daylight-looking setting with the warning present, and flagged.
It is an editor viewport overlay - it belongs to the capture rig rather than
the scene - but it IS in the captures, which is the same class of defect as
the axis gizmo.

### The "sand pit" was never the plaza

Resolved by reading the owner's own viewport camera rather than guessing:
`EditorAppToolset.GetCameraTransform` returned (10491, -11563, 12184) pitch -57
yaw 113, which looks at roughly world (7400, -4280). The plaza is at world X
1500..3000. **They were looking at a different place entirely** - and five
failed camera attempts on my side were solving the wrong problem.

What is there is **empty board**: the block-shaped gap between streets 2 and 3,
east of block C, where nothing was ever built. `fix4_props` and `place_baked`
follow the STREETS, so it was ringed by pavement, trees, lamps and parked cars
with nothing behind them - which is precisely what made it read as a paved
void.

`park_before.jpg` / `park_after.jpg` are that camera, before and after.

**Reading the user's camera should have been the first move, not the sixth.**
It is one MCP call and it removes the entire class of "which bit are we
talking about" error.

### Block E - a full-block park

`kind='park'`, world X 6000..10100, depth 1280, fronting both streets. Planting
now scales with AREA - six trees is right for a 1500 x 600 square and nothing
at all for a 4100 x 1280 park - so it gets 52 trees and 14 benches instead of 6
and 4.

That is the third time a lot without building keys has taken a sweep down:
`roof_z` indexed `spec['gf_h']` on a park and raised KeyError, killing the
whole props step. Guard on `kind`, not on key presence.

### The Lumen exposure lever was backwards

Stopping down to f/8 with the sun at 260 produced *"Cached lighting in Lumen
and real-time sky capture lighting is going to be clipped... Exposure: 8.9"*
burned across the viewport. That number is the exposure **compensation** the
engine applies, so **closing** the aperture raises it.

The fix is the opposite of what it looks like: light the scene brighter and
OPEN the aperture, so less compensation is needed and the exposure lands back
inside Lumen's cached range. Sun 180 at f/4 clears it. Real-time sky capture is
also off - the sun is static, so it buys nothing and it is named in the warning.

Daylight defaults: **sun 180, sky 1.4, ISO 800, f/4, 1/60** - the gate's own ISO
and shutter, only the aperture and the lamp differ from night.

`lamp_mode.py` switches the 48 sodium lamps off in daylight; they were burning
on a sunlit street because `lamp_lights.py` knows nothing about the rig mode.

### The plaza was roofed over by 401 accumulated props

`fix4_props.py` wiped only `SUR_prop*` and `SUR_tree*`. Everything added since -
zone planting (`SUR_zone_*`), traffic signals (`SUR_signal_*`), rooftop units
(`SUR_roof_*`), street furniture (`SUR_kit_*`) - was **never removed**, so every
run added another full set. Clearing the whole `SUR_` prefix removed **401**
actors on the first pass.

That is why the plaza was solid foliage: not density, accumulation. I had
already "fixed" it once by thinning the planting, and the render came back
identical - which should have told me the density was not the variable, and
did, on the second look.

From directly above it now reads as a square: lawn bands, a paved forecourt to
the street, a cross of paths, kerbed beds, benches. `plaza_plan.jpg`.

### It is dark because of its proportions, not its lighting

The plaza is 1500 x 610 uu - 15 x 6 m - between a 34 m tower and a 25 m block.
At the sun's 52 degree elevation it never receives direct light. That is a
light well, not a square, and no rig setting changes it. Either the lot gets
wider, or it is accepted as a shaded courtyard.

### Moving the owner's viewport

`EditorAppToolset.SetCameraTransform` moves the editor viewport directly, and
`GetCameraTransform` reads it. Between them there is no reason to ever guess a
camera again - which was the single biggest waste of this session.

Its materials are confirmed correct - `Grass_Lawn` binds `MI_grass`,
`Ground_*` binds `MI_concrete`. But **I never got a working camera onto it**:
five attempts landed inside block B, inside Tower, or behind the backdrop. So
the claim "the sand pit is fixed" is unverified and should not be believed
until somebody looks. The lawn geometry and material are right; whether the
space READS as a square is a different question and an open one.

### Also open

The street lamps stay lit in daylight mode - `lamp_lights.py` does not know
about the rig mode, so there are 48 sodium pools on a sunlit street.

---

## Files

    Content/Python/curvebake.py      curvature -> vertex colour bake (+ self-check)
    Content/Python/fix_amp.py        restore PaperNormalAmount to the normal chain
    Content/Python/fix_wear.py       edge wear: normal proxy -> VertexColor.R
    Content/Python/mk_masked.py      create M_StacktownMaster_Masked
    Content/Python/wire_mask.py      wire LeafMask alpha -> MP_OpacityMask
    Content/Python/mk_leaf_mi.py     MI_leaf_card, MI_leaf_card_b
    Content/Python/step_foliage.py   assign foliage by material slot name
    Content/Python/triplanar2s.py    triplanar projection for the 2S master
    Content/Python/align2s.py        match 2S instance values to their counterparts
    Content/Python/mk_2s_missing.py  MI_glass_b_2S, MI_interior_2S
    Content/Python/step_veh2s.py     bind two-sided card materials to shell actors
    Content/Python/save_level.py     force-save the level and prove it hit disk
    Content/Python/step_elevations.py  punched elevations on exposed flanks
    Content/Python/cam_street_hero.py  block hero re-derived for two facing rows
    Content/Python/_path.py            repo tool paths, replacing a dead scratchpad
    Content/Python/build_blockC.py     builds the island block additively
    Content/Python/sk_bake_more.py     bakes five more vehicles from the pack
    Content/Python/mk_precast.py       two more precast tones for block C
    Content/Python/light_rig.py        board-derived rig: sky, moon, fill, rects
    Tools/measure/spread.py            illuminance spread across the board
    Content/Python/zones.py            plaza / park / vacant emitters
    Content/Python/mk_ground.py        MI_grass
    Content/Python/street_lamps.py     lamp columns down every pavement
    Content/Python/lamp_lights.py      a sodium light under each head
    Content/Python/objgen.py           restored: bakegen imports it by this name
    Tools/rung.sh                    guarded runner, finally in the repo
    Tools/measure/                   host-side measurement harness
      img.py       high-pass SD, gradient energy, detrended SD, spatial diff
      cap2.py      fixed-transform viewport capture
      settle.py    capture until the frame stops moving
      ab.py        A/B with the return control built in
      mgraph.py    material graph dump, reachable vs orphaned
      matlib.py    material graph edit helpers
      img.py also carries anisotropy(), the within-frame directional-bias ratio

Every capture in this directory is an **automated diagnostic**, not gate
evidence. `AGENTS.md` forbids submitting an automated capture as visual
evidence and none of these is offered as any.

## State

- `M_StacktownMaster`, `M_StacktownMaster_Masked`, the two leaf instances and
  **104 baked meshes are saved**. Zero dirty packages among them.
- **The level is saved.** `step_foliage.py` assigned the card foliage to 8 slots
  on the four trees in `Stage2_Block`, the owner approved the look, and
  `/Game/Maps/Stage2_Block` was written on request. `restore=True` still puts the
  pack's materials back if that is ever wanted.
- 14 material instances were touched by A/B testing and restored to their exact
  authored values, then saved. `MI_paint_cream` picked up explicit
  `EdgeWearLift` 1.42 and `EdgeWearWidth` 0.30 overrides that equal the master
  defaults — no behavioural change, but they are new overrides.

---

## Daylight, and why the plaza was the actual complaint

The owner said "the lighting is still too dark" three times. The first two
times I raised overall light and it partly worked. The third time it did not,
so I stopped raising things and asked which part was dark.

**Measured, one variable at a time, exposure held at ISO 800 / f/4 / 1/60:**

| change | plaza | board | plaza / board |
|---|---|---|---|
| baseline, sun 430 sky 10, elevation 52, azimuth 45 | 83 | 141 | 0.58 |
| sun elevation 52 -> 85, nothing else | 146 | 146 | 1.00 |
| sun azimuth 45 -> 225, nothing else | 131 | 125 | 1.05 |

Two different changes, each moving one thing, both lifting the plaza to parity.
The plaza was never underexposed. It was **occluded**: at azimuth 45 the light
travels toward +X and +Y, and the plaza's only two closed sides are the -X side
(the Terrace lot) and the -Y side (block CS, whose front wall stands 30 uu off
the plaza's rear edge). The plaza is bounded on exactly the two sun-facing
sides. A 6-storey wall at 52 degrees throws 0.55 x height into +Y; the plaza is
610 deep, so nothing short of an 11 m neighbour would let sun in.

**Neither fix was taken.** Elevation 85 is noon overhead — board and plaza
measured identically at 146, which is another way of saying the modelling was
gone. Azimuth 225 lights the plaza but backlights the hero camera, which stands
in the +X/-Y quadrant; the board dropped from 141 to 112. The plaza's open side
(+Y) and the hero camera's side (-Y) are opposite, so no single azimuth serves
both. That is a fact about this board's layout, not a lighting bug.

What was taken instead: hold the key, raise the fill. The sun sets contrast,
the sky sets how dark a shadow goes, and the complaint was always about shadow.

| sky | board | plaza | ratio | board sd |
|---|---|---|---|---|
| 8 | 189 | 116 | 0.62 | 46.0 |
| **14** | **193** | **138** | **0.71** | **45.1** |
| 22 | 204 | 167 | 0.82 | 44.1 |

Sky 22 lights the plaza best and washes the board out — the pink and yellow
elevations go pale and the cast shadows stop reading. Sky 14 is the knee.
**Daylight default is now sun 430 lux at 52 degrees, sky 14, ISO 800, f/4,
1/60.** Nothing blown at any setting tested.

### The measurement was wrong for most of this

Board sd read 42 in one capture and 87 in the next with the rig untouched. The
editor viewport does not always fill the captured buffer; when it does not, the
surround is pure black, and measuring the whole buffer mixes a constant 0 into
every statistic. `Tools/measure/live.py` finds the live rectangle first and
measures only that. It carries a synthesised known-answer frame — bars around a
flat 200 patch — and asserts both the bounds and the mean before it is trusted.
Every number in the tables above is live-rectangle only. The earlier numbers in
this session that are not are worth nothing and are not reproduced here.

## Cars were parked in the intersection

`check_clear.py` asks whether any lamp pole stands inside a parked vehicle, and
self-checks `overlap()` against a pair that plainly does and a pair that plainly
does not before it reports. First run of it found nothing — because it searched
for `SUR_lamp*` and `VEH_*`, and the actors are `LAMP_s*`, `LAMP_a*` and
`BAKED_veh*`. It returned "0 intersections" while asking the wrong question.
With the real labels: **54 lamps, 49 vehicles, one intersection** —
`LAMP_a1E_52` through `BAKED_veh5` at (6292, -1590), which is the pink car
visible in `day_cross`.

The lamp was in the right place. The car was not. `place_baked.py` walks each
street's parking lane across the full board width and had no exclusion for the
avenue, so parking lanes ran straight through the junction and out onto the
avenue's pavement. Ten of the forty-nine cars were standing in an intersection
or on a crossing. Added a keep-clear of the avenue corridor plus half a car
length at each end. **39 vehicles, 0 intersections.**

## Evidence

`day_board.jpg`, `day_road.jpg`, `day_cross.jpg`, `day_plaza.jpg` — pillarbox
cropped, live rectangle only. Automated diagnostics, not gate evidence.
