# Stage 0 — bay recess comparison, scene record

Built 2026-08-22, rebuilt and captured 2026-08-23. Level SAVED as
`/Game/Maps/BayRecessTest`. `/Game/Maps/OneBuildingTest` does not exist; nothing
protected was touched. Rebuildable from `Content/Python/stage0_build.py`.

## The variable
| Actor | Window recess from wall face |
|---|---|
| BLD_Bay_A | 75 mm |
| BLD_Bay_B | 150 mm |
| BLD_Bay_C | 250 mm |

Everything else identical. Scale 1 uu = 1 cm. Bays abut at X = 0 / 360 / 720 uu,
forming one continuous facade so all three sit under identical light.

## Geometry (per bay, from BAY_RECIPE.md)
bay width 3600 · floor-to-floor 3600 · wall thickness 300 · opening 2400w x 2100h
sill projection 40, thickness 60 · mullion 60 deep x 50 wide · glass 80 behind
mullion face · spandrel recess 40 · interior card 400 behind glass.
Head and jamb reveals equal the recess by construction.

## Light rig
LIGHT_Key   RectLight, 4500 K, 300000 lm, source 900x600, 45 deg off camera axis
            in plan, 35 deg elevation, attenuation 8000
LIGHT_Fill  RectLight, 7200 K, 40000 lm, source 1400x900, opposite side (~1/8 key)

## Camera (CAM_Hero, CineCameraActor)
70 mm on 36 x 24 mm full-frame back (h-FOV 28.84 deg)
location (540, -2378, 685) · rotation pitch -12, yaw 90 · DOF focus method Disable

## Exposure (LOOK_Post, unbound PostProcessVolume)
Manual (AEM_Manual), ISO 800, f/4, 1/60 s  ->  EV100 = 6.91
Bloom 0 · motion blur 0 · auto-exposure bias 0

## Materials
M_StacktownMaster + 6 instances (concrete, paint_cream, dark_metal, glass,
model_board, studio_grey). Roughness = Lerp(RoughMin, RoughMax, fine noise),
painted band 0.35-0.55, glass 0.02-0.08. 40/40 components assigned.

## Approved captures (gate evidence)
`stage0_hero_70mm.png`   CAM_Hero   (540, -2378, 685) pitch -12 yaw 90
`stage0_angle_70mm.png`  CAM_Hero_B (1545, -2155, 685) pitch -12 yaw 115
Both: 70 mm on 36x24 full frame, 3270x2180 (HighResShot 2), aspect 1.5,
fixed manual exposure EV100 6.91 (ISO 800, f/4, 1/60), DOF/bloom/motion blur off,
Game View on. Measured: 0.00% blown, 0.00% crushed, max 237/238, min 24/15.

## Critical editor setting
The perspective viewport had `ExposureSettings=(FixedEV100=1.0,bFixed=True)` in
`Saved/Config/MacEditor/EditorPerProjectUserSettings.ini`, which OVERRODE the
PostProcessVolume and rendered ~6 stops hot. Set to bFixed=False. If captures
ever come back blown, check this first. Backup: same file + `.bak-stage0`.

## Capture procedure that works
Pilot the camera (viewport must show the "Piloting" bar), press G for Game View,
then `HighResShot 2`. A correct frame is 1.5 aspect; 1.86 means it was NOT
piloted and is invalid (wrong FOV and wrong exposure).

## Known gate failures
B6 (zero-radius edges), E5 (perf not measured), E6 (validation not run).
The diag*.png files in this folder are DIAGNOSTIC ONLY, not gate evidence.

---

## Phase 3 — controlled recess experiment (2026-08-23)

The original side-by-side layout CANNOT rank the three depths:
  1. The sill reveal is invariant (dominated by the fixed 40mm projection and
     60mm thickness), so the most prominent feature carries none of the variable.
  2. Bay B sits on the camera axis head-on, so its jamb reveal is zero by
     construction. Never put a variant in the centre slot.
  3. The angled view confounds recess with obliquity (obliquity falls A->C
     while recess rises).

Redone by translating the WHOLE RIG (camera + both lights) per bay so each bay
is shot at an identical position, obliquity and lighting angle. Only recess varies.

| Recess | Jamb reveal | % of frame width |
|--------|-------------|------------------|
| 75 mm  | ~5 px       | 0.15%            |
| 150 mm | ~8 px       | 0.24%            |
| 250 mm | ~13 px      | 0.40%            |

ANSWER: 250 mm at the approved camera. 75 mm is a hairline (~2px at normal
viewing) and is effectively the flat-plane failure. 150 mm is the legibility floor.

