# Stage 2 — the block

Built 2026-08-23 in `/Game/Maps/Stage2_Block` (duplicate of Stage1_Building;
`OneBuildingTest` untouched). Four lots, party-walled, on one board with the
studio backdrop. 85 actors, 723 static mesh components, 430 of them generated,
34 lights. Level saved, zero dirty packages.

## What was built, and how

**Buildings are parameter sets, not drawings.** `Content/Python/genbuild.py`
takes a dict — name, x0, width, depth, floors, floor heights, parapet, bays,
canopy, setback, roof units, seed — and emits the whole card building. Three new
lots came from three dicts; the Stage 1 building is the fourth, reused as-is.

    Mid     x0 3300  w  980  5 floors  height 2240   MI_card_rose
    Wide    x0 2020  w 1240  3 floors  height 1670   MI_card_sage   canopy
    Narrow  x0 1120  w  860  6 floors  height 2430   MI_card_ochre  setback
    Stage 1 x0    0  w 1080  4 floors  height 1950   MI_paint_cream  canopy

Height steps of 480, 760 and 570 uu — against a 230 mm block-hero threshold,
all of them 20x over. Silhouette is doing the work, exactly as the budget
predicted.

**Material role lives in the component name.** `Wall_`, `Band_`, `Glass_`,
`Interior_`, `Frame_`, `Mullion_`, `Accent_`, `Roof_`. One sweep
(`assign_roles.py`) assigned 430 slots with **zero unresolved**, and adding a
building costs nothing in material work. Stage 1 wired materials per component
by hand; that is the part that could never have scaled. The pattern was taken
from the Portland build, which got this right first.

**Practicals are derived from geometry, not placed.** `practicals.py` finds each
building's shop glass and upper-floor interiors and lights a deliberately uneven
42% of them. 27 placed.

## Three things measured, all three wrong first time

**Colour separated by brightness, not hue.** Sampled off the render, the four
facades came out R160 / R200 / R196 / R223 — they differed in value, and "sage"
measured R200 G192 B178, which is warm. The albedos were only ~0.04 apart per
channel and a 4500K key swamped the rest. Pushed apart, sage pushed cooler to
survive the key.

**The ground floors were black voids.** MASTER_MATERIAL_SPEC's rule that
emptiness behind glass reads as a hole, not a room. Stage 1 only escaped it
because its practicals were hand-placed. Crushed pixels 0.328% -> 0.000%.

**A dead-on hero cannot show a plane break.** Facades were stepped 700 and
550 mm in Y — comfortably over threshold — and were completely invisible at
CAM_Block, because at frame centre a Y offset produces almost no cue.
`CAM_Block_B` at 27 degrees plan shows all of it. **Depth needs an oblique;
straight-on is a silhouette camera.**

## Exposure

    block hero   mean 134.8   blown 0.011%   crushed 0.000%

## The scaling bottleneck, measured

431 boxes were created through MCP `add_cube`, one round trip each:

    lot 2 (136 boxes)        105 s
    lots 3 and 4 (295)       219 s
    -----------------------------------
    431 boxes                324 s   = 0.75 s per box

That is the whole cost of this stage, and it is entirely round-trip latency. A
block of four is ~430 boxes. A hundred blocks is ~43,000 boxes, which is **nine
hours of nothing but MCP calls** — before considering that 43,000 separate
StaticMeshComponents would not render.

The generator architecture scales. The transport does not.

## The single-mesh bake test

Question: can a whole building be one generated mesh with per-role material
sections, instead of ~140 components placed one MCP call at a time?

`Content/Python/bakegen.py` emits the identical geometry to `genbuild.py` as one
OBJ with a `usemtl` group per material role.

### What it proved

| | components | baked |
|---|---|---|
| generate | 105 s (136 MCP round trips) | **0.036 s** |
| import | n/a | 1.1 s |
| total per building | 105 s | **~1.2 s, 87x faster** |
| MCP round trips | 136 | **0** |
| components in level | 136 | **1** |
| triangles | — | 5,984 |
| material slots | per component | **7, named, bind correctly** |

`StaticMeshActor` spawns straight from Python, so a baked building costs ZERO
MCP calls, not one. Slots import with their `usemtl` names intact — Band, Frame,
Glass, Interior, Mullion, Roof, Wall — so the same role vocabulary binds them.
Whole-frame exposure is unchanged: mean 135.4 against 134.8, 0.000% crushed.

### What it did NOT prove — the fidelity gap is unresolved

Substituted into the block at the identical transform, the baked building does
not match the component version:

    baked (chamfered) vs component   mean abs diff  34.8
    baked (sharp)     vs component   mean abs diff  29.9
    component vs itself, re-rendered  mean abs diff   6.31   <- grain floor

