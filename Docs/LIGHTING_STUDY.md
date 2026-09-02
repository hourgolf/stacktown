# Why it still reads as a rendering — a measured lighting study

**Status: FIRST MECHANISM SHOT AND ELIMINATED — but not the way the study
expected. The board key turned out to be INERT. See "The null result" below,
which supersedes this document's own first-ranked hypothesis.**

**Original status: STUDY DESIGN. Nothing changed, no pairs shot yet.** The owner's
note is the whole brief: *"the lighting in the reference feels more natural
and it doesn't look like a rendering (it is)."*

I refused to guess at this for several exchanges, because reaching for
plausible-sounding knobs is how the crossed normals survived three boards.
So it starts with measurement.

## The measurement, and it inverts the obvious guess

Same instrument on both, whole-frame:

| | B1 (a photograph of a real model) | our 12x9 oblique (a render) |
|---|---|---|
| local contrast, gradient p90 | **92** | **12** |
| gradient p99 | 231 | 63 |
| shadow lift, p05/p50 | 0.337 — deep | 0.500 — filled |
| tonal spread, p95-p05 | 190 | 147 |
| histogram shape | **bimodal** — a dark mass AND a bright mass at 160-207 | **unimodal** — 40% of all pixels in one 16-level bucket |

**The intuitive diagnosis is that a render looks harsh. Ours measures the
opposite: FLAT and FILLED.** Local contrast is nearly eight times lower than
the reference. There is no bright population at all where B1 has an entire
second peak. Shadows are lifted, not crushed.

"Looks like a rendering" here means *evenly lit*, not *over-lit*.

## Which indicts a decision this lane made on purpose

`board_light.py` places a 4000 x 2600 rect light and argues, in its own
comment, that "softness comes from source SIZE relative to subject... a 4 m x
2.6 m rectangle at this distance is a studio window onto a 68 m board."

That is correct optics and it is working exactly as designed. **The design was
wrong for the subject.** B1 is not a studio product shot with a big soft
window. It is a model on a table under a harder source: deep shadows, crisp
arris shadows, and a bright board bouncing light back. A large soft source is
precisely how you erase local contrast, and local contrast is the single
biggest measured gap.

## Candidate mechanisms, ranked by how much of the gap they could close

Each is one variable, and each has a measurable prediction. A mechanism whose
prediction fails is eliminated, not re-tuned.

1. **SOURCE SIZE (key).** 4000x2600 is enormous relative to a 900 uu block.
   Shrinking it hardens every shadow edge.
   *Predicts:* gradient p90 rises sharply; shadow lift falls. Biggest
   expected effect, and the one contradicting an existing decision — so it is
   first.
2. **FILL / SKYLIGHT.** `CITY_Sky` at 12 lifts every shadow uniformly. Less
   ambient deepens shadows without touching the key.
   *Predicts:* p05/p50 falls toward 0.34; p50 barely moves.
3. **KEY INTENSITY vs AMBIENT RATIO.** Not the same as (2): more key with the
   same ambient raises the bright population B1 has and we lack.
   *Predicts:* a second histogram peak appears above 160; p95 rises from 175
   toward 221.
4. **TONEMAPPER / CONTRAST CURVE.** `LOOK_Post` runs manual exposure with
   film-curve defaults untouched. A curve change moves everything at once and
   is therefore LAST — it is the knob most likely to flatter a bad frame
   without fixing it.

## Deliberately NOT on the list

- **Palette or tone.** D13 settled the value ladder against B1 and it matches
  (+45% vs +50% roads, -55% vs -58% darks). This is not a material problem.
- **Anything about grain.** D16 and the figure work are separate axes.
- **More lights.** A rig with five sources is not more natural, it is more
  managed. B1 looks like ONE source and a bright board.

## Protocol

- **One variable per pair**, the whole rig otherwise frozen, same framing,
  same lens state — `ue.tool` now refuses a capture whose lens state is
  undeclared, so exposure cannot drift underneath a lighting pair.
