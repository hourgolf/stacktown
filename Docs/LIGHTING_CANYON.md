# Lighting a street canyon — two mechanisms, measured

**Date:** 2026-08-31 · **Maps:** `Sandbox_Bench`, `TestCity` · **Status:** bench fixed
and saved; `citylight.py` fixed and verified in `TestCity`

Cold read #2 called the street *flat* and named LIGHTING as a tell. This is what
"flat" turned out to be. Neither cause was the one under investigation at the time
("is the sun standing in for a lamp?"), and both were found by measurement rather
than by looking.

## The instrument

`Tools/measure/falloff.py`. In a street frame the carriageway is the only surface
running continuously from camera to vanishing point in **one material**, so its
brightness profile down the image is the light's falloff with albedo held constant.
Facades cannot do this — they change colour every parcel.

`near/far > 1` is a light with real falloff. **`near/far < 1` is impossible for any
light with falloff**, and means the key is not reaching the road at all.

Caveat on the record: the far band is small and dark, so its relative variance is
high. Two converged captures of the same scene read 3.34x and 3.91x. The stops
figure is good to about ±0.2; do not tune against the third digit.

## Mechanism 1 — the key stood outside the canyon

The bench canyon is **2,096 uu** wide between facade rows with a median roofline of
**2,541**. `BLOCK_Key` stood **9,147 uu to the south at pitch −34** — outside it. The
south row occluded the key off the carriageway completely: the passing frame carries
no cast shadow anywhere on the road.

| | near/far | |
|---|---|---|
| key alone | 3.56x | falls off toward the far end |
| fill alone | 0.31x | rises toward the far end (it sits at x=18,678) |
| **combined** | **1.25x** | a quarter stop across 15,000 uu |

The fill was positioned to lift exactly where the key fell away. They cancelled.

**Fix:** put the key where a modelmaker's lamp goes — above the canyon, behind the
camera, raking along the street's length. (−600, −23544, 5657), pitch −45, yaw 8,
standoff 8,000 from an aim point on the road.

## Mechanism 2 — the skylight was laundering the sun

`LIGHT_Sky` is `SLS_CAPTURED_SCENE` with `real_time_capture` off: it replays a baked
cubemap. That cubemap was captured **while the sun was at 430**. Zeroing `LIGHT_Sun`
therefore removed the *direct* sun and left its energy in the scene, replayed
omnidirectionally with every trace of direction stripped out.

This is why the "blockrig as key" test read warm but flat — the dominant light in
that frame was still the sun, just diffused.

| | sky 10 → 0 |
|---|---|
| cubemap still hot | frame moved **15 levels** (83.12 → 67.98) |
| cubemap recaptured dark | sky **100 vs 0** moved it **0.13 levels** — inert |

**Fix:** `SLS_SPECIFIED_CUBEMAP` on `GrayLightTextureCube`, tinted cool — even
ambient from every direction, no sky dome, no atmosphere dependency, and an honest
intensity knob. `light_rig.py` already solved this for the night rig; the lesson was
on disk and unread.

Swept on the bench, intensity is now a real shadow-lift: crush **4.87% → 1.38%** from
0.5 to 12 while the road falloff held. **12 is the knee** — 24 buys 0.27% more crush
for 0.29x of falloff.

## Result

| | mean | sd | crushed | blown | road |
|---|---|---|---|---|---|
| baseline (sun as key) | 70.22 | 45.72 | 0.18% | 0.00% | 0.71x (backwards) |
| blockrig as key, far | 76.16 | 44.56 | 0.06% | 0.00% | 0.86x (backwards) |
| **close key + fixed sky** | **68.68** | **53.64** | **1.38%** | **0.00%** | **3.3–3.9x** |

## What this does NOT cover

- **It is a street fix, not a bench fix.** The same change dropped `b70_mid_judge` by
  71 levels and `tell_judge` by 55 — those subjects were living entirely on the
  skylight and have no key of their own. Same diagnosis, separate work.
