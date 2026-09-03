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

**CLOSED by the owner, 2026-09-02: TWO STATES, NOT THREE.** *"We shouldn't
show proposed blocks."* An unbought lot is **bare board**; a built one is
**timber**. B2's parked white-block idea is closed with it.

The reasoning that survives is the owner's own: *"players should be able to
build wherever board space is available... we just need to figure out the grid
behind the scenes so players feel like they have ultimate control of laying
out their city."* A proposed-block state implies the game has decided what
goes where, which is the opposite of that. Bare board says the space is
YOURS; a white block says the space is SPOKEN FOR.

---

### The wiring, built 2026-09-02, and the trap it walked around

Implementation began under the coordinator's window. The floor is measured,
the script is written, and the master edit itself is **not applied** — the
wire step was refused by the permission classifier in this session and waits
on the owner's own decision. What follows is design, recorded now because the
trap is worth more than the wiring.

**Where it lands.** `M_StacktownMaster` has **90 referencers and only 8 are
wood.** D16 puts wear at material level for good structural reasons, and the
price of that is a graph the flagship depends on. The four scalars are
ScalarParameters with `bUseCustomPrimitiveData` set and `PrimitiveDataIndex`
0..3 — so they stay named parameters an MI can still override for testing,
and read per-instance CPD in the game. No new node type, no new material.

**THE TRAP.** `EdgeWearLift` has exactly one consumer, `Multiply_1` pin B, so
the obvious splice is:

    lift' = EdgeWearLift * Attention          <-- WRONG

With `Attention` defaulting to 0 this sets edge wear to **zero on all 82
flagship materials.** It is not inert; it is the most destructive edit
available, and it wears the costume of a no-op — a new parameter, defaulted
off. The wooden board would never have revealed it, because the wooden board
does not render those materials. What is wired instead:

    lift' = EdgeWearLift * (1 + Attention * AttentionGain)

At `Attention = 0` that is `EdgeWearLift * 1.0`, exact in IEEE rather than
close. Negative Attention is settled dust, positive is burnish, **0 is
today**. `AttentionGain` is per-SPECIES (an MI override, no CPD), which is
D16's own split doing its job: the instance says how far along, the species
says which way.

**"Defaults to off" is a claim about the parameter, not about the expression
it lands in.** That sentence is the general form and it belongs beside D9's
half-repointed family.

**The proof standard, met before the edit rather than after.** D8's
split-proof rule requires the no-op half to prove itself by render on a
flagship material. Three details make it real rather than ceremonial:

1. **The floor spans a recompile, not two static captures.** POLISH_PROTOCOL
   records Lumen cache invalidation measuring 47.5 levels between captures of
   an identical scene. So the floor is: shoot, force a no-op recompile of
   this same master, shoot again. **0.7091 levels.**
2. **The crop is what the subject fills.** The first framing put the three
   flagship cubes in a tenth of the picture; a whole-frame diff would have
   averaged a real change into nothing. Re-framed, the floor rose 0.3904 ->
   0.7091, and higher is the honest direction — the noise lives on the lit
   surfaces, not the empty ground. Stored as fractions, not pixels, because
   `grad_p90` already proved a resolution change can move a window silently.
3. **Revert restores the connection BEFORE deleting nodes.** Deleting first
   would leave `Multiply_1` pin B dangling — the flagship's edge wear gone
   everywhere — which is worse than the edit being undone.

**Attention drives EdgeWearLift, not Age.** The relay that opened this window
said Age; D16 says Attention, and the inversion is the entire reason the
ladder does not read as an age gradient. Followed the declaration.

### THE SPECIES CURVES, MEASURED. 2026-09-02.

Age is built and shot. `BaseColor * lerp(White, AgedTint, saturate(Age))` —
inert twice over, since Age 0 returns White and `AgedTint` defaults white, so
a species that has declared no curve renders unchanged even at Age 1.

SE0 walnut and SW3 oak in one frame, same camera, same light, one variable:

| Age | walnut | oak |
|---|---|---|
| 0.0 | 42.13 | 102.58 |
| 0.5 | 44.81 | 100.57 |
| 1.0 | 47.02 | 97.35 |

**walnut +4.89, it LIGHTENS. oak −5.23, it darkens. 10.12 levels apart from
one Age value.**

This is the section's own argument stopping being an argument. D16 claimed
that walnut fades toward honey-brown under UV while every other timber in the
palette ambers and deepens, and that *"a single shared 'age toward the
board's honey tone' curve would have been WRONG for one of the seven and
slightly wrong for the rest, and nobody would have known why the dark
buildings looked stale."* Two species now visibly diverge under one number.

**The magnitudes are a first pass and the direction is the claim.** The seven
tint ratios in `wear_age.py` carry D16's directions, taken from real timber
behaviour; their strength is a dial for the owner's eye, not a measured
constant. Nothing downstream should treat those numbers as settled.

**And the limit belongs in the same breath as the result:** this ages by
SPECIES. Every walnut on the board ages together, because the per-building
channel does not arrive (below). Frames and their README are in
`Saved/DirectionB/wear/species/`, and the README leads with that limit rather
than burying it, because a reader who takes these frames for game behaviour
has been misled by evidence that is otherwise honest.

**Failure and Scorch were NOT shot.** Both are parameters connected to
nothing. A ladder on a floating parameter is three frames of renderer drift
wearing a label, and this pass came close to filing that report twice
already.

### CORRECTED, same day: the first Attention verdict used an INVALID test

The section below was written from two measurements, and one of them could
not have produced a result no matter what was true. **A ScalarParameter with
`bUseCustomPrimitiveData` set reads the PRIMITIVE's data and ignores the
instance's scalar override entirely** — so "overrode Attention to 5 on
`MI_wood_walnut`, arris moved −0.06" was a test of nothing. The verdict was
right; the reasoning under it was not, and a right answer reached that way is
worth no more than a guess.

**Retested with an instrument that works**: flip `bUseCustomPrimitiveData`
off, drive the parameter from the instance, restore the flag afterwards. Age
and Attention through the identical rig, same camera, same patch:

