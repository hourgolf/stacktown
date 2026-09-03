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
spare pool parcel moved each tick to the snapped position, at the width
the click would get, drawn in a "ghost" state (CPD channel 3 "Selection"
is reserved for exactly this kind of runtime tint; a second option is a
translucent material instance on the ghost only). Red ghost + the refusal
text when the spot is illegal. The click then places exactly what the
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
