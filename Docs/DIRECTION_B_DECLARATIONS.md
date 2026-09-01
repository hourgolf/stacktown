# Direction B — the lane's declaration ledger

Declare before geometry (DIRECTION_B_LANE.md contract 3). Every entry here
precedes the wooden mesh it governs, states what "good" means for it, and
names what it CANNOT do — a declaration that only lists wins is an opinion.

Comparison set: `Docs/DIRECTION_B.md` and nothing else. Never citable for
flagship work; flagship canon is never cited here.

---

## D1 — Patina is MATERIAL-level. Decided 2026-08-31.

The charter's open question, flagged by the flagship design lane at handover:
*is patina-as-time GENERATOR-level or MATERIAL-level?* The coordinator's
recorded lean was material-level, to be argued not assumed. It is argued
below, and it lands on material-level for a **mechanical** reason the lean
did not name, and with **two refinements that change what gets built**.

### The verdict in one line

**Age is a per-parcel runtime scalar the wooden shader reads. It never
reaches the generator, and it must never reach the catalogue key.**

### Why not generator-level — the receipt, not the taste

The decisive argument is not aesthetic. It is that generator-level patina
breaks the one mechanism the entire beta twin rests on.

1. **A box's only material channel is its NAME.** `genbuild.box()` and
   `slab()` emit `dict(kind, actor, name, c, d, r)` — no material field
   (`genbuild.py:152`, `:231`). Material is derived downstream from the role
   prefix: `rolemap.material_for()` maps `Wall_*` to the **lot spec's `wall`
   value** (`rolemap.py:163`). So a generator-level patina can only be
   expressed as a different `wall=` value, or a differently-named box.