| driven from the instance, CPD flag off | delta | drift |
|---|---|---|
| `Age = 1` (per-species tint) | **−10.67 levels** | −0.14 |
| `Attention = 8` (7.4x on EdgeWearLift) | **−0.05 levels** | −0.05 |

Age moves the frame seventy-six times the drift. Attention does not move it
at all. **Attention's mechanism is confirmed dead, and Age's graph is
confirmed live**, both now on evidence that could have come out either way.

### AND THE ONE THAT BLOCKS EVERYTHING: CPD NEVER ARRIVES

Age works when driven from the instance and does nothing when driven through
Custom Primitive Data. Writing `CustomPrimitiveData.data` on the component
read-back verified — the array grows, the values land, the assertion passes —
and the shader ignores it.

D16 predicted this in its own footnote and this lane did not act on it: *"The
property's own description is 'Optional user defined DEFAULT VALUES for the
custom primitive data of this primitive' — that is the editor-set defaults
array, which is NOT the same thing as the runtime per-component values a
`SetCustomPrimitiveDataFloat` call writes."* The write went to the defaults
array. The shader reads the runtime one.

**This blocks the whole per-instance architecture, not just one channel.**
Age, Attention, Failure and Scorch all ride CPD by declaration, and none of
them can be driven per-building until the delivery is a
`SetCustomPrimitiveDataFloat` call rather than a property write. The four
scalars, the channel map, the splices and the species curves are all correct
and all currently unreachable from the game side.

**What still stands, and it is not nothing:** the Age chain is built and
proven, the seven species curves are written with walnut running backwards as
D16 requires, and the material can age a whole species at a time today. What
it cannot do is age ONE BUILDING.

### THE NORMALS HYPOTHESIS IS WRONG. Counted 2026-09-02.

The section below names welded or averaged bevel normals as the first suspect,
and the commit message repeated it. **It is disproven.** Read out of
`SM_WMass_w1230_tower` with GeometryScript rather than argued about:

| max&#124;n&#124; | faces | what the proxy would return |
|---|---|---|
| 1.00 | 72 | 0.00 — the flat faces, correctly |
| 0.71 | 144 | 0.97 — the chamfer facets |
| 0.58 | 48 | 1.00 — the corner triangles |

264 triangles, **72.7% of them non-axis, in the FACE normals and the SHADING
normals alike.** The bevel is present, hard-normalled, and is exactly the
geometry `edge_wear.py` was designed for. `mk_woodcat` needs no change and the
baker was never at fault. A suspect named from plausibility and left standing
for hours is how a wrong idea gets into a commit message; counting took one
script.

### WHAT WAS ACTUALLY WRONG: the proxy reads the SHADED normal

`Abs_0` — the front of the curvature chain — is fed by **`PixelNormalWS`**,
the normal *after* the grain normal map perturbs it. This master writes a
normal map (`PaperNormalAmount` 0.55, `MP_Normal` connected), so the proxy has
never seen a geometric facet normal on any board this lane made.

`edge_wear.py`'s own docstring states the intent: *"the geometry is entirely
axis-aligned boxes with 45 degree chamfer facets. So the world normal IS a
curvature proxy."* That is a geometric question, and the wiring answers a
shaded one.

**It also explains the failure's shape**, which nothing else did: driving
`EdgeWearLift` moved the flat face **+0.21** and the arris only **+0.17** — the
face moving MORE than the edge. A normal-mapped flat face is perturbed
off-axis across its whole area, while the chamfer's own 45° signal is swamped
by the same perturbation.

Swapped to `VertexNormalWS` **on the fork only** — the flagship's master keeps
its wiring, being no longer this lane's to correct.

### AND THE FIX DID NOT WORK, which is the part that matters

Against a drift floor of **0.478**, driving `EdgeWearLift` to 12 through the
corrected proxy peaks at **0.572**. Signal/drift **1.20**. That is not a
result.

So: a real defect is found and fixed, and **at least one more cause is still
out there.** The defect is not being presented as the answer. A plausible fix
that does not move the frame is the exact shape this document has caught four
times now, and calling it closed because the story is satisfying would be the
fifth.

**Next, scoped and untested:** `Multiply_1`'s A input is `Multiply_24`
(`VectorParameter_0` x `Add_12`, the base albedo path), and its output goes to
`LinearInterpolate_2` pin B with the curvature mask as Alpha. If the lerp's two
ends sit close together, a 70x lift on B still barely moves the result. One
trace and one A/B.

### THE ATTENTION MECHANISM DOES NOT WORK. Measured 2026-09-02.

D16 above says: *"The burnish half already exists: `EdgeWearWidth` /
`EdgeWearLift` is a curvature proxy that LIFTS value at the arris. It scored
0.00 on every board this lane ever made, because `add_cube` leaves `max|n|`
at 1 on every face. The 14 uu chamfer on the baked masses gives it a surface
for the first time. **Attention is not a new system; it is an existing one,
newly reachable.**"*

**That last claim was a prediction, and it is false.** Measured on a shipped
`SM_WMass_*` at a close camera, on the dressed play board:

| what was driven | how far | arris response |
|---|---|---|
| `EdgeWearLift` default, in the master | 1.42 -> 12.0, an 8.5x lift | none |
| `Attention`, overridden on `MI_wood_walnut` | 0 -> 5, a 5x multiplier | −0.06 levels — INVALID TEST, see the correction above; kept because the record of how a right answer was nearly reached for a wrong reason is the useful part |

The column profile settles it. The pixels that respond most to Attention
0 -> 5 are **the same columns that respond most to a 0 -> 0 comparison**, and
the pure-drift response is TWICE as large: peak signal 0.855 against peak
drift 1.775, a signal-to-noise of 0.48. The mechanism is not weak. It is not
there.

