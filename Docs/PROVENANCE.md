# Provenance

## Lineage

| Project | What it was | Outcome |
|---|---|---|
| MONEYVILLE | React/WebGL financial city, deployed | Wound down 2026-08-22, handoff letter written |
| StacktownUSA | Unity 6 / URP visual test | Lost the bakeoff; frozen as comparison evidence |
| StacktownVisualBakeoffUE | Unreal 5.8 visual truth test | Failed its visual gate; archived 2026-08-23 |
| **StacktownAlpha** | This repository | One-building depth and material proof |

Legacy Unreal repository: `~/Documents/Codex/StacktownVisualBakeoffUE`
Legacy Unity project: `~/Documents/Codex/StacktownUSA`

Both are **read-only archaeological evidence**. Do not continue work in them, and do not
transplant maps or generated scenes out of them.

## What was carried forward

**Ported as code, unchanged:**
- `Content/Python/stacktown_validation.py` — config-driven, project-relative, ports cleanly
- `Content/Python/stacktown_smoke_test.py` — same
- `Tools/enable_git_lfs.sh`
- `.gitattributes`, `.gitignore`

**Ported as skills:**
- `stacktown-asset-intake`
- `stacktown-performance-validation`

**Ported as ideas, re-authored here:**
- The material role vocabulary → `Docs/MASTER_MATERIAL_SPEC.md`
- Deterministic actor ownership by stable label, fixed seeds, sandbox-before-experimenting,
  never-silently-save → `AGENTS.md`
- The native-MCP-is-authoritative architecture → `AGENTS.md`, `.mcp.json`
- Narrow toolset selection over `AllToolsets` → `.uproject`

## What was deliberately left behind, and why

| Left behind | Why |
|---|---|
| All maps and generated scenes | The letter's own instruction. They failed the gate. |
| `Content/Python/init_unreal.py` | Hardcoded an absolute path and fired `HighResShot` six seconds after every editor start. This is why `Stacktown_Unreal_Bakeoff_Final.png` — the image the engine decision rested on — has the editor axis gizmo in it. Auto-capture of evidence is now prohibited by `AGENTS.md`. |
| `Plugins/StacktownEditorTools` | An 80-line C++ module whose only function is auto-opening Fab three seconds after editor startup. Not worth a compiled module, and the auto-open is a misfeature. |
| `stacktown-pcg-city-grammar` skill | PCG is deferred until approved modules exist. Carrying the skill invites premature use. Retrieve it from the legacy repo when PCG is genuinely opened. |
| `build_portland_hero_corner.py` and the other `build_*` scripts | Bound to the old sandbox map and to assets that failed. The patterns they demonstrate are recorded in `AGENTS.md`; the code is not portable. |
| `normalize_asset_zoo_materials.py` | Map-locked disposable bridge. Its valuable content — the role vocabulary — is in `Docs/MASTER_MATERIAL_SPEC.md`. |
| `Content/Deko_MatrixDemo` (5.73 GB City Street Props) | Yielded roughly sixteen usable objects in the asset zoo, mostly flat planes plus a period-wrong Victorian street clock. Installed locally; re-import selectively if a specific mesh is ever needed. |
| The `AndroidFileServer` block in `DefaultEngine.ini` | Template residue with a stray security token. |
| Legacy auto-exposure workaround | Fixed at the root instead: `ExtendDefaultLuminanceRange=True` and auto-exposure off by policy. |

## Config changes made deliberately, not inherited

- **Auto-exposure is disabled project-wide.** Matched baseline captures cannot be reproducible
  while exposure adapts to scene content. Set exposure explicitly on the PostProcessVolume.
- **PCG plugins are not enabled.** See `AGENTS.md`.
- **Project name is `StacktownAlpha`, not `STACKTOWN-ALPHA`.** Unreal derives module names from
  the project name and hyphens break C++ module naming. The folder matches the project name so
  the two never drift.

## Backup status

**There is no git remote and no off-machine copy.** This is the largest single risk to the
project and it is not a code problem. See the archive runbook for `git bundle`.

## The recipe pipeline (25 Aug 2026)

The sandbox authors **recipes**, not models. `recipes.py` holds them: a style, a
base spec that never changes, and a list of tiers. `bake_catalogue.py` builds
each recipe at each tier far off the board, binds its roles, merges it to a
single `StaticMesh` through GeometryScript, and clears the staging actors.
`grammar.py` answers "what could stand on this parcel" and picks the tier from
how developed the area is. `place_catalogue.py` places the baked meshes.

Two properties this exists to protect:

- **The seed lives in the base, not the tier**, so an upgraded building keeps
  its jitter, colour and roof pitch. It is the same house grown, not a
  different house swapped in.
- **The plot has its own random stream.** Drawing it from the building's stream
  meant a tier change shifted every later draw, so upgrading moved the drive
  and swapped the swing set for a putting green — the opposite of the identity
  the tiers exist for.

Measured: cottage tiers bake to 131 / 176 / 201 source boxes, 6,288 / 8,448 /
9,648 triangles, **7 material slots each**, placed as one component.

## Donor assets available (25 Aug 2026)

Vehicles came from a FAB pack and are baked statics bound to our own 2S card
materials; the Deko shopfront pack supplies awnings, signs, boards and street
furniture the same way - donor GEOMETRY, our materials, their textures never
shipped. The owner has more packs in their FAB library that can be pulled in
the same way when the detailing pass needs them.

The rule that makes this safe is the one already applied twice: take the
SHAPES, bind by role, never inherit the donor's material tier. Every complete
donor object tried in this project has had to be fought back to the diorama;
every donor part used as a part has worked.
