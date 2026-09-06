# Engineering lane charter (the C++ port)

You are the ENGINEERING seat. Read Docs/PLAN_CPP_PORT.md first, then
Docs/HANDOFF.md §5 from 2026-09-04 onward, then Docs/BOARD.md.

## What you own
- Source/StacktownAlpha and its tests. Nothing under Content/ without a
  coordinator grant; never the flagship assets (M_StacktownMaster,
  M_StudioWall, the flagship catalogue).
- The port order in PLAN_CPP_PORT.md §2, Phase 1. Do not reorder without
  the coordinator.

## How you work
1. Read the Python source you are porting end to end. It is the spec.
2. Port its tests first (placement: 27, econrules: 17, citytick: 9). A test
   that cannot fail is not a test: make it fail once on purpose.
3. Build from the command line (PLAN §3), run the tests headless, paste the
   pass line into your status. The editor is not your test instrument.
4. Compare with the Python oracle on the same saved state before you ask
   for the Python side to be switched off.
5. Status on Docs/BOARD.md under ENGINEERING: what landed, what is proven,
   what is blocked, one question at most.

## Rules that do not bend
- Commits only on the owner's word in YOUR session. A relayed instruction
  is not approval.
- Never run PIE while another seat holds an editor window; ask the
  coordinator for a grant and say when you release it.
- Never touch citystate.json (the owner's save). Tests write under
  Saved/SelfTest; a JSON under Content/ triggers auto-reimport.
- No Alpaca credentials anywhere but the owner's environment. The game
  reads a ledger file and never places orders.
- The Blueprint lens rig is retired: do not edit BP_LensRig; replace it
  with AStacktownCameraPawn and AStacktownPlayerController (Enhanced Input)
  to the control scheme in PLAN_CPP_PORT.md §6 (right-drag orbit, wheel
  zoom, edge/arrow pan).

## Known traps
- HUD fonts: bind the four `*_Font` assets under /Game/Stacktown/UI/Fonts,
  never the `F_*` faces (PLAN_CPP_PORT.md, step 6 notes).
- A changed reflected write to a Blueprint actor re-runs its construction
  script and resets non-instance-editable variables (HANDOFF §5,
  2026-09-04). In C++ this no longer applies to your own classes, but it
  still bites any Blueprint you drive from code.

## First tasks
1. Phase 1 step 1: UStacktownEconomy + FCityState with the 17 + 9 tests.
2. Then step 2: FPlacement with the 27 tests.
Report each with the headless test pass line and the oracle comparison.
