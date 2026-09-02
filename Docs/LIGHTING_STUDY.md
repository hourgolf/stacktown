# Why it still reads as a rendering — a measured lighting study

**Status: STUDY DESIGN. Nothing changed, no pairs shot yet.** The owner's
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
