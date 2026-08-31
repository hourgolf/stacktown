# The archetype-aware gate

**Written 2026-08-27, in the worktree, before any non-street geometry
exists.** Why: the per-model gate encodes "articulated street building" as
its only definition of good. GATE-03 (parts per m² of elevation), GATE-07
(mass behind the front third) and GATE-08 (rear face carries parts) would
all refuse a CORRECT warehouse or barn — an industrial shell is defined by
*not* being an articulated street elevation. A gate that refuses correct
work teaches teams to pass it with `--force`, and a forced gate still stamps
the mesh. The fix, approved by the owner: each rule declares which
archetypes it judges, and each archetype declares what good means for it —
declared **before** the geometry, so the gate never meets a model it has no
opinion about.

Files: `Content/Python/archetypes.py` (new), `Content/Python/modelgate.py`
(wired), `Content/Python/qc.py` (one new constant).

## The registry shape

`archetypes.ARCHETYPES` maps a name to three things:

```python
'industrial': dict(
    good='a working shell: large plain elevations, mass as one honest '
         'volume, openings where work needs them - correct by NOT being '
         'an articulated street front',
    exempt={
        'GATE-07': 'a shed is one volume; articulation behind the front '
                   'third is the street question, not the works question',
        'GATE-08': 'the rear of a depot is a working wall with a door in '
                   'it, not an elevation to dress',
    },
    overrides={
        'GATE-03': dict(DETAIL_MIN=qc.DETAIL_MIN_INDUSTRIAL),
    },
)
```

- **`good`** — one line saying what a correct model of this archetype *is*.
  If it cannot be said in one line, the archetype is not understood yet.
- **`exempt`** — rules that do not judge this archetype, each **with a
  reason**. The reason is printed in the verdict's SKIPPED line;
  `check_declarations` refuses an empty one, because a skip without a
  reason is a rule turned off.
- **`overrides`** — rules judged at a different threshold. The value must
  be a `qc.py` constant (never a literal — two copies of 0.70 is how gates
  drift) and must name a constant the gate module actually reads, or
  `archetypes.patched` raises instead of silently binding a constant
  nothing looks at.

The other half of the ledger lives on the rules: every `@rule` in
`modelgate.py` now carries `judges=(...)`, the archetypes it is entitled to
judge. This is deliberate double entry — *not* the forbidden two-copies-of-
a-threshold: what is written twice is the yes/no applicability matrix, and
`check_declarations` fails the entire gate (rules report nothing) the
moment the two entries disagree. Adding a rule forces a decision about
every archetype; adding an archetype forces a decision about every rule.

The current matrix:

| rule | street | industrial | agricultural-structure |
|---|---|---|---|
| GATE-01 roles | judged | judged | judged |
| GATE-02 materials | judged | judged | judged |
| GATE-03 density | judged @ 0.70 | judged @ `DETAIL_MIN_INDUSTRIAL` | exempt |
| GATE-04 mat count | judged | judged | judged |
| GATE-05 parcel fit | judged | judged | judged |
| GATE-06 auto-rename | judged | judged | judged |
| GATE-07 rear mass | judged | exempt | exempt |
| GATE-08 rear face | judged | exempt | exempt |
| GATE-09 glass/floor | judged | judged | exempt |
| GATE-10 z-fighting | judged | judged | judged |

## The doctrines it enforces

1. **Fail closed.** `spec['archetype']` absent (or `None`) means `street` —
   that is the entire existing catalogue. A *present* unknown name raises
   `UnknownArchetype` from `of_spec`/`judge`/`run`; it never falls through
   to street. Same doctrine as `citygeom.zone_layouts`.
2. **Skips are visible.** An exempted rule contributes an explicit
   `SKIPPED for archetype X: <reason>` entry: printed by `run(verbose=True)`
   and carried in `facts['skipped']`, so the stamp records which rules stood
   aside. This project's worst bug class is checks that silently stop having
   an opinion; a silent archetype skip would be that bug installed on purpose.
3. **Street is byte-identical.** The rule bodies are untouched; overrides
   work by rebinding the gate module's constant for one rule call
   (`archetypes.patched`, restored in a `finally`). For street the judge
   loop reduces exactly to the pre-archetype loop.

## The proof, and its result

Two layers:

- **In-module, runs on every `run()`:** `ARCH-STREET-IDENTICAL` in
  `archetypes.py` replays the pre-archetype loop verbatim (`every rule,
  r['check'](m)`) against `judge(m)` on `_clean()` plus a planted-defect
  model per rule family, asserting `repr`-equal findings and zero skips —
  both with the key absent and with `archetype='street'` spelled. It runs
  in the same self-test phase as the ten rule self-tests; if it (or any
  archetype test) fails, the gate reports nothing, exactly as when a rule
  cannot see its own defect.
