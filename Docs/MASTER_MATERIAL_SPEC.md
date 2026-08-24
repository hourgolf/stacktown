# The Stacktown Master Material

## Why this is a first-class system and not a hack

The bakeoff project built per-instance material overrides to make mismatched donor props
readable, and its handoff letter filed that work under "quarantine — overrides developed solely
to rescue unsuitable donor packs."

That was the wrong call, and the evidence is in the project's own captures. The storefront
vignette — concrete, teal glazing, dark mullions, painted-styrene surfaces — is the closest
anything in that project came to the target. The unified material is not what rescued bad
assets. **The unified material is the art direction.**

The reason is physical. A real architectural model reads as one object because everything on it
genuinely *is* one thing: styrene and resin and printed card, painted in one session, lit by one
lamp. It is not a collection of accurate materials — it is a collection of *the same* material,
shaped differently. That is the single highest-leverage system available to a solo developer
with mismatched sources, because it converts an asset-sourcing problem into a shader problem.

## The rule

Every architectural surface in Stacktown derives from one master material. Variation comes from
instance parameters, never from a differently-authored shader. If a surface cannot be expressed
as a parameterisation of the master, that is a signal the asset does not belong.

Donor assets keep their imported materials untouched. Overrides are applied at the actor or
component level so a rejected asset never contaminates the content library.

## Role vocabulary

Inherited from the bakeoff and worth keeping. Roles, not materials — each is an instance of the
master with different parameters.

| Role | Use |
|---|---|
| `concrete` | Cast structural surfaces, sidewalk, plinth faces |
| `paint_cream` | Light painted architectural surfaces, markings |
| `paint_accent` | Saturated painted accents; use sparingly |
| `dark_metal` | Mullions, railings, brackets, poles, fixtures |
| `glass` | Glazing — see the glass rule below |
| `wood` | Warm timber elements, benches, soffits |
| `brass` | Small bright metal details only |
| `model_board` | The base the model sits on |

Keep the set this small. The last project's palette grew a `walnut` and a `cedar` and a
`bronze` that did nothing a parameter could not have done.

## Master material parameters

At minimum the master exposes:

- **Base colour** and a **tint** so a role can be recoloured without a new material
- **Roughness range** — clamped, and clamped narrowly. Fabricated surfaces occupy a much
  tighter roughness band than real ones. This clamp is what unifies mismatched sources.
- **Edge wear / paint break** driven by curvature, at model scale rather than world scale
- **Fine surface noise** — the tooth of paint or print, visible only at inspection range
- **Panel seam** control — fabrication seams are a feature, not a defect (gate line C3)
- **Texel density normalisation**, so a donor mesh's UV scale does not betray it

## The glass rule

Glass gets its own paragraph because it failed hard in the bakeoff: a flat teal gradient with a
white glow behind it, no frame, no depth, no reflection.

Glass in a physical model is usually clear acrylic behind a frame, and it reads as glass because
of three things, none of which is the glass shader:

1. **Frame depth** — real geometry, recessed (gate lines A1, A2)
2. **A reflection that responds to the environment** — which requires there to *be* an
   environment (gate line D1)
3. **Something behind it** — an interior card, a blocked-in room, even a dark box. Emptiness
   behind glass reads as a hole.

Get those three right and a nearly trivial glass material works. Get them wrong and no glass
shader saves it.

## Prohibited

- A second master material for architecture "just for this one thing"
- Per-asset bespoke shaders
- Using the master to disguise geometry that fails the reveal checks in the gate. The material
  unifies *fabrication*. It cannot manufacture depth, and the last project proved that.
