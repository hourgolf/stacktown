# Stage 1 — one building

Map: `/Game/Maps/Stage1_Building` (sandbox). The protected
`/Game/Maps/OneBuildingTest` was NOT created or touched — promoting Stage 1
into it needs an explicit instruction.

Rebuilds from scratch: `Content/Python/stage1_massing.py` -> `stage1_street.py`
-> `stage1_mats.py` -> `stage1_chamfer.py` -> `stage1_swap.py` -> `stage1_life.py`

## What was built
5 storeys (ground + 4 upper), 19.5 m, on the Stage 0 3600 mm bay module.
19 actors, 212 static mesh components, 0 unassigned materials.
194 of 211 chamfered (2.5 mm); 17 left plain — sub-3 uu cards and the
oversized ground/backdrop planes whose edges are off-frame.

## Design basis (measured, not guessed)
At Stage 1 framing the camera sits ~95 m back = 0.671 px/uu, against Stage 0's
2.616. The Stage 0 answer of 250 mm window recess reads only 3.5 px there, so
per-window recess CANNOT carry the reveal at building scale. Depth is carried
by metre-scale features instead:
  600-700 mm floor-band offsets   8-10 px
  2.2 m canopy                    ~21 px
Uneven band projections (620/550/680/580 mm) and floors nudged 15-45 mm
laterally give the hand-assembled misalignment (gate C3).

## Approved cameras
CAM_Hero    (540, -9272, 2946)  pitch -12  yaw 90   70 mm / 36x24
CAM_Hero_B  (4893, -8187, 2946) pitch -12  yaw 118  70 mm / 36x24  (28 deg off-axis)
Fixed manual exposure EV100 6.91 (ISO 800, f/4, 1/60). Bloom, DOF, motion blur off.
Key 1,580,000 lm 4500 K; Fill 210,000 lm 7200 K; attenuation 26000.
Practicals: 2 shopfront (2700 K) + 3 upper windows, deliberately uneven.

## Measured
Hero     mean 151.3  max 250  min 31  blown 0.001%  crushed 0.000%
Angle B  mean 147.4  max 250  min 17  blown 0.004%  crushed 0.000%

E6  validation: 76 assets scanned, 0 hard failures, 0 warnings.
E5  wall frame time 8.333 ms — this is a 120 fps CAP, i.e. a ceiling, not the
    scene cost. Resident memory 1.37 GB. Stage 0 measured a 16.8 ms ceiling
    with a twentieth of the geometry, which supports the Stage 0 finding that
    cost here is fixed renderer overhead (Lumen + TSR), not scene complexity.
    GPU breakdown NOT obtained this session — see below.

## Measurement traps (all cost real time)
  - Piloting a camera moves the ACTOR. Navigating while piloted silently edits
    the approved camera; CAM_Hero drifted 3.2 deg in yaw that way. Run
    `resetcam.py` before every evidence capture.
  - `stat unit` / `stat memory` are TOGGLES. Re-issuing them turns them back
    on. Use `stat none`.
  - The editor throttles rendering when not foreground, so a deferred
    HighResShot silently writes nothing. `Slate.bAllowThrottling 0` + bring the
    editor to the front.
  - Never `time.sleep()` inside a remote-exec script — Python runs on the game
    thread, so the editor cannot tick and the screenshot never services.
  - `pilot_level_actor` takes effect on the NEXT tick. Setup and capture must be
    separate remote-exec calls or the shot uses the pre-pilot viewport.
  - ProfileGPU: opens a GPU Visualizer window which the NEXT profile then
    captures instead of the viewport (`r.ProfileGPU.ShowUI 0` helps, closing the
    window helps more). Even then it captured Slate/idle frames rather than the
    3D scene. Unresolved.
  - A correct capture is 1.5 aspect. 1.86 means it was NOT piloted, and is
    invalid on both FOV and exposure.

## Print pass (2026-08-23)
94 frame lines  -> MI_frame_print (0.30 mid grey)
14 interiors    -> MI_interior (0.03 near-black)
12 glazing      -> alternating MI_glass / MI_glass_b by floor

The bug this fixed: window frames/mullions and the interior cards both used
MI_dark_metal (0.13), so every window rendered as one undifferentiated black
mass and the mullion grid built in the previous pass was invisible against the
void behind it. Separating the two values makes the grid read as a light
printed line against a dark interior - the key cue in the paper reference.

