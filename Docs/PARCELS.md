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
    S 820      M 1230      L 1640

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
