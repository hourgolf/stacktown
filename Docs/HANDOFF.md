# Stacktown — Team Handoff

**Written 2026-08-24.** This is the entry point for anyone joining the project.
Read this, then `AGENTS.md`, then `Docs/ONE_BUILDING_GATE.md`.

---

## 1. What this is

A **living diorama city**. Not a photoreal city — a city that reads as a
*physical card and paper model sitting on a board under studio lights*, which
the player can zoom into. The distinction governs every technical decision here.

The project has three generations. Two failed the same way and the third exists
because of it:

| generation | outcome |
|---|---|
| `StacktownUSA` (Unity) | abandoned |
| `StacktownVisualBakeoffUE` (Codex) | abandoned |
| `StacktownAlpha` (this) | current |

**The documented failure mode of both predecessors was adding features to route
around a failing visual gate.** That is why this project is gated, why evidence
lives under `Saved/`, and why the correct response to a failure is to stop and
say so.

## 2. Current state

A **two-block street**, built by script, in `/Game/Maps/Stage2_Block`.

- **Block A** — 4 buildings: 2 generated, 1 Assetsville tileset volume, 1 reused Stage 1 building
- **Block B** — 3 buildings, generated, rotated 180° across the road
- Street, pavements both sides, trees, parked vehicles, pedestrians, rooftop clutter
- Practicals behind glazing on both blocks

Verified at the block hero: **blown 0.000%, crushed 0.000%**, geometry check
passing, no hollow facades.

### What is NOT done

- The far side of the street is underlit. The key/fill rig was derived for a
  single row facing −Y and has never been re-derived for two facing rows.
- The backdrop does not cover the view down the street; there is black void past
  the board edge.
- Props, trees and vehicles exist only on block A's pavement.
- Edge wear does not work on imported geometry (see §5).
- There is **no gameplay of any kind**. Not a line. This is a visual proof.

---

## 3. How the work is judged

The gate (`Docs/ONE_BUILDING_GATE.md`) has lettered sections. Two carve-outs
have been approved by the owner and are recorded in that file with dates: Stage 0
(three bays) and Stage 2 (one block).

**The single most important rule:** the illusion question — *does this read as a
physical model?* — is settled by a **cold read from a human who has not seen the
project**. An agent's own opinion never satisfies it. Measurements support that
judgement; they do not replace it.

### The 0.4% rule

**A feature must subtend roughly 0.4% of frame width to read.** Required depth is
a function of camera distance, not an absolute. This is the most transferable
finding in the project.

| framing | distance | frame width | 0.4% threshold |
|---|---|---|---|
| player zoom | 900 uu | 463 uu | **19 mm** |
| approach | 3,500 uu | 1,800 uu | 72 mm |
| block hero | 11,168 uu | 5,744 uu | **230 mm** |

Consequence: at block range the *window recess* — the entire subject of Stage 0 —
is 1.1× threshold and cannot be relied on. Silhouette and mass carry the read.
Surface work (seams 6 uu, glue 12 uu, chamfers 4 uu, the dent 2 uu deep) is
**invisible** at block range and earns its keep only at the player zoom.

---

## 4. Architecture

### 4.1 Buildings are parameter sets

`Content/Python/genbuild.py` → `build(spec, origin, yaw)`.

A building is a dict: width, depth, floors, floor heights, parapet, bay count,
canopy, setback, roof units, seed, wall role. Lot coordinates are **block-local**;
the block's world placement lives on the actor transform. That is what allows a
block to be dropped anywhere and rotated.

`Content/Python/city.py` is the city table — a block is an origin, a yaw, and a
list of lots.

### 4.2 Material role lives in the component name

`Wall_`, `Band_`, `Glass_`, `Interior_`, `Frame_`, `Mullion_`, `Accent_`, `Roof_`.
One sweep (`step_roles.py`) assigns every slot in the level. **Adding a building
costs nothing in material work.** This is the single most important scaling
property in the codebase — do not break it.

Imported assets bind by material *slot name* instead, which is why the
Assetsville **tileset** is usable (mesh names carry role) and its four complete
buildings are not (`customMat_01`..`customMat_14` carry nothing).

