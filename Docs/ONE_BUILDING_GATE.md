# The One-Building Gate

**Written 2026-08-23, before any geometry existed.** That ordering is the point. Both
predecessor projects wrote their acceptance criteria after the work, which is how criteria
quietly bend to fit what got built.

## The question

> Can a single building be authored in Unreal 5.8 so that it reads as a photographed
> physical scale model?

Not a block. Not an intersection. One building, on a board, in a lit room — and before
that, one bay.

If the answer is no, no asset package fixes it and no procedural system fixes it, and you have
found that out for $0 instead of $200 and a month.

If the answer is yes, you have a depth recipe and a material recipe — and *then* an asset
purchase has a specification to shop against instead of a vibe.

## Two stages, and the first one is smaller than a building

**Stage 0 — one bay.** Before a building exists, build a single facade bay: one window, one
sill, one spandrel panel, one strip of wall, on a board. Roughly one to two sessions.

Stage 0 answers the identical question a building would, at a twentieth of the cost: *can a
surface in this project read as fabricated rather than rendered?* If one bay cannot, no
building can, and no asset package changes that. If one bay can, the recess depths and material
parameters that made it work are the recipe — and a building is that bay repeated with a ground
floor and a roof condition.

### Stage 0 carve-out

*Added 2026-08-23 by owner decision, after Stage 0 was built and walked. This is an
amendment by the owner, not a downward negotiation by an agent — that remains prohibited.*

Stage 0 as originally written was judged against sections **A, B, D, E, F**. Building it
exposed two places where that is not executable, so the scope of each line is now stated
explicitly.

**Applies at Stage 0 — full pass/fail, no partial credit:**

- **A1, A2** — window recess and sill. These are the reveal lines a bay can carry.
- **B1–B6** — the whole material and fabrication section.
- **D1–D4** — environment, light, fixed exposure, no clipping.
- **E1–E6** — evidence discipline in full.
- **C2, C4** — board edge and contact shadows.

**Not applicable at Stage 0:**

