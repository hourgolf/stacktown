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
