---
name: stacktown-studio-director
description: Hold the Stacktown art direction — the handmade-miniature look, fabrication language, palette discipline, and what makes a surface read as a physical model. Trigger for look decisions, material choices, lighting and camera intent, reference interpretation, or any question of whether something looks right rather than whether it works.
---

# Stacktown Studio Director

Three other skills defer to this one for art direction. In the legacy repository this skill was
referenced but never written, which is a large part of why the visual target was never reached:
every skill pointed at an authority that did not exist.

## The target, stated once

A dense, modern, Portland-inspired building photographed as a **handmade architectural model**.

The operative word is *handmade*. Not a small real city — a made object. Everything follows from
that: the surfaces are fabricated, the light is a lamp in a room, the base is a board, and the
imperfections are a maker's imperfections rather than a city's weathering.

## The one insight that makes this achievable solo

A miniature is easier than a photoreal city, and the reason is worth internalising: **a model is
unified by fabrication.** Every object on a real architectural model is the same handful of
materials, painted in one session, under one lamp. That is why models read as coherent even when
their subjects are not.

This converts an asset-sourcing problem — which a solo developer with $200 cannot win — into a
shader and lighting problem, which one person can win. See `Docs/MASTER_MATERIAL_SPEC.md`.

## What reads as a physical model

In rough order of impact:

1. **Geometric reveal.** Recess, projection, thickness, inset. A model reads as physical because
   light catches real edges. This outranks everything below it and no amount of the rest
   compensates for its absence.
2. **A base.** A visible board edge tells the eye this is an object on a table.
3. **An environment.** A model in a black void is a render. A model in a lit room is a model.
   The room does not need to be modelled in detail — it needs to exist and contribute bounce.
4. **A narrow roughness band.** Fabricated surfaces cluster; real materials scatter.
5. **Contact shadows.** Where things touch the board.
6. **Scale-honest detail.** Detail that a maker could plausibly have made at this scale, not
   detail scanned from reality.
7. **Deliberate imperfection.** A seam, a paint break, a slight misalignment.

## What does not

- Depth of field. It is the last five percent and it is the first thing everyone reaches for.
  Judge with it off. If the scene needs it to work, the scene does not work.
- Tilt-shift on a scene without real depth. It reads as a filter on a render.
- Bloom, warm grading, or a long lens applied to weak geometry.
- More props. Density is not the same as specificity.
- Photoreal donor assets dropped next to flat-shaded ones. Detail tier must match, and it must
  match at the fabrication tier, not the reality tier.

## Palette discipline

Restrained. The legacy project's best captures were grey concrete, teal glazing, dark mullions
and warm practicals — roughly four values plus glass. That restraint was working; it was the
geometry underneath that was not.

When adding a colour, the question is what it replaces, not what it adds.

## Interpreting references

- Real handmade miniatures and architectural presentation models are the primary references, for
  surface, light, and base treatment.
- Portland is a *character* reference — contemporary mixed-use, timber and glass and brick,
  transit, greenery. Not a geographic one. Literal GIS reconstruction is explicitly retired.
- Aspirational games may be studied lawfully for camera behaviour, pacing, and interaction only.
  Never extract their assets or code.
- Generated concept renderings are mood, never specification. The single most consequential
  mistake in this project's history was treating a persuasive render as proof that the same
  result was reachable in-engine with the assets on hand.

## How to use this skill

When a decision is aesthetic, decide it here rather than deferring to the owner. Consequential
decisions — the approved camera, the approved baseline, an asset purchase, or a change to the
target itself — go to the owner. Everything else is yours to fix before review.

When you make a look claim, open the rendered image and look at it first. Both prior stewards
reported visual progress they had not inspected.