- **Shoot at the OBLIQUE framing** — the main view the game is played from,
  not the survey and not a study wall. Acceptance happens on the frame the
  player sees.
- **Measure the same five numbers each time** and record them beside the
  frame, so a pair that looks better and measures worse is visible as such.
- **The owner's eye settles it.** The numbers say which mechanism moved what;
  they do not say which frame is right. B1's numbers are a target to
  approach, not a score to maximise — a frame that hit 92 gradient and looked
  like a photocopy would have failed.

## The honest caveat

B1 is a photograph. It carries lens character, sensor noise, real bounce, and
the imperfection of a physical object under real light. Some of the measured
gap is not lightable at all — it is the difference between a photograph and a
render, and closing the last of it may belong to the lens and grain work
rather than to the lighting rig. This study should find out how much of the
gap the lights own before anyone reaches for film grain.


---

# The null result, 2026-09-02 — the study aimed at the wrong object

The source-size ladder ran exposure-matched, four rungs, source AREA varied
100x from the approved 4000x2600 down to 400x260:

| source | mean | grad p90 | lift | spread |
|---|---|---|---|---|
| 4000 x 2600 (approved control) | 75.4 | 11 | 0.509 | 147 |
| 2000 x 1300 | 75.6 | 11 | 0.500 | 147 |
| 1000 x 650 | 75.6 | 11 | 0.500 | 147 |
| 400 x 260 | 75.7 | 11 | 0.500 | 147 |

**Nothing moved.** Not the local contrast the study exists to raise, not the
shadow lift, not the spread. A hundredfold change in emitting area produced a
frame that measures identical to three decimal places on lift.

## The null control that explains it

Rather than tune, switch the light OFF:

| | mean | grad p90 | lift | spread |
|---|---|---|---|---|
| LIGHT_BoardKey ON (as approved) | 75.8 | 11 | 0.500 | 148 |
| LIGHT_BoardKey **OFF** | 75.8 | 11 | 0.500 | 148 |

**0.06 luma levels.** The board key contributes nothing to this frame and
never has.

## What that means, stated plainly

- **The soft-source decision was never in effect.** `board_light.py` argues
  softness should come from a large source, the owner approved it at the
  regroup, and it has been inert since the day it was placed. Every "soft
  key" frame the owner has judged was lit by something else.
- **This study's first-ranked mechanism is eliminated for the wrong reason.**
  Source size is not disproved; it was never tested, because the instrument
  had no authority over the subject.
- **The cause is almost certainly the intensity units.** The board key sits at
  intensity **26**. The city rig's own rect lights measure **2.0 x 10^7** and
  **1.9 x 10^7** with a 67,568 uu radius that reaches the board from 33,000
  uu away. The board is lit by the CITY rig plus CITY_Sun (430) and CITY_Sky
  (12) - never by its own key.

## The family this belongs to

This is the same shape as the crossed normals and the f/22 exposure leak: a
mechanism that was reasoned about, built, approved and discussed for days
while contributing nothing measurable. The pattern each time is that nobody
asked the null question - **does this thing do anything at all?** - because
the thing was plausible and present.

The cheap guard, and it should precede every future look study: **before
tuning a parameter, switch its owner OFF and confirm the frame changes.** One
capture. It would have saved this study its first mechanism, and it would
have saved board_light.py from being written against a scene it could not
reach.

## What the corrected study must do first

Establish a rig that actually lights the board before comparing anything about
it. That is a decision for the owner, not a fix to apply quietly:

1. **Raise the board key into the scene's units** (26 -> order 10^7) so the
   board has its own key, and re-run the source-size ladder against a light
   that is doing the work.
2. **Or accept that the city rig lights the board**, and study THAT - in
   which case the variables are CITY_Key/CITY_Fill/CITY_Sun, which are SHARED
   SCENE STATE belonging to another lane and not mine to vary.

Option 1 is this lane's to do. Option 2 is not, and the boundary matters more
than the study.


---

# The census, 2026-09-02 — which lights actually light the board

