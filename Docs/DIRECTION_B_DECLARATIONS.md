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
