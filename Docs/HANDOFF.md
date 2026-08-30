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

**MESHES CURRENT THROUGH d30dc8b** (staleness ledger, maintained per bake
wave under the 2026-08-30 bake policy — POLISH_PROTOCOL "The bake
policy". HARD RULE: no acceptance or reader frames while this line names
a commit older than the fix being judged.)

**Updated 2026-08-25.** The authoritative current state is always the newest
record under `Saved/Stage*/` and `Saved/Lane*/` plus `Docs/RECIPES_DRAFT.md`
and `Docs/RUNTIME_SLICE.md` — this section is a summary and loses to the
records wherever they disagree.

**Nine built blocks** on a board grown north, in `/Game/Maps/Stage2_Block`:
the original facing street (blocks A and B), a civic square with a fountain,
a park with housing across from it, walk-ups, and block H — the works, with
sawtooth roofs and a stack. All generated from `city.py`/`genbuild.py`;
measured build rate **0.068 s per box**.

**The runtime slice is approved and partly wired** (`Docs/RUNTIME_SLICE.md`):
a catalogue `PrimaryDataAsset`, `BP_Parcel` with a mesh component, an
owner-wired `ResolveMesh` and CityTick graph, and a first measured tick
against real assets. A runtime upgrade is a mesh pointer swap against
pre-baked tier meshes in `/Game/Stacktown/Baked/`.

**Recipe status** (`Docs/RECIPES_DRAFT.md`): four ladders drafted
(vernacular, modern, deco, works). Pipeline expansion is deliberately
stopped; `vernacular` is being brought up to standard first. Cottage and
walkup are kept as **rough drafts** awaiting the same detailing pass (owner
decision, 2026-08-25). The per-model gate (`modelgate.py`), stamp
(`stamp.py`) and `catalogue_audit.py` are in place.

### Session of 2026-08-27 — catalogue, street, block rig

**The catalogue is 32 recipes across four eras**, eight each: vernacular, deco,
modern, contemporary. `Content/Stacktown/Baked/` holds **284 baked meshes**.
Contemporary was rebuilt against `CANON.md` slot 5 after the owner rejected the
first attempt as not reading as modern.

**A two-block street exists** in `Sandbox_Bench` (`street.py`) — sixteen
buildings in two facing rows against a road and pavements, built to test the
Stage 2 gate line that the work must read at BOTH block hero and player zoom.
**Player zoom passes.** Block hero was weak and has been improved by varying
the building line (setbacks 0–210 uu, gaps 40–300) and composing a crown-rich
mix so no two neighbours share a crown type.

**A block lighting rig exists** (`blockrig.py`), derived by inverse square from
the measured board rig rather than reused: key 5,948,117 lm, fill 5,509,606 lm
at a 14,000 uu rig. Canyon interior 13.4 → 35.8 mean, 0.000% clipped.

**The flicker is fixed** and confirmed by the owner. It was two faults: core
tops made coplanar with every roof deck by an `open_roof` change (now
`ROOF_CLEAR = 17.5`, gated by GATE-10), and four Lumen cvars a diagnostic left
at 0 (`lumen_defaults.py`).

**New knowledge worth not re-deriving is in `Docs/CATALOGUE_PIPELINE.md`** —
the recording sink, the two execution channels, the measured variation levers,
and the traps. Read it before touching the generator.

