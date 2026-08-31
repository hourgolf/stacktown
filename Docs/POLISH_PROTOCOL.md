# The polish protocol

Adopted 2026-08-27 from the scaling review's recommendation, with the
coordinator's loop wrapped around it. This is how polish scales to hundreds
of buildings and stays sane at thousands.

## The doctrine, restated once

**Polish the systems; gate the instances. Never hand-finish a building.**

Every polish finding resolves into exactly one of four outcomes. There is no
fifth outcome, and "I'll just fix this one building" is not on the list —
a fix that touches one building is a fix in the wrong place. The evidence:
three whole-catalogue defects (deco's missing glazing, the dark-quad
foliage, the roof flicker) each looked like per-building art problems and
each was a one-line systems fix.

## The four outcomes

| outcome | goes to | required companion |
|---|---|---|
| **Generator fix** | genbuild / recipe / step_* | a gate rule that would have caught it, wherever one is expressible |
| **Gate rule** | modelgate / invariants, with self-test | nothing — it IS the companion |
| **Vetted kit part** | avkit, through the donor sheet (rendered and LOOKED at, per `Docs/DONORS.md`) | — |
| **Closed** | the finding log, marked not-worth-doing with a sentence of why | — |

The companion-rule requirement is the hardening: a generator fix without a
regression rule is a fix that will be re-made at three times the catalogue
size. GATE-09 and GATE-10 are the pattern — every defect that earned a fix
also earned the rule that keeps it fixed.

## The loop

1. **Sheets, not strolls.** Findings come from contact sheets rendered at
   exactly two framings — player zoom and block hero — because the 0.4%
   table makes those different quality questions. Nobody browses meshes.
2. **Cold review.** A reviewer agent loaded with ONLY `Docs/CANON.md`, the
   reveal hierarchy, and the gate vocabulary — never the build context —
   files findings in fabrication language, each citing the canon slot and
   blessed quality it judges against (or stating that no slot covers it).
   The builder never reviews its own wave.
3. **Owner spot-check.** The owner reviews everything flagged plus ~10% of
   passes, sampled. When sampled passes keep failing the owner's eye, the
   reviewer's brief gets corrected — not the individual models.
4. **Triage.** Every finding through the four outcomes. Triage is where the
   never-hand-finish discipline is enforced.
5. **Waves re-bake everything.** Fixes land in batches; each batch is
   followed by a full catalogue re-bake, re-gate, re-stamp, fresh sheets.
   At ~7 s per model the full catalogue re-bakes in well under an hour —
   which is the entire economic argument for the doctrine. The catalogue is
   cattle, not pets.
6. **Convergence is the stop condition.** Findings-per-wave must fall.
   The polish pass is DONE when a wave produces only "closed" findings —
   a measurable end state, not a feeling.
7. **Cold human reads punctuate the waves.** One per major wave, on the
   street or a block, per the gate's contract: no agent opinion — the
   reviewer agent's included — ever settles the illusion question.
   **Timing (owner, 2026-08-27):** a read triggers on the FIRST CLEAN
   CAPTURE from current framing — never on polish converging. "Show it
   when it's better" is the procrastination shape that ate the
   predecessors; the read's value is diagnostic and decays.
   **Lens protocol (owner, 2026-08-27):** the reader sees the SHOW-camera
   frame FIRST — the shipped claim, and a real photo of a real miniature
   HAS macro optics; their absence is itself a render-tell — optionally
   followed by a judge-mode frame, which MEASURES how much the lens buys
   in the reader's own words. The judge-with-DOF-off rule is for US, so we
   never hide weak geometry from ourselves: all production judging and all
   gate evidence stays lens-off. Two named camera modes (judge | show)
   with settings READ BACK after applying, show-mode DOF DERIVED from the
   fiction (a real camera at model distance from a 1:87 subject — macro,
   never tilt-shift filter), and EVERY capture stamped with the mode that
   took it, so a show frame can never quietly become judging evidence.

## Standing instruments