- **A3** parapet/cornice, **A4** inset ground-floor entrance, **A5** curb and sidewalk,
  **A6** silhouette broken by three projections.

  These describe building-scale features that `Docs/BAY_RECIPE.md` explicitly forbids
  building in Stage 0 ("Do not add a second bay type, a ground floor, a roof, a tree, a
  prop"). A single upper-floor bay has no roofline, no entrance, no curb and no silhouette
  to break. Failing a line for the absence of something the recipe prohibits would be
  scoring the gate against a scene it forbids. They are **deferred to Stage 1, where they
  apply in full.**

- **F1** — the subjective line.

  **Owner's rationale:** a single bay is not enough to judge whether the result reads as a
  real diorama model. That judgement needs a full small building — massing, roofline,
  ground floor and silhouette together — because it is the whole object a person responds
  to, not one facade panel. F1 is therefore **deferred to Stage 1.**

  This contradicts the claim above that "Stage 0 answers the identical question a building
  would." That claim is hereby narrowed: **Stage 0 answers whether a *surface* can read as
  fabricated. It does not answer whether the *object* reads as a model.** The second
  question is Stage 1's.

**The deferral is not a waiver.** It moves F1; it does not weaken it. Specifically:

1. Stage 1 is judged against the **whole** gate, F1 included, with no further carve-out.
2. **F1 must be tested before any scope beyond Stage 1 opens** — no block, no
   intersection, no district, and no asset purchase justified by "it will look better at
   scale."
3. F1 is tested as written: a person who has not seen the project is shown the capture
   with no explanation. An agent's own opinion is not a substitute and never satisfies it.
4. If A through E pass at Stage 1 and F1 still fails, the original instruction stands —
   that is the most valuable possible result, and the cause must be found before anything
   else is built.

**Known cost of this amendment, recorded honestly:** the gate was designed to answer the
visual question at a twentieth of the cost, "for $0 instead of $200 and a month." Deferring
F1 to Stage 1 gives up that cheapness. Stage 0 now completes without the headline question
answered, and the Stage 0 recipe carries forward as an untested premise. That is the
owner's accepted risk, taken deliberately and with the alternative understood.

Build instructions with real numbers are in `Docs/BAY_RECIPE.md`.

**Stage 1 — one building.** Only after Stage 0 passes. Judged against the whole gate.

Do not start Stage 1 because Stage 0 went well. Stage 0 passing means the recipe exists; the
owner decides when Stage 1 opens.

## What gets built

One building. Approximately four to six storeys, contemporary, Portland-plausible mixed-use.
Ground floor plus a repeating upper facade plus a roof condition.

Plus exactly this and nothing more:

- one model board it sits on, with a visible edge
- one strip of sidewalk and curb along its street face
- one tree, real, not a sphere
- one room-like environment for it to be photographed in — a backdrop and a ground plane, so
  the building is lit by a place rather than floating in a void
- one key light, one fill, and whatever practicals the building's own windows need
- one camera at 70mm
- one PostProcessVolume with **fixed** exposure

No vehicles. No people. No second building. No signage beyond what the building itself carries.

## The gate

Every line is pass/fail. There is no partial credit and there is no "close enough for now".
Evaluate at the approved camera, at fixed exposure, **with depth of field, bloom, and motion
blur disabled**. Finishing effects are judged only after the gate passes without them.

### F1 result — 25 August 2026

**Tested as written**: a person who had not seen the project was shown a capture
with no explanation. Recorded here because "done" is not a result and the gate
distinguishes hard between the two outcomes.

**Verdict: PASS, with a finding.** The reader judged that the main city pulls
off the miniature look convincingly. They also observed, unprompted, that as
blocks were built out into the sandbox the work appeared to lose architectural
detail, architectural logic and material richness. The owner agrees with that
observation.

**A pass with a finding is not a clean pass, and the finding is the useful
half.** It was measured rather than argued about (`Content/Python/richness.py`).

The first measurement was **wrong and is corrected here.** It counted a level
that contained 151 duplicate actors - `step_elevations` wiped over MCP, the call
that silently returns nothing, so a standalone re-run stacked a second set of
elevations and in places a third. That inflated deco to 905 parts and
vernacular to 383. `NAME-03` now fails the build on any duplicated label, and
the level shrank from 6.29 MB to 5.22 MB when they were removed.

The denominator was wrong too. Parts per metre of frontage is unfair to a low
building: a two-storey block over 13 m has half the elevation of a four-storey
one and cannot carry the same count. **Parts per square metre of street
elevation** is the honest measure.

Deduped, area-normalised, and after the modern ribbon and arcade were
articulated:

    style        parts/m2 range      mean
    house        4.26 - 4.91         4.43
    walkup       2.66 - 4.08         3.58
    deco         1.06 - 1.41         1.29
    vernacular   0.65 - 1.71         1.15
    modern       0.52 - 1.04         0.76

**The reader was right and the direction survived the correction**: modern is
the thinnest style on the board, and its worst - Court at 0.52 - sits beside a
Marquee at 1.41. Block C was called "more rough draft than our first street"
when it was built and was never brought up to standard.

**Consequence.** Detail density becomes a measured invariant rather than a
habit, so a style cannot ship under-built again. `DETAIL-01` is set at **0.70
parts per m2**, which is ABOVE four buildings that are genuinely thin - Court
0.52, Civic 0.57, Annex 0.65, Narrow 0.65 - and not below them. **The suite is
red on this rule on purpose.** Tuning the threshold down to green would be the
exact failure this document opens by naming: criteria bending to fit what got
built. Those four are the punch list. See `Docs/INVARIANTS.md`.

### Finishing-effects carve-out

*Added 2026-08-25 by owner decision. This is an amendment by the owner, not a downward
negotiation by an agent — that remains prohibited.*

The rule above stands **for evaluation**: every gate line is still judged on a capture with
depth of field, bloom and motion blur off, at the approved camera and fixed exposure. What
changes is that finishing effects may now be **developed and reviewed before the gate is
passed**, rather than only after.

**Owner's rationale:** the project is eight blocks in and the lens treatment is part of the
art direction being decided, not a polish pass bolted on at the end. Waiting until F1 passes
would mean choosing the whole look blind.

**What this does not do.** It does not weaken any gate line, and it does not move F1. In
particular:

1. **Gate evidence is captured with the effects OFF.** A DOF frame is never gate evidence,
   for the same reason `AGENTS.md` forbids submitting a `-NullRHI` run: it is not the thing
   being judged.
2. **A DOF-off camera is kept alongside every hero camera**, so the geometry stays gradeable
   at all times.
3. **F1 is still untested and still gates scope.** This amendment is about effects, not about
   the cold read.

**Known cost, recorded honestly:** depth of field hides geometry. At f/2 on a board-wide
shot almost nothing is sharp, which flatters the model and conceals exactly the depth,
alignment and material faults sections A and B exist to catch. That is why point 1 above is
not negotiable — the risk of this amendment is that a pretty frame starts standing in for a
graded one.

### A. Geometric reveal — the thing that failed last time

- [ ] **A1.** Every window is recessed into the wall plane. The recess depth is visible as a
      shadow line at the approved camera. No window is a texture or a coplanar decal.
- [ ] **A2.** Every window has a sill or a projecting frame with real thickness.
- [ ] **A3.** The roof terminates in a parapet or cornice with visible cap thickness. The
      roofline is not a zero-thickness plane.
- [ ] **A4.** The ground-floor entrance is inset from the facade plane.
- [ ] **A5.** The curb has height. The sidewalk meets the road with a visible vertical face.
- [ ] **A6.** Silhouette against the backdrop is broken by at least three real projections —
      a canopy, a balcony, a rooftop unit, a fire escape, a sign bracket. Not a flat box.

### B. Material and fabrication language

- [ ] **B1.** Every material slot on every visible mesh is assigned. **Zero default-material
      surfaces.** Unassigned materials rendering as flat green shipped in the last project's
      final evidence image; that must never recur.
- [ ] **B2.** All architectural surfaces derive from the master material described in
      `Docs/MASTER_MATERIAL_SPEC.md`. They share one roughness range and one weathering logic.
- [ ] **B3.** The surfaces read as *fabricated* — painted, printed, cast — not as real
      full-scale concrete and steel. This is what makes it a model rather than a small city.
- [ ] **B4.** Glass has physicality: frame depth, a reflection that responds to the
      environment, and something behind it. Not a flat gradient with a glow.
- [ ] **B5.** Texel density is consistent across the building. No surface is visibly softer or
      sharper than its neighbours at the approved camera.
- [ ] **B6.** Edges are softened, as fabricated edges are. No razor-perfect zero-radius corners.

### C. Scale and physicality

- [ ] **C1.** Storey height, door height, window proportion, curb height, and tree height agree
      with each other and with a human scale.
- [ ] **C2.** The board edge is visible and reads as a physical base the model sits on.
- [ ] **C3.** There is at least one deliberate fabrication imperfection — a seam, a slight
      panel misalignment, a paint variation. Perfection reads as CG.
- [ ] **C4.** Contact shadows are present and correct where every object meets the board.

### D. Environment and light

- [ ] **D1.** The building is not in a black void. There is a backdrop and a ground beyond the
      board, and they contribute bounce light.
- [ ] **D2.** Lighting is directional and purposeful, with a readable key direction.
- [ ] **D3.** Exposure is fixed, not automatic, and its value is recorded with the capture.
- [ ] **D4.** No blown highlights and no crushed blacks at the approved camera.

### E. Evidence discipline

- [ ] **E1.** The capture was composed and taken deliberately. **Not** produced by a startup
      script or any automated trigger.
- [ ] **E2.** The capture is clean — no editor gizmo, no selection outline, no sprites, no
      viewport overlay. Simulate mode or a proper HighResShot.
- [ ] **E3.** Camera transform, FOV/focal length, exposure value, resolution, and quality
      settings are recorded alongside the image.
- [ ] **E4.** A second capture exists from a different angle within the intended envelope, and
      the building holds up in it.
- [ ] **E5.** Frame time and resident memory were measured on the Mac mini at the approved
      camera.
- [ ] **E6.** `Content/Python/stacktown_validation.py` reports zero hard failures.

### F. The only subjective line

- [ ] **F1.** Shown the capture with no explanation, a person says it looks like a photograph
      of a physical model.

F1 is the actual gate. A through E exist because every one of them was a specific, documented
reason the last attempt failed F1. If A through E all pass and F1 still fails, that is the most
valuable possible result — it means the problem is somewhere none of us have named yet, and it
must be found before anything else is built.

## If the gate fails

Revise the reveal depth, the master material, the glass, the lighting, or the camera. In that
order — it is roughly the order of impact.

**Do not add a second building.** Do not add props to distract from the failure. Do not enable
depth of field to blur it. Do not buy an asset package hoping it carries the look. Report the
failure plainly, name which numbered line failed, and stop.

## If the gate passes

The project's purpose is complete. Record the recipe — reveal depths, material parameters,
light rig, camera, exposure — as the specification. The owner decides what opens next. An agent
does not expand scope because the gate passed.

---

## Stage 2 carve-out — one block (owner decision, 2026-08-23)

**Approved explicitly in conversation by the owner on 2026-08-23**, after a second agent built
a Portland block in a separate sandbox and the owner chose to build one to this project's
standards instead. This crosses the `CLAUDE.md` hard stop on "a block, an intersection, or any
city context". It is recorded here so the crossing is deliberate and dated rather than quiet.

Stage 1 is not revoked. `Stage1_Building` and its evidence stand as the passing record for a
single building. Stage 2 is additive and lives in its own sandbox map.

### What changes, and it is not what it looks like

The temptation is to treat a block as "Stage 1, five times". It is not, because the camera
moves back and **the 0.4%-of-frame-width rule invalidates almost everything Stage 1 learned
about surfaces.**

Measured at the Stage 1 hero (95 m, one building filling 60% of frame height) against a block
hero framing the whole board:

    Stage 1 hero      0.4% threshold ~19 uu   (190 mm)
    block hero        0.4% threshold 39-51 uu (390-510 mm)

Against that, everything built in the last pass — panel seams 6 uu, glue beads 12 uu, chamfers
4 uu, the dent 2 uu deep — is below threshold at a block hero, and below it at a block
*inspection* camera too. **Surface work does not transfer. Do not port it and do not let its
absence be read as a regression.**

### The actual requirement: hold at two ranges

The project's goal is a living diorama city the player zooms into. So the block must read as a
model at BOTH:

  block hero        whole board in frame — carried by MASS: setbacks, roof clutter, parapet
                    and cornice depth, canopy projection, silhouette variation between
                    buildings, and the gaps between them
  player zoom       one facade filling the frame — carried by the Stage 1 surface toolkit,
                    which already exists and already works at that range

A block that only works at one of these is not a pass. This is the new gate line and it is the
whole point of Stage 2.

### Constraints carried forward unchanged

- One master material. Role instances only. No second master.
- Card material band: roughness 0.62-0.80, specular 0.20, band width ~0.18.
- Fixed manual exposure. Bloom, DOF and motion blur OFF. Grain, vignette and fringing allowed.
- Light intensity scales with the inverse square of rig distance. Re-derive it; do not reuse
  Stage 1 numbers at a block rig distance.
- No purchased or imported assets.
- Work in a duplicate sandbox map. `OneBuildingTest` remains untouched.

### Still prohibited at Stage 2

People, vehicles and signage remain out unless the owner reopens them separately. PCG stays
disabled. `AllToolsets` stays excluded. No C++ module.
