# Packaged beta charter — what moves, where, and how we'd prove it

Coordinator's ask, 2026-09-03, HEADLESS: everything that lives in editor
Python today and would have to move for a build the owner can hand to a
tester, per item — the Blueprint-or-C++ home it would get, and what its
proof would be. No code in this pass. The owner is deciding WHEN to port
(PLAYABLE_PLAN.md section 2.7 already named this "a strategic call for the
owner") — this document is what they'd be deciding on, not a plan already
chosen.

## 0. What this document is, and isn't

A survey and a set of recommendations, not a plan of record. Every "home"
below is architectural reasoning grounded in this project's own code and
its own Config files — checked directly this pass, not recalled from
general engine knowledge — but nothing here has been run against an actual
packaged build. Section 5 says this again, plainly, at the end, so it
isn't lost in the middle.

## 1. The one fact that decides everything else

`PythonScriptPlugin` and `EditorScriptingUtilities` are both `"Enabled":
true` in this project's own `.uproject`. `EditorScriptingUtilities` is
unambiguously editor-only by name and purpose — it's the actor-bounds/
asset-tool surface this whole session's own tooling has leaned on.
`PythonScriptPlugin`'s runtime module is not loaded in Game/Client/
Shipping targets by default; nothing in `Config/DefaultEngine.ini` here
overrides that (checked — the only Python-related block there is the
remote-execution channel comment, itself explicitly an editor-only
convenience for agents).

As configured today, **none of `Content/Python/*.py` runs at all in a
packaged build** — not slower, not degraded, absent. That makes this
exercise a rewrite, not a port in the "recompile it" sense: every item
below is really answering "what does this look like in Blueprint or C++
instead," not "how do we ship the `.py` file."

One escape hatch, named so it isn't silently foreclosed rather than
recommended: UE's PythonScriptPlugin has, in some engine versions, an
option to cook Python for non-editor use. Not evaluated against this
project's UE 5.8 specifically. If the team would rather spike that than
commit to the rewrite below, that is a separate, small investigation —
this charter does not assume it works, and does not rule it out.

## 2. What's actually engine-dependent vs. what's just Python-shaped

Grepped, not recalled, 2026-09-03 — the real `unreal.*` surface in use:

- **citytick.py / econrules.py / placement.py**: zero `unreal` imports,
  confirmed both in each module's own docstring and by grep. The economy
  math and the click→lot geometry are pure Python today — portable in the
  sense that the LOGIC transcribes directly to Blueprint math nodes or a
  C++ function, but the FILES themselves cannot run as-is in a packaged
  build (there is no Python interpreter present at all). Transcription,
  not reuse.
- **clickdriver.py / init_unreal.py**: the editor-only surface is
  narrower than "everything." `unreal.register_slate_post_tick_callback`
  (the driver's own scheduling — Slate is the editor's UI framework; this
  callback type has no packaged-game equivalent) and
  `unreal.get_editor_subsystem`/`UnrealEditorSubsystem` (how the driver
  reaches the PIE world — a packaged game just IS the world, this whole
  discovery step disappears) are the real blockers. Most of the actual
  OPERATIONS called along the way — `GameplayStatics.get_player_controller`
  /`get_game_instance`/`get_all_actors_of_class`,
  `SystemLibrary.line_trace_single`/`draw_debug_box`/`print_string` — are
  normal runtime Blueprint nodes with no packaging problem at all; the
  issue is that Python is the one calling them on a per-frame poll, not
  that the operations themselves are editor-only.
- **State kept as ad hoc attributes on the `unreal` module object itself**
  (`_stacktown_driver_state`, `_stacktown_place_width`,
  `_stacktown_clickdriver_handle`, and the rest of that family) has no
  packaged-game home at all — there is no persistent Python module to hang
  a global off between frames. Every one of these needs a real owner: a
  GameInstance property, an Actor member, or a Subsystem.

## 3. Per-system charter

### 3.1 Economy tick
citytick.py / econrules.py, driven today by init_unreal.py's
`_city_driver_tick`.

- **Today**: a Slate post-tick callback, polling every `_TICK_INTERVAL_S`
  = 2.0s, running growth-threshold/rent math in Python against JSON state.
- **Home**: Blueprint, on a looping Timer (`SetTimerByEvent`, 2.0s) on
  GameState or a dedicated `CityEconomyActor` — not GameMode (doesn't
  exist on clients, and this project's own `.uproject` description names
  its scope as "one-building miniature," not a multi-client game, but
  GameState is still the conventionally correct single-source-of-truth
  actor for shared state, and costs nothing extra to use). C++ is not
  required by complexity — ECONOMY_TICK_CONTRACT.md's own formulas are a
  handful of arithmetic lines — recommend Blueprint FIRST, **human-
  authored and human-verified directly in the editor**, not Claude-driven
  DSL writes. That distinction matters: this session's own scars
  (HANDOFF.md, "BLUEPRINT GRAPHS ARE NOT READABLE FROM PYTHON") are about
  the automated write_graph_dsl pipeline specifically, not about Blueprint
  as a host being unreliable. A human wiring nodes by hand, or reading the
  graph back visually, doesn't hit that failure mode.
- **Proof**: a packaged (or standalone `-game`) build left running 10
  minutes shows the same tier-up cadence ECONOMY_TICK_CONTRACT.md's own
  pacing table predicts, cross-checked against a parallel PIE session
  started from identical state — the same "compare against a hand-derived
  number" acceptance shape this project has used all session, not "it
  compiled."

### 3.2 Placement
placement.py — `resolve_road`/`resolve_click`/`place`.

- **Today**: pure Python, called from clickdriver.py against a raycast
  hit result.
- **Home**: the strongest C++ candidate on this list — not because
  Blueprint can't do it (it's arithmetic and comparisons, nothing
  exotic) but because this module already carries 26 precisely-specified,
  self-tested cases (this file's own `__main__` block) that a C++ port
  could compile against nearly verbatim as an automation test target,
  which a Blueprint graph has no equivalent way to be unit-tested against.
  `AutomationTestToolset` is already enabled in this project's
  `.uproject`. If the team isn't ready to stand up a C++ module yet — none
  exists today, see section 4 — Blueprint is a legitimate fallback, just
  without that same test-portability.
- **Proof**: port the 26 self-test cases as either a C++ automation test
  or, if Blueprint, a Blueprint-callable test harness run from an editor
  utility widget — same input/output pairs, same assertions, run against
  the ported implementation, not re-derived by eye.

### 3.3 Click driver / input
clickdriver.py.

- **Today**: Python polls `pc.is_input_key_down` every frame via the
  Slate post-tick callback, with edge-detection state in a Python dict.
- **Home**: Enhanced Input, bound to Blueprint events (Pressed/Released/
  Triggered) on the player's own Pawn/PlayerController Blueprint. This
  isn't a workaround standing in for what Python did — it's the
  architecturally cleaner shape (event-driven, not polled) that the
  Python approach was itself standing in for, because Python had no event
  hooks to bind to and could only poll. The raycast
  (`get_hit_result_under_cursor_by_channel`) and the ghost-preview drawing
  are both normal runtime PlayerController/SystemLibrary calls already —
  directly callable from Blueprint, no translation needed.
- **Proof**: the reset-hold latch (`RESET_HOLD_S` = 2.0, hold-then-
  release, `_st['n_acc']`/`_st['n_fired']` today) and the width-scroll
  cycle are the two pieces of real STATE this port has to get right, not
  just "a click places a lot." Acceptance: in a packaged build, holding N
  for under 2.0s does nothing, releasing early does nothing, holding
  through 2.0s fires exactly once — a live-observed proof, same as the
  ghost pad's own acceptance test was, not something headless.

### 3.4 State persistence
citytick.py `save_state`/`load_state`; `GameInstance.CityStateJSON`
passthrough (`_read_state`/`_write_state`, init_unreal.py).

- **Today**: a plain JSON file at `Content/Python/citystate.json`, read
  and written by Python's own `open()`/`json` module, mirrored onto
  `GameInstance.CityStateJSON` as a string property.
- **Home**: the SHAPE survives almost unchanged. A GameInstance (or a
  `USaveGame` object) holding the live state, serialized via UE's own
  JsonUtilities/JsonObjectConverter (Blueprint-callable) or a small C++
  helper, is a completely normal packaged-game pattern — if anything, the
  "GameInstance holds the live truth" architecture ECONOMY_TICK_CONTRACT
  .md already committed to (its own decision b') is MORE natural outside
  the Python workaround than inside it, since that's what GameInstance is
  for. Two concrete things DO have to change: the file PATH (`Content/` is
  cooked read-only in a packaged build — needs `FPaths::
  ProjectSavedDir()` or a proper `USaveGame` slot), and the reader/writer
  itself (Blueprint JSON nodes or C++, not Python's `json` module).
- **Proof**: save under the packaged build, quit, relaunch, confirm every
  field `citytick.seed_state()`'s own schema declares — money, demand,
  and each parcel's rid/tier/width/owned/accum/placement — reads back
  identical. The same round-trip self-test 26 (this file) just proved for
  `road_id` specifically, generalized to the whole schema.

### 3.5 HUD runtime construction
BP_LensRig's `EventBeginPlay`.

- **Today**: HANDOFF.md's own finding — real UMG `WidgetTree`
  construction is blocked from Python reflection specifically (a
  protected property), so the only proven-working HUD is
  `SystemLibrary.print_string` debug text.
- **Home**: the one item on this list that isn't really a PACKAGING
  problem at all — it's an artifact of building the HUD FROM Python in
  the first place. A normal UMG Widget Blueprint, authored the ordinary
  way (the UMG designer, bound to Money/Demand/Selection via standard
  Blueprint bindings or a small C++ interface), has no `WidgetTree`
  restriction of any kind — that restriction is specific to Python's
  reflection access, not to Blueprint or C++ authoring it directly. Likely
  the single lowest-risk, highest-leverage item in this whole charter: it
  doesn't require solving a new problem, just doing HUD construction the
  way UMG is normally done instead of the Python workaround this
  session's own history was forced into by condition 1 (HANDOFF.md).
- **Proof**: a real UMG widget on screen showing Money/Demand/current
  selection, driven by the same GameInstance fields the Python HUD reads
  today, with no PrintString calls anywhere in the path. "Does it look
  like a HUD" is a human/PIE judgment call, the same way the ghost pad's
  own feel was — not headlessly provable.

## 3.6 Interim: `-game` exists today — it is not the port

New fact, 2026-09-04, worth this document's own section because it
touches the schedule this charter is written against, not because it
changes anything section 1-3 concluded. `Tools/play.sh` launches the
UNCOOKED editor binary with `-game` on `TestCity`: the Python plugin
loads (its main module ships as `UncookedOnly` — a real UE module type,
distinct from `Editor`, that loads in uncooked/development targets
including `-game`, but NOT in a cooked/Shipping build), `init_unreal.py`
runs, both drivers register, and the city restores from `Content/
Python/citystate.json` — the owner's real save. The owner can now play
as a standalone user in a second process while lanes keep editing in
the main editor window.

**This does not contradict section 1.** `-game` here is still the full
uncooked engine binary on the same machine with the whole project
checked out — not a packaged/cooked build, nothing a tester could run
without the engine and the source tree. Every conclusion in sections
1-3 (Python is absent from an actual cooked/Shipping build; each
system's home and proof) is unchanged.

**What it DOES change: schedule pressure, not scope.** The owner
playing live, in real time, in a process none of the lanes control,
while headless work continues in the editor is a new fact this
charter's own timeline should account for — work that assumed "the
owner tests when a lane hands off a checkpoint" now has to reckon with
the owner potentially playing continuously, on their own schedule,
against whatever is on disk at launch time (`-game` reads state once,
at startup — it does not hot-reload a lane's later save; the owner
relaunches to see new work, per `play.sh`'s own comment).

**One real risk this surfaces, not yet solved:** the owner's own
EDITOR session is not subject to the lane-isolation rule (that rule is
about lanes never running PIE against the owner's real save — the
owner's own PIE was always the exception, by definition). If the owner
presses Play in the main editor WHILE `Tools/play.sh`'s `-game` process
is also running, and neither has an override set, BOTH processes' own
drivers tick against the SAME `citystate.json` concurrently — a
last-writer-wins race on the owner's real save, not a lane-isolation
question at all. **CLOSED, 2026-09-04**: the standalone game writes
`Saved/standalone.lock` (its own pid) at driver registration;
`_state_path_source` now checks that pid (`os.kill(pid, 0)`, proven
both live and dead headless) and steers an editor PIE to the test file
instead of the real save whenever it's running, logging why on screen.
`Docs/TRADE_ADAPTER.md`'s own ledger-consumption design
has the same shape of risk from a different angle — see its own note,
added the same day this fact was found.

## 4. What this charter deliberately does not decide

- **WHEN to port** — still the owner's call (PLAYABLE_PLAN.md section
  2.7).
- **Whether a C++ module gets stood up for this project at all** — today
  there is none (checked: the `.uproject` shows no `Source/` module
  entry). Choosing C++ for ANY item above is also a decision to add a
  first Source module — a bigger step than the per-item choice it looks
  like on this page, and worth the owner seeing named as its own decision
  rather than bundled silently into "port placement.py."
- **The cooked-Python escape hatch** named in section 1 — genuinely
  unverified, not ruled out, just not assumed.

## 5. One honest caveat about this whole document

Nothing here has been measured against an actual packaged build — no
packaging pass has been run this session, headless throughout by the
coordinator's own instruction. Every "home" recommendation above is
architectural reasoning from this project's own code and its own Config
files, the same discipline as the rest of this session's work, but the
proof column for each item is a real, not-yet-run test. This document is
what the owner would be deciding to schedule, not a report that any of it
already works.