**The wiring is not what failed**, and that distinction matters for whoever
picks this up. The four scalars are present on the instance and readable
(`Age`, `Attention`, `Failure`, `Scorch`, `AttentionGain` all list on
`MI_wood_walnut`), the CPD channels match `cpdmap.py` under its double-entry
self-test, and `MI_wood_*` does not override `EdgeWearLift`, so the master's
value does reach it. Everything the wire was responsible for arrived. The
thing it arrived at was already inert.

**The chamfer geometry is almost certainly present**, so that is not the
cause either: `fastbake.py` refuses a bake where bevelled parts average under
20 triangles each ("a chamfered box is 44 triangles, a sharp one 12"), and
`mk_woodcat.py` bakes the shipped catalogue at `CHAMFER = 14.0`. A chamfer
that did not take would have failed the bake, not shipped silently.

**~~Which leaves the normals as the first suspect.~~ DISPROVEN — see the
count above. Kept because the reasoning below is exactly how a plausible
suspect becomes an assumption.** The proxy is
`saturate((1 - max|n|) / 0.30)`, and it only separates a chamfer from a face
if the chamfer facet carries its OWN normal. Averaged or welded vertex
normals across the bevel would leave `max|n|` high on the facet and slightly
below 1 on the faces — which is what the measurements weakly look like: the
flat face moved +0.21 and the arris +0.17, the face moving MORE than the
edge. Unconfirmed; it is the next thing to test, not a finding.

**What this costs D16.** The six-state ladder's Attention rung has no
mechanism behind it. Polish-as-attention — the inversion that stops the
ladder reading as a simple age gradient — cannot be shown until either the
bake emits hard normals on chamfer facets, or Attention drives something
other than the curvature proxy. **Age, Failure and Scorch are untouched by
this**: none of them depend on edge curvature, and all three remain wired,
inert at 0, and ready. Attention alone is blocked.

**The measurement traps this pass walked into, all of them the same shape.**
Recorded because three separate readings were nearly reported as findings:

1. A whole-frame mean over a subject occupying a tenth of the frame. The
   flagship floor read 0.3904 and was 0.39 of empty ground.
2. A "floor" of 0.7091 taken between two fast captures, used to convict an
   edit at 2.13 — when doing NOTHING for 75 seconds produces 2.58. Fixed by
   cycling wire and revert repeatedly so drift hits both populations and
   cancels: across a wire 0.3498, across a revert 0.4951, one population.
3. An "arris patch" 62 px wide over a chamfer about 11 px wide — 80% flat
   face, diluting the very thing being measured by roughly five times.

Every one of them would have reported a confident number about the wrong
pixels. The column profile is the instrument that finally answered, because
it asks the frame WHERE it responded instead of being told where to look.

## D17 — the wooden catalogue mapping. Phase F, 2026-09-01.

Phase F was pulled forward when the owner's first successful in-game buy
produced a FLAGSHIP building. The game must wear the wooden city. The beta
lane wires `DA_Catalogue_Wood` and the pointer swap; this lane owns the
MAPPING — which wooden mass each catalogue key resolves to.

`Content/Python/woodmap.py` is that mapping and `mk_woodcat.py` bakes what it
resolves to. They build asset names from the same function, so the baker and
the resolver cannot drift, and the bake ASSERTS its table equals
`woodmap.catalogue()` before it finishes. A pointer resolving to an asset that
does not exist is the failure the owner just hit from the other direction.

### The width gap, which blocked the obvious approach

Flagship lots run **820–2460 uu**. The 20 masses baked for the look study run
**600–1000**, because they were sized for a demo board and nobody ever asked
them to fit a parcel. A mass from that set covers as little as **41% of a wide
lot's frontage** — it would sit marooned in the middle of its plot.

So the wooden catalogue is re-parameterised onto the flagship width ladder.
That costs nothing: the same vocabulary, the same generator, the same three
minutes, and every key now resolves to a mass that fits its parcel exactly.

### The corner correction — and how the error was made

An earlier draft of this mapping argued that corner variants were a
flagship-only problem: a flagship corner needs a handed variant because its
facade is articulated, and a wooden mass has no blank flank. It cited
`DEPTH_CORNER_DECISIONS.md` — **and cited the sentence that document
retracts.** Its own words:

> "This section originally claimed the protruding corner presented a blank
> party flank... That was wrong on the second half, and the correction matters
> more than the finding."

**A withdrawn claim inside a real document is more dangerous than a wrong
guess, because it arrives wearing a citation.** A guess sounds like a guess.
A retracted line is in the repo, on topic, quotable, and grep finds it — and
this project's docs are *written to record corrections*, so they are full of
superseded statements sitting next to the truth. The rule that follows: when a
document supplies the decisive quote for an argument, read the section to its
end before using it, and look for "originally claimed", "that was wrong",
"superseded". If a quote is doing a lot of work, that is when to check it
hardest.

### What the document actually says, and what carries over

The real reason for `DEPTH_CORNER = 1500` is **occupancy, not facade**: "the
deep value is the PARCEL DEPTH: a corner fills its lot front to back", and a
corner at base depth "leaves the back half of its parcel empty".

**That reason is fabrication-independent.** A 700-deep wooden mass on a
1500-deep corner lot leaves half its plot bare, and bare plot is exactly as
visible in timber as in card. So corners DO apply here.

**Handedness does not.** `_cL`/`_cR` exist so an articulated facade turns the
right way; a solid block is the same block whichever way the street runs.

> **Depth survives. Handedness dies.** Corner is a DEPTH PARAMETER in wood,
> not a variant axis — which is the twin rule working properly: the two
> fabrications share the constraint they both have and diverge on the one
> only card has.

### The mapping

    tier     flagship 0..6 -> four bands: 0-1 flat, 2-3 setback1,
             4-5 setback2, 6 tower
    width    must be ON the ladder. Off-ladder RAISES rather than rounding -
             a wooden mass must fit its parcel exactly, and a silent round is
             how the city stops being the one that was pinned
    corner   -> depth 1500 instead of 700. Never handed. Corner lots are
             1230/1640/2050/2460 and never 820, so no deep mass exists at the
             narrowest width and asking for one RAISES
    species  per RECIPE ID, stable across every tier and width — D3's "a
             building does not repaint itself when it gains a storey". crc32
             rather than hash(), so it does not repaint on restart either

