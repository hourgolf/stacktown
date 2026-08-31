# The reference canon — gold frames

This board is the **only** set of images any session or agent may compare
work against. Everything else — moodboards, pinterest finds, generated
concepts, other games — is explicitly non-canonical and stays out of
prompts. `Docs/MASTER_MATERIAL_SPEC.md` and the studio-director skill say
what the target *is*; this board shows what it *looks like*.

## Why a closed board

Drift does not come from having references. It comes from references
entering the pipeline informally — one session pins a photo, another pins a
render, and six weeks later two agents are building toward different
cities. A fixed-size board with a gatekeeper cannot accrete into a
contradictory pile. The predecessor projects both died partly of this: "the
single most consequential mistake in this project's history was treating a
persuasive render as proof" (studio-director skill).

## Governance — the whole point, do not soften these

1. **Maximum 8 slots.** A new image enters only when the owner blesses it,
   dated, and names which slot it takes. If the board is full, something
   leaves. There is no annex.
2. **Every entry declares its reference class**, from the studio-director
   taxonomy: `miniature` (real handmade models — surface, light, base),
   `portland-character` (era/typology character, never geography),
   `camera` (framing/behaviour only), `own-capture` (a blessed Stacktown
   frame — proof we hit the target once). Generated concept art is
   **mood-only and does not get a slot.**
   *Owner amendment, 2026-08-26:* `render-goal` — a rendered game image may
   be blessed as a **rendering goal**: a statement of what fabricated
   materials and staging should READ AS in a render (in the owner's words:
   "looks like a diorama but is a render" — grass that reads as flock,
   trees that read as formed and painted models, lamp pools, ambient).
   Lighting and environmental intent only. It is never a fabrication spec
   and never proof a look is reachable in our engine. (Supersedes the
   narrower `game-nightlight` wording; slot 2 enters under this rule.)
3. **Every entry says what it is blessed FOR and what to ignore.** A
   reference is a claim about one or two qualities, not an endorsement of
   the whole image. An agent citing a canon image must cite the quality,
   not the picture.
4. **Agents cite the canon or say they can't.** A look decision that cannot
   name its slot and quality is taste smuggling; flag it to the owner
   rather than proceeding.
5. Files live in `Docs/canon/` as `slotN_shortname.jpg|png`, committed.
   The annotation lives here, next to the slot. An image without its
   annotation is not yet canon.

6. **Specialty buildings get DESIGN REFERENCES, not slots.**
   *Owner amendment, 2026-08-31.* The gameplay buildings — marketplace,
   real estate office, and the several more still to come — do **not**
   each take a canon slot. There are more specialty buildings than there
   are slots, and spending the board one-per-building would empty it
   before the catalogue is served.

   So a second, lower tier exists, and the difference is what the image
   is a claim ABOUT:

   | | canon slot | design reference |
   |---|---|---|
   | claims | what the PROJECT should look like | what ONE building should look like |
   | scope | the whole catalogue | that building's geometry only |
   | enters by | owner blessing, dated, named slot | owner supplies it |
   | lives in | `Docs/canon/`, annotated here | with that building's declaration |
   | citable for | any look decision | that building's own geometry |

   A design reference is **not canon**. It is not a claim about the look
   target, it cannot be cited to justify a general look decision, and it
   never enters the board or takes a slot. Where the two disagree, **canon
   wins** — a design reference cannot override a blessed canon quality,
   and a specialty building is still judged against the target like
   everything else.

   Rule 4 is unchanged and still binds: a look decision that can name
   neither a canon slot NOR the design reference of the building it is
   about is taste smuggling. What this amendment adds is a second thing an
   agent is allowed to name — and it must say WHICH it is naming.

   The slots therefore stay for coverage that serves everything: the
   close-up SURFACE reference, the `portland-character` entry, and an
   `own-capture`.

## The slots

<!-- Template for each slot:

### Slot N — <shortname>
![slotN](canon/slotN_shortname.jpg)
- **Class:** miniature | portland-character | camera | own-capture
- **Blessed for:** the one or two qualities this image is the authority on
  (e.g. "how a card edge catches a key light", "base/board treatment",
  "practical glow temperature at dusk")
- **Ignore:** what this image gets wrong or does not speak to
- **Blessed:** YYYY-MM-DD by owner
-->

### Slot 1 — boardedge
![slot1](canon/slot1_boardedge.jpg)
- **Class:** miniature (owner confirms: photograph of a real model, N-scale
  urban layout)
- **Blessed for:**
  1. **Board edge & base** — the raw wood baseboard edge grounding the whole
     scene as an object on a table. Reveal hierarchy #2, demonstrated
     perfectly: the eye finds the edge and everything above becomes a model.
  2. **Scale-honest ground & planting** — molded curb strip, painted road
     markings, static-grass clumps, wire-armature trees. Fabrication-tier
     detail that is proudly *made*, never photoreal.
- **Finishing-only note (NOT a blessing):** the owner values this image's
  camera feel — macro depth-of-field, bokeh, the sense a real lens stood
  close to a small thing. Recorded as an aspiration for the *shipped* lens
  under the gate's finishing-effects amendment. It is never a judging
  reference: gate section E still judges geometry with DOF off.
- **Ignore:** the macro DOF during any judging or comparison; the
  cracked-asphalt road weathering (city weathering and large-scale albedo
  variation — our imperfections are a maker's, and albedo variation is the
  documented trap).
- **Blessed:** 2026-08-26 by owner. Slot assigned 2026-08-26.

