# `resolve_road` — generalizing placement off the one hardcoded arterial

**Status: DESIGN NOTES, NOT A BUILD.** Written headless, 2026-09-03, while
the editor is held for the owner's own play session. This is the follow-on
`placement.py`'s own module docstring names and defers: *"ONE road: the
existing arterial... Multi-road frontage is out of scope entirely, not
stubbed."* These notes are that stub, written down before anyone
implements it, per this project's own "declare first" discipline
(`PLACEMENT_GRID.md`, `ROADS_AS_MECHANIC.md`). Nothing here is authorized
to build; it exists so the next editor window doesn't re-derive the
geometry from scratch.

Read `PLACEMENT_GRID.md` §1 and `ROADS_AS_MECHANIC.md` §0–§1 first — the
"grid IS roads" verdict and the chord-lot model are inherited whole, not
re-argued here. This document is narrower and more mechanical than either:
one function, its signature, and what changes downstream of it.

## 1. What v0 actually does today, precisely, so the generalization is
   honest about its starting point

`placement.py`'s current geometry is the SPECIAL CASE of one road running
along the world X axis, centered at Y=0 (`citylayout.py`'s own convention,
reused not re-derived):

    side = 'north' if y >= 0 else 'south'
    x0 = snap(x - WIDTH/2); x1 = x0 + WIDTH        # along the road
    overlap: 1-D interval test on [x0, x1] per side

Three things are baked into this that a second road breaks the moment it
exists: (a) "the road" is implicit — there is exactly one, so nothing
ever asks WHICH road a click belongs to; (b) "along the road" and "world
X" are the same axis, so no projection step exists; (c) "side" is a
global compass direction (north/south), which only means something
because the one road happens to run east-west. A north-south road's two
sides are not north/south, they're east/west, and a diagonal road's two
sides aren't compass directions at all.

## 2. The function

    def resolve_road(roads, x, y):
        """(road, local) | (None, None). `roads` is the candidate list
        (see §3 for shape). `local` is {'along', 'across', 'side'} in
        the winning road's own frame — 'along' replaces today's bare
        `x` as the snap/overlap axis, 'side' replaces today's
        north/south with a road-relative label. None, None on no
        candidate close enough to claim the click at all — the
        generalized form of today's implicit 'there's only one road, it
        always applies.'"""

Everything downstream of this call — snapping, the width span, the
overlap scan, the off-plate check — is `local['along']` and
`local['side']` standing in for today's bare `x` and its `y>=0` derived
side, unchanged in shape. That's the point of factoring it out here:
`resolve_click`'s own body barely changes, only what feeds it does.

## 3. What a "road" needs to carry

The minimum a straight-segment road needs to define a local frame:

    {'id': str, 'start': (x, y), 'end': (x, y)}

A ROAD ID matters even for a straight segment, for the same reason a
`pid` does: `citystate.json`'s parcel shape (`PLACEMENT_GRID.md` §5)
already proposes `road_id` as a new field once frontage is real state —
"which road" has to be nameable, not just geometrically implied, or two
parcels on parallel roads at the same local offset are indistinguishable
in the data. `ROADS_AS_MECHANIC.md`'s own road-as-polyline model is
richer than this (curved roads, multiple segments per road) — this
function only needs ONE straight segment per candidate, because
`ROADS_AS_MECHANIC.md` §0 already established that a curved road is
served by straight chord-lots anyway; a curving road's relevant unit for
THIS function is whichever segment/chord is nearest the click, not the
whole polyline at once. Practically: feeding `resolve_road` a flattened
list of segments (one entry per chord, curved roads pre-split into their
already-straight pieces) means this function never needs to know about
curvature at all — that complexity stays where `ROADS_AS_MECHANIC.md`
already put it, upstream of this call.

**Where the segment list comes from is explicitly out of scope here.**
For the existing arterial alone, it's one static entry, computable once
from `citylayout.py` the same way `PINNED_SPANS` is today. Once
player-drawn roads exist, the list grows at runtime — that's the roads
mechanic's own data structure to own and hand to this function, not
something this function derives itself.

## 4. The projection math

For a straight segment `start -> end`:

    direction = normalize(end - start)          # unit vector along the road
    normal    = perpendicular(direction)         # unit vector across it
    to_click  = (x, y) - start
    along     = dot(to_click, direction)         # position along the segment
    across    = dot(to_click, normal)            # signed distance off the centerline
    side      = 'plus' if across >= 0 else 'minus'   # road-relative, not compass

