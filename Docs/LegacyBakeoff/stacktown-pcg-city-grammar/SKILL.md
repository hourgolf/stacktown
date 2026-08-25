---
name: stacktown-pcg-city-grammar
description: Design or modify Stacktown PCG rules for repeatable roads, lots, buildings, props, vegetation, and district variation. Trigger for procedural city assembly, PCG regeneration, module contracts, seeds, or scaling beyond the Portland hero block.
---

# Stacktown Pcg City Grammar

PCG assembles approved modules; it must not compensate for rejected assets. Use `stacktown-studio-director` when grammar choices affect the visual target.

## Preconditions

- Read `AGENTS.md` and `PRODUCTION_PASS_01.md`.
- Inspect existing graphs, generators, actor labels, and Toolset Registry entries before creating a tool.
- Work in `/Game/Maps/PortlandAssetZoo_01` or an explicit duplicate sandbox. Never regenerate a protected map unattended.
- Define the module contract: dimensions, pivot, sockets/tags, collision, materials, and allowed variation.

## Workflow

1. Inspect PCG assets/components through native Unreal MCP and PCGToolset.
2. Express one small rule at a time: street/lot subdivision, frontage, building selection, roof/prop dressing, or vegetation.
3. Keep deterministic seeds and separate source modules, grammar assets, and generated output.
4. Regenerate only the designated sandbox component; inspect logs and generated actor bounds/counts.
5. Validate multiple seeds for collisions, gaps, repetition, implausible scale, and broken composition.
6. Capture the asset zoo and intended camera before proposing promotion to the hero slice.

## Validation checklist

- [ ] Inputs meet the module contract and retain provenance.
- [ ] Seed and parameters reproduce the result.
- [ ] Generated content stays in its assigned folder/root.
- [ ] No overlaps, floating/sunken assets, blocked roads, or missing materials.
- [ ] Variation is controlled and visually coherent.
- [ ] Regeneration logs, actor counts, validation report, and captures exist.

## Evidence and stopping

Produce graph/parameter identifiers, seed, before/after counts, logs, and matched captures. Stop for nondeterminism, destructive regeneration, unclear ownership of generated actors, a protected-map target, unacceptable performance, or source assets that fail intake.