### Slot 2 — nightlight
![slot2](canon/slot2_nightlight.jpg)
- **Class:** render-goal (owner amendment, see governance §2 — a game
  screenshot, cursor visible in frame; miniature-aesthetic night scene)
- **Blessed for:**
  1. **Night lighting** — warm practicals glowing in windows and the pool of
     lamplight on the pavement, read against a dusk-blue ambient. The
     statement of what Stacktown's night mode should feel like; directly
     relevant to the practicals and sodium lamp-light rig.
  2. **Street-level camera height** — eye at miniature-pedestrian height,
     close standoff.
- **Ignore:** the tilt-shift DOF (never a judging reference); the Czech
  vintage character (bus, shopfront era — not Portland).
- **Noted, not ignored:** the legible signage and the human figure. The gate
  currently forbids both as visual elements; the owner deliberately declined
  to list them under Ignore, which reads as a signal that rule may be
  revisited — it is NOT permission to cite this image for signage or figures
  while the gate rule stands.
- **A render's limit:** this image proves nothing about what is reachable
  in-engine. It states intent only.
- **Blessed:** 2026-08-26 by owner. Slot assigned 2026-08-26.

### Slot 3 — daylightflock
![slot3](canon/slot3_daylightflock.jpg)
- **Class:** render-goal (same game as slot 2, cursor in frame; daylight
  model-railway scene on a visible tabletop)
- **Blessed for:**
  1. **Planting honesty** — grass that reads as a flock mat with visible
     seams; trees that read as formed-and-painted scale models. The owner's
     own framing: "looks like a diorama but is a render" — which is the
     project's whole objective, stated as an image.
  2. **Daylight warmth** — the warm daytime key against green; the daylight
     mood anchor opposite slot 2's night.
- **Noted, not ignored:** the steam plume — an in-game effect today, but
  recorded as a city-life aspiration (smoke from chimneys and works stacks
  when the game grows life). Not citable for current visual work.
- **Ignore:** the tilt-shift DOF (standing rule); the steam-rail vintage
  character (period rail, telegraph poles — not Portland-modern).
- **A render's limit:** rendering goal only — never fabrication spec, never
  proof of in-engine reachability.
- **Blessed:** 2026-08-26 by owner. Slot assigned 2026-08-26.

### Slot 4 — worksyard
![slot4](canon/slot4_worksyard.jpg)
- **Class:** industrial-character (a game render of full-size buildings —
  enters exactly the way Portland does: typology and massing vocabulary for
  the WORKS district. What to build, never how it should read.)
- **Blessed for:**
  1. **Works massing & rooftop kit** — pier-and-spandrel mill blocks with
     banded brick, lattice water tower, stack, roof huts: the silhouette
     dictionary for block H and the works ladder (shed → works → foundry →
     plant).
  2. **Yard & apron dressing** — crates staged on aprons, service streets
     between blocks: the worked-yard look, not sprinkled props.
- **Ignore:** the open-sky sun and full-scale realism (contradicts
  lamp-in-a-room; nothing here speaks to miniature reading — citing this
  for surface or light is the legacy mistake); the era vehicles; the
  districtwide sameness (our works sit inside a varied city).
- **Blessed:** 2026-08-26 by owner. Slot assigned 2026-08-26.

### Slot 5 — highrise
![slot5](canon/slot5_highrise.webp)
- **Class:** miniature (photo of a real plastic model city — an eBay
  listing shot, and the artlessness is informative: even under flat retail
  light the massed blocks read instantly as a model city)
- **Blessed for:**
  1. **The highrise city read** — tight-packed towers of real height,
     silhouette and massing carrying everything, printed-grid facades that
     are exactly enough at city range. The owner's explicit direction:
     highrise scale IS the value here — the city needs true towers.
  2. **Kit-family coherence** — wildly different buildings cohering because
     one fabrication family made them: the project's core insight
     ("a model is unified by fabrication") as a photograph.
- **Design signal (owner, 2026-08-26):** recipe ladders must grow past t5 —
  some buildings need more than five tiers. Affects `Docs/RECIPES_DRAFT.md`
  ladders and catalogue sizing; recorded there too.
- **Noted, not ignored:** the palette scatter (yellow/teal/black variety is
  wider than the four-value discipline; the owner declined to bar it —
  treat as an open question for the district palette, not permission).
- **Ignore:** the flat listing light and white void — nothing about light
  or staging is citable.
- **Blessed:** 2026-08-26 by owner. Slot assigned 2026-08-26.

### Slot 6 — (empty)
### Slot 7 — (empty)
### Slot 8 — (empty)

Open coverage the remaining slots want: a close-up SURFACE reference (card
edge, paint sheen, a maker's seam at player-zoom range), a
portland-character entry for the non-works districts, and an own-capture.

## Candidates worth considering for own-capture slots

The blessed Stage 1/2 hero frames under `Docs/evidence/` are natural
candidates for one or two `own-capture` slots — they are the proof the
target was reached at least once, and they anchor "what our own success
looks like" against outside references. Owner's pick.

## Change log

- 2026-08-26 — board created, empty. Awaiting the owner's first references.
- 2026-08-26 — five references intaken and blessed; slots 1-5 assigned
- 2026-08-31 — owner amendment: specialty gameplay buildings take DESIGN
  REFERENCES, not slots (governance rule 6). Slots 6-8 stay open for the
  surface, portland-character and own-capture coverage.
  (boardedge, nightlight, daylightflock, worksyard, highrise). The
  `render-goal` and industrial-character amendments recorded. Owner design
  signal: ladders must grow past t5.
