# The runtime slice

Approved 2026-08-25: Blueprint authoring and a catalogue DataAsset. Narrowly —
**not** a C++ module, `AllToolsets`, PCG, or a parallel MCP server. Those stay
approval-gated, and C++ comes back for discussion when a **measured** wall says
so, not in anticipation of one.

## What "working" means, agreed before it is built

A runtime system cannot be checked by the invariant suite the way geometry can:
there is no snapshot to run a rule over. So the numbers come first, or we are
back to judging by eye — which is exactly what the F1 finding caught us doing
with the geometry.

| what | budget | why this number |
|---|---|---|
| Full city tick, 500 parcels | **< 100 ms** | tick-based, so the sim runs about once per game-second. 100 ms is invisible at that cadence and leaves room to grow. |
| Placed buildings before frame time moves | **500** | eight blocks is 23 buildings; 500 is a city. |
| Upgrade, one parcel | **< 1 ms** | see below — it is a pointer swap, not a generation. |
| Catalogue bake, whole set | offline, unbudgeted | it is an authoring step, not a runtime one. |

**The number that makes the rest affordable.** The level today holds **1,061
actors and 8,582 visible components** for 23 buildings, because a generated
building is 130–300 boxes. Baked, a building is **one component**. Five hundred
generated buildings would be roughly 186,000 components, which is not a
budget problem, it is an impossibility. Five hundred baked buildings is 500
components.

**So a runtime upgrade is a mesh pointer swap.** The catalogue is pre-baked at
every tier, so moving a parcel from tier 1 to tier 2 assigns a different
`StaticMesh` to an existing component. No generation, no merge, no allocation.
That is the whole reason the recipe/bake split exists, and it is why tick-based
buys us ambition per building rather than costing us performance.

## What Python authored, and what it cannot

Established by probe, not assumption:

- `BlueprintEditorLibrary` **can** create a class against a parent, add typed
  member variables, and compile. `mk_runtime.py` does all three.
- It **cannot** author graph nodes. There is no Python API for wiring
  execution flow.
- `UserDefinedStructEditorLibrary` is **not exposed** in this build, so a
  custom row struct cannot be authored — which rules out a `DataTable` and is
  why the catalogue is a `PrimaryDataAsset` with parallel arrays rather than an
  array of structs. Uglier than a struct, and reproducible, which a hand-made
  struct is not.

**Consequence, stated plainly rather than worked around: the data layer is
generated and the graph is editor work.** The spec below is what to wire.

## Assets

`/Game/Stacktown/Runtime/BP_BuildingCatalogue` — `PrimaryDataAsset`

    RecipeIds   Name[]         'cottage', 'walkup', ...
    Tiers       int[]          0, 1, 2
    Widths      double[]       the parcel width the mesh was baked for
    Meshes      StaticMesh[]   /Game/Stacktown/Baked/SM_Bld_<id>_t<n>_w<w>
    TierNames   String[]       'cabin', 'house', 'extended'

Parallel arrays: row *i* of each is one catalogue entry.

`/Game/Stacktown/Runtime/BP_Parcel` — `Actor`

    RecipeId    Name           what stands here
    Tier        int            how far along it is
    Level       double         0..1, how developed this part of the city is
    WidthUU     double         parcel dimensions, for the grammar
    DepthUU     double
    Catalogue   PrimaryDataAsset

## The graph to wire

Three functions on `BP_Parcel`, none of them long:

1. **`ResolveMesh`** — find the row where `RecipeIds[i] == RecipeId` and
   `Tiers[i] == Tier` and `Widths[i] == WidthUU`; return `Meshes[i]`. Assign it
   to the StaticMeshComponent. This is the whole of "place" and the whole of
   "upgrade".

2. **`PickRecipe`** — the grammar. Given `WidthUU` and `DepthUU`, choose from
   the recipes that fit. `Content/Python/grammar.py` is the reference
   implementation and carries the known-answer tests, including the negative
   cases — a grammar that returns something for every parcel is not a grammar.

3. **`Tick`** — advance `Level`, derive `Tier` from it, and if `Tier` changed
   call `ResolveMesh`. **`Level` selects the tier, never the recipe.** A
   neighbourhood does not swap its houses for different houses as it grows; it
   grows the ones it has. That property is why the seed lives in a recipe's
   base and not in its tiers.

## What this slice does not prove

Everything above happens in the editor. A packaged build has no Python, so the
simulation itself will eventually need to live in Blueprint or C++. The slice
proves the **data and asset pipeline** end to end; it does not prove the
simulation loop under load. That measurement comes when there is a loop to
measure, and it is the measurement that would justify C++.