- **The lever diff.** Before believing any proposed variation lever, emit
  the geometry twice and diff it (with a known-answer check first). This
  instrument killed the per-parcel-seed plan — seed moved 2 parts, 0
  visibly; parcel width moved 322 — and must be run on every future lever.
- **Variety is bought with parcels, not randomness.** Placement owns
  variety: no two parcels on a block share (recipe, tier, width); width is
  tried before tier. The district placer, not the generator, is where
  variety investment goes.
- **The donor-bounds limit.** Offline tooling reasoning over recorded parts
  CANNOT see a donor mesh's true bounds (maker-local pivots). Any offline
  check touching donor geometry needs the mesh-bounds table, and any new
  offline tool must state which side of this limit it stands on.
- **Instrument hygiene: a check calibrated against a real defect must be
  re-pointed at a SYNTHETIC one the moment that defect is fixed.** The
  ladder sweep's fail-case was the real canopy bug; fixing the bug left the
  sweep with two passing cases and no proof it could detect anything — it
  failed OPEN and would have kept reporting confidently. Replaced with a
  planted yaw-180 defect (clean 0.0 / planted 1568.0 SEEN). When fixing any
  defect that a check's known answer depends on, replacing the known answer
  is part of the fix. Other checks in this repo calibrated against real
  defects should be audited for the same shape.
- **The honest catalogue precedes breadth.** No zoning or archetype plan is
  sized against declared combinations — only against baked-and-stamped
  ones. CORRECTED 2026-08-27 (S18): the ladder sweep measures the X axis
  ONLY, so its "548/548 buildable" was a WIDTH claim misreported as a
  GATE-05 claim. The wave found the depth axis honestly: 18 refusals, all
  contemporary6 (every tier x width), donor-driven — boxes span 961 inside
  the allowance, boxes+donors span 1107, exceeding depth 900+130. Current
  honest state: 530/548 baked and fastbake-stamped; 18 contemporary6
  combos OUTSTANDING BY DESIGN pending a real recipe fix; 6 old
  contemporary6 assets on disk are falsely certified (they passed depth
  only because their donors were missing).
- **Graduated rules: a new rule that would mass-refuse the existing corpus
  enters PENDING, not RULES.** Registering GATE-11 on day one would have
  refused all 548 models (73,582 coplanar pairs, median 72 per model) and
  taught everyone to pass the gate with --force - the failure mode the
  gate's own header says must never install itself; GATE-01 did exactly
  this when donors became real. A PENDING rule runs its self-test with the
  voting rules so it cannot rot, MEASURES the debt on every run, and moves
  into RULES in one line when the debt is paid down. The debt curve is the
  progress metric (GATE-11: 73,582 -> 32,060 in wave 1a).
- **GATE-11 ARMING (owner, 2026-08-29): budget + ratchet.** Baseline is the
  SQUARE catalogue census, independently re-derived by the coordinator
  before the number went to the owner: 548 models, 13,976 visible pairs,
  37 clean, median 19 / p90 55 / max 208. Armed as:
    1. REGRESSION, effective immediately: a rebaked/changed model may not
       INCREASE its visible-pair count. Full stop, no tolerance.
    2. BUDGET, opening at **N = 75 visible pairs per model** (refuses 25 of
       548 at arming), ratcheting 75 -> 50 -> 30 as fix waves clear. N only
       decreases; every change to N is the owner's word; the gate prints
       the budget it judged against in every verdict; the per-model count
       is stamped into provenance so nothing hides in an aggregate.
  Zero-tolerance was rejected because a bar the corpus can never clear is
  how --force installs itself (above); the size-threshold alternative was
  MEASURED closed (minov=8.0 already exceeds the 0.4% player-zoom
  threshold of 1.85 uu, and per-framing thresholds would forgive debt only
  at block hero, against the both-framings rule). Sequenced owner calls,
  same date: targeted contemporary2 pass FIRST (the tail is that one
  recipe - excluding it the max falls 208 -> 115), and roof planting
  outranks the whole pair list (green plaid is naked-eye; pairs need an
  instrument). Code arming in modelgate.py follows the planting work.

