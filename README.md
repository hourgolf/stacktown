# Stacktown

A **living diorama city** — a city that reads as a physical card and paper model
on a board under studio lights, which the player can zoom into.

Unreal Engine 5.8. **Two products share one game** (`Docs/BETA_TWIN_PLAN.md`):
the flagship card-and-paper miniature, and a market-test twin — **the wooden
city** (`Docs/DIRECTION_B.md`), carved timber on an inlaid board. As of
2026-09-02 the twin is PLAYABLE in `/Game/Maps/TestCity`: fly the boom,
click a lot, buy it, watch a wooden building rise and grow on a real
economy tick (`Docs/ECONOMY_TICK_CONTRACT.md`, `Docs/PARCELIZATION_CONTRACT.md`).
Roads and free placement are designed, not yet built
(`Docs/ROADS_AS_MECHANIC.md`, `Docs/PLACEMENT_GRID.md`). The flagship's own
look work lives in `Sandbox_Bench` / `Stage2_*` and is currently on break.
(Currency note, coordinator: the line this replaced said "no gameplay
exists yet" and predated all of the above.)

## Start here

| document | what it is |
|---|---|
| **[Docs/HANDOFF.md](Docs/HANDOFF.md)** | **read this first** — state, architecture, and the trap list |
| [Docs/WORKSTREAMS.md](Docs/WORKSTREAMS.md) | the five lanes and how to divide them |
| [AGENTS.md](AGENTS.md) | the development contract. Authoritative. |
| [Docs/ONE_BUILDING_GATE.md](Docs/ONE_BUILDING_GATE.md) | what "done" means, and the approved carve-outs |
| [Docs/MINIATURE_RECIPE.md](Docs/MINIATURE_RECIPE.md) | every measured number |
| `Saved/Stage0..3/*_RECORD.md` | what was tried, what failed, and why |

## Two things that will bite you

**This is not photoreal.** Every technical decision follows from the model
illusion. Uniform colour, varied sheen and edges — large-scale albedo variation
is the trap and it stays a trap.

**`Content/AssetsvilleTown/` is not in this repository.** It is a paid Fab
entitlement (680 MB). Add it to your own project from your own account.

**A click on empty board is a build order, not just a deselect.** As of
`PLACEMENT_GRID.md`'s v0, `BP_LensRig`'s click handler treats "didn't hit
a parcel" as "try to place one here" — so clicking away from a selected
lot to clear it can also attempt a placement. Deliberate, not a bug: the
owner asked for click-anywhere-there's-board, and `placement.py`'s own
refusal rules (off-board, overlap) keep it safe. The likely next step if
this reads wrong to a player is a placement MODE rather than every stray
click being a build order — the handler is deliberately structured so
that split is one branch away, not a rewrite.

## Running a build

```bash
cd Content/Python
python3 build_block.py     # block A, end to end, then the checks
python3 build_blockB.py    # block B
```

`rung.sh <script>` prepends `_guard.py`, which refuses to run against the wrong
project or level. **Use it for anything that mutates** — several Unreal editors
run on this machine and the guard has already caught a script writing into the
wrong one.
