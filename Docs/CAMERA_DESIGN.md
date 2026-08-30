# The Impossible Boom — Stacktown camera design

**STATUS: owner + coordinator draft, 2026-08-28. Not yet a design-team
work item — do not action until the owner hands it over.** Prototype
territory throughout; this document is the intent, not the tuning.

## The one sentence

The player is not a person in a city and not a drone above one: the
player is **the feed from a camera on an impossibly reaching boom**,
standing in the studio with the model — and every input is a
cinematography verb.

This single commitment answers the open-world question structurally.
A boom's subject is the model; the model is bounded by its board; there
is no "inside" to sprawl into and no traversal to build. The player
never goes anywhere. The eye reaches, arcs, racks, and cuts.

## Why a boom and not a drone

A drone hovers anywhere with any heading — six degrees of freedom and
no story about where it came from. A boom head is **on an arm from
somewhere**: it enters every shot from outside-in, it moves in arcs and
reaches, and it has mass. The difference is felt, not explained:

- **Arcs, not strafes.** Lateral reframing curves around the subject.
- **Reaches and pedestals, not flight.** In/out and rise/fall along the
  arm, with ease and settle.
- **Pan/tilt on the head** for aim; never yaw-in-place at speed, never
  hover-drift.
- **A hair of arm flex at full reach**: on a hard stop at macro range, a
  one-or-two-pixel damped sway, gone in half a second. The "impossible"
  part is the reach; the *believable* part is that even an impossible
  arm behaves like an arm.

Parameterize camera pose in **boom space** — azimuth around the board,
reach, height, head pan/tilt — and author every move as a spline in
that space. Boom-legal motion then falls out by construction; cartesian
strafing is unrepresentable. At low height the reach is constrained to
the street axes the city table already defines: the streets are the
dolly rails, and threading the canyon reads as a crane operator's
party trick rather than a drone's default.

## The zoom ladder: the 0.4% table, made playable

Four-to-five named **optical stops**, matched to the gate's measured
framings (board / block hero / approach / facade / macro). Each stop is
a real prime-lens character: focal length, maximum aperture, breathing
coefficient, vignette, a whisper of fringing at the extremes — the
finishing effects the gate already permits because "they read as
evidence a camera existed."

- **Snap zoom (optical):** a flick racks to the adjacent stop — fast
  ease, slight overshoot, settle. Superzooms are not perfectly
  parfocal: allow a two-frame focus recovery after the rack. That
  imperfection is the authenticity.
- **Digital zoom (between and beyond stops):** hold-zoom glides within
  a stop's band. Near the band's top, authored sensor-crop artifacts
  arrive — a subtle resolution crunch, a sharpen, amplified grain, a
  micro image-stabilization wobble — until the next optical snap
  "rescues" the image. The degradation is honest and it *sells the
  camera*.
- **Perf falls out:** stops quantize LOD and budget; every stop has a
  known frame cost, exactly as the gate already budgets detail per
  framing. The QC ladder and the player ladder are the same ladder.

## Focus is attention

The focal plane is the eye's attention, and the **focus pull is the
selection mechanic**:

- Select a parcel → the lens racks to it. Big pulls take longer than
  small ones (eased S-curve); a couple of frames of autofocus hunt —
  slightly past, then back — precede the lock. What is in focus is what
  is selected; what is selected is what the game describes.
- **Aperture varies by stop**, as real macro work does: deep focus at
  board range (survey — the whole model legible, the reader's
  "you can actually see it"), shallow at facade/macro (isolation — the
  reader's preferred lenswork). The f-stop the owner locks from the
  current sweep is the **character anchor** at facade range; the
  gameplay curve breathes around it. The informal reader signal — lens
  character wanted, this much blur not — is satisfied at both ends
  because the two preferences live at different stops.
- **Focus breathing:** real lenses shift field of view slightly during
  a pull (~1–2%). Include it. It is the literal name of what this
  design is for.

## Exposure: breathe small, breathe slow (proposal)

The doctrine fixes exposure for *judgment* — reproducibility of
evidence. Gameplay is not evidence. Proposal, pending prototype feel:

- A **slow, small auto-iris**: ±2/3 stop range, 2–3 second adaptation,
  show mode only. Swinging from a lit facade into a shaded canyon, the
  image settles the way a metering camera does.
- A **brief iris settle on snap zooms**: a sixth-stop dip-and-recover
  as the "camera" re-meters. Six frames of authenticity, nearly free.
- Judge mode: both off, fixed exposure, unchanged — one rig, flags off.
- Guardrail: amplitude small enough that practicals and economy cues
  never stop reading. If the breathing ever fights legibility, the
  breathing loses.

## Motion grammar: the eye cuts, it does not commute

- **MOVE** (boom arcs, reaches, pedestals, street-rail glides) for
  nearby reframing — continuous, physical, eased.
- **CUT** for distance. An all-seeing eye has no travel time. Between
  angularly close subjects, a **whip-pan**; between far ones, a **feed
  cut** — a six-to-ten-frame defocus-settle, like a director's monitor
  switching cameras. Cuts delete traversal, collision, and streaming
  corridors from the game's cost structure entirely, and they are more
  cinematic than flying, not less.
- Whips need motion blur to avoid strobing; the gate forbids motion
  blur for judging. Resolution: shutter-angle blur **only inside whip
  transitions**, authored, brief — a finishing effect under the
  existing amendment, owner-visible before it ships.

## The shot list: how a player watches a city grow

- **Setups.** The player saves framings — position, stop, focus subject
  — and cuts back to them by name. The bookmark UI is a director's
  shot list; the player is accumulating *their own hero frames* of
  their own city.
- **Event-driven inspection.** The economy fires (a parcel upgrades, a
  district heats): a chip offers one click → the eye cuts to a framing
  of that parcel and pulls focus onto the change. The city calls the
  eye; the player never patrols. This is the entire "examine the city
  as it grows" loop, with zero open-world surface.
- **Information altitude = optical stop.** Board range reads districts
  and markets; block range reads the skyline-as-chart; facade range
  reads the single business; macro is delight and fabrication. The
  0.4% rule already dictates what *can* read at each stop — the
  economy design (its zoom-verb mapping is an open question in the
  econ draft) plugs into this ladder directly.
- **Growth is stop-motion.** A tier upgrade is a mesh swap; under a
  locked camera it pops. Do not hide it — *embrace it.* A model city
  that grows is stop-motion animation, and a clean two-frame pop reads
  as a craftsman's hand between exposures. The fiction has an answer
  for the engine's cheapest behavior; take the gift. (Optionally: a
  parked "timelapse" verb — lock a setup, run time fast, and watch the
  city stop-motion itself. The player can film their own growth reel.)

