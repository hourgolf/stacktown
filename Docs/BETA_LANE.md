# The beta gameplay lane — charter (staff on Sonnet; owner-worded 2026-08-31)

**Scope: BETA_TWIN_PLAN phases A–E** — the playable slice. Catalogue
pointer (two catalogues behind one swappable table in the runtime
path), parcel selection from the boom (focus-as-selection made real),
the economy tick wired through econrules.py, the buy verb, a minimal
HUD, and PIE play sessions for the owner. NOT in scope: phase F
(direction-B catalogue — its own chartered lane), flagship look work
(the flagship design lane's, currently on break), economy DESIGN
(owner's notes replace the scaffolding numbers when they land).

## Contracts inherited (non-negotiable, all on the record)

1. **econrules.py is the rules engine** — pure module, 7/7 known-answer
   self-test, constants in econrules.json READ FRESH per tick (the
   bytecode-cache trap, HANDOFF §5 — never import-cache the hot
   numbers). Growth-to-unbaked-assets BLOCKS LOUDLY: a block on
   office_t1 is the design working, asserted by self-tests 5–6 and
   flagged independently by the flagship lane.
2. **ANNOUNCE-BEFORE-PLAY**: PIE and baking are mutually exclusive
   (bake preflight hard-refuses). PIE runs in DECLARED BLOCKS with
   expected duration, announced to the coordinator; every block ends
   StopPIE + confirmation.
3. **One writer in the editor; announce before you mutate.** The
   editor is currently free; Sandbox_Bench and TestCity are saved and
   committed; TestCity is the beta's map.
4. **mkactor declares intent** — genbuild.record() for data probes,
   genbuild.live() for real spawns (commit 726be63).
5. **BP work through the Blueprint DSL** (BlueprintTools via
   Tools/measure/ue.py — never raw MCP relay; rm Tools/measure/.mcp_sid
   after any editor restart). BP_LensRig is the camera and the
   selection host; read Docs/LENSRIG_P0.md before touching it.
6. **Every capture**: cap2.set_fov immediately before; measured frames
   follow the capture protocol (dwell + settle criterion,
   POLISH_PROTOCOL); subject-present verified by eye; evidence under
   Saved/.
7. **Commits and anything destructive: the owner's word in YOUR
   session** — a relayed instruction is not approval (the flagship
   lane's precedent, upheld under pressure). Surface, don't assume.
8. **The trap ledger is load-bearing**: HANDOFF §5 and
   POLISH_PROTOCOL's instruments before inventing anything. When a
   fault has a syntactic signature, grep is the detector. One capture
   is one sample. A convenient accessor is not a measurement.

## Opening prompt for the session that staffs this lane

"You are the BETA GAMEPLAY session for Stacktown Alpha, running the
playable-slice lane. Read, in order: AGENTS.md, Docs/BETA_TWIN_PLAN.md,
Docs/BETA_LANE.md (this charter), Docs/LENSRIG_P0.md,
Docs/POLISH_PROTOCOL.md ('Standing instruments' + 'The bake policy'),
and Docs/HANDOFF.md §5 (traps). Your subject is gameplay machinery,
never look: the flagship's gate and canon are not yours to touch, and
direction B has its own lane. The coordinator session holds cross-lane
relay and verification; the owner's word in THIS session governs your
commits, saves, and PIE blocks. Start with phase A — the catalogue
pointer: design the swappable-table mechanism against
BP_BuildingCatalogue and ResolveMesh, prove it with the existing
flagship catalogue before any second catalogue exists, and bring the
owner one working demonstration (a placed parcel resolving through the
pointer) before building further. Announce your first editor window
before taking it."