- **End-to-end, against the real old file:** `prove_invariant.py`
  (scratchpad) loads the pristine pre-archetype `modelgate.py` under a
  second module name and compares full `run()` results — ok, findings,
  every pristine facts key — over 18 street models. Result on 2026-08-27:
  **INVARIANT HOLDS, 18/18 IDENTICAL**, and the comparator passed its own
  instrument check (it demonstrably sees the difference on an industrial
  spec, so the null result is not a blind diff — HANDOFF §5).

The only additions visible to a street caller: `facts` gains
`archetype: 'street'` and `skipped: []`. `gate_run.py` serializes facts to
JSON unchanged and `stamp.py` reads keys with `.get`, so both tolerate the
new keys; findings and `ok` are untouched.

Known pre-existing condition, preserved deliberately: `modelgate.py`'s
`__main__` footer prints `clean model passes: False` because `_clean()`
carries no `Glass_` parts and `SPEC` has `floors=1`, so GATE-09 fires on
it. That predates this work and byte-identity means keeping it.

## Adding an archetype — declare BEFORE building. This is mandatory.

The whole point of this file is that the definition of good exists before
the first model does. Building geometry for an undeclared archetype gives
you a gate that raises on its name — by design, that is the fail-closed
path working. The steps:

1. In `archetypes.py`, add the entry: `good` (one line), `exempt` with a
   real reason per exempted rule, `overrides` per re-thresholded rule.
2. Any new threshold constant goes in `qc.py`, next to `DETAIL_MIN`,
   commented **PROVISIONAL** until it is measured against real models —
   HANDOFF §5: do not invent a threshold and then judge against it.
   `DETAIL_MIN_INDUSTRIAL = 0.25` is currently exactly such a declared
   intent and must be calibrated against the first real industrial model
   before its bake is judged by it.
3. Add the name to every rule's `judges=` in `modelgate.py` that should
   judge it (`ALL_ARCHES` covers the universal rules automatically once the
   name is added there). `check_declarations` will hold the gate shut until
   the two ledgers agree on every rule.
4. Run `python3 Content/Python/archetypes.py` and
   `python3 Content/Python/modelgate.py` headless. Both must pass before
   any recipe carries the new name.
5. Recipes opt in with `archetype='<name>'` in the spec. Nothing existing
   changes: no key means street.

Adding a **rule** is the mirror image: `judges=` is required (a rule
without it fails `check_declarations`), so the author must decide, rule in
hand, what it means for a warehouse and a barn — not discover it in a
forced gate a month later.

## Integration into the live tree

Do this at a design-session pause point; the editor is serialized and the
owner designs in it. All steps are headless file copies plus `python3` —
no Unreal, no MCP. Worktree paths below are relative to
`.claude/worktrees/agent-a209d7a9d9d459a9e/`.

1. Confirm the base matches: `diff Content/Python/modelgate.py` (live)
   against the pristine copy this work started from — the worktree's
   modelgate was branched from the live file as of 2026-08-27. If the live
   gate has moved since, re-run the invariant proof after merging, not
   before.
2. Copy in, in this order (modelgate imports the other two):
   - `Content/Python/qc.py` (adds `DETAIL_MIN_INDUSTRIAL` only — verify
     with diff that nothing else moved),
   - `Content/Python/archetypes.py` (new file, no collision),
   - `Content/Python/modelgate.py` (wired).
3. Prove, headless, from the live `Content/Python`:
   - `python3 archetypes.py` → six self-tests ok, `all pass: True`;
   - `python3 modelgate.py` → `gate self-tests: 10/10`, footer unchanged;
   - copy the pre-integration live `modelgate.py` aside and run
     `prove_invariant.py` against it → `INVARIANT HOLDS`.
4. Call sites need no change: `gate_run.py` unpacks the same 3-tuple;
   `stamp.py` reads facts by `.get`. The stamp JSON now carries
   `archetype` and `skipped` — that is the intent (a skip that is not in
   the evidence is a silent skip), mention it in HANDOFF when it lands.
5. Docs: move this file to `Docs/ARCHETYPE_GATE.md` in the live tree and
   add one line to `Docs/CATALOGUE_PIPELINE.md` §1 pointing at it.
6. Do not commit any of it without the owner's say — hard stop.

Until integration, the live gate keeps refusing non-street work loudly,
which is safe; nobody may `--force` past it in the meantime — that is the
exact failure mode this registry exists to remove the excuse for.