So the difference is roughly five times the noise floor and it is real. Visually
it is the window mullions: the component version shows a crisp cross in every
window, the baked version does not.

Eliminated, each by measurement:

- **Missing geometry.** The OBJ carries 702 mullion faces = 27 boxes x 26, and
  the imported mesh has exactly 5,984 triangles = 136 boxes x 44. Nothing was
  dropped.
- **Winding.** Real bug, found and fixed: `objgen.polys()` returns unoriented
  polygons and it is `objgen.write_obj()` that flips the inward-facing ones,
  which only works while they are still origin-centred. Reusing `polys()`
  without that step rendered the first bake inside-out — backface culling ate
  every wall and left a skeleton of frames. Fixed; walls are solid now.
- **Chamfer.** `genbuild` uses MCP `add_cube`, which makes SHARP cubes;
  `bakegen` chamfered every box at 40 mm, clamped to 2.7 uu on a 6 uu mullion.
  Re-baked at chamfer 0 — barely moved the number, 34.8 -> 29.9.
- **Slot binding.** Blacking out every slot except Mullion shows the mullions
  present and roughly correctly placed, so the section and its material do bind.
- **Floor pivot.** `genbuild` rotates each floor about the ACTOR origin, world
  (0,0,0), not the building centre; baking about the centre displaced floors by
  up to 24 uu. Corrected — and it made no difference to the number, so it was
  not the cause either.

**The cause is not yet known.** The architecture is right on transport grounds
and the numbers are not close — 87x and 136:1 — but nothing should be converted
until a baked building is pixel-equivalent to its component original. That is
the next piece of work, not a detail to wave through.

Block restored to the component version; verified at 6.31 against the original,
i.e. grain only.

## Defect audit of the block-with-life pass

Prompted by the owner, who pointed out that the self-review named only the
foliage and ignored several obvious faults in the same frame. Every item below
was then verified by measurement, not by looking.

**1. The generated buildings are hollow facades.** `BLD2_Mid_F0` spans
Y 47.0 .. 113.0 - a 66 uu slab. Its roof spans Y 75.0 .. 805.0 and the side
parapets (`Wall_ParapetL/R`) run the full 730 uu depth, but ONLY at roof level.
So every generated building is a thin facade with a full-depth roof lid floating
on top and nothing between the sidewalk and the parapet. Invisible straight-on,
obvious from any angle. `genbuild.py` never emitted flank or rear walls.

**2. Vehicles render see-through.** Their car materials are ALL `two_sided=True`
(MI_glossyBlue, MI_glossyWhite, MI_ColorPalette, MI_GlassBasic) and the meshes
are single-sided shells that depend on it. `M_StacktownMaster` is
`two_sided=False`, so binding card roles culls the backfaces and the road shows
through the bodywork. Needs a two-sided variant of the master for shell geometry.

**3. The water tower is a rooftop asset dumped in the street.**
`SM_Water_Tank_01` is 877 uu - 8.8 m - and was placed at X3000 Y-160, which is
mid-sidewalk and intersecting the Assetsville facade. Props were placed at
arbitrary coordinates with no collision test and no thought about what the asset
is for.

**4. The Assetsville facade has no returns.** One plane of 30 uu modules. Its
"roof" tiles float as unconnected slats and the cornice projects into open air.
That is my assembly, not the pack.

**5. A pedestrian clips the water tower base; a car overlaps the curb.** Same
cause as 3 - blind placement.

**6. Foliage cannot take the card treatment** - the one fault the original
review did report.

NOT a defect, and wrongly implied to be one: `SM_tree_02` is a stylised low-poly
conifer, 1198 x 1223 x 1248 with correct materials (MI_matteBrown /
MI_Leaf_01). It reads oddly beside the deciduous trees but it is working
exactly as authored.

### The actual failure here

The render was reviewed for the thing that had just been changed rather than
audited as a whole. That is the second time in one sitting: the skeletal crash
cause was also declared before the deciding variable had been isolated. Both
times the correction came from the owner, not from the process. A pass is not
finished when the last edit renders - it is finished when the whole frame has
been walked.

## Milestone: the block builds itself

Stage 2 is part generated, part hand-assembled, part stopgap, so block #2 would
cost what block #1 did. The milestone that changes that:

> One script, run against an empty sandbox, reproduces the entire block.

    1. build_block.py on an empty map produces the whole thing        OPEN
    2. zero geometry interpenetration (automated)                     PASS
    3. blown <= 0.02%, crushed <= 0.05% at block hero                 PASS
    4. holds at block hero AND player zoom                            NOT RE-VERIFIED
    5. no hand-placed stopgaps                                        PARTLY

### The Assetsville lot is a real building now

