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

Everything below is in `Content/Stacktown/Runtime`. The catalogue now carries a
**MeshByKey** map — key `recipe_tier` (`cottage_0`, `walkup_2`) to the baked
mesh — so `ResolveMesh` is five nodes instead of a twelve-node loop. Six entries
are already filled in.

### The panels, once

Double-click **BP_Parcel**. Four areas matter:

- **Components**, top left. You will see `DefaultSceneRoot` and **Building**.
- **My Blueprint**, bottom left. Variables: RecipeId, Tier, Level, WidthUU,
  DepthUU, Catalogue.
- The **graph**, middle — the big grid.
- **Details**, right — shows whatever is selected.

Two things to know. **White pins are execution** (the order things happen);
**coloured pins are data**. And "drag off a pin" means click the little circle,
drag into empty space, let go — a search box appears, and it only offers nodes
that fit that pin.

### 1. Make the function

In **My Blueprint**, hover the **Functions** row, click the **+**. Name it
`ResolveMesh`. A new tab opens with one node: `ResolveMesh` with a white output
pin. That white pin is where the chain starts.

### 2. Get the catalogue and cast it

- Drag **Catalogue** from My Blueprint into the graph. A menu offers Get/Set —
  choose **Get Catalogue**.
- Drag off the blue pin on its right, let go, type `Cast to BP_BuildingCatalogue`,
  pick it.
- Connect the entry node's **white** pin to the cast's **white** input.

The variable is typed as the generic `PrimaryDataAsset`, which is why it needs
the cast to reach the arrays.

### 3. Build the key

- Right-click empty graph space, type `Append`, choose **Append** (under String).
- Drag **RecipeId** in as a *Get*, connect it to the Append's **A**. It converts
  Name to String automatically — a small dot appears on the wire, which is
  correct.
- Click **B** and type `_` (one underscore).
- On the Append node click **Add pin**. Drag **Tier** in as a *Get* and connect
  it to the new pin. Int converts to String the same way.

Append now produces `cottage_0`.

### 4. Look the mesh up

- From the **cast node's** blue output ("As BP Building Catalogue"), drag off
  and type `MeshByKey` → **Get MeshByKey**.
- Drag off MeshByKey's pin, type `Find`, choose **Find** (the Map one).
- Connect **Append's** output to Find's **Key**.

Find gives you **Value** (the mesh) and a boolean.

### 5. Set the mesh

- Drag **Building** from **Components** into the graph.
- Drag off it, type `Set Static Mesh`, choose it.
- Connect **Find's Value** to **New Mesh**.
- Connect the **cast's** white output to **Set Static Mesh's** white input.

Press **Compile** (top left). Green tick means done.

### 6. The tick

Go to the **EventGraph** tab. Right-click empty space → `Add Custom Event`, name
it `CityTick`.

- Drag **Level** in as *Get* → drag off it → `+` → choose **float + float**. Set
  the second box to `0.1`.
- Drag off the result → `Clamp (float)`. Min 0, Max 1.
- Drag **Level** in as a **Set** and feed the clamped value in. Connect
  `CityTick`'s white pin to it.
- Drag off the clamped value again → `*` → **float * float**, second box `2`.
- Drag off that → `Round`.
- Drag off Round → `!=` → **Not Equal (integer)**; drag **Tier** in as *Get* for
  the other side.
- Drag off that boolean → **Branch**. Connect Set Level's white pin to Branch.
- Branch **True** → drag **Tier** in as a **Set**, feed it the Round result.
- From Set Tier's white pin → drag off → type `ResolveMesh` → call it.

Compile. **The Branch is the whole point**: `ResolveMesh` only runs when the
tier actually changed. Measured, that is the difference between 295 ms and
1.1 ms across 500 parcels.

### 7. Try it

Drag **BP_Parcel** from the Content Browser into the level. In **Details** set:

    Catalogue   DA_Catalogue
    RecipeId    cottage
    Tier        0
    WidthUU     820

