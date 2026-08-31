# Core gameplay buildings — declarations

**Declare-before-geometry. Owner's call: build LOOK-FIRST, function retrofits
when the economy notes land (rework risk accepted knowingly). These
declarations are the declaration; registry entries in `archetypes.py` derive
from them; geometry starts only after each has its owner-supplied DESIGN
REFERENCE.**

Status: **owner-shaped 2026-08-31.** The real estate office's soul was
replaced by the owner at that review — see §2, which supersedes the storefront
draft and the gate ruling that went with it.

## The signage pre-empt (read this before either declaration)

`ARCHETYPE_DECISIONS` says signage returns, fabrication-honest, for the stores
family. The Stage 2 gate constraint says no signage in GATE frames. **These do
not conflict**: the gate constraint governs what appears in gate evidence
framings; the archetype vocabulary governs what the building IS. A marketplace
may carry printed-card signage as its own honest fabric and still never show it
in a gate frame. Stated here once so no future reader of the two documents
manufactures a contradiction.

## Reference policy (owner decision, 2026-08-31)

**Neither building takes a canon slot.** There are more specialty buildings
coming than there are slots, and spending the board one-per-building would
empty it before the catalogue is served. The owner supplies a **design
reference** for each — a working image that shapes that one building's
geometry, which is not canon, cannot be cited for a general look decision, and
never enters the board. Recorded as governance rule 6 in `Docs/CANON.md`, with
the full canon-vs-design-reference distinction.

Slots 6–8 stay open for coverage that serves everything: the close-up SURFACE
reference, the `portland-character` entry, and an `own-capture`.

## A gap found while wiring this, and its resolution

The previous draft said the office "RIDES STORES' ENTRY" and that the
marketplace "inherits the stores-archetype soul". **There is no `stores`
archetype.** `ARCHETYPES` holds exactly `street`, `industrial` and
`agricultural-structure`; `modelgate.py` has no rule naming stores; and
`ARCHETYPE_DECISIONS.md` mentions the word once, in passing, about signage
scope. The 2026-08-30 ruling therefore resolved a question by pointing at an
entry that does not exist.

This matters because `archetypes.of_spec` defaults an undeclared spec to
`street`, and `GATE-07` and `GATE-08` both carry `judges=('street',)`. A
building that declares nothing is judged as an articulated street elevation —
silently, and by rules that may be the wrong questions for it.

## 1. STRATEGY MARKETPLACE

**Soul** — a MARKET HALL, not a shop:
- Standalone one-to-two-storey hall massing with its own roof story — long
  ridge, clerestory band — plus the street-life layer at full strength:
  stalls, awnings, spill-out goods, trade visible outside. The busiest place
  on the board by design.
- **Landmark legibility at every stop**: by the 0.4% rule the hall must read
  as "the market" from block-hero range on SILHOUETTE alone (the long roof +
  awning rhythm), not on signage. Signage carries the read only at player
  zoom, printed-card, model-scale.
- Fabrication: card hall + timber stall framing (the water-tower trestle's
  language), awning fabric as the one soft material.

**Archetype — OWN ENTRY, with a `GATE-03` override.** *Owner decision,
2026-08-31.* The declaration's own test is "is there a criterion that would
judge it differently?", and here there is: a hall is defined by long, plainer
flanks under a clerestory, so `GATE-03`'s parts-per-m² is the street measure it
is partly defined by not having — the same shape as `industrial`'s
`DETAIL_MIN` override, and an override is a real consumer, not a reserved name.
`GATE-07` and `GATE-08` **still apply**: the hall is standalone and deep, so all
four faces show and a blank rear would be a genuine defect. `industrial` was
considered and rejected for exactly that reason — its exemptions would stop
judging the rear and the depth of the most-looked-at object on the board.

Per `archetypes.py`'s double-entry rule, adding this entry forces a decision
about every rule, and the `GATE-03` override value must be a `qc.py` constant,
not a second copy of a number.

**Design reference**: owner-supplied, before geometry.
**Function**: TBD pending economy notes.

## 2. REAL ESTATE OFFICE — soul replaced by the owner, 2026-08-31

**SUPERSEDED:** the earlier draft described a modest glazed storefront office
with listing cards in the window, and carried an owner ruling that it "RIDES
STORES — mistaking it for a shop is a shrug, not a defect." **Both are
withdrawn.** That ruling answered "must it read as an office and not a shop?"
for a shopfront; the building is no longer a shopfront, so the question it
answered no longer arises. Recorded rather than deleted so the change is
legible.

**Soul** (owner's, 2026-08-31):
- A **distinctive small house with a blue roof and a landscaped yard** —
  detached, sited in its own ground rather than in a terrace. The quiet
  counterpart to the marketplace: where parcels are considered, not where
  crowds gather.
- **Four growth tiers.** The building visibly grows as the player invests.
- Precedent exists: *"we have built similar models already"* — the cottage and
  walkup drafts.

**What the code already knows.** `cores.DETACHED` is `('house', 'walkup',
'works')` and `step_elevations.freestanding()` skips `house` because
`build_house` already builds all four sides. So the detached family is
machinery that exists. What does **not** exist is a catalogue member: **no
recipe in `RECIPES` currently uses a detached style**, so the cottage and
walkup remain drafts and this office would be the family's first entry into the
catalogue.

**Growth tiers vs catalogue tiers — the same machinery, a different purpose.**
The catalogue's `t0..t5` are variety ACROSS a street: different massing on
different parcels. Growth tiers are the SAME parcel over time. The meshes are
identical in kind, so the bake is unchanged and the difference lives in the
placer/runtime, which swaps the mesh as the building grows. Noted so nobody
builds a second tier mechanism. **Four is shorter than the catalogue's six**,
which is deliberate here and does not amend the standing "ladders must grow
past t5" design signal for the catalogue proper.

**Archetype — OPEN, and it is not `street`.** A detached house standing in a
landscaped yard is not an articulated street elevation, so letting it default
would judge it by the wrong rules. It is also not `industrial` or
`agricultural-structure`. Deferred deliberately: the distinct judging rules
are easiest to name once the recipe exists and the first bake shows which rules
actually misfire — but it **must not reach a bake undeclared**, because the
default is silent.

**Design reference**: owner-supplied, before geometry.
**Function**: TBD pending economy notes.
**Yard**: landscaping is a zone, not building parts — `zones.py` already builds
green/park/vacant and the flowerbed donors are surveyed. Whether the yard ships
with the mesh or is placed beside it is a placer question, flagged not answered.

## Sequence

    1. owner shapes/approves these declarations              DONE 2026-08-31
    2. design references land (owner's hand, NOT canon slots)   <- BLOCKING
    3. registry entries wired in archetypes.py
       - marketplace: own entry + GATE-03 override (decided)
       - office: entry still to be named (NOT street)
    4. recipes through genbuild, gated and stamped like everything
    5. placed in TestCity by the placer - after the rig exists, so their
       first frames are judgeable

## Standing constraints

Bake policy governs. Declare before geometry, even look-first. One writer in
the editor. Evidence under `Saved/`. A specialty building is still judged
against the look target like everything else — its design reference shapes it,
it does not excuse it.