**36 assets**: 5 widths x 4 bands, plus 4 corner widths x 4 bands deep.
Species is NOT baked in — the material is bound per instance, which is why 36
masses serve a catalogue of hundreds of keys.

### The caveat, flagged rather than buried

These masses were designed to be LOOKED AT on a demo board, not lived in
across 11 buyable lots and 7 tiers of growth. Four tier bands is coarse on
purpose — v0 ships fast because the owner is waiting on a wooden game.

**Whether four bands READ as growth when a player watches a building climb is
a look question nobody has asked yet.** It will need frames, not argument, and
the owner seeing it live is the test.

---

## D18 — TestCity's lighting rig is this lane's. Owner, 2026-09-02.

**Owner's word, verbatim through the coordinator: "RIG IS DIRECTION-B'S NOW."**

TestCity is the wooden game's map, so the lights that actually reach the board
— `CITY_Key`, `CITY_Fill`, `CITY_Sun`, `CITY_Sky` and the studio room's light —
are this lane's to study and tune. Recorded here so the next reader does not
re-litigate a boundary that has moved.

**What this reverses.** Until today those lights were another lane's shared
scene state and explicitly out of bounds; the lighting study's own closing
section says so — "Option 2 is not [mine], and the boundary matters more than
the study." That reading was correct when written and is now superseded.

**What is unchanged.** Flagship maps keep their rigs untouched:
`Sandbox_Bench`, `Stage2_*`. The boundary moved for TestCity only, because
TestCity became the wooden game's map. "Your lane is only to help design-b"
still governs everything else.

### LIGHT_BoardKey is retired

Measured 2026-09-02: switching it fully off changed the frame by **0.06 luma
levels**. It has never lit anything. It sat at intensity 26 while the city
rig's rect lights measure 2.0 x 10^7 — a units mismatch, present since the day
it was placed and approved.

It is removed rather than repaired, and the reason is the trap it became: **a
second rig with no authority is worse than no second rig**, because it draws
tuning effort, earns approval, and absorbs a design decision — the soft-source
argument — that was never in effect. `board_light.py` goes with it.

### The study restarts on the real instrument

Null-first on **each** `CITY_*` light before any ladder: switch it off, capture,
confirm the frame changes. Only lights that demonstrably move the frame get
tuned. Then source size, then the ranked mechanisms of `LIGHTING_STUDY.md`.

This is the guard that null result bought, now standing doctrine: **before
tuning a parameter, switch its owner off and confirm the frame changes.**
Applied here to four lights before a single value is touched.

---

## D19 — the studio surround. Owner's verdict, 2026-09-02. Design only.

**The owner's verdict on the first wooden play board:** the timber, the species
ladder and the chamfers read as wood. What still says *rendering* is **the
floor and the backdrop** — a shadowless uniform beige plane under a flat grey
sky.

That is founding failure 5 in a lighter shade. The doctrine already says it:
*"a model in a black void is a render; a model in a lit room is a model."* Ours
is no longer a black void. It is a beige one.

### What B2 actually shows, which is not what the brief assumed

The brief asked for a table surface with grain and falloff. Reading B2 — the
honey city photographed on a table in a studio — that is **not** what makes it
read as a photograph:

- **There is almost no floor in the frame.** The model fills it and runs off
  every edge. There is no expanse of visible table at all.
- **The board's own RIM is dark and prominent** — a deep timber edge banding
  the model, which is what says "object with a boundary" rather than "terrain
  extending forever".
- **The backdrop is a wall with a TONAL GRADIENT**, cool and neutral against
  the warm wood, darker at one corner than the other. Not a flat field.
- **Depth of field does the rest** — the far edge of the model is soft, so the
  surround is mostly *out of focus*, which is a large part of why so little of
  it needs to exist.

**So the surround problem is at least half a FRAMING problem.** A photographed
model fills its frame; ours sits in the middle of acres of empty floor and the
floor is therefore doing work it should never have been asked to do.

### The four candidates, ranked by what the reference supports

1. **THE BOARD EDGE.** A deep, dark rim around the plate. B2 has one and it is
   the single most "object on a table" cue in the image. Cheapest of the four
   and the only one that is pure geometry — no lighting, no material study.
2. **FRAMING.** The play pose shows the whole board plus surround. B2 crops
   in. Whether the boom's default pose should sit lower and closer is the
   owner's call, and it costs nothing to test.
3. **THE BACKDROP.** A wall with a tonal gradient, cool against the warm
   timber, rather than a flat grey sky. The studio room already has walls;
   whether they are in frame from the play pose is the question.
4. **FLOOR FALLOFF.** The board should be the brightest thing on a surface
   that darkens toward the edges. Ranked LAST of the four because B2 barely
   shows floor — this is the one the brief led with and the reference supports
   least.

### The honest complication

**The play board is sparse.** Fourteen buildings cannot fill a frame the way
B2's several hundred do. Some of the emptiness the owner is reading as "floor
problem" may be a DENSITY problem wearing a floor's clothes, and the density
board — 476 buildings — is the control that would tell them apart.

That comparison is free: both boards exist, and the same framing on each
answers whether the surround or the sparseness is doing the damage. **It
should be shot before any of the four candidates is built.**

### Method

Null-first and A-B-A as standing doctrine, matched resolution against B2 for
every comparison, subject named in line one of every README. But this is a
LOOK study before it is a measurement: pairs to the owner's eye, and the
numbers exist to say which mechanism moved what, never which frame is right.

**Boundary — the OWNER'S OWN WORD, 2026-09-02:** *"Yes — the room is theirs
too."* TestCity's studio room — floor, walls and backdrop, and `LOOK_Post` as
it affects the room — sits inside this lane's grant alongside the lights.
Flagship maps keep their rooms untouched.