Deliberately NOT done: surface grain (invisible below ~4 px at 95 m) and
facade albedo variation (BAY_RECIPE calls it "the trap").

Hero    mean 149.7  max 250  min 19  blown 0.000%  crushed 0.000%
Angle B mean 146.8  max 250  min 14  blown 0.004%  crushed 0.000%

## CRITICAL BUG — imported meshes must be saved
`StaticMeshTools.import_file` creates a StaticMesh asset in memory but does NOT
persist it. All 66 chamfered meshes were lost on the next editor restart and
194 components had their mesh reference silently nulled on load - they simply
rendered nothing, with no error or warning. Content/Stacktown/Meshes had 0
files on disk.

Symptom to watch for: a capture whose histogram is suspiciously narrow
(max 203 / min 77 instead of max 250 / min 19) because most of the scene is
missing rather than dark.

Fixed: stage1_chamfer.py now saves after import. reimport_meshes.py rebuilds
all 66 from the archived OBJ sources in Saved/Stage1/obj and Saved/Stage0/obj.
Recovery cost minutes because the scene rebuilds from script - that is the
whole argument for scripted builds over hand-authored state.

## F1 — FAILED (2026-08-23)

Verdict, unprompted: "it looks like a rendering still, not like a photo of a
model of a building."

A1-A6, B1-B6, C2/C3/C4, D1-D4, E1-E6 all PASS. F1 fails.

Per ONE_BUILDING_GATE.md this is the most valuable possible result: it means
the cause is something none of the A-E lines measure. Do not add content, do
not enable DOF, do not buy an asset. Find the cause first.

## Paper texture pass (2026-08-23)

The 9 m close-up showed the surfaces had nothing to resolve as a player
approaches - parameter-only materials (colour + roughness + specular, no maps)
cannot serve a zoom range. MASTER_MATERIAL_SPEC specified a ~0.5 mm micro-normal
and fine surface noise from the start; the simplified master skipped them.

Generated procedurally, no external assets: `Content/Python/papertex.py`
  T_PaperNormal  512px tileable fibre normal (stretched value noise, 2 axes)
  T_PaperDetail  512px greyscale, drives roughness variation
Sources archived at Saved/Stage1/T_Paper*.png

Wired by `Content/Python/wire_paper.py`. The meshes have no UVs, so the textures
are projected from WORLD POSITION masked to X and Z - correct for the facade,
the dominant visible surface. One 512 px tile per 20 uu = 0.39 mm per texel,
matching the spec's feature size. The roughness alpha moved off the old
procedural Noise node (which varied over ~1 cm and averaged flat at any real
distance) onto the detail map.

### Two bugs worth not repeating
1. Texture compression must match SamplerType. T_PaperNormal imported with
   default sRGB colour compression while the sampler declared
   SAMPLERTYPE_Normal - a hard compile error. Set TC_NORMALMAP + srgb=False.
2. ComponentMask's input pin is UNNAMED - `get_expression_input_names` returns
   ["None"], and connecting with 'Input' silently fails. WorldPosition also
   needs its output named explicitly ('XYZ'). The failed connection produced
   "(Node ComponentMask) Missing ComponentMask input" and the whole master fell
   back to the Default Material, turning every surface muddy brown.

Symptom to recognise: EVERY surface goes flat muddy brown at once = the master
failed to compile. Check the log for "Failed to compile Material" and then for
"Material failed to compile:" which names the offending node.

Hero after: mean 150.5 max 249 min 20, 0.000% blown, 0.000% crushed.

## F1 — PASS at the approved camera (2026-08-23)

Cold read, five angles, no explanation given. Verdict: read as a MODEL through
the wide and mid frames; broke at the close-up.

Gate wording: "Shown the capture with no explanation, a person says it looks
like a photograph of a physical model." The capture is the approved-camera
capture - CAM_Hero at 95 m. At that camera it read as a model. **F1 PASSES.**

Being precise about scope rather than generous: the close-up that broke it is
NOT the approved camera. It is an exploratory view I introduced to test how the
build holds at player range. It was never part of the gate.

