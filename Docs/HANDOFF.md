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

**MESHES CURRENT THROUGH d90957f** (staleness ledger, maintained per bake
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
- Edge wear does not work on imported geometry (see §5) — AND, found
  2026-09-02 on the wooden masses, may be INERT ON FASTBAKED CHAMFERS
  TOO: an 8.5x EdgeWearLift drive moved a 14 uu bevelled arris by
  nothing (column profile = pure drift). Suspect averaged/welded
  normals across the bevel (fastbake creates assets with
  enable_recompute_normals=False), so the curvature proxy never sees a
  low max|n| facet. Nobody has measured the flagship's own edge wear on
  a baked chamfer; FLAGSHIP LANE RETURN BRIEFING ITEM. The wood lane is
  running the normals diagnosis on its own baker first.
- The single-mesh bake fidelity gap (§9.1).
- Gameplay: **nothing in-engine.** A Lane 2 agent started the headless
  economy sim on 2026-08-25 — see `Docs/WORKSTREAMS.md` Lane 2.
- **The real UMG HUD: CORRECTED 2026-09-03.** The earlier version of this
  item said "Designer-named widgets are variables by default, no extra
  step needed" — WRONG for this bridge: designer-placed widgets become
  widget-compiler UPROPERTYs that the DSL's node creation cannot
  reference (see §5). What actually works: the owner placed ONE Canvas
  Panel root in the Designer (the only thing code cannot create), the
  DSL could reach NEITHER that panel NOR GetWidgetFromName — the bar is
  built HOSTLESS: every widget (Border, boxes, spacer, the six named
  TextBlocks) is CONSTRUCTED AT RUNTIME in BP_LensRig's BeginPlay per
  `Docs/DIRECTION_B_HUD.md`'s construction order, held in DSL-added
  object variables for binding, and added to the screen with
  GameViewportSubsystem.AddWidget; WBP_HUD is unused. Never ask the
  owner to place the six texts by hand — they would be unreachable.

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
- **A session-fresh Blueprint FUNCTION may not resolve as a callable
  node until the editor restarts** (beta lane, 2026-08-31, hit twice —
  phase A diagnostics and phase B selection): a function added via the
  DSL compiles but calls to it from other graphs fail to resolve in the
  same editor session. WORKAROUND that avoids the broken resolution
  path entirely: inline the logic into a CUSTOM EVENT and dispatch via
  SetTimerByFunctionName (stock node, string-based runtime dispatch).
  Workarounds of this shape get an EXPIRY: on the next natural editor
  restart, migrate to the proper function call so the polling timer
  doesn't fossilize as architecture. EXPIRY PAID 2026-09-01: post-restart,
  `find_node_types` resolved `SelectTick` as a normal `CallFunction` node;
  the timer and its dispatch were removed, replaced with a direct call
  wired into `EventTick`.
- **The editor's quit prompt is a save-all with a friendly face**
  (2026-09-01: a save-on-quit click during a coordinated restart wrote
  a disposable test rig — 23 actors, "built live and unsaved" by
  declaration — permanently into TestCity.umap; every lane inherited
  them, and the rig's own cleanup assertions kept passing because they
  check the LIVE level, not the map file). RULE: clear disposable rigs
  and deliberate-unsaved scene state BEFORE any editor shutdown, so the
  quit prompt has nothing to trap — and clear AT IMMINENCE, NOT AT
  INQUIRY (refined 2026-09-01 after a speculative clear emptied the
  board mid-owner-review: a scheduling question is not a shutdown, and
  the owner's view outranks pre-positioning; the clear fires in the
  same minute as the actual quit). Detection when suspected: compare
  the map file's mtime against the editor process start time — the
  wood lane's method, evidence not inference.
- **Spawning into the PIE world from Python: `unreal.World` has NO
  `spawn_actor`, and the editor spawn helpers spawn into the EDITOR
  world.** (2026-09-02, placement v0's first live click: the whole
  chain worked to `placement.place()` and died on
  `'World' object has no attribute 'spawn_actor'`, suppressed after the
  first occurrence.) CORRECTION, same day, the coordinator's own wrong
  advice retracted: the deferred pair
  `GameplayStatics.begin_deferred_actor_spawn_from_class` DOES NOT
  EXIST in this build's Python reflection either — a scan of the whole
  `unreal` module found exactly two spawn functions, both EDITOR-world
  (EditorActorSubsystem / EditorLevelLibrary .spawn_actor_from_class).
  THERE IS NO PYTHON-REFLECTED WAY TO SPAWN AN ACTOR INTO THE PIE
  WORLD in this build. A runtime spawn must happen in a Blueprint
  already ticking in the game world (reverse request channel: Python
  validates, Blueprint's SpawnActor node executes) — OR the design
  avoids runtime spawning entirely with a POOL of dormant pre-placed
  actors that Python ACTIVATES through reflected calls
  (set_actor_location, set_actor_hidden_in_game,
  set_actor_enable_collision, property writes): no spawn needed, and
  friendlier to packaging. Twin
  lesson from the same click: a refusal that is loud in the log and
  silent on screen reads to the player as "nothing happens" — every
  player-facing refusal gets on-screen text.
- **A reservation is only real in the mode that makes it real**
  (2026-09-02, empty-board mode's first click): the pinned-lot overlap
  guard — added the same day to stop placements crossing the starter
  city's footprints — kept reserving those 14 spans in EMPTY mode,
  where the pins are dormant and nothing stands there; every click on
  the bare road refused "crosses a pinned lot." Any guard derived from
  content that a mode can switch off must read that mode; a self-test
  that exercises the guard in BOTH modes is the detector.
- **The legal placement area is measured off THE THING THE PLAYER SEES,
  never derived from the math that was supposed to produce it**
  (2026-09-02): placement's plate was first one BLOCK_LEN (±2460), then
  citylayout's four-block union (±6050); the board MESH the owner
  clicks on measures ±7650 (get_actor_bounds on the board actor) —
  1,600 uu a side of visible, standable plate the procedural layout
  never knew about, and every refusal there read as "can't build on the
  board." The self-test that asserted plate == layout union was itself
  the bug; the honest check is containment (layout fits inside the
  measured plate).
- **A pooled actor derives its look ONCE at BeginPlay from empty
  identity; activation must trigger a re-derive, or the derived state
  stays wrong while every property reads right** (2026-09-02, placement
  v0's second live click): seven lots activated exactly where the owner
  clicked — location, mobility, mesh, material, visibility all correct on
  a live read — and none were visible, because the placeholder pad's
  scale was computed at PIE start from WidthUU = 0 and the Tick
  change-detection watched only Owned/Tier. Read the DERIVED values
  (scale), not just the inputs, when an actor "should be visible"; and
  every field that activation writes must be in the change-detection
  set, or deactivation must reset it.
- **The Blueprint DSL cannot place a getter for a DESIGNER-placed widget
  ("Is Variable" on a widget-tree widget), only for variables it added
  itself — and it cannot place UserWidget.GetWidgetFromName either**
  (2026-09-03, HUD build): the widget compiler turns the designer's
  Canvas Panel into a UPROPERTY on the generated class — reflection
  reads it on the CDO — but the DSL's node creation walks the
  Blueprint's own variable-description list, so
  `Variables|Default|GetCanvasPanel_43` "does not exist" no matter how
  many compiles run (API-level or the Designer's own button), and
  GetWidgetFromName missed under three namespaces. THE ROUTE THAT WORKS
  NEEDS NO WIDGET BLUEPRINT AT ALL: `GameViewportSubsystem.AddWidget
  (UWidget, GameViewportWidgetSlot)` takes any constructed widget, so the
  whole HUD is Construct-Object-from-Class in BP_LensRig's BeginPlay
  (Border → row HorizontalBox → clusters → TextBlocks), styled with
  SetFont/SetFontSize/SetColorAndOpacity, held in DSL-added object
  variables for binding, added straight to the viewport. WBP_HUD is
  unused. DSL gotchas met on the way: Panel|SetContent takes self
  first (unlike the Class|X|Set family); MakeSlateFontInfo needs a real
  MakeFontOutlineSettings struct ("None" is only for object refs);
  Math|Vector2D|MakeVector2D; colours must be converted sRGB→linear
  through the curve, not byte/255. Designer-placed widgets stay
  unreachable to code; never rely on them for binding.
- **Never OpenEditorForAsset on the level PIE is playing — it raises a
  MODAL on the main thread and the whole bridge blocks** (2026-09-03:
  every MCP call from every session timed out at 300 s; the editor
  process stayed alive at ~45% CPU with the port listening, and only
  the owner dismissing the dialog freed it). The tell: calls time out
  while `ps` shows the editor busy and `lsof` shows 8000 LISTENING —
  that is a blocked main thread, not a dead process, and the fix is a
  human at the dialog. To see the player's view during PIE, verify by
  state (object variables, viewport widgets, log) and leave pixels to
  the owner; do not bring the level tab forward.
- **LANES NEVER TEST ON THE OWNER'S LIVE SAVE.** 2026-09-03: the six-tower
  city the owner built in their first from-scratch session was wiped by
  a CITYSTATE RESET at 02:00:59. First attributed to a lane's PIE test;
  CORRECTED the same hour: the lane has no input injection and logged
  zero resets across its own sessions, and the 02:00:03 session carried
  a placed lot AND a B-key buy — human input — so the reset was almost
  certainly the owner's own N press, which they had been taught as a
  casual "fold placed lots back" key while it actually wipes money and
  ownership. Two lessons, both real: the economy's state file
  (citystate.json) is ONE shared file, so any lane's N press, reset
  channel or test seed WOULD land on the owner's city; and a reset that
  destroys a session must not sit on a bare key with no confirmation. Rule: the driver takes a STATE-PATH OVERRIDE and every lane
  session runs against citystate_test.json (logged at registration:
  "CITY DRIVER: state file = ..."); the owner's citystate.json is
  touched by nobody but the owner. Corollary for HUD reads: a bar whose
  text is built from live values at construction shows "$100.0" after a
  reset without any tick binding — construction-time truth is not
  proof the binding runs.
- **One unguarded property read kills the WHOLE economy driver, silently**
  (2026-09-02): a pre-staged placement channel read PlaceRequestX/Y at
  the top of the driver's tick body before the properties existed on
  the GameInstance; the read threw every tick, the outer try/except
  swallowed it once-per-class, and the economy tick, Price/Accum and the
  CPD push all went dead behind it with one suppressed log line to
  show. Rule: every request-and-clear channel read in the driver gets
  its OWN local try/except defaulting to no-request; the tell is the
  EconHUD freezing — if money stops ticking, suspect the driver body
  before the economy.
- **`pgrep -f <pattern>` can match the WATCHER that runs it: a wait
  loop whose own command line contains the pattern waits for itself,
  forever, and answers "RUNNING" for a job that never started**
  (2026-09-01, direction-B lane: `while pgrep -f wood_set.py; do
  sleep; done; ... mk_woodbake &` — the bake was reported in-progress
  across several exchanges and had never launched; assets on disk were
  the old set). Wait on a CAPTURED PID with `kill -0`, never on a
  pattern that can see the waiter. Fifth member of the reports-success-
  while-doing-nothing family (with: one material instance reused
  across species, a leftover rig measured as the subject, a binding
  loop matching zero components, the zsh no-match glob below).
- **A foreground command that TIMES OUT reports a completed step it did
  not complete: the tool returns, the caller reads a return, and the
  work stopped partway** (2026-09-02, direction-B lane: a board clear
  timed out at 476 -> 126 actors and would have been reported "board
  cleared" — the number was only visible because the clear happened to
  print progress). A destructive bulk operation must be written as a
  LOOP UNTIL THE QUERY IS EMPTY, not as one long call whose completion
  is assumed from its return: `while search() non-empty: delete batch`,
  then assert the search is empty as a separate statement. Sixth member
  of the reports-success-while-doing-nothing family. Worse than the
  others because a HALF-cleared board looks exactly like a cleared one
  from anywhere except the count — the tell is a number, never a look.
- **Under zsh, a no-match glob kills the rest of an `&&` chain silently
  enough to look like success** (2026-09-01, direction-B lane: `rm
  *.bmp` with no matches aborted the chain before a heredoc wrote a
  README — the lane reported the README as written and it was not; the
  error scrolled past). Same family as the rename-on-&&-chain trap:
  a multi-step shell chain is only as done as its LAST step, verified
  by reading the result back, never by exit-looking output.
- **A palette hit is a NAME, not an identity: check the CATEGORY before
  believing it** (2026-09-01, coordinator's error, owner's second look
  caught it): the Blueprint action search showed "City Tick" placeable
  and it was taken as proof the Python bridge's city_tick had
  registered — it was the phase-A TOY CityTick function on BP_Parcel,
  a name collision with legacy code. With Context Sensitive off, none
  of the bridge's four functions existed anywhere, and the automation
  instrument (find_node_types) had been RIGHT all along. Same family
  as the substring traps below, at the UI level. Corollary, now solid:
  Python-defined @unreal.ufunction BFL functions do not reach the
  Blueprint action database in this setup, and Execute Python Script
  is editor-utility-only — a runtime BP cannot call Python through a
  graph node at all.
- **A substring test standing in for a NUMERIC one inverts answers**
  (two instances, 2026-08-31, different lanes, same family): `'_c' in
  name` matched "_contemporary" and silently discarded 8 recipe
  families from a census; `'0.77' in readback` reported a Custom
  Primitive Data write as LOST because the float came back as
  0.76999998092651367. Both were caught only by re-running with a real
  parse/compare. When the question is numeric or structural, parse and
  compare — never grep the repr.
- **Python bytecode lives OUTSIDE the repo on this machine** (found
  2026-08-31, cost an hour): `sys.pycache_prefix` is
  `~/Library/Caches/com.apple.python`, so `rm -rf __pycache__` clears
  NOTHING — and invalidation is mtime+SIZE, so a same-length edit landing
  in the same second serves STALE BYTECODE against the restored file.
  The tell: `import` and `exec(open(path).read())` disagree about the
  same file. Size-preserving constant edits in a tight edit-rerun loop
  (100 -> 200, 5 -> 9, 1.0 -> 2.0) are the exact trigger. Fix: clear
  `~/Library/Caches/com.apple.python/<abs repo path>`. If a Python value
  contradicts the source in front of you, it is this, not the source.
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
- **`_guard.py` cannot survive PIE.** It calls
  `UnrealEditorSubsystem.get_editor_world().get_path_name()` for its
  level check, and `get_editor_world()` returns `None` while PIE is
  running — the guard itself crashes before a script's own code runs.
  `rung.sh` is therefore unusable for any PIE-time Python; call
  `Tools/measure/uepy.py <script>` directly instead (skips the
  guard-prepend step). Found running a live economy-driver probe during
  PIE, 2026-09-01. Separately: `EditorActorSubsystem.
  get_all_level_actors()` also returns EMPTY via bare Python during PIE
  — only the MCP bridge toolset's own actor/scene queries correctly
  resolve to the PIE world; that PIE-context resolution is NOT a general
  property of Python running in the editor process, it's specific to
  that bridge. The method that DOES work from bare Python:
  `UnrealEditorSubsystem.get_game_world()` (a separate method from
  `get_editor_world()`) + `GameplayStatics.get_game_instance(that
  world)`.
- **A Python-defined `@unreal.uclass()` — `BlueprintFunctionLibrary` or
  plain `Object` — does not reach Blueprint's action database in this
  project's setup**, even though it is genuinely registered
  (`ObjectTools.search_subclasses` finds it) and genuinely callable from
  Python with correct results. Confirmed the hard way, 2026-09-01: two
  restructure attempts across two editor restarts to fix a "the node
  doesn't show up in search" problem, before the owner's OWN palette
  check (not a tooling search) confirmed no such node exists anywhere,
  under any name. The earlier "it's placeable, I saw it in the palette"
  report was a NAME COLLISION with an unrelated legacy event sitting in
  the same category — verify a palette hit by its CATEGORY, not just its
  name, before trusting it; this is the same species of false-positive
  as a name-keyed lookup over anything a generator emits more than once
  (see instrument hygiene). The stock "Execute Python Script" node is
  ALSO no fallback here — it is editor-utility-blueprint-only, absent
  from Actor/Pawn graphs. The working alternative for Python-driven
  gameplay logic in this project: a `unreal.
  register_slate_post_tick_callback` registered from `init_unreal.py`,
  reading/writing state directly via `get_game_world()` — no Blueprint
  node ever created, no palette involved.
- **A bare `(bind x (CastToFoo ...))` in the Blueprint DSL silently eats a
  failed cast.** It's a real DynamicCast node (Then/CastFailed exec
  branches); the bare bind form only wires Then, so on failure nothing
  downstream runs and nothing logs — no error, no "Accessed None," just
  silence (beta lane, phase B, 2026-08-31). Wire `:CastFailed` with a loud
  print wherever a failed cast would otherwise be invisible.
- **A baked catalogue actor's placed LOCATION is its bounds MIN CORNER,
  not its center.** Confirmed twice independently by two different lanes —
  camera P0's aiming (2026-08-29, cost three probe rounds, undocumented
  until now) and beta lane's selection work (2026-08-31) — before either
  lane knew the other had already paid for it. Any aiming/bounds math
  against a placed catalogue actor must compute the true center via
  `get_actor_bounds`, never assume actor location = center.
- **Editing a Blueprint instance variable (e.g. `BoardCentre`) while PIE
  is running only touches the transient PIE-world copy of that actor** —
  it is lost on `StopPIE` and never reaches the editor-world actor. Set it
  on the editor-world actor path before `StartPIE` if it needs to survive
  the session; mid-PIE edits are fine for same-session testing but must be
  re-applied to the editor-world copy to persist.
- **`BP_LensRig`'s `BoardCentre` moves the boom's ORBIT ORIGIN, not its
  aim.** `EventTick` sets `Location = BoardCentre + polar(Reach, Azimuth,
  Height)` but `Rotation` from `Tilt`/`Azimuth`/`Pan` alone — those are
  driven only by WASD/ladder-stop input and never recomputed toward
  `BoardCentre`. A trace along the camera's forward vector (the correct,
  intentional design for focus-as-selection — see `Docs/CAMERA_DESIGN.md`
  "Focus is attention") therefore does NOT track `BoardCentre`; moving
  `BoardCentre` relocates the rig without turning it to face anything. A
  six-block selection-trace investigation (beta lane, 2026-08-31 into
  2026-09-01) mistook this for an asset/vintage/collision defect before
  the actual DSL was read — see the measurement-chain entry above.
- **`CaptureViewport` and `GetVisibleActors` reflect the EDITOR world, not
  the live PIE world, even during in-viewport PIE.** Same underlying split
  as the `BoardCentre`-mid-PIE entry above (PIE runs a transient duplicate
  world alongside the editor's own), landing on a different tool this
  time. `GetVisibleActors` returns actor paths without the `UEDPIE_0_`
  prefix — the tell. Confirmed 2026-09-01: pushed correct, verified
  Owned/Tier state onto live PIE `BP_Parcel` actors (proven via
  `GameplayStatics.get_all_actors_of_class` + `get_editor_property`,
  which DO read the PIE world), then called `CaptureViewport` at those
  exact world coordinates and saw nothing — because the editor-world
  copies of those same actors never ran `EventBeginPlay` (PIE-only) and
  so never resolved a mesh at all. Confirmed by checking the editor-world
  copies directly after `StopPIE`: `mesh=None` on both, matching what the
  capture showed. There is currently no known route to a PIE-accurate
  screenshot through this bridge; a visual acceptance pass needs either a
  different capture path or a human actually watching PIE.
- **`/Engine/BasicShapes/Cube`'s own default material slot is
  `WorldGridMaterial`, not an opaque surface.** Spawning it via Python
  (`SetStaticMesh` to the bare asset) and never overriding the material
  reproduces this exactly — the editor's own "drag a basic shape into the
  level" UI applies `/Engine/BasicShapes/BasicShapeMaterial` as a
  convenience on top, which nothing in a Python-driven spawn path does
  automatically. Confirmed 2026-09-01 building the empty-lot placeholder
  (`PARCELIZATION_CONTRACT.md`'s amendment A4): every property read back
  correct — mesh assigned, component visible, transform and world bounds
  exactly matching the intended footprint — and the placeholder was still
  functionally invisible until `Rendering|Material|SetMaterial` explicitly
  set slot 0 to `BasicShapeMaterial`. A property-correct actor is not the
  same claim as a rendering-correct one; this is the second time that gap
  has cost real time this session (see the `CaptureViewport` entry above).
- **A `PrintString` node's `Duration` pin left at `0.0` prints to the
  Output Log correctly and is simultaneously invisible on-screen** — the
  nastiest kind of debug residue, because every log-based check says PASS
  while the human sees nothing. Confirmed 2026-09-01: the owner reported
  "selection doesn't work" after the click/highlight redesign's
  predecessor mechanism (focus-as-selection); `SelectTick`'s trace, cast,
  and text-generation were all already correct and had already succeeded
  multiple times in the owner's own session — provable by reading the
  Output Log directly (`GetLogEntries`) rather than trusting the struct
  fields (see the measurement-chain entry above for why `HitResult`
  introspection is a dead end). The actual defect was three
  `Development|PrintString` nodes in `SelectTick`
  (`K2Node_CallFunction_182/183/184`) with `Duration="0.0"`, a leftover
  debug value never meant for player-facing display. Fixed with
  `set_pin_value` targeting each node's `Duration` pin directly, not
  `write_graph_dsl` — `SelectTick` contains a `Math|Vector|vector*vector`
  expression that reads back fine but cannot be recreated via
  `create_node`/`write_graph_dsl` (`"AssertionError: The node could not
  be created"`), so any DSL rewrite of this event fails even when the
  edit is unrelated to that node. `set_pin_value` edits an existing pin
  on an existing node without touching graph structure and has no such
  restriction — treat it as the default tool for a small edit inside any
  event that already contains a non-recreatable node type, rather than
  reaching for `write_graph_dsl` and discovering the limitation live.
  General lesson: when an instrument (a log line, a passing test) and
  the human's lived experience disagree, suspect the display/visibility
  layer before suspecting the mechanism underneath it — the mechanism
  had been correct the whole time.
- **There is no path found to build a UMG widget tree (CanvasPanel +
  child widgets) programmatically in this project.** Confirmed
  2026-09-01 attempting a real HUD to replace `PrintString`.
  `WidgetBlueprintFactory` + `AssetToolsHelpers` DO create a valid
  `WidgetBlueprint` asset cleanly — that part works. But its
  `WidgetTree` is BlueprintProtected: `get_editor_property('WidgetTree')`
  fails on both the Blueprint asset and its generated class's CDO
  (`"Property 'WidgetTree'... is protected and cannot be read"`),
  `dir()` on both surfaces zero widget/tree-related methods, and
  `unreal.WidgetBlueprintLibrary` does not exist in this build — three
  separate access paths tried and logged, not one naming guess. The
  MCP bridge has no UMG-equivalent toolset either (`list_toolsets`
  confirmed). This isn't just a missing accessor: UMG widget trees are
  a DESIGN-TIME construct compiled from the Widget Designer, and
  standard Blueprint graph nodes don't build one from nothing at
  runtime either (`Create Widget` instantiates an ALREADY-DESIGNED
  class, it doesn't construct one). A HUD's actual layout needs a
  human in the Designer, or C++ (a hard stop per `AGENTS.md`).
  Fallback in place until then: `PrintString` calls with a real
  `Duration` and a stable per-message `Key` (`"ParcelHUD"`,
  `"EconHUD"`) so messages replace themselves instead of stacking —
  functional, not the asked-for widget.
- **`StaticMesh` and `OverrideMaterials` cannot be set in one combined
  `ObjectTools.set_properties` write — the mesh change resets the
  material-slot array, silently dropping whatever `OverrideMaterials`
  value was in the same call.** Caught live 2026-09-02 building
  `study_dress.py` (a study-only editor-world dressing script, never
  saved): the first lot's read-back showed `StaticMesh` landed correctly
  but `OverrideMaterials` came back empty, from a single call that set
  both. Fix: two sequential `set_properties` calls, mesh first, then
  material — matches how `BP_Parcel.ResolveMesh` already does this in
  Blueprint (`SetStaticMesh`, then a separate `SetMaterial` node), which
  is presumably why that path never hit this: it was never combined into
  one write to begin with. Any future Python-side mesh+material
  assignment should default to the two-call form rather than discover
  this again.
- **A `write_graph_dsl` call can return success, compile clean, and still
  not reach the live graph — with no orphaned node left behind to explain
  it** (beta lane, 2026-09-03, fixing EventTick's Money/Demand text so it
  updates every frame instead of only on the Reset key). Five submissions
  targeting only `(event EventTick ...)` — not the full multi-event script
  `read_graph_dsl` returns for that graph. The first four failed on real
  pin-connection errors (the four traps below); the fifth returned
  `{"returnValue":null}` with a clean `LogBlueprint: Compiling` and no
  error after it in the log — and `read_graph_dsl`, called twice to rule
  out staleness, still rendered the OLD EventTick verbatim, unchanged.
  Ruled out a duplicate/orphaned override before concluding this:
  `find_nodes(title="Tick", entry_points_only=true)` found exactly the
  same two entry nodes (`ReceiveTick`, `SelectTick`) as before any edit,
  and a raw `get_connected_subgraph` dump from the real Tick entry node
  contained none of the new bind names anywhere. Cause UNRESOLVED.
  Stopped rather than keep guessing against a Blueprint that was
  otherwise stable and working — the untouched original logic (camera,
  LMB/B/N, placement) still runs correctly; nothing broke, the fix simply
  never took. NEXT ATTEMPT should not retry this call shape: build the
  new logic as its own FUNCTION GRAPH and splice one CallFunction into
  EventTick's exec chain — the shape that persisted reliably for
  `SelectTick` (see the function-graph-resolution entry above) — rather
  than resubmitting a whole existing event body.
- **The DSL's read-back `type_id` label is not always the write-time
  node** — four distinct ways this bit in the same session (2026-09-03),
  on code that was either untouched or a straight copy of something
  currently live and compiling, not new code being drafted:
    - `Class|Factory|SetText`, read back verbatim from a WORKING,
      already-compiled TextBlock `SetText` call, resolves on write to an
      unrelated Factory class's boolean `bText` property setter
      (`get_node_type_pins` confirmed: self = `Factory Object Reference`,
      value pin = `bText` Boolean) — `"Could not connect pin ReturnValue
      to bText"`. Correct node, verified by pins: `Class|Text|SetText`
      (`Text` in, `self` = `Text Object Reference`).
    - `Rendering|SetVisibility`, used on a UMG widget, is actually a
      boolean actor/component visibility setter (`bNewVisibility`) —
      `"Could not connect pin SelectionCluster to bNewVisibility"`.
      Correct node: `Class|Widget|SetVisibility` (`ESlateVisibility Enum`
      value, `self` = `Widget Object Reference`).
    - The inline-multi-output-node-as-argument trap (a call like
      `(Utilities|Casting|CastToBP_Parcel (Collision|BreakHitResult
      _hitresult))` silently connects to the callee's FIRST output —
      `bBlockingHit`, a Boolean — regardless of the target pin's actual
      type) fired on a VERBATIM, untouched, currently-compiling line
      copied straight from `read_graph_dsl`'s own output —
      `"Could not connect pin bBlockingHit to Object"`. This was assumed
      to only be a risk for newly-authored code; it is not — it applies
      to ANY inline multi-output call resubmitted through this tool,
      regardless of provenance. Fix: never pass a multi-output node call
      inline as an argument; `bind` it with a full positional
      destructuring list (`_` for every unwanted output, confirmed
      against `get_node_type_pins`) and pass the named variable instead.
    - A plain-looking `(bind _location (Collision|BreakHitResult
      _hitresult))` — also copied verbatim from a working read-back, also
      currently live — turned out to secretly need output index 4
      (`Location`), not output 0 (`bBlockingHit`): `.x _location` failed
      with `"Could not connect pin bBlockingHit to InVec"`. The read-back
      renderer had silently collapsed what must originally have been a
      destructuring bind down to a plain-looking one, discarding which
      output it actually pointed at — a plain `(bind name (Node ...))` in
      a read-back is not proof the underlying node is single-output.
      Fixed by folding it into ONE shared destructuring bind alongside the
      HitActor extraction: `(bind (_ _ _ _ _location _ _ _ _ _hitactor _ _
      _ _ _ _ _ _) (Collision|BreakHitResult _hitresult))`, positions
      taken from `get_node_type_pins`, never guessed from memory.

  General rule going forward: before resubmitting ANY `read_graph_dsl`
  output through `write_graph_dsl` — changed lines or not — treat every
  multi-output node call as suspect. Verify it is either fully
  destructured or dot-accessed, and verify any `Type|Id` string against
  `get_node_type_pins` unless its self-type and pin order are already
  known-good from a call made THIS session — never from memory, and never
  from a prior session's transcript.
- **A `write_graph_dsl` call can report success on a graph the running
  process never actually executes** (beta lane, 2026-09-03, same window
  as the entry above — a DIFFERENT mechanism from it, easy to conflate
  since both look like "the write didn't take"). `init_unreal.py`'s
  economy driver is a Slate post-tick callback registered ONCE per
  editor process (`register_slate_post_tick_callback`, guarded against
  double-registration by an attribute on the `unreal` module). Editing
  the FILE on disk does nothing to the ALREADY-RUNNING callback — Python
  captured a reference to the old function object at registration time,
  and the registration guard blocks a plain re-import from replacing it.
  The tell: grep the log for the callback's own "registered" line
  (`CITY DRIVER: registered` here) and compare its timestamp against the
  edit's — if the edit is newer, the running process is still executing
  the OLD code, no matter how many times it's been resubmitted. Confirmed
  by adding a new log line to the edited function and never seeing it
  fire across three full PIE sessions post-edit. Fix needs one of: an
  editor restart (this project restarts often enough that it usually
  arrives on its own, but don't assume it has), or a session with an
  in-process Python channel (`Tools/rung.sh`, not this bridge)
  unregistering the stale callback, clearing the guard attribute, and
  re-importing. A DSL graph write (the entry above) and a `.py` file edit
  fail to "take" for completely unrelated reasons — a graph write is
  live the moment it compiles; a Python file is only ever a proposal
  until something re-imports it.
- **The economy driver's save file is shared by every lane in this
  editor, and the safe default is the OWNER'S real file, not a test
  one** (beta lane, 2026-09-03: a stray owner N-press wiped six built
  towers back to a fresh seed — see `citytick.city_reset`'s own "LOUD by
  design" comment — and the post-mortem found every lane's PIE had been
  writing `citystate.json` by default all along). The economy driver
  (`_state_path_source` in `init_unreal.py`) picks the save path in this
  order: `unreal._stacktown_state_override` (a path, set by a session
  with a Python channel, before `StartPIE`) > `Content/Python/
  lane_pie.marker` existing (a file-tools-only lane's route — empty
  content means `citystate_test.json`, non-empty content is read as the
  path) > neither set, which is `citytick.STATE_PATH` — the owner's real
  file — UNCONDITIONALLY. That ordering is the fix: the FIRST design put
  the test path behind a GameInstance bool defaulting off, which put the
  OWNER on the test path too, since a hand-started PIE never sets a bool
  either — inverted from what was needed. A lane must opt OUT every
  time, deliberately, or it is on the real file. The driver clears both
  routes the instant it sees PIE end (a `pie_was_running` transition in
  the tick state, not a fixed per-tick check), so neither can leak into
  the owner's next hand-started session. Every PIE start logs `CITY
  DRIVER: session state file -> <path> (override|marker|default)` — the
  audit trail for the two failure modes this can't fully engineer away:
  (1) a marker left behind by a lane session that crashed mid-test,
  closed by the driver's own PIE-end cleanup, not by the lane remembering
  to; (2) a lane that simply forgets to write the marker before
  `StartPIE` — still possible, still real exposure, but now visible after
  the fact as a `default` line in the log against that lane's own
  session instead of invisible. See `Docs/BETA_LANE.md` contract 9 for
  the protocol.

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
- **FASTBAKE SHIPS NO SIMPLE COLLISION — on any asset.** (CORRECTED
  2026-09-01 by the coordinator, replacing its own same-day claim that
  plain assets ship one hull.) The disproof: untouched
  `SM_Bld_vernacular8_t0_w820` has a genuinely empty `AggGeom`, same as
  the corner variants. The hull found on `SM_Bld_vernacular_t0_w1230`
  was the beta lane's DIAGNOSTIC `generate_convex_collisions` output,
  accidentally swept to disk by a save-all during the selection
  investigation — REVERTED to committed bytes on the owner's word,
  2026-09-01. The editor's in-memory copy still carries the hull until
  the next restart, so the file must be re-checked clean after any
  subsequent save-all (the coordinator holds this check).
  The trap inside the trap: "verified unsaved via git status" is only
  good until the NEXT save-all — an in-memory asset edit stays live all
  session and any later broad save sweeps it to disk silently. And the
  rule that follows (wood lane's phrasing, adopted): A SAVE-ALL IS A
  MUTATION WITH AN UNBOUNDED SUBJECT LIST — every other mutating call
  in this project names what it touches; `save_assets` with an empty
  list saves whatever ANYONE dirtied. Save explicit paths, always.
  Production is unaffected as long as selection runs `complex=true` (it
  does — SW3, NW1 and the parcel are the proof complex traces answer);
  anything that later wants `complex=false` traces must add simple
  collision to the WHOLE catalogue first, not just corners.

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
- **Verify the measurement chain, not the setup.** Six blocks of a
  selection-trace investigation confirmed that `BoardCentre` correctly moved
  the boom's position, and treated that as proof the trace was aimed at the
  target. It wasn't: `SelectTick`'s trace fired along the camera's
  independently input-driven forward vector the whole time — `BoardCentre`
  only ever moved the orbit origin, never the rotation. Every "miss" across
  six blocks was chased as an asset/vintage/collision defect; none of it
  was, because the ray's actual path against the target was never checked
  until block seven. When a test depends on A causing B, print B, not A —
  confirming A happened is not evidence B did.

### Process

- **Review the whole frame, not the thing you just changed.** A pass is finished
  when the frame has been walked, not when the last edit renders.
- **Vary one thing, and make sure it is the thing that differs.** The skeletal
  crash cause was announced after changing the setter while holding the actor
  count at one — the count was the variable that mattered.
- **Report a cause as a hypothesis until it is isolated.**

---

- **`EditorAssetLibrary` has NO reload in this build. The entry point is
  `EditorLoadingAndSavingUtils.reload_packages`, which takes PACKAGES —
  not asset paths — plus a `ReloadPackagesInteractionMode` whose values
  are `ASSUME_POSITIVE` / `ASSUME_NEGATIVE` / `INTERACTIVE`.** Get the
  package with `asset.get_outermost()`. `ASSUME_POSITIVE` is the
  non-interactive one; an interactive mode sits waiting on a dialog
  nobody is watching. (2026-09-02, direction-B lane, clearing a dirty
  flag on the shared master without writing it.)

  **Why a reload at all:** a fully and correctly reverted edit still
  leaves the asset DIRTY. The content is back; the asset is not clean.
  While that flag is set, any save-all re-serialises the package and
  lands a changed LFS oid in the repo — a flagship asset modified by
  another lane, arriving as a side effect of somebody else's tidy-up.
  Reloading from disk discards the in-memory copy and the flag with it,
  and writes nothing. **"The content is back" and "the asset is clean"
  are different facts**, and the first was verified and reported as
  though it settled the second.

  **The guard is the lesson, not the API.** The first script guessed
  `EditorAssetLibrary.reload_asset`, then `reload_assets`, then
  `ReloadPackagesInteractionMode.LOAD_ALL_CHANGED` — three wrong names in
  a row. Each time it REFUSED with an explicit "do NOT work around this
  by saving the asset", because saving was the one outcome the whole
  exercise existed to prevent and is exactly what a tired operator
  reaches for when a reload call keeps failing. A refusal branch that
  names the tempting wrong move is worth more than the guess it replaces.

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
5. **`PaperDetail` texture** — RESOLVED 2026-08-31 (direction-B lane,
   traced from `wire_paper.py:74-93` — the code that wired it, not a
   graph guess): PaperDetail is the ROUGHNESS DETAIL channel — a
   grayscale sample on the same tiled UVs as the paper normal, feeding
   the Alpha of the RoughMin/RoughMax Lerp. It replaced the older
   world-scale Noise alpha. `PaperMottle` (checked in the same pass) is
   bound to the three coarse normal samplers — the parked two-octave
   system — and is not a colour channel either.

- **BLUEPRINT GRAPHS ARE NOT READABLE FROM PYTHON (2026-09-03).**
  `Blueprint.UbergraphPages` and `EdGraph.Nodes` are protected to
  Python's get_editor_property (same wall as WidgetTree), and
  `BlueprintEditorLibrary.find_event_graph` hands back a graph whose
  node list is equally closed. There is NO in-process authority on
  what a graph contains: the MCP's read_graph_dsl (an EXEC-reachability
  walk from the event node) is the best structural reader available,
  get_connected_subgraph follows data links too and sweeps every
  orphan, and find_nodes matches spaced display titles ("Cast To
  BP_Parcel"), so its empty result proves nothing. Repeated
  write_graph_dsl submissions to the SAME event leave every superseded
  chain in the page as orphans (12 hit traces, 22 SetHighlighted after
  one evening) — the third HUD write compiled clean with the click
  chain's body dropped, and the owner found it. Rules: a graph that has
  been written more than twice is a junkyard — move the body to a
  FRESH function graph and leave the event as one call; after EVERY
  write, read_graph_dsl back before compile; and the only proof that a
  chain runs is behaviour (a click producing its CITY PLACE line).

- **INPUT MOVED TO PYTHON; BP_LensRig FROZEN (2026-09-03, 04:00-04:40).**
  Three "press Play" calls in one night were issued on compile-clean
  graphs that did nothing, with the owner as the only test instrument
  ("this is starting to feel like a death spiral and potentially a
  project management issue"). What settled it was INSTRUMENTATION, not
  another rewrite: an in-process probe (slate post-tick, no asset
  touched) logged that every mouse-down reached the PlayerController,
  and that calling the rig's TickBody directly via reflection in the
  same frame as a real press still wrote no PlaceRequest - the break was
  inside the DSL-written function, and no reader could show where.
  Decision: player input lives in Content/Python/clickdriver.py (own
  slate callback, imported by init_unreal.py, guarded): cursor trace,
  parcel select + SetHighlighted via call_method, PlaceRequestX/Y for
  empty plate, B -> BuyRequestPID (the label), hold-N 2 s -> reset with
  a release latch and an on-screen countdown. Proven HEADLESS in a
  coordinator PIE on the test file: click_at -> "CITY PLACE: P1
  activated", click on P1 -> selected + highlighted, B -> "CITY BUY: P1
  bought". Facts the port will need: HitResult reaches Python only via
  to_dict() ('hit_actor', 'location'); get_hit_result_under_cursor_by_
  channel returns None on a miss; GameplayStatics.break_hit_result is
  not exposed; BP_LensRig.SelectedParcel is NOT instance-editable, so the
  reflected write is refused and the selection is held in Python (the
  HUD's selection cluster stays collapsed until that variable is made
  instance-editable - a variable-flag edit, not a graph write); rung.sh's
  guard cannot run during PIE (editor world is None) - use uepy.py with
  the script's own project assert. PROCESS RULES that came out of it:
  the owner never tests a guess - every human run answers one question
  with a log line; a proven graph is frozen and features go in new
  graphs, new actors or the driver; a working click gets committed the
  minute it is proven.

- **GHOST PAD + REACH (2026-09-03, owner's word "go ahead with the
  ghost pad").** placement.resolve_click gained two refusals (in the
  road / too far from a road, PLACEMENT_GRID.md §2.1) and clickdriver.py
  draws the would-be footprint on hover with the same resolver. Proven
  headless in a marker-isolated coordinator PIE: six preview points
  (road, overlap, legal, too far, off-board, studio floor) resolved as
  specified; the draw call runs. Self-tests: placement 13/13 after
  moving the test clicks from y=100 (now "in the road") onto the block.
  Facts: KismetSystemLibrary draw_debug_box/draw_debug_string work from
  a slate post-tick callback in PIE; an activated pad's front edge is on
  the facade line (measured), the bought mass sits 750 uu behind it -
  the setback convention is an open design question, not a bug.

- **PAD/MASS OFFSET FIX, MEASURED (2026-09-03 13:41).** The design
  lane's ruling (genbuild's mass pivot is the FRONT-LEFT corner at
  ground; "setback2" in a mass name is a HEIGHT BAND, not a street
  setback) plus the coordinator's finding that the pad and the mass are
  the SAME component ("Building": a centre-pivot Cube before purchase,
  the mass after) explained two live misalignments: the bought mass sat
  750 uu behind the facade (a doubled offset) and the pad cube sat half
  a lot off the lot span in X. Fix in init_unreal._apply_lot_offset:
  keep the actor at (x0|x1, +/-1880, yaw 0|180) and set the component's
  RELATIVE location by the mesh actually on it - Cube: (W/2, 0, 0);
  mass: (0, -750, 0) - applied at activation, reactivation and every
  sync for placement-created lots. Measured in an isolated PIE: fresh
  pad P3 bounds x [-3280, -2460] == lot span, y [1130, 2630] front on the
  facade; bought P2 (north) x [2437, 3269] vs lot [2460, 3280], front y
  1117 (plinth oversail); bought P1 (south) front y -1129. Both sides,
  both states. Scar re-earned on the way: get_relative_location is not
  a Python method (the property is relative_location) and the first cut
  killed every driver tick until the helper was wrapped - the "one
  unguarded call" rule applies to helpers called FROM the sync too.

- **WIDTH CYCLE SHIPPED AND MEASURED (2026-09-03 13:5x).** Scroll wheel
  (MouseScrollUp/Down, discrete FKeys) cycles woodmap.WIDTHS on the ghost;
  the width rides a PYTHON-SIDE channel (unreal._stacktown_place_width,
  consume-and-clear in the placement consumer) - both drivers are
  in-process, so no GameInstance variable and no Blueprint edit. Q/E NOT
  bound (the rig's zoom-ladder keys; would double-fire). Proven headless
  in an isolated PIE: preview boxes at 1230 and 2050; placed P4 (north,
  [0, 1230]) and P5 (south, [-2050, 0]) with pads covering their spans
  exactly and citystate widths matching. DEFECT MADE VISIBLE BY THE
  TEST: both clicks hit the CROSS STREET (TC_Road_Cross / TC_Walk_C4 at
  x=0) and v0 placed lots straddling it - resolve_click knows one road.
  The beta lane's resolve_road (19/19) is the fix; integration into
  resolve_click (both roads, crossing refusal) is the next headless
  window, and the ghost inherits it for free.

- **CROSS STREET LIVE AND MEASURED (2026-09-03 14:04).** The beta lane
  integrated resolve_road into resolve_click (24/24; lots carry
  placement.road_id, x0/x1 are the span along the winning road's axis);
  the driver gained _lot_transform (arterial unchanged; cross street
  west = (-1880, y0, yaw 90), east = (+1880, y1, yaw -90) so local +x
  runs along the road and local +y points away from it, which is what
  _apply_lot_offset and genbuild's pivot both assume) and the ghost box
  is road-aware. Measured in an isolated PIE: west pad P6 x [-2630,
  -1130] (front on the facade), y == lot span; after purchase its mass
  front at x=-1129; east pad P7 x [1130, 2630], y == lot span, yaw -90.
  The crossing refuses with its own player text. TEST ARTIFACT worth
  knowing: two _stacktown_click_at calls in ONE remote-exec script write
  PlaceRequestX/Y twice in the same frame and the driver consumes only
  the last - not a bug a human can hit, but a headless test must sleep
  between placements.
  RESTART PROOF (14:10): a fresh isolated session reactivated all seven
  test-save lots - five arterial, two cross-street - on the exact
  transforms they were placed with (cross west (-1880, -3280, yaw 90),
  east (1880, 3280, yaw -90)), masses and pads with the right offsets;
  the lane's lot_road_id helper (26/26) is what the legacy lots without
  a road_id key resolve through.

- **THE CORNER (2026-09-03 14:2x, owner's play report: "it allowed me
  to place where a building already existed, and they just grew into a
  morphed building").** The overlap scan compared spans WITHIN a road;
  a cross-street lot and an arterial lot share ground at the corner on
  different axes and were never compared. Fixed in placement.resolve_
  click: lot_rect() gives every lot's world footprint (span along its
  road, facade line to block back edge across it) and rects_overlap()
  refuses across all lots and roads; the reason names both roads.
  Self-test 27 (27/27) covers both directions. Checkpoint 0e35ee9 was
  committed on the owner's "commit it or not" just before this fix, so
  the fix is the first change after it. Live after re-registration once
  the owner's session ends (PIE was running when it was written).

- **GHOST PAD ON A BORROWED ACTOR (2026-09-03 14:5x).** With both lane
  sessions offline the coordinator ran the design lane's mk_ghost_mi.py
  (PIE measured off): MI_ghost_accept (opacity 0.34) and MI_ghost_refuse
  (0.00) created off M_WoodMaster with the blend-mode override, proven
  translucent AFTER a reload from disk. clickdriver now shows the ghost
  on the HIGHEST-numbered dormant POOL_ parcel (activation claims the
  lowest): material swapped on the Building component, size via WidthUU
  (the parcel's own change-detection scales the cube a frame later and
  RESETS the component's relative location, so the W/2 offset is
  re-applied every hover tick), hidden again off-plate; the debug box
  stays as the rim and the label. Capture at the boom's far stop: the
  translucent fill alone is not readable - D22's prediction - so the
  outline is kept over it. Runtime-only; nothing saved. Also seen in
  that capture: the editor status bar reads "30 Unsaved" - dirty
  packages from the day's lane work; NEVER save-all, the owner decides
  per asset.

- **FREE PLACEMENT ALONG THE ROAD (2026-09-03, owner: "let it slide
  freely along the road").** placement._snap now rounds to
  POSITION_QUANTUM = 10 uu instead of the 410 width quantum, so the pad
  lands under the click; widths stay on woodmap's ladder. Self-tests
  that encoded the old snap (1, 4, 5, 20, 21) were moved to the free
  values (27/27); the overlap and reach logic is unchanged and the
  ghost inherits it. Live after re-registration.

- **A JSON UNDER Content/ IS A DATATABLE SOURCE TO THE EDITOR (2026-09-03
  17:23).** placement.py's and citytick.py's self-tests wrote their
  throwaway state files next to themselves in Content/Python/; the
  editor's auto-reimport watcher saw each one appear, dispatched
  ReimportDataTableFactory on it (log: "FactoryCreateFile: DataTable with
  ReimportDataTableFactory ... _selftest_citystate_placement.json"), and
  on the third occurrence the game thread stopped answering - MCP calls
  timed out, the remote-exec node went silent - the shape of a modal
  prompt only the owner can dismiss. Both artifacts now live in
  Saved/SelfTest/. Rule: no test writes under Content/, ever; and when
  the editor goes silent, the first thing to read is the LAST log line,
  which named the cause here. Also from this window: the MCP property
  reader returns None for an enum it cannot see (BlendMode on a material
  instance's base-property overrides, typeface lists) - a None there is
  not absence; check through the in-editor API before calling an asset
  broken (design lane).
  THE CLASS, not the instance (design lane, beta lane, same hour): five
  JSONs sit under Content/Python - the owner's citystate.json, rewritten
  EVERY TICK by the economy driver; citystate_test.json (the lane
  isolation state, also rewritten during lane PIE); econrules.json;
  genbuild_identity.json; study_pose.json - all inside the /Game/
  directory the engine default monitors with only Localization/*
  excluded, and the project had no AutoReimport section of its own.
  Fix applied in Config/DefaultEditorPerProjectUserSettings.ini: the
  engine entry removed and re-added with Python/* and *.json excluded
  (FAutoReimportWildcard.bInclude defaults to false = exclude). Takes
  effect at the next editor start. Long-term the state files belong in
  Saved/, but moving the owner's save path is a change for their word.
  PROVEN BY A PROCESS SAMPLE (17:5x): the game thread sat in
  FAutoReimportManager::ProcessAdditions -> UCSVImportFactory::
  FactoryCreateText -> FSlateApplication::AddModalWindow - the CSV/JSON
  import options dialog, a Slate MODAL that stops every tick (MCP HTTP,
  remote exec, the drivers) while it waits, with the process at 100% CPU
  drawing it. Two facts for next time: it fires on file ADDITIONS (a new
  JSON appearing under /Game/), not on rewrites of an existing one, so
  the transient self-test artifacts were the trigger and the owner's
  per-tick save was not; and the dialog can sit behind the main window
  or on another Space, which is why "the editor should still be up" and
  "nothing answers" were both true. `sample <pid> 2` from the shell is
  the instrument when the editor goes silent - it needs no permission
  and names the frame.

- **SELECTION FLAG LIVE; BOUGHT MASSES HAVE NO COLLISION (2026-09-03
  22:5x).** The beta lane made BP_LensRig.SelectedParcel instance
  editable (set_variable_instance_editable, compile clean, explicit-path
  save); in an isolated PIE the driver's mirror write now lands
  (rig.SelectedParcel = P3 after a headless click). Found on the way: a
  cursor/line trace on ECC_VISIBILITY passes straight through a BOUGHT
  lot's wooden mass and hits the board - the baked masses carry no
  collision, only the placeholder pad cube does. So today a player can
  select a pad but not a building. Owning fix is the bake path
  (collision on the masses, or a per-lot invisible collision box the
  driver keeps on the Building component's footprint) - PLAYABLE_PLAN
  section 2.6's "click a building selects it" depends on it.
  HUD CLUSTER PROVEN BY CAPTURE (22:5x): with P3 selected headlessly the
  bar's right cluster reads "vernacular  UNOWNED  $66.4  PRESS B TO BUY"
  and the pad is highlighted cyan - the runtime-constructed HUD's
  selection half is live for the first time. (Status bar also shows a
  red "Diagnostics" badge - unread, worth a look when the editor is idle.)

- **BOUGHT-MASS COLLISION: DRIVER-SIDE, NOT THE BAKE PATH (2026-09-03,
  headless, answering the entry above).** Checked genbuild.py itself
  first, not just the finding above: zero matches for
  collision/CollisionComplexity/BodySetup anywhere in it - the bake path
  has never generated collision, not a flag left off. Recommend the
  per-lot box the driver keeps, not a bake-path change, for four
  reasons: no cross-lane dependency, ships without the design lane's
  schedule; no re-bake - the width-ladder-doubt finding already put the
  catalogue at 548 declared vs 284 baked, so a bake-path fix leaves
  every EXISTING mass collision-less until individually redone, where a
  driver-side fix covers every lot, old or new, the moment it activates;
  the geometry it needs (width, footprint) is already fully known to
  the driver - placement.py's width/side/road_id, the same width-based
  math _apply_lot_offset already does; and the pad and the bought mass
  are already the SAME "Building" component (PAD/MASS OFFSET FIX
  above), so this may not even need a new component - a runtime
  collision-profile override on that EXISTING component, in the same
  is_placeholder branch _apply_lot_offset already has, may be enough.
  That last point is the one open question, not settled here: whether
  Python reflection can set a StaticMeshComponent's collision profile/
  complexity at runtime the way it already sets relative_location.
  Also worth naming: a box across the LOT's own rectangular footprint
  may be the RIGHT shape for click-selection specifically, not a
  compromise - no notches a real silhouette could introduce, and
  SelectedParcel is a whole-actor selection everywhere in this project,
  never sub-mesh. Not a claim the bake path should never get real
  collision (physics, camera occlusion would want it) - only that
  PLAYABLE_PLAN 2.6's "click a building selects it" doesn't need it.

- **RUNTIME COMPONENTS CANNOT BE ADDED FROM PYTHON (2026-09-03 23:16).**
  The driver-side click box (a BoxComponent per lot) died in the same
  way the runtime spawn did: AActor.add_component_by_class is not
  reflected in this build (dir(unreal.Actor) has only add_tick_
  prerequisite_component / create_input_component), new_object makes an
  unregistered component with no physics state, and RegisterComponent is
  not callable. Removed. The slab ghost from the same window WORKS:
  SM_GhostPad_w820 on the borrowed pool actor, MI_ghost_accept, bounds
  820 x 1500 at the facade line, z 2..44. Building selection therefore
  goes the ASSET route: collision on the wood masses themselves - one
  mass first (add_simple_collisions BOX, or complex-as-simple on the
  body setup), proven by a trace that stops on it in an isolated PIE,
  then all masses; fastbake's enable_collision/collision_mode for future
  bakes is a shared-code change and the owner's call.
  COMPLEX-AS-SIMPLE IS NOT ENOUGH (23:3x): with the flag set and saved
  on SM_WMass_w820_setback2, and after reload_packages, a Visibility
  trace still passes through the mass in two isolated PIEs - the body
  never cooked; a trace flag cannot conjure a trimesh a GeometryScript
  mesh created with collision off never built. Next step is the
  analytic BOX (no cooking) as the mechanism proof, then convex
  decomposition for the silhouette, each proven by a trace before any
  rollout.
  RESOLVED (23:5x): the cursor trace was asking for COMPLEX collision
  (bTraceComplex=True) - per-triangle geometry the masses never had, so
  even the analytic box could not stop it; a sphere trace by profile hit
  P1 at once, and a SIMPLE line trace on Visibility stops on the mass
  (box), the pad cube, the board and both roads, and passes the ghost
  slab (0 prims, as it must). clickdriver now traces simple. Rollout of
  collision to all masses is the design lane's; shape (box vs convex
  hulls) decided by one more simple-trace test on the same asset.
  BUILDING SELECTION PROVEN (23:5x): with ONE convex hull on
  SM_WMass_w820_setback2 (set_convex_decomposition_collisions 4/16/100000
  - the decomposer returns exactly one hull for a stepped mass at every
  setting; a hull cannot follow a concave step) and the click driver
  tracing SIMPLE, a click on bought P1 selects it. The hull tapers: simple
  traces from z=6000 hit z=4352 at the centre, ~3530 at the base edges,
  the board just outside - less air than a 4581 box, more than the
  silhouette above the base stage. Rollout to all wood masses is the
  design lane's (hulls; box where the decomposer yields nothing).
  Ledger theme of the week, in the design lane's words: twice the fault
  was in the INSTRUMENT (a reader blind to an enum; a trace asking for
  complex geometry) and both times the SUBJECT was changed first.

- **GROWTH DECIDED BY THE OWNER (2026-09-03 late):** climbing upgrade
  price; performance from PLAYER TRADES ONLY (no automatic score); poor
  performance charges a premium, never blocks; pay to repair; nothing
  changes by itself. econrules.tick() stops tiering up; UPGRADE and
  REPAIR verbs join buy on the request-and-clear pattern; a neutral
  per-lot performance value waits for the trading system, which is the
  next design question for the owner (what a trade is).
  ECONOMY_TICK_CONTRACT.md carries the answers verbatim.

- **EDGE WEAR: FOUR SESSIONS OF NULLS EXPLAINED BY ONE WIRE (2026-09-04
  00:xx, design lane).** The curvature mask on the wood master read
  VERTEX COLOUR RED (unset = 1, so 1 - 1 = 0) while the real max|n|
  branch (Abs -> masks -> Max_1) was computed every frame and consumed by
  nothing. Every experiment for four sessions drove an INPUT that
  multiplied a mask that was zero - EdgeWearLift 12 and 100, Attention 8,
  the CPD flag, the chamfer, the PixelNormalWS -> VertexNormalWS
  correction - and every null was correct. Found in one window by wiring
  the mask to emissive and LOOKING at the value. Fix: Max_1 -> OneMinus_0
  on the FORK; proven 19x signal over drift on the chamfer columns. D16's
  cause is being corrected by its author; its symptom stood. Rule, in
  the coordinator's words: when a chain of nulls grows past two, stop
  driving inputs and read the intermediate value directly. Fork fix is
  IN MEMORY awaiting the owner's save word.

- **UPGRADE AND REPAIR LIVE (2026-09-04 00:xx).** The beta lane's
  econrules.upgrade/repair (13/13) and citytick wrappers (9/9) are
  consumed by the driver on Python-side channels
  (unreal._stacktown_upgrade_request / _repair_request, consume-and-
  clear next to buy - no GameInstance variables, Python-to-Python like
  the width channel); clickdriver binds U and R with on-screen results.
  Proven in an isolated PIE: select P3 -> B bought -> U "done", tier 0
  -> 1 -> R refused "not failed"; no CITY TICK tier-ups in the session
  (growth retired). Note: lots registered before the schema change lack
  'failed'/'performance' keys (read as None; econrules treats missing as
  neutral/not failed) - new lots carry them. Rent cadence (part E) still
  open; the test file's balance reads 60k. Edge wear: the design lane's
  A/B shows Attention 0 vs 1 at 32x signal over drift on the chamfer
  columns - D16's burnished arris renders for the first time; the fork
  save waits on the owner's word IN THE DESIGN SESSION (their rule).

- **THE GAME RUNS OUTSIDE THE EDITOR (2026-09-04 00:17).** The owner asked
  for a way to play as a user while the lanes edit, without leaving PIE
  on. Found: the uncooked editor binary with `-game` on TestCity loads
  the Python plugin (its main module is UncookedOnly, so it loads in
  -game), runs init_unreal.py, registers both drivers, restores the city
  from citystate.json and takes clicks - Tools/play.sh launches it.
  Three things had to change: a world lookup that works without editor
  subsystems (_find_game_world: find_object on the map's world path),
  FKey construction via import_text (set_editor_property('key_name') is
  editor-only), and pie_just_started True at registration (a game
  process never sees the no-world tick). TRAPS: (1) the game process
  answers the SAME remote-exec multicast as the editor and uepy.py
  connected to it first - rung.sh would have re-registered drivers in
  the game; uepy now waits for every node and probes for the editor
  (UEPY_WANT_GAME=1 to target the game); (2) the game ticks rent into
  the owner's save for as long as it runs, even with nobody playing -
  a test launch left running is a session; (3) the game shows what was
  on disk at launch - relaunch to see new work; (4) the marker file is
  read once at the game's start and never deleted by it.
  TWO DRIVERS, ONE SAVE - CLOSED (00:3x): the standalone game writes
  Saved/standalone.lock (its pid) at driver registration; an editor PIE
  whose resolver finds a LIVE pid there uses the test file and says so
  on screen ("A standalone game is running - this session uses the TEST
  save"), source 'standalone-lock' in the log line. Liveness by
  os.kill(pid, 0), proven on a live and a dead process; the explicit
  Python override still outranks it. The owner's editor PIE was the one
  session the lane-isolation rule never covered (beta lane's catch).

- **COORDINATOR'S OWN COLLISION (2026-09-04 00:4x).** Inside a granted
  design-lane window I started a two-minute isolated PIE to probe the
  camera rig, without telling the lane; the engine refused their actor
  cleanup ("Cannot remove actors while PIE is active") and left their
  Failure A/B subject (FAILAB_mass at the origin) stranded until PIE
  ended. The rule I set for lanes applies to me: no PIE inside another
  lane's window without saying so first. Same hour, design lane: a
  Failure wiring that lerped base colour to a flat grey measured +65
  levels at 145x noise and was WRONG - bleached plaster, grain gone; a
  large delta praised a wrong look. Rebuilt as desaturation x cold tint
  so luminance and figure survive; D16's "species legible to the end"
  outranks any number. And: the one script written in a hurry was the
  one without a PIE guard.

- **CAMERA MOVES INTO THE PYTHON DRIVER (2026-09-04 00:5x).** The owner's
  first report from the standalone: "the camera controls don't seem to
  work". The rig re-applies its pose from its own variables every tick
  (a direct transform write reverted within a frame) and eases each live
  value (Azimuth, Reach, Height, Tilt, Pan, Focal) toward a Tgt* twin;
  all twelve were read-only from Python until the beta lane made them
  instance-editable (flags only, two scoped passes). clickdriver now
  drives them: A/D orbit, W/S reel, Q/E the camera study's four stops,
  arrows pan BoardCentre in the camera frame, writing Tgt* first and the
  live value second. Proven in an isolated PIE: TgtAzimuth 250 -> 290
  turned the rig to yaw 110 and TgtReach 19000 -> 9000 moved it, within
  two seconds. Whether the rig's own TickBody still handles keys is
  unverified (beta lane: honest non-answer); if the owner sees double
  motion, the graph side is alive and must be found - no rewrite.
  ANSWERED BY THE OWNER'S NEXT RELAUNCH (01:0x): "camera rig seems to
  work better but starts fighting itself once zoomed in with the Q/E
  buttons" - so the rig's graph still runs its Q/E zoom ladder (that
  part of TickBody's input survived the rewrites) and two writers made
  two targets alternate. Python dropped Q/E; the graph keeps the ladder,
  Python owns orbit, reel and pan. A fight on a key is the tell that
  the graph side of that key is alive.
  RESOLVED BY READING THE RIG'S OWN DOC (01:2x): Docs/LENSRIG_P0.md has
  the complete boom-space scheme - A/D arc, W/S proportional reach, R/F
  pedestal, arrows head pan/tilt, E tighter, Q wider - and it is ALIVE;
  the Python camera duplicated A/D, W/S and the arrows, so every pose
  variable had two writers ("wonky", "can't zoom out"). The Python
  camera is removed; the rig keeps its own controls; REPAIR moved from R
  (the rig's pedestal) to H. The original "camera doesn't work" in the
  standalone was most likely keyboard FOCUS - the doc's own first
  instruction is "click into the viewport so it has keyboard focus" -
  not dead input. Lesson: the rig's doc existed the whole time; read
  the owning doc before probing a live object.

- **ROADS, WIRED END TO END, UNTESTED LIVE (2026-09-04 01:4x).** Beta
  lane: road state in citystate, placement.ROADS dynamic (state roads
  + the two built-ins), lot_rect by the lot's own road axis,
  resolve_road_draw/draw_road with the pinned-lot gap closed,
  axis-aligned segments only in v0 (39/39). Coordinator: the driver
  consumes unreal._stacktown_road_request like place, draw_road is the
  authority, a dormant POOL_ROAD_NN StaticMeshActor shows the segment
  (section-5 transform: chord centre, one yaw, scale length/100 x
  CORRIDOR/100 x thin), drawn roads restore at session start; the click
  driver's G key toggles road mode (first click start, second end, the
  chord previewed through resolve_road_draw). No pool actors exist yet -
  a road drawn now exists for placement and says so on screen but is
  invisible until mk_testcity_builds.py places the pool (an editor window
  plus the owner's word for saving TestCity).

- **THE MARKER FLIPPED A RUNNING GAME'S SAVE FILE (2026-09-04 01:5x).**
  _state_path_for() resolved the file on EVERY call, so when the
  coordinator wrote lane_pie.marker for an editor test while the owner's
  standalone game was running, the game's next ticks wrote the owner's
  state into citystate_test.json, then back into citystate.json when the
  marker went (both files identical, four seconds apart) - and the test
  road R1 / lot P9 drawn in the editor session vanished under it. The
  owner's save was never wrong, only mirrored. Fix: the path is resolved
  ONCE at session start and cached in the driver state (cleared at PIE
  end; a game process keeps its first answer for life). Until the owner
  relaunches, the running game still carries the old resolver, so NO
  MARKERS while it runs - an editor PIE under the standalone lock lands
  on the test file without one. Rule: anything that steers a running
  process by a file on disk must be read once, at a boundary, never per
  call.

- **ROAD POOL IN TESTCITY, ROADS VISIBLE (2026-09-04 02:2x, owner's word
  "save the testcity for road pool").** mk_roadpool.py placed ten
  POOL_ROAD_NN StaticMeshActors (stock cube, MI_studio_grey, hidden, no
  collision) at the parcel pool's graveyard; save_current_level saved
  TestCity only (the dirty wooden master untouched, checked by mtime).
  First proof failed the useful way: the piece took the label, scale
  and visibility but stayed at the graveyard - a placed StaticMeshActor
  is STATIC mobility and SetActorLocation is a no-op on it in play.
  Pieces are now Movable at build time and the driver sets mobility
  again before moving. Proven: R1 drawn (6500,1500)->(6500,4000) put
  POOL_ROAD_00 at (6500, 2750, 4), yaw 90, scale (25, 22.6, 0.08),
  visible, on the test file. INCIDENT, cleaned: the owner had closed
  their standalone game, so the lock no longer steered my proof PIE
  and it ran on the owner's save - a test road R1 was drawn into it
  and removed by hand (backup in the scratchpad; their eight lots
  untouched). Rule: before any coordinator PIE, write the marker
  unless a game with the OLD resolver is running - never rely on the
  lock alone, it depends on a process the owner can close at any time.

- **PER-LOT WEAR PROVEN (2026-09-04 03:xx, design lane's framing,
  coordinator's session).** Four adjacent same-species oak towers
  (recipe 'tower' - 'shop' is not in DA_Catalogue_Wood - tier 3, width
  1230) on the arterial's north side; P2 held at Failure 0.85 and P3 at
  Scorch 0.5 through set_custom_primitive_data_float on their Building
  components (the driver's sync now honours a per-lot override dict, the
  headless hook unreal._stacktown_set_cpd); frames A, A' (drift) and B
  shot from INSIDE the session by HighResShot 2 in the game world -
  CaptureViewport renders the EDITOR world and showed bare plate, and
  so did the first in-session shot, because the rig had been given a
  reach without the stop's height and tilt (two paths, one blind spot:
  "agreement between two instruments is evidence only if they can fail
  separately"). Framed from due south at the BLOCK stop, which MIRRORS
  x in the frame (left to right P4..P1). Design lane's measurement: P1
  and P4 within their drift floors; P2 uniform (-26.6/-27.4/-28.0 top/
  mid/base, spread 1.4); P3 top-down (-30.3/-9.0/-0.1). Per-lot, not
  per-species; fire and bankruptcy told apart by shape. D23 unblocked.
  The override dict was cleared after the session - its keys are pids,
  and the owner's save has a P2 and a P3 too.

- **NIGHT GLOW: MATERIAL WIRED, TWO GAPS FOUND BY THE FRAME (2026-09-04
  04:xx).** Design lane: emissive = GlowTint(GlowState) x GlowLevel x
  NightAmount on the fork (252 expressions, unsaved), NightAmount a
  scalar on MPC_WoodCity (deliberately not "Stacktown" - only the wood
  master reads it); coordinator: the sync pushes GlowLevel/GlowState per
  lot (for sale 0.35/0.5, owned 0.15/0.5 - for sale brighter, D23) and L
  toggles NightAmount through MaterialLibrary.set_scalar_parameter_value
  (set and read True). The acceptance frames (glow_D1/D2/N1/D3.png,
  in-session HighResShot) then showed: (1) a FOR-SALE lot is the
  placeholder pad - engine cube, BasicShapeMaterial - so the for-sale
  glow has no fork material to render on; (2) NightAmount only gates the
  emissive; nothing dims the world lights, so "night" is a daylit board
  with an invisible 0.15 emissive. Both go back to the design lane as
  declarations: a fork material for the pad (the ghost slabs already
  live on the fork) and the night lighting STATE (per-light intensities)
  the L toggle will apply. Per-lot glow remains unproven until then.
  NIGHT MECHANISM (04:xx): L applies NightAmount on MPC_WoodCity AND dims
  the rig by the design lane's fractions (Sun 0, Key 0.10, Fill and
  StreetKeys 0.04, Sky 0.15 and cooled, BoardKey 0), day values captured
  from the actors at first use and restored by day. CITY_Sky is a
  SPECIFIED CUBEMAP (GrayLightTextureCube), not a scene capture, so
  intensity is the right dial. The studio wall: M_StudioWall is SHARED
  (Sandbox_Bench renders it) while MI_studio_wall_city is ours - and an
  instance cannot read a parameter collection, so the wall gets a
  second fork (M_WoodStudioWall, NightWallDim 0.12 from the same
  collection), our one instance re-parented, the flagship master
  untouched and named in woodmaster.py's guard. For-sale glow dropped:
  D20 says an unbought lot is bare board and reads by absence.

- **NIGHT, FIRST FRAMES (2026-09-04 05:xx).** Studio-down proven: the
  backdrop fell to 18.6% of day through the wall fork reading the
  collection, the plate to 9%, form legible under the tenth-key, pads
  gone into bare board, day restored within drift - "I would not move a
  light" (design lane). The glow push is proven PER LOT on ch1: one
  owned tower held at GlowLevel 1.0 rose +4.38 while its same-species
  neighbour at 0.15 moved -0.88 and the road -0.40. But 6.7x the level
  bought 4 displayed levels: the emissive is an order of magnitude too
  weak for this exposure (a lit surface sits well above linear 1.0
  under the key; an emissive of 1.0 is a dim emitter here). Decision:
  a GlowScale in the material, CPD stays 0..1 - but NOT set yet: the
  window-slot mask (B4: windows exist only as night light through
  etched slots) changes the required scale by the inverse of slot
  coverage and a flat facade reads as a lit box at any brightness, so
  the mask is declared and built first and the scale tuned once against
  the masked look. Overrides cleared after the session.

