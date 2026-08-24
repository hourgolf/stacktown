# Assetsville treatment test

Owner approved importing Fab assets on 2026-08-23, overriding the `AGENTS.md`
prohibition. Pack landed at `/Game/AssetsvilleTown`, 680 MB.

## What the pack actually is

    Meshes/BuildingTilset    100   modular walls, windows, doors, roofs, cornices
    Meshes/StreetProps       205
    Meshes/InteriorProps     350
    Meshes/Characters         68
    Meshes/Vehicles           40
    Meshes/Nature             21
    Meshes/Buildings           4   complete buildings only

It is a KIT, not a set of finished buildings. That matters more than it sounds.

## The decisive question: modelled or painted windows

**Modelled.** Measured, not eyeballed:

    SM_wall_01        4 tris    30.0 uu thick
    SM_window_01    680 tris    40.3 uu thick   + a dedicated Glass slot
    SM_window_02   1360 tris    40.3 uu
    SM_shopFront_01 350 tris    70.0 uu

680 triangles for a window is real frame and sash geometry, and the window
assembly is 10 uu deeper than the wall it sits in, so there is a genuine reveal.
At the 9 m player zoom the jamb return is clearly visible catching light. Stage
0's finding is satisfied by their geometry.

## Scale

Their module is 400 wide x 300 tall x 30 thick, at 1 uu = 1 cm - the same
convention we use. Their 300 uu floor sits directly against our 330-380 with no
scaling. Complete buildings run 2,806-3,280 tris, LIGHTER than our generated
5,984.

## What transferred, and what did not

| | result |
|---|---|
| card materials bound by slot name | **yes, cleanly** |
| window recess depth | **yes, modelled** |
| scale compatibility | **yes, no scaling needed** |
| triangle budget | **better than ours** |
| edge wear | **no** - their geometry has no 45 degree chamfers, so the normal-as-curvature proxy finds nothing |
| panel seams | inconclusive - no seam fell in the sampled 204 uu strip; the mechanism is world-projected so it should apply, but it was not demonstrated |
| interiors behind glass | **absent** - their windows have no room behind, so they read as holes. Same trap as the generated block before practicals |
| glue / peels / dent | not applicable - would need placing per asset |

## Use the tileset, not the complete buildings

The four complete buildings expose slots named `customMat_01` .. `customMat_14`.
Those names carry no role, so the one-sweep material binding that makes the
generated block cheap does not work on them - each would need mapping by hand.

The tileset is the opposite: the ROLE IS IN THE MESH NAME. `SM_window_01` is a
window. That is the same property our generated components have, and it is what
makes automatic treatment possible.

So the synthesis is: **our generator drives their modules.** Parameter-driven
layout, their module vocabulary in place of emitted boxes, our card treatment
over the top. That buys typology variety - houses, barns, gas stations, shops -
without hand-placing anything, and keeps per-floor tolerance because the
building is still assembled from separate pieces.

## Two things to fix before that is real

1. **Edge wear must be rebuilt geometry-agnostic.** The normal proxy only works
   on axis-aligned boxes with 45 degree chamfers. Baked curvature via
   GeometryScripting would work on their pieces and ours alike.
2. **Interiors and practicals must be generated behind their windows**, the same
   way `practicals.py` derives them from our geometry.

## Errors made during this test

`unreal.Rotator(a, b, c)` is **(roll, pitch, yaw)**. Passing `Rotator(0, 90, 0)`
for "yaw 90" sets PITCH 90 and lays every piece flat on the ground. The first
capture showed twelve tiles lying in the street.

## The skeletal crash: cause found, and it does NOT inhibit scale

### What actually causes it

    Assertion failed: VertexFactory == nullptr || VertexFactory->IsReadyForStaticMeshCaching()
    [SkeletalRenderGPUSkin.cpp:2071]  ->  SIGSEGV

Crashed twice. It is a **render-state race when several skeletal meshes are
spawned inside one remote-execution call**: the script completes, and 42 ms
later the render thread tries to cache draw commands for meshes whose vertex
factories are not ready yet.

Isolated by testing one variable at a time:

| test | actors | setter | result |
|---|---|---|---|
| 1 | 1 | `spawn_actor_from_object` | survived |
| 2 | 1 | + material override | survived |
| 3 | 1 | empty actor + `set_skinned_asset_and_update` | survived |
| 4 | **8** | `spawn_actor_from_object` (correct API) | **CRASHED** |

**A REASONING ERROR WORTH RECORDING.** After test 3 I reported the deprecated
`skeletal_mesh` property as the confirmed cause. It was not. The original
failure had twelve actors AND the deprecated setter; I changed the setter, held
the count at one, and concluded the setter was the differentiator. Tests 1-3
never exercised the variable that mattered. Test 4 used the correct API and
crashed anyway. Vary one thing, and make sure it is the thing that differs.

### Why it does not inhibit scale

Because a city should not be spawning skeletal meshes at all. Skeletal is for
animated foreground actors; background people and parked cars want to be static
so they can be instanced. `GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh`
bakes them:

    SK_veh_Sedan_01          -> SM_Baked_Sedan    6064 tris  4 slots
    SK_veh_Pickup_01         -> SM_Baked_Pickup   6461 tris  4 slots
    SK_veh_PoliceCarSedan_01 -> SM_Baked_Police   6720 tris  3 slots
    SK_veh_CargoTruckOld     -> SM_Baked_Truck    5738 tris  3 slots
    SK_citizen_female_01     -> SM_Baked_Ped1     1784 tris  1 slot
    SK_citizen_female_05     -> SM_Baked_Ped2     1436 tris  1 slot
    SK_citizen_female_09     -> SM_Baked_Ped3     1606 tris  1 slot

    six assets baked in 1.1 s, material slots preserved

Baking runs on the game thread and never puts a SkeletalMeshComponent in front
of the renderer, so it is safe to batch even though spawning is not. The baked
statics then placed seven at a time with no incident.

So the crash is a symptom of doing the wrong thing for a city, and the right
thing removes it. Bake once per pose, place as statics, instance at scale.

**The one real cost:** a baked mesh is a frozen pose. A living diorama will
still want some genuinely animated characters, and those must be real skeletal
actors - spawned in small batches, foreground only, and few.
