# STACKTOWN — one-shot brief for building it again from the ground up

Written 2026-09-07 by the coordinator, on the owner's word, as the owner would
put it to a fresh LLM with an empty repository. Everything below was decided or
measured on the real build; nothing is a guess. Paste it whole.

---

You are building STACKTOWN with me. Read all of this before you write a line.

## 1. What it is

A city-building game presented as a handmade wooden architectural model on a
studio table — a "living diorama". The player buys and builds lots along roads,
draws new roads, keeps buildings maintained, and grows a small city on a
wooden board. Time shows in the model's own language: fresh-cut timber is pale,
it ambers as it ages, greys as it tires, chars when it fails, and is sanded back
pale when repaired or upgraded. By day the buildings are solid carved blocks; at
night, light shows through slots that were never visible by day. A ledger of the
player's own PAPER trades (a brokerage paper account) can feed rewards into the
city. The game consumes trade outcomes; it never, under any circumstances,
places an order.

The bar for "done" is a stranger: they double-click the app, meet a started
wooden city, click a marked lot and buy it, watch rent arrive, draw a curved
road, see a building tire and fail, repair it, chase a score to the next goal,
toggle night, and cannot lose a city by starting another.

## 2. The look (this is the part that was hardest to get right)

The target is a HANDMADE MODEL, not a small real city. A model is unified by
fabrication: one maker, a handful of stocks, one lamp in one room. That turns an
impossible asset problem into a shader-and-lighting problem one person can win.

Rules that held, in order of impact:

1. Geometric reveal before anything else: recess, projection, thickness, a
   real edge for light to catch. No amount of post-processing rescues flat
   geometry.
2. A base: the board is a plate with a visible edge, on a table, in a studio
   surround that contributes bounce. A model in a black void is a render.
3. WOOD IS THE DIRECTION. Carved timber massing on an inlaid board. Seven
   species, pale to dark — maple, pine, ash, oak, cherry, sapele, walnut —
   each with its OWN grain normal map. A species is a stock a modelmaker would
   reach for, never a colour on one map; if a species cannot be given its own
   grain it is dropped, not admitted.
4. Windowless masses by day. A window is not a hole or a pane; it is LIGHT at
   night, through a procedural slot mask (about 12 percent coverage) multiplied
   by a NightAmount that is zero by day, so no daylight frame can ever show
   one. The mask is gated off chamfers so no window is cut by a building's own
   edge (windows sit on a face where max(|n.x|,|n.y|) > 0.85).
5. Patina IS time. Three clocks: game time (the depicted building ages), model
   time (the board is maintained over years — fresher blocks where it was
   updated), material time (timber ambers, checks, greys, sands back). The
   model maker is the ageing system: build carves a pale block; upgrade pulls
   it, sands it, refits it pale; neglect ambers then greys; failure chars; only
   repair helps.
6. Roads are inlays of one paler stock in four stains, pale to dark as the
   road gets grander: dirt, avenue, boulevard, highway. Tone reinforces width;
   it never has to identify a road alone. A drawn road is drawn at its
   CARRIAGEWAY width on bare plate (no painted verge); a curved road's chords
   are MITRED so consecutive pieces share one edge — never overlapped, never
   stepped. Grain scale 0.010: it must not resolve at the survey stop and must
   read as fine cathedral figure up close.
7. Deliberate imperfection: a seam, a paint break, a slight misalignment. Hand
   tolerance is ON.

What does NOT work, learned the expensive way: depth of field (judge with it
OFF; if the scene needs it, the scene does not work), tilt-shift, bloom, warm
grading on weak geometry, more props, photoreal donor assets next to
flat-shaded ones, and any look claim made from a number instead of a frame.

Palette: restrained. Four values plus glass was the best the previous project
ever looked. When adding a colour, ask what it replaces.

## 3. The camera

A table-level oblique. One pawn: a focus point on the board, yaw, pitch
(negative looks down; clamp about -85 to -8), and a reach. The focal length
ramps with reach on a log scale — 24 mm at the wide stop (reach 21,024 uu)
to 200 mm at the close stop (1,200 uu) on a 36 mm sensor — so closing in reads
tighter than a plain zoom. Right-drag orbits, the wheel closes toward the point
under the cursor, screen edges or arrows pan, HOME returns to the arrival.

