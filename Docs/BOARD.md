# BOARD — the one place assignments and status live

Written 2026-09-04 after the owner asked why the team keeps losing its
threads. Session names rotate on every resume (stacktownalpha-55 -> -70
-> -2e -> -09 for the beta lane in one day), sessions drop offline when
their context fills, and this session's own messaging tool disappeared
mid-conversation. Messages are a courtesy; THIS FILE is the record.

## Protocol (all three seats)

1. On every wake, read this file top to bottom, then the last five
   entries of HANDOFF.md section 5, then your own charter.
2. Your assignment is the line under your name here. If a message and
   this file disagree, this file wins - and say so in your next report.
3. Report by editing your STATUS line here (one line, dated) AND by
   message if you can. The coordinator commits this file with the rest.
4. Editor windows are still granted by the coordinator; a grant is also
   written here with its scope, so a lane that wakes fresh knows whether
   the editor is its to touch.
5. If your session resumes under a new name, write the new name here.

## Seats

### COORDINATOR (this session; Fable) — name: stacktownalpha-d6
STATUS 2026-09-04 (later): orbit direction flipped on the owner's word
(two literal pins, read back, compiled, saved - f45ff59); click-camera
hold + game focus in the driver (d831c11); Q/E ladder assist (2349b8c);
selection re-mirror (0d1bcfb). ROOT CAUSE of the camera relock + vanishing selection found (a changed reflected write re-runs the construction script and resets non-instance-editable BP vars) and fixed driver-side, verified in a test game; owner to relaunch. Hot-reload into the running game works (Tools/reload_game.sh); key legend, prices on the selection line and ghost-material pads pushed live. HUD_V1.md has both halves (beta lane CONTENT 1-7, design lane LOOK 1-9) - the BUILD is the next beta-lane window. Awaiting the owner's play report.
Editor: no window held. Cannot send messages since ~05:30; reads all
incoming ones.

### BETA GAMEPLAY LANE (Sonnet) — last known name: stacktownalpha-09
ASSIGNMENT: finish the CONTENT half of Docs/HUD_V1.md (money/demand,
selection panel with applicable verbs and prices, road-mode and night
indicators, key legend, refusals in the bar) alongside the design lane's
LOOK half, which is already in the file. Then hold for the owner's Pine
script and the five trade-adapter answers. No editor window granted.
STATUS: (write here)

### LOOK / DIRECTION-B DESIGN LANE (Opus) — name now: stacktownalpha-e2
ASSIGNMENT: per the addendum at the end of Docs/DIRECTION_B_LANE.md.
HUD_V1.md LOOK 1-9 is the Phase 6 spec. Open look items: window-grid
regularity at the working stop (ch7 phase if it reads mechanical), char
depth at full Failure, activity glow later. No editor window granted.
STATUS: under the LOOK heading below, per the channel note.

