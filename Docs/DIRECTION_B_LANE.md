# The Direction-B design lane — charter (staff when the work starts)

**Created 2026-08-31; STAFFING REVISED same day, coordinator's call on
an owner signal: STAFF NOW.** The original gate (wait for beta phases
A-E) was engineering economics against idling the lane — obsoleted by
two facts: phase A PROVED the catalogue pointer, which is the only
machinery the wooden catalogue actually depends on; and the owner asked
to SEE "the actual wood block model city" — a mechanism demo on grey
masses cannot carry that, and direction B's v0 look is UNIQUELY cheap
to make real, because per DIRECTION_B.md B1 the direction at massing
level IS windowless carved blocks: wooden masses with honest grain,
tone and patina ARE direction-B-v0, not a placeholder for it. The beta
lane continues phases B-E in parallel; editor windows interleave under
the standing announce discipline.**

## First commission (scoped deliberately narrow)

**THE FIRST WOODEN BOARD**: (1) the wood MATERIAL FAMILY — grain, tonal
range (pale pine to walnut per B1), and the patina AGE SCALAR (material-
level per the open question below unless argued otherwise — argue it
first, it is the lane's first declaration); (2) a WOODEN MASSING
CATALOGUE SLICE covering the test-city identity keys — massing-only
blocks through genbuild's spec layer under the byte-identical contract;
(3) the swap demonstrated: TestCity resolving through the PROVEN
ActiveCatalogue pointer to wood — the owner sees the wooden city
standing. Night glow, inlay boards, water and terrain come after the
owner has judged the first board, not before.**

## The lane's scope

The WOODEN CITY's production: the direction-B catalogue (carved-timber
massing through genbuild's spec layer), its own archetypes.py entries
(its own definition of good, with reasons — the flagship gate is never
forced), the night/information lighting system (glow = ownership +
activity + selection, subtle colour temperature per DIRECTION_B.md B4),
the patina/time material treatment, and the board's inlay construction
(water as stained inlay, carved terrain).

## Contracts the lane inherits (non-negotiable, all owner-worded)

1. **Docs/DIRECTION_B.md is the ONLY reference board** — flagship canon
   is never cited here, and this board is never cited for flagship work.
2. **Generator changes are SPEC-LEVEL with behaviour-preserving
   defaults**, proved byte-identical for flagship output via
   `python3 Content/Python/genbuild_identity.py` BEFORE any commit that
   touches generation (BETA_TWIN_PLAN seam 2; baseline committed at
   de1af18).
3. **Declare before geometry** — archetype entries and definitions of
   good precede any wooden mesh.
4. **The full process doctrine applies**: POLISH_PROTOCOL (bake policy,
   capture protocol, trap ledger), HANDOFF traps, one-writer editor
   rule, announce-before-mutate/PLAY, evidence under Saved/, commits on
   the owner's word, mkactor intent declaration (record()/live()).
5. **Simplicity buys art, not shortcuts** (owner, at intake): the wood
   direction is judged with the diorama doctrine's own standards for
   details, lighting and camera.

## Opening prompt for the session that staffs this lane

"You are the Direction-B design session for Stacktown Alpha. Read, in
order: AGENTS.md, Docs/DIRECTION_B.md, Docs/BETA_TWIN_PLAN.md,
Docs/DIRECTION_B_LANE.md (this charter), Docs/POLISH_PROTOCOL.md, and
HANDOFF §5 (traps). Your subject is the wooden city; your comparison
set is DIRECTION_B.md and nothing else. The coordinator session holds
owner-word relay, commits, and cross-lane verification; the flagship
design lane's precedents (identity manifest, byte-identical proof) are
your contracts when you touch shared generation. Announce before you
mutate. Your assignment is the FIRST COMMISSION above: argue the
patina question first (it is your first declaration), then the wood
material family, then the massing slice for the test-city identity
keys under the byte-identical contract (run genbuild_identity.py
before and after anything touching generation), then show the owner
the wooden city standing in TestCity through the ActiveCatalogue
pointer the beta lane proved. The beta gameplay session (DESIGN B
(WOOD) — title historical, it runs the BETA lane) works in parallel;
editor windows are negotiated through the coordinator."

## Open question for the lane's first session (flagged by the flagship
## design lane at handover, 2026-08-31)

**Is patina-as-time GENERATOR-level or MATERIAL-level?** This is the
one place the byte-identical contract could get quietly stretched —
"patina" could mean a new spec key or a whole second surface family.
Coordinator's lean, to be argued not assumed: MATERIAL-level — a
per-instance age scalar on the wooden shader, no geometry change,
which keeps the byte-identical proof trivially clean and makes aging
a runtime parameter the tick can drive. Decide it declaration-first,
before any wooden mesh exists.

## Addendum 2026-09-05: the LOOK seat under the C++ plan

Read Docs/PLAN_CPP_PORT.md. Your charter stands: the wooden city, wear,
night, windows, the miniature gate. What changes:
- The Blueprint lens rig is retired; the camera will be C++. Camera
  intent (Docs/LENSRIG_P0.md ladder, boom space, f-stop) stays the spec;
  send corrections to the coordinator, not to the rig.
- HUD LOOK 1-9 in Docs/HUD_V1.md is now the spec for a C++-built HUD.
  Do not build HUD in Blueprint.
- Open look items remain yours: window-grid regularity, char depth at
  full Failure, activity glow later. Same rules: explicit-path saves,
  never the flagship assets, never a PIE inside another seat's window.
- Status on Docs/BOARD.md under LOOK, ten lines, every working day.
