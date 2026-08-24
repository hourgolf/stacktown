---
name: stacktown-miniature-gate
description: Run the one-building miniature acceptance gate — geometric reveal, material and fabrication language, scale, environment, lighting, evidence discipline. Trigger for visual reviews, capture comparison, or any claim that the building is ready.
---

# Stacktown Miniature Gate

`Docs/ONE_BUILDING_GATE.md` is the checklist. This skill is how it gets run honestly.

Use `stacktown-studio-director` for what the look should be. This skill turns that into a
reproducible pass or fail.

## Preconditions

- Read `AGENTS.md` and `Docs/ONE_BUILDING_GATE.md`.
- Confirm no unsaved protected packages.
- Confirm the display is live. A `-NullRHI` run cannot capture and its output is not evidence.
- Record commit state, map, camera transform, focal length, exposure value, resolution, and
  quality settings before capturing.

## Workflow

1. Set the approved camera through the native viewport subsystem. Field of view must be set
   explicitly — the EditorToolset camera transform does not change FOV, which is how the legacy
   project captured a whole pass at 90 degrees by accident.
2. Disable depth of field, bloom, and motion blur. The gate is judged without them.
3. Confirm exposure is fixed, and record its value.
4. Capture deliberately, in Simulate mode or via a composed HighResShot. **Never** through a
   startup hook, a ticker, or any automated trigger.
5. Open the resulting image and look at it.
6. Walk `Docs/ONE_BUILDING_GATE.md` line by line. Record pass or fail per numbered line.
7. Capture a second angle within the intended envelope and re-check section A.
8. Run `Content/Python/stacktown_validation.py` and record the result.
9. Write the scorecard to `Saved/Automation/` alongside the captures.

## Reporting rules

- Report per numbered line. "Mostly passes" is not a result.
- A failed line is reported as failed even when the overall image looks better than last time.
  Improvement is not the gate.
- Never soften a line to fit what was built. The gate was written before the geometry existed
  precisely so it could not be negotiated afterward.
- Never present a build, a clean validation run, a passing test count, or a completed script as
  evidence that the scene looks right.

## Stopping

Stop and report when: any section A line fails, any material slot is unassigned, the capture
contains editor overlay, the display is unavailable, exposure was not fixed, or the gate fails
for a reason not covered by a numbered line — the last of which is the most valuable outcome
and must be escalated rather than worked around.

Do not add a second building, add props, or enable depth of field in response to a failure.