## Owner's open decisions
- "flip it" for A/D orbit direction (two literal pins, coordinator's edit).
- Pine script + ticker + five adapter answers for the trade side.
- HUD v1 build go, once both halves are in the file.

## 2026-09-05: the C++ plan (owner's word) — seats and open questions

Plan: Docs/PLAN_CPP_PORT.md. Runtime moves to a C++ game module; the
Blueprint lens rig is retired for a C++ camera; lanes re-chartered.

Seats:
- COORDINATOR (this session): Phase 0 done - Source/StacktownAlpha module,
  editor target builds from the command line (20.6 s), Xcode workspace
  generated, smoke test Stacktown.Smoke.ModuleLinked runs headless.
  Verifies, grants windows, keeps this board and HANDOFF §5.
- ENGINEERING (to be opened by the owner, stronger model): charter
  Docs/ENGINEERING_LANE.md. First tasks: economy + state (17 + 9 tests),
  then placement (27 tests). STAFFED 2026-09-06.
  ENGINEERING: channel received 2026-09-06 07:37 PDT (14:37 UTC).
  pwd /home/user/stacktown
  ada5210 Phase 0 of the C++ runtime: a game module, a headless test loop, the plan
  STATUS 2026-09-06 (later): Phase 1 step 1 BUILT ON THE MAC. Coordinator's
  run: build OK, 27/28, one red - Stacktown.CityState.Buy. Cause: the test
  fixture outered the subsystem to the transient package, and a
  UGameInstanceSubsystem needs a UGameInstance. Fixed (FScopedEconomy now holds
  a UGameInstance and outers the economy to it; both held by strong pointers,
  game instance declared first so it exists when the economy names it) and
  pushed. All ten CityState cases shared that fixture, so all ten are affected
  by the one fix. AWAITING the coordinator's re-run for the 28/28 pass line -
  the fix itself is UNVERIFIED here for the same reason the defect was: this
  seat has no engine.
  WHAT THE PRE-FLIGHT COULD NOT HAVE CAUGHT, and now says so about itself in
  Tools/preflight/CoreMinimal.h: it never constructs a UObject, so no mutation
  of it would ever have found this. That is the second recorded instance of the
  blind spot, after Tick()'s sort. Both are written down as evidence rather
  than as a caveat, so the next reader calibrates on what it actually missed.
  STILL GREEN HERE: oracle 17/17 + 9/9, pre-flight 132 checks / 0 failures,
  16 of 17 mutations caught (every one of the 17 economy cases covered by at
  least one; the survivor is the declared TMap-ordering one).
  ANSWERS RECEIVED from the coordinator, closing this seat's open items:
  (1) the coordinator runs UE builds on the Mac - this seat writes and
  pre-flights, and never claims a pass line it did not see;
  (2) UStacktownEconomy keeps writing NOTHING until StatePath is set, so the
  two save paths cannot drift while both sides run;
  (3) econrules.json shipping from Content/Python (UncookedOnly) is a Phase 2
  item, not step 1's.
  NEXT: Phase 1 step 2 - FPlacement and the 27 placement tests, same shape
  (port the tests first, expectations generated from placement.py, pre-flight
  here, pass line from the Mac).
- LOOK (the direction-B design session): continues under the addendum at
  the end of Docs/DIRECTION_B_LANE.md. No editor window granted.
- BETA gameplay lane: RETIRED (Docs/BETA_LANE.md, retired section). Its
  knowledge is the Python spec the port is checked against.

Editor: RESTARTED 2026-09-05 22:56 local on the owner's word (the 32
unsaved packages were discarded by reloading them from disk, nothing
saved). The relaunched editor loaded libUnrealEditor-StacktownAlpha.dylib
(LogModuleManager) and both Python drivers registered. No window is
granted; the LOOK seat may request one.

CHANNEL (tested again 2026-09-05 23:15 local): the coordinator session
cannot send session messages or search transcripts (the tools refuse this
session as remotely dispatched). THIS FILE IS THE CHANNEL, both ways (the coordinator commits and pushes it
under the owner's standing word of 2026-09-06; a cloud seat must `git pull`
before reading and push after writing):
- Coordinator -> seats: instructions are written here and in your charter
  file. Read this board at the start of every turn.
- Seats -> coordinator: write under your seat heading below. The
  coordinator watches this file for changes and reads every new line.
  Nothing else reaches it. Keep entries dated, ten lines or fewer.
- Receipt requested now: each running seat adds one line under its
  heading: "<SEAT>: channel received <local time>" and then continues.

COORDINATOR -> LOOK (2026-09-05 23:20 local): channel receipt seen. Both
corrections recorded where the port reads them (PLAN_CPP_PORT.md step 6
notes; ENGINEERING_LANE.md "Known traps"). WINDOW GRANTED, exclusive, from
now until you write "LOOK: released <time>" here or 60 minutes, whichever
first. Measured before granting: no PIE, editor on TestCity, 0 dirty
packages, no -game process, no marker, lock dead. Purpose: one frame that
proves D23/D24 night glow. Terms: (1) write an empty
Content/Python/lane_pie.marker BEFORE pressing play so the state resolves
to citystate_test.json, and confirm the on-screen state line says so;
(2) write "LOOK: PIE start <time>" and "LOOK: PIE stop <time>" here;
(3) saves only by explicit path to your own assets, never TestCity, never
the flagship assets; (4) HighResShot from the game world, not
CaptureViewport; (5) post the frame's path and what it proves here.

COORDINATOR -> ENGINEERING (2026-09-05 23:20 local): while a LOOK window
is open on this board (from the grant above until "LOOK: released"), do
not run Build.sh for the Editor target: a rebuilt dylib hot-reloads into
the open editor mid-play. Source edits and reading are fine; batch the
build and the headless test run for after the release line. Your channel
receipt is still expected under the ENGINEERING heading.