`CORE_AV` - a raw box dropped in as a stopgap - was reported as "clipping into"
its neighbour. Measured: it was not. A 72 uu gap, and the neighbour correctly
drew in front. But the complaint was right: a featureless slab terminating
against another building with no corner reads as embedded whatever the numbers
say.

Rebuilt as a closed volume from the tileset - front, rear, two flanks, parapet,
roof cap - 38 modules. Module pivots are corner-based (local Y -400..0, Z 0..300)
so under yaw 90 a module occupies world X P..P+400; everything is placed from
that rather than guessed.

### THREE measurement bugs in one sitting, on the same test

The AABB overlap test proposed as acceptance criterion 2 was wrong twice before
it was right:

    v1  added LOCAL mesh bounds to the world location, ignoring rotation.
        Every yaw-90 module measured 40 uu wide instead of 400, and it invented
        a 3 uu overlap that did not exist.
    v2  used get_actor_bounds(), which includes the actor's root component at
        the origin - reported every building as starting at X -128.
    v3  transforms the 8 local corners by the component world transform, and
        CARRIES A SELF-CHECK against two placements whose answer is known
        (a flank at X 2005..2035, a window at X 2020..2420).

A test that has never been checked against a known answer is not evidence. v3
reports 0 cross-building overlaps and proves it can measure.

### Exposure recovered by locating the pixels, not by taste

    0.268% blown  -> stray practicals: LIGHT2_Wide_* still lit inside the new
                     walls, because BLD2_Wide is hidden rather than removed
    0.108% blown  -> interior practicals clipping on the reveal box; x~2688
                     stripe repeating every 256 px, one per floor. Scaled x0.55
    0.100% crushed-> 82% of crushed pixels sat in ONE 96 px column at frame
                     centre: the 17 uu slot between the Assetsville lot and
                     Narrow, looking through to black. Party-walled buildings
                     should touch. Lot shifted to butt; remainder filled

    final: blown 0.014%   crushed 0.043%   both inside criterion

Locating defective pixels spatially beat adjusting exposure by eye every time.

### uepy was mis-using the remote-execution API all session

`MODE_EXEC_FILE` takes a PATH. uepy read the script and sent its SOURCE, which
UE had been silently accepting as a fallback until one script tripped it and it
reported `Could not load Python file '<the entire source>'`. Now sends the
absolute path. `rung.sh` also needed a newline between the guard and the script.

## The block builds itself — 4 of 5 criteria

`Content/Python/build_block.py` wiped 112 owned actors and rebuilt the whole
block from `lots.py` in one run: two generated buildings, the Assetsville lot as
a tileset volume, cores, materials by role, practicals, props by rule, baked
vehicles and pedestrians, then the checks.

    1. one script reproduces the block from empty     PASS
    2. geometry check                                 PASS  (0 failures)
    3. blown <=0.02%, crushed <=0.05%                 PASS  (0.011% / 0.049%)
    4. holds at block hero AND player zoom            FAIL
    5. no hand-placed stopgaps                        PASS

Ownership-gated: it can only destroy labels starting with BLD2_, AV_, CORE_,
PARTY_, SUR_, BAKED_, SKT_, LIGHT2_. The reused Stage 1 building, the stage, the
cameras and the key/fill rig are never touched.

### Two corrections to the CHECK, not the block

**Self-check constants must come from the data.** The overlap test's known-answer
constants were hardcoded for the old Assetsville position and reported MISMATCH
against a block that was fine, the moment the lot moved. They now derive from
`lots.py`. A check that needs hand-editing when the data changes is a second
source of truth and will eventually lie.

**Party walls are correct architecture.** Demanding zero overlap between
neighbours was wrong, and it is what produced the 17 uu slot showing black at
frame centre. The check now allows neighbours to share up to 40 uu and rejects
any overlap between NON-adjacent lots. Current shares: Stage1/Narrow 38,
Narrow/AV 8, AV/Mid 8.

### Why criterion 4 fails — the generator emits un-chamfered cubes

At the 9 m player zoom the generated facade reads flat: no fibre, no crushed
edges, a hard-edged band of practical spill on the spandrel. The materials are
NOT the problem - measured on MI_card_ochre: paper normal 0.55, tiling 0.050,
seams 0.88 at 6 uu / 380 uu, wear 1.42, roughness 0.62-0.80, specular 0.20. All
correct.

The cause is geometry. `genbuild` builds through MCP `add_cube`, which produces
**plain Cubes with sharp edges**. Edge wear is a normal-as-curvature proxy that
needs 45 degree chamfers to act on, so on these buildings it does nothing at all.
Stage 1 only reads as card up close because its components were swapped to
chamfered SM_Cw_* meshes in a later pass; Stage 2's generated buildings never
were.

Two things to do, in order: swap generated components onto chamfered meshes (the
Stage 1 swap pass, applied per lot), and pull the practical spill off the
spandrel so the surface is not locally blown out where it should read.

