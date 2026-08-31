# Recipe ladders

**Owner signal, 26 Aug 2026** (from canon intake, `Docs/CANON.md` pending 5):
ladders must eventually grow past t5 — some buildings need more than five
tiers, and the city needs true highrise towers. Not a change to the current
vernacular-first plan; a direction the ladder design must not preclude.

## Status, 25 Aug 2026

**Cottage and walkup are set aside as rough drafts — preserved, not retired
(owner decision, 2026-08-25).** They were the first two recipes written and
the least refined: the cottage rendered with a blank front and blank dormers
after three separate rounds of "these need more detail". A catalogue built on
them today would inherit that, so they wait for the same
bring-it-up-to-standard detailing pass that `vernacular` is getting first.
Their baked tier meshes stay in `/Game/Stacktown/Baked/` as drafts. Before
walkup returns, the `flank_walkup` problem needs a real fix - it is the only
style falling through to a COMMERCIAL side elevation, and a residential
building in shopfront grammar is two buildings pretending to be one.

**Pipeline work is stopped.** The gate, stamp, contact sheet and all-faces
elevations work and have caught four real defects (the 842 uu garage, the
facade-only generators, the blank rear, the 156 uu flank overrun). But they
are instrumentation, and building more of them while the models going through
them are not good enough is backwards. One recipe gets brought up to standard
and judged first; only then does anything scale.

**`vernacular` is that recipe.** It already has the strongest opening
vocabulary in the project - ten parts per bay: glass recessed 27 uu, an
interior behind it, frame left/right/head, a cill, vertical and horizontal
glazing bars, and two corbels under the cill.

## Known quality defects, found 25 Aug 2026

- **Dormer glazing is buried.** `window()` recesses glass 24 uu behind the
  plane it is given; the dormer call passes `hy0 - 8`, putting glass at
  `hy0 + 16` while the dormer face spans `hy0 - 12` to `hy0 - 4`. The glass
  sits 20 uu behind the dormer's back face, inside the roof - which is exactly
  how the dormers render as blank white boxes. In `build_house`, so it is
  parked with the cottage draft and must be fixed when the cottage gets its
  detailing pass. The CLASS of bug is worth remembering: this project
  has a documented earlier instance (`Glass_Shop Y 78..80 INSIDE CORE ->
  storefronts read blank`).

---

# Ladders — DRAFT for review, not yet baked

Drafted 25 Aug 2026. Numbers below are COMPUTED from the draft, not typed —
the first version put a deco "picture palace" at 22.7 m (an office block in
deco trim) and made works t3 and t4 identical apart from a parameter that
does not exist. Both were invisible until the table was generated.

## Levers the generators actually have

| recipe | floors | bays | gf_h/fl_h | parapet | setback | roof_units | canopy | chimney |
|---|---|---|---|---|---|---|---|---|
| vernacular | yes | yes | yes | yes | top floor | yes | yes | — |
| modern | yes | yes | yes | yes | top floor | yes | — | — |
| deco | yes | yes | yes | yes | — | yes | — | — |
| works | yes | yes | yes | yes | — | — | — | bool only |

`setback` applies to the TOP floor only — a crown detail, not a massing
lever. `bays` is derived from the built width against a per-recipe bay
target, so the same tier genuinely differs across S/M/L rather than being
the same building stretched.

## The ladders

```

VERNACULAR  (commercial)  widths S/M/L  bay target 280  align left
  t   name            fill floors   S: w/bays/height   M: w/bays/height   L: w/bays/height
  t0  lock-up         0.55      0    451/2/ 380   676/2/ 380   902/3/ 380   -
  t1  shop & flat     0.72      1    590/2/ 660   886/3/ 660  1181/4/ 660   canopy=90
  t2  terrace         1.00      2    820/3/ 945  1230/4/ 945  1640/6/ 945   canopy=110
  t3  mansion block   1.00      3    820/3/1250  1230/4/1250  1640/6/1250   canopy=110,cornice=50,roof_units=1
  t4  chambers        1.00      4    820/3/1560  1230/4/1560  1640/6/1560   canopy=110,cornice=55,roof_units=3,setback=90,setback_floors=2

MODERN  (office)  widths S/M/L  bay target 300  align left
  t   name            fill floors   S: w/bays/height   M: w/bays/height   L: w/bays/height
  t0  showroom        0.60      0    492/2/ 390   738/2/ 390   984/3/ 390   -
  t1  office over     0.80      1    656/2/ 660   984/3/ 660  1312/4/ 660   -
  t2  block           1.00      3    820/3/1210  1230/4/1210  1640/5/1210   roof_units=1
  t3  slab            1.00      5    820/3/1765  1230/4/1765  1640/5/1765   roof_units=2,setback=90,setback_floors=1
  t4  tower           1.00      7    820/3/2325  1230/4/2325  1640/5/2325   roof_units=3,setback=110,setback_floors=2

DECO  (civic)  widths M/L  bay target 320  align centre
  t   name            fill floors   M: w/bays/height   L: w/bays/height
  t0  picture house   0.65      0    800/2/ 460  1066/3/ 460   -
  t1  cinema          0.85      1   1046/3/ 770  1394/4/ 770   -
  t2  theatre         1.00      1   1230/4/ 800  1640/5/ 800   -
  t3  grand           1.00      2   1230/4/1115  1640/5/1115   roof_units=1
  t4  palace          1.00      3   1230/4/1435  1640/5/1435   roof_units=2

WORKS  (industrial)  widths M/L  bay target 380  align centre
  t   name            fill floors   M: w/bays/height   L: w/bays/height
  t0  lock-up yard    0.40      0    492/2/ 475   656/2/ 475   -
  t1  shed            0.62      0    763/2/ 535  1017/3/ 535   -
  t2  works           0.85      0   1046/3/ 595  1394/4/ 595   chimney=True
  t3  foundry         1.00      0   1230/3/ 695  1640/4/ 695   chimney=True
  t4  plant           1.00      1   1230/3/ 995  1640/4/ 995   chimney=True,chimney_h=1.7

catalogue: 50 meshes (10 recipe-width combos x 5 tiers)
```

