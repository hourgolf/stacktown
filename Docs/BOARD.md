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
  STATUS 2026-09-06: Phase 1 step 1 WRITTEN, NOT YET BUILT.
  LANDED (branch claude/engineering-lane-task-1-i3hi7s, uncommitted):
  StacktownEconomyRules.h/.cpp (pure, no UObject - the verbs, the pricing,
  the ledger, FStaticCatalogue); StacktownEconomy.h/.cpp (UStacktownEconomy
  GameInstance subsystem - persistence, Blueprint boundary, econrules.json
  parsing); 17 Stacktown.Economy tests and 10 Stacktown.CityState tests;
  Tools/oracle/ (fixture generator + pre-flight harness + mutation runner).
  PROVEN HERE: the Python oracle runs in this container (econrules 17/17,
  citytick 9/9), and every C++ expectation is GENERATED from it into
  EconOracleFixture.inl rather than transcribed. The ported rules were
  compiled with clang and executed against those expectations - 132 checks,
  0 failures - and 13 of 14 planted mutations turned it red, so the suite
  can fail. NOT PROVEN: anything requiring the engine.
  BLOCKED, unchanged: no Unreal here (Linux container, no UBT/engine
  headers/Automation, unreal-mcp ConnectionRefused), so PLAN section 3's
  headless pass line CANNOT be produced from this seat. The 14th mutation
  (unsorted tick iteration) survives here BY CONSTRUCTION - the pre-flight
  shim maps TMap onto std::map, which is ordered - and only a real UE build
  can catch it. Treat the harness as pre-flight, never as the proof.
  ALSO FOUND, for the coordinator: citytick.py persists to
  Content/Python/citystate.json but PLAN step 1 says the C++ state is
  "FCityState JSON in Saved/". While both sides run those are two files that
  drift the moment both are live, so UStacktownEconomy writes NOTHING until
  its StatePath is set explicitly and never guesses at the owner's save.
  Related: econrules.json lives under Content/Python, which is UncookedOnly
  and cannot ship - a Phase 2 item, flagged not fixed.
  QUESTION: who runs the UE build and pastes the pass line - the coordinator
  on the Mac, or should this seat be moved onto the Mac? Nothing is
  committed; commits need the owner's word in the committing session.
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