## Chamfer swap: edges fixed, flat faces still flat

42 unique component sizes enumerated from the generated buildings, chamfered
meshes generated and imported at 40 mm (objgen clamps to 45% of the smallest
dimension, so the 2 uu glass and 6 uu mullions survive), and **297 components
swapped** off plain Cubes with scale reset to 1.

The edges now read. Every chamfer catches the key light and the frames and
mullions look like cut card rather than bars - visible in
`Saved/Stage2/block_player_zoom_chamfered.png`.

Practicals were also reseated: they had been at the interior box minus 10 uu,
which put them INSIDE the facade slab depth (fy..fy+60) where they washed the
spandrel with a hard-edged band, with a 780 uu radius for a room 26 uu deep.
Now 4 uu in front of the interior box, radius 300 (shopfronts 420).

**Criterion 4 still fails, and the measurement says so plainly:**

    zoom framing            blown %    flat wall patch, detrended sd
    before chamfer swap      0.554%    0.12
    after chamfer + lights   0.623%    0.22

    per-pixel grain floor is sd 4.8; a detrended column sd of 0.1-0.2 is FLAT

So the edge treatment landed and the SURFACE treatment did not. The flat faces
carry no measurable detail at the player zoom despite the paper normal being
configured correctly (PaperNormalAmount 0.55, PaperTiling 0.050, verified on the
instance). Wall patch mean is 226 of 255 and blown is 0.62% at this framing, so
the most likely cause is that the surface is simply too hot for a normal-map
perturbation to register - but that is a hypothesis, not a finding, and the last
few sessions are a good argument for not reporting it as one.

Next: establish whether the wash is the practicals or the key by measuring a
pier face far from any window. If the pier is equally hot it is the key light and
the zoom exposure needs its own treatment; if not, the practicals still spill.

## Do not put data files in Content/

Copying `stage2_sizes.json` and `marks_table.json` into `Content/Python/` for
archival made UE's asset importer pick them up. It opened a **DataTable Options
modal**, which blocks the game thread - so remote execution stopped answering
and the editor looked hung. It was not busy and it had not crashed; it was
waiting on a dialog nobody was going to click.

Content/ is watched by the importer. Only `.py` belongs in `Content/Python`.
Data and shell helpers now archive to `Saved/Stage2/data/` instead.

Symptom to recognise next time: `uepy` reports NO NODE FOUND, the editor process
is alive and burning ~100% CPU, and the log's last entry is whatever ran before
the file was copied in. That is a modal, not a crash - check the screen before
restarting anything.

## The practicals-vs-key test, and what it actually found

Same zoom frame, practicals hidden then restored, two patches measured:

    SPANDREL (a practical shines on it)      mean    detrended sd   frame blown
      practicals ON                          226.2       0.22          0.623%
      practicals OFF                         200.6       0.48          0.000%

    PIER FACE (far from any window opening)
      practicals ON                          179.1      14.96
      practicals OFF                         176.6      15.99

**The practicals cause 100% of the blown pixels** - 0.623% to 0.000% - and the
key light is not implicated: the pier moves 179.1 to 176.6, which is nothing.

**But the hypothesis was still wrong.** With the practicals off the spandrel is
STILL flat (sd 0.48). The wash was not hiding surface detail; there was almost
no surface detail to hide. Reporting "too hot for the normal to register" as the
answer would have been wrong for the third time today, which is exactly why it
was flagged as a hypothesis and tested.

### Isolating the paper chain, one variable at a time

    PaperNormalAmount 0.55 -> 3.00, tiling unchanged     sd 0.48 -> 2.07
    PaperTiling       0.05 -> 0.20, amplitude unchanged  sd 0.48 -> 0.45

Amplitude is wired and responds proportionally. **PaperTiling is inert** - a 4x
change moves nothing - even though `T_PaperNormal` and `T_PaperDetail` are bound
on both the master and the instance. So the tiling parameter is not reaching
those samplers' UVs. The master also carries a Noise node at Scale 1 alongside
the two texture samplers, and which of them actually drives the surface has not
been traced.

Set to amplitude 2.0 on all card roles, which makes the fibre plainly visible at
the player zoom. Hero unaffected and slightly better:

    block hero  mean 130.4  blown 0.000%  crushed 0.042%   criterion 3 PASS
    geometry check PASS, self-check OK

### A criterion I made up

The sd >= 4.8 target was my own invention - it is the per-pixel FILM GRAIN
floor, which has nothing to do with whether a surface reads as card. Judging
criterion 4 against it was measuring the wrong thing. Surface presence is a
cold-read question, the same as F1; the sd number is only useful as a relative
before/after, which is how it was used to isolate the paper chain.
