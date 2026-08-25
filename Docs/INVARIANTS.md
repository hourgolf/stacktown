# Invariants

`AGENTS.md` §Reporting: **"Never turn the owner into the regression suite."**

That line was being violated every session. Pedestrians, translucent vehicles,
cars laid out at random, lamps through cars, the sand-pit plaza, the dark
lighting, lampposts in the road, tree scale — every one found by the owner's
eye, none by a check. This file is the index of the rules that now look for
them instead, and the record of which defect bought each one.

## How a rule works

Rules live in `Content/Python/invariants.py`. Each is a **pure function over a
snapshot** of the level (`snapshot.py` reads the level into plain data once, so
every rule sees the same world and no two rules can disagree about what is in
it).

Two properties are not negotiable:

**1. Every rule scans the whole level.** `check_block.py` records in its own
header that it printed `PASS (0 failures)` through the entire construction of
blocks B and C while only ever looking at block A. No rule takes a "which
block" argument.

**2. Every rule proves it can see its own defect.** Each carries a self-test
that builds a synthetic level with one clean case and one planted defect, and
asserts the rule finds exactly the planted one. **Self-tests run first; if any
fails, the suite reports nothing about the level at all.** A suite that cannot
detect a planted defect has no standing to call anything clean.

This is aimed at one specific failure. `check_clear.py` reported
`0 lamp/vehicle intersections` while searching for `SUR_lamp*` and `VEH_*`;
the actors are `LAMP_s*`, `LAMP_a*` and `BAKED_veh*`. It was not wrong about
the world — it was asking about actors that do not exist, and it answered
"clean" with complete confidence. The self-test caught the same class of
mistake the first time this suite ran: the "clean" lamp in DRESS-03's test was
sitting in the avenue carriageway, so the rule found two violations instead of
one and the suite refused to run.

## Adding a rule

**A defect the owner reports by eye is a bug in the suite as well as in the
world. The rule lands before the fix ships.** Write the rule, write its
self-test, add the row here naming the defect that caused it, then fix the
world.

Thresholds are drawn from measured distributions, never invented — a rule with
an invented number either never fires or fires on correct data. Re-derive them
with `thresh_probe.py`.

## The label registry

`Content/Python/labels.py` is the one place actor label families are spelled.
No check spells a family itself; they all read it from there. `NAME-01` fails
when the level contains a family the registry does not list, so a script that
invents a prefix is caught the pass it is written rather than six blocks later.

A **family** is the leading run of capitals in a label: `LIGHT2_Narrow_Shop` is
`LIGHT`, `LAMPLIGHT_s1F_0` is `LAMPLIGHT`. Anything finer is decided by the
**mesh name**, not the label — label conventions drift between scripts, a mesh
name is a fact about the asset. The zone planting bag forces this: it puts
bushes in labels ending `_t`, so `_t` does not mean tree and never did.

Re-derive the registry from the level with `census.py`.

## The rules

