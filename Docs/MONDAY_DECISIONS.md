# Monday decisions - what turns test day into a bigger game

Written 2026-09-06 18:39 PDT by the coordinator after the owner's read: "we're barely at
a 15/100 on the scoreboard." Everything below is a decision only the owner
can make, each with a PROPOSED DEFAULT so a yes takes one word. The seats
are already queued on the parts that need no decision (BOARD.md, 18:xx).

## 1. The goal loop and the score  (design lane drafts the one-pager first)

Today a session has no end and no score: you place, buy, upgrade, repair,
draw roads, toggle night, and money only rises. A game needs a reason to
stop and a number to beat.

PROPOSED DEFAULT (react to it; the design lane's one-pager may replace it):
- A SESSION is one board, played until the plate is full or the player
  quits. No timer in the beta.
- The SCORE is one number, always on the bar (HUD_V1 LOOK 5 has the slot):
  money + the purchase value of every owned lot + a road bonus per 100 uu
  drawn - $50 per failed lot standing. It rises with every good move and
  falls when the city is neglected, so it reads at a glance.
- A GOAL LADDER, not a win screen: 1,000 / 5,000 / 20,000 / 100,000 score,
  each announced once on the bar. The first one is reachable in the first
  ten minutes from the fresh $100 city; the last is a long game.
- FAIL STATE: none in the beta. A neglected city loses score, never the
  session.

## 2. Road types as mechanics  (decided 2026-09-01; the numbers are not)

The four types are decided - dirt, paved avenue, tree-lined boulevard,
highway - and the highway REFUSES frontage. Roads are free today and there
is one type. The seat needs three numbers per type to build it:

| type | carriageway | frontage | PROPOSED cost per 100 uu | PROPOSED effect |
|---|---|---|---|---|
| dirt | 900 | yes | $5 | lots on it rent at 0.75x |
| paved avenue | 1400 (today's road) | yes | $10 | 1.0x (today's rent) |
| tree-lined boulevard | 1400 + median | yes | $20 | 1.25x, and its lots age (patina) slower |
| highway | 2000 | NO | $30 | every lot within 2,000 uu of it rents at 1.1x |

Yes to the table as written, or change any cell. The rent multipliers are
the part that makes a type a planning decision rather than a price.

## 3. Game start: BOTH  (decided 2026-09-01; the offer is not built)

A new game must offer an empty board OR the 14-lot starter preset. The C++
fresh city is empty-only today. PROPOSED: on a fresh city, before the first
placement, the bar reads "P  start from the 14-lot preset"; pressing P seeds
the preset as for-sale lots at their pinned positions. No menu screen in the
beta. Yes/no.

## 4. Demand never moves

DEMAND reads 1.00 forever: nothing in the rules changes it, so prices and
rents are flat and the city has no feedback. PROPOSED rule (the Python
oracle changes first, then C++): each tick, demand moves toward
1 + 0.05 x (owned lots) - 0.05 x (for-sale lots standing empty), clamped to
[0.5, 2.0]. Owning raises demand, leaving pads unbought lowers it, and the
next lot's price follows demand (Price already multiplies by it). Yes/no, or
different coefficients.

## 5. Sound

None exists. PROPOSED: four placeholder tones generated in-repo (place,
buy/upgrade, refuse, goal reached), wired now so the loop has feedback,
replaced by real sounds when there is a sound direction. Yes/no.

## 6. Save slots  (BUILT 2026-09-07 on the proposed default)

One save per install until 2026-09-07. BUILT as proposed: three slots, keys
1, 2 and 3 at any time outside road mode; the city being left is saved
first; a slot never written opens as a fresh board; slot 1 is the file that
always existed, so no save written before slots moved. The choice is
remembered beside the saves (Saved/Stacktown/slot.txt; the packaged app's
own container). Not built: NAMING a slot - they are 1, 2, 3. Owner's call
whether names matter for the beta.

## 7. Already moving, no decision needed

- Design: the road grain fork (one timber stock, four stains = the four road
  types' look, D10/D11), the window-pattern fix so two masses never light
  identically, the goal-loop one-pager.
- Engineering: the typed parcel actor (item 8), the shim removal (9), then
  road types (10), curved multi-node roads (11), the preset seed (12) - all
  decided mechanics, all buildable without a new decision except the
  numbers in section 2.
- Coordinator: the Monday package is rebuilt with age and the outline;
  wiring the controller side of nodes, types and the preset key as the
  seat's pieces land.

## 8. What would move the score fastest, honestly

In order: the loop and score (1), road types with rent effects (2 + 4),
sound (5). Building variety exists already (20 masses x 7 species); what it
lacks is the design lane's patina and windows reading at the far stop,
which is their queue. A 15 becomes a 30 when a stranger can lose points,
chase a number, and hear the board answer.
