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

### DIRECTION-B DESIGN LANE (Opus) — last known name: stacktownalpha-05
ASSIGNMENT: HUD_V1.md LOOK half is done; answer the beta lane's content
questions in the file. Open look items for the owner's eye: window-grid
regularity at the working stop (ch7 phase if it reads mechanical), char
depth at full Failure. No editor window granted.
STATUS: (write here)

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

Session messaging: the send tool reports this coordinator session as
unattended, so relays still go through the owner. Lanes read this board
and their charter files.

Owner's answers (2026-09-05): 1. camera = right-drag orbit, wheel zoom,
edge/arrow pan (PLAN_CPP_PORT.md §6). 2. universal builds. 3. Mondays are
the milestone-test day. 4. discard the 32 unsaved packages. 5. Phase 0
committed on the owner's word.
