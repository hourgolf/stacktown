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

**These figures replace an earlier, uncontrolled pair.** The first run compared a *stale
rig left in the map* against a fresh run of the fixed code, and both frames contained
four stray actors that were themselves contributing contrast. Corrected: both runs
below are fresh builds of their own code, with the strays removed and no leftover lamps.

| | mean | sd | road |
|---|---|---|---|
| before (rig at `43b3f7c^`) | 87.18 | 43.42 | 1.13x (+0.17) |
| after (rig at `43b3f7c`) | 111.20 | 51.74 | **2.35x (+1.23)** |

The roofline-clearance check earned its place: TestCity's **measured** p90 roofline is
4,147, not the 3,480 estimated on paper, so `CITY_StreetKey_C` raised itself 45° →
61.3° rather than sitting under the parapets it was meant to rake over.

### Limits on this evidence

- **Nothing converges.** Every run hit the frame cap at final deltas 0.26–0.68 against a
  0.5 criterion. The settle protocol proved on the bench does not hold in `TestCity`.
- **Absolute levels are not trustworthy here.** Two nominally identical rebuilds of the
  fixed rig measured mean 95.48 and 111.20 — **16 levels apart**. The falloff RATIO was
  stable across the same pair (2.41x and 2.35x), which is an argument for the ratio as
  the instrument and against tuning anything in this map against absolute level.
- **Not exposure-matched.** Two street lamps stacked on the transplanted sun add light;
  the rig wants re-metering before this is a fair *look* comparison.

`TestCity` was **not saved** — `citylight.py` owns the rig and is idempotent, so the
script is the source of truth and re-running it rebuilds the lighting exactly.

## The wall in the verification frame was not what I said it was

The first pass at this frame blamed a blank party flank on the protruding corner. That
was wrong. `step_elevations.freestanding()` already treats every face of a catalogue
model — *"a blind wall is a visible bug the moment a model lands on a corner"* — and a
close capture of `SW3`'s west flank shows piers, band courses, recessed panels and
mullions, all present.

The wall was **four stray `ELEV_T` actors** standing at world origin, which in `TestCity`
is the middle of the junction: 1,844 × 1,638 × 1,608, three of them exact duplicates of
each other. `step_elevations.run()` wipes the `ELEV` family before building precisely to
stop this, but the wipe lives in `run()` and does not fire when `flank()` is called
directly. Destroying them cleared the frame.

The row assignment is what produced the wrong answer: UE is left-handed, so looking
along +x, **+y is frame RIGHT**. The blamed corner sits at −y. Project a suspect actor's
bounds into the frame and check the sign before naming it. Recorded in
`Docs/DEPTH_CORNER_DECISIONS.md`.

## Scale

**One lamp per corridor is O(streets).** For a two-street test city that is two lamps
and it mirrors how a diorama is lit. It is *not* proposed as the answer at full city
scale — that question is open and belongs to the coordinator.

## Postscript: the settle protocol was wrong, and the curve says how

Clearing ten stale bake-staging actors from `Sandbox_Bench` required a level
reload, and the reference frame came back 10 levels darker with **12.99% crushed
against the committed 1.38%**. The rig was intact — sun 0, `BLOCK_Key` at
(−600, −23544, 5657), the specified grey cubemap at 12, all verified by readback —
so the difference was Lumen rebuilding from cold.

Sampling one parked frame every 10s for four minutes:

```
t=15s   mean 64.91  sd 53.93  crushed 2.82%
t=252s  mean 67.47  sd 53.55  crushed 1.44%   still climbing +0.07/sample
```

**Every consecutive delta across that entire run was 0.07–0.19 levels** — under
any sane floor, from the first sample — while the frame still had 2.5 levels and
1.4% of crushed pixels to go. The protocol this session established ("keep when
consecutive delta < 0.5") declares victory at t=15s. *The frame stopped moving*
and *the frame is moving too slowly to notice between two samples* are not the
same statement.

The committed bench numbers are the settled ones — the curve asymptotes toward
68.68 / 1.38% — because they were taken after a long live session with GI fully
accumulated. What was wrong was the criterion, not those figures.

**This also explains the TestCity instability.** Two identical rebuilds measured
mean 95.48 and 111.20, sixteen levels apart, while their falloff ratios agreed to
0.06 (2.41x vs 2.35x). A uniform ramp cancels in a ratio and does not in a level.
That is not "TestCity is unstable"; it is two captures taken at different points
on the same ramp.

**Fixed in `Tools/measure/settle.py`**: `drifting()` compares against a frame
`BASELINE_S` (60s) old rather than the immediate predecessor, and `settled()`
takes `drift_test=True` for cold starts. It defaults False so `ab.py`'s
same-session A/Bs — where both sides ride the same ramp and it cancels — are
unaffected. The self-test synthesises the measured ramp and asserts the old
criterion cannot see it.
