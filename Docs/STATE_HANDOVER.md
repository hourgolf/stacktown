# State handover: from the Python economy to the C++ economy

Written 2026-09-06 by the coordinator so step 3 (the parcel actor) can hook
up to UStacktownEconomy without creating a second writer of the city state.
The seat's own rule stands and is the spine of this contract: the C++
economy writes NOTHING until its StatePath is set explicitly.

## The files

| writer | file | when |
|---|---|---|
| Python driver (init_unreal.py) | Content/Python/citystate.json (owner) or citystate_test.json (lanes; marker / override / standalone lock decide) | today, until Phase B |
| C++ economy (UStacktownEconomy) | Saved/Stacktown/citystate.json, or Saved/Stacktown/citystate_test.json under the same lane rules | from Phase B |

Never both at once. Content/Python is UncookedOnly and cannot ship; the
Saved/Stacktown path is the one a packaged app can write.

## Phase A: C++ mirrors, Python owns (now, through step 3 and step 4)

- The Python driver keeps ticking, buying, upgrading, repairing, writing.
- The C++ economy MIRRORS the Python file read-only: every sync it re-reads
  the file the Python side resolved (the same marker / override / lock
  rules, ported as `StatePathForSession()`), parses it with
  CityStateFromJson, and exposes it. It never calls CityTick/CityBuy/...
  on its own and never sets StatePath. The seat adds one method for this:
  `bool MirrorFromFile(const FString& AbsolutePath, FString& OutError)`.
- The parcel actor (step 3) reads its facts (rid, width, tier, owned,
  failed, price, accum) from the mirrored state by its label, the same
  facts the Python sync writes onto the Blueprint today. Proof of step 3
  is that both agree on every standing lot in a live game.
- Verbs still travel the Python channels (BuyRequestPID, the upgrade /
  repair / road request attributes). The HUD model is written by Python.

## Phase B: the switch (after the input port, owner's word)

1. One-time migration: copy the last Python-written file to
   Saved/Stacktown/ (both the owner's and the test file). Ledger the copy.
2. The Python economy and click drivers stop registering in the game
   (a single flag: `[/Script/StacktownAlpha.StacktownRuntime]
   bPythonDrivers=false` in DefaultGame.ini; init_unreal.py reads it and
   returns early). Editor tooling scripts are untouched.
3. The C++ economy sets StatePath from StatePathForSession(), loads,
   ticks at citytick's cadence, and is the only writer.
4. The C++ input port calls CityBuy / CityUpgrade / CityRepair / the
   placement and road verbs directly and writes the HUD model.
5. Same-state proof before the flag flips for the owner: both runtimes
   replay the same recorded verb sequence from the same seed and produce
   the same file (the oracle comparison PLAN §2 promised).

## Phase C: Python out of the game path

Content/Python keeps the tooling and the oracle tests; nothing in it runs
in a game process. The packaged app is the beta.

## Rules that carry over

- Lanes never test on the owner's file; the marker / override / lock rules
  port to C++ verbatim, and a lane's C++ game writes only the test file.
- A reflected write to a Blueprint actor re-runs its construction script;
  the parcel actor in C++ owns its facts as UPROPERTYs so nothing resets.
- econrules.json ships by copying it into Config/ (or a cookable asset) at
  Phase B; until then the C++ economy loads it from Content/Python at
  runtime in the editor only.
