# Stacktown disk audit — 2026-08-24

Figures below are allocated disk usage from `du -sk`; GiB and MiB are binary
units. The protected projects were inspected read-only except for the bakeoff's
explicitly regenerable Unreal caches.

## Result

**Cumulative net machine reduction: 28,058,196 KiB = 26.758 GiB
(28.732 GB decimal).** The deletions and conversions reclaimed 28,058,220 KiB;
the written audit and mined artifact copies add back 24 KiB.

The first pass accounted for 5.606 GiB net. The owner-approved deletion and
Unity-uninstall follow-up added 21,537,820 KiB (20.540 GiB) of gross reclaim.

An additional **124,036 KiB = 121.13 MiB** of regenerable cache remains in
StacktownAlpha because its Unreal editor was running during this pass. It was
not safe to disturb live editor state for that small remainder.

## Immediate reclaim

| Target | Before | After | Freed |
|---|---:|---:|---:|
| PortlandGate1 `DerivedDataCache` + `Intermediate` | 123,224 KiB | 0 | 123,224 KiB |
| StacktownHeroRescue `DerivedDataCache` + `Intermediate` | 123,324 KiB | 0 | 123,324 KiB |
| StacktownVisualBakeoffUE root/plugin `DerivedDataCache` + `Intermediate` | 2,413,020 KiB | 0 | 2,413,020 KiB |
| StacktownAlpha `Saved/Screenshots` | 2,658,080 KiB | 0 | 2,658,080 KiB |
| **Immediate-reclaim subtotal** | **5,317,648 KiB** | **0** | **5,317,648 KiB (5.071 GiB)** |

The deleted cache directories are engine-regenerable. `Saved/Screenshots` was
permanently removed rather than moved to Trash, so those raw captures are not
locally recoverable; their recorded evidence remains in `Saved/Stage0..3` and
the repository's curated evidence.

## Archived evidence downsampling

Forty-two PNGs were converted to JPEG at quality 82 with a 1400 px maximum
edge, validated for dimensions/nonzero output, and spot-checked visually before
their PNG sources were removed. The converted image payload went from
586,004,765 bytes (558.86 MiB) to 11,327,502 bytes (10.80 MiB), a 98.1% reduction.

| Archive | Before | After | Freed |
|---|---:|---:|---:|
| `Saved/Stage0` | 42,848 KiB | 37,840 KiB | 5,008 KiB |
| `Saved/Stage1` | 680,476 KiB | 237,660 KiB | 442,816 KiB |
| `Saved/Stage2` | 122,720 KiB | 18,172 KiB | 104,548 KiB |
| `Saved/Stage3` | 15,388 KiB | 6,560 KiB | 8,828 KiB |
| **Archive subtotal** | **861,432 KiB** | **300,232 KiB** | **561,200 KiB (548.05 MiB)** |

Nineteen lossless originals remain because the records depend on exact source
pixels, full-resolution feature measurement, or lossless before/after analysis:

- Stage 0: `phase3_bayA_75mm.png`, `phase3_bayB_150mm.png`,
  `phase3_bayC_250mm.png`, `phase3_recess_compare.png`,
  `phase4_bevel_before_after.png`, `phase4_hero_beveled.png`,
  `stage0_hero_70mm.png`, and `stage0_angle_70mm.png`.
- Stage 1: `T_PaperDetail.png`, `T_PaperNormal.png`,
  `seam_grid_diagnostic.png`, `hero_seams_v2.png`, and
  `closeup_9m_seams_v2.png`.
- Stage 2: `bake_vs_components.png`, `block_player_zoom.png`,
  `block_player_zoom_chamfered.png`, and `block_zoom_paper.png`.
- Stage 3: `end_wall_triplanar.png` and `facade_triplanar.png`.

## Bakeoff archaeology

The bakeoff's `.claude/skills/stacktown-pcg-city-grammar/SKILL.md` was only a
broken symlink; its target had already disappeared. The exact skill and metadata
were recovered from `~/Documents/Codex/Stacktown_Codex_Handoff_2026-08-22.zip`,
hash-verified, and archived inactive at
`Docs/LegacyBakeoff/stacktown-pcg-city-grammar/`. PCG was not enabled and the
skill was not installed as an active project skill.

Two other reusable text records were copied to `Docs/LegacyBakeoff/`:

- `FREE_ASSET_INTAKE.md`: verified Fab candidates, URLs, license/storage rules,
  and acquisition status.
- `PRODUCTION_PASS_01.md`: the PCG asset-zoo proof, grammar layering, and the
  specific Epic asset-grid graph used.

The old Portland visual-gate skill was not copied because the active miniature
gate and studio-direction skill supersede it. Map-bound build/capture scripts,
generated scenes, the auto-Fab C++ module, and the donor content were not copied;
`Docs/PROVENANCE.md` explicitly records why they are rejected, non-portable, or
locally re-downloadable. The bakeoff's dirty and untracked files were not edited.

## Owner-approved deletion and Unity uninstall

| Target | Before | After | Freed |
|---|---:|---:|---:|
| `~/Documents/Codex/StacktownUSA` | 8,957,500 KiB (8.543 GiB) | 0 | 8,957,500 KiB |
| `~/Documents/Codex/StacktownVisualBakeoffUE` | 6,103,564 KiB (5.821 GiB) | 0 | 6,103,564 KiB |
| Unity CLI, Hub state, Asset Store cache, editor caches, licenses, preferences, and logs | 6,476,756 KiB (6.177 GiB) | 0 | 6,476,756 KiB |
| **Follow-up subtotal** | **21,537,820 KiB** | **0** | **21,537,820 KiB (20.540 GiB)** |

Both abandoned projects were permanently removed rather than moved to Trash.
The Unity application/Editor was already absent from the documented macOS Hub
installation path. Verification after cleanup found no Unity app, editor, Hub,
CLI command, process, Homebrew cask, package receipt, launch service, shell-path
entry, user Library support path, or system Library support path.

The previously mined bakeoff artifacts remain under `Docs/LegacyBakeoff/`.

## Quarantine removal

`~/Documents/Codex/StacktownUSA_Quarantine` was not a complete runnable project.
Its own August 21 reset README identifies it as files deliberately removed from
the active Unity project after a visual-production reset, with a warning not to
restore it wholesale.

- `Assets/vrbn_studios`: 10,403,688 KiB, the rejected building bundle.
- `Packages`: 609,524 KiB, chiefly the Cesium Unity package.
- Remaining material: older low-poly city/vehicle packs, nine experimental
  Stacktown scenes, two recovery scenes, project scripts, and one reference PNG.

The quarantine's original inventory was 11,045,232 KiB (10.534 GiB). After the
Unity Asset Store/cache cleanup it measured 641,552 KiB (626.52 MiB) immediately
before final removal. That final figure is used for the incremental total above
to avoid double-counting storage already reclaimed with Unity's support data.

| Target | Original inventory | At final removal | After | Incremental freed |
|---|---:|---:|---:|---:|
| `~/Documents/Codex/StacktownUSA_Quarantine` | 11,045,232 KiB | 641,552 KiB | 0 | 641,552 KiB (0.612 GiB) |

## Remaining pre-authorized cache

| Target | Before | After | Reason retained |
|---|---:|---:|---|
| StacktownAlpha `DerivedDataCache` + `Intermediate` | 124,036 KiB | 124,036 KiB | UnrealEditor was open on `StacktownAlpha.uproject`; delete after a safe editor shutdown. |