This replaces the coordinator's extension of D18, which was recorded here
first so the owner could veto it and was then put to them explicitly. The
distinction matters and is kept: a boundary that moves should move in the
owner's words, not in a relay's reading of them.

---


### The room has TWO masters, and nobody had mapped the second

Recorded 2026-09-02, after the studio room rendered magenta in PIE and the
shared master was the obvious suspect:

| actor | material | parent |
|---|---|---|
| `CITY_Room_Floor` | `MI_studio_grey` | `M_StacktownMaster` |
| `CITY_Room_N/S/E/W` | `MI_studio_wall_city` | **`M_StudioWall`** |

`M_StudioWall` is built by `mk_studioroom.py` and is **UNLIT emissive** — a
sound-stage cyclorama that ignores every light in the level, with
`use_emissive_for_dynamic_area_lighting` off so its emission stays out of
Lumen GI and the room contributes provably zero light to the board.

**Why this matters beyond bookkeeping.** Both the floor and the walls were
reported magenta, and the shared master — which this lane had edited and
reverted — was the natural culprit. But only the FLOOR descends from it. The
walls descend from a second master this lane never touched, and an unlit
material has no lighting path to invalidate in the first place. So the shared
master cannot be the whole cause, and possibly not any of it.

D19 gave this lane the room. It did not give this lane a map of the room, and
"the studio surround is ours" quietly implied one master where there are two.
Anyone reasoning about the room's look — the backdrop gradient, the floor —
now has both.

## D20 — the growing plate. Owner, 2026-09-02. Design only.

**Owner's word:** *"small plate that grows... players should be able to build
wherever board space is available (we can constrain the board size at first so
they can't travel into the void and drop a building) we just need to figure out
the 'grid' behind the scenes so players feel like they have ultimate control of
laying out their city."*

The placement grid and its data model are the beta lane's (`PLACEMENT_GRID.md`,
with roads folded in, since drawn roads and placement are one system). **This
declaration is only what a growing plate LOOKS like.**

### The principle, which B3 already supplies

B3's board *"reads as MANY FITTED INLAY PIECES making the landscape; that
visible pieced construction is part of the look."*

So the plate does not stretch, scale or fade in at its edges. **It grows the
way a real planning model grows: someone cuts another piece and fits it.** The
seam where two pieces meet is not concealed — it is the evidence that a person
built this, and it is the same argument as D12's hand tolerance and D14's
wedges. Every time this direction has been asked to hide a fabrication mark, it
has been wrong to.

### A new piece arrives PALE, and ages into the board

This is the part that costs nothing because it already exists.

D16 gives every timber an `Age` scalar that oxidises along its own species
curve, and B3's locked patina says new work starts pale and settles. **A
freshly cut plate piece is fresh timber.** So a newly added piece arrives at
`Age` 0 — visibly paler than the board around it — and ambers into the field
over game time.

That makes **expansion legible with no UI at all**: the newest ground is the
palest, and the board carries its own history the way B3's reference does with
*"visibly fresher blocks where the model was updated over years."* The player
can see where their city grew last, and how long ago, by looking at the floor.

**The seam never fades; the tone difference does.** Piecing is permanent
construction; age is a finish.

### The growing edge shows END GRAIN

A model-maker's board in progress has a raw sawn edge where the next section
will go. End grain is what a cut across the grain exposes, and this lane
already renders it — the polar-sampling master edit, the thing that first made
a maple block's top read as a block cut from a log.

So: **the outer boundary of the current plate shows end grain**, raw and
unfinished, saying "this is where the board stops for now". When a piece is
fitted beyond it, that edge becomes an interior seam and its end grain is
covered. The board's frontier is visibly a work in progress, which is exactly
what the owner's constraint ("constrain the board size at first so they can't
travel into the void") should look like rather than an invisible wall.

D19's dark RIM is then the finished outer edge — and it must **move** as the
plate grows, because a rim is a trim piece a maker re-fits, not a boundary the
world has. Rim on the finished side, end grain on the frontier.

### The piece quantum — a PROPOSAL, to be reconciled with the beta lane

This lane does not own the grid, but the piece size must land on the quanta
that already govern everything:

    catalogue WIDTH_QUANTUM   410      (nothing may violate this — D-roads §3)
    citylayout BLOCK_LEN     4920      = 410 x 12
    citylayout BLOCK_DEPTH   1500
    woodlayout STREET         560

**Proposed: one piece = one city block plus its bounding streets**, on the 410
quantum. It is the smallest unit that is a *place* rather than a fragment — a
piece the player recognises as "a block of my city" — and it means a plate
grows by whole blocks, never by half a building.

**The quantum is the beta lane's to set**, and if their grid wants a different
unit this lane follows it; what must survive is that the piece is a WHOLE
number of 410s and contains complete blocks, because a seam running through a
building is the one thing the fitted-piece language cannot survive.

### What is NOT proposed

- **No proposed-block state.** Closed by the owner in the same breath: an
  unbought lot is bare board. Bare board says the space is yours.
- **No fade, scale or dissolve on arrival.** A piece is fitted. If it needs a
  moment of motion, it is a piece being set down, not an object materialising.
- **No hidden seams.** See the principle.

### What was asked, kept verbatim so the answer has something to answer

1. Does the plate grow **automatically** as the city reaches its frontier, or
   is fitting a piece **a thing the player does**? B3 makes terraforming and
   water-laying build verbs; extending the board could be one too, and that
   would make the plate itself part of the game rather than its container.
2. Does the **rim** move with every piece, or does the board run to a raw edge
   until the player chooses to trim it? The second is more honest to the craft
   and gives "finishing your board" a meaning.

### Answered by the owner, 2026-09-02, relayed via the coordinator

Both questions came back as one answer: **BOTH AUTOMATIC.**

1. **Fitting a piece is not a player verb.** New pieces appear when growth
   triggers fire, and the rim follows. The board is the **container**, not part
   of the game's action.
2. **The rim moves automatically.** There is no trim verb; the player does not
   shape the frontier deliberately.