`along` is bounded to `[0, length(end - start)]` for a finite segment —
a click projecting outside that range is either off this road entirely
(nearest-road selection in §5 should have picked a different candidate,
or none) or exactly at an end, which is the intersection case §7 leaves
open. `across`'s sign is what today's `y >= 0` was really doing, just
honestly relative to the road instead of to true north — for the
existing arterial specifically (running along world X, `direction =
(1,0)`, `normal = (0,1)`), this reduces to EXACTLY today's math:
`along = x`, `across = y`, `side = 'north' if across>=0 else 'south'`
once 'plus'/'minus' are relabelled to the compass names the existing
arterial already uses in state (`PLACEMENT_GRID.md` §5's proposed
`frontage_side` field, and `PINNED_SPANS`' existing 'north'/'south'
values) — the generalization is provably a superset of the special
case, not a rewrite of it, which is the check worth re-running once
this is code: feed today's arterial through the general path and assert
byte-identical output to the current `resolve_click`.

## 5. Nearest-road selection

For each candidate segment, the perpendicular distance from the click is
`abs(across)` from §4 IF `along` falls within the segment's bounds;
otherwise the distance is to whichever endpoint is nearer (standard
point-to-segment distance, not point-to-infinite-line — a click well
past a short segment's end must not claim frontage on a road that
doesn't reach that far). `resolve_road` picks the minimum across all
candidates, subject to a MAX CLAIM DISTANCE — a click deep in a block
interior, equidistant-ish from two distant roads, must resolve to
NEITHER, the same way today's off-board check refuses a click past the
plate edge. This project's whole placement ledger already runs on loud,
specific refusal (`PLACEMENT_GRID.md` §2: "no legal frontage" is one of
the three named refusal conditions from the start, folded into
off-board in v0 only because v0 has nothing else for it to mean yet) —
once a second road exists, "too far from any road" becomes a REAL,
distinct case from "off the plate entirely," and the refusal message
should say which.

**No max-claim-distance number is proposed here.** It's a function of
building depth (how far back from the road a lot's far wall can sit
before it's obviously not part of that frontage), which is recipe/
massing data this document doesn't own — named as an open constant, not
guessed at.

## 6. What changes in the callers, concretely

- `PLATE_X_MIN/MAX`, currently a hardcoded world-space box, becomes
  either a per-road bounded `along` range (simplest: reuse each road
  segment's own finite length as its bound, no separate plate check
  needed at all) or a genuine 2-D containment test against the real
  board mesh if roads are meant to be placeable anywhere on it, not just
  within reach of a known segment. This document leans toward the
  former — a click has to resolve to SOME road under §5 before X/Y ever
  matter again, so a separate world-space plate box becomes redundant
  with the road-reach check rather than a second, independent gate.
- `PINNED_SPANS` gains a `road_id` (or stays arterial-only if the
  starter preset's 14 pins are never re-expressed against a second
  road — a real question, not answered here: does the multi-road pass
  touch the pinned starter city at all, or only player-placed lots on
  NEW roads?). Left open deliberately.
- The overlap scan (today: one list, filtered by `side`) becomes
  filtered by `(road_id, side)` — two lots on different roads with the
  same local `along`/`side` do not overlap just because the numbers
  match.
- `_next_pid`'s letters-vs-digits disjointness (`PLACEMENT_GRID.md` §5)
  is untouched — pid generation doesn't know or care which road a lot
  is on.

## 7. Named, not answered: corner lots

`citylayout.py`'s own comments already know about this — a block "has
TWO street frontages and a corner at the crossing," and `BP_Parcel`
already carries a `CornerSide` property that today's placement path
always leaves empty. A click near an intersection of two roads is
ambiguous under §5 exactly at the point where both candidates are
similarly close — real geometry, not an edge case to special-case away.
Two directions, both real, neither decided here:

1. **Nearest-wins, full stop.** A click near a corner resolves to
   whichever road's segment it's marginally closer to; corner treatment
   (if any) is a RECIPE/meshing concern triggered some other way, not
   this function's problem.
2. **Corner detection as a THIRD resolve_road outcome.** A click within
   some radius of a segment endpoint that itself touches another
   segment's endpoint resolves to a corner lot explicitly, carrying
   both roads' local frames instead of one.

This document does not choose between them — it's flagged because
`BP_Parcel`'s `CornerSide` field existing, unused, is exactly the kind
of "the data model already expected this" fact that's worth surfacing
before someone re-derives it from a support ticket instead of a grep.

## 8. What this does NOT cover

Curved-road meshing, the road-drawing verb itself, board growth
(`PLACEMENT_GRID.md` §3), and the placement-as-identity data-model
migration in full (§5 of the same document) — all named there already,
untouched by these notes. This document is scoped to exactly one
question: given more than one road exists, how does a click resolve to
one of them and a local frame on it, in a way that is a strict
generalization of the math `placement.py` already ships, not a
competing rewrite of it.