The generalisable rule matters more than the number: **required recess is a
function of camera distance.** A reveal needs to subtend roughly 0.4% of frame
width to read. The recipe's framing (three bays filling frame at 70mm -> ~24m)
is what forces 250 mm. A closer camera needs less depth.

Captures: phase3_bay{A,B,C}_*.png, phase3_recess_compare.png

## Phase 4 — B6 edge bevels: BLOCKED

GeometryScripting plugin was enabled in the .uproject (backup:
StacktownAlpha.uproject.bak-stage0). It mounts and its modules load, BUT:
  - `GeometryScriptLibrary_MeshBevelFunctions` does not exist in Python at all
    (load_object returns None). Bevels are not reachable from Python in UE 5.8.
  - `GeometryScriptLibrary_MeshPrimitiveFunctions` exists as a UClass but has
    no Python binding.
  - Authoring meshes via StaticMeshDescription is a dead end: `create_polygon`
    is bound as create_polygon(group) -> tuple, exposing its INPUT vertex
    instances as OUTPUTS. Creating an empty polygon then calling
    set_polygon_vertex_instances CRASHED THE EDITOR
    (Assertion failed: (Index >= 0) & (Index < ArrayNum), Array.h:1339).
    Do not retry that path. No work was lost; the level was already saved.

Remaining options for B6: author chamfered boxes as OBJ on disk and import
them; bevel by hand in Modeling Mode; or carry B6 as a documented failure.

## Editor capture gotchas (cost several captures each)
  - `pilot_level_actor` takes effect on the NEXT tick. Piloting and shooting in
    the same call captures the pre-pilot viewport (comes out 1.86 aspect).
  - UE throttles rendering when not the foreground app, so a deferred
    HighResShot silently writes nothing. Fix: `Slate.bAllowThrottling 0`.
  - Never `time.sleep()` inside a remote-exec script: Python runs on the game
    thread, so the editor cannot tick and the screenshot never services.

## Phase 4 — B6 edge chamfers: DONE (2026-08-23)

GeometryScripting was enabled (kept, for future Blueprint work) but does NOT
provide bevels to Python. Route taken instead: author chamfered boxes as OBJ on
disk, import via `StaticMeshTools.import_file`.

Generator: `Content/Python/objgen_chamfer.py`. OBJ sources: `Saved/Stage0/obj/`.
A chamfered box = 6 inset face quads + 12 edge strips + 8 corner triangles = 26
polys / 44 triangles. Winding fixed by Newell normal vs centroid (valid because
the solid is convex and centred). Chamfer 0.25 uu = 2.5 mm world.

10 distinct meshes -> /Game/Stacktown/Meshes/SM_Cx_<x>_<y>_<z>
32 of 40 components swapped, scale reset to 1, material overrides preserved.
Verified: 0 wrong scales, 0 lost material overrides.

Deliberately left as plain boxes (8): Glass x3 and InteriorCard x3 (1 uu thick,
a chamfer would consume most of the thickness and they sit behind the mullion
frame), STAGE_Backdrop and STAGE_Ground (edges outside the approved framing).

Result: at the approved camera a 2.5 mm chamfer is sub-pixel, so it reads as a
faint specular line rather than visible geometry - which is what a softened edge
looks like at 24 m. The unexpected bonus is that box-to-box junctions now read
as PANEL SEAMS, so the facade reads as assembled pieces rather than a monolithic
slab. That is a fabrication cue (gate C3 territory, not scored in Stage 0).

Evidence: phase4_hero_beveled.png, phase4_bevel_before_after.png

## Phase 2 — E5 / E6 (2026-08-23)

### E6 — PASS
`Content/Python/stacktown_validation.py` run against the live project:
  assets_scanned 17 | hard_failures 0 | warnings 0
Report: Saved/Validation/stacktown_validation.json
Advisories only: METADATA_ADVISORY_ONLY, NO_OWNED_PCG_GRAPHS.

### E5 — PASS (measured on the Mac mini at the approved camera)
Machine quiet: StacktownAlpha the only editor running (~18% CPU).
An earlier attempt read 37-58 ms; that was CPU contention from a second editor
running the archived bakeoff project at 92% CPU, not the scene. A further
attempt read a flat 333.333 ms (exactly 3 fps) - that is UE's background
throttle, not a measurement. The editor must be FOREGROUND to measure.

  Wall frame time   16.8 ms   (60 fps; display-capped at 60 Hz - unchanged
                               with r.VSync 0 / t.MaxFPS 0, so it is the
                               display refresh, not the scene)
  GPU frame total   15.758 ms (ProfileGPU, at the approved camera)
  Resident memory   0.91 GB   (StacktownAlpha editor RSS)