| id | rule | threshold drawn from | the defect that bought it |
|---|---|---|---|
| `NAME-01` | every actor label family is in the registry | — | `check_clear.py` searched for `SUR_lamp*`, found nothing, reported clean |
| `NAME-02` | no component auto-renamed to `StaticMesh<N>` | — | reusing `Wall_Pier0` across floors made UE silently rename 122 components |
| `MAT-01` | zero unassigned or engine-default material slots | — | gate **B1**: flat-green default materials shipped in the last project's final evidence image |
| `DRESS-01` | no lamp column inside a parked vehicle | pole footprint 40 uu square | far-side lamps were placed 62 uu *into* the carriageway, spearing parked cars |
| `DRESS-02` | nothing parked inside a junction keep-clear | carriageway + 270 uu (half a car) | street parking lanes ran the full board width; 10 of 49 cars stood in an intersection |
| `DRESS-03` | no lamp column inside a carriageway | zero tolerance | owner: "lightposts in the middle of the roads" |
| `DRESS-04` | every dressing actor stands on the board | zero tolerance | dressing placed from street tables that run past the board edge |
| `SCALE-01` | a street tree overhangs the kerb by ≤ 200 uu | measured: 31 of 73 trees overhang, worst 618 uu into a 1400 uu road | owner: trees oversized; a 618 uu overhang eats 44% of the carriageway |
| `SCALE-02` | zone planting is smaller than the narrow dimension of its lot | measured crowns: `SM_tree_02` 1131–1613 uu, `SM_tree_03/04` 374–715 uu | owner: "the trees in the plaza are badly oversized" — a 1613 uu crown cannot stand in a 610 uu plaza |
| `ZONE-01` | planting sits in a lawn panel or bed; seating sits on ground it can | — | owner: "benches strewn about and trees planted in sidewalks rather than the authored planting beds" — `zones.py` drew the beds, `fix4_props.py` planted at uniform random across the whole lot |
| `ZONE-02` | a bench faces open ground, not a wall | bench forward measured from vertices: `SM_bench` backrest at mean X −30.6, seat at +0.8 over 306 verts, so it faces +X at yaw 0 | owner: "the benches seem to be rotated illogically" — they were placed at block yaw ± 180, which has nothing to do with what they look at |
| `LIGHT-01` | no practical aimed within 30° of vertical | measured: all 304 practicals sit at pitch −12.5..0; the defect was pitch 90 | 43 practicals had `Rotator(0,90,0)` read as yaw when it is pitch — "a horizontal bar of light casting upwards" |

## Not yet folded in

These are real checks that run in the build but are not yet rules here, because
folding them in means rewriting working code and that is a separate risk:

- `check_block.py` — buildings present, lots match the table, no unintended
  overlap, party walls declared. Carries its own two self-checks.
- `gap_check2.py` — no hollow facade; worst void behind any facade ≤ 6 uu.

Both run before `invariants.py` in `build_block.py` and `build_blocks.py`.
Folding them in would give one runner and one report; until then this file is
the index and the build runs three.

## Kinds of open lot

`green` — lawn-dominant strip with a path through it. `plaza` — paving-dominant
civic square with a fountain as its focus, planting in **pits**. `park` — lawn
either side of a walk. `vacant` — a cleared site.

A **pit** is the distinction that took three attempts to see. A tree in a lawn
panel must be *contained* by it; a tree in a paved square stands in a pit and
*overhangs* the paving, which is what a pit is for. Sizing a corner bed to
contain a canopy kept failing, and the reason was not a number — the smallest
crown we own is 348 uu across and no corner of a 1400 uu square clears the
fountain by that much. `ZONE-01` therefore checks a pit tree by its **trunk**
and a lawn tree by its **crown**. For the same reason the fountain keep-off is
tested against the trunk: it exists to stop things standing in the water, and a
canopy above it is exactly what a tree beside a fountain does.

## The zone layout

`Content/Python/zonelayout.py` is to an open lot what `labels.py` is to actor
names: the one description both sides read. `zones.py` **builds** the forecourt,
lawn, spine, beds and basin from it; `fix4_props.py` **plants into** it — trees
in lawn panels, shrubs in beds, benches on paving. Before this they were two
scripts with separate ideas about the same ground, and the old hard-coded bed B
was authored at `cy+150`, past the back edge of a 610 uu lot.

The layout is adaptive because depth decides what fits: a full path cross needs
about 700 uu of lawn to leave usable quadrants, so shallower lots get a single
spine instead.

## Standing state

First run over the two-block city, 1015 actors / 6944 visible components:

```
self-tests: 12/12 rules proved they can see their own defect
NAME-01   ok     NAME-02   ok     DRESS-01  ok     DRESS-02  ok     LIGHT-01  ok
MAT-01    FAIL   216 components on WorldGridMaterial - all 54 lamps, 4 parts each
DRESS-03  FAIL   12 lamp columns standing in a carriageway
DRESS-04  FAIL   1 street tree 67 uu off the board
SCALE-01  FAIL   12 street trees overhang the kerb, worst 523 uu
SCALE-02  FAIL   1 park tree, 1613 uu crown in a 1280 uu lot
invariants: 12 rules, 0 violated
```

All eleven are green. The five that were red on the first run are recorded
above with the defect each one caught; `MAT-01` had never been reported by
anything, and the lamps had been rendering on the engine default material since
the day they were built.
