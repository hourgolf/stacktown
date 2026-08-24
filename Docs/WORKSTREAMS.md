# Workstreams and delegation

## An honest caveat before the table

I can speak to Claude models with confidence. **I cannot verify the current
capabilities of GPT 5.6 or Kimi k3** — they sit at or past my knowledge cutoff,
and inventing a capability profile for them would be guesswork dressed as
advice.

So this document delegates by **task character** — what each lane actually
demands — rather than by claimed model strength. Map models onto lanes using
what you know of them. Where a lane has a hard requirement (tool access, visual
judgement, long-context refactor), it is stated explicitly so the mapping is
informed rather than arbitrary.

One constraint that is NOT negotiable regardless of who takes a lane:
**the illusion question is settled by a human cold read.** No model, including
me, satisfies it.

---

## Lane 1 — Disk audit and repository hygiene

**Character:** careful, destructive, low-creativity, high-consequence. Wants
patience and a bias toward asking. Needs filesystem access. Does NOT need visual
judgement or Unreal knowledge.

**Scope:** ~35 GB across three project generations.

    ~/Documents/Codex/StacktownUSA_Quarantine       11 GB   decision needed
    ~/Documents/Codex/StacktownUSA (Unity)          8.5 GB  decision needed
    ~/Documents/Codex/StacktownVisualBakeoffUE      8.1 GB  mine useful bits
    ~/Documents/Unreal Projects/StacktownAlpha      4.2 GB  active
    ~/Developer/Projects/...                        4.0 GB  other agents' sandboxes

**Safe to reclaim immediately, no judgement required (~5 GB):**
- every `DerivedDataCache/` and `Intermediate/` — regenerable by the engine
- `StacktownAlpha/Saved/Screenshots/` — 2.5 GB of raw 20 MB captures whose
  evidence is already archived under `Saved/Stage0..3/`

**Needs judgement, do not delete without the owner:** the 11 GB quarantine and
the 8.5 GB Unity project. `Docs/PROVENANCE.md` says what was deliberately left
behind; mine the bakeoff repo for the PCG city-grammar skill before anything is
removed.

**Also in scope:** downsample the archived evidence PNGs. Most are 20 MB
full-resolution captures where a 1400 px JPEG carries the same information.

---

## Lane 2 — Gameplay and trading mechanics

**Character:** design-led, no existing code to respect, no Unreal dependency at
the start. Wants strong systems reasoning and the ability to hold an economy in
its head. Benefits from writing simulation prototypes in plain Python before
anything touches the engine.

**Status: nothing exists.** Not a line. This is genuinely greenfield, and it is
the largest unknown in the project.

**The one hard constraint from the visual side:** the player zooms from a block
hero (112 m) down to a facade (9 m). Whatever the mechanics are, they must be
legible at *both*, and the 0.4% rule in `HANDOFF.md` §3 governs anything that
must be seen. A mechanic that needs a 50 mm indicator to be readable at block
range is not a mechanic, it is an invisible feature.

**Deliverable before any engine work:** a plain-Python simulation of the economy
that can be run and tuned headless. Do not build trading mechanics inside
Unreal first.

---

## Lane 3 — City generation at scale

**Character:** long-context refactor over an existing, quirky codebase. Wants
tolerance for reading a lot of prior art and respecting invariants. Needs Unreal
MCP access and the ability to run and read captures.

**Current state:** two blocks, generated, from `city.py`. Measured build rate is
**0.068 s per box** (426 boxes in 29 s) — the 0.75 s figure in the Stage 2 record
was taken under machine contention and is wrong.

**Next:** a city-layout generator above `city.py` — streets, intersections,
block subdivision — and the question of whether blocks become instanced.

**Invariants that must not be broken:**
- material role lives in the component name (`HANDOFF.md` §4.2)
- lot coordinates are block-local; world placement is on the actor transform
- every mutating script runs through `rung.sh`
- checks run inside the build, not from memory

---

## Lane 4 — Material and surface treatment

**Character:** deep, narrow, measurement-driven. Wants the patience to isolate
one variable at a time and the discipline to report a hypothesis as a hypothesis.
Needs Unreal MCP access.

**Open items,** in order of how much they unblock:

1. **Baked curvature to replace the edge-wear normal proxy.** Currently the
   proxy fires on any 45° surface — a pitched roof reads as fully worn — and does
   nothing at all on imported geometry. This is the last structural assumption
   in the material and it blocks using bought assets properly.
2. **Masked foliage variant of the master.** Alpha-tested, same card band.
3. **The single-mesh bake fidelity gap** (`HANDOFF.md` §9.1).
4. **Trace `PaperDetail`** — bound, contribution unknown.

**Read `HANDOFF.md` §5 "Measurement" before starting.** This lane is where every
expensive mistake in the project happened.

---

## Lane 5 — Lighting and camera

**Character:** small, visual, judgement-heavy. Wants an eye more than a
technique. Needs the ability to run captures and look at them.

**Open:** the key/fill rig was derived for a single row facing −Y. With two
facing rows, half of every street is in shadow. It is physically correct and
visually wrong. Also: the backdrop does not cover the view down the street.

Intensity scales with the **inverse square of rig distance** and must be
re-derived, never carried across. Getting this wrong by 65% once clipped an
entire colour band while everything else looked fine.

---

## Sequencing

Lane 1 first and alone — it is destructive and everything else is easier on a
machine that is not full.

Lanes 2 and 4 in parallel: they share nothing. Lane 2 needs no engine, Lane 4
needs no design.

Lane 3 after Lane 4's item 1, because geometry-agnostic materials change what a
city can be built from.

Lane 5 any time; it is independent and improves every capture the others take.
