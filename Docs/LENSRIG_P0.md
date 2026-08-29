# BP_LensRig — the Impossible Boom, interactive P0

**STATUS: built and machine-verified 2026-08-29. The Blueprint asset is
saved; the placed rig in `Sandbox_Bench` is an UNSAVED level change —
the owner decides whether that level gets saved.** Companion to
`Docs/CAMERA_DESIGN.md`; the demo reel (`Content/Python/p0_reel.py`)
demonstrated the grammar, this pawn makes it flyable.

## How to fly it

Open `Sandbox_Bench`, press **Play** (in viewport), click into the
viewport so it has keyboard focus. You are the boom head.

    A / D        arc around the board (azimuth; constant radius)
    W / S        reach in / out along the arm (proportional - equal
                 feel at every scale)
    R / F        pedestal up / down
    arrow keys   head pan / tilt (aim offset from board centre)
    E            SNAP one stop tighter  (BOARD > BLOCK > STREET >
                 FACADE > MACRO)
    Q            SNAP one stop wider
    Esc          stop playing

The rig opens on the reel's establishing framing: BOARD stop, azimuth
250°, the whole board from the south. Press E four times slowly and you
walk the entire optical ladder down to the macro cornice range.

## What it is

One pawn: `/Game/Stacktown/Runtime/BP_LensRig`. No input assets, no
game mode, no C++ — input is polled (`IsInputKeyDown` /
`WasInputKeyJustPressed`), the camera component is created at runtime
in BeginPlay, and the level just needs one placed instance with
**Auto Possess Player = Player 0** (already set on `LENSRIG_P0`).

Pose is authored in **boom space** — azimuth / reach / height / pan /
tilt — exactly like `boomspace.py`. Input moves *targets*; the pose
*chases* the targets each tick; boom-legal motion falls out by
construction and strafing is unrepresentable, per the design doc.

    steer      targets move (A/D azimuth, W/S reach, R/F height, arrows head)
    snap       E/Q set target focal + standoff + height + tilt from the
               stop ladder (lenskit.py values, baked into BeginPlay)
    chase      currents FInterpTo targets - azimuth via shortest-path
               (NormalizeAxis), arm at speed 4, head at 6, RACK AT 8 -
               the rack outrunning the arm is the snap-zoom feel
    apply      boom space -> world transform + FOV = 2*atan(18/focal)
               (the 36mm back, same optic as cap2/lenskit)

## The one instance property

`BoardCentre` (instance editable) — the point azimuth and reach orbit.
Set to the street span midpoint `(11200, -22750, -128)` on `LENSRIG_P0`.
If the rig ever feels like it orbits the wrong thing, this is why —
measure the new centre, never eyeball it (the reel's first cut aimed an
authored centre at the catalogue shelf).

## Tuning knobs (all in the Blueprint, no restructuring)

- **Chase speeds** (Tick, the FInterpTo `InterpSpeed` pins): arm 4,
  head 6, rack 8. More mass = lower numbers.
- **Steer rates** (Tick, the literals): 30°/s arc, 0.9/s proportional
  reach and pedestal, 20–25°/s head.
- **The ladder** (BeginPlay array literals): focal / standoff / height /
  tilt per stop, currently lenskit.py's table with the reel's heights.

## Verification record

- Compiled clean; graph read back and inspected.
- PIE: pawn spawns, BeginPlay runs, player possession confirmed
  (`get_player_pawn` returns the rig), pose applied at exactly the
  hand-computed BOARD opening — location (4702, -40604, 8872),
  pitch -25, yaw 70, FOV 73.74° = 24 mm. Caught in the same pass:
  `BoardCentre` defaulted to origin until set on the instance.
- NOT yet verified: keypress feel. That is the owner's flight, and the
  point of P0.

## Deliberately absent (P1, per the design doc)

Snap overshoot, AF hunt, focus breathing, iris settle, arm-flex sway,
digital-zoom crunch, foley, focus-as-selection. P0 answers "does the
ladder + boom + cut grammar feel right in the hands"; the breath comes
after the skeleton is approved.