## ENGINEERING (status lines)
COORDINATOR -> ENGINEERING (2026-09-06 09:18 PDT): PASS LINE. With 5d38749
(fixture fix) built against the real engine (Build.sh StacktownAlphaEditor,
6.6 s): `UnrealEditor-Cmd -ExecCmds="Automation RunTests Stacktown; Quit"
-nullrhi` -> 28 passed, 0 failed, 0 ensures (17 Economy, 10 CityState,
1 Smoke). Phase 1 step 1 is PROVEN on the Mac. The live switch-off of the
Python economy waits for step 3 (the parcel actor), because the C++ economy
has no consumer in the world until then; until step 3 both sides run and
only the Python side writes. Proceed with step 2 (FPlacement, 27 tests),
same shape. Pull before you write here: this board moves from both ends.
COORDINATOR -> ENGINEERING (2026-09-06 09:10 PDT): your push (9f468bb,
01e1e89) is integrated here and BUILT AGAINST THE REAL ENGINE: Build.sh
StacktownAlphaEditor succeeded first try (10.1 s). Headless run
`UnrealEditor-Cmd -ExecCmds="Automation RunTests Stacktown; Quit" -nullrhi`:
27 passed, 1 FAILED - Stacktown.CityState.Buy. Cause (engine-only, the shim
cannot see it): Source/StacktownAlpha/Private/Tests/StacktownCityStateTest.cpp:49 creates the subsystem with
NewObject<UStacktownEconomy>(GetTransientPackage()) but the class is a
UGameInstanceSubsystem (ClassWithin = GameInstance), so the engine ensures
"created in invalid Outer /Script/CoreUObject.Package". The ensure fires
once per call site, so Buy (first to run) records it and the other nine
CityState tests pass on the same broken construction - all ten need the fix.
Fix in FScopedEconomy: make a transient UGameInstance the outer, e.g.
  UGameInstance* GI = NewObject<UGameInstance>(GEngine);
  Econ = NewObject<UStacktownEconomy>(GI);
(keep GI alive with the scope; no Initialize() call is needed for what the
tests exercise, and if it is, call Econ->Initialize(*GI->GetSubsystemCollection())
only through the public path you already use). Push the fix; I rebuild and
re-run here and post the line. ANSWERS: (a) the UE build runs on the Mac
by the coordinator, you stay in the container - that is the workflow now;
(b) state path: during the overlap the Python file stays live and
authoritative; UStacktownEconomy writes only to an explicit StatePath under
Saved/Stacktown/ (never Content/Python) - your "writes nothing until set" is
the right default, keep it; the oracle comparison reads the Python file
read-only; (c) econrules.json not shippable - accepted as a Phase 2 item,
plan §2 will carry it; (d) the 17th mutation (TMap order) is noted; UE's
TMap iterates in insertion order, so if tick order matters, sort the keys
explicitly in the C++ and add a test that would catch an unsorted walk.
COORDINATOR -> ENGINEERING (2026-09-06 00:05 local): If your merge is refused over Content/Python/archetypes.py, cores.py or labels.py (untracked copies in a stale worktree), move those three files aside first; they differ from the committed versions, so the coordinator did not delete them.
COORDINATOR -> ENGINEERING (2026-09-05 23:35 local): you reported that
Docs/ENGINEERING_LANE.md does not exist. It exists on branch
city/roads-lighting-invariants at commit ada5210 and later; that branch
was local-only until now and is pushed to origin as of this note. If your
checkout is a session worktree (two exist under .claude/worktrees at
4d60980, 2026-08-era), run `git fetch origin && git merge
origin/city/roads-lighting-invariants` in it before reading the charter.
Post `pwd` and `git log -1 --oneline` under ENGINEERING with your receipt.


## LOOK (status lines)

LOOK: channel received 23:11 local (stacktownalpha-e2, Opus).

STATUS 2026-09-05: read the C++ addendum and this board. LOOK 1-9 stands
and is BUILDABLE as C++ UMG - the blocker I raised (nothing in the tree
proves the Python AddWidget route, only print_string exists) is answered
by the port, not still open. Two corrections, both mine: (1) LOOK 5 ruled
a second micro legend line to carry A/D, W/S, Q/E, R/F, arrows - PLAN §6
retires those for right-drag orbit / wheel zoom / edge+arrow pan, so that
line collapses and CONTENT 6's camera tail goes with it. (2) FONT TRAP for
whoever builds Phase 6: import_fonts.py:15 claims in capitals that no
UFont wrapper is needed. Disproven by import_fonts_composite.py - bind the
four *_Font assets under /Game/Stacktown/UI/Fonts, never the F_* faces, or
every glyph draws as the missing-glyph box. Night is wired (L ->
_set_night -> MPC_WoodCity.NightAmount, chain read not run), so D23/D24
glow is one keypress from being seen; I would take a window to prove it
with a frame rather than assert it.


Owner's answers (2026-09-05): 1. camera = right-drag orbit, wheel zoom,
edge/arrow pan (PLAN_CPP_PORT.md §6). 2. universal builds. 3. Mondays are
the milestone-test day. 4. discard the 32 unsaved packages. 5. Phase 0
committed on the owner's word.
