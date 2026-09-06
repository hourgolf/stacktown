# Stacktown: the C++ runtime and the road to a packaged beta

Owner's decisions, 2026-09-05: gameplay moves to a C++ game module; the
Blueprint lens rig is retired in favour of a C++ camera; the coordinator
re-charters the lanes. This is the plan the seats work from. The honest
starting point is in HANDOFF.md §5 (2026-09-05): a prototype whose every
mechanic lives in editor-only Python that cannot cook, roughly 18/100 toward
the declared beta and 10/100 toward a simple building game a stranger could
download. The target tier is Townscaper / Islanders / Dorfromantik scale, with
the handmade-miniature look and the trade-linked economy as the differentiators.

## 1. Why C++

- The Python plugin is UncookedOnly: nothing in Content/Python can ship.
- Blueprint graph surgery through the MCP dropped chains and reset variables
  (see memory: reflected-write-resets-blueprint-vars); C++ with a compile loop
  is where agents are productive and where tests run from the command line.
- The Python drivers are not wasted: they are the specification and the test
  oracle. Every port is checked against them on the same inputs.

Toolchain on the owner's Mac (checked 2026-09-05): Xcode 26.6 inside UE 5.8's
supported range (15.2 to 27.9), Apple M4 Pro, 24 GB, 139 GB free. The engine is
prebuilt; only the game module compiles.

## 2. Phases

### Phase 0 (this week): a C++ project
- Source/StacktownAlpha module, editor target built from the command line,
  the editor and play mode open as before, one smoke automation test runs
  from the command line. Python freezes to bug fixes only.
- Proof: `Stacktown.Smoke.ModuleLinked` passes in UnrealEditor-Cmd; the
  editor opens the project with the module loaded.

### Phase 1 (weeks 1 to 3): port the spec
Order is by testability, headless first:

| Step | Python source (spec + oracle) | C++ home | Proof |
|---|---|---|---|
| 1 | citytick.py, econrules.py (+ econrules.json) | `UStacktownEconomy` (GameInstance subsystem), `FCityState` JSON in Saved/ | 17 + 9 rule tests ported; oracle diff on recorded states |
| 2 | placement.py | `FPlacement` pure functions | 27 placement tests ported |
| 3 | BP_Parcel behaviour + init_unreal sync | `AStacktownParcel` C++ base; BP_Parcel re-parented, keeps ResolveMesh | parcel state round-trips; CPD channels pushed |
| 4 | roads (resolve_road, draw_road, pool) | `AStacktownRoad` + road pool | road tests ported |
| 5 | clickdriver.py + BP_LensRig | `AStacktownCameraPawn`, `AStacktownPlayerController` (Enhanced Input; controls per §6) | play test from a checklist |
| 6 | PrintString HUD + Docs/HUD_V1.md | `UStacktownHUD` (UMG built in C++) | screenshot review by the look seat |

Step 6 notes from the LOOK seat (board, 2026-09-05): bind the four `*_Font`
assets under /Game/Stacktown/UI/Fonts, never the `F_*` faces, or every glyph
draws as the missing-glyph box (import_fonts.py:15 is wrong; proven by
import_fonts_composite.py). LOOK 5's second legend line for the key rig is
retired with the rig; the HUD legend describes the §6 controls.

Rules for every step: the test lands with the port; the Python driver keeps
running until its C++ replacement passes; both are compared on the same saved
state before the Python side is switched off.

### Phase 2 (weeks 4 to 8): make it a game
Goal loop and score, growth over time, twenty building types across the five
species, save and load, the real HUD, sound. Trade adapter: a separate Python
process on the owner's Mac (Alpaca paper) writes a ledger file; the game only
reads the ledger. Keys live in the owner's shell environment only.

### Phase 3 (from about week 6): packaged Mac builds
UAT BuildCookRun produces a real universal .app (Apple Silicon + Intel, owner's word); the owner tests the app, not the editor.
Signing and notarization only when builds go to other people.

## 3. The workflow

- Two active seats: ENGINEERING (the port; Docs/ENGINEERING_LANE.md) and LOOK
  (direction B and flagship; Docs/DIRECTION_B_LANE.md). The coordinator
  verifies, grants editor windows, keeps the ledger and the board.
- Every change carries proof: a test that could have failed, or a measured
  capture. Nothing is written down as verified without one.
- The owner tests milestones only, from a written checklist of five to ten
  items, and replies in the same format (what you did, what you saw).
- Ten-line status on Docs/BOARD.md every working day. Commits on the owner's
  word in the committing session, with one standing exception (owner's word
  2026-09-06): the coordinator commits and pushes board, ledger and plan
  changes under Docs/ without asking, so the board reaches the cloud seat.
- Command-line loops the seats use:

```bash
# build the editor target
"/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh" StacktownAlphaEditor Mac Development -Project="$PWD/StacktownAlpha.uproject" -WaitMutex
```

```bash
# run the Stacktown tests headless
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" "$PWD/StacktownAlpha.uproject" -ExecCmds="Automation RunTests Stacktown; Quit" -unattended -nopause -nullrhi -log -ABSLOG="$PWD/Saved/Logs/tests.log"
```

### Instrument rule: build with the editor CLOSED before any pass line
Found 2026-09-06: with the editor open, Build.sh links a hot-reload library
(libUnrealEditor-StacktownAlpha-000N.dylib) and leaves UnrealEditor.modules
pointing at the previous plain library, so UnrealEditor-Cmd tests the OLD
module and reports the old suite as if it were the new one. A pass line is
only valid when the build ran with no editor process on the project and the
.modules file names the plain library. Tools/reload_game.sh and the LOOK
seat's windows are scheduled around that.

## 4. Scope for the simple building game

One board. Roads. Twenty building types across oak, ash, pine, cherry and
walnut. Growth over time. A goal loop with a score. Save and load. A real HUD.
Sound. Nothing else until those ship.

## 5. What the owner provides

| Item | When |
|---|---|
| Milestone testing from a checklist, 20 to 30 minutes | twice a week from Phase 1 |
| Pine script, ticker, the five adapter answers (Docs/TRADE_ADAPTER.md) | Phase 2 start |
| Alpaca paper keys in the shell environment only | Phase 2 start |
| Fresh lane sessions on the named model when asked | as needed |
| Money: none now; Apple Developer Program only when sharing builds | later |

## 6. Camera specification (owner's word, 2026-09-05)

The C++ camera uses the common city-builder scheme, not the boom-space keys:
- right mouse drag: orbit (yaw around the focus point; pitch clamped so the
  board never flips);
- mouse wheel: zoom toward the cursor, between a close stop and a wide stop
  that keep the miniature framing (LENSRIG_P0.md ladder values are the
  starting numbers: reach 800 to 19000, focal 200 to 24);
- screen-edge and arrow keys: pan the focus point across the board, clamped
  to the board's extent;
- left click: select or place, never moves the camera.
Everything eases (targets plus interpolation), as the rig did. The f/2.8 lock
and the studio framing from Docs/LENSRIG_P0.md stay the look spec.

## 7. Decisions log

- 2026-09-05 owner: C++ runtime. BP_LensRig retired for a C++ camera. Lanes
  re-chartered by the coordinator.
- 2026-09-05 owner: camera = right-drag orbit, wheel zoom, edge/arrow pan
  (§6). Builds = universal (Apple Silicon + Intel). Milestone-test day =
  Monday. The 32 unsaved editor packages = discard. Phase 0 = commit.
- Open questions to the owner are tracked on Docs/BOARD.md.
