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

## Already done by `mk_runtime.py` and `fill_runtime.py`

- `BP_BuildingCatalogue` and `BP_Parcel` created, members added, compiled.
- `BP_Parcel` has a `StaticMeshComponent` named **Building**.
- `DA_Catalogue` exists and holds **6 rows** — cottage and walkup, three tiers
  each, each pointing at its baked mesh.

Only the graph is left, and it is three short functions.

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

## First measurement, 25 Aug 2026

`sim_tick.py` runs the tick in Python against the REAL assets - it spawns 500
`BP_Parcel` actors, reads `DA_Catalogue`, and does exactly the lookup
`ResolveMesh` will do. Python through Unreal's reflection layer is the SLOWEST
possible implementation of this, which is what makes the numbers useful:

    place 500 parcels                     1240 ms   (2.48 ms each)
    tick, every parcel upgrades            295 ms   (0.59 ms each)
    tick, nothing changed                  1.1 ms   (0.002 ms each)

**The budget is not met in the worst case and is met 90x over in the common
one.** A tick where all 500 buildings upgrade at once is 295 ms against a
100 ms budget - but that is not a case a city produces; buildings cross tier
thresholds at different times. A tick where nothing changes is **1.1 ms**, and
that is the case that runs almost every tick.

The Branch in the tick is what buys that: `ResolveMesh` only runs when the tier
actually changed. Without it every tick would cost the 295 ms.

**What this says about C++.** Nothing yet, and that is the point of measuring
before deciding. The slow path is Python reflection writing one property at a
time; Blueprint does not pay that. If a Blueprint implementation still misses
the budget on a realistic tick, THAT is the measurement that justifies C++.

## Step by step

**1. Open it.** Content Browser → `Content/Stacktown/Runtime` → double-click
`BP_Parcel`. Left panel is Components (you will see **Building**), the middle is
the Event Graph, and **My Blueprint** on the left lists the six variables.

**2. Make the function.** In My Blueprint, hover **Functions** → **+**. Name it
`ResolveMesh`. It opens its own graph tab with a single entry node.

**3. Wire `ResolveMesh`.** Drag from the entry node's white execution pin and
build this chain:

- Drag **Catalogue** from My Blueprint into the graph → choose *Get*.
- Drag off it → **Cast to BP_BuildingCatalogue**. (The variable is typed as the
  generic `PrimaryDataAsset`, so it needs the cast to reach the arrays.)
- From the cast's blue output → **Get Recipe Ids**.
- Drag off that array pin → **For Each Loop with Break**.
- Connect the entry node's exec to the cast, and the cast's exec to the loop.

Inside the loop body:

- **Array Element** (a Name) → **Equal (Name)** ← drag in **RecipeId** (*Get*).
- From the cast → **Get Tiers** → **Get (a copy)** with **Array Index** from the
  loop → **Equal (integer)** ← drag in **Tier** (*Get*).
- Both Equal outputs → an **AND** node → into a **Branch** condition.
- Loop Body exec → Branch.
- Branch **True** → **Set Static Mesh**: drag **Building** from Components into
  the graph, drag off it, choose *Set Static Mesh*. Its **New Mesh** pin comes
  from the cast → **Get Meshes** → **Get (a copy)** with the same **Array
  Index**.
- After Set Static Mesh, run the exec into the loop's **Break** pin so it stops
  at the first match.

Compile. That one function is the whole of *place* and the whole of *upgrade*.

**4. Wire the tick.** Back in the Event Graph, right-click → **Add Custom
Event**, name it `CityTick`.

- **Level** → **+ (float)** with 0.1 → **Clamp (float)** 0 to 1 → **Set Level**.
- **Level** → **× (float)** by 2 (that is tier count minus one) →
  **Round** → a local variable or straight into **Set Tier**.
- Before setting, a **Branch**: **Not Equal (integer)** comparing that rounded
  value against **Tier**. True → **Set Tier** → call **ResolveMesh**.

The branch is the point: `ResolveMesh` only runs when the tier actually changed,
so a tick that does nothing costs nothing.

**5. Try it.** Drag `BP_Parcel` into the level. In its Details panel set
**Catalogue** to `DA_Catalogue`, **RecipeId** to `cottage`, **Tier** to `0`,
**WidthUU** to `820`. Right-click the `ResolveMesh` node → *Call Function* — or
just press Play and fire `CityTick` from a key binding — and it should take the
cabin mesh. Set Tier to 2 and call it again: the extended house, same identity,
one pointer swap.

**If Cast to BP_BuildingCatalogue does not appear** in the node menu, the
Blueprint has not been compiled since the class was made — hit **Compile** on
`BP_BuildingCatalogue` first.

## What this slice does not prove

Everything above happens in the editor. A packaged build has no Python, so the
simulation itself will eventually need to live in Blueprint or C++. The slice
proves the **data and asset pipeline** end to end; it does not prove the
simulation loop under load. That measurement comes when there is a loop to
measure, and it is the measurement that would justify C++.