### 4.3 One master material, role instances only

`M_StacktownMaster` plus `MI_*` instances. **Do not add a second master.**
There is a two-sided variant (`M_StacktownMaster_2S`) for single-sided shell
geometry such as vehicles.

### 4.4 Everything is checked by script

`build_block.py` runs the build then the checks. Both live in the pipeline, not
in someone's memory:

- `check_block.py` — world AABBs, party-wall adjacency, **carries a self-check**
- `gap_check2.py` — no hollow facades

### 4.5 Capture

Fixed manual exposure, 70 mm on a 36×24 back, **no DOF, bloom or motion blur**
(gate section E). Film grain, vignette and chromatic aberration are permitted and
are worth having — they read as evidence a camera existed.

---

## 5. Traps — read this section twice

Every item cost hours. They are ordered by how much.

### Editor and tooling

- **`load_level` over remote execution crashes the editor.** SIGSEGV in
  `Map_Load` from inside the remote-exec ticker. Change levels from the Content
  Browser or set the startup map in config and restart. Do not retry it.
- **Spawning several skeletal meshes in one call crashes the editor.**
  `VertexFactory->IsReadyForStaticMeshCaching()`. One is fine, eight is not.
  Bake skeletal → static via GeometryScripting instead; it is the right answer
  for a city anyway.
- **Never put non-`.py` files in `Content/`.** UE's importer picks up a `.json`
  and opens a modal DataTable dialog, which blocks the game thread. The editor
  then looks hung: alive, ~100% CPU, no log activity, remote exec dead. **That is
  a modal, not a crash** — a real crash writes an assertion and an exit.
- **`MODE_EXEC_FILE` takes a path, not source text.**
- **`unreal.Rotator(a, b, c)` is `(roll, pitch, yaw)`.** Passing `Rotator(0,90,0)`
  for "yaw 90" sets pitch and lays everything flat.
- **`set_level_viewport_fov(fov, key)`** — fov first. In a multi-pane layout
  piloting a camera does NOT adopt its FOV, and saving the level resets it, so it
  must run immediately before every capture.
- **`import_file` does not persist.** Save explicitly or the assets vanish on
  restart, silently nulling components.
- **Delete `.mcp_sid` after an editor restart** or every MCP call 404s.

### Material and geometry

- **Edge wear only works on 45° chamfers.** It is `saturate((1-max|n|)/0.30)`, a
  normal-as-curvature proxy. A 45° pitched roof gets 0.98 wear; a cylinder gets
  0.98 at its 45° points. **It does nothing on imported geometry.** Baked
  curvature is the fix and is not yet built.
- **`objgen.polys()` returns unoriented polygons.** `objgen.write_obj()` is what
  flips the inward-facing ones, and only while they are origin-centred. Reusing
  `polys()` without that step renders geometry inside-out.
- **Size a boolean tool against the material's thinnest dimension, not the
  object's longest.** A radius-21 sphere is modest against a 1100-long cap and
  catastrophic against its 12 thickness.
- **Keep normals flat after any boolean.** `recompute_normals` averages across
  box faces and turns crisp card into a soft ribbon. Use `set_per_face_normals`.
- **A chamfered box cannot be a lifted edge.** No taper, so it reads as a tab
  stuck to a wall at any thickness.
- **Additive geometry cannot make a dent.**
- **Baking skeletal → static loses material slot NAMES** (count survives). Read
  the roles from the source and apply positionally.

### Measurement — the most expensive category

**Three separate defects in this project existed for a long time because a check
was asking the wrong question and returning "ok".**

- **A test that has never been checked against a known answer is not evidence.**
  `check_block.py` carries a self-check for this reason. The overlap test was
  wrong twice before it was right: v1 added *local* mesh bounds to world location
  and ignored rotation; v2 used `get_actor_bounds`, which includes the actor root
  at the origin.
- **`core_check` compared only street-side edges** and passed all five buildings
  while every one of them was hollow behind the facade.
- **Absolute-luma thresholds are worthless across captures** with different
  exposure or vignetting. Find edges by local gradient. Two such measurements
  reported a 4% framing error as a 60% one.