This closes the more interesting half of the proposal against itself, and it
should be said plainly rather than buried: the "finishing your board" reading in
question 2 — a raw edge the player chooses when to trim — is **rejected**, and
the "plate as a build verb" reading in question 1 is **rejected**. What survives
is everything above about how a piece LOOKS when it arrives, and nothing about
who makes it arrive. That is a smaller declaration than the one this section
opened with, and it is the right size: the plate is scenery that keeps up with
the city, not a thing the city is played on.

### Growth is not scheduled yet — this declaration is DECLARED, NOT BUILT

Owner, same relay: growth is **purchase-fill only at first.** No plate expansion
in early versions. The beta lane builds a placement v0 — click-to-place along
the existing arterial, small hard-edged plate, no growth
(`PLACEMENT_GRID.md` §7).

So everything in D20 that describes **arrival** — the pale new piece ageing into
the board, the raw end-grain frontier, the moving rim, the visible seam — has no
trigger to fire it and **is not to be built.** It stays declared, in this
document, waiting. When growth is scheduled, this section is the brief; until
then a lane that builds any of it is building for a mechanic that does not
exist.

What is NOT parked, because purchase-fill is shipping: **bare board is the
correct look for an unbought lot** (above, "no proposed-block state"), and the
plate's hard edge is a real edge the player is refused at, not a fade. Those are
live requirements for v0.

### The quantum needed no meeting

`PLACEMENT_GRID.md` §3 adopts this lane's hard requirement **verbatim and as a
requirement**, not as a preference it is free to soften: a plate piece must be a
whole number of 410-uu quanta AND must contain complete blocks. It also defers
to the proposal above — **one piece = one city block plus its bounding
streets** — as the natural unit, noting it is exactly the shape
`citylayout.py`'s `blocks()` already produces.