**First cold read, 2026-08-27** (Saved/ColdRead1/RECORD.md): PASS at
block/hero range - the first in project history - FAIL at player zoom with
named causes (rendering artifacts, clipping/planar geometry, and the
uniform 'paper' texture itself reading as a render-tell - cause not yet
isolated; see the record's open question). Owner called it a success; wave 1
priorities come from the reader's own findings.

### Open items

- **The declared width ladder may not be honest.** `recipes.py` declares 548
  (recipe × tier × width) combinations; 284 are baked. The first attempt to
  fill a gap was REFUSED by the gate — `vernacular5` at w1230 oversails its
  parcel by 1162 uu — so an unknown share of the other 264 are not "unbaked"
  but "unbuildable at that width". Determine which before planning any
  district placer, because the placement palette is the whole variation story.
- Street and review bench share one map, so the block rig's attenuation had to
  be tightened to avoid relighting the shelf, costing the street's far end
  light. Needs a separate map — blocked because `load_level` crashes the editor
  over remote execution, so the owner must create and open it.
- The backdrop does not cover the view down the street.
- Edge wear does not work on imported geometry (see §5).
- The single-mesh bake fidelity gap (§9.1).
- Gameplay: **nothing in-engine.** A Lane 2 agent started the headless
  economy sim on 2026-08-25 — see `Docs/WORKSTREAMS.md` Lane 2.

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

- **Every transform bug in this project has been a FRAME applied in the
  wrong place** - Rotator argument order, GATE-10 world-vs-local, the
  sweep's unapplied actor rotation, and a loop variable shadowing a yaw
  parameter (four instances by 2026-08-27). When geometry lies, check the
  frame before the geometry.
- **A build script must RELOAD the project modules it reads, or it is
  reporting on session state rather than on the repository.** The editor
  caches modules for the whole session; the quiet mode is the dangerous
  one - two consecutive rebuilds ran a superseded palette and reported
  success, and the before/after frames delivered from them showed
  behaviour the owner had already rejected (retracted and replaced).
  apply_stocks, street.py and shelf.py reload; anything that reads
  project modules and writes to the level belongs on that list. The
  warning was already written in apply_stocks' own comment by the person
  who then walked past it - written down is not the same as remembered,
  third instance.
- **A restore file a re-run can clobber is not a restore file.** Restore
  snapshots are WRITE-ONCE; the second run of apply_stocks overwrote the
  only route back to the pre-split look.
- **A clearance check that ignores ROOM walls is not a clearance check.**
  A derived whole-building standoff placed the camera OUTSIDE the studio
  room, photographing the scene through its wall. Clearance is checked
  against everything that occludes, including the room itself.
- **UV maths on WorldPosition goes AFTER the tiling scale, never before.**
  World position is LWC; at -22,000 uu a decompose/re-append costs
  precision the sampler sees (a proven-identity rotation failed its no-op
  proof by 0.28 against a 0.25 floor). Downstream of the multiply the
  values are ~132 and the maths is safe.
- **A study row needs clear ground BEHIND it for the camera and IN FRONT
  for the light.** The route-2 sweep's far camera stood 189 uu behind an
  existing row, photographing another panel's back, while that row
  shadowed the new one - producing a plausible, monotonic, garbage table.
- **This machine has persistent MetalRHI (GPU) render-thread crashes**
  (S19): MetalCommandList assertion failures killed the editor twice on
  2026-08-27, before AND after the 5.8.2 update, unrelated to scripts or
  memory. Long-running batch drivers must be RESUMABLE, stop clean against
  a dead bridge, and stamp progress so the resume set is computable.
  Set the viewport non-realtime for long batches - the fault is the render
  thread and a fastbake needs no viewport. Trigger UNIDENTIFIED: the dummy
  display is a plausible contributor, but capture activity is NOT
  correlated on the timeline to date (neither crash followed a capture;
  fastbake does no viewport work). If a third crash lands, record what ran
  in the seconds before it, so the correlation is tested, not assumed.
- **Re-baking an asset NULLS every placed actor that references it** (S17).
  The actor keeps its label, renders nothing, and reports zero bounds - a
  street silently empties and the frame reads as a lighting fault. After
  ANY re-bake, re-run the placers (street.py, place_catalogue) BEFORE any
  capture. Same species as the import-persist trap: a reference that dies
  without an error.
- **The live merge DROPS material slots — and NOT only masked ones.**
  SceneTools.merge_actors cannot carry a masked blend mode (leaf cards
  keep their triangles and lose their material, rendering as dark quads)
  — but the 2026-08-29 slot diff on vernacular_t4_w820 showed it also
  dropped MI_paint_cream, a plain BLEND_OPAQUE facade trim material
  (expected 18 slots, baked 16, both leaf AND paint_cream missing). The
  "masked" diagnosis was incomplete: a live-merged mesh may be missing
  ARBITRARY materials, so no appearance judgment may be made on one.
  Measured 2026-08-27: live 350s vs fastbake 2.6s, identical bounds.
  FASTBAKE is the production path; the live merge is for nothing on the
  judgment path at all.
- **NEVER purge `LOOK_`.** `LOOK_Post` is the unbound PostProcessVolume
  holding the fixed grade (AEM_Manual, ISO 800, shutter 60). Deleting it
  silently reverts the level to UE default AUTO exposure - the same camera
  read 87.71 before and 245.95 after, every frame blown white - and it is
  invisible to every natural hypothesis, because no geometry or light you
  change is the cause. Cost hours on 2026-08-27. Any script that wipes
  actors excludes `LOOK_` explicitly; and a wipe list is MEASURED from the
  level inventory first, never asserted from memory - the coordinator's
  remembered prefix list would have left 249 of 266 furniture actors
  standing while reporting success.
- **Every emitter needs a `_SINK` branch.** Seven ue.tool calls sat
  directly in the builders (the hand-tolerance jitter) with no record-mode
  guard: record-mode runs silently did one blocking HTTP round trip per
  floor per building - a 548-combo sweep was 1635s of ~99.9% network wait
  (1s once guarded), and with a busy editor each call sat on the 180s
  timeout, presenting as a low-CPU hang. A builder-level editor call is a
  live-only branch by construction; guard it or record it.
- **An MCP call from inside a rung script DEADLOCKS.** `rung.sh` executes
  on the editor's game thread over remote exec; `genbuild.build()` in live
  mode calls `ue.tool`, and an MCP call issued from inside that script
  waits on the very thread it is running on. Documented in
  CATALOGUE_PIPELINE §2 and still walked into on 2026-08-27 - same species
  as the LOOK_ trap: written down is not the same as remembered. Live
  builds are driven from LOCAL python (which calls MCP from outside);
  rung scripts must never import the live build path.
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
- **FIRST ACTION after ANY editor restart: clear `.mcp_sid` — next to
  WHICHEVER ue.py the script imports.** There are TWO: Tools/measure/ and a
  scratchpad copy. The cached session id makes every MCP call return HTTP
  404, which reads exactly like a dead server - mistaken for one twice.
- **rung.sh forwards NO ARGUMENTS to scripts.** An argv branch inside a
  rung script never fires - wave_throttle.py's `restore` silently
  re-applied the throttle while PRINTING that it had restored. Caught by
  reading output, not exit codes. State changes prove themselves by
  READ-BACK (cvar.py), never by printing intent.

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