- **The warm cast grew.** R−B went +17.90 → +31.88 against baseline. The owner called
  the warmth desirable, so it is left; but it is nearly double the baseline's cast and
  the key's 4,500 K is the knob if that is more than intended.
- **The convergence protocol does not hold in `TestCity`.** See below.

## `citylight.py`, fixed on the same evidence

1. **Street keys per corridor** — one lamp above each, transplanted from the bench
   reference (5,733,620 lm at 8,000 uu, emitter 3,751 × 2,453, 4,500 K) by the file's
   own inverse-square rule, and auto-raised when 45° would sit below the p90 roofline.
   `CITY_Key` alone could not do this: at 25,988 uu and 35° elevation, any facade over
   **1,812 uu shadows the whole carriageway** — 33% of the catalogue options that fit
   TestCity's lots.
2. **`CITY_Fill` tilt −5.4° → −30°.** At 5.4° the horizontal reach is height × 10.58,
   so a 300 uu parapet alone shadows more than the full corridor. The measured board
   angle is correct for one building on a 2,900 × 2,400 board and does not transplant.
3. **`CITY_Sky` configured** — it was a bare `SkyLight` with only mobility set, so it
   inherited `SLS_CAPTURED_SCENE`, was spawned *before* `CITY_Atmosphere`, and was
   never recaptured. This also repairs the `OUTDOOR` ladder: `'sun_sky'` returns before
   the atmosphere exists, so that mode could never have differed from `'sun'`.

## Verified in `TestCity`

Arterial frame `(-6800, 0, 260)` pitch 2 — the existing `rig_street` framing, reused.
Full numbers in `Saved/TestCity/rigfix/RESULTS.json`.

| | mean | sd | crushed | blown | road |
|---|---|---|---|---|---|
| before (rig at 17f552e) | 68.32 | 41.90 | 0.14% | 0.00% | 1.15x (+0.20) |
| after, sun on | 96.83 | 49.38 | 0.12% | 0.00% | **2.05x (+1.03)** |
| after, sun off | 81.75 | 42.81 | 0.14% | 0.00% | **2.44x (+1.29)** |

The roofline-clearance check earned its place: TestCity's **measured** p90 roofline is
4,147, not the 3,480 estimated on paper, so `CITY_StreetKey_C` raised itself 45° →
61.3° rather than sitting under the parapets it was meant to rake over.

Two limits on this evidence, both stated rather than smoothed over:

- **Nothing converged.** All three runs hit the 26-frame cap at final deltas
  0.57–0.68 against a 0.5 criterion. The settle protocol proved on the bench does not
  hold in `TestCity`, so these numbers are approximate and the map needs its own
  settle criterion before anything is tuned against them.
- **Not exposure-matched.** Two street lamps stacked on the transplanted sun add 28
  levels. Nothing is blown, but the rig wants re-metering before this is a fair *look*
  comparison rather than a falloff measurement.

`TestCity` was **not saved** — `citylight.py` owns the rig and is idempotent, so the
script is the source of truth and re-running it rebuilds the lighting exactly.

## What the verification frame actually showed

The arterial frame is dominated by a blank windowless wall: `TC_Bld_SW3_vernacular_t5`
presenting **847 uu of bare party flank, 1,996 uu tall**, filling the frame from centre
to right edge. Corners bake at `DEPTH_CORNER = 1500` (1,572–1,628 measured) against
neighbours at 781–924, so **every corner stands proud of the building behind it** and
shows that flank down the street.

**This frame cannot judge lighting** — whatever the rig does, half the image is an
untextured wall. The lighting result above is real and measured, but the visible drift
in that frame is geometry. Recorded in `Docs/DEPTH_CORNER_DECISIONS.md`; the fix is an
owner/coordinator call, not actioned.

## Scale

**One lamp per corridor is O(streets).** For a two-street test city that is two lamps
and it mirrors how a diorama is lit. It is *not* proposed as the answer at full city
scale — that question is open and belongs to the coordinator.
