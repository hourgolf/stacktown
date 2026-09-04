# Making the wooden beta playable

Written 2026-09-03 after the owner's first complete loop in the from-scratch
board: click empty plate -> pad -> click pad -> B -> wooden building. The
owner's verdict, verbatim: "its extremely clunky right now so i'd love to
hear your game plan for making this playable". This is that plan. It is
ordered by how much feel each item buys per unit of risk, and every item
names its proof. Nothing here is authorised until the owner says so; the
checkpoint commit comes first regardless.

## 0. Checkpoint (before anything else)

Commit the working tree the moment the owner gives the word. The last
commit with a working click is 3036f91 (2026-09-02 05:41); everything
since - state isolation, the HUD bar, fonts, the wear fork, the placement
pool, the Python click driver - is uncommitted. A working loop that is not
committed is one bad write from gone, and tonight showed how cheap a bad
write is.

## 1. Why it feels clunky (diagnosis, from the log and the code)

- **The pad lands "generally around" the click, not under it.** Placement
  v0 (`placement.py`) snaps every click to the ONE arterial's frontage:
  the pad's centre goes to a fixed depth from the road axis (1880 uu) and
  its X to the nearest legal slot at a catalogue width - with NO limit on
  how far the click may be from the frontage. The owner's 04:38 session,
  from the log: a click at (4671, 6954) - on the studio floor, off the
  board entirely - placed P1 at (4100, 1880), five thousand units away;
  a click at (-1253, -3580) placed P3 at (-820, -1880), seventeen
  hundred units away. The player clicks a spot; the game answers with a
  slot, and nothing shows the slot before the click, so the answer looks
  arbitrary. Fix, in 2.1: the ghost shows the slot, and clicks farther
  than a named reach from any frontage refuse with "too far from a road".
- **No preview, no hover.** The cursor gives no sign of what a click will
  do: whether it will place, where, how wide, or why it will refuse.
