# STACKTOWN ALPHA — Claude Code Entry Point

`AGENTS.md` is the authoritative development contract. Read it before doing anything.
`Docs/ONE_BUILDING_GATE.md` is the acceptance gate and defines what "done" means here.

This file adds **only** Claude-specific mechanics. It deliberately does not restate the rules.
Where this file appears to disagree with `AGENTS.md`, `AGENTS.md` wins and this file is the
bug — report it rather than following it.

## Read order

1. `AGENTS.md` — scope, safety, naming, responsibilities, prohibited actions.
2. `Docs/ONE_BUILDING_GATE.md` — the checklist this project is judged against.
3. `Docs/MASTER_MATERIAL_SPEC.md` — the material role vocabulary and why it exists.
4. The task-relevant skill in `.claude/skills/`.
5. `Docs/PROVENANCE.md` — what was inherited, what was deliberately left behind, and where
   the legacy repository is if you need to look something up.

## Tooling

- **Editor bridge:** the `unreal-mcp` server (native Epic Unreal MCP, UE 5.8), declared in
  `.mcp.json` at `http://127.0.0.1:8000/mcp`. Only authoritative bridge to editor state.
  Same server name as `.codex/config.toml`, intentionally.
- **Discover before building:** `list_toolsets` → `describe_toolset` → `call_tool`. Search the
  Toolset Registry and `Content/Python` before writing a new editor utility.
- **Enabled toolsets are deliberately narrow:** `EditorToolset`, `AutomationTestToolset`.
  `AllToolsets` is excluded on purpose. PCG is not enabled at all — see `AGENTS.md`.
- **Skills are shared, not copied.** `.claude/skills/*/SKILL.md` are symlinks into
  `.codex/skills/`. Edit the file under `.codex/skills/`. Never replace a symlink with a copy —
  that is how two agents start disagreeing.

## Hard stops

Do not do any of the following without explicit approval in the current conversation:

- edit or save `/Game/Maps/OneBuildingTest` without being asked to — duplicate to a sandbox
- enable PCG, `AllToolsets`, a parallel MCP server, or a C++ module
- purchase, download, or import a paid asset
- build a second building, a block, an intersection, or any city context beyond the gate
- reset, revert, delete, force-push, rewrite history, migrate, or renormalize Git
- commit or push anything
- discard, stash over, or stage past a dirty worktree
- automate a capture that will be presented as visual evidence
- submit a `-NullRHI` run as visual evidence
- claim a visual pass without opening the rendered image and looking at it

## Definition of done

A change is not done until its validation and capture evidence exists under `Saved/`, or the
missing runtime check is explicitly reported as missing. When the gate fails, stop and say so
plainly. Do not add features to route around a failed gate — that is the documented failure
mode that ended both predecessors.

## Known gaps

- No git remote and no off-machine backup. See `Docs/PROVENANCE.md`.
- Git LFS is not installed. `.uasset`/`.umap` will commit as raw blobs until it is.
- Viewport capture needs the live display (HDMI dummy adapter on the headless mini).