Read on disk by this lane, not accepted on the relay's word. Two lanes agreeing
about a number is exactly the kind of claim that has been wrong before in this
document (see D17's retracted citation), and the cost of opening the file was
one command.

### The camera consequence, flagged by the beta lane and owned there

`PLACEMENT_GRID.md` §3 closes by flagging that a growing plate breaks the boom's
hardcoded `BoardCentre` (currently `(0,0,0)`) and its `Reach` clamp
(300..40000), both sized to the 14-lot board. That is their math and their
flag; recorded here only so this lane does not later "discover" it as new. It
is parked with the rest of growth.

---

## D21 — the twin stops sharing a master. Owner, 2026-09-02.

**Owner's word:** *"nothing we're doing in this direction B wood city should be
affecting the flagship models or the teams handling the flagship project for
now. these are separate projects with different yet similar looks. The wood
city is an easier to render and scale version that we can then hopefully borrow
some mechanics for flagship down the road."*

### This lane argued the other way and was overruled

The argument against forking was real and is recorded rather than quietly
dropped: `M_StacktownMaster` is 195 expressions, and the grain, paper, seam and
end-grain work all fork with it. Two masters means a fix to one is not a fix to
the other, and the twin rule was supposed to mean both cities speak one
fabrication language.

**The owner's principle outranks it, and the reason is in their own sentence:
"separate projects."** A twin that shares a master is not a market test, it is
a skin — one lane's experiment lands in the other lane's product, and the
flagship team inherits changes nobody on that team approved. What the twin
shares is a *vocabulary*, not an asset. That reading also makes "borrow some
mechanics for flagship down the road" possible in a way the shared master
quietly prevented: you cannot borrow selectively from something you are
already forced to share.

### What was done

- The shared master was **reverted to exactly the flagship's state** — 195
  expressions, `BaseColor` back on `LinearInterpolate_3`, `Multiply_1` pin B
  back on `EdgeWearLift` — and verified by read-back, not by intent.
- **`M_WoodMaster`** duplicated from it. Direction B's wear lives there and
  only there. 210 expressions with the four CPD channels, the Attention splice,
  the Age chain and the `VertexNormalWS` correction.
- **Nine instances re-parented**: the seven `MI_wood_*`, plus `MI_board_plot`
  and `MI_board_road`.
- **`MI_model_board` and `MI_studio_grey` left alone.** Both are referenced by
  flagship maps. `MI_studio_grey` is referenced by TestCity too, and the rule
  would say duplicate — but USING an unchanged shared material changes nothing
  for the flagship, and the studio room's actors are persistent saved content,
  so a per-session repoint would be "looks done but isn't" wearing a script.
  When D19's room work actually needs to edit it: duplicate, repoint once,
  saved on the owner's word.

### The boundary is structural, not remembered

`Content/Python/cpdmap.py` owns the channel map. `Content/Python/woodmaster.py`
owns which master this lane may write to, and names the shared one **only** so
`assert_not_shared()` can refuse a write aimed at it. Both wear scripts read
their target from there.

That mattered immediately: `wear.py` and `wear_age.py` each had the shared
master hardcoded a **second** time, inside the strings they hand to the
programmatic toolset. Retargeting the module constant alone would have left
them rebuilding the wire on the flagship's master while every line of the code
read as though it pointed at the fork.

### The zero-referencer trap, worth its own line

`MI_board_plot` and `MI_board_road` reported **zero referencers** — which reads
as "dead asset, leave it." They are not dead: `wood_set.py`'s `BOARD_STOCKS`
declares both and `ensure_board_mis()` creates them at rig build time, applied
to `ZONE_SetBRoad` and `ZONE_SetBPlots`. The referencer graph was a snapshot of
a board that happened to be **down**. **Provenance overrides the snapshot** —
and the reading that would have got this wrong was true, just not about what it
appeared to be about.

---

## D22 — the ghost pad. Look only, 2026-09-03.

The driver draws a debug box today and that is right for proving the resolver.
This is what it should LOOK like once the feel is settled. Asset creation waits
for a grant; nothing here is built.

### What the ghost IS

**A piece of board that has not been carved yet.** Not a hologram, not a
selection rectangle, not a highlighted tile. The plate is a pale timber ground
at `#BEB19F` with pale inlay ribbons at `#DFD6C9`; a ghost is the moment before
a maker cuts a block — the outline chalked on the stock.

That reading gives the accept state its colour for free and rules out the
obvious alternative, below.

### Accept: pale fresh-cut timber, not green

    fill      #DFD6C9   the road inlay's exact tone, at 0.34 opacity
    edge      #F2ECE1   a 6 uu proud rim at 0.85 opacity
    height    40 uu above the plate — proud, so it casts a faint shadow

**Green is rejected, and the reason is not taste.** A saturated green would be
the only green in the entire frame, which does make it unmissable — and makes
it the one thing on the board that is obviously software. Every other decision
in this direction has been to remove the tells that say a program drew this
(D14's admitted carvings, D12's hand tolerance, the HUD's paper-then-bar, the
board's visible seams). A green ghost spends all of that on a hover state.

The pale-timber ghost is legible for a different reason: **it is the only thing
on the board with a soft edge and no grain.** Presence, not hue.

### Refuse: red, and red is CORRECT here

    fill      none — no fill at all
    edge      #B4472E   the same 6 uu rim, 0.9 opacity, no proud offset
    plus      the refusal text at the cursor, per PLACEMENT_GRID §2.1

**A refusal is a UI event, not a material state**, and it SHOULD look foreign.
Nothing in a wooden model is red; that is exactly why it reads instantly and
why it does not have to belong. The asymmetry is deliberate: accept speaks the
board's language because it is a promise about the board, refuse speaks the
interface's language because it is a fact about the rules.

**And the fill goes away on refusal, which does more work than the colour.**
A red-filled rectangle still looks like a thing being placed. An outline with
nothing in it looks like an outline — the shape says "no block here" before the
hue says "not allowed".

### It has to read at the boom's distance, which sets the edge

The first-boot framing is reach 19000 (`study_pose.json`). An 820 uu pad at
that distance is a few dozen pixels across, and the zoom ladder runs in to
1350 and 800.

**At the far stop a fill of any opacity is a smudge and the EDGE is the whole
signal.** So the rim is specified proud (40 uu) rather than flat: at distance
it catches the key light and reads as a bright line, and a bright line survives
downsampling in a way a 34%-opacity wash does not. The fill matters at the
close stops, where it stops the ghost reading as a wireframe.

That is one look serving both ends of the ladder, which is the constraint the
camera study already established: nothing may be tuned for one zoom stop.

### Mechanism — and the channel it must NOT use

**Not CPD channel 3.** PLAYABLE_PLAN §2.1 offered "Selection" for the ghost
tint, and the channel is reserved for exactly that in `cpdmap.py`. But Custom
Primitive Data does not reach the shader on this setup: the component property
is the editor-set DEFAULTS array while the shader reads runtime values only a
`SetCustomPrimitiveDataFloat` call writes. **A CPD tint would read back as set
and draw nothing.**

So: **a translucent MI on the ghost component only** — two instances off
`M_WoodMaster`, `MI_ghost_accept` and `MI_ghost_refuse`, swapped by the driver.
Two assets, no runtime channel, no dependency on anything unproven.

**AND THE DETAIL THAT MAKES IT WORK, without which this fails silently.**
Blend mode is a MASTER-level property, and `M_WoodMaster` is `BLEND_Opaque`
(read 2026-09-03). An instance cannot be translucent by setting an opacity
value alone — it must also carry the base-property override:

    bOverride_BlendMode = true
    BlendMode           = BLEND_Translucent
    then the Opacity scalar

The fork is ready for this and needs no change: **`MP_Opacity` is already
connected**, driven by a ScalarParameter (`Opacity`, default 1.0), so once the
blend mode is overridden that parameter does real work. Checked, not assumed.

Without `bOverride_BlendMode` the instance renders fully opaque and the
Opacity parameter does nothing — it sets, it reads back, and it draws a solid
block. That is the same shape as the CPD failure this declaration exists to
route around, and it would be found by the owner rather than by a test. **The
proof frame is what catches it: a ghost that is not see-through is not a
ghost.**

The cost is one extra shader permutation per instance, which for two assets is
nothing worth trading the look for.

**Proof, per this lane's own rule: a MEASURED FRAME at the far stop and at a
close stop, accept and refuse, or the look is not accepted.** Opacity and the
rim width are the two numbers most likely to be wrong on the first pass, and
neither can be judged from the arithmetic.

### The rim: GEOMETRY, and the far-stop capture already ruled out the alternative

Ruling 2026-09-03, after the coordinator's capture showed the translucent fill
alone does not read at the boom's far stop — which is what this declaration
predicted, and the prediction is now the evidence.

Three ways to make the rim, and two of them lose for the same reason:

- **A material border** (distance-to-edge in UV or from object bounds). It
  draws a band of a different colour on a flat surface — which is *another
  flat wash*, and a flat wash at the far stop is exactly what just failed. It
  would also stretch with the pad's scale unless the bounds are passed in,
  since the ghost is a scaled cube and UV space scales with it.
- **Fresnel.** Does not apply. Fresnel needs viewing-angle variation across
  the surface; a flat pad seen from a fixed 25 degree boom tilt has almost
  none, so the term is near-constant across the whole quad and produces a
  wash, not an edge.
- **Geometry — take this one.** A raised lip is a real surface at a different
  angle to the key light, so it returns a genuinely different luminance rather
  than a different colour at the same luminance. That is why D22 said *proud*
  rather than *outlined*: at distance the signal that survives downsampling is
  a lit line, and only geometry produces one.

**The shape: a purpose-baked ghost pad, not a scaled cube.** A shallow slab
with a raised border, emitted through the same `fastbake` path as the masses so
it carries the catalogue's chamfer and pivot conventions — front-left origin,
so it drops straight into the placement offsets the driver already applies. One
component, one material, real lit geometry, rim included. It is the smallest
asset this lane would ever bake and it removes a debug-draw call from the
hover path.

**The debug outline stays until that exists**, and it is not a stopgap to be
ashamed of: a debug line is drawn at constant screen width, which is precisely
why it reads at every zoom stop. What it cannot do is belong to the board —
it is unlit, it ignores occlusion, and it reads as a wireframe. So it is
correct for proving the resolver and wrong for the shipped look, which is the
same distinction D22 drew between a refusal (interface language, allowed to
look foreign) and an accept (board language, must belong).

### The dimensions, and the arithmetic corrects this declaration's own number

**D22's 6 uu rim is wrong and would not have read at all.** Worked from the
actual pose (`study_pose.json`: fov 73.74, the boom's reach ladder) at the
2802 px capture width:

| reach | uu per pixel | a 6 uu rim | a 45 uu rim |
|---|---|---|---|
| 19000 (survey) | 10.2 | **0.6 px** | 4.4 px |
| 3500 (working) | 1.87 | 3.2 px | 24 px |
| 1350 | 0.72 | 8 px | 62 px |
| 800 (closest) | 0.43 | 14 px | **105 px** |

Six uu is **sub-pixel at the survey stop** — the exact failure this section was
written to prevent, specified inside the section that prevents it.

**And no single height satisfies both ends.** The ladder spans 19000 to 800, a
24:1 range; a rim that reads at the survey stop is a 105-pixel kerb at the
closest one. That is not a number to be tuned, it is a contradiction.

**The contradiction dissolves because the survey stop is the wrong target.**
The owner's camera ruling: *"player should be able to zoom out to see most if
not all of the gameboard, but the main view would be closer in."* The ghost is
a **placement affordance** — it exists while the player is choosing where to
build, and that happens in the working view, not the survey view. Sizing it for
19000 optimises the one stop at which nobody places anything.

So D22's far-stop argument, which the capture appeared to confirm, was aimed at
the wrong stop. The capture was right that a flat fill does not read; the
conclusion drawn from it — make the rim survive the survey stop — did not
follow.

**Rim: 12 uu proud, 60 uu wide in plan.** 6 px at the working stop, 17 at 1350,
28 at the closest — present at every stop a player places from, a kerb at none.
It does **not** read at the survey stop, deliberately; the debug outline
already covers that case at constant screen width, and if placement from the
survey view is ever wanted, that is the tool for it.

### Five slabs, not one scaled

    width   820 / 1230 / 1640 / 2050 / 2460      the catalogue's 410 quanta
    depth   1500                                  BLOCK_DEPTH, the lot, constant
    slab    30 uu thick, top face 30 uu above the plate
    rim     60 uu wide in plan, top face 42 uu above the plate (12 proud)
    pivot   front-left at ground, per the fastbake convention
    chamfer 14 uu, the catalogue's own value

**Scaling one slab in X would stretch the rim.** A 60 uu rim baked at 820 and
scaled to 2460 is 180 uu on the left and right edges and still 60 front and
back — a rim of two different widths on one rectangle, which reads as a
mistake rather than as a style. Five assets is what the catalogue already
costs for the same reason (36 masses across five widths), and PLAYABLE_PLAN
§2.2 puts width in the player's hands, so the five are needed the moment that
lands rather than being speculative.

Depth does not vary: the ghost shows the LOT, and every lot is 1500 deep.

**Proof: a measured frame at the working stop and the closest stop, accept and
refuse.** The survey stop is no longer part of the acceptance, and that change
is the finding above rather than a relaxation.

---

## D23 — lot-state glow. Declaration only, 2026-09-03.

B4 makes night glow carry ownership, activity and selection at once. This
declares what the lot states look like. **The mechanism is blocked and the
declaration says so rather than pretending otherwise.**

### First, a correction to the brief: "refused" is not a lot state

The four asked for were for sale / owned / growing / refused. Three of those
are properties of a LOT. **Refusal is a property of the CURSOR** — it is about
where the player is pointing, it lasts as long as the hover, and no lot is in a
refused state when nobody is looking at it. It belongs to D22's ghost, where it
already lives, and putting it in the glow set would mean a lot could sit on the
board glowing red at nobody.

Three states, then:

| state | glow | what the player reads |
|---|---|---|
| for sale | `GlowLevel` 0.35, `GlowState` 0.5 — neutral warm | "this is available" |
| owned | `GlowLevel` 0.15, `GlowState` 0.5 — barely lit | settled, unremarkable |
| growing | `GlowLevel` 0.55 pulsing to 0.35 over 2.5 s, `GlowState` 0.62 | "something is happening here" |

**For sale glows MORE than owned, which is the inversion worth stating.** The
instinct is to light up what the player owns. But an owned lot is the default
condition of a working city — light every one of them and the board is a
runway. What deserves attention is what the player could still act on, so
availability is brighter than ownership and a finished city goes quiet. Same
argument as D16's polish-means-attention: the interesting signal is where
something is possible, not where something exists.

**Growing pulses and nothing else does.** Motion is the scarcest signal on a
static board; spend it on the one state that is genuinely transient.

### The mechanism is BLOCKED and this is a declaration, not a plan

`GlowLevel` and `GlowState` are CPD channels 1 and 2, reserved for these in
`cpdmap.py`. **CPD does not reach the shader** — measured: Age driven through
CPD moved nothing, the same Age driven from the material instance moved the
frame −10.67 levels against 0.14 drift, and the CPD write read back correct
throughout.

So the per-lot glow **cannot be built** until the runtime push lands (a real
`SetCustomPrimitiveDataFloat` on the component, not a property write). Until
then this is the brief and nothing more.

**Do not substitute the per-instance route.** Driving glow from `MI_wood_*`
would light every lot of a species at once, which is worse than no glow: it
would look like a mechanic and behave like a bug, and somebody would spend an
evening on it.

**And when the push does land, per this lane's rule: the glow is proven by a
MEASURED FRAME showing two adjacent lots in different states, or it is not
proven.** A read-back proves the write landed, never that the thing the write
was for now works — four instances of that this week, every one with the same
tell: nothing failed.
