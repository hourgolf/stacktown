# Stage 0 — The Bay Recipe

Build instructions with real numbers, so the first session is an experiment rather than
fumbling. Everything here is authorable in Modeling Mode. No purchase, no import, no donor pack.

**Honest caveat up front:** the depths below are reasoned from how architectural models and
miniature photography actually behave, not measured in your project. The recess depth that reads
correctly at 70mm is the one thing that must be found empirically — which is why the session is
built as a comparison rather than a single attempt.

---

## The experiment

**Build the bay three times, side by side, identical except for one variable.**

| Variant | Window recess from wall face |
|---|---|
| `BLD_Bay_A` | 75 mm |
| `BLD_Bay_B` | 150 mm |
| `BLD_Bay_C` | 250 mm |

One capture, all three in frame, at the approved camera. You will know within one image which
depth reads as physical and which reads as a decal. That answer is the single most valuable
output of Stage 0 and it costs one session.

Everything else stays constant across the three. Change one variable per experiment.

---

## Scale decision: build at 1:1, fake the optics

Build at real-world scale — 1 uu = 1 cm, a 3.6 m storey is 360 uu. Do **not** model a physically
tiny object.

The miniature read comes from the camera and the material, not from shrinking the geometry:

- long focal length at close distance gives the compression that says "macro shot of a small
  thing"
- looking slightly **down** at the subject says "an object on a table"
- the master material supplies the fabrication cue

Building at literal miniature scale fights asset imports, units, and any future gameplay code,
and buys nothing the optics don't already give you.

---

## Bay geometry

Contemporary mixed-use, upper-floor bay. All dimensions in millimetres.

| Element | Dimension |
|---|---|
| Bay width | 3600 |
| Floor to floor | 3600 |
| Wall plane thickness | 300 |
| Window opening | 2400 w × 2100 h |
| **Window recess from wall face** | **the variable — 75 / 150 / 250** |
| Sill projection beyond wall face | 40 |
| Sill thickness | 60 |
| Head reveal depth | matches the window recess |
| Mullion depth | 60 |
| Mullion width | 50 |
| Glass set back behind mullion face | 80 |
| Spandrel panel recess from wall face | 40 |

The **spandrel recess** matters more than it looks. A secondary plane only 40 mm back is what
gives real facades their layered read — a facade with one plane is a box with holes in it, which
is exactly what the bakeoff produced.

Every one of these numbers exists to satisfy gate lines A1 and A2 — the only reveal lines a
single bay can carry. A3 (parapet), A4 (entrance), A5 (curb) and A6 (silhouette) describe
building-scale features this recipe forbids building; see the Stage 0 carve-out in
`Docs/ONE_BUILDING_GATE.md`, which defers them to Stage 1. There is no texture-based
substitute for any of them.

---

## Master material v0

One material, instanced per role. See `Docs/MASTER_MATERIAL_SPEC.md` for why.

**The roughness clamp is the most important parameter in the project.** Fabricated surfaces
occupy a much narrower roughness band than real ones, and that narrowness is what will
eventually unify mismatched sources.

| Parameter | Starting value | Note |
|---|---|---|
| Roughness clamp (painted) | 0.35 – 0.55 | Narrow on purpose. Do not widen to "add realism." |
| Roughness clamp (glass) | 0.02 – 0.08 | Acrylic, not optical glass |
| Base colour — concrete | sRGB 0.62 / 0.61 / 0.58 | Desaturated, slightly warm |
| Base colour — paint_cream | sRGB 0.80 / 0.78 / 0.73 | |
| Base colour — dark_metal | sRGB 0.13 / 0.13 / 0.14 | Mullions, brackets |
| Edge wear width | ~2 mm world | Curvature-driven lightening. Reads as a brush edge. |
| Micro-normal feature size | ~0.5 mm | Low intensity, 0.05 – 0.10 |
| Large-scale albedo variation | **none** | This is the trap |

That last row is the counterintuitive one. Large-scale colour and dirt variation is what makes
real concrete look real — and what makes model concrete look wrong. A painted model surface is
uniform in colour and varied only in *sheen* and at *edges*. Resist adding grunge.

### Glass

Three things make glass read, and none of them is the glass shader:

1. Frame depth — real geometry, recessed
2. A reflection that responds to an environment — which requires there to be an environment
3. Something behind it — an interior card or a dark blocked-in box. Emptiness behind glass
   reads as a hole, which is what the bakeoff's flat teal gradient was.

Put a simple dark interior card 400 mm behind the glass. Not a room. A card.

---

## Light rig — the highest-leverage single choice

**Use a Rect Light as the key. Not a Directional Light.**

A directional light is the sun. It says "outdoors, full scale," and its hard uniform shadows are
visible in the bakeoff's hero-corner capture — that alone was working against the miniature read
in every image the last project produced.

An area light says "a lamp above a table," which is exactly what is being simulated.

| Light | Setup |
|---|---|
| `LIGHT_Key` | Rect Light, ~4500 K, 45° off camera axis in plan, ~35° elevation, large source relative to subject — soft-edged but clearly directional |
| `LIGHT_Fill` | Large dim Rect or a low-intensity sky, cooler, opposite side, roughly 1/8 key intensity |
| Practicals | Only what the bay's own glass needs, behind the interior card |

## Environment

- `STAGE_ModelBoard` — the board the bay sits on, with a **visible chamfered edge**. Gate C2.
- `STAGE_Backdrop` — a flat or gently curved neutral mid-grey card, 3–5 m behind, catching a
  gradient from the key.
- Ground extending past the board.

**No black void.** Gate D1. A model in a void is a render; a model in a room is a model.

## Camera

| Setting | Value |
|---|---|
| Focal length | 70 mm |
| Pitch | **−12°, looking down** |
| Height | above the top of the bay |
| Framing | bay group fills ~60% of frame height |
| Exposure | fixed, recorded with the capture |
| DOF / bloom / motion blur | **off** |

The downward pitch is not a stylistic preference. Looking down at something is one of the
strongest miniature cues available, it is free, and every capture in the bakeoff was shot from
a raised but essentially level three-quarter view.

Set FOV explicitly through the native viewport subsystem. The EditorToolset camera transform
does **not** change FOV — that is how the last project captured an entire pass at 90° by
accident.

---

## Session definition of done

- [ ] Three bays exist, identical but for recess depth, labelled `BLD_Bay_A/B/C`
- [ ] Every material slot assigned — zero default materials (gate B1)
- [ ] Board with visible edge, backdrop, ground; nothing floating in a void
- [ ] Rect key light, not directional
- [ ] Fixed exposure, value recorded
- [ ] One deliberate composed capture at 70 mm / −12°, DOF and bloom off, no editor overlay
- [ ] The capture has been **opened and looked at**
- [ ] Gate sections A, B, D, E, F walked line by line, pass/fail recorded per numbered line
- [ ] A stated answer to: which recess depth reads as physical?

## What not to do in this session

Do not add a second bay type, a ground floor, a roof, a tree, a prop, a vehicle, or a person.
Do not enable depth of field to see if it helps. Do not import anything. Do not buy anything.

If the bay fails, report which numbered gate line failed and stop. That failure is worth more
than a week of additions.