## Sound sells the gear (cheap, large)

Servo whir on zoom racks, a focus-motor tick on pulls, one soft
mechanical settle at the end of a boom move, room tone under it all.
The boom is never seen; it is *heard*. Half the authenticity budget
lives in a handful of foley samples.

## Architecture: one rig, two modes — the week's lesson, applied forward

A single **LensRig** owns: the setup (boom-space pose), the stop ladder,
the focus solver, the motion grammar, the breathing layer (AF hunt,
iris, sway), and the artifact layer (crop crunch, grain, fringing).
**Judge mode is the same rig with the layers off.** One camera
authority for gameplay, capture, and QC — the two-paths-diverge disease
this project spent a week curing must not be reintroduced by its
camera. cap2/the capture pipeline should eventually *be* this rig's
judge mode.

Engine notes, high level: CineCamera-based; snap durations tuned
against TSR so racks do not smear; every effect budgeted with the
machine's Metal instability in mind (the breathing layer is many small
cheap things, never one expensive thing).

## The feed layer (owner-approved direction, 2026-08-29)

The player is the FEED — so beyond lens artifacts, a subtle analog-
transmission layer sells the signal between the camera and the viewer.
Owner decisions of record:

- **Flavor: MONITOR, not tape.** Faint scanline/aperture-grille texture,
  slight curvature, phosphor bloom on practicals — "modern superzoom,
  old studio monitor" is coherent kit; VHS tape artifacts against a
  modern digital lens would be two eras in one image. (Tape variant may
  be shot once for comparison, then discarded or kept on the owner's
  frames.)
- **One master intensity scalar 0→1** multiplying every component;
  per-component scalars underneath. Tested at multiple intensities —
  the owner's explicit worry is overdoing it.
- **Show-side only, by construction:** the layer lives in its own post
  volume/blendable, never in LOOK_Post, so the judge path cannot inherit
  it. Same one-rig/flags-off discipline as everything else.
- **Judged IN MOTION.** Analog artifacts are temporal (noise dances,
  wobble drifts) and scanlines can moiré against mullions and coursing
  during arcs — verdicts come from a motion clip through the reel
  pipeline plus stills, at off/subtle/visible intensities.
- **Interaction with DOF:** the reader wanted lens character but less
  blur; analog texture is an alternate carrier of "a camera existed" —
  test the feed layer and aperture together, since it may buy back blur.
- Legibility rule stays senior: if the layer ever fights economy cues or
  practicals, the layer loses.
- **Zero is byte-identical** (DESIGN, accepted): master intensity 0 must
  produce a frame byte-identical to no-layer-at-all, proven by capture
  diff, not assumed. And **every frame's sidecar stamps the intensity**,
  the way cap2 stamps the lens mode — a feed frame and a show frame are
  the same file type and look like the same kind of evidence; that trap
  already has one entry in cap2 and does not get a second one layer up.
- **The layer is, functionally, defect-hiding** (DESIGN, on the record):
  everything this week's instruments caught — weave tiling, solid quads,
  coplanar shimmer, missing trim — is the class of fault a soft analog
  overlay obscures. Safe while judge is the acceptance path; what a
  COLD READER sees is therefore an explicit owner decision, recorded
  below when made, not a per-session choice.
- **Reader exposure (owner, 2026-08-29): BOTH, LABELED.** Readers see
  judge frames first, feed-layered frames second, and are told which is
  which. Preserves the defect-finding instrument and cold-reads the
  layer itself. Feed-only reader frames are prohibited.

Status: **SHELVED (owner, 2026-08-29)** after the A/B/C delivery — "it
needs refinement and we're not there yet." The prototype is complete and
parked, not discarded: M_FeedLayer / MI_FeedLayer exist with their
generation scripts (mk_feedlayer.py, mk_feedvolume.py — rerunnable), the
LOOK_Feed volume was removed from the level, and the A/B/C footage
(stills + motion at off/0.35/0.70) is the reference for what "refinement"
means when this reopens. All spec guarantees above were implemented and
verified: zero-position noise-floor-equivalent, judge path untouched,
one master scalar.

## Prototype plan (when the owner hands this over)

- **P0 — the skeleton.** Boom-space pose + stop ladder + cuts + focus-
  as-selection, greybox, on the existing street. Answers: does the
  ladder feel like a superzoom; does cut-not-commute feel like power or
  like disorientation; input grammar candidates.
- **P1 — the breath.** AF hunt, focus breathing, iris settle, arm flex,
  digital-zoom crunch, foley. Answers: authenticity per cost.
- **P2 — the game.** Shot list, event cuts, information altitudes wired
  to the economy sim. Answers: is watching-a-city-grow a loop.
- Acceptance, per house rules: numbers where they exist, then a LOOK,
  and eventually a reader — who should *feel* the camera without being
  able to say why.
