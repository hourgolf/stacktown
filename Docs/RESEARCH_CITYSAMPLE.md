# Research: Epic's City Sample — what it is, how it works, what to lift

**Owner assignment, 2026-08-30.** Fab listing 4898e707 in the owner's
library = Epic's **City Sample** (the "Matrix Awakens" city). Research
from public documentation; nothing downloaded, imported, or enabled.

## The one correction up front

City Sample has **no city-building gameplay**. It is an exploration demo
(walk / drive / drone) over a finished city. Everything "city-building"
about it happens at **editor time**, in its procedural generation
pipeline. That pipeline — and the runtime population systems — are where
the liftable ideas live.

## How the city gets built (two generations of the pipeline)

**Original (Houdini):** designer draws city shape + road network →
Houdini generates districts, lots, freeway, building volumes (shape
grammar over volumes, ~Chicago/NY/SF styles) → exports a giant **point
cloud with metadata** → UE's **Rule Processor** maps points to mesh
instances via rules. Traffic lanes, parking spots, traffic lights,
intersections, even ambient-audio zones ship as attributes in that same
point cloud.

**Remake (native PCG, UE 5.8):** the same city rebuilt as **18
interdependent PCG graphs** inside the engine — splines define terrain,
arterials, districts; a shape-grammar-over-splines primitive
(grammar-string data assets, 28 building styles, one grammar engine)
assembles buildings from kit meshes; strict stage ordering
(foundation → landmarks → layout → details → polish), infinitely
regenerable.

## How the city lives at runtime

- **ZoneGraph**: lightweight lane corridors (roads, sidewalks) with
  tags — generated from the same point-cloud metadata.
- **Mass Entity (ECS)**: thousands of agents. Crowds run **StateTree**
  behaviors + **SmartObjects**; traffic runs **MassTraffic** (
  intersections, lights, lane changes, parked-car pool). Spawn points
  come from generation metadata.
- **Presentation**: World Partition + OFPA + Data Layers + HLOD;
  Nanite/Lumen/VSM/TSR; photo mode; day/night toggle; **Soundscape**
  ambience driven by spatial "ColorPoint" metadata from generation.

## The lift list (ranked for Stacktown)

1. **The metadata-emission pattern** — their single biggest idea: one
   generation pass emits data for MANY downstream consumers (meshes,
   traffic, parking, audio, spawn). Stacktown's stamps/provenance
   already do the QC half; the DISTRICT PLACER should emit the gameplay
   half — per-parcel economy hooks, practical-light anchors, camera
   POIs/setups, parking/route points, ambience zones. Cheap to design
   in now, expensive to retrofit.
2. **CityTick traffic (concept only)** — the model-railway fiction
   supports MOVING VEHICLES (canon slot 1 is a model railroad). Their
   MassTraffic is heavy C++; the diorama-honest version is stop-motion:
   resin cars REPOSITION on discrete CityTicks between parking points
   emitted by the placer — pops, like building growth, "a craftsman's
   hand between exposures." Near-zero runtime cost, no new plugins, no
   C++.
3. **Roads-first layout grammar** — their layout order (arterials →
   districts → lots → buildings) matches and validates the planned
   district placer; their strict stage-dependency ordering mirrors our
   sweep/wave discipline. Steal the staging, keep our generator.
4. **Soundscape-by-zone** — ambience selected by generation metadata;
   for us: room tone + zone character from placer data when audio
   starts. Pairs with the camera doc's foley plans.
5. **Shape grammar as data** — 28 styles over one grammar engine =
   validation of recipes-as-data over genbuild. Nothing to adopt;
   genbuild is already this, with fabrication honesty theirs lacks.

## The do-not-lift list

- **PCG framework**: their modern path is PCG-native; PCG is
  deliberately OFF in Stacktown (AGENTS.md). Nothing above requires it
  — genbuild already plays the shape-grammar role in gated Python. The
  doctrine stands unless the owner reopens it; this research found no
  need to.
- **Nanite kit assets / MetaHuman crowds**: wrong fabrication tier
  (photoreal detail beside card kills the miniature read) and moving
  PEOPLE break the model fiction where moving cars do not. Also the
  Mac: 64 GB / RTX-class recommended; our machine's MetalRHI is the
  documented instability.
- **Importing the project into this repo**: never — ~100 GB, the
  Uniblocks sweep-in lesson at 30×. If code study is ever wanted, open
  Small City in a SEPARATE scratch project (M2+ Nanite works under SM6
  since 5.5), never inside Stacktown.

## Decisions this puts to the owner

1. Adopt metadata-emission as a district-placer requirement (rec: yes).
2. Prototype CityTick stop-motion traffic after economy notes land
   (rec: yes, it is the "living" in living diorama).
3. PCG doctrine: unchanged (rec: reaffirm; nothing here needs it).

## Sources

- Fab listing (City Sample) · Epic docs: "City Sample Project UE
  Demonstration", "City Sample Quick Start (city + freeway)", "City
  Sample PCG for Unreal Engine" · community: MassSample (Megafunk),
  MassTraffic extraction (Myxcil), vrealmatic Mass/crowd notes,
  SideFX procedural-city material, UE-on-Mac feature-parity tech blog.
