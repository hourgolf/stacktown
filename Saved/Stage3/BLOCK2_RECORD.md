# Block #2 — the far side of the street

Built 2026-08-24. The generalisation test: a second block from the same
generator, at a different origin, **rotated 180 degrees** so it faces block A
across a road.

## The structural change that made it possible

`genbuild.build(spec, origin, yaw)`. Lot coordinates are now BLOCK-LOCAL and the
block's world placement lives on the actor transform. Boxes were already placed
with `local_transform` relative to their actor, so the change was small - but
until it was made, every coordinate in the build was world space and a second
block could only ever have been a copy-paste.

`city.py` holds the city table: a block is an origin, a yaw, and a list of lots.

    block A  origin (0, 0, 0)         yaw 0     3 lots (2 generated + Assetsville)
    block B  origin (4150, -1600, 0)  yaw 180   3 lots, all generated

Under yaw 180 a lot at local x 0..W lands at world X0-W..X0, and local +Y
(depth) runs toward -Y, so B's origin sits at the far kerb and its buildings
grow away from the street.

## What had to become city-aware

    step_roles.py    wall colour read from the city table, not a hardcoded map
    step_cores2.py   cores derived in BLOCK-LOCAL space and spawned with the
                     block transform. The previous version measured world
                     extents, which only works for an unrotated block
    step_stage2.py   board extended to X -300..4600, Y -2700..900, and the
                     street rebuilt as a road between TWO pavements

## Result

    Bank  4 floors  h 2030   Slim  7 floors  h 2520   Hall  3 floors  h 1930
    426 boxes, 721 material slots assigned with zero unresolved, 5 cores,
    43 practicals

Both rows read as facades from a camera on the street centreline.

## A timing correction that changes the scale projection

Block B's 426 boxes took **29 seconds** - 0.068 s per box. The figure recorded
during Stage 2 was 0.75 s per box, and the nine-hour projection for a hundred
blocks was built on it. That projection is wrong by more than an order of
magnitude.

The likely difference is machine contention: the earlier measurement was taken
while two other Unreal editors were running for the parallel Portland work. At
0.068 s a hundred blocks is about **50 minutes of MCP calls**, not nine hours,
which materially weakens the argument for the single-mesh bake path on transport
grounds alone. The bake still wins on component count (1 vs ~140 per building),
and that remains the real reason to pursue it.

## Open

- **The far side of the street is underlit.** Block B faces +Y, away from a key
  light placed for a single row. Physically correct and visually wrong; the rig
  was derived for one block and needs re-deriving for a street.
- The backdrop does not cover the view down the street - there is black void
  past the end of the board.
- Props, trees and vehicles exist only on block A's pavement.

## "Facades standing away from the building" — measured

Reported from two close screenshots. Checked every core against its own facade:
no core protrudes toward the street on any of the five buildings. But the
numbers showed the real fault:

    Narrow  facade X 1072..1948   core X 1080..1940
    Mid     facade X 3162..4158   core X 3170..4150

The band course runs `x0-8 .. x0+W+8` and the parapet cap sits 14 uu above
ztop, while the core was cut to exactly (width, height). So the facade
overhangs its core by 8 uu on each side and 14 uu on top. Head-on that is
invisible; at a block END it reads as a thin fin standing away from a blank
slab, which is exactly what the screenshots showed.

Cores now carry the overhang (width+16, height+14) and the corner reads flush.

## The paper projection degenerates on X-facing surfaces

Fixing the fin exposed a large blank end wall for the first time, and it is
visibly ribbed. Measured as detrended sd along rows vs columns:

    END wall        normal +/-X    rows 5.68   cols 0.42   ratio 13.5x
    facade spandrel normal -Y      rows 0.37   cols 0.52   ratio  0.7x
    facade pier     normal -Y      rows 2.07   cols 3.01   ratio  0.7x

The paper texture is world-position projected on **XZ**. On a face whose normal
is X the X coordinate does not vary across the surface, so the texture varies
only in Z and the result is horizontal banding - corduroy, not paper. On a -Y
facade both coordinates vary and it is isotropic.

This has been true since the projection was written. It was never visible
because until block ends and core walls entered a render, every surface examined
faced +/-Y.

**The fix is triplanar projection** - blend XZ / YZ / XY by the surface normal -
which is a master-material change, not a parameter. It would also make the
treatment work on arbitrary imported geometry, which is the same thing the edge
wear needs.

## Triplanar projection — built and measured

`Content/Python/triplanar.py` samples `T_PaperNormal` on all three world planes
and blends by the surface normal.

    END wall   before  rows 5.68  cols 0.42  ratio 13.5x
               after   rows 0.63  cols 0.40  ratio  1.6x

    FACADE     before  rows 0.37  cols 0.52  ratio  0.7x
               after   rows 0.44  cols 0.42  ratio  1.1x

The banding is gone from X-facing surfaces and the facades are unchanged in
magnitude - so nothing regressed when `MP_Normal` was replaced.

Two things worth keeping:

**Blend weights come from `VertexNormalWS`, not `PixelNormalWS`.** Weighting the
normal map by the pixel normal it produces is circular. The vertex normal is the
geometric one and is the correct input.

**`PaperTiling` is live again.** It was inert - a 4x change moved the measured
detail by nothing - because it was not reaching the samplers' UVs. The triplanar
chain scales world position by it before masking, so it now controls the tile
size as its name claims.

Hero after the change: mean 167.1, blown 0.000%, crushed 0.000%. Geometry check
passes with its self-check OK.

### Still open, unchanged by this

- The far side of the street is underlit; the key/fill rig was derived for a
  single row facing -Y and needs re-deriving for a street.
- The backdrop does not cover the view down the street.
- Props, trees and vehicles exist only on block A's pavement.
- Edge wear still needs the same treatment triplanar just got: it is a
  normal-as-curvature proxy that only works on 45 degree chamfers, so it does
  nothing on imported geometry. Baked curvature is the equivalent fix.

## Hollow facades — every floor of every building

Reported as "the front of the building isn't attached to the main building".
It was not attached. Measured, in block-local Y:

    Narrow  facade back 60.0   core front 160.0   void 100.0
    Mid     facade back 60.0   core front 190.0   void 130.0
    Bank    facade back 60.0   core front 130.0   void  70.0
    Slim    facade back 60.0   core front 140.0   void  80.0
    Hall    facade back 60.0   core front 130.0   void  70.0

**Every floor of every building**, 70-130 uu of empty space between the back of
the facade and the front of the mass behind it. Head-on it is hidden; at an
oblique angle or a block end you look straight into the slot.

Two causes, both mine:

1. The core front was `max(130, setback+70)` - ONE value per building, driven by
   the deepest floor. genbuild only sets back the TOP floor, so every other
   floor got a void the depth of the setback.
2. The 130 floor was arbitrary. The facade back is at 60.

Cores are now per-band segments (`step_cores3.py`): ground plus all non-setback
floors at front 62, top floor plus parapet at setback+62. Worst remaining void
**2.0 uu**, which is the intended clearance.

### The check was as wrong as the geometry

`core_check.py` compared only the STREET-side edges and passed all five
buildings while every one of them was hollow. Then `gap_check.py` kept whichever
core actor it found last, so once cores became two segments it compared every
floor against the setback band and reported 72 uu voids that did not exist.

`gap_check2.py` matches each floor to the core segment covering its Z band. Both
checks now run inside `build_block.py` rather than being one-off scripts, which
is the only reason a regression here would be caught next time.