Nothing appears yet — `ResolveMesh` has not run. Press **Play**, then stop.
Or set **Tier** to 2 and press Play again: the extended house rather than the
cabin. Same house, grown, one pointer swap.

### If something does not match

- **No `Cast to BP_BuildingCatalogue` in the menu** — compile
  `BP_BuildingCatalogue` first.
- **A pin will not connect** — the types differ. Unreal usually inserts a
  converter automatically; if it refuses, the wrong node was picked.
- **`Find` offers several versions** — you want the one whose target is a Map.
- Tell me what the screen actually says. These node names come from the API;
  the menu wording in 5.8 I have not seen.

## The per-model gate and the stamp — 25 Aug 2026

**Baking destroys the thing the invariant suite measures.** Every rule in
`invariants.py` reads a level snapshot and counts *components*; `DETAIL-01`
asks whether a building carries 0.70 parts per m² of elevation by counting
boxes. Merge that building and it becomes **one component** — the rule does
not fail, it silently stops having an opinion, which is worse. A catalogue of
baked meshes cannot be checked the way the sandbox city is.

So the check moved to the only moment it can see anything: after the roles are
bound, before the merge.

    build alone off-board  ->  bind roles  ->  GATE  ->  merge  ->  STAMP

`modelgate.py` holds six rules as pure functions with known-answer self-tests
that run FIRST, exactly as the suite does. Thresholds come from the new
`qc.py`, which both it and `invariants.py` import — **a gate that passed a
model the suite would fail is worse than no gate**, and two copies of `0.70`
is how that happens.

| rule | asks |
|---|---|
| `GATE-01` | every component carries a role from `labels.ROLES` |
| `GATE-02` | no component sits on a default or missing material |
| `GATE-03` | ≥0.70 parts per m² of elevation — **building components only** |
| `GATE-04` | ≥4 distinct materials |
| `GATE-05` | the model fits the parcel it is baked for |
| `GATE-06` | no component auto-renamed by a name collision |

`GATE-03` counts `BLD2_`/`ELEV_` and ignores `PLOT_`, because `DETAIL-01`
draws the line there. Counting garden furniture toward elevation density would
let a thin building pass the gate and fail the suite the moment it was placed;
a self-test asserts a thin model stays failed with sixty fence posts added.

**The stamp.** `stamp.py` writes the verdict onto the baked asset as metadata
(`Stacktown.Gate`, `.Parts`, `.Materials`, `.Density`, `.SpanX/Y`, `.Recipe`,
`.Tier`, `.Width`, `.Stamped`) and reads it back before reporting success. A
mesh is then **evidence rather than an assurance**, and `catalogue_audit.py`
reports an unstamped mesh as UNVERIFIED rather than assuming it is fine.

`bake_catalogue.py` refuses to bake a model that fails the gate. `--force`
bakes anyway and stamps `Gate=FAIL` rather than lying.

### What it caught on its first working run

`cottage` tier 2 measured **842 uu wide inside an 820 uu parcel** — the garage
roof oversails 16 uu either side and was never clamped to the lot. In the city
that overhang lands in a garden and `check_block` passes; baked into a
catalogue mesh it is a parcel 22 uu into its neighbour. Clamped in
`build_house`; now 819.

### Catalogue state

    asset                    gate  tier          parts mats  per m2  span x
    SM_Bld_cottage_t0_w820   PASS  cabin           106    6    6.46     818
    SM_Bld_cottage_t1_w820   PASS  house           144    6    4.50     818
    SM_Bld_cottage_t2_w820   PASS  extended        166    6    5.19     819
    SM_Bld_walkup_t0_w1420   PASS  two-storey      191    5    2.59    1418
    SM_Bld_walkup_t1_w1420   PASS  three-storey    288    5    2.73    1418
    SM_Bld_walkup_t2_w1420   PASS  four-storey     385    5    2.80    1418

    6 stamped, 0 unverified, 0 gate-failed, 0 missing