### The newly named finding
The illusion is OBJECT-scale, not SURFACE-scale. It holds while the viewer sees
the whole thing as an object on a board, and fails once they are close enough to
read an individual surface. Everything the gate measures - reveal, material,
light, exposure, evidence - is satisfied, and the failure lives somewhere the
gate never looks: mm-scale evidence of making. Cut marks, glue, crushed edges,
fibre lifting at a corner, the small damage a hand leaves.

This matters for the stated end goal (a living diorama city a player can zoom
into) but it is NOT a gate failure and must not be treated as one. It is the
next question, and it is the owner's to open.

STAGE 1 STATUS: gate satisfied at the approved camera. NOT a finished hero -
see the owner's framing below.

### Owner's framing of the F1 pass (2026-08-23)
Not a hero-quality result. Proof of direction, not a finished look. The gate is
satisfied at the approved camera and that is worth recording, but there is
substantial work left before this reads as a model at every range a player would
use. The surface-scale problem is being addressed BEFORE any new scope opens.

## Surface-scale pass 1 — edge wear (2026-08-23)

Addressing the close-range break rather than opening new scope.

### Edge wear — the last unbuilt MASTER_MATERIAL_SPEC feature
Spec asked for "curvature-driven lightening" and there is no curvature data on
these meshes, which is why it was skipped. But every surface here is an
axis-aligned box face or a 45 deg chamfer facet, so the world normal IS a
curvature proxy:
    flat face  max(|n|) = 1.0      chamfer  ~0.707      corner  ~0.577
    wear = saturate((1 - max(|n|)) / 0.30)
Drives an albedo lift (EdgeWearLift 1.42) on chamfers and corners only.
Built by `Content/Python/edge_wear.py`.

### Chamfer 2.5 mm -> 40 mm
2.5 mm was chosen as "fabrication-plausible" in ABSOLUTE terms and never paid
for itself - sub-pixel at every range a player uses. Proportionally it was also
wrong: a 300 mm facade standing in for ~1 mm card puts this build near 1:300,
where a crushed cut edge is tens of millimetres.

40 mm reads ~11 px at the 9 m close-up and 0.27 px at the 95 m hero - visible
when you walk up, invisible before, which is the correct behaviour. The
generator's clamp (chamfer <= 45% of smallest dimension) protects thin parts.

58 meshes regenerated as SM_Cw_*, imported AND SAVED, 242 components swapped,
0 lost materials. Sources in Saved/Stage1/obj_w.

Result: mullions and frames now read as cut card strips with crushed edges
rather than flat bars. Hero unchanged: mean 150.9 max 250 min 21,
0.000% blown, 0.000% crushed.

STILL OPEN at surface scale: glue, deliberate small damage, fibre lifting at a
corner, panel seams (the third spec feature still unbuilt).

### Fire escape removed
It spanned X 30-200, directly over bay 0's window (X 60-300), occluding that
window's mullion grid entirely and clipping the facade. Removed by
`Content/Python/drop_fe.py`. A6 (fitted elements at model tolerance) is still
satisfied by the canopy, the balcony and the rooftop unit.

### Panel seams — v1 was wrong, and the way it was wrong is the finding
v1: world X and world Z each folded to a seam profile and combined with Max,
spacing 150 uu, width 6 uu. It worked exactly as written and that was the
problem.

Cranked to SeamDarken 0.55 for a diagnostic (HighresScreenshot00067) the
pattern is unmistakable: a uniform square grid over the whole facade. Softened
to 0.90 it does not stop being a grid, it just becomes a faint one. **A regular
XZ grid reads as cladding panels on a building — the opposite of the cue we
want.** Scoping it to card-only roles fixed the backdrop tiling but not this.

v2 (`Content/Python/seam_v2.py`), two corrections:

1. **Vertical only.** Horizontal division is already carried by the floor-band
   mouldings, which are geometry and throw real shadows. A second horizontal
   set laid on top of them is what made the grid. Card sheets butt vertically;
   the horizontal joints are the section stack, and those already exist.
2. **Irregular.** Evenly spaced anything reads as machined. World X is offset
   by sin(2*pi*X/900) * 55 before the frac — the offset depends on X alone, so
   every line stays perfectly vertical while the spacing goes uneven. A second
   sine (period 1700) varies joint strength between 0.36 and 1.00 so they are
   not all the same weight.

Spacing 150 -> 380 uu. At 150 the facade carried ~9 joints across three bays;
a card model has a joint per sheet, not per window.