- **Detrend before concluding a feature is missing.** A facade's own lighting
  falloff swings wider than any seam.
- **Locate defective pixels spatially.** Blown pixels forming a stripe every
  256 px identified per-floor practicals; 82% of crushed pixels in one 96 px
  column identified a 17 uu gap between buildings. Both beat adjusting by eye.
- **Do not invent a threshold and then judge against it.** The "surface must
  exceed sd 4.8" target was the *film grain* floor and had nothing to do with
  whether a surface reads as card.

### Process

- **Review the whole frame, not the thing you just changed.** A pass is finished
  when the frame has been walked, not when the last edit renders.
- **Vary one thing, and make sure it is the thing that differs.** The skeletal
  crash cause was announced after changing the setter while holding the actor
  count at one — the count was the variable that mattered.
- **Report a cause as a hypothesis until it is isolated.**

---

## 6. The recipe — measured numbers

Full detail in `Docs/MINIATURE_RECIPE.md`. Essentials:

    card material     roughness 0.62-0.80   specular 0.20   band width ~0.18
    glass             roughness 0.055-0.105 specular 0.55   opacity 0.42
    window recess     250 mm      sill 40 mm proud, 60 mm thick
    floor band offset 550-680 mm, uneven      canopy 2.2 m
    edge chamfer      40 mm       paper normal amplitude 2.0, triplanar
    hand tolerance    MODEL tolerances 1-2%, not building tolerances 0.15-0.4%
    light rig         Rect key 4500K 45° off axis, 35° elevation; fill 7200K ~1/8
                      intensity scales with the INVERSE SQUARE of rig distance
    exposure          ISO 800, f/4, 1/60, fixed. Bloom/DOF/motion blur OFF
    optics            grain 1.05, vignette 0.42, fringing 0.30

**No large-scale albedo variation.** Uniform in colour, varied in sheen and at
edges. This is the trap and it stays a trap.

---

## 7. Repository layout

    Content/Python/     all build scripts (see §8)
    Content/Stacktown/  our generated meshes, materials, textures  (~7 MB)
    Content/Maps/       sandbox maps
    Docs/               gate, recipe, provenance, this file
    Saved/Stage0..3/    evidence and records — READ THE RECORDS

**`Content/AssetsvilleTown/` is licensed marketplace content (680 MB) and is
excluded from the repository.** Anyone joining must add it to their own project
from their own Fab entitlement. Do not commit it.

---

## 8. Script index

    build_block.py      builds block A end to end, then checks
    build_blockB.py     builds block B
    city.py             the city table — origins, yaws, lots
    genbuild.py         the building generator
    bakegen.py          whole building as one mesh (fidelity gap open, see §9)
    step_roles.py       material assignment by role prefix
    step_cores3.py      per-band solid cores
    step_av.py          Assetsville tileset volume
    practicals.py       procedural interior lighting
    fix4_props.py       props with rooftop/street rules and a footprint test
    sk_bake_batch.py    skeletal → static bake
    triplanar.py        triplanar paper projection
    check_block.py      geometry + party walls + self-check
    gap_check2.py       hollow-facade check
    prep_shot.py        viewport into the hero state before a capture
    _guard.py           refuses to run in the wrong project or level

`rung.sh <script>` prepends `_guard.py`. **Use it for anything that mutates.**
Multiple editors run on this machine; the guard is what stops a script writing
into the wrong project. It has already caught it happening.

---

## 9. Open technical questions

1. **Single-mesh bake fidelity gap.** A baked building differs from its component
   original by 29.9 mean absolute luma against a 6.31 grain floor. Cause unknown.
   Eliminated: missing geometry, winding, chamfer, slot binding, floor pivot.
   Wins on component count (1 vs ~140), not on speed.
2. **Edge wear on arbitrary geometry.** Needs baked curvature.
3. **Masked foliage material.** Opaque card fills alpha-cut leaf gaps; the pack's
   own materials clash with the diorama. Neither works.
4. **Street lighting for two facing rows.**
5. **`PaperDetail` texture** — bound but its contribution is untraced.
