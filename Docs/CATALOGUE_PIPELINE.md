# The catalogue pipeline

**Written 2026-08-27.** How a building gets from a dict in `recipes.py` to a
mesh standing in a street, what the levers actually are, and the traps that
have each cost real time. Read after `AGENTS.md` and `ONE_BUILDING_GATE.md`.

`INVARIANTS.md` covers rules over a *level*. This file covers the pipeline that
produces the things in it.

---

## 1. The shape of it

```
recipes.py  →  genbuild.build()  →  modelgate  →  merge  →  stamp  →  place
  a dict        parts, in memory     pure rules   one mesh  verdict   street.py
```

**One generator, never two.** `genbuild.py` is the only thing that emits
geometry. A new building type is a new *parameter set* in `recipes.py`, not a
new generator. Every time this project has grown a second generator it has
grown a second set of bugs and a second visual language.

### The recording sink is the reason any of this is measurable

`genbuild.record()` / `genbuild.drain()` swap the backend: instead of calling
into the editor, every `box()`, `slab()`, `piece()` and `mkactor()` appends a
plain dict to a list. Same generator, same code path, no editor.

That is what makes the model **inspectable as data before it is geometry**, and
it is the single most useful thing in the codebase:

- the gate runs on it, while the model is still parts — after the merge it is
  one component and every rule goes blind
- variation levers can be diffed offline (§3)
- a whole-catalogue sweep needs no editor and cannot crash one

Record shapes: actor `{kind, name, loc, rot}`; box `{kind, actor, name, c, d, r}`
where `c` is the centre and `d` the dimensions; mesh `{kind, actor, name, asset,
c, r, s, mat}`. **Boxes do not have `loc`/`size` fields** — diffing for those
names silently reports "nothing changed", which is exactly the false negative
that happened on 27 Aug and is why §4 exists.

## 2. Two execution channels, and the rule about mixing them

| channel | how | use for |
|---|---|---|
| **MCP** | `ue.tool(...)`, local `python3` | queries, captures, single edits |
| **remote exec** | `Tools/rung.sh <script>` | anything that mutates the level |

`rung.sh` prepends `_guard.py`, which refuses to run against the wrong project
or a level outside `_ALLOWED = ('Stage1_Building', 'Stage2_Block',
'Sandbox_Bench')`. Everything that writes goes through it.

**Never call `ue.tool` or `genbuild.build()` in live mode from inside a rung
script — it deadlocks.** The script is already executing inside the editor;
an MCP call from there waits on the thread it is running on.

**Never call `load_level` over remote execution. It crashes the editor.**
This is why new maps have to be created and opened by hand, and why the
street currently shares `Sandbox_Bench` with the review shelf.

**One writer at a time.** Announce before mutating. Two rung scripts against
one editor will interleave and the result is not reproducible.

## 3. The variation levers, measured

Ranked by what actually restructures a building. Measured 27 Aug 2026 on
`vernacular3` t4 w1640 by diffing recorded part lists:

| lever | parts restructured | moves past the 39 uu block threshold | max move |
|---|---|---|---|
| **parcel width** 1640→2050 | 322 | 5 | **410 uu** |
| **tier** 4→5 | 243 | 5 | 64 uu |
| **seed** | 2 | **0** | **0.00 uu** |

**The seed is not a variation lever.** It swaps two rooftop clutter meshes — an
air conditioner becomes an antenna — and moves no geometry at all on most
recipes; only those owning a stairhead move anything, and that is 3 parts. Any
plan that relies on per-parcel seeds to stop a district reading as wallpaper is
relying on nothing. Vary the **parcel**.

This is why `street.vary_repeats()` forbids two parcels on a block from sharing
`(recipe, tier, width)` — that triple *is* the baked asset name, so sharing it
means placing the identical mesh twice. Width is tried before tier: it
restructures more, and it keeps the building's story (same type, bigger plot)
rather than implying the owner rebuilt.

## 4. Measurement discipline

Every one of these was bought with hours.

**Check the instrument against a known answer before trusting a null result.**
A diff that reported "0 fields changed" was reading field names the records do
not have. A 60 uu parcel change moves 477 fields — running that first turns a
silent false negative into an obvious pass.

**Measure the statistic that can see the defect.** Frame *mean* cannot see
shimmer; it took a per-pixel frame delta to see the flicker at all. Ask what
number would move if the defect were present.

**Point the camera at the thing.** Two flicker investigations sampled facades
and empty floor while the reported defect was on roofs.

**Let Lumen converge.** A reading taken right after replacing 194 meshes was
19.39%; settled, the same view reads 0.76% across four runs within 0.01%. A
four-config sweep was built on the unconverged number.

**A cause is a hypothesis until isolated by varying one thing.** The flicker
was two independent faults — z-fighting I introduced, and four Lumen cvars a
diagnostic left at 0 and never restored. Session state does not show in a diff.

**Reconcile expected against produced.** "188 of 194 stamped, 0 failures" was a
job list written without a trailing newline, so bash's `while read` dropped its
last line. Count what you asked for against what came back.

## 5. Traps that are still live

- `preview.py` runs `fastbake` with `capture_output=True` and surfaces only the
  `FASTBAKED` line. Real errors are inside the captured output.
- `get_actor_bounds` **includes the editor billboard**, which swamps anything
  thin. Assert on location and compute the top yourself.
- `unreal.Rotator(roll, pitch, yaw)` — *not* `(pitch, yaw, roll)`. Passing yaw
  second set PITCH 180 and stood an entire street row on its head.
- Donor meshes are **multi-slot**. Binding one material across the whole mesh
  is what made all foliage render as dark quads; `rolemap.material_for_slot()`
  resolves per slot. Never re-derive that as "alpha doesn't survive the merge".
- Donor pieces have **arbitrary pivots**. `SM_drainPipe_ending` spans local
  z −59.8..0, so placing it by its origin buried it. Place by where the bottom
  lands, and self-test it.
- **Vet a donor by rendering it, not by its name.** `SM_roofStand_donut` was
  picked by name and read as a giant car tyre on a tower crown. `donorsheet.py`
  exists so donors are looked at before use.

## 6. Where the bodies are

| file | what it owns |
|---|---|
| `genbuild.py` | the only geometry emitter; feature flags per era |
| `recipes.py` | 32 recipes × tiers × declared widths; `asset_name()` |
| `cores.py` | core massing, `setback_at()`, `ROOF_CLEAR` |
| `modelgate.py` | 10 pure rules, self-tests run FIRST |
| `fastbake.py` | merge; per-slot donor materials; non-uniform scale |
| `palette.py` | 9 schemes × 5 roles, keyed on parcel identity not tier |
| `stagegeo.py` | board top z=0, room floor z=−128 |
| `blockrig.py` | block key/fill, derived by inverse square |
| `street.py` | the block layout and `vary_repeats()` |
| `avkit.py` | vetted donor pieces, with a `REJECTED` list and reasons |