Only the mask was rebuilt — the existing lerp's Alpha was rewired — so the
SeamSpacing / SeamWidth / SeamDarken parameter names and every instance
override survived. Ceilings: MI_concrete 0.86, MI_paint_cream 0.87,
MI_model_board 0.90. Seams stay OFF (1.0) on the eight non-card roles.

**Measured** (HighresScreenshot00068, hero, detrended against a 121 px moving
baseline to remove the facade's lighting falloff):

    joints in the flat card strip   2, spaced 304 px
    depth below local baseline      33.7 and 35.0 levels
    residual sd                     8.66   (per-pixel grain floor sd 4.8)

Clear of the grain floor, so they read; narrow enough not to dominate. Hero
histogram unchanged: mean 150.9, max 249, min 22, 0.000% blown, 0.000% crushed.

MEASUREMENT TRAP: the first attempt measured a raw column mean and reported the
vertical seams as absent (1.4% amplitude vs 6.7% horizontal). They were not
absent. The facade has a lighting gradient across it whose swing dwarfs a seam,
and the patch happened to sit between two joints. Both ComponentMask nodes were
verified correct (R-only and B-only) before the cause was found. Detrend before
concluding a feature is missing, and confirm with a cranked diagnostic render
rather than a statistic.

STILL OPEN at surface scale: glue, deliberate small damage, fibre lifting at a
corner. The 9 m close-up (HighresScreenshot00069) shows why this matters — at
that range the wall between windows is a flat, featureless expanse. Seams are
sparse by design there (frame width 463 uu against 380 uu spacing puts at most
one joint in frame), so they are not the answer to the close-up.

### The missing mullions were never missing — the room set never followed its floor
Reported as "the upper right window still has no mullions" after the fire
escape came out. The components were all present: right mesh, right material,
visible=True, correct X/Z, and a line trace from the hero camera reached them.

The room set — Reveal, RoomFloor, RoomCeil, RoomSideL, RoomSideR — takes its X
and Z from the floor actor but its **Y was written in world space** and is
identical on every floor and every bay (Reveal Y=56.00, Room* Y=49.50).
Everything else in the window follows the floor, including the per-floor offset
and yaw from the hand-made-tolerance pass.

So the reveal's front face, fixed at world Y=39.50, cuts the window assembly at
a different depth in every bay. Floor 4 drifted back until its glass sat at
Y=46.33 — 6.83 uu BEHIND that plane — and the reveal's dark outer face became
what the camera sees. A flat dark rectangle with no mullions. Floor 2 bay 0 was
1.75 uu from the same failure, so this was fragility, not a one-off.

Two constraints, and the first fix only honoured one:

    front > glass Y   or the reveal's outer face swallows the window
    front < 60        or the core (MI_concrete, cream) shows through instead

Using the floor-1-bay-0 relationship unclamped (front = glass + 21.85) put
floor 4's reveals at 68.18, behind the core's front face at Y=60, and every
top-floor window went cream. Corrected to
`front = clamp(glass Y + 21.85, 39.50, 56.00)` — the authored plane as the
floor, 4 uu of core clearance as the ceiling. Bays that never drifted keep
their exact original numbers; 40 components moved. All 12 bays now assert clean
on both constraints. `Content/Python/fix_reveal2.py`.

DIAGNOSTIC NOTE: bay indices are mirrored in frame. The hero camera faces +Y at
yaw 90, so its right vector is -X and **higher X renders further left**. The
"upper right" window is bay 0, not bay 2. Half an hour went into proving bay 2
was fine — which it was.

### Viewport capture regression
The editor is in a **FourPanes2x2** layout. In that layout `pilot_level_actor`
moves the viewport to the camera but does NOT adopt its FOV — the pane stays at
the default 90 deg and renders the model at about a quarter size. The `FOV`
console command does not route there either. The working setter is
`LevelEditorSubsystem.set_level_viewport_fov(fov, key)` — note the argument
order, fov first — against `get_active_viewport_config_key()`.

Saving the level resets it, so it has to run immediately before every capture,
not once at setup: `Content/Python/prep_shot.py`.

Captures in this layout are 4436x2844, aspect **1.560**, not the camera's 3:2.
The framing is the pane's, not the filmback's. Recorded rather than corrected —
any capture offered as gate evidence needs the single-pane layout restored
first.

### Fabrication marks — glue, peeled facing; the ding was cut
23 components under a new `BLD_Marks` actor. Scale comes from the recipe's
1:300: a physical 0.4 mm glue squeeze-out is ~120 mm here, so the bead section
is 12 uu. That is ~8 px at the 95 m hero and ~115 px at a 9 m player zoom —
present but not legible far away, obvious close up, which is the whole point.

**Glue.** `MI_glue`, three runs: canopy top against the facade, under the
parapet cap overhang, and where the canopy fascia meets the slab top. The
material is what carries it, not the geometry — card is 0.62–0.78 rough at 0.20
specular, glue is 0.34–0.46 at 0.34. Roughness and specular are the two
properties the recipe says still read at range, so the bead is legible as a
DIFFERENT substance rather than a lump of the same card.

First attempt used 0.26–0.38 rough at 0.42 specular and the beads read as
BRIGHTER OBJECTS — white bars laid on the card — rather than card with a sheen.
Pulling the gloss back toward the card band and darkening the base fixed it.
Segments also had to overlap rather than sit in a spaced row: discrete bars
with square ends read as bars, whatever they are made of.

**Peeled facing.** Two failed versions before one worked, and the failures are
the finding:

  46 x 4 x 34 chamfered box, mid-face   a rounded tab stuck to the wall
  44 x 1.6 x 30 chamfered box, mid-face a thinner tab stuck to the wall
  purpose-built tapering peel, AT an edge   reads

A chamfered box cannot taper, and a lifted edge cannot occur in the middle of a
face. `Content/Python/peelgen.py` writes a sheet that is 0.18 of its thickness
at the attached edge, narrows to 42% of its width at the free edge, and curls
on v² rather than tilting flat. Two orientations are baked rather than rotated
— getting the lift direction 90 degrees wrong is invisible in a transform table
and obvious in a render. Four peels, all with their free edge landing on a real
cut edge.

**The ding was removed, not fixed.** A crushed corner needs material taken
away. Additive geometry can only add, so the block placed at the parapet cap
corner read as an extra tab stuck on the corner — the opposite of damage. The
GeometryScripting plugin is enabled in the uproject and is the honest path to a
real dent; it was not opened for this pass.

Hero unchanged in substance: 0.000% blown, 0.000% crushed, every mark invisible
at 95 m. Mean reads 105.9 against the earlier 150.9, which is the FourPanes2x2
aspect (1.560) pulling in more dark backdrop, not a lighting change — the two
numbers are not comparable across viewport layouts.

STILL OPEN at surface scale: the glue runs still read slightly as low rails
rather than squeeze-out, because every segment is the same section. A bead
whose thickness varies along its length needs the same treatment peelgen got.

### Hero framing corrected without touching the editor layout
The FourPanes2x2 pane is 1.560, and `set_level_viewport_fov` sets HORIZONTAL
FOV, so 28.84 in this pane gives an 18.72 deg vertical against the authored
19.454. Setting HFOV to **29.939** reproduces the authored vertical exactly;
cropping the 4436-wide capture to a centred 4266x2844 gives a true 3:2.
Verified by facade silhouette width: authored 34.0% of frame height,
corrected 34.1%.

MEASUREMENT TRAP, twice in one sitting. Two different absolute-luma thresholds
both reported the framing as catastrophically wrong — "board 83.7% vs 52.2%",
then "facade width 84.95% vs 36.29%" — because the backdrop's brightness
differs between captures and the threshold was swallowing backdrop and building
together. The real error was 4%. Absolute-threshold measurements across
captures with different exposure or vignetting are worthless; find edges by
local GRADIENT instead.

### Glue taper and a real dent — plus a live bug the second editor exposed
Both landed. The route to each was mostly finding out how the first version was
wrong.

**Bead taper.** `Content/Python/beadgen.py` sweeps a K-gon along X with the
radius driven by a smooth end-taper times two out-of-phase sines, so no two
beads share a silhouette. Six variants; runs assemble them with the tails
overlapping. Ends close on a small cap — a true point makes degenerate
triangles the importer drops silently.

RUN CLAMPING was the non-obvious part. The first placement walked `while x < x1`
and centred each bead at `x + L/2`, so the last bead of every run hung up to
74 uu past the end of the building. At the parapet that rendered as a ribbon
floating in mid-air off the corner, which looked like a boolean failure and
sent me looking in the wrong place. Beads now must lie wholly inside the span,
falling back to the shortest variant that fits.

**The dent, by subtraction.** GeometryScripting, first use in this project.
Copy the cap into a DynamicMesh, subtract two scaled spheres at the +X
front-top corner, `set_per_face_normals`, write back to a duplicated asset.
The cap mesh was verified to have exactly one user (BLD_Roof/ParapetCap)
before anything was touched. 44 tris -> 276.

    SIZE THE TOOL AGAINST THE MATERIAL, NOT THE OBJECT.

The cap is 1100 long but only 12 THICK. Radius 21 spheres — modest against
1100 — cut clean through and left a writhing ribbon. Radius 9 and 6.5, centred
mostly ABOVE the top face so only the lower cap enters, removes ~2 uu of 12.

`recompute_normals` with default options averaged across the box faces and
turned crisp card into a soft ribbon. Card has hard edges: `set_per_face_normals`.

`assign_dent.py` originally read the component's CURRENT material to restore it
after the mesh swap. That breaks on a re-run — deleting and re-duplicating the
mesh asset drops the component to WorldGridMaterial, which then gets faithfully
re-applied. Assign the role explicitly.

### The remote-execution channel was connecting to the wrong editor
A second agent's editor appeared on the multicast group
(`.../MONEYVILLE/UnrealSandboxes/StacktownPortlandGate1/`) and exposed a bug
that had been latent all session:

    rem.open_command_connection(node)      # node is a DICT
    open_command_connection(remote_node_id)  # wants the ID STRING

With one editor on the group this worked by luck. With two it connected to
whichever it liked — in practice the other agent's — and four consecutive runs
executed there. Fixed to pass `node['node_id']`.

Two further fixes in `uepy.py`:
- the discovery loop exited on the FIRST node to answer, so the other editor
  could win the race and this would report "no node for project" while ours was
  still answering. It now waits for OUR project root specifically.
- `remote_nodes` rebuilds its dicts on each access, so identity comparison
  against a previously-taken node never matched. Snapshot once.

Selection alone is not enough. `Content/Python/_guard.py` is prepended to every
mutating script (`rung.sh`) and aborts unless `Paths.project_dir()` is
StacktownAlpha AND the level is Stage1_Building. It is what caught the
mis-routing — nothing was written to the other project.

**Hero:** 0.000% blown, 0.000% crushed, marks invisible at 95 m.
CAVEAT: mean reads 107.2 against the authored 150.9 and the two are NOT
comparable. The vignette is computed over the pane's frame, so a 4436-wide pane
cropped to 4266 carries more corner falloff than a native 4266 render. Framing
itself is verified identical (facade silhouette 34.1% vs 34.0% of frame
height). A mean directly comparable to the record needs the single-pane layout.

### I crashed the editor: do not call load_level over remote execution
`LevelEditorSubsystem.load_level()` invoked through UE's Python remote-execution
channel killed the editor:

    SIGSEGV: invalid attempt to access memory at address 0x3
      UEditorEngine::Map_Load
      ULevelEditorSubsystem::LoadLevel
      FPythonScriptRemoteExecutionCommandConnection::Tick

The map load tears down the current world from inside the remote-execution
ticker. `s1_ready.py` has carried this call all session behind an `if` that
never fired, so it was never exercised until it mattered.

**Do not retry it** — same standing rule as `StaticMeshDescription.create_polygon`,
which crashed the editor earlier in this project. Change levels from the Content
Browser, or set the startup map in config and restart.

No work was lost: `Stage1_Building` had been saved at 17:48 with zero dirty
packages verified, and `Stage2_Block` was duplicated and saved before the crash.

RESTART NOTES, both cost time:
- `open <file>.uproject` passes only the project NAME to the engine, which then
  looks for it under the engine directory and exits with "Could not find a valid
  project file". Launch the binary with the full path instead.
- `open -a <app>` ACTIVATES an already-running instance rather than starting a
  new one. With another editor already up, nothing happens at all. Use `open -n -a`.

Also worth noting: two UE editors on a 32 GB machine is tight, and the engine
logged `MemorySharingInfo: UsedMemory=428641MiB, MaxMemoryAvailable=32768MiB`
around the failure. Memory pressure may have contributed.