2. **`wall=` is resolved at BAKE time.** `fastbake.py:107` reads
   `e.get('mat') or rolemap.material_for(e['name'], ...)` and freezes the
   result into the asset's `static_materials`. A building leaves the bake as
   **one static mesh with N fixed slots** (RUNTIME_SLICE.md: "Baked, a
   building is one component"). Generator-level age is therefore **baked-in
   age**: one mesh per age step.

3. **Which makes age a catalogue-key component — and that is the break.**
   `MeshByKey`'s key is `recipe_tier`, with no width component
   (`mk_da_catalogue.py` docstring). Two parcels at the same recipe, tier and
   width but different ages would need different meshes, so the key would
   have to grow to `recipe_tier_age`. **Phase A's proven pointer is the only
   machinery the wooden catalogue depends on** (charter, staffing revision).
   Generator-level patina is the first thing that would un-prove it.

4. **And it multiplies the bake the bake policy exists to stop.** The honest
   catalogue is 530/548 baked (POLISH_PROTOCOL, standing instruments). Four
   age steps is a 4x bake; the policy's whole point is that baking is needed
   to SEE a fix, never to FIND one, and that the scarce resource is the
   editor window, not compute (16 min per 156 models).

5. **It also spends a visual event that is already spoken for.** Tier growth
   is a stop-motion pop (growth doctrine). Quantised age would pop the same
   way. At board range a building that popped because it GREW and one that
   popped because it AGED are indistinguishable — two meanings on one event.

6. **The project's own instrument agrees, and can be made to say so.** The
   lever diff (POLISH_PROTOCOL, standing instruments) is the arbiter for any
   proposed variation lever: emit the geometry twice and diff it. **Stated as
   a falsifiable prediction: run the lever diff on age and it moves 0 parts.**
   A lever that moves 0 parts is not a generator lever — that is precisely
   the finding that killed the per-parcel-seed plan (seed: 2 parts, 0
   visibly; width: 322). If anyone reopens this, that is the command to run,
   and this paragraph is the pre-registered expected answer.

### Why material-level is not merely the leftover option

7. **It is structurally outside the byte-identical instrument's field of
   view.** `genbuild_identity.py` hashes SINK RECORDS. Boxes carry no
   material. A patina that lives in the wooden MI instances and a per-instance
   scalar **cannot** move the manifest — not "trivially clean" as the lean
   put it, but *impossible to dirty by construction*. The converse is the
   real exposure: generator-level patina must touch box names or spec `wall`
   values, i.e. it lands squarely inside a contract that currently **cannot
   be certified**, because the flagship lane that certifies phase-F-class
   generator changes is on break.

8. **It is what the reference actually locks.** ~~B3 locks a colour journey
   through the material's own range.~~ **CORRECTED BY D3 (owner, 2026-08-31):
   age is a WEAR journey, not a colour one.** Tone belongs to timber identity;
   age reads through sheen, edge polish and grain contrast. The mechanism
   argument in 1-7 is untouched by this — it was never about colour — and D3
   makes it *cheaper*, because the wear it now drives is a curvature proxy
   that is already built into the master. See D3.

9. **Its one hard constraint is correct for this direction and would be wrong
   for the flagship.** A per-component scalar ages every slot of a building
   together. For a carved timber mass — one piece of wood — that is right. On
   a flagship building (painted wall, concrete base, glass) it would be
   nonsense. The mechanism fits direction B specifically.

### Refinement 1 — Custom Primitive Data, NOT dynamic material instances

The lean said "a per-instance age scalar". Per-instance is right; the
mechanism matters and has a measurable cost:

- **Dynamic material instances**: `BP_Parcel.Building` is one component with
  N slots, so a MID per slot per parcel is ~500 x N allocations at the
  declared 500-building budget, and it breaks static batching. That lands
  directly on the number RUNTIME_SLICE.md committed to ("500 placed buildings
  before frame time moves").
- **Custom Primitive Data**: one float on the component, read in the material
  by index. No MID, no batching break, and it survives `SetStaticMesh` — which
  matters, because a tier-up swaps the mesh on that very component.

**Custom Primitive Data is the declared mechanism.**

**Held as unverified until called.** This project has a precedent that makes
asserting an unused API a documented failure: `add_static_mesh` was called on
every live build for weeks and **never existed on any toolset**, its response
discarded, models stamped PASS regardless (`genbuild.py:272` note; POLISH
BACKLOG S11). So: the CPD float budget, the read node, and CPD survival across
`SetStaticMesh` are each **to be verified by calling them in this engine build
before anything is designed on top of them**. No number is written here that
has not been measured.

#### Verification, read-only editor window 2026-08-31 — 2 of 3 closed

**THE READ NODE — CLOSED, and the declaration above was WRONG in a useful
direction.** There is no dedicated Custom Primitive Data material expression:
`search_subclasses(MaterialExpression, "PrimitiveData")` returned **empty**.
The empty was not trusted on its own — a known-answer control (the same search
for `"ScalarParameter"`, which returned
`MaterialExpressionScalarParameter`) proved the search works, so the empty is
a real absence and not a broken instrument.

The mechanism is a **flag on ScalarParameter**, confirmed by reflection:

    bUseCustomPrimitiveData   bool   "True if this parameter value provided
                                      by custom data on the primitive."
    primitiveDataIndex        int    "The slot index for custom primitive data."

**This is better than a dedicated node.** An existing master scalar parameter
becomes CPD-driven by flipping a flag: the material's existing parameter
surface is reused, no graph surgery, no new expression class, and any instance
not supplying CPD falls back to the parameter's own default for free.

**THE FLOAT BUDGET — STILL OPEN, deliberately.** `customPrimitiveData` exists
on `PrimitiveComponent` as `{"data": [number]}` and the reflection schema
declares **no maximum**; `primitiveDataIndex` likewise has `minimum: 0` and no
maximum. The engine's real cap is a compile-time constant this interface does
not expose. A number is not written here, because the whole point of the
`add_static_mesh` precedent is that a confident unmeasured number is worse
than an admitted gap. It closes in the scratch-actor window.

**A NUANCE THE SCHEMA GAVE UP, and it matters to the tick.** The property's
own description is "Optional user defined **default values** for the custom
primitive data of this primitive" — that is the *editor-set defaults* array,
which is NOT the same thing as the runtime per-component values a
`SetCustomPrimitiveDataFloat` call writes. Age is a runtime quantity; the two
must not be conflated when the tick drives it.

**SURVIVES `SetStaticMesh` — STILL OPEN.** Needs a live component and a
mutation; out of scope for a read-only window. Closes in the same
scratch-actor window: spawn, write CPD, `SetStaticMesh`, read back, destroy.

### Refinement 2 — declare the per-instance channel map NOW

Patina is not the only thing that wants a per-instance channel. B4's night
glow carries **ownership AND activity AND selection** through subtle hue and
colour temperature. If patina silently claims float 0 and glow retrofits
later, that is the two-copies-of-one-table drift this project is bitten by
"roughly once a session" (rolemap.py docstring). Proposed layout, decided
here so it is decided once:

    0   Age          0..1   unworn -> handled: edge polish, sheen, grain
                           contrast. NOT colour - see D3
    1   GlowLevel    0..1   night window emission, 0 = daytime carved mass
    2   GlowState    0..1   encoded hue: green positive / red negative / other
    3   Selection    0..1   the selection ring, SEPARATE from GlowState so
                           selecting a failing building never recolours its
                           state
    4-7 reserved

**Why Selection is its own channel and not a GlowState value:** B4 makes glow
carry three things at once. Ownership, activity and selection can be true
simultaneously and must be able to disagree. Folding selection into the state
hue means selecting a red building either hides the red or hides the
selection.

**One authority, double-entry.** The map lives in ONE Python module and the
material's parameter names are checked against it by a self-test that reads
the names back from the asset — the `archetypes.py` double-entry pattern, and
the `cvar.py` read-back rule ("state changes prove themselves by READ-BACK,
never by printing intent"). Not a comment in two files.

### What this declaration does NOT cover, named so it is not assumed

- **Age is not the white "proposed building" block.** B2's white block is a
  PARKED IDEA and, if it lands, it is a **different catalogue entry** — an
  undeveloped massing resolved by the existing pointer. Two different
  mechanisms both look like "a pale building"; conflating them later would be
  a mess, so they are separated now. Age 0 is a real building, freshly cut.
- **Age is not the board's inlay.** B3's "many fitted inlay pieces" is BOARD
  construction (water, terrain, carved ribbons) and is deferred by the
  charter until the owner has judged the first board. When it arrives it is a
  board question, not a building-patina question.
- **Material-level age cannot change silhouette.** No literally sharper
  arrises on a fresh piece, no checking or cupping at the end grain. The
  original justification here (that freshness reads as TONE, so relief does
  not matter) was **voided by D3**, which put age onto the wear axis. The
  replacement justification is stronger, not weaker: direction B's masses are
  generated axis-aligned boxes with **40 mm 45-degree chamfers**, which is the
  exact geometry class the master's existing curvature proxy works on, so
  edge wear is *simulated at the chamfer that is already there* rather than
  needing new geometry. If relief-by-normal is ever added on top, it is swept
  for AMPLITUDE on a BUILDING, never on the flat study wall (POLISH_PROTOCOL:
  "the flat slab hides amplitude entirely").

### The interaction with growth, which falls out of B3 and is a design win

B3: "new **and upgraded** buildings start pale". Upgraded. So:

**A tier-up sets Age := 0.**

Growth makes a building visibly fresh again, and it then ages back into the
board. That is exactly what the reference photograph shows — "visibly fresher
blocks where the model was **updated** over years". Freshness marks recent
change. Age and tier are therefore coupled, in the simplest possible
direction, and the coupling is the mechanic rather than a bug to defend
against. **Unchanged by D3** — only the channel freshness is expressed in
changed, from tone to wear. A freshly grown building is a freshly *cut* one.

### What "good" means for patina, so it can be judged

**Revised under D3: every criterion below is about WEAR, not tone.**

1. At any single moment the board shows a **range of handling**, not a uniform
   finish — the B3 read is fresh blocks *against* a worked field.
2. The journey is **legible at board range** (B2's framing) without being
   readable as an animation. Time made visible, not a surface cycling.
3. A freshly-grown building is **noticeable but not loud**: it is the
   crispest thing in its neighbourhood and it is still the same timber. "The
   key is subtlety" (owner, B4) governs here too.
4. It must survive the night frame: an unworn building at midnight is still
   the same wood under glow, distinguished by its edges, not by its colour.
5. **It must not read as dirt.** Age on a cherished planning model is
   handling, polish and softened arrises — the patina of something looked
   after. It is never grime, and grime is the failure state to watch for the
   moment wear amplitude goes up.

Acceptance happens **on buildings, in a frame, at the show camera**, never on
a study wall (POLISH_PROTOCOL: attribution and acceptance are different jobs
on different surfaces), and no agent's opinion — including this one's —
settles it.

---

## D2 — the wood material family. Declared 2026-08-31.

First Commission item (1). Declared before any wooden mesh, per contract 3.

### The best news in the lane: nothing new is needed

**Direction B's entire city is TWO stocks that already exist**
(`fabrication.py:86-87`):

    chipboard   tooth 0.004  amount 2.6  rough 0.70-0.88   "the base board"
    basswood    tooth 0.020  amount 1.6  rough 0.48-0.64   "carved + sanded timber"

and they are already wired to materials that exist: `MI_model_board` ->
chipboard, `MI_wood` -> basswood (`fabrication.py:200-201`).

So the wooden city needs, in full:

- **no second master** — prohibited by MASTER_MATERIAL_SPEC, and not wanted;
- **no new stock** — the vocabulary's own admission rule is "a stock exists
  iff a modelmaker would reach for a different material", and carved timber
  and the board are already the two they would reach for;
- **no new role prefix, and no `labels.ROLES` change** — `Wall_` resolves
  through the lot spec's `wall` value (`rolemap.py:163`), so a wooden
  building is a normal building whose spec names a wood MI. **NAME-01 is
  untouched and `rolemap` is untouched.**

The family is therefore a set of **MI instances of the existing master**,
named in wooden recipe specs — structurally identical to how the district
palette works today (`MI_dist_*` all share one stock, differing in colour).

### THE FINDING: the wooden city currently has paper grain

`basswood` and `chipboard` are both declared with `normal=None`
(`fabrication.py:86-87`). `normal=None` does not mean "no map" — it means
**the master's default paper**, which `apply_stocks.py:92` names in its own
output as `T_PaperNormal`. Both stocks wear a **cardstock weave**.

B1's material lock is **"grain as the surface."**

So the two stocks direction B is entirely built from currently carry the one
surface the direction is defined against. This is **cold read #1's finding one
level down**: "everything has the same paper texture" was literal then, and it
is literally true of timber now.

**The asymmetry that makes this the lane's item and not the flagship's.** On
the flagship, basswood is decking, planters and pergolas — a minor surface, no
one has had reason to look. On direction B it is *every building in the city*.
Direction B is what makes it urgent, and because the fix is a stock property
rather than a per-model one, **fixing it improves the flagship for free** —
the polish doctrine's whole economic argument, arriving unprompted.

### FAB-FIRST: the survey is done, before anything is proposed

The rule (MASTER_MATERIAL_SPEC, owner 2026-08-28) is "prove nothing installed
serves" before generating — written after a value-noise generator's
axis-aligned lattice artifact survived six tuning attempts and lost to the
first surveyed photographic normal. So the survey ran first.

**12 installed wood-family normal maps**, across three donor packs:

    Mega_Street_Props_Pack  T_Wood060_4K_Normal, T_Wood039_4K_Normal,
                            T_Wood057_4K_Normal, T_Wood027_4K_Normal,
                            T_WoodFloor039_4K_Normal
    Deko_MatrixDemo         T_PlywoodBoards_A01_N (x2 locations),
                            T_WoodenPallet_A01_N, _B01_N, _C01_N,
                            T_Wood_Particle_01_N
    Uniblocks               T_UB_wood_lacquered_N

**The discriminating question is CONTINUOUS GRAIN vs JOINTED BOARDS**, and it
is the whole question. A carved solid mass has grain running through it and
**no plank seams**; almost every photographic wood map depicts a floor, a
pallet or a panel — i.e. boards with joints. A plank map on a carved block
would read as a crate, not as timber, and it would do so at exactly the
distance B2's framing puts the viewer.

**That question is not answered from filenames and will not be here.**
Admission stays closed-list: survey -> shortlist -> **the owner's eye**, with
acceptance on a BUILDING, both standoffs, amplitude swept — never on the flat
study wall, which hides amplitude entirely. No map is proposed in this
declaration; the survey is the deliverable, the shortlist is the next step.

One candidate is worth flagging for a different job: `T_Wood_Particle_01_N`
reads by name as particle board, which is what **chipboard** actually is —
the board, not the buildings.

### Custody, declared now because it decides a fresh clone

All four donor packs are gitignored (`.gitignore:4, 50, 65, 75`). Of the 12
candidates, exactly **one** wood-family map sits inside the pack's own
`PolyHaven_CC0/` folder — `T_UB_parquet_1_N` — and parquet is a laid-block
floor pattern, not carved grain.

Consequence, stated rather than discovered later: **an admitted map from this
inventory will almost certainly be pack-resident and guarded by
`check_textures.py`, not copied into tracked content** — so a fresh clone
would render direction B without its grain. That is precisely the regression
class the brick map was *replaced* to close, and the replacement was chosen
over guarding for that reason.

**The ladder, in order:** (1) shortlist from the 12; (2) if none serves, a
**CC0 source that arrives with custody** — the brick precedent, which closes
the fresh-clone class outright rather than guarding it; (3) generate a grain
only as the last rung, with the value-noise lattice on the record as the
warning. Rung 3 is not expected to be reached and is not planned for.

### Roughness

basswood's 0.48-0.64 is the second-lowest architectural band — below card
(0.62-0.80), above wire. Sanded timber, and correct as declared. Whether it
holds when it is *every surface in the frame* rather than a soffit is an
**acceptance** question, not a declaration: a band that reads as one material
among seven can read as uniformly waxy when it is the whole city. Carried
forward as a named acceptance risk, tested on a building, not asserted here.

### The tonal system — and the one place two locked references pull apart

**CLOSED by the owner, 2026-08-31 — see D3. The lane's proposal below was
NOT the option chosen; it is kept because a declaration ledger that quietly
deletes its rejected arguments cannot be audited.** Two reference slots each
specify tone, and taken literally they collide:

- **B1**: "tones pale pine to dark walnut", and tone variation is *"warmth and
  tonal dynamics **for now**"* — explicitly NOT gameplay, with the door to
  tone-as-gameplay "open for later discussion".
- **B3**: patina LOCKED — "start pale and age toward the board's honey tone".
  Tone *is* information: it carries time.

**If tone carries time, tone cannot also be free decoration.** A dark building
is either walnut or it is old, and nothing in the frame says which. The same
discipline B4 applies to glow ("the glow carries information") applies here
the moment patina is locked.

The lane's proposal, offered with reasons and subject to the owner's word:
**age owns VALUE; timber identity owns HUE and GRAIN.** A freshly-cut walnut
is a *pale red-brown with walnut figure*; a settled pine is a *honey
yellow-brown with fine straight grain*. Value alone carries time, so time
stays readable; species variety survives in hue and figure, so B1's tonal
dynamics survive without lying. This is a derivation from the two references,
not a preference, and it is the owner's to overturn.

It is flagged rather than built because it decides the SHAPE of the family:
how many wood MIs exist, what each means, and whether `wall=` varies per
wooden recipe at all. Everything above this section is independent of the
answer and stands either way.

### What "good" means for the wood family

1. **It reads as CUT, not as printed.** The failure state is the current one:
   a paper weave on a timber mass. Grain has direction; paper tooth does not.
2. **Grain is continuous across a carved mass** — no plank joints where the
   fiction says solid block.
3. **One fabrication, many tones.** Every building is visibly the same
   material worked differently — the master-material argument, which is the
   art direction and not a rescue.
4. **It survives the night frame** (B4): wood under glow is still wood.
5. **Grain is a DISCOVERY at inspection range and a warmth at board range** —
   B1's "surprise the player with the little details they find without going
   overboard", applied to the surface rather than to street furniture.

---

## D3 — tone belongs to timber; age reads as WEAR. Owner, 2026-08-31.

**The owner's decision, put to them as D2's open question and answered
directly: TIMBER OWNS TONE. AGE SHOWS AS WEAR, NOT COLOUR.**

The lane recommended the opposite split (age owns value, timber owns hue and
grain) and argued this option was ruled out by B3's locked wording. **The
owner overruled it, and B3 is theirs to interpret.** This section records the
decision, what it overturns, and — written down because it is the substantive
part — the reason the lane's recommendation was the weaker call on evidence
that was already in the repository.

### What it means

- **Tone is IDENTITY.** A building's timber (pale pine .. dark walnut, B1) is
  chosen once and held for every tier it climbs — the same rule the district
  palette already follows: "A building does not repaint itself when it gains a
  storey" (`palette.py`). B1's "warmth and tonal dynamics" survives intact and
  stays decorative, exactly as B1 says it is "for now".
- **Age is HANDLING.** Sheen, edge polish, softened arrises, grain contrast.
  Time is visible in the SURFACE, not the hue.
- **B3 re-read accordingly:** "start pale and age toward the board's honey
  tone" is read as *start freshly cut and settle into the board's worked
  finish*. Freshness is a crispness, not a colour.

### Why this is the stronger call — the evidence the lane missed

`Docs/MINIATURE_RECIPE.md:81`, under the flagship's own fabrication rules:

> **No large-scale albedo variation.** Uniform in colour, varied in sheen and
> at edges. **This is the trap and it stays a trap.**

The lane's recommendation — age driving VALUE across a whole city over game
time — is large-scale albedo variation, i.e. the documented trap, proposed
without connecting it. The owner's choice is that existing doctrine applied
to direction B, and the doctrine is shared with the flagship rather than
invented here. Recorded plainly so the ledger shows which argument was right
and why, not merely which one won.

### And it is CHEAPER to build, which was not obvious

Edge wear is **already built** into `M_StacktownMaster`
(`MINIATURE_RECIPE.md:163`: "Edge wear, a 40 mm chamfer and vertical panel
seams are now built"), implemented as a normal-as-curvature proxy:

    wear = saturate((1 - max(|n|)) / 0.30)      albedo lift 1.42

The standing trap on it (`HANDOFF.md:332`) is that **it does nothing on
imported geometry** — no curvature data, so donor meshes get nothing. That
trap does not bite here, and the reason is structural: it works on
"axis-aligned boxes with 45 degree chamfer facets", and

**direction B's carved masses ARE axis-aligned chamfered boxes** — generated
by `genbuild.box()`/`slab()` and chamfered at bake (`fastbake.py:170-182`,
which asserts the chamfer took by triangle count: 44 per chamfered box
against 12 for a sharp one).

So direction B is the geometry class the project's one existing wear
mechanism was written for. The owner's option needs **a scalar driving a proxy
that already exists**; the lane's recommendation would have needed value/hue
separation in the shader plus per-species grain maps. The rejected option was
the expensive one.

### What this changes upstream

- **D1's mechanism is untouched.** Material-level, Custom Primitive Data,
  never in the catalogue key, tier-up sets Age := 0. None of that was ever
  about colour. D1's *content* is corrected in place above.
- **Channel 0 is a wear ramp**, not a tone ramp. The channel map is otherwise
  unchanged, and it gets better: **value = never, hue = species, wear = time,
  temperature = status (B4)**. Three orthogonal channels, each meaning exactly
  one thing, and colour is left entirely free for B4's information glow
  instead of being shared with time.
- **The wood MI family is a SET, not a single material** — one per timber
  tone, all sharing the `basswood` stock, differing in base colour, resolved
  through the spec's `wall` value exactly as `MI_dist_*` are today. How many,
  and which tones, is the next declaration and is a look call.

### It is cheaper AGAIN than D3 first recorded — measured 2026-08-31

D3 says above that the wear machinery is "already built in the master". The
read-only window found it is further along than that: **the parameters are
already NAMED AND EXPOSED.** `MI_wood`'s parameter list carries

    EdgeWearWidth   (Scalar)
    EdgeWearLift    (Scalar)

alongside `RoughMin`/`RoughMax`, the `Paper*` family, the `Seam*` family,
`BaseColour`, and the `PaperNormal` / `PaperDetail` textures.

`Scalar` is **precisely the parameter type `bUseCustomPrimitiveData` applies
to**. So the whole patina path is now evidenced end to end with nothing left
to invent: **Age at CPD index 0 drives `EdgeWearLift` (and possibly
`EdgeWearWidth`) on an existing named parameter of the existing master.** No
new node, no new master, no dynamic material instance, no graph change.

The same read confirms D2 from the other side: `MI_wood` has a bound
`PaperNormal` **texture parameter**, and `fabrication` declares basswood
`normal=None` — so the wooden city wears `T_PaperNormal` through a parameter
that is already there to be repointed the moment a grain map is admitted. The
grain work needs no new plumbing either.

Worth stating plainly for the record: the lane recommended AGAINST this option
and the coordinator endorsed that recommendation. Every measurement taken
since has made the owner's call cheaper.

### The named risk

Wear is a NARROWER channel than tone. Edge polish on a 40 mm chamfer is a thin
band of pixels at board range, where a tone shift would have been the whole
face. **Whether age is legible at B2's framing is therefore a real question
and it is an ACCEPTANCE question, not a declaration** — measured on buildings
in a frame at the show camera, not asserted here, and not settled by any
agent's eye including this one's. If it proves illegible at board range, the
honest move is to say so and return to the owner with the measurement, never
to quietly reintroduce a tone shift to rescue it.

---

## D4 — sizing the wooden slice. Measured 2026-08-31.

First Commission item (2) begins with a number nobody had: **how big is
"covering the test-city identity keys"?** Measured headless, offline, through
genbuild's sink — no editor, no bake, no actors.

### What TestCity actually asks for

`citylayout.PARTITIONS` lays **14 lots** across four blocks, at five widths:

    w820   x2      w1230  x7 (1 corner)    w1640  x3 (1 corner)
    w2050  x1 (corner)    w2460  x1 (corner)

Against the 566 assets on disk, the identities those lots can reach are:

    549   distinct (recipe, tier, width)  — the MESH count
    195   distinct (recipe, tier)         — the POINTER key space (MeshByKey)
     33   recipes, essentially the whole catalogue

**So "covering the test-city identity keys" read literally means rebuilding
the entire catalogue in wood.** That is not a slice, and the charter calls the
First Commission "scoped deliberately narrow". The tension is real and this
declaration resolves it — but only after testing the assumption that would
have made it go away.

### The hypothesis that failed, and the sweep that saved it from being believed

**Hypothesis:** direction B strips articulation (windowless masses by day, B1),
so many of the 549 should collapse onto the same MASS — the catalogue's
variety living in bays, glazing and cornices rather than in shape. If so, the
wooden catalogue would be a fraction of the flagship's.

**Measured, first pass:** 549 models -> **537 distinct bounding envelopes** at
10 uu rounding. Collapse ratio **1.02x**. Hypothesis falsified.

Two known-answer cells, because a table without one cannot be believed:
determinism (the same model twice -> identical signature) **PASS**; width
sensitivity (deco4_t2 at w1230 vs w1640 -> dx 1230 vs 1640) **PASS**.

**And then the instrument was checked against itself**, because 1.02x reported
alone would have been misleading: 10 uu is ~1 mm on a 1:87 model, so the first
pass was counting differences no eye could resolve as "distinct". Sweeping the
quantum:

    quantum    distinct   collapse   ~size on the model
     10 uu        537       1.02x      1 mm
     50 uu        478       1.15x      6 mm
    100 uu        330       1.66x     11 mm
    200 uu        165       3.33x     23 mm
    400 uu         64       8.58x     46 mm
    800 uu         27      20.33x     92 mm

**The conclusion survives the sweep and is now honest: there is no cheap
collapse.** Even binned at 23 mm on the physical model — a difference plainly
visible at B2's framing — 165 distinct masses remain. The flagship catalogue's
variety is genuinely IN ITS MASSING, not only in its articulation.

The envelope is the crudest possible descriptor, and a finer one can only
distinguish MORE, never less. So 165-at-23mm is a floor, and the finding is
robust in the direction that matters.

**Where the variety lives**, per axis at 100 uu bins:

    dz (height)   46 distinct   370 .. 7541      <- the variety axis
    dx (width)    21 distinct   521 .. 2460
    dy (depth)     5 distinct   676 .. 1592      <- nearly constant

Depth is almost a constant. Worth carrying into the board read: a wooden city
built from these masses is a skyline of varying height on a nearly uniform
footprint depth — which is what a street of lots *is*, and which the carved
reference (B1) also shows.

### What this corrects in the lane's own charter

The charter's staffing argument says direction B's v0 is "UNIQUELY cheap to
make real". **That is true of per-model DETAIL and false of model COUNT**, and
the two were not separated when it was written. Stated properly:

- **Authoring cost stays tiny** — a massing-only wooden model is one spec key
  with a behaviour-preserving default, not 549 art tasks. The charter's claim
  holds where it matters.
- **Bake cost is real and is the whole cost.** At the measured rate (16 min per
  156 models, POLISH_PROTOCOL) a full 549 wooden catalogue is **~56 minutes of
  serialized editor window** — and the editor window, not compute, is this
  project's scarce resource by its own bake policy.

### The declared slice: 14 models, not 549

**A board with 14 lots cannot show more than 14 buildings.** The full 549 is
the eventual coverage cost, not the first commission's cost. So the first
wooden board is declared as:

**One wooden model per lot — at most 14, across the five widths TestCity
uses** (2 at w820, 7 at w1230, 3 at w1640, 1 at w2050, 1 at w2460), chosen to
show the tonal and massing range rather than to cover the catalogue.

This works because the placer draws from what is BAKED (`mk_testcity_builds`
builds `stock[w]` from assets that exist): a wooden catalogue of 14 does not
fail to resolve, it simply offers less variety — and 14 lots cannot display
more than 14 anyway. Coverage beyond the board is a later, separate bake
decision, taken when there is a board to justify it.

**One caution recorded against that plan.** The draw is
`rnd.choice(stock[w])` on a fixed seed, so **changing what is baked re-deals
every lot** — the same shape as the share-promotion lesson (appending to a
hashed draw list changed `hash %% len` and repainted every vernacular
building). The first board's 14 must therefore be pinned by identity, not left
to a draw that a later bake silently re-rolls. How they are pinned is an
implementation choice for item (3); that it must be pinned is decided here.

**TWO HAZARDS, NOT ONE — separated 2026-08-31 so neither is mistaken for the
other.** The placer's determinism has been attacked twice, by different
mechanisms, and only one of them is fixed:

1. **The ORDERING cause — FIXED at 17f552e.** The gap and setback draws sat
   AFTER the asset-existence check, so a `continue` on a missing asset
   consumed fewer random numbers and shifted every later lot. Its own commit
   message states the diagnosis exactly ("SEED promises the same city every
   run; it was promising the same city per bake state") and the fix moved both
   draws ahead of the check. Verified there by running the placer twice.

2. **The DOMAIN cause — STILL LIVE, and it is what D4 measured.** The seed
   fixes the SEQUENCE of random numbers; it does not fix the LIST being drawn
   from. `stock[w]` is rebuilt from what exists on disk, so changing the bake
   set at a width re-deals every lot at that width even with the ordering
   fixed. Measured: removing one asset moved **7 of 14** buildings.

The second is genuinely additional, not a re-discovery of the first — checked
against the backlog before being offered as new. The pin table addresses the
DOMAIN cause, which is the one the wooden catalogue triggers by construction.

**AND IT DOES NOT FIRE ON EVERY BAKE — checked, not assumed.**
`catalogue_at()` (`mk_testcity_builds.py:58-68`) builds `stock[]` from the
**PLAIN** asset name via `recipes.asset_name(rid, t, width)`, never the corner
name. So baking a CORNER VARIANT leaves the draw domain byte-identical and
cannot re-deal anything; only a bake that adds a PLAIN asset at a width can.
This distinction was worth measuring rather than reasoning: it is the
difference between the second-tower bake being safe and being a board-wide
reshuffle, and the answer is that it is safe.

### Still open, and NOT decided here

**Which spec key produces a massing-only model, and whether it can be added
with a behaviour-preserving default**, is the byte-identical question at the
heart of item (2). It is deliberately not answered in this declaration: it
requires reading genbuild's build path properly, and the flagship lane that
certifies phase-F-class generator changes is on break. Sized first, built
second.

---

## D5 — grain varies by SPECIES. Owner, 2026-08-31. Corrects D2/D3.

**Owner, on being shown the grain shortlist: "grain should vary by
species/building type/etc so it's hard to pick just one grain (and we need
more than 3)."**

### What this corrects

D3 declared the wood family as "one per timber tone, all sharing the
`basswood` stock, differing in base colour". **That is wrong, and it is wrong
in a way D3 itself should have caught.** D3's own channel map says
**hue = species** — and grain is as much a species trait as hue. A stock
carries the normal map, so one stock for all timber means one grain for every
building in the city: the same paper-tell fault D2 found, wearing a wooden
name. Pale pine and dark walnut do not differ only in colour; they differ in
figure, ring spacing and how coarsely the grain reads.

**Corrected: SPECIES IS A STOCK, not a colour on a shared one.**

### It needs no new machinery, and the precedent is exact

`fabrication.stock_for()` resolves by LONGEST PREFIX. Verified:

    today                          with species stocks added
    MI_wood        -> basswood     MI_wood        -> basswood
    MI_wood_pine   -> basswood     MI_wood_pine   -> pine
    MI_wood_walnut -> basswood     MI_wood_walnut -> walnut

This is the mechanism `MI_dist_brick` already uses to leave the `MI_dist`
paint family: a longer key wins, no special case, no code change — a table
entry per species. And it satisfies the stock admission rule as written:
**"a stock exists iff a modelmaker would reach for a different material."**
Pine, oak and walnut are different materials a modelmaker reaches for. Species
-as-stock is the doctrinally correct reading, not a stretch of it.

Each species stock therefore carries its own **normal (grain)**, its own
**tooth/amount**, and its own **roughness band** — species genuinely differ in
how they take a finish — while the MI carries the colour. Building type
reaches grain the way it already reaches colour: recipe -> spec `wall` ->
`MI_wood_<species>` -> stock -> grain.

### The installed inventory cannot supply this — MEASURED, not assumed

All twelve installed wood normals were opened in the texture editor, cropped
and measured. Anisotropy is the discriminator: grain is directional, so a
ratio near 1.0 is not depicting wood.

    map                detail   ratio   verdict
    T_Wood060           28.31    2.96   continuous grain      MASS
    T_Wood039            6.28    1.96   continuous, fine      MASS
    T_Wood027            3.31    2.34   continuous, very fine MASS
    T_Wood_Particle      7.32    1.03   isotropic granular    BOARD - see below
    T_PlywoodBoards      4.38    1.66   plywood boards        reject
    T_Parquet            1.76    1.90   laid blocks, faint    reject
    T_Wood057            4.13    1.05   isotropic - noise     reject
    T_WoodenPallet_A     7.79    1.01   isotropic (knots)     reject
    T_WoodenPallet_B     8.05    1.02   isotropic             reject
    T_WoodenPallet_C     9.33    1.02   isotropic             reject
    T_WoodFloor039       3.25    1.76   planked, CROSS-axis   reject + bad import
    T_UB_wood_lacquered  0.68    1.73   no relief (lacquer)   reject

**Three usable mass grains, from one pack, all ambientCG woods.** Three
species is not a city. FAB-FIRST's bar — "prove nothing installed serves" — is
therefore MET by measurement rather than by argument, and the next rung is
open.

**One real find outside the mass question:** `T_Wood_Particle_01_N` measures
isotropic-granular (ratio 1.03, gradient 7.95), which is exactly what particle
board IS. `chipboard` — the stock for the BOARD the city stands on — also
wears `T_PaperNormal` today. It is a separate admission for a separate job,
and it is the best-supported one in the inventory.

### The convergence: more species and the fresh-clone cost have ONE answer

D2 flagged that admitting a pack-resident map means direction B renders
grainless on a fresh clone, guarded by `check_textures.py` rather than fixed.
That looked like a cost to weigh against admitting from the packs.

It is not a separate question any more. The inventory cannot supply enough
species, so we must go outside it — and the correct outside source is **CC0
with custody** (the Poly Haven route taken for brick, which closed the
fresh-clone regression class outright instead of guarding it). Sourcing the
species set and fixing the custody problem are **the same move**.

### What the shortlist could NOT answer, named at the owner's prompting

The owner asked whether the purple was expected. It is — a normal map encodes
surface direction as RGB and a flat surface is (128,128,255) periwinkle — but
the question exposes a limit in how the shortlist was presented: **a normal
map viewed as RGB is a data visualisation, not an appearance.**

It is a valid instrument for STRUCTURE (planked vs continuous survives the
encoding, and that is what rejected nine of twelve). It is not a valid
instrument for LOOK. No grain may be admitted on the strength of its map
alone; the candidates go on lit geometry before any species is chosen — which
is the acceptance rule this project already has ("acceptance happens on a
BUILDING", never on a flat sample), arriving here one step earlier than usual.

### Open, for the owner

**How many species, and which?** B1's range is "pale pine to dark walnut". The
district palette runs nine schemes for comparison. The number is a look call
and it sizes the admission list, so it comes before sourcing rather than after.

---

## D6 — the six timbers. Owner, 2026-08-31.

**Owner's word: "lets do 6 species to start, pale pine through walnut...
wood grain should be species/tonally accurate."**

Two decisions in one sentence. The count (six) sizes the admission list. The
accuracy constraint decides *where the maps can come from*, and it rules out
the answer D5 was drifting toward.

### FIRST: the prohibition this must answer

`MASTER_MATERIAL_SPEC.md:45`, in the role-vocabulary section:

> Keep the set this small. The last project's palette grew a **`walnut`** and
> a **`cedar`** and a `bronze` that did nothing a parameter could not have done.

A future reader will grep `walnut`, find that line, and conclude this
declaration violates the spec. It does not, and the distinction is precise:

- The prohibited walnut was a **role** that differed from its neighbours only
  in COLOUR — a parameter wearing a material's name.
- These six are **stocks**, and each carries **its own normal map**. A grain
  is not a parameter. Nothing in the master can turn oak's open pores and ray
  fleck into walnut's wavy close figure.

The spec's own test is the admission rule D5 already invoked — *a stock exists
iff a modelmaker would reach for a different material* — and a modelmaker
reaches for different timber, not for the same stick painted darker. **The
line to watch is that these six never become six colours on one map.** If a
species cannot be given its own grain, it is a colour and it must be dropped
rather than admitted. That is the falsifiable form of this argument.

### The six, pale to dark

Tones are TARGETS for the species, not final values — they are verified on a
building at the show camera like every other look number here.

    stock       tone target   grain character (what makes a map ACCURATE)
    ---------   -----------   ---------------------------------------------
    basswood    #E8DCC0       the modelmaker's own timber: near-featureless,
                pale cream    very fine even grain, almost no figure. The
                              PALE END and the existing stock name - it keeps
                              its meaning rather than being renamed.
    pine        #E5C99A       fine straight grain with STRONG LATEWOOD
                pale yellow   BANDING - the alternating soft/hard stripe is
                              pine's tell, and knots are characteristic.
    ash         #D9C4A0       COARSE OPEN PORES at a pale tone - the entry
                light tan     that proves tone and coarseness are independent
                              axes. Long, straight, prominent grain.
    oak         #C19A6B       open grain plus RAY FLECK, the short cross-grain
                honey         flashes nothing else here has. The honey middle
                              of the ladder.
    mahogany    #A0522D       medium INTERLOCKED grain, ribbon figure that
                red-brown     alternates direction - reads as stripe under
                              raking light.
    walnut      #5C4033       medium-coarse with WAVY, irregular figure and
                dark chocolate colour variation within the board. The DARK END.

**The ladder is two axes, not one.** Tone runs pale to dark; coarseness does
NOT run with it (basswood fine/pale, ash coarse/pale, walnut coarse/dark).
That is deliberate and it is what stops the city reading as a single gradient
- a pale building and a dark one can share a grain family, and two pale
buildings can differ in it.

### SECOND: the accuracy constraint forecloses the installed inventory

D5 measured three usable mass grains and was heading toward assigning them by
coarseness — Wood060 as the coarse one, Wood027 as the fine one. **The
owner's accuracy constraint kills that plan, and correctly.**

The three are ambientCG `Wood060`, `Wood039`, `Wood027`: generic, UNIDENTIFIED
woods. Nothing names their species. Assigning Wood060 to "oak" because it
measures coarse would be exactly the failure this project has a rule for — *a
plausible mechanism plus a matching axis is not evidence the axis is the right
one*. Coarse is not oak. Oak is oak, and its ray fleck is the thing that says
so.

**Therefore: species-accurate grain requires species-IDENTIFIED sources, and
the installed packs contain none.** FAB-FIRST is satisfied twice over now —
first by count (three cannot fill six), now by kind (unidentified cannot be
accurate).

### What this makes of the custody problem: it disappears

D5 noted the two problems were converging. Under the accuracy constraint they
have merged completely:

- accurate maps must be species-identified -> they come from a catalogue that
  names species -> **Poly Haven / ambientCG name their woods**;
- those are **CC0**, so they arrive with custody and are COPIED into tracked
  content under the texture-custody carve-out;
- which closes the fresh-clone regression class **outright** rather than
  guarding it — the brick precedent, and the reason brick was replaced rather
  than guarded.

There is no longer a trade-off to weigh. The accurate route and the
custody-correct route are the same route, and the pack-resident option is
dead on accuracy grounds before custody is even considered.

### The admission list, and what still gates it

Six maps to source, one per stock, each carrying:
`source URL, licence, acquisition date, species identification` — the asset
acceptance record `AGENTS.md` already requires, plus species, which is new
here because accuracy is now a stated requirement rather than a preference.

**Gates that do NOT relax for being CC0:**

1. **Green convention.** `flip_green_channel` verified per map at import and
   recorded in the stock's `needs`. An inverted green renders grain proud
   where it should be recessed and MEASURES IDENTICALLY either way. This is
   the fault that motivated the custody rule; six new maps is six new chances
   to reinstate it.
2. **`sRGB` off, `Normalmap` compression, `WorldNormalMap` group** — the exact
   trio `T_WoodFloor039` gets wrong today (D5), proving the fault is live in
   the packs and not hypothetical.
3. **Their micro-relief, our colour.** A CC0 wood texture set ships albedo and
   roughness. **Only the normal is admitted.** The six tone targets above are
   OURS and stay ours; a photographed walnut's albedo is not the palette.
4. **Acceptance on a building**, at the show camera, amplitude swept — never
   on a flat sample, and never on the normal map viewed as RGB, which is a
   chart of slopes and not a picture of wood (D5).

### Still open

**Sourcing itself is not started and needs the owner's word** — six downloads
from an external source is an acquisition, and this project does not acquire
assets on an agent's initiative. What is decided here is WHAT to look for and
WHAT it must satisfy; the looking is a separate approval.

### The tone ladder, MEASURED — and a collision worth the owner's call

The six targets above were checked in CIE L* before anything is built on them.
Even spacing across the range would be ~11.6 L* per step:

    stock       hex        L*     step
    basswood    #E8DCC0   88.0
    pine        #E5C99A   82.3    -5.8
    ash         #D9C4A0   80.0    -2.2   <-- collision
    oak         #C19A6B   66.1   -13.9
    mahogany    #A0522D   43.8   -22.3
    walnut      #5C4033   29.9   -13.9

**The pale end is bunched and the middle has a hole.** Three species occupy
the top 8 L* while a 22-point gap yawns between oak and mahogany. Most
sharply: **pine and ash are 2.2 L* apart** — at B2's board range they will
read as the same timber, distinguished only by grain (pine's latewood banding
against ash's open pores).

This is not a fault in the targets; it is what *accurate* costs. Real pale
timbers really are all pale. The instruction was species-accurate, so the
tones are not being fudged to spread the ladder — that would be inventing a
timber, and inventing a threshold and then judging against it is a named
failure here.

**Two honest resolutions, owner's call:**

(a) **KEEP ALL SIX.** The pale end is separated by FIGURE, not tone — a row of
    pale timbers differing in cut rather than stain, which is arguably the
    more interesting read and is exactly what species-accuracy buys. Risk,
    stated: if grain does not survive board range, three species collapse into
    one look and two of the six are wasted.

(b) **SWAP ASH FOR A MID TIMBER** — cherry sits naturally around L* 52 and
    fills the oak-to-mahogany hole, giving roughly 88 / 82 / 66 / 52 / 44 / 30.
    Cost: ash is the lane's only COARSE-AND-PALE entry, and losing it makes
    coarseness correlate with darkness — the two-axis property this
    declaration argued for stops being true.

**Recommendation: (a), and treat it as the first thing the lit samples must
answer.** The question "does grain separate two same-toned timbers at board
range?" is answerable on a test surface before any species is sourced, and it
decides (a) versus (b) with evidence instead of preference. If grain does not
carry it, (b) is the fallback and nothing has been wasted.

---

## D7 — the six are sourced, and sourcing found a rule problem. 2026-08-31.

Owner approved CC0 sourcing. Seven maps downloaded from Poly Haven (CC0
verified at https://polyhaven.com/license: commercial use, redistribution, no
attribution required), 2048x2048 16-bit PNG, into
`Tools/textures/source/polyhaven/` beside the brick.

**One improvement on the brick precedent, already anticipated by its own
note.** Poly Haven publishes both green conventions. The brick took `nor_gl`
and needed `flip_green_channel` at import — the fault class that motivated the
whole custody rule. **These are `nor_dx`**, DirectX convention, which is what
UE samples. The flip is not set, not needed, and cannot be forgotten on a
fresh clone. `PROVENANCE.md`'s own line — "flip green (*or import as
DirectX*)" — is now taken up.

### The six, and one substitution the evidence forced

    stock     asset                    L* target   why this species
    maple     white_maple_veneer         88        the pale end
    ash       ash_veneer                 80        coarse open pores, pale
    oak       white_oak_veneer           66        ray fleck, the honey middle
    cherry    cherry_veneer              52        fills the measured tone hole
    sapele    sapele_veneer              44        a TRUE mahogany-family
                                                   timber with the interlocked
                                                   ribbon figure D6 described
    walnut    american_walnut_veneer     30        the dark end

**PINE IS OUT, on evidence.** D6 said "pale pine through walnut" and pine is a
softwood, so it is essentially never veneered — the only Poly Haven pine is
`coated_pine`, varnished. It was downloaded anyway rather than argued away,
and its normal map is **completely blank**: a uniform blue field, zero
relief, because the varnish fills the grain. Rejected by looking at it. Maple
takes the pale end, and the substitution is now backed by a frame rather than
by my preference.

Cherry also resolves the 22-point L* hole D6 measured between oak and
mahogany, so the ladder is 88 / 80 / 66 / 52 / 44 / 30 — still bunched at the
pale end by the owner's accepted decision, but no longer holed in the middle.

### THE RULE PROBLEM, measured

**"Their micro-relief, our colour" (owner-approved 2026-08-28) does not
survive contact with sanded timber.**

A veneer is sanded flat. Its grain is COLOUR figure, not relief. Measured on
the same asset through the same pipeline and the same window — a
within-subject comparison, which is the standard this project holds
between-subject comparisons to:

    asset            map       detail    direction
    ash_veneer       NORMAL      1.07      2.26
    ash_veneer       DIFFUSE     4.78      5.22      <- 4.5x the grain
    white_oak        NORMAL      2.33      1.39
    white_oak        DIFFUSE     4.96      2.84      <- 2.1x the grain

Confirmed by eye: oak's normal shows shallow pore streaks; ash's is nearly
flat; coated pine's is blank. **Taking only the normal discards most of what
makes each species look like that species** — and would land the wooden city
in a new form of the exact fault D2 found: near-featureless surfaces, species
separated only by flat tone, on a direction whose material lock is "grain as
the surface".

The rule is not wrong; it was written for BRICK, where the relief IS the
feature (embossed brick sheet has real depth). Wood is the case it does not
cover.

### The decision this needs — OWNER'S, not the lane's

**(a) Normal only, rule as written.** Species differ by flat tone plus very
shallow relief. Honest to the rule; risks a city of featureless blocks and
makes D6's whole species argument moot, since figure is what was meant to
separate the bunched pale end.

**(b) Their PATTERN, our PALETTE — the proposed extension.** Take the normal
AND a **luminance-only grain mask** derived from the diffuse, used to modulate
**our** species tone. Their colour is never imported: the mask says WHERE the
grain is, our palette says WHAT COLOUR it is. This keeps the rule's actual
purpose — donor albedo must not set our palette — while accepting that wood's
figure is tonal. It is an extension of an owner-approved rule and therefore
the owner's call, not mine.

**(c) Source rough-sawn or weathered timber instead**, which has real relief.
Rejected on look grounds before it is offered: a carved model block is
SANDED. Rough-sawn grain would read as driftwood, not as a planning model.

**Recommendation: (b).** It is the only option that delivers species-accurate
grain, and the palette discipline the original rule protects is untouched by a
luminance mask.

**A possible existing home, flagged not assumed:** `MI_wood` carries a bound
`PaperDetail` texture parameter, and HANDOFF open question 5 says PaperDetail
is "bound but its contribution is untraced". That may be the channel a grain
mask belongs in, or it may be a trap. It is traced before it is used.

### Not yet done

Nothing is imported. No `.uasset` exists, no stock references any of these,
`fabrication.py` is untouched, and the seven sources are downloaded but
uncommitted. **Repo cost to flag: ~135 MB of 16-bit PNG sources** (the brick
pair is ~32 MB for comparison). Whether the sources are committed like the
brick's, or recorded by SHA-256 in PROVENANCE.md and re-fetchable instead, is
a repo decision worth taking deliberately rather than by precedent.

---

## D8 — THEIR PATTERN, OUR PALETTE. Owner, 2026-08-31.

**Owner's word: "approve the grain mask, their pattern our palette."**

The extension proposed in D7 is approved. Recorded with its scope, its
mechanism, and the line it must not cross.

### The rule, stated so it can be enforced

MASTER_MATERIAL_SPEC's admitted scope was **"their MICRO-RELIEF, our colour
and sheen"** — a donor lends its normal map and nothing else. For direction
B's timber that is extended to:

> **THEIR PATTERN, OUR PALETTE.** A donor wood map may lend, in addition to
> its normal, a **LUMINANCE-ONLY GRAIN MASK** derived from its diffuse. The
> mask carries *where the figure is*. The palette — hue, value, and the
> species tone the figure modulates — remains entirely ours.

**Why this does not gut the original rule.** The rule exists so that donor
albedo cannot set our palette; that is its whole purpose, written after a
photoreal donor beside flat-shaded work. A luminance mask imports no hue, no
saturation and no absolute value — it is a black-and-white pattern. Our six
tone targets are unchanged by it, and a donor's brown never reaches the frame.

**The line, and it is testable:** the mask is **single-channel and
mean-normalised**. If any pipeline step ever carries a donor's colour, hue or
absolute brightness into the material, the extension has been violated,
regardless of what it is called. That is checkable in one assertion and
should become one.

### SCOPE: direction B only, deliberately

This extension is recorded **in the direction-B ledger, not in
MASTER_MATERIAL_SPEC.** The owner approved it in the context of the wooden
city's timber, and generalising a shared doctrine on that basis would be
overreach twice over: the flagship lane owns that spec's consequences and is
on break, and its materials are brick, plaster and paint — the cases where the
original relief-only rule is exactly right.

If the flagship wants it, that is a separate decision on that lane's return.
What is owed meanwhile is a **cross-reference** in MASTER_MATERIAL_SPEC so a
future reader of the shared spec learns the extension exists — proposed to the
coordinator rather than written by this lane.

### Mechanism

Each species stock carries **two maps**, not one:

    normal   the species' nor_dx map    - shallow relief, replaces the
                                          master's default paper tooth
    figure   the species' grain mask    - luminance from the diffuse,
                                          mean-normalised, modulating
                                          BaseColour

`fabrication._st()` gains a `figure` key defaulting to `None`, exactly as
`normal` does — additive, behaviour-preserving, and every existing stock keeps
emitting what it emits today. `figure_for(name)` joins `normal_for(name)` as a
sibling accessor rather than being folded into `params_for`, which emits
scalars only and would break every caller if a texture were folded in — the
reason that separation already exists.

This composes with D3 without collision, and the channel map holds:

    hue        species    BaseColour vector, ours
    figure     species    grain mask, donor pattern modulating our tone
    wear       time       EdgeWearLift, CPD channel 0
    glow       state      B4's night system, CPD channels 1-3

### Where the mask lives — TO BE TRACED, NOT ASSUMED

`MI_wood` carries a bound `PaperDetail` texture parameter, and HANDOFF's open
question 5 records that PaperDetail is **"bound but its contribution is
untraced"**. It may be the channel a grain mask belongs in; it may be
something else; it may be doing nothing.

**It is traced before it is used.** An untraced parameter that happens to
produce a plausible result is precisely how this project acquires faults that
survive for weeks — and if PaperDetail turns out to be wrong for this, the
alternative is a new parameter on `M_StacktownMaster`, which is a **shared
master** and therefore a change this lane does not make alone.

### Still not done

Nothing imported. `fabrication.py` untouched. The seven sources sit
uncommitted, and the ~135 MB repo question is still open.

### PaperDetail TRACED — and it splits the grain mask in two

D8 said PaperDetail is traced before it is used. Traced, from the code that
wired it (`wire_paper.py:74-93`) rather than by inspection of a graph:

    det = TextureSampleParameter2D('PaperDetail', T_PaperDetail,
                                   SAMPLERTYPE_LinearGrayscale)
    wire(mul, det, 'UVs')          # the same tiled UVs as the paper normal
    wire(det, target, 'Alpha')     # -> the ROUGHNESS Lerp's Alpha

**PaperDetail is the ROUGHNESS DETAIL channel**: a grayscale map interpolating
each material between its `RoughMin` and `RoughMax` across the surface. It
replaced an older world-scale Noise alpha.

**This answers HANDOFF open question 5**, which has stood as "bound but its
contribution is untraced" in HANDOFF, WORKSTREAMS and THREAD_PROMPTS. The
answer is owed to those three docs; HANDOFF.md is currently DIRTY in the
worktree with another lane's edits, so this lane does not touch it — the fact
is reported to the coordinator to route instead.

`PaperMottle` was checked in the same pass and is NOT a colour channel either:
`rebind_mottle.py` binds it to the three COARSE normal samplers — it is the
two-octave normal system, since parked.

**So there is no existing base-colour texture channel on the master**, and the
grain mask splits cleanly in two:

**HALF A — roughness figure. FREE, no master change.** Point each species
stock's `PaperDetail` at its own grain mask instead of the shared
`T_PaperDetail`. Open earlywood pores are genuinely rougher than dense
latewood, so a grain-shaped roughness variation is physically right, and it
arrives through a parameter that already exists on every instance. This half
can be built the moment the maps are imported.

**HALF B — colour figure. NEEDS A MASTER CHANGE.** `fix_wear.py:40` records
the chain: `MP_BaseColor -> Lerp(seam) -> Lerp(wear) -> BaseColour`. Making
the figure VISIBLE means inserting a multiply between the `BaseColour`
parameter and that chain — a change to **`M_StacktownMaster`, which every
material in the project shares**.

### Half B is not this lane's to make alone

It is additive and behaviour-preserving in principle — a `GrainMask` texture
parameter defaulting to white multiplies by 1.0, so every existing instance
renders byte-identically. But "in principle" is the phrase this project has
been burned by, and the master is the one asset the whole catalogue depends on.

**The split-proof standard, named BEFORE the change starts, per the rule that
requires it:**

- **the no-op half** proves itself by RENDER: an existing flagship material
  (not a wood one) captured before and after under the capture protocol, mean
  absolute difference within the measured noise floor. The parameter defaults
  to white; if anything moves, the default is not neutral and the change is
  wrong.
- **the look-change half** proves itself on a WOODEN building at the show
  camera, with the owner's eye — never on the study wall, and never on the
  numbers alone.

Neither half starts without the owner's word, and the coordinator holds
cross-lane verification for a shared-master change while the flagship lane is
away.

---

## D9 — THE HALF-REPOINTED FAMILY. Named 2026-08-31, on the second instance.

**"Repoint one consumer, miss the other."** Two instances in one session, same
shape, so it is a family and not two accidents — the treatment POLISH_PROTOCOL
gives the lapped-span and crown-collapse families.

**Instance 1 — the BaseColour multiply (CAUGHT).** `BaseColour` fed TWO nodes:
the wear Lerp's A and the `EdgeWearLift` Multiply's A. Inserting the grain
term meant repointing both; repointing one would have left half the material
reading the ungrained colour. It was caught because the graph was WALKED
first — the walk printed both consumers before a node was added.

**Instance 2 — the pith offset (SHIPPED, then caught on review).** The polar
centre feeds the radius (`DotProduct`) AND the angle (`Arctangent2Fast`). The
offset was wired into the DotProduct only, so rings were measured from the
shifted centre and their sweep from the original one — which shows as a swirl
seam across the end face. It was NOT caught by a walk, because no walk was
done: the shape was assumed from having built it an hour earlier.

**THE DETECTOR: walk the graph's consumers before any repoint.** Not "check
afterwards" — enumerate what reads a node BEFORE inserting anything between it
and them, and repoint the full set. Assumption is how instance 2 happened, and
knowing the graph is exactly the state in which one stops walking it.

The MCP tool reports INPUTS, never outputs, so a consumer list must be built
by scanning — and a full scan of the master is 141 round trips and times out.
The affordable version is what instance 1 used: walk DOWN from the material
property to the node, which reveals its consumers on the way past.

---

## D10 — the board's own stocks. Declared 2026-09-01, before any geometry.

Owner's order puts roads, sidewalks and board detail next. Declare before
geometry, as every stock before these.

**THE FAULT BEING FIXED, stated plainly:** the first boards' roads are
`MI_dist_slate` — a DISTRICT PAINT borrowed because it existed, not because
it was right. In frame they read as pale blue-grey plastic, the one element in
an otherwise wooden picture that says "engine". That is the exact error
`fabrication.py` was written to end: a surface wearing whatever material was
nearest rather than what a modelmaker would reach for.

**THE PRINCIPLE:** *a model is unified by FABRICATION.* The board is not a
painted texture of a city; it is a made object, and the question for every
part of it is the same one the stock table always asks — **what would a
modelmaker reach for?**

### The proposed vocabulary — three stocks, and why not more

    board_plate   the base the city stands on. CHIPBOARD ALREADY EXISTS for
                  exactly this and already has its admitted map waiting:
                  T_Wood_Particle measured isotropic-granular (ratio 1.03),
                  which is what particle board IS (D5). No new stock - the
                  one in the table gets the map D5 already shortlisted for it.

    road_inlay    NEW. The reference's roads are a stained inlay set INTO the
                  board, not paint on top of it: matte, muted green-grey,
                  darker than the timber and with no figure of its own. A
                  modelmaker cuts these from a different sheet and beds them
                  in - which is precisely the admission rule, so this earns
                  its place as a stock rather than a colour.

    kerb_card     NEW, and the one I am least sure of. Sidewalks in the
                  reference read as a THIN pale edge standing slightly proud
                  of the road - cut card, not stained wood. If it turns out
                  a modelmaker would cut kerb and road from the SAME sheet at
                  different colours, this must be dropped: two stocks that
                  differ only in tone is the walnut-and-cedar prohibition
                  MASTER_MATERIAL_SPEC names, and D6 already committed this
                  lane to dropping any species that cannot earn its own grain.

**Three, not seven.** The temptation is a stock per element - kerb, gutter,
crossing, plaza, verge. The table's own rule refuses it: those are the same
few materials cut to different shapes, and shape is geometry's job.

### What "good" means for the board

1. **The board reads as MADE, not as ground.** It has a visible edge and a
   thickness; the current plate reads as a sheet and the reference's does not.
2. **Roads sit IN the board, not on it.** Inlay, not paint — the joint where
   they meet is a feature.
3. **Nothing on the board out-saturates the timber.** The buildings are the
   subject; the board is what they stand on. The current slate roads fail
   this and are the loudest thing in frame.
4. **It survives the night frame** (B4), when the board is the unlit context
   the glow reads against.

### Open, and NOT decided here

**The road colour is the owner's eye, not a hex I pick.** My D6 tone targets
were derived from real timber and one was still wrong enough to need
compressing after a frame. A stained inlay has no natural referent to derive
from, so it goes to the owner as candidates on the board rather than as a
declared value — the same route the timbers took, and for the same reason.

---

## D11 — four owner answers, 2026-09-01. Two of them are LOCKS.

### 1. ROADS ARE STAINED WOOD INLAY

The board is **one material family**. Roads are cut from the same timber and
stained green-grey, bedded flush into the plate. "A model is unified by
fabrication" holds for the board as it does for the buildings — everything is
wood, differing by stain and by cut.

**This kills `kerb_card`, and D10 predicted it would.** D10 flagged that stock
as the one it was least sure of, on the rule that two stocks differing only in
tone is the walnut-and-cedar prohibition. Kerbs are the same sheet at a paler
stain — a COLOUR on one stock, which is exactly what the rule says a colour
should be. **The board vocabulary is TWO stocks, not three.**

    board_plate   chipboard, already in the table; T_Wood_Particle is the
                  map D5's survey already shortlisted for it
    road_inlay    NEW. Stained timber - it keeps GRAIN, because a stained
                  board still shows its figure; what changes is the stain,
                  not the material. Kerbs and crossings are tones of this.

### 2. DENSITY: TIGHTER, BUT STREETS STAY LEGIBLE

Not reference-tight. Buildings fill their lots and streets halve, while each
parcel stays distinguishable from the boom — because this is a board people
click on, and the buy/select verb needs a parcel to be pickable. The
photograph is the target for the LOOK, not for the geometry, and the owner
drew that line rather than letting it blur.

### 3. CARVING SCOPE — **LOCKED** at massing plus shallow reveals

**No recessed openings. No carved window bays.** Setbacks, a plinth, and a
scored line where a stage steps; all information from silhouette and tone;
windows exist only as light at night per B4.

**This makes `build_mass` feature-complete**, and that is the point of writing
it down. "A bit more carving" is the shape scope creep takes on a direction
whose whole economy is fewer parts per m2, and a future session reading this
should treat added facade articulation as a change requiring the owner's word,
not as polish.

#### The receipt for why `build_mass` exists at all — filed 2026-08-31

`build_mass` was written because its predecessor, `massing_only`, was wrong in
a way that is easy to state and was, until now, impossible to show:
`massing_only` suppressed the glazing family at the emission primitives, which
removes the FILL and leaves the VOID. A wall in this generator is piers and
spandrels around an opening, so deleting the glass does not close the hole - it
opens it. The buildings come out as open lattices you can see straight through.
Bookshelves, not carved masses.

That was argued from reading the generator, and the frames that should have
shown it could not: `DIRECTIONB_massing_blockhero` and `_playerzoom` were staged
at y=60000, outside `CITY_Room`, and ran **50-58% of their pixels crushed to
black**. The artifact was in the frame and invisible in it.

Re-shot 2026-08-31 from inside the lit room, the same framings measure 104-110
mean at 0.4% crushed and the lattices are unmistakable. So the decision to
write `build_mass` now has evidence rather than testimony, and a future session
minded to revive `massing_only` as the cheaper path can look at the picture
instead of taking this document's word for it.

The four dark originals are kept as `Saved/DirectionB/SUSPECT_*` with
`SUSPECT.md`; the replacements carry the original names. See also
[[look-post-fstop-drives-exposure]] for the separate exposure fault found in
the same audit, and `Tools/measure/ue.py` for the guard that now refuses an
undeclared lens state at capture time.

### 4. THE BOARD IS A TEST RIG — **LOCKED** as disposable

It exists to judge materials and forms. It stays built LIVE and UNSAVED; it is
not baked, not pinned, and nothing on it needs to survive. The real board
comes later through the pin table and a proper bake.

**So `testcity_pins` and the tower bake do NOT gate this work**, and neither
should be pulled forward to serve it. The rig is allowed to be cheap, and
being told so explicitly is what stops it quietly accreting into an asset
nobody meant to own.

---

## D12 — hand tolerance ON for direction B. Owner, 2026-09-01.

**The flagship's 2026-08-29 decision stands untouched. This reverses it for
direction B only.**

### What is being reversed, and why that is not a contradiction

The owner was shown a square building and a jittered one, same seed, same
spec, same light, and preferred the SQUARE one. `HAND_TOLERANCE = False` in
genbuild records that as a decision rather than a workaround, and the machinery
was left correct and switched off.

That call was made about the FLAGSHIP: a photographed architectural model
whose subject is fabricated precision — cut card, sprayed paint, mitred trim.
Jitter there reads as sloppiness.

Direction B is a different object. It is a **hand-laid wooden planning
model**: blocks sawn from stock and set down on a board by a person. The
maker's tolerance is not an error in that fiction, it IS the fiction — and a
grid of blocks in perfect axial alignment is the single loudest statement a
frame can make that no hand was involved. The owner's verdict on the current
board was "it looks like a render still", and machine alignment is one of the
reasons why.

**So the same machinery is right in one direction and wrong in the other,
which is exactly what a two-product repository should expect.** The flagship's
answer is not a general truth about jitter; it is an answer about card.

### The cost, stated because it was measured before

Turning jitter on costs COPLANAR DEBT — measured over the 548-model catalogue
at 11,166 pairs with jitter against 13,897 without. Nudging a floor off square
is the cheapest way to stop two planes being exactly coincident, so jitter
REDUCES the count. For direction B that cost is a benefit, and it is recorded
here so nobody re-derives it in surprise.

### Scoping: a spec key, not a global flip

`HAND_TOLERANCE` is a module constant read by both products. Flipping it
globally would apply the owner's rejected look to every flagship build.

So it becomes **overridable per build**, defaulting to the module constant —
absent, every existing caller behaves exactly as before, and
genbuild_identity proves it. Direction B's masses pass the key; nothing else
does.

### What it must NOT become

Jitter is placement tolerance, not damage. A block set down a degree off
square is a hand at work; a block visibly broken is wear, which is a separate
question the owner has PARKED until edges, light and tolerance have been
judged. One change-set per verdict, or the next "render" verdict cannot be
attributed to anything.

---

## D13 — the value ladder, read off B1. Owner, 2026-09-01. Amends D6.

The owner asked how the lane compares to the B1 reference on detail, form and
cinematic quality. Measuring both frames with the same instrument turned the
answer into numbers rather than opinion, and the numbers said something none
of us expected: **the timber was already right, and everything around it was
wrong.**

### The ladder B1 actually uses

| element | value | vs lit timber |
|---|---|---|
| road inlay | 165 | **+50%** |
| lit timber face | 110 | — |
| pale ground | 89 | −19% |
| dark timber | 47 | −58% |

**The roads are the brightest thing in the reference.** That is the whole
trick: warm blocks read as objects on a light field, and the street grid
carries the eye through the city. This lane had roads at −15%, *darker* than
its buildings, so the town sat in a grey pool and the streets disappeared.

Building-face value matched to within a point (110.0 vs 110.7) before any of
this changed. The tone work of D2/D3/D5/D6 was sound; the board was not.

### The palette drops and widens — D6 amended

D6 locked seven timbers and their tones. The owner amended it on the
measurement: every tone scaled in **linear albedo, uniformly per channel**, so
hue and saturation are untouched and only value moves. The wood is exactly as
warm; it sits lower.

The scale runs **0.496 at the pale end to 0.263 at the dark end**, both solved
from measured frames (pale 165 → 120, dark 101 → 55) rather than picked.
Scaling the dark end harder is what WIDENS: the light/dark ratio opens 2.31 →
3.35 while every tone drops.

    maple  #DCC49F -> #A18F73      oak     #B18E62 -> #725A3D
    pine   #CDB088 -> #907B5E      cherry  #9C7A54 -> #5F4931
    ash    #C2A278 -> #836C4F      sapele  #8A6844 -> #4E3A24
                                   walnut  #6E5236 -> #392919

Result: roads +45% (B1 +50%), darks −55% (B1 −58%).

### What is NOT chased

Frame contrast sits at 46 against B1's 66.5 and should be left there. That gap
is COMPOSITION — B1 fills its frame edge to edge, and more than half of ours
is empty studio floor. Widening the palette further to close that number would
over-darken the wood to fix a framing problem. It closes with density.

---

## D14 — D11 §3 lifted, but only three ways. Owner, 2026-09-01.

D11 §3 locked the carving scope: no recessed openings, no carved window bays.
The owner allowed "a little lifting" **on condition of seeing it first**, so
five treatments were built on one geometry, one species and one light, with
the part cost quoted beside each — parts being this direction's currency.

| treatment | parts | cost | verdict |
|---|---|---|---|
| locked | 2 | — | the baseline |
| base | 3 | +50% | **admitted** |
| band | 4 | +100% | **admitted** |
| courses | 10 | +400% | **admitted** |
| flutes | 5 | +150% | **rejected** |

`base` is the only one that changes how the STREET reads rather than the
object: the ground course steps back, so a block meets the pavement with a
shadow line instead of a hard edge.

`band` gives a windowless mass one horizontal division, so height becomes
readable without an opening. It is a shadow, not a window — which keeps faith
with B1's windowless-by-day rule.

**`flutes` is rejected on a reason, not a preference.** Its channels run
vertically and so does the grain, so the treatment and the material say the
same thing and neither wins. It is the most expensive per unit of legibility
in the set. Recorded so a future session does not re-propose it as an
oversight.

Still forbidden, unchanged: recessed openings and carved window bays.
Everything admitted is a shallow recess made by emitting a narrower slab —
there is no boolean subtraction in this pipeline, so a shadow line is real
geometry or it is nothing.

---

## D15 — the form vocabulary and roof furniture. Owner, 2026-09-01.

### Form: four gestures, because one gesture is a monolith

Shown twenty blocks, the owner's note was explicitly **not** about height:
"the variety of shape and geometry and how the blocks still read as distinctly
styled buildings instead of blocks/monoliths". Heights are therefore untouched.

`build_mass` knew ONE move — concentric setbacks, every stage shrinking evenly
on four sides. Twenty blocks built that way are the same gesture at twenty
heights. Worse, B1's commonest block was not expressible at all.

  podium   wide low base, narrower shaft OFF-CENTRE. B1's commonest block; a
           centred shaft is a concentric setback renamed.
  bar      long low slab with an annex. B1 is full of them; this generator
           made none — every block it produced stood upright.
  ell      two arms meeting, one lower: a corner, an inner yard, two roof
           levels.
  stepped  setbacks on TWO sides only, so a building has a front and a back.

Distributed 5/5/4/3 with **three left plain on purpose**: if every building
has a gesture, the gesture stops being one. Cost 3–4 parts against the locked
prism's 2 — cheaper than a single `courses` treatment.

### Roofs: where B1 actually spends its detail

The carving study was aimed at facades. Re-reading the reference afterwards:
its WALLS are almost entirely plain and nearly every block carries two to five
elements on its ROOF. That is the correction, and it matters structurally — on
a windowless mass the silhouette carries everything, so a repeated top shows
far more than the same repetition would on an articulated facade.

Replaces the single jittered cap with a coping lip (two roofs in three), one
to four housings varying in count, footprint, height AND placement, and one
element in three tall and narrow rather than low.

**Cost quoted before it was spent, on the real set: 55 → 96 parts, +75%,
4.8 a building.** For scale, one flagship model is 130–800.

### Held, not forgotten

The tall elements bristle slightly against B1, which uses them sparingly. Fix
is one number — tall-element probability 1/3 → 1/6 — and one bake. The owner
accepted the pass as-is with this recorded.

### Composition rule

`form` and `roof` both default to None and emit the locked vocabulary
unchanged — `genbuild_identity` confirms 10 models unchanged after both. They
compose: roof furniture sits on whatever rect the FORM left at the top, so a
podium's off-centre shaft is furnished at its own footprint rather than at an
assumed centre. Carving composes with both, since every mass is emitted
through `_carve_stage`.

---

## D16 — wood ages, wears, rots and is refinished. Owner, 2026-09-01.

Wear was parked so edges, light and hand tolerance could be judged without a
third variable. All three were judged, the owner re-opened it, and then
corrected the first draft of this declaration — which is the useful part and
is recorded before the design it produced.

### The error worth keeping: three clocks, not one

The first draft said a wooden model does not get dirty, it gets HANDLED, and
built everything on that. The owner's correction: *"wood naturally wears and
naturally rots, ages, gets refinished. It is also being handled by the model
maker."*

Handling is one clock of three, and the draft collapsed all three into it:

1. **Game time** — the DEPICTED building ages. New, mature, neglected,
   renovated. This is the clock the player drives.
2. **Model time** — the BOARD is maintained over years. B3's reference shows
   exactly this: "visibly fresher blocks where the model was updated over
   years."
3. **Material time** — what TIMBER does unattended. Fresh-cut is pale and
   ambers with light and oxygen; it checks along the grain; neglected outdoor
   timber greys; sanding returns it to pale.

"Not dirt" is a correct CONSTRAINT and it is not a DESIGN. This is the design.

### The unifying idea: the model maker IS the ageing system

Every verb the player has, the maker performs on the board.

    build     ->  carve a new block: pale, crisp arrises
    upgrade   ->  pull the block, sand it back, refit it: pale again
    maintain  ->  handle it: arrises burnish, dust does not settle
    neglect   ->  leave it: it ambers, dust gathers, then it greys
    fail      ->  it chars through, and only replacement helps

This explains B3's locked patina rather than merely restating it. "New and
upgraded buildings start pale and age toward the board's honey tone" is not a
metaphor for newness: **sanding wood back genuinely returns it to pale
timber.** The mechanic and the material agree, which is the same kind of
agreement the roads study found between chord-lots and fitted inlay.

### The ladder — six states, all in wood's own vocabulary

| state | what the timber does | what it means |
|---|---|---|
| refinished | pale, crisp arrises, fresh cut | just built or upgraded |
| maintained | burnished arrises, settled amber, dust-free | attended to |
| settled | ambered along ITS OWN species curve | the default field |
| neglected | dust in the horizontals, arrises sharp and unpolished | nobody is touching it |
| rotting | grain lifts and frays, checks open, colour **greys** | neglect, or a failing strategy |
| burnt | blackened, surface alligatored, grain lost | failed |

**Polish means ATTENTION, not newness.** A long-loved block is old AND
burnished; a neglected one keeps sharp arrises because no hand has worn them.
That inversion is what stops the ladder reading as a simple age gradient.

### The find: failure goes COLD while health stays WARM

Neglected untreated timber weathers **silver-grey**. That is what real wood
does, and it means the whole health axis is one legible run of hue:

    pale  ->  honey  ->  dark amber  ->  silver-grey  ->  black
    new       settled      old            rotting        burnt
    <------------ WARM ------------>      <---- COLD ---->

A struggling district reads as **cold patches in a warm field, at board
range, with no UI at all.** Nothing needs a label, an icon or a tint that is
not timber.

### THE SPECIES PERSISTS. Owner's correction, 2026-09-01.

An earlier draft of this section said failure ERASES species identity — "by
the time it is charred you cannot tell walnut from maple". **That is wrong
and the owner corrected it:** the species stays the same and "ages/changes
states accordingly and accurately to that species".

Recorded because the correction makes the design better, not merely different.
A walnut block is walnut for its whole life. It ages as walnut ages, rots as
walnut rots, chars as walnut chars.

**Species do not age the same way, and one of them runs backwards.** This is
material fact, not styling:

| species | what light and time do to it |
|---|---|
| pine | yellows and oranges strongly, and FAST — the most visible ager here |
| cherry | darkens and reddens dramatically; the classic UV-darkening timber |
| sapele | darkens and reddens, more slowly than cherry |
| maple | ambers slowly toward gold from a near-white start |
| ash | mild amber; open grain frays first when neglected |
| oak | moderate amber, and the most characteristic SILVER-GREY when weathered |
| **walnut** | **LIGHTENS.** Walnut fades toward honey-brown under UV — the opposite of every other species in this palette |

Walnut running backwards is the reason this correction matters. A single
shared "age toward the board's honey tone" curve would have been WRONG for
one of the seven and slightly wrong for the rest, and nobody would have known
why the dark buildings looked stale.

**B3's locked patina survives, re-read once more.** "New and upgraded
buildings start pale" is not a hue reset toward white: sanding removes the
oxidised surface layer and returns a block to ITS OWN fresh state. Fresh-cut
walnut is light chocolate; fresh-cut maple is near-white. Both are pale
*relative to their own settled state*, which is all B3 ever required.

**Failure is per-species too.** Weathering does converge — UV and water break
down lignin in every timber, so all seven grey eventually — but the ROUTE and
the RATE differ, and open-grained species (oak, ash, sapele, pine) fray and
check visibly earlier than dense ones (maple, cherry). Char is black in every
species, but the alligatoring is coarser on open grain. **The species is
legible right to the end**, which is what the owner asked for and is also
what actually happens to burnt wood.

### How this settles D3 — more completely than the draft did

D3 gave tone to timber as IDENTITY. The correction strengthens that rather
than straining it:

> **The species owns its tone AND owns how that tone changes.**

There is no point in the ladder where a block stops being its species. D3
stands exactly as written, and ageing becomes a property OF the identity
rather than something that competes with it.

### Which forces the parameter split

Two different things vary, and they belong in two different places:

    per-INSTANCE (Custom Primitive Data)   HOW FAR ALONG this block is
        Age, Attention, Failure, Scorch

    per-SPECIES (the existing MI_wood_* )  WHICH WAY this timber goes
        oxidation direction (cherry darkens, walnut lightens),
        fray/check character, grey target, char coarseness

This is the same split the figure system already uses and proves: `GrainGain`
and `GrainMean` are per-species, derived from each mask's measured mean and
sd, while the per-instance state rides CPD. One number per building, one
character per timber, and no new material count — the seven MIs already
exist.

### Fire: a state AND an event, told apart by SHAPE

Owner, 2026-09-01: burning is a state reached by sustained failure, and also
a random event "to keep the game interesting" — but **a random fire must not
affect the trading that happens in that building.**

That constraint does real design work. If both roads to black looked
identical the player could not tell a misplay from bad luck, and the second
would feel like the first. The material tells them apart for free:

- **SCORCH — the event.** Fire burns **top-down**: roofs and upper faces
  blacken, the lower block is sound. Surface char, so sanding reaches good
  timber. **Repairable by refinishing. No economic effect.**
- **CHAR — the state.** Sustained failure blackens the **whole piece,
  uniformly**, through the timber. **Not repairable. The block is replaced** —
  the maker lifts out a charred piece and fits a fresh pale one, which gives
  demolish-and-rebuild a native language for free.

**Partial and top-down reads as accident; total and uniform reads as
failure.** Same colour, different shape, legible at board distance.

**No spread** (owner): fire does not pass to adjacent blocks, not even across
a party wall. Spreading fire with no economic effect would be drama without
stakes.

**It costs to fix** (owner). The refinish is not free. The amount is the
economy's business, not this lane's — named here because it is the SEAM where
wear touches the beta lane's work, and seams are cheaper named than
discovered.

### Recovery, and why the asymmetry is the mechanic

| damage | how deep | fix |
|---|---|---|
| dust / neglect | surface | attention |
| rot / grey | surface, deepening | refinish |
| scorch / fire | surface, top-down | refinish |
| char / failure | through the piece | **replace the block** |

**Neglect is reversible until it is not.** Everything above the line is
sanded back; char alone requires a new block. That is the whole risk curve of
letting a district slide, expressed in what timber physically permits.

### Where it lives — unchanged from the first draft, and not negotiable

**Per-instance Custom Primitive Data.** Four scalars:

    Age         oxidises along THIS SPECIES' curve (cherry darkens, walnut
                lightens). Irreversible except by refinish.
    Attention   edge burnish vs settled dust. Fully recoverable.
    Failure     0 -> 0.6 weathers toward THIS SPECIES' grey, 0.6 -> 1 chars.
                Follows the species' own route and rate; open grain
                (oak, ash, sapele, pine) frays and checks earlier than
                dense (maple, cherry). Never overrides the species.
    Scorch      blackens TOP-DOWN. Surface only, repairable.

D1 fixed patina at MATERIAL level and the structural argument still holds:
`genbuild_identity` hashes SINK RECORDS, boxes carry no material, so
per-instance scalars **cannot** move the manifest — impossible to dirty by
construction. A generator-level patina would touch box names or spec `wall`
values and land inside a contract that cannot be certified while the flagship
lane is dark.

The burnish half already exists: `EdgeWearWidth` / `EdgeWearLift` is a
curvature proxy that LIFTS value at the arris. It scored 0.00 on every board
this lane ever made, because `add_cube` leaves `max|n|` at 1 on every face.
The 14 uu chamfer on the baked masses gives it a surface for the first time.
**Attention is not a new system; it is an existing one, newly reachable.**

### The A/B plan — one variable at a time

Pairs at the show camera, on buildings, never on a study wall.

1. `Attention` 0 vs 1 on one block. Polish, or dirt?
2. `Age` ladder: does pale settle into the field, and is a refinished block
   conspicuous WITHOUT being loud (D3 criterion 3)?
3. `Failure` ladder: where does grey stop reading as weathering and start
   reading as damage? The failure state has a threshold; measure it.
4. `Scorch` vs `Failure` at equal blackness. **Can a reader tell accident
   from failure without being told?** If not, the shape distinction has not
   landed and the design is wrong, not merely under-tuned.

**Measurable companion:** sample a recess patch and an arris patch in the
same frame. Attention must RAISE the arris and leave the recess alone. If a
recess darkens, the mechanism is grime and the mechanism is wrong.

### PARKED NOTE — what an empty plot looks like on a wooden board

Not to be built now; recorded because the question is coming and this lane's
answer should exist before it is asked.

The beta lane is designing the "empty lot" state — an unowned parcel before
the player buys — for the test city in flagship language. B2 parked the same
question in ours: the white "proposed building" block.

A planning model already has a convention: an unbuilt plot is **bare board**.
Not a placeholder mesh, not a white block — the plot's own surface with
nothing on it, which is exactly what an undeveloped parcel looks like on a
real model. B2's white block reads as PROPOSED, which is a third state:
proposed is a design the maker has mocked up; unowned is a lot nobody has
touched.

So direction B may want THREE plot states where the flagship needs two:
**bare** (unowned), **white block** (proposed / bought but unbuilt), **timber**
(built). The middle is already parked and owner-open per B2. For the owner
when the beta session's empty-lot work surfaces, so both products answer in
their own language rather than one borrowing the other's.
