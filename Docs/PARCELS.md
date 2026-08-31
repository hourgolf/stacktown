# Parcels — the width ladder, growth, depth and tiers

Decided 25 Aug 2026. These four answers together fix the size of the catalogue
and the shape of the grammar, so they are written down rather than carried in
anyone's head.

## The measurements they came from

The nine built blocks were measured before any of this was chosen. Widths
already clustered into three bands and depth already varied by district — the
ladder below formalises what the city had drifted into, rather than imposing
something new on it.

    widths in use   740 820x5 860 980 1000x2 | 1120 1300x2 1330 1340 1350
                    1400x3 1420 1450 | 1600 1900
    depths in use   620-820 commercial | 1150 industrial | 1500 residential
    block widths    3040 3200 4100x4 4150x2 5000

**4100 = 5 x 820**, which is exactly how block F fits five houses.

## 1. Growth: fill the parcel, then rise

A parcel's width is fixed when it is placed. Tier 1 occupies part of it and
later tiers widen to fill it, and only then add storeys. So the same recipe
tells a different growth story on a small parcel than on a large one, which is
the point — a wide parcel and a narrow one are not the same building at
different heights.

Mesh identity is therefore **recipe + parcel width + tier**.

## 2. Widths: one shared ladder, per-recipe eligibility

    module 410
    S 820   M 1230   L 1640   XL 2050   XXL 2460   XXXL 2870

### Assembly — growing sideways before growing up (2026-08-26)

A building grows vertically only as far as its LAND allows. Past that it has
to grow horizontally first, which means acquiring the parcel next door and
demolishing what stands on it. Owner: *"not all buildings grow vertically in
real life."*

Each tier declares `needs` - the minimum parcel it can stand on. A tower on an
M lot tops out as a low block:

    parcel  tops out at        buy next door   becomes   new ceiling
    M       t2 low block       S               XL        t5 tower
                               M               XXL       t6 landmark
    L       t4 high rise       S               XXL       t6 landmark
    XL      t5 tower           S               XXXL      t6 landmark
    XXL     t6 landmark        - (maxed)

`unlocks` raises the CEILING; the building still grows through the tiers
between. `parcels.py` holds the arithmetic and its self-tests.

**The module is what makes this clean.** Lots tile edge to edge and every
width is a multiple of 410, so any two adjacent lots merge onto another ladder
width exactly - no offcuts:

    S+S = L     S+M = XL    M+M = XXL    S+L = XXL    M+L = XXXL

**Assembly overshoots, deliberately.** The smallest lot is 2 modules, so an M
(3) can never become an L (4) - the smallest neighbour it can take is an S,
landing it on XL and skipping a rung. Land comes in lots, not slices. That is
a consequence of the module rather than a flaw, and `parcels.py` asserts it so
nobody later "fixes" it.

### PINNED, not built: assembly only grows one way (2026-08-26)

Owner, on seeing the whole catalogue laid out together: buildings currently
only get **wider along the street**, then go up. The ladder is effectively
1x1 -> 1x2 -> 1x3 -> up. It should be able to grow in BOTH directions -
something nearer:

    1x1  ->  1x2  ->  2x2  ->  3x3  ->  up

That is a bigger change than a width table. Today a parcel is a WIDTH on a
block of fixed depth, and depth is a district property (see 3 below), so
growing backwards means a parcel can annex the lot BEHIND it - which is a
different neighbour, on a different street, possibly in a different block.
It also gives "buy the building next door" a second axis and makes corner
sites genuinely valuable.

Consequences to think through before building it:

  * `needs` becomes an AREA or a (w, d) pair, not a single width
  * mesh identity gains depth, so the catalogue grows by a depth factor -
    unless depth stays absorbed by the plot, which is what section 3 relies on
  * blocks are currently two rows back to back; annexing rearwards crosses
    that party line
  * `citygeom.lot_rect` and the block table assume one row of lots per side

To be workshopped with the owner before any of it is coded. Recorded here so
it is not rediscovered later as a surprise.

**Filler recipes carry no `needs`** and do not accept assembled parcels: a
lock-up on an XXL lot is not filler, it is a wasted corner.

A 4100 block tiles many ways: `820x5`, `1640+1230+1230`, `1640x2+820`,
`1230x2+820x2`. The current ad-hoc widths (1300, 1350, 1400, 1450) do not
tile and are why blocks have needed hand-fitting.

Each recipe declares which sizes it accepts — `works` refuses S, a cottage
refuses L — so the vocabulary stays at three while the categories still
differ.

## 3. Depth: per-district ranges, not one number

Fixed per-district depth was rejected: *"i don't want this to become a
monotonous grid city"*. So a district declares a RANGE and parcels vary
within it.

    commercial   620 - 820
    residential  1400 - 1600
    industrial   1050 - 1250

**This only stays affordable if depth is NOT part of mesh identity**, or the
catalogue triples. It can be kept out, because a building does not fill its
parcel's depth: measured, a house is **430 deep in a 1500 parcel** — 250 of
front garden and 820 of backyard absorb the rest.

**Consequence, and it is a real change:** the bake currently merges `PLOT_`
into the building mesh, so the baked cottage spans 1492 and depth *is* baked
in today. The plot has to come out of the bake — building mesh at a fixed
footprint, plot dressing sized to the parcel at placement. Until that split
happens, depth variation is not available.

## 4. Tiers: five

    office   small 1-2st -> larger 1-2st -> 3-4st -> taller -> tower
    house    house -> bigger house -> small mansion -> mansion -> estate

    4 recipes x 3 widths x 5 tiers = 60 baked meshes

## Recipes to build

`vernacular`, `modern`, `deco`, `works`. `cottage` and `walkup` were the first
two written and are the weakest — cottage needs the most detail work — so they
are not the set to build the catalogue on.