THE ARRIVAL is the first frame a stranger meets and it is measured, not
eyeballed: all four plate corners inside the frame, no corner within 5 percent
of an edge (the HUD bar's bottom is the top edge), the plate as large as that
allows, its long axis running corner to corner of the frame. On a 15,300 by
8,460 board that is yaw 49, pitch -38, reach 18,500, aimed 2,000 uu short of
the plate's centre toward the camera, about 28 percent of the frame. Write the
projection as a script and check candidates against it before touching the
number. The arrival must show wood: the starter city has three built lots, one
of them a tier higher so the skyline says the city grows.

## 4. The board and placement

- The plate is 15,300 by 8,460 uu (x by y), axis-aligned. Two pinned roads: an
  arterial along x through the centre and a cross street along y. A road's
  CORRIDOR is its carriageway plus a 430 uu verge either side; an avenue's
  carriageway is 1,400, so its corridor is 2,260 and its half is 1,130.
- Fourteen pinned lot spans line the arterial (three or four per quadrant) with
  a recipe each; the starter city seeds them as marked, for-sale lots.
- FREE PLACEMENT: a click on the board resolves to the nearest road with
  frontage; the pad snaps to that road's frontage line at the click's position
  along it, with the width the player has chosen (820, 1,230, 1,640, 2,050 or
  2,460 uu — a 410 quantum) and a depth of 1,500. A lot faces exactly one road
  and may touch its own corridor but never overlap ANY road's corridor, any
  other lot, or leave the plate (a rotated pad's bounding box must sit inside
  the plate). Highways carry no frontage. Refusals are one short sentence at
  the cursor, subject-first: "Off the board", "Roads can't cross a highway",
  "Can't afford it".
- ROADS are drawn by nodes: in road mode each click adds a node, a ghost shows
  the curve (a Catmull-Rom through the nodes sampled at the 410 quantum into
  chords), ENTER draws it as ONE road, BACKSPACE drops the last node, T cycles
  the type. A road may not cross another road, a path may not cross itself
  (centreline test between non-adjacent chords), and its corridor may not leave
  the plate. Two nodes make a straight road.
- Road types are MECHANICS, not decoration:

      type       carriageway  cost per 100 uu  rent multiplier  frontage
      dirt          900            $5            0.75             yes
      avenue      1,400           $10            1.00             yes
      boulevard   1,700           $20            1.25             yes
      highway     2,000           $30            1.10 (bonus)     no

  A lot's rent is multiplied by its road's factor; a highway within 2,000 uu
  adds its bonus on top. A 45-degree road cannot carry lots on both sides on a
  board this size — measured, and left as a decision (tolerance or a bigger
  plate).

## 5. The economy (one tick every 2 seconds; every number is a placeholder)

- Money starts at $100. A lot's price is (50 + 2 per 100 uu of width + 25 per
  tier) times a recipe factor: vernacular 1.0, office 1.6, tower 3.0. Rent per
  tick is 0.75 per tier times the recipe's rent factor (1.0 / 1.5 / 2.5) times
  DEMAND times the road multiplier.
- Demand is a number on the bar, never a word. It moves 0.1 per tick toward a
  target and clamps between 0.5 and 2.0 (gain and loss 0.05).
- Wear: every owned lot wears 1 per tick; the limit is 150 per tier. At the
  limit the building FAILS: no rent, minus 50 score, and the wood chars until
  repaired (H). Buying, upgrading and repairing reset wear. Failure is an
  event, not a gradient: the wood's failure channel runs 0 to 0.3 while the
  building tires (never alarming), steps to 0.6 at failure, and rises to 0.8
  with neglect. The empty band between 0.3 and 0.6 is the step the player
  notices; nothing may creep into it.
- Verbs: click to select or place, TAB width, R building type, B buy, U upgrade
  (price climbs with tier and with a premium for poor performance, never a
  discount), H repair, G road mode, L night, hold N two seconds to reset (the
  city is archived first, never destroyed), P seeds the starter city on an
  empty board, 1-3 load a save slot (three per install; the city being left is
  saved first; a slot never written is a fresh board).
- SCORE is one number, always on the bar: money plus the price of every owned
  lot plus $5 per 100 uu of road minus $50 per failed lot. Goals at 1,000,
  5,000, 20,000 and 100,000; reaching one puts a three-second accented message
  on the bar and a sound. Placeholder sounds: one wood tap for every
  successful verb, one dull tap for every refusal; none for goals.

