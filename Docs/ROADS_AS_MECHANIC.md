# Roads as a player mechanic — a research board

**Status: RESEARCH, WITH FOUR DECISIONS TAKEN.** Nothing here is built and no
engine work is authorized. The owner answered all four open questions on
2026-09-01; they are recorded in section 6 and threaded into the sections
they change. What remains open is everything section 6 does not name. Written by the direction-B lane on the owner's
assignment, 2026-09-01; the mechanics and data-model sections are for the
beta lane's co-authorship once their board ships.

**The owner's brief, near-verbatim.** Roads must be a mechanic, not an
emergent side effect — "it shouldn't just be where a player puts a building
down and the road appears... it also shouldn't be a bland 'drop a grid of
road'". The player DRAWS roads that CURVE, SELECTS ROAD TYPES ("dirt road,
paved avenue, tree lined boulevard, highway as some examples"), and can LIFT
roads into BRIDGES over other roads and rivers. "This is a mechanic that is
very common in city building games and matches the natural shape of the city
references i've supplied where its not just a never ending grid of
intersections."

**The twin rule applies: ONE mechanic, TWO art languages.** The data model is
shared; only the fabrication forks.

---

## 0. The finding this study turned on

The engineering constraint and the art direction **agree**, and that is not
a coincidence worth wasting.

A curved road cannot give a building a curved frontage — our buildings are
baked meshes at five fixed widths. So a curved street must be served by
STRAIGHT CHORDS: a polyline whose segments are quantized, with the curve
living in the road ribbon and the joints between lots.

That sounds like a compromise until you read B3 again: the reference board
"reads as MANY FITTED INLAY PIECES making the landscape; that visible pieced
construction is part of the look." **A curve assembled from fitted straight
pieces is not our workaround for a planning model — it is how planning models
are actually made.** The seams are the aesthetic.

Everything below follows from that.

---

## 1. Mechanic shape

### 1.1 How the genre does it, and which part matters

Three families, and they differ in what the player's hand does:

- **Node-and-segment** (SimCity 4, Cities: Skylines' straight/curve tools):
  click a start, click an end, the tool fits a segment. Curves come from a
  third control point or from a "curve" mode. Precise, forgiving, and the
  segment is an OBJECT with endpoints — which is what makes intersections
  tractable.
- **Freehand-then-smooth** (Skylines' freeform, Cities XL): drag a path, the
  system fits a spline afterwards. Expressive, and it produces geometry
  nobody chose — the smoothing is where the player's intent goes to die.
- **Spline-with-handles** (Anno's roads, most editors): a full bezier with
  draggable tangents. Maximum control, maximum cursor.

**What matters for us is not which is prettiest but which survives our
camera**, and that is decided in 1.2.

### 1.2 THE CONSTRAINT NOBODY CAN DESIGN AROUND: we have no cursor

`Docs/CAMERA_DESIGN.md` is explicit that **focus IS selection**: "Select a
parcel → the lens racks to it... What is in focus is what is selected; what
is selected is what the game describes." The player's instrument is a boom
and a focus pull, not a pointer on a plane.

Every road tool in the genre assumes a cursor dragging across a map. **Ours
cannot, without abandoning the camera the project has already locked.**

That is a hard constraint and it should be stated before any tool is
designed, because it eliminates freehand entirely: you cannot drag a path
with a lens.

**What the camera CAN do is aim.** The boom's look-point is already a point
on the board that the player moves continuously and precisely — it is the
thing focus racks to. So:

> **PROPOSAL: the boom is the pen. The look-point is where the road goes.**
> The player aims, commits a node, aims again, commits the next. The road is
> laid node by node, and the curve is fitted through the committed nodes.

This is node-and-segment, chosen because it is the only family that fits the
camera we have — and it happens to be the family that also makes
intersections tractable. The constraint is doing us a favour.

### DECIDED, 2026-09-01: a CURSOR, in road mode only

**The owner chose against this study's recommendation.** A pointer appears on
the board plane while roads are being drawn; the camera and focus-as-selection
are untouched everywhere else in the game.

Recorded as what it is: a deliberate trade of purity for precision. The
boom-as-pen was the more distinctive answer and this lane argued for it; the
owner weighed distinctiveness against the accuracy a player needs when placing
a road they will live with, and bought the accuracy.

**It also simplifies v0**, which is worth saying plainly rather than sulking
about the recommendation. The input path becomes a conventional
cursor-projected-onto-board hit test instead of a look-point commit gesture,
and hit-testing under a pointer is a solved problem in a way that "commit the
thing the lens is racked to" is not. The cost is one new UI element - the
game's first - and the discipline that it must appear ONLY in road mode, or
it becomes the pointer this camera was designed to avoid.

**What survives from 1.2's analysis:** node-and-segment is still the family,
and still the right one - it was chosen for intersection tractability as much
as for the camera, and the cursor does not change that. Freehand remains a bad
fit, now for a design reason rather than an input one: a smoothed freehand
path produces geometry nobody chose, and this board's lots must land on a 410
quantum.

### 1.3 Road types as a palette

The owner named four: dirt road, paved avenue, tree-lined boulevard,
highway. Read as a hierarchy, they are not four skins — they differ in
**width, speed, capacity and what they permit at their edges**:

| type | carriageway | footway | frontage? | notes |
|---|---|---|---|---|
| dirt | narrow | none | yes | the cheapest thing that reaches a plot |
| paved avenue | 1400 (today's `ROAD_W`) | 430 each side | yes | the current street, exactly |
| tree-lined boulevard | 1400 + median | 430 + planting | yes | the median is the identity |
| highway | wide | none | **no** | frontage-refusing: this is its mechanic |

**DECIDED, 2026-09-01: road types are MECHANICS, not skins.** Choosing a type
is a planning decision. The highway refuses frontage; the palette is four
mechanics with four different consequences for what can be built where.

**The mechanically interesting one is the highway, because it REFUSES
frontage.** A road nothing can face is a different object from a street, and
it is the reason bridges exist in the brief: a highway wants to cross the
city rather than serve it.

Today's `city.py` already encodes a two-level hierarchy — `ROAD_W` 1400 with
430 footways, and `SERV_ROAD_W` 900 with 250 — so the *idea* of road classes
already exists in the numbers. It has never been a player-facing choice.

### 1.4 Elevation and bridges

Bridges are the third verb and the most expensive. Minimum viable version:
a road segment carries a **height at each node**, and a segment whose height
clears another segment's by more than a threshold is a bridge; the system
inserts an abutment and a deck. Grade limits fall out (a segment whose slope
exceeds the type's maximum is refused).

B3 already makes **terraforming and water-laying BUILD VERBS**, so the
elevation axis is not foreign to the design — it is the same axis the player
already carves terrain on. A bridge over a river is the intersection of two
verbs the owner has already locked.

---

## 2. Fabrication language, per product

One mechanic; the look forks. This is where direction B has an advantage,
because its references already contain drawn curving roads.

### 2.1 Direction B — the wooden board

B1: roads are **etched flat**. B3: **carved freeway ribbons** and a
**green-stained wood-inlay river**, on a board of **many fitted inlay
pieces**.

So a drawn road on a wooden board is an **INLAY RIBBON**: a shallow channel
routed into the board and filled with a piece of stained timber cut to fit.
Its fabrication vocabulary, in the language this lane already uses:

- **the groove** — the road sits slightly BELOW the board surface, because a
  router cuts down. This also solves a real problem: `D13` measured that
  roads must read BRIGHTER than buildings (+50%), and a recessed pale ribbon
  against warm blocks does that without lighting tricks.
- **the pieces** — a curve is assembled from fitted segments and the joints
  SHOW. Per B3 that visible piecing is part of the look, so segment joints
  are an asset rather than an artefact to hide.
- **type = stock** — `road_inlay` is already a declared timber stock (D10,
  D11), stained but keeping its grain. Four road types become four stains of
  one stock, not four materials: dirt is bare unstained board, avenue is the
  current inlay, boulevard adds a planted median strip, highway is a wider
  ribbon in a darker stain.
- **the bridge** — a raised timber ribbon on small piers, which on a real
  planning model is exactly what a modelled flyover is: a separate carved
  piece standing proud of the board.

### 2.2 Flagship — the card board

Not this lane's to specify, and deliberately left thin: roads are etched or
printed on the card board rather than routed into timber, so the same data
model expresses as a printed surface with painted markings. Named here only
to hold the seam open. **The flagship lane owns this section.**

### 2.3 What must be shared

The DATA MODEL: nodes, segments, type, elevation, and the intersection graph.
Both products must agree on what a road IS, or the twin stops being a twin.
Only the MESHING and the MATERIAL fork.

---

## 3. Engine shape — survey only, no recommendation to build

- **Spline components / spline mesh components** are UE's native answer and
  the obvious candidate: a `USplineComponent` carries the node list, and
  `USplineMeshComponent` deforms a segment mesh along each span. Curving
  ribbons are what they are for.
- **But deformation fights our fabrication.** A spline mesh BENDS a mesh
  along a curve; an inlay ribbon is CUT and FITTED. A bent timber piece is a
  different object from a routed groove, and at board range the difference is
  visible — bending is how you get a road that looks extruded rather than
  inlaid. **Straight segment meshes placed along a fitted polyline are closer
  to the fabrication than a deformed spline mesh**, and cheaper.
- **Instancing** carries the count: several hundred segments of a handful of
  meshes is the same problem density solved for buildings.

### 3.1 THE COLLISION, named and not solved

`citylayout.py` is a hard-coded four-quadrant grid: `BLOCK_LEN = 4920`,
`BLOCK_DEPTH = 1500`, four fixed `PARTITIONS`, and lots derived from them.
Drawn roads delete the premise that block envelopes are known constants.

**But the deeper collision is not the grid — it is the QUANTUM.**

`WIDTH_QUANTUM = 410`, and the catalogue is baked at 820/1230/1640/2050/2460,
i.e. 410 x {2,3,4,5,6}. citylayout's own comment records what happens when
this is violated: a block length that is not a multiple of 410 "cannot be
tiled by catalogue buildings at all", and the first attempt produced 800-wide
lots that "NOTHING IN THE CATALOGUE FITS".

A curved road produces **continuously varying frontage**. The catalogue has
**five widths**. These cannot be reconciled by any amount of spline work:

- widening the catalogue to a continuous width axis is impossible — each
  width is a separate BAKE, and width restructures the model (street.py
  measured 1640 -> 2050 restructuring 322 parts).
- so the frontage must stay quantized, which means **lots are straight
  chords along a curving road**, and the road's curve is absorbed by the
  ribbon and by wedge-shaped gaps at the joints.

Per section 0, that is also what the reference looks like. **The constraint
and the art direction agree.**

**DECIDED, 2026-09-01: the wedge gaps ARE THE LOOK.** The owner ruled
that the gaps between chord-lots read as B3's fitted piecing, so the 410
quantum collision is officially a FEATURE rather than a defect to hide.
Greenery and inlay may dress the wedges.

That converts the hardest constraint in this study into an art direction:
the chord-lot generator is not a fallback, it is the intended fabrication.
Design the wedges; do not minimise them.

`DISTRICT_PLACER_CONTRACT` and seam 6's parcel model both assume the grid.
Naming the collision, per the brief; not solving it here.

---

## 4. What it displaces — honest notes

| machinery | fate |
|---|---|
| `citylayout.py` block/lot grid | **dies** as a source of truth; **survives as the starter preset** - decided 2026-09-01, new game offers EITHER an empty board or the 14-lot preset |
| `city.py` `ROAD_W`/`WALK_W`/`CORRIDOR` | **survives and is promoted** — these become the paved-avenue road TYPE's parameters, and the numbers are already right |
| `SERV_ROAD_W` 900 / `SERV_WALK` 250 | **survives** as a second type; the hierarchy already exists in the constants |
| `street.py` | **adapts** — it builds one street for a gate, and its `vary_repeats` placement rule is about lot width, which outlives the grid |
| `road_inlay` stock (D10/D11) | **survives and grows** into the type palette (four stains of one stock) |
| `testcity_pins` | **survives** — it pins by IDENTITY, not by geometry, which is exactly why it was built that way |
| `parcels.py` / `parcelmeta.py` ids | **at risk** — re-placing lots "retires parcel ids and mints new ones under the contract"; the cost is recorded and real |
| the 410 quantum | **survives, and constrains everything** |

---

## 5. Recommended v0 — the smallest drawable curving road

**Goal: the owner draws one curving road and a building faces it.** Nothing
else.

1. **One road type only** — the paved avenue, using `city.py`'s existing
   1400 + 2x430. No palette yet; a palette with one entry proves nothing and
   costs a UI.
2. **Node-and-segment with a CURSOR** (owner's decision, 2026-09-01). A
   pointer projected onto the board plane while road mode is active; click a
   node, click the next. Three or four nodes. A Catmull-Rom through the
   committed nodes, sampled to a polyline at the 410 quantum.
3. **The ribbon is straight segment pieces on that polyline** — inlay
   language, joints visible, no spline deformation.
4. **Lots are chords**, quantized to 410, generated along one side only.
5. **No elevation, no bridges, no intersections.** A single open-ended road.
   Intersections are the expensive half of every road system in the genre
   and they are not needed to answer the question.

**What v0 answers:** does drawing with the boom feel like a mechanic or like
fighting the camera? That is the one thing no amount of study settles, and
it is answerable with a single road.

**What v0 deliberately does not answer:** intersections, junction geometry,
traffic, elevation, road types, or how the placer survives. All are real and
all wait for the owner's verdict on the feel.

**Cost honesty:** v0 is not small. It needs a road-mode input path, a cursor
projected onto the board plane, a polyline fitter, a segment mesher and a
chord-lot generator. It is the smallest thing that answers the question, which
is not the same as being cheap.

**The cursor decision moved the question v0 answers.** It was "does drawing
with the boom feel like a mechanic or like fighting the camera" - a question
about our camera. With a conventional pointer that risk is largely bought
off, so v0 now answers a different and more ordinary one: **does a drawn
curving road, served by quantized chord-lots with dressed wedges, read as a
wooden planning model?** That is a LOOK question rather than a feel question,
which suits this lane and makes the frames the deliverable.

---

## 6. Decisions — owner, 2026-09-01

All four open questions answered. Recorded as decisions; the sections above
are amended to match.

1. **THE PEN: a cursor, in road mode only.** Against this study's
   recommendation of boom-as-pen. A deliberate trade of purity for precision,
   and it simplifies v0's input path while adding the game's first UI element.
   Discipline attached: the cursor exists ONLY in road mode.
2. **ROAD TYPES ARE MECHANICS.** The highway refuses frontage. Choosing a
   type is a planning decision, not a skin. Four mechanics, not four looks.
3. **THE WEDGE GAPS ARE THE LOOK.** Fitted piecing, B3's own language. The
   410 quantum collision is a FEATURE. Greenery and inlay may dress the
   wedges. Design them; do not minimise them.
4. **GAME START: BOTH.** A new game offers an empty board - draw the first
   road yourself - or the starter preset. The 14-lot board survives as that
   preset.

### What these four settle, and what they do not

They settle the SHAPE: a cursor-drawn, node-and-segment road system with a
four-mechanic type palette, chord-lots whose wedges are dressed rather than
hidden, and two ways to begin a game.

They do not settle: intersections and junction geometry, elevation and
bridges beyond section 1.4's sketch, traffic or capacity, how
`DISTRICT_PLACER_CONTRACT` and seam 6's parcel model survive the loss of the
grid, or what the flagship's fabrication of a drawn road is. Sections 1 and 3
go to the beta lane for co-authorship of the mechanic shape and the shared
data model once their board ships.

**No build authorization exists.** v0 needs its own declaration, and the
owner reads this amended study before any engine work begins.

### The insight that survived all four answers

Spline meshes BEND a mesh along a curve; an inlay ribbon is CUT and FITTED.
Straight segment meshes on a fitted polyline are closer to the fabrication and
cheaper, and none of the four decisions touches that. It anchors the v0 mesh
approach for direction B.