- **Selection is a text line.** The HUD's selection cluster stays
  collapsed (the rig's selection variable refuses writes from outside);
  the parcel highlight and an on-screen line are the only feedback.
- **Growth is too fast to read as a city.** In the coordinator's test
  session a fresh lot reached the top of its ladder (tier 5) in about two
  and a half minutes; in the owner's 04:39 session P4 was bought at :07
  and hit tier 1 at :15, tier 2 at :23, tier 3 at :32 - a tier every
  eight seconds. Buildings should grow while the player is
  doing something else, not while they watch.
- **Pads stretch into the road** (owner, earlier session): the pad is
  centred at the fixed depth with a fixed footprint instead of putting
  its front edge on the road edge the way the builder's setback math does.

## 2. The plan, in order

### 2.1 Placement feel - the ghost pad (biggest win, Python-side, no BP writes)

While the cursor hovers empty plate, show WHERE the click would land: a
box at the snapped footprint, at the width the click would get - shipped
2026-09-03 as a debug box drawn by the click driver (green = will place,
red = refused, with the reason). The translucent pad that replaces it is
the design lane's, as a material instance on the ghost only - NOT a CPD
tint: custom primitive data written through the component property does
not reach the shader on this setup (design lane, measured), so a CPD
ghost would read back as set and draw nothing. The click then places exactly what the
ghost showed. Proof: a capture with the ghost on a legal spot and one on a
refused spot; the owner's play note.

Same window: **front edge on the road edge** (the setback math from the
builder), so pads never intrude. Proof: pad front-edge Y equals the road
edge Y in the log for three placements.

### 2.2 Width in the player's hands

Scroll wheel (or Q/E) cycles the catalogue widths for the ghost before
the click - the player chooses the lot size instead of receiving one.
Later: drag-to-size. Proof: three pads of three widths placed in a row.

### 2.3 Economy pacing (numbers, not code)

`econrules.py` is the only executed authority; the change is its
constants. Target: first tier-up two to three minutes after purchase,
top of ladder in twenty to thirty minutes of play, money visibly ticking
on the HUD every few seconds. Written as a table in
ECONOMY_TICK_CONTRACT.md before it is applied, then one timed session.

### 2.4 The HUD selection cluster

One variable-flag edit on BP_LensRig (make `SelectedParcel` instance
editable) - not a graph write - then the Python driver's mirror write
succeeds and the right-hand cluster lights up with name, state, price and
the buy prompt. Beta lane's task when it is back online; proof: the
cluster visible in a capture after a click.

### 2.5 More board to build on

Multi-road frontage (`resolve_road`, notes already written in
RESOLVE_ROAD_NOTES.md): the cross street becomes buildable, corner lots
get their CornerSide. Then the drawn-road mechanic (ROADS_AS_MECHANIC.md)
opens the rest of the plate.

### 2.6 Camera and selection polish

Hover highlight before the click; click on a building selects it; a
subtle state read on every lot (for sale / owned / growing) in the night
glow the direction-B declarations already reserve for information.

### 2.7 The packaged beta - a strategic call for the owner

Everything above runs in the editor's Python. A packaged build cannot run
it: the economy, placement and input all need a port to Blueprint or C++.
Recommendation: stay editor-only while the loop is being made fun (fast
iteration, no toolchain), and port once the mechanics stop moving. The
port is a chartered lane of its own (packaged-beta charter, pending). If
the owner wants a shareable build sooner, the port moves up and the feel
work slows; that is the trade.

## 3. How the work runs from here (the process, owner-mandated)

- The owner never tests a guess. Every human run answers one question
  with a log line, and the instrument is in place before the run.
- Proven graphs are frozen. BP_LensRig takes no graph writes; new
  behaviour goes in the Python driver, a new function graph or a new
  actor. Variable-flag edits are allowed, one at a time, compiled and
  saved by explicit path, verified by a reflected read.
- Lanes run PIE only on the test file (lane_pie.marker); the owner's save
  is theirs alone.
- One owner run per feature, then commit on proof.

## 4. Where we are, and the road home (2026-09-04, after the owner's "we still feel a long way from home")

**Done and owner-verified (commits 0e35ee9, 8789d05, 4b410d2 + the set
after):** from-scratch board; click to place with a ghost that shows
the lot before the click, free along both roads; widths on the wheel;
overlap and reach refusals with reasons; pads and masses on the facade
line; cursor selection of pads AND buildings; the HUD bar with the live
selection cluster; buy, upgrade, repair, hold-to-reset; growth retired
from the timer; rent slowed 13x; state isolation so no lane can touch
the owner's save; the wooden look's edge wear finally rendering.

**Why it still feels far from home - the honest list:**

1. **There is no game in the middle.** Performance is player trades
   only (the owner's ruling), and there is no trading system. Today the
   loop is place, buy, upgrade, watch rent - it has no decision that can
   go wrong. Every other item on this list is polish around a hole.
2. **Money is still a faucet.** Rent accrues with no cost, no risk and
   flat lot prices, so the tenth lot arrives faster than the second.
3. **The board reads as a rendering test, not a place.** Lots are pads
   and towers on a bare plate; no roads drawn by the player, no lot
   states in the night glow (blocked on the runtime CPD push), no life.
4. **Everything runs only in the editor.** The economy, placement,
   input and HUD are editor Python; nothing can be handed to a tester.
5. **The tools bite.** Two editor stalls, an offline lane twice, a graph
   writer that drops chains, readers blind to enums - every window
   costs proofs that a normal project would not need.

**The road, in order, each step with its proof:**

- **Step 1 - the trade (this week).** The owner describes what a trade
  is; the beta lane writes the trading contract (verbs, counterparty,
  what is exchanged, how it moves per-lot performance); the coordinator
  prototypes the simplest version in the Python driver (recommended
  first shape: sign a tenant to a building at a negotiated rent - one
  verb, one number, success/failure per lot). Proof: a 20-minute
  session where a bad trade costs the owner something they notice.
- **Step 2 - money that can be lost.** Lot prices climb with owned
  count (the lane's table), rent depends on the tenant, repairs cost,
  failure exists. Proof: a session where the owner has to choose
  between two purchases.
- **Step 3 - the board becomes a place.** Lot-state glow (needs the
  runtime CPD push, proven by two adjacent lots in different states),
  the ghost's baked rim in play, wear on aged buildings, the drawn-road
  mechanic v0 (ROADS_AS_MECHANIC.md). Proof: the owner's cold read.
- **Step 4 - fun before port.** Three owner sessions with a written
  goal each (e.g. "reach 5,000 with no failed lot"), rated; tune
  numbers between sessions; nothing new until the rating moves.
- **Step 5 - the packaged beta.** Only once step 4 holds: the port per
  PACKAGED_BETA.md - HUD as a normal widget first (lowest risk), then
  input via Enhanced Input, then economy and placement into Blueprint or
  a first C++ module (the owner's call). Proof: a build on a second
  machine, played by someone who is not the owner.

**What the owner decides, in order:** what a trade is; whether lot
prices climb with count; when to port (recommendation: after step 4).
Everything else is the lanes' and the coordinator's to build and prove.

