---
name: stacktown-asset-intake
description: Evaluate, normalize, document, and promote third-party or generated assets into Stacktown. Trigger for Fab imports, donor packs, mesh/material cleanup, licensing review, or deciding whether an asset belongs in the one-building slice.
---

# Stacktown Asset Intake

Use `stacktown-studio-director` for art-direction decisions; this skill governs safe intake and
evidence.

## Preconditions

- Read `AGENTS.md` and `Docs/PROVENANCE.md`.
- Inspect Git status and existing asset locations. Do not modify protected maps.
- Confirm provenance and license before promotion. Unknown licensing is a stop condition.
- Work in a duplicate sandbox, never directly in the authored map.
- **The budget is approximately $200 total and the owner approves every purchase.** Evaluate
  candidates with actual meshes in Unreal, never marketing screenshots.

## Workflow

1. Search native Unreal MCP and the Toolset Registry for existing asset inspection and capture
   tools before writing anything new.
2. Inventory the smallest candidate set. Adding an item to a library is not permission to import
   a whole pack — the legacy project carries a 5.73 GB pack that yielded roughly sixteen usable
   objects.
3. Keep donor content separate; normalize accepted assets under
   `Content/Stacktown/Source/<provider>/<asset-id>`.
4. Inspect dimensions, pivot, collision, UVs, material slots, texture sizes, and LOD/Nanite
   policy through MCP and EditorToolset.
5. Use Unreal first for material unification and simple fixes. Use Blender only for mesh repair
   Unreal cannot do cleanly.
6. Run `Content/Python/stacktown_validation.py`; capture the sandbox from a consistent camera.
7. Record source, license, acquisition date, modifications, and the acceptance decision.

## Validation checklist

- [ ] Scale and dimensions agree with the building's storey height and human scale.
- [ ] Pivot supports placement; collision matches intended use.
- [ ] UVs, texel density, material slots, and texture budget are coherent.
- [ ] LOD or Nanite choice is explicit.
- [ ] The asset can join the master material without hiding weak geometry.
- [ ] Detail tier matches the fabrication tier, not the photoreal tier. A scanned Victorian
      street clock next to flat-shaded modern architecture is the failure to avoid.
- [ ] Provenance and license record is complete.
- [ ] Sandbox capture and validation report exist.

## Evidence and stopping

Produce an intake record, validation JSON, and a matched sandbox capture. Stop and escalate for
unknown rights, destructive reimport, protected-map edits, ambiguous scale, a period or detail
mismatch that needs art direction, any request to spend money, or a candidate that cannot pass
without bespoke rebuilding.
