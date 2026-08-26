# Thread starter prompts

Three lanes, three threads. Each is self-contained — paste it as the first
message. Repo: `https://github.com/hourgolf/stacktown` (private).

## Status, 2026-08-25

- **Prompt B (Lane 2) is superseded.** A Claude agent took the lane on
  2026-08-25, working in a git worktree from the coordinator session:
  headless economy sim (`Tools/econsim/`) plus an interaction-model memo
  (`Docs/ECONOMY_DRAFT.md`). Do not start a second Lane 2 thread without
  reading its output first.
- **Prompt C (Lane 1) is done.** The audit ran 2026-08-24 and reclaimed
  26.76 GiB — `Docs/DISK_AUDIT_2026-08-24.md`.
- **Prompt A (Lane 4) is still current**, but a joiner should also read
  `Saved/Stage3/BLOCK2_RECORD.md`, `Saved/Lane4/MATERIAL_RECORD.md`,
  `Docs/RECIPES_DRAFT.md` and `Docs/RUNTIME_SLICE.md` — the project has
  moved past Stage 2.

---

## A. New Claude thread — Lane 4, material and surface treatment

> You're joining Stacktown, a living-diorama city in Unreal Engine 5.8. The
> project is at `/Users/ben/Documents/Unreal Projects/StacktownAlpha` and on
> GitHub at `hourgolf/stacktown`.
>
> Read `Docs/HANDOFF.md` first, then `AGENTS.md`, then
> `Saved/Stage2/STAGE2_RECORD.md`. **Read §5 "Traps" twice** — every item there
> cost hours, and the Measurement subsection is where most of them happened.
>
> Your lane is the master material. Three open items, in order:
>
> 1. **Replace the edge-wear normal proxy with baked curvature.** It is
>    currently `saturate((1-max|n|)/0.30)`, which fires on any 45° surface — a
>    pitched roof reads as fully worn — and does nothing at all on imported
>    geometry. This is the last structural assumption in the material and it
>    blocks using bought assets properly. GeometryScripting is enabled and has
>    been used successfully for booleans and skeletal→static bakes.
> 2. **A masked variant of the master for foliage.** Alpha-tested, same card
>    band. Opaque card fills the gaps between alpha-cut leaf cards and turns a
>    canopy into a solid cone; the asset pack's own materials give correct
>    leaves but clash with the diorama. Neither currently works.
> 3. **Trace `PaperDetail`** — it is bound on master and instances but its
>    contribution is unknown. `PaperTiling` was similarly inert until this week.
>
> Working rules for this project: run anything that mutates through
> `rung.sh <script>`, which prepends a guard refusing to run against the wrong
> project or level — several editors run on this machine and the guard has
> already caught a script writing into the wrong one. Never call `load_level`
> over remote execution; it crashes the editor. Never put non-`.py` files in
> `Content/`.
>
> Two habits this project learned the hard way, and I'd ask you to hold to them:
> **report a cause as a hypothesis until you have isolated it by varying one
> thing**, and **check your measurement against a known answer before trusting
> it** — three separate defects survived a long time here because a check was
> asking the wrong question and returning "ok".

---

## B. GPT thread — Lane 2, gameplay and trading mechanics

> You're joining Stacktown, a living-diorama city game. Repo:
> `hourgolf/stacktown` (private). Read `Docs/HANDOFF.md` and
> `Docs/WORKSTREAMS.md`.
>
> **Your lane is entirely greenfield. No gameplay exists — not a line.** What
> exists is a visual proof: a two-block street in Unreal that reads as a
> physical card model on a board. Your job is the game inside it, and the
> trading and economic mechanics in particular.
>
> **Do not build anything in Unreal first.** The deliverable before any engine
> work is a plain-Python simulation of the economy that runs headless and can be
> tuned — agents, goods, prices, whatever the design calls for — so the systems
> can be balanced before they are ever rendered.
>
> One hard constraint from the visual side, and it is a real design input rather
> than a technicality. The player zooms between a **block hero at 112 m** and a
> **facade at 9 m**. A feature must subtend roughly **0.4% of frame width** to be
> visible at all, which means a **230 mm** minimum at block range and **19 mm**
> at the player zoom. Anything that must be *seen* — a signal that a shop is
> trading, that a building changed hands — has to clear that at the range the
> player will be at. A mechanic needing a 50 mm indicator to read at block range
> is not a mechanic, it is an invisible feature. `Docs/HANDOFF.md` §3 has the
> table.
>
> Also worth knowing: the project currently forbids signage, people and vehicles
> as *visual* elements by gate rule, though baked static pedestrians and parked
> cars now exist. If your mechanics depend on visible signage, say so early — it
> is an owner decision, not a blocker, but it needs raising rather than assuming.
>
> Start by proposing the economic model and what makes it legible at both ranges.
> Don't write engine code.

---

## C. Kimi thread — Lane 1, disk audit and repository hygiene

> You're doing a cleanup pass for Stacktown, a game project spanning three
> generations of attempts. **~35 GB across the machine and it needs to come
> down.** This is a careful, destructive task — bias heavily toward asking before
> deleting anything that required judgement.
>
> Read `Docs/WORKSTREAMS.md` Lane 1 and `Docs/PROVENANCE.md` in
> `/Users/ben/Documents/Unreal Projects/StacktownAlpha`.
>
> **Reclaim immediately — no judgement needed, roughly 5 GB:**
> - every `DerivedDataCache/` and `Intermediate/` directory under any Unreal
>   project. The engine regenerates both.
> - `~/Documents/Unreal Projects/StacktownAlpha/Saved/Screenshots/` — 2.5 GB of
>   raw 20 MB captures. The evidence that matters is already archived under
>   `Saved/Stage0..3/` and a curated set is committed to the repo.
>
> **Then downsample archived evidence.** `Saved/Stage1/` alone is 665 MB of
> full-resolution PNGs. A 1400 px JPEG carries the same information at about 1%
> of the size. Keep originals only where a record explicitly depends on
> full-resolution detail.
>
> **Needs the owner's decision — do NOT delete:**
> - `~/Documents/Codex/StacktownUSA_Quarantine` (11 GB)
> - `~/Documents/Codex/StacktownUSA` (8.5 GB, the abandoned Unity project)
> - `~/Documents/Codex/StacktownVisualBakeoffUE` (8.1 GB, abandoned UE project)
>
> Before anything is removed from the bakeoff project, **mine it**:
> `Docs/PROVENANCE.md` records that a `stacktown-pcg-city-grammar` skill was
> deliberately left behind there and should be retrieved when PCG is opened.
> Check for anything else worth keeping and copy it out first.
>
> Deliverable: a written audit — what was reclaimed, what was downsampled, what
> is awaiting a decision and why — plus the freed total. Report before/after
> figures rather than describing the work.