GPU breakdown - where the 15.758 ms actually goes:
  15.191  Scene
   7.243  RenderDeferredLighting
   5.405  DiffuseIndirectAndAO      <- Lumen
   5.222  PostProcessing
   5.189  LumenScreenProbeGather    <- Lumen
   5.118  TemporalSuperResolution
   2.526  UpdateWorldRadianceCaches

FINDING: the cost is almost entirely FIXED RENDERER cost - Lumen GI plus TSR -
not scene complexity. 40 components at 44 triangles each is nothing. GPU sits at
~94% of the 60 fps budget with essentially no geometry in the scene, which means
Stage 1 (a whole building) would add little GPU cost, but also that there is
little headroom before Lumen settings have to be revisited.

Note: r.VSync 0 / t.MaxFPS 0 / Slate.bAllowThrottling 0 were issued as console
cvars for measurement only; they are not persisted and reset on editor restart.

## F1 — NOT TESTED (owner-deferred, 2026-08-23)

F1: "Shown the capture with no explanation, a person says it looks like a
photograph of a physical model."

Status: **NOT RUN.** The owner elected to defer it and proceed. Recorded here as
deferred rather than passed, because no person has been shown the capture cold.
This is not a failure — it is an untested line.

Agent's own read (not a substitute for F1): the capture reads as a white
architectural study model on a board. The chamfer-induced panel seams help it
read as assembled rather than monolithic. What holds it back is the complete
absence of fabrication imperfection (gate C3, which Stage 0 does not score) and
the uniformity of the surfaces - no edge wear, no paint variation, no seams
beyond the structural ones.

To run it later: show Saved/Stage0/stage0_hero_70mm.png to someone who has not
seen this project, with no explanation, and ask what they are looking at.

## Stage 0 gate summary
  A1, A2                 PASS
  A3-A6                  NOT APPLICABLE (roof/entrance/curb/silhouette are
                         forbidden in Stage 0 by BAY_RECIPE.md - unresolved
                         conflict with ONE_BUILDING_GATE.md, owner decision)
  B1-B6                  PASS
  D1-D4                  PASS
  E1-E6                  PASS
  F1                     NOT TESTED (deferred)

## The Stage 0 recipe (the deliverable)
  Window recess          250 mm at the approved camera. 75 mm does not read.
                         General rule: a reveal must subtend ~0.4% of frame
                         width, so required depth scales with camera distance.
  Sill                   40 mm proud, 60 mm thick (its front face dominates the
                         near-window read and is independent of recess).
  Spandrel recess        40 mm secondary plane.
  Edge chamfer           2.5 mm. Sub-pixel at 24 m; its value is the panel seams
                         it creates at box junctions, not the edge softening.
  Master material        One master, instanced per role. Painted roughness band
                         0.35-0.55, glass 0.02-0.08.
  Light rig              Rect key 4500 K 300k lm + Rect fill 7200 K 40k lm,
                         attenuation 8000 (default 1000 does not reach).
  Camera                 70 mm on 36x24, -12 deg pitch, fixed manual exposure
                         EV100 6.91 (ISO 800, f/4, 1/60).
  Do NOT put a variant   on the camera axis - its jamb reveal is zero.

## Gate amended — Stage 0 carve-out (2026-08-23, owner decision)

`Docs/ONE_BUILDING_GATE.md` now carries a Stage 0 carve-out, and
`Docs/BAY_RECIPE.md` line 71 was corrected (it claimed the bay numbers satisfy
"A1 through A4"; a bay has no entrance, so it is A1-A2).

Resolved status of the two open items:
  A3-A6   formally NOT APPLICABLE at Stage 0, deferred to Stage 1.
  F1      formally DEFERRED to Stage 1. Owner's rationale: a single bay cannot
          answer whether the result reads as a real diorama model; that needs a
          full small building, because a person responds to the whole object.

The gate's claim that "Stage 0 answers the identical question a building would"
is narrowed by the amendment: Stage 0 answers whether a SURFACE reads as
fabricated. Whether the OBJECT reads as a model is now Stage 1's question.

Guards written into the carve-out so the deferral cannot become a waiver:
  1. Stage 1 is judged against the whole gate, F1 included, no further carve-out.
  2. F1 must be tested before ANY scope beyond Stage 1 opens.
  3. F1 is tested as written - a person who has not seen the project, shown the
     capture with no explanation. An agent's opinion never satisfies it.
  4. If A-E pass at Stage 1 and F1 fails, that is the most valuable result and
     the cause must be found before anything else is built.

Accepted cost, recorded: the gate existed to answer the visual question cheaply
("for $0 instead of $200 and a month"). Deferring F1 gives that up. The Stage 0
recipe now carries into Stage 1 as an untested premise. Owner's accepted risk.

STAGE 0 STATUS: complete under the amended gate. All applicable lines pass.
