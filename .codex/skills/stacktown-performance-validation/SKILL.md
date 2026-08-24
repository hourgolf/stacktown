---
name: stacktown-performance-validation
description: Validate Stacktown asset health, editor stability, and Mac performance using repeatable reports and Unreal automation. Trigger before visual promotion, after material or lighting changes, or when investigating slowdowns, crashes, memory, or rendering cost.
---

# Stacktown Performance Validation

## Preconditions

- Read `AGENTS.md` and `Docs/ONE_BUILDING_GATE.md`.
- Preserve dirty assets and maps; use a clean duplicate or a commandlet-safe run.
- Record Mac model, resolution, quality settings, map, camera, and commit state.
- Search native Unreal MCP, EditorToolset, AutomationTestToolset, and existing validation before
  adding instrumentation.

## Workflow

1. Run `Content/Python/stacktown_validation.py` and classify hard failures separately from
   advisories.
2. Use AutomationTestToolset to discover and list tests, then run only the narrow applicable
   filter.
3. Run the smoke workflow without baseline mutation.
4. At the approved camera, collect frame time, draw calls, triangle cost, texture memory,
   shader and material complexity, lighting cost, and actor count.
5. Compare like for like. Change one variable per experiment.
6. Save reports under `Saved/Validation` or `Saved/Automation`, never `Content`.

## Validation checklist

- [ ] Test environment and camera are reproducible.
- [ ] No asset hard failures and no automation errors.
- [ ] Performance evidence covers the target Mac mini at the intended settings.
- [ ] Any bottleneck claim is supported by an Unreal measurement, not an assumption.
- [ ] Approved baselines are unchanged.
- [ ] Regressions have owners or explicit decisions.

## Evidence and stopping

Produce validation and smoke JSON, automation results, capture metadata, and a compact
performance table. Stop for crashes, unavailable authoritative tooling, dirty protected content,
incomparable settings, or a regression that would require changing the approved visual
direction.
