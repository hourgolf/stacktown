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
- **A figure in an old log is not a measurement.** A regression worry was
  built on comparing a fresh measurement against a number REPORTED by an
  earlier run - from a capture that had not converged. Both frames were
  still on disk; re-measuring them with identical code took one command
  and dissolved the alarm. When two numbers disagree, re-measure both
  from artifacts before trusting either. (Flagging the inconsistency was
  still right - 'amplitude up, detail down' should never pass unexamined.)
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
  it. Corollary: the
  acceptance rig is ONE BUILDING PER STOCK UNDER TEST, chosen because its
  WALL is the material being judged - never the building listing the most
  stocks (ACCEPT_Modern lists seven and shows two at any size).

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

Every design-session pause point ends with a commit request to the
coordinator. The project has now three times accumulated days of
unversioned work; and the coordinator's own Uniblocks sweep-in (2026-08-27)
adds the companion rule: **never `git add -A` — enumerate what you stage.**