## Crown levers — BUILT and rendered 25 Aug 2026

Vernacular and modern tiers were differing only in floor count, which reads as
one building photographed at three heights. Three changes, all built and
looked at before any of this was baked:

- **`roof_units` distribution fixed.** Unit *u* sat at
  `x0 + W*(0.28 + 0.42*u)`, so the THIRD unit landed at 1.12 x width — off
  the end of the facade. No ladder had asked for three until now. GATE-05
  would have refused the mesh as wider than its parcel; the fix belongs in
  the generator.
- **`setback_floors`** — the top N floors each step back a further notch, so
  the crown steps rather than making one plane break.
- **`cornice`** — three courses (bed mould, corona, cap) for vernacular.
  Modern keeps its flat coping over a shadow gap; that is its identity, not
  an omission, so modern's grandeur is the stepped crown and roof plant.

Two errors showed up on the first render and are fixed:

1. **The parapet ignored the setback** — pinned to the full front plane while
   the floors behind it stepped back, so it hung 180 uu out in front as a
   floating shelf.
2. **The cornice crowned the wrong mass** — placed at the very top, above the
   set-back attic, so the attic wore it as a hat. It now sits at the top of
   the main mass with the setbacks rising behind it.

## Elevations: every face, decided 25 Aug 2026

A catalogue model gets **full elevations on all four sides**.

The owner spotted it from a screenshot: the crown-test renders were facades
and crowns, not buildings. Measured, share of a building's parts sitting
behind its own front third:

    Court  (modern)  1.3%     Terrace  32.5%
    Narrow (vern)    1.9%     Depot    43.8%
    Civic  (modern) 18.0%     Bijou      59%

`build_vernacular`, `build_modern` and `build_deco` emit a street front and a
roof. Flanks and rear come from `step_elevations`, which treats only the two
END lots of a block on their outward side - because a mid-terrace flank is a
party wall buried against its neighbour. Correct for a fixed city.

**A catalogue mesh has no neighbours.** It lands wherever the grammar or the
player puts it, so it must be right freestanding. The cost is asymmetric: a
blind wall is a visible bug the moment a model sits on a corner, while a
window hidden behind a neighbour is a few hundred triangles nobody sees.

`step_elevations.freestanding()` treats both flanks and the rear, and
`bake_catalogue` calls it before the role sweep. Its label set was also wrong:
`BLD2_*_H / BLD2_*_A / PLOT_*` is complete for house and walkup and misses
everything the commercial generators emit (GF, F0..Fn, Roof, Canopy, Shaft)
plus every `ELEV_` face. Left alone it would have baked 30 hollow meshes.

### Two rules, because these are two defects

- **GATE-07** - at least 20% of a model sits behind its own front third.
  Catches a FACADE. Fires on Court (1.3%), Narrow (1.9%), Civic (18%).
- **GATE-08** - the rear face carries at least 10 parts, not a blank wall.

GATE-07 alone was not enough and the walk-up proved it: all three tiers passed
it and baked, and the contact sheet then showed `walkup_t2` with a completely
blank back. GATE-07 asks "is there a building behind the front" and a walk-up
has balconies and stairs all through its depth, so it passes honestly. The
blank rear is a different question and needed its own rule.

## What this needs that does not exist yet

1. **`fill`** — the fraction of the parcel the building occupies. Costs NO
   generator change: every generator derives from `spec[x0]` and
   `spec[width]`, so a reduced width with an offset x0 gives a narrower
   building. It does need the plot split, because something has to dress
   the leftover.
2. **`chimney_h`** — works t4 is otherwise identical to t3. Small change;
   `chimney` is a bool today. (`fill`, `setback_floors` and `cornice` are
   now built; this is the only generator parameter still missing.)
3. **`align`** — vernacular and modern sit against one party wall so a
   partly-built street still reads as a street; deco and works centre in
   their plot.