## 6. The market hook

A separate adapter process polls a brokerage PAPER account for closed trades
(keys live only in the environment, never in the repo, never in chat; there is
a --mock mode with no keys) and appends one JSON line per closed trade to a
ledger file the game watches. The game applies rewards idempotently by count:
every ten closed trades credit $20; every winning trade adds $5; per-lot
performance is reserved for the player's trades only and today drives nothing
visible. There is deliberately no path to live trading and the game never
places an order. Which building a trade lights up at night is an open design
decision.

## 7. The HUD (a caption on a photograph)

One dark bar across the top: money large, then DEMAND, SCORE, NEXT goal, then a
message; mode words (NIGHT, ROAD) on the right only while the mode is ON. A
selection panel: name, state ("OWNED, TIER 2"), the one verb that applies with
its price. A legend bottom-right that is a legend, not a manual: the camera
line always, the verbs line only what is available now. Refusals: a hover
refusal at the cursor, an action refusal on the bar cleared on the next input.
Three colours only (body, dim, accent). A type ramp of two faces; do not use
glyphs the display face lacks (no middle dot). The HUD does not respond to zoom.
Nothing goes on it that does not carry information the player needs at that
moment — a permanent fact never sits in the transient cluster.

## 8. How to build it so it stays true (the practice that worked)

- The rules live twice on purpose: a Python SPEC (placement, economy, tick)
  with self-tests and closed-form known answers, and a C++ runtime that must
  agree with it. Fixtures are GENERATED from the spec into the C++ test tree;
  a C++ test that reads the fixture fails if the port drifts. A host-side
  pre-flight harness with a mock engine header compiles the rule files without
  the engine, and a MUTATION TABLE plants known bugs and demands every one is
  caught; a test that cannot fail is not a test.
- Gameplay is C++ (an engine module with a game-instance economy subsystem, a
  world city-sync subsystem that spawns one actor per lot and per road chord
  from the state, a player controller with the verbs, a camera pawn, a HUD
  built in code). No gameplay in editor scripting: it cannot cook.
- State is one JSON file per save slot, saved on every verb, archived on reset,
  with a lane/test file that no test ever confuses with the owner's real save.
- Every look claim is proven by a frame at a named camera, opened and looked
  at, never by a read-back of a parameter. Predict, then build: state the one
  observation that would prove a mechanism wrong before building its fix.
- Seats: a coordinator who owns the engine and the pass line, a design seat
  that owns the look and its assets by name (and never touches the flagship
  masters), an engineering seat that owns the rules and their oracle. They talk
  on ONE board document: grants of editor windows against a measured state,
  releases naming every asset saved by explicit path, pass lines with the test
  count, decisions with attribution. The owner's word is the only approval for
  commits of code, assets or config; docs may be pushed on a standing word.
- Package a universal Mac app that opens WINDOWED (1600x900); a fullscreen
  default stalled on an unattended display. Verify by the double-click path.

## 9. Decided, so do not relitigate

Wood is the direction; patina is the time mechanic; both starts (empty board
or starter city); road types are mechanics and curved roads are drawn by nodes;
free placement over pins with the hidden grid being the roads; score is one
number with a goal ladder; the HUD is C++; three unnamed save slots; sounds are
wood taps; demand is a number; failure is a step; the arrival is measured; no
live trading ever.

## 10. Open, for the owner

The pinned map roads still draw white at corridor width and are the brightest
things on the board (make them the avenue's stain at carriageway width); which
lots the starter city has built and how many; whether a fresh install opens on
the starter city; a tolerance or a bigger plate for diagonal roads; what lights
a building at night (attribute trades to lots, or drive hue from rent); slot
names; water-laying and terrain-carving as future build verbs (the reference
board's ambition).

## 11. Honest state of the build this brief was written from

About 45 of 100 against "a simple building game a stranger enjoys": the
mechanics are largely in (70), the loop exists but is thin (45), content is
sparse (30), polish is early (30). What would move it: content — more roof
furniture, more massing variety within the seven species, the studio surround
finished; a tick rate tuned by play rather than by default; the market loop
visible on the board; water and terrain as verbs; real sound design.
