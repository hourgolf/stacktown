# Stage 2 — the block, scale budget

Derived 2026-08-23, before any geometry. Every later number depends on this, and
getting it wrong is how a block ends up looking like a model of a model.

Owner decisions: four buildings from a shared kit, the Stage 1 building reused
as one of them; one board with the studio backdrop, as Stage 1.

## The block

    four lots, party-walled   1080 (Stage 1) + 860 + 1240 + 980, 40 uu joints
    frontage                  4280 uu (42.8 m)
    board width               5222 uu

## The two ranges it must hold at

| framing | distance | frame width | 0.4% threshold |
|---|---|---|---|
| block hero | 11,168 uu (112 m) | 5,744 uu | **23.0 uu (230 mm)** |
| approach | 3,500 uu | 1,800 uu | 7.2 uu (72 mm) |
| player zoom | 900 uu | 463 uu | 1.9 uu (19 mm) |

## What carries the block hero — 230 mm threshold

| feature | size | margin |
|---|---|---|
| height step between buildings | 3000 mm | 13.1x |
| canopy projection | 2200 mm | 9.6x |
| setback / plane break | 900 mm | 3.9x |
| roof unit | 800 mm | 3.5x |
| floor band offset | 680 mm | 3.0x |
| gap between buildings | 400 mm | 1.7x |
| cornice depth | 300 mm | 1.3x |
| window recess | 250 mm | 1.1x — marginal, do not rely on it |

**Design consequence.** At the block hero the reveal is carried almost entirely
by silhouette and plane breaks between buildings. Height variation is the single
strongest tool available and it is free. Window recess, which was the whole
subject of Stage 0, is at 1.1x and can no longer be relied on for anything.

## Stage 1 surface work at the block hero — all of it invisible

| feature | size | margin |
|---|---|---|
| glue bead section | 120 mm | 0.52x |
| panel seam width | 60 mm | 0.26x |
| mullion width | 50 mm | 0.22x |
| edge chamfer | 40 mm | 0.17x |
| dent depth | 20 mm | 0.09x |

Not one of them reaches threshold; the dent is an order of magnitude under. This
is expected and it is recorded so its absence is never read as a regression. All
of it still earns its keep at the player zoom, where the threshold is 19 mm and
every item above clears it by 2-6x.

**So the block is not "Stage 1 five times".** The two ranges want opposite things
and both have to be paid for separately:

    block hero    mass, silhouette, plane breaks, height variation
    player zoom   the Stage 1 surface toolkit, unchanged, on facades only

## Rig, to be re-derived not reused

Stage 1 lit a 4200 uu rig at 1.58M lm. The block hero sits at 11,168 uu. If the
rig scales with the subject, inverse square from the measured baseline
(300k lm at 1830 uu) puts the key near:

    300,000 x (9000/1830)^2  = 7.26M lm at a 9000 uu rig distance

Do not carry the Stage 1 intensity across. Confirm attenuation radius exceeds
the throw before judging anything dark.