D18 gave this lane TestCity's rig. The null-first guard says find out what has
authority before tuning anything, so: every light switched off in turn, with a
fresh all-on control immediately before AND after each.

| light | intensity | contribution (luma levels) | |
|---|---|---|---|
| **CITY_Sun** | 430 | **+23.63** | **DOMINANT** |
| CITY_Key | 2.05e7 | +8.14 | contributes |
| CITY_Fill | 1.90e7 | +2.17 | contributes |
| CITY_Sky | 12 | +0.70 | trace, but real |
| CITY_StreetKey_A | 8.22e6 | +0.04 | **INERT** |
| CITY_StreetKey_C | 2.51e6 | -0.00 | **INERT** |

Noise floor, four identical captures: **0.16 levels**. Every figure above
except the two street keys clears it comfortably.

## The finding: intensity numbers do not rank these lights

`CITY_Sun` carries an intensity of **430** and does **three times the work** of
`CITY_Key` at **2.05e7** — a number forty-seven thousand times larger.

The reason is that a DIRECTIONAL light does not attenuate with distance. The
rect lights are aimed at the city at the origin and the board sits ~33,000 uu
away, so their enormous values buy a fraction of what they appear to. The sun
does not care where the board is.

**Anyone tuning this rig by reading intensities would tune the wrong lights.**

## Two more inert lights — WRONG, SEE THE PLAY-BOARD CENSUS BELOW

`CITY_StreetKey_A` (8.22e6) and `CITY_StreetKey_C` (2.51e6) contribute
**0.04 and 0.00 levels** — indistinguishable from nothing against a 0.16 floor.
They are close keys aimed into the city's street canyon, and a key that cannot
clear a 2,096 uu canyon certainly cannot reach a board 33,000 uu away.

With `LIGHT_BoardKey` retired that is **three lights in one scene carrying real
intensity values and lighting nothing.** The null-first guard is not a nicety
here; it is the difference between tuning and theatre.

## What the first census got wrong, and how it was caught

The first pass reported `CITY_Sky` and both street keys as NEGATIVE
contributors — the frame got brighter when they were switched off. **That is
impossible for an additive light**, and the impossibility is what exposed it:
the scene was still converging after 476 actors had just been placed, so the
baseline rose underneath the whole census and contaminated every delta.

The fix was an A-B-A design: a fresh control before and after each light, so
drift cancels rather than accumulates. Measured drift per pair afterwards was
0.04-0.66 levels.

**The noise floor made this visible.** Without it, a 1.3-level artefact and a
1.3-level effect are the same number.

## The study re-aims

The original first mechanism was "source size" on a rect light. On the real
instrument the equivalent lever is different:

1. **`CITY_Sun`'s source angle.** A directional light's shadow softness is its
   angular diameter, and that is the true analogue of source size. Our problem
   is too little local contrast; a smaller angle hardens every shadow edge on
   the light that is doing 70% of the work.
2. **Sun-to-fill ratio.** `CITY_Key` and `CITY_Fill` together contribute ~10
   levels of largely directionless fill. Reducing them deepens shadows without
   touching the key light.
3. **The two inert street keys** should be removed or re-aimed, not tuned —
   they are `LIGHT_BoardKey`'s problem repeated twice.
4. Tonemapper last, as before.


---

# The play-board census — "inert" was a property of the FRAME, not the light

The census above was shot on the 12x9 density board at its staging spot,
33,000 uu from the origin. `CITY_StreetKey_A` and `_C` are aimed into the
ORIGIN city's street canyon — the pinned 14-lot board the owner actually
plays on. Calling them dead from a frame 33,000 uu away was a conclusion that
outran the conditions it was measured under.