- **The fix-class ladder: instance param < stock swap < NEW ASSET < graph
  change < doctrine** (owner, 2026-08-28: a new asset ships with its
  GENERATION SCRIPT committed alongside — reproducible, never a
  hand-painted orphan — gated by study acceptance plus the owner's look;
  hand-made assets without a script need explicit per-asset sign-off).** Every finding is triaged to a rung - the rungs have different
  approval gates and different blast radii - and findings are placed AFTER
  isolation, never from the symptom: the vehicle finding looked like rung
  four when the reader described it and landed on rung two once the A4
  panel isolated scale from family. A split proof standard is named BEFORE
  any multi-part change starts (the no-op half proves byte-identity; the
  look-change half proves itself on the study wall plus owner eyes), so a
  no-op instruction can never quietly cover a look change.

- **Every sweep table carries a KNOWN-ANSWER CELL** - one row whose value
  is already established (e.g. the master-default configuration must
  reproduce the baseline panel's numbers). A table without one cannot be
  believed: the first route-2 sweep read plausibly and monotonically and
  was garbage - the far camera was photographing another panel's back.
  The known-answer cell is what caught it.
- **A measurement floor is measured ACROSS the perturbation class it will
  judge.** A noise floor from two captures of a static scene does not
  cover a comparison spanning a shader recompile - Lumen's cache
  invalidation measured 47.5 between captures of an IDENTICAL scene, a
  false positive shaped exactly like a real finding. Settle to a
  criterion; take null-state bands across the same class of change.

- **The detail metric has no opinion on STRUCTURE.** Detail >= 3.0 at both
  standoffs measures how much fine variation exists; a lattice motif is
  dense in exactly the band the metric rewards. Demonstrated four times in
  one work item: cross-hatched linen, houndstooth, tweed and camouflage
  all PASSED the numbers - several with the best scores yet - and every
  one failed the look. The numbers gate admission to the look; they never
  substitute for it.
- **Attribution and acceptance are different jobs on different surfaces**
  (owner, 2026-08-28). The study wall - one variable, one flat sample - is
  the ATTRIBUTION instrument. ACCEPTANCE happens on a BUILDING: windows,
  bands, reveals, grazing light and silhouette change the verdict (the
  same material read as tweed on the wall and stucco on a building), and
  the flat slab hides amplitude entirely (2.0 reads as texture on a slab
  and as RELIEF on a pier). Amplitude is in every sweep from now on.
- **FAB-FIRST: survey what is installed before generating** (owner,
  2026-08-28). The new-asset rung's gate now BEGINS with "prove nothing
  installed serves." 722 textures were available; a noise generator was
  written first, its axis-aligned lattice artifact survived six tuning
  attempts because it was constructional, and the FIRST surveyed
  photographic normal beat it at both standoffs. Reproducibility is not
  a reason to synthesize what photography already did better.

- **The metric sees QUANTITY, not DIRECTION** (sixth numbers-said-yes
  case, distinct in kind): an inverted-green normal map carries exactly
  the same high-frequency content as a correct one - brick coursing
  rendered RECESSED with proud mortar and measured identically either
  side of the fix (2.39/1.24 vs 2.39/1.26). Right subject, right
  instrument, accurate number, backwards surface: only an eye that knows
  which way light falls can catch it. The admission gate therefore
  verifies GREEN CONVENTION alongside TC_NORMALMAP and sRGB, and
  check_textures.py runs after any fresh clone, pack re-download, or
  before any survey - it exits non-zero on a live-asset mismatch.
- **A plausible mechanism plus a matching axis is not evidence the axis
  is the right one.** The inverted brick was investigated as a STOCK
  problem (relief depth swept 2.4->1.0, roughness narrowed, with a tidy
  fabrication argument attached) when the fault was a TEXTURE property.
  Depth moved the number 7%; the actual fault moved it 0%. When sweeping
  an axis barely moves the symptom, the axis is wrong - stop arguing and
  change axes.
- **A sweep does not start without a pre-registered stop condition, and
  two nulls on one axis means STOP.** The render_smooth chase ran five
  nulls and an instrument fault; the signal was clear after two, and
  three more rounds were spent not believing a correct answer. Tuning
  tasks declare their frame budget and their stop rule before the first
  capture - open-ended sweeps are how instrument-perfecting replaces
  project-advancing without anyone deciding it should.
- **A share change is a PROMOTION on an untouched base draw, never an
  edit to the draw list.** Appending to a hashed draw list changes
  `hash %% len` and re-deals EVERY outcome downstream - the first brick
  share attempt repainted every vernacular building while hitting the
  target share exactly, invisible to every share statistic and visible
  only in frames. The shipped mechanism promotes on a separate hash
  decision and self-tests three preservation properties, including "any
  building that changes must change TO the promoted value."
- **A figure in an old log is not a measurement.** A regression worry was
  built on comparing a fresh measurement against a number REPORTED by an
  earlier run - from a capture that had not converged. Both frames were
  still on disk; re-measuring them with identical code took one command
  and dissolved the alarm. When two numbers disagree, re-measure both
  from artifacts before trusting either. (Flagging the inconsistency was
  still right - 'amplitude up, detail down' should never pass unexamined.)
- **An accurate observation without the backlog read is not a diagnosis**
  (2026-08-29). The specific shape, recorded at the request of the session
  that made it: a delivered frame showed roof trees as "bare sticks with
  dark polygon clusters" - described correctly, in the right words, and
  offered as a NOVEL look problem for someone's future attention. It was
  S16, a documented, diagnosed, already-RESOLVED fault (the live merge
  dropping masked leaf slots), recognisable in one grep of the backlog.
  The sibling rule to "a figure in an old log is not a measurement": eyes
  tell you WHAT is there, only the record tells you whether it is KNOWN.
  Before offering any observed defect as new, grep the backlog and HANDOFF
  for its symptom - the cost is seconds, and the failure mode otherwise is
  re-discovering a resolved fault as fresh work while the resolution
  (use the other bake path) goes unapplied in the very run producing the
  frame. THE OTHER HALF, added the same day when the scoping itself fell:
  **a scoping claim is a measurement too.** "The coping verdicts are
  unaffected because no masked slot is involved" was reasoned from S16's
  STATED cause; diffing the actual slot lists showed the live merge had
  also dropped MI_paint_cream - opaque, and the facade trim of the very
  elements being pronounced on. Twice in one session a confident "this is
  fine because <mechanism>" substituted for checking; both retracted. A
  claim about what a fault does or does not touch is judged like any other
  measurement: from the artifact, not from the diagnosis of record.
- **Assert the level before any destructive level action** (2026-08-29,
  demonstrated, not hypothetical): an owner-approved remove-and-resave
  script ran seconds after the owner switched the loaded level at the
  GUI; a one-line `assert world.get_name() == ...` was the only thing
  that stopped it deleting the correct actor from the correct level. The
  loaded level is user-controlled GLOBAL state that can change between
  writing a script and running it. Companion, same weekend: **"temporary"
  is not a category the guard rule recognises** — an exploratory mutation
  run outside rung's guard because it would be reverted is still a
  mutation; the rule is "anything that mutates", with no exploratory
  tier. And **a convenient accessor returning something plausible is not
  a measurement**: get_actor_bounds inflated a shed's width by its
  neighbour's extent and nearly set a framing-doctrine question on the
  wrong building; per-mesh bounds against world transforms was the real
  number. Same family as the name-keyed lookup. Related, same day, three instances of
  one failure: **the message was on screen and nothing was reading it** —
  a TOOL-ERROR string fed to a JSON parser, a single CPU sample over-read
  as "loading" while the editor sat at the project browser, and rung's
  own "[guard] ... /Game/Maps/<level>" line discarded by a grep filter
  while both sessions reasoned about the wrong level for an hour. Filters
  you write are instruments too: a grep that drops the guard line is the
  TOOL-ERROR swallow wearing your own initials.
- **THE LAPPED-SPAN FAMILY** (named 2026-08-29, on the third instance):
  a run that spans its neighbours' OUTER faces instead of butting between
  them. Parapet ring (both back corners built twice on all 548), coping
  ring (two rejected attempts before has_flank_cap), timber reveal head
  (spanning ox0-14..ox1+14, lapping its own jambs at every opening's top
  corners - 1,479 pairs, the entire recipe-shaped census tail). Three
  fixes, one sentence each time: FOUR STRIPS CUT TO LENGTH AND BUTTED,
  NOT LAPPED AT THE CORNER. Fixed three times before being seen as one
  thing; if a fourth instance exists, nothing in the current process
  finds it except another accident - so the family needs a DETECTOR (a
  census query for runs whose extent equals a neighbour pair's outer
  span), owed by the design session, not another incident report.
  DETECTOR BUILT, FAMILY CLOSED at 264 -> 0 (instances 4-5 found by
  search). INSTANCE 6 appeared 2026-08-31 in NEW code — the corner
  continuation's flank soffit starting inside the front's — and was
  caught by GATING THE VARIANT BEFORE ORDERING THE BAKE (3 pairs vs the
  base's 2, one query). A closed family stays closed only because the
  gate runs before the bake; new code is where old families are reborn.
- **THE CROWN-COLLAPSE FAMILY** (closed 2026-08-30): any course series
  driven by `(1.0 - t*t) ** 0.5` collapses to zero width at t = 1 — the
  ellipse inset equals the half-span and both edges land on the midpoint.
  Two instances (market arch, found by eye; deco3 relieving arch, found
  by a degeneracy sweep), both now capped to a keystone course, which is
  what the top of a real arch looks like anyway. The family's detector
  is a GREP for the expression: run 2026-08-30, exactly two hits, both
  guarded — closed by search, not by waiting for a third accident. When
  a fault family has a syntactic signature, grep IS the detector; a
  sweep is for families that only geometry can reveal.
- **A fresh PostProcessVolume meters AUTO by default** (2026-08-30):
  lensrig's shutter/ISO/aperture drive exposure only under MANUAL
  metering, so a light sweep against a default volume measures the
  METER CHASING THE LIGHTS, not the lights. This made a correct rig
  derivation look wrong by 250x (key fell to 1/250 of derived before it
  "looked right"); with manual metering set, the derived values landed
  in family with the passing frames on the first try, no sweep. Any new
  volume gets metering set before anything is judged through it.
- **A RENAME THAT RIDES AN && CHAIN IS NOT A RENAME** (2026-08-31): a
  control sequence's frames were lost when the rename chained after a
  toggle that failed - the rename never ran, the re-run silently
  overwrote the evidence it was to be compared against. The numbers
  survived in the transcript; the raw frames did not. Evidence moves
  FIRST, in its own command, verified - then the next experiment runs.
- **ONE CAPTURE IS ONE SAMPLE OF A DISTRIBUTION** (2026-08-31): the
  bench street measured THREE distinct brightness states (~61/69/83)
  across sixteen unchanged captures, far-canyon columns swinging 44
  levels — and a single capture nearly got reported as a scene-change
  finding. dof_matrix.py already captured twelve times per measurement
  because settling is a KNOWN property of this renderer; every new
  instrument re-learns it. Any frame that will be MEASURED (not only
  looked at) is captured as a sequence with a stated settle criterion,
  and a scene that does not reproduce blocks every measurement made on
  it — reproducibility is item zero, not a nicety. RESOLVED 2026-08-31:
  the tri-state was THE CAPTURE PATH, not the scene — every
  captureTransform render is a transient camera sampling time-amortized
  far-field GI mid-cycle. **THE CAPTURE PROTOCOL for every MEASURED
  frame: park the viewport on the pose, dwell 10 s, capture with >=1.5 s
  between frames, discard until consecutive delta < 0.5 levels, keep the
  next.** Proven: deltas 3.8 -> 0.41 monotonic, converged-run
  reproducibility 2.8 levels (the real noise floor) against 44 levels of
  phase noise. dof_matrix's twelve captures were the folk version; this
  is the criterion.
- **Prefer a WITHIN-FRAME control, and state your settle criterion**
  (2026-08-30). FOUR measurements went wrong in one day and every one was
  a BETWEEN-SUBJECT comparison in a scene that drifts: the grass alpha
  cutoff's "improvement" was its control moving; the tree-card "1.57x
  instability" vanished (0.97x) when canopy and wall were measured in the
  SAME frames; and the drift itself was live the whole time - both
  patches decayed in lockstep 0.8 -> 0.45 and did not flatten until
  frame 8, so a 4-frame settle was not settled and everything before it
  measured Lumen convergence wearing the experiment's label. Two subjects
  in one frame share their lighting, their convergence state and their
  exposure; two frames share nothing you have not proven. And "settled"
  is a CRITERION you state (delta flat across N frames), not a wait you
  guessed.
- **When every arm of a sweep agrees, doubt the instrument before
  accepting the result.** Twice a suspiciously flat table meant the
  metric was not looking at the subject - once measuring frame centre to
  judge an off-centre pier, once a measurement patch STRADDLING the
  pier's silhouette edge, where the bright-dark boundary dominated the
  residual and overstated every magnitude by double. The subject-present
  rule applies one level down: to the metric's own window, not just the
  frame. Flatness across arms was the only clue, both times.
- **Two acceptance buildings, two jobs** (2026-08-28): ACCEPT_Vernacular
  judges ARTICULATION - piers, bands, reveals, grazing light, one surface.
  ACCEPT_Modern judges MATERIAL SPREAD - the ensemble, whether the family
  coheres (it is the one mass carrying concrete, brick, two paints,
  timber, shingle, metal and glass). Standoffs are DERIVED per building
  from its own dimensions, never inherited, or two buildings frame
  different fractions of mass and their numbers stop being comparable.
- **Convert the FULL slot set of the building under test.** A partial
  conversion judges a mixture: the first per-stock pass read SMOOTHER
  because half the facade was still on the old paper. The conversion list
  is derived from the building under test, never drawn up in advance.

- **CONFIRM THE SURFACE UNDER TEST IS PRESENT AND VISIBLE IN THE FRAME
  before trusting the frame.** Proven four separate ways in one arc: a
  flat panel showing a material in a condition no city surface is seen
  in; an acceptance building whose relevant slots were all one plaster,
  so a seven-map change looked like nothing; a standoff photographing the
  BACK of another row; and a building that DECLARES a stock without
  wearing it (deco3 declares a brick wall; the district palette overrides
  it). Every one produced a confident, coherent, wrong reading with fine
  numbers - the subject was wrong, not the measurement. A FIFTH instance
  arrived in the same report that proposed the rule, recorded at its
  author's own insistence: two buildings were sampled for a marked
  material, both happened to miss it, and 'brick is effectively unused'
  was generalized to the city - when brick walls one building in nine by
  active palette rotation. The correct move is to FIND a building that
  HAS the subject first, never to infer absence from a sample that lacks
  it. A further instance upgraded the stakes from wrong MEASUREMENT to
  wrong STOP: non-existence was asserted from the wrong level, the wrong
  actor prefix, and a parameterised builder's missing filename - and a
  decided owner item was nearly cancelled on it. An ABSENCE claim demands
  the rule at full strength: find the thing first, in the level where it
  lives, by the name it actually has, through the mechanism that actually
  builds it. Corollary: the
  acceptance rig is ONE BUILDING PER STOCK UNDER TEST, chosen because its
  WALL is the material being judged - never the building listing the most
  stocks (ACCEPT_Modern lists seven and shows two at any size).

## The bake policy (owner-adopted 2026-08-30)

Answering the owner's own question after four waves in two days: yes, it
was a rebake treadmill — fix a mechanism, bake, census, find the next,
bake again. Every mechanism that week was found OFFLINE in sink data in
seconds; not one was found in a baked mesh. Baking is needed to SEE a
fix, never to FIND one. Therefore:

- **Fixes batch offline**, census after each. Per-mechanism offline
  proofs (union rasters, box counts, known-answer checks) stay MANDATORY
  — a batched look confirms, it does not discover.
- **Bake only on a pre-registered trigger**, whichever lands first:
  (a) a LOOK-RISKY mechanism — any change altering silhouette or
      material on a shipped surface (fin clamp, proud quoin: yes; a
      coplanar trim inside a wall: no);
  (b) the changed-model set exceeds 150;
  (c) any acceptance, precast confirmation, or reader event approaches.
- **The staleness ledger is first-class**: HANDOFF carries one line,
  "MESHES CURRENT THROUGH <commit>", maintained per wave, and the hard
  rule beside it: **no acceptance or reader frames while stale** — the
  S16 shape (evidence that looks current) is the hole this closes.
  **Scope is decided by what the change reaches, not by what list the
  subject appears on** (2026-08-30): the works sheds were ruled shootable
  while the catalogue sat six commits stale — but "not in the 548" was
  not the licensing claim, because the sheds are generator-built too. The
  licensing claim was MEASURED: build_works byte-identical across the
  stale span, sharing no helper with any changed builder (ast-level diff,
  no editor needed). A subject-list argument would have been right by
  accident and wrong the next time a shared helper moved.
- **Batched looks ship with a named checklist** (mechanism, model, where
  to look); a failed look bake-bisects via checkpoint waves.
- **The regression ledger populates as a side effect** of whatever wave
  comes next — never as a reason to bake.
- **EVERY WAVE IS FOLLOWED BY AN S17 SWEEP before any frame is taken
  anywhere** (added 2026-08-30, after the full wave nulled 225 of 228
  placed references in Sandbox_Bench — essentially every placed actor in
  the bench, caught only because the check ran before framing).
  Rebaking nulls placed actor references; this is a POST-WAVE REQUIRED
  STEP, not a thing to remember. The repair depends on a level
  inventory (label -> mesh mapping), which is therefore LOAD-BEARING
  INFRASTRUCTURE: regenerated as part of every wave, never maintained
  by hand.
- The treadmill's real cost is EDITOR-WINDOW SERIALIZATION AND ATTENTION
  (16 min per 156 models — compute is not the scarce resource; the one
  writer is).

## Sequencing (owner-approved 2026-08-27)

1. Width sweep (donor-bounds table first) → the honest catalogue number.
2. Ladder decisions: fix or retract dishonest widths. Expect the catalogue
   to get smaller before it gets bigger; that is health.
3. First polish wave on the honest catalogue.
4. Archetype-aware gate lands (built in parallel, integrates at a design
   pause point) — BEFORE the first industrial or agricultural building.
5. New archetypes, each declaring its definition of good before geometry.
6. District placer, sized to the real variety budget.

## Commit discipline

- **The WIP bar: "green and coherent on its own", not "finished
  feature"** (agreed between lanes, 2026-08-30). An increment commits
  when it passes its own tests and leaves every existing contract
  byte-intact (the depth-axis start: grammar declared, self-test
  extended, zero bakes, all 548 names identical to the ledger keys) —
  even though the feature it enables is not built. Whoever knows an
  increment fails that bar says so BEFORE staging, not after.
- **Measuring a PNG leaves a 17.6 MB sibling** (2026-08-30): img.load
  deliberately caches a BMP beside every PNG it measures, unbounded, in
  whatever directory the PNG lives in — a 30-frame sweep costs ~half a
  gigabyte in Saved/. Now gitignored (*.png.bmp) with the reason; the
  cache is regenerable by construction (0 orphans found at cleanup).
  Disk item, not a bug — but Saved/ is the EVIDENCE directory, and
  DISK_AUDIT exists because this shape has bitten before.

Every design-session pause point ends with a commit request to the
coordinator. The project has now three times accumulated days of
unversioned work; and the coordinator's own Uniblocks sweep-in (2026-08-27)
adds the companion rule: **never `git add -A` — enumerate what you stage.**
