# STACKTOWN ALPHA — Development Rules

## Mission and current gate

STACKTOWN, USA is a believable, interactive handmade miniature city that will eventually
serve as the operating surface for a trading platform. **This repository is not that city.**

This repository exists to answer exactly one question:

> Can a single building be authored in Unreal 5.8 so that it reads as a photographed
> physical scale model?

Nothing else is in scope. Not a block. Not an intersection. Not a district. Not trading UI.
Not multiple city styles. Not open-world traversal. Not PCG.

The gate is written in `Docs/ONE_BUILDING_GATE.md` and it was written **before** anything was
built, deliberately. If the gate passes, this repository's purpose is complete and the next
scope is opened by the owner — not by an agent noticing there is room for a second building.

Use Unreal Engine 5.8. Native Epic Unreal MCP is the authoritative bridge for editor state,
actors, assets, viewport control, captures, and automation. Search the Toolset Registry and
existing project tools before creating a new editor utility.

## Why this project exists at all

Two predecessors failed and left written post-mortems: MONEYVILLE (a React/WebGL financial
city) and the Stacktown Unreal visual bakeoff. Both failed the same way — implementation
breadth outran visual proof, and technical milestones were reported as visual progress.

The specific, evidenced failures inherited from the bakeoff, which this project exists to
avoid repeating:

1. **Every surface was a flat plane.** Windows, storefronts, and facades had no geometric
   reveal — no recess, no sill projection, no parapet cap thickness, no door inset. This,
   not asset quality, is the primary reason nothing read as physical.
2. **Glass had no physicality** — a flat gradient with a glow behind it.
3. **Placeholder geometry shipped in evidence captures** — green spheres for trees, and
   unassigned materials rendering as flat green on roofs and pavement.
4. **Props came from the wrong period and detail tier** — a photoreal Victorian street clock
   against flat-shaded modern architecture.
5. **Everything was captured in a black void**, which reads as a render. A model photographed
   in a lit room reads as a model.
6. **Evidence was auto-generated.** A startup script fired `HighResShot` six seconds after the
   editor opened, so the image the engine decision rested on was an uncomposed viewport grab
   with the editor axis gizmo still visible. **Never automate a capture that will be used as
   visual evidence.**

## Responsibilities

- **Unreal** owns the scene, geometry, materials, lighting, cameras, LOD, validation,
  captures, and runtime behavior.
- **Modeling Mode** is the primary tool for adding geometric reveal. Reveal is authored in
  engine before any external DCC is considered.
- **Python** owns narrow, repeatable editor audits and orchestration. Read-only by default.
  It must never silently save a map or asset.
- **Blueprint** owns designer-facing interaction and small reusable authoring tools.
- **C++** is for measured gaps that nothing above can safely solve. There is no C++ module in
  this project and adding one requires approval.
- **Blender** is an optional normalization station for pivots, UVs, dimensions, collision, and
  mesh repair. It is not where the building gets built.
- **PCG is deferred.** It is not enabled in the `.uproject`. PCG multiplies approved art; there
  is no approved art yet. Enabling it is an approval-gated decision.

Keep reusable workflows in narrow project skills under `.codex/skills/`. Do not grow this file
into a procedural manual.

## Repository conventions

- Maps live in `Content/Maps`; editor Python lives in `Content/Python`; Stacktown-owned content
  lives in `Content/Stacktown`.
- Normalized imports use `Content/Stacktown/Source/<provider>/<asset-id>` when provenance
  applies. Donor packs remain source material, never the authored result.
- Actor prefixes: `CAM_`, `LIGHT_`, `LOOK_`, `STAGE_`, `ART_`, `PROP_`, `DIO_`, `BLD_`.
  Python files and functions use snake_case. Asset names stay PascalCase.
- `/Game/Maps/OneBuildingTest` is the single authored map and is **protected**. Duplicate into
  a clearly named sandbox before experimenting.
- Every user-authored map and asset is protected unless an explicitly named duplicate has been
  designated disposable.

## Visual acceptance

`Docs/ONE_BUILDING_GATE.md` is the authority. It is a checklist, not a judgement call, and it
is not negotiable downward by an agent. Depth of field, bloom, and long-lens framing are
finishing tools evaluated **after** the gate passes with them disabled.

The gate is evaluated at the approved camera and exposure, never an arbitrary editor view.

## Asset acceptance

Before promotion from donor or generated content, record or verify: dimensions and scale,
usable pivot, collision appropriate to use, UV integrity and texel density, intentional
material slots, texture budget, and LOD/Nanite policy. Record provider, asset identifier,
source URL, license, acquisition date, and modifications. Reject unknown provenance or
incompatible licenses.

**Spend nothing without an approved purchase.** The asset budget is approximately $200 total
and the owner approves each purchase. Evaluate candidates using actual meshes in Unreal, never
marketing screenshots.

## Performance and verification

- Measure on the target Mac mini at the intended camera, resolution, and quality settings.
- Use Unreal validation, AutomationTestToolset, viewport captures, and reproducible reports
  under `Saved/`. Never alter an approved baseline during a test run.
- A change is not complete until its validation and capture evidence exists, or the missing
  runtime check is explicitly reported as missing.
- `-NullRHI` command-line runs validate and smoke-test. They **cannot** produce a capture and
  must never be submitted as visual evidence.

## Source control and prohibited actions

Unreal binary assets require Git LFS for future additions — see `Tools/enable_git_lfs.sh`. Do
not hand-merge binaries; duplicate for competing experiments.

Never reset, revert, delete, overwrite, mass-renormalize, migrate history, force-push, or
rewrite Git history. Never commit or push without explicit owner direction. Never make
unattended edits or saves to protected maps. Never enable `AllToolsets`, add a parallel MCP
server, replace native Unreal MCP, or install paid or external services without approval.
Preserve dirty worktree changes and report overlap before editing an existing changed file.

## Reporting

- Inspect the rendered result before reporting any visual claim. Looking at the file is the
  minimum bar, and it is the bar the last two stewards missed.
- Never report a successful build, clean validation, passing test count, or completed script
  as evidence that the scene looks right.
- Stop a milestone when its acceptance gate fails. Do not conceal a failure by adding content.
- Fix ordinary defects autonomously. Ask only consequential product questions.
- Never turn the owner into the regression suite.