Same A-B-A census, same lights, from the play framing (`cam_city.py`'s
three-quarter aerial down the pinned city's street):

| light | density board | **play board** | |
|---|---|---|---|
| CITY_Sun | +23.63 | **+28.37** | dominant on both |
| **CITY_StreetKey_C** | **-0.00** | **+9.39** | **second biggest here** |
| CITY_Key | +8.14 | +6.35 | |
| **CITY_StreetKey_A** | **+0.04** | **+3.84** | |
| CITY_Fill | +2.17 | +2.91 | |
| CITY_Sky | +0.70 | +1.11 | |

**`CITY_StreetKey_C` goes from exactly zero to the second most important light
in the scene, purely by changing where the camera stands.** Removing the two
street keys as "dead" would have gutted the lighting of the board the game is
played on.

## The receipt, from the dressed play board

Measured later the same day, on the play board WITH BUILDINGS ON IT, from the
boom's own first-boot pose:

| light | my "inert" reading | **the truth, dressed play board** |
|---|---|---|
| CITY_StreetKey_A | +0.04 | **+10.34** |
| CITY_StreetKey_C | -0.00 | **+8.62** |

**They are the second and third most important lights on the board the game is
played on.** I called them dead twice - once from a frame 33,000 uu away, once
from an empty plaza - and both times the number was honestly measured and
completely wrong about the world.

Had they been removed the play board would have lost roughly a fifth of its
light, and nothing would have said why: nobody re-lights a board they assume
was always like that.

## The correction, stated as a rule

**Inertness is a property of a LIGHT AND A FRAME, never of a light alone.**
The null-first guard says switch the owner off and confirm the frame changes —
and "the frame" is load-bearing in that sentence. A null result licenses a
conclusion about the frame it was measured in and nothing wider.

This is the same shape as the session's other failures — a conclusion that
outran its conditions — and it is the one that would have caused real damage,
because the others cost measurements and this one would have cost the owner's
lighting.

## What survives, and what it means for the study

- **`CITY_Sun` dominates BOTH boards** (+23.6 and +28.4). It is the only
  finding that generalises, and it is the study's first mechanism.
- **`LIGHT_BoardKey` remains genuinely dead** — 0.06 levels on the density
  board, and it is nowhere near the play board either. Its retirement stands.
- **The street keys stay.** They are load-bearing where they were aimed.
- **The two boards are different lighting problems.** The play board sits at
  mean 133; the density board at 77. Any tuning must name its subject.

**The study therefore needs the owner to say which board they judge**, or to
judge both. The re-aim (sun source angle, then sun-to-fill, then tonemapper)
is unchanged — but "sun-to-fill" now means something different on each board,
because the fill is a different set of lights in each.


---

# Mechanisms 1 and 2 eliminated — and the metric was partly the instrument

## The two ladders, density board, subject present and asserted

**Mechanism 1, sun source angle.** 2.0 deg down to 0.05 - forty times - with
476 buildings in frame:

| angle | mean | grad p90 | lift | spread |
|---|---|---|---|---|
| 2.0000 | 75.16 | 12 | 0.509 | 147 |
| 0.5357 (the real sun) | 75.80 | 12 | 0.518 | 146 |
| 0.2000 | 76.00 | 12 | 0.518 | 147 |
| 0.0500 | 76.19 | 12 | 0.518 | 147 |

**Eliminated.** Local contrast does not move at all.

**Mechanism 2, sun-to-fill ratio.** Fill scaled from full to zero, exposure
held by ISO so the lights keep one variable, baseline read from file:

| fill | ISO | mean | grad p90 | lift | spread |
|---|---|---|---|---|---|
| 1.00 | 800 | 76.42 | 12 | 0.536 | 146 |
| 0.50 | 850 | 74.68 | 11 | 0.483 | 136 |
| 0.25 | 919 | 75.22 | 11 | 0.467 | 131 |
| 0.00 | 1009 | 74.70 | 11 | **0.397** | **126** |

**Half-eliminated, and it costs something.** Killing all fill moves shadow
lift 0.536 -> 0.397, genuinely toward B1's 0.337. But local contrast does not
move, and tonal SPREAD gets worse - 146 -> 126, away from B1's 190. Fill is
holding the frame's range open while lifting its shadows; removing it trades
one number for another.

## THE METRIC WAS PARTLY THE INSTRUMENT

`grad_p90` is a PER-PIXEL gradient, and it is therefore resolution-dependent:
the same luminance step spans fewer pixels in a smaller image, so the same
scene measures a larger gradient. **B1 is 768 x 768. Our captures are
2802 x 1570.** The two were never comparable.

| frame | size | grad p90 |
|---|---|---|
| our frame, native | 2802x1570 | 12 |
| our frame, resampled | 1401x785 | 19 |
| our frame, resampled | 768x430 | **28** |
| **B1 reference** | 768x768 | **94** |

**The gap is ~3x, not ~8x.** It is still real and still worth chasing - but a
large part of what two ladders were aimed at was an artefact of comparing
statistics across resolutions.

This is the same family again, at one remove: the earlier failures were
mechanisms with no authority over the subject; this is a MEASUREMENT with no
authority over the comparison. **Ask the null question of the instrument too:
does this number mean the same thing on both sides?**

## Where that leaves the study

- Mechanism 1 eliminated outright.
- Mechanism 2 deepens shadows, buys no contrast, costs range.
- **All future comparisons against B1 must be made at matched resolution.**
  Every number in this document above this section understates our frame.
- The remaining 3x is smaller than a lighting rig plausibly explains on its
  own, which strengthens the caveat this study opened with: B1 is a
  PHOTOGRAPH, and lens character, sensor grain and real bounce are not
  lighting parameters. The tonemapper is still last, and film grain is a
  different lane of work from a light.


---

# Census, all three subjects — what generalises and what does not

| light | density board | empty origin | **dressed play board** |
|---|---|---|---|
| **CITY_Sun** | **+23.63** | **+28.37** | **+35.67** |
| CITY_StreetKey_A | +0.04 | +3.84 | +10.34 |
| CITY_StreetKey_C | -0.00 | +9.39 | +8.62 |
| CITY_Key | +8.14 | +6.35 | +5.90 |
| CITY_Fill | +2.17 | +2.91 | +5.12 |
| CITY_Sky | +0.70 | +1.11 | +1.37 |

**Only CITY_Sun's rank is stable.** It is first on every subject, and it is the
one finding of this study that survived every correction — three withdrawn
results, two eliminated mechanisms, and a metric that turned out to be half the
gap it was measuring.

Every other light's importance moves by an order of magnitude depending on
where the camera stands. That is the study's most transferable lesson and it is
not about lighting: **a measurement inherits the conditions it was taken under,
and a number quoted without them is a claim about a world that may not exist.**


---

# CLOSED, 2026-09-02 — the answer was not lighting

The control settled it. Identical boom geometry about each board's own centre,
matched resolution:

| subject | mean | grad p90 @768 | lift | spread |
|---|---|---|---|---|
| play board, 14 buildings | 135.2 | **17** | 0.283 | 160 |
| density board, 476 buildings | 86.2 | **39** | 0.421 | 163 |
| B1 target | — | 94 | 0.337 | 190 |

**Population moved local contrast by 129%. Two lighting mechanisms moved it by
zero** — sun source angle across 40x, and fill from full to none.

What read as a floor-and-backdrop problem was **sparseness wearing a floor's
clothes**. Put the density frame beside B2 and the composition is nearly the
same: city filling the frame, running off the edges, a strip of floor in one
corner, a wall behind. The floor stops being a problem when there is barely any
of it in shot.

## The thread closes here

- **Tonemapper: parked**, untried. It was always last, and after population
  it has nothing left to explain.
- **The ~3x residual against B1 is noted, not chased.** B1 is a photograph;
  lens character, sensor grain and real bounce are not lighting parameters,
  and this study said so before it had evidence. It now has evidence.
- **What the study is actually worth** is not its one surviving mechanism
  (`CITY_Sun` dominates every subject) but its four corrections: an inert key,
  a light judged from the wrong frame, a baseline poisoned by a crashed run,
  and a metric that was not comparable across resolutions. Every one of them
  would have shipped as a confident finding.
