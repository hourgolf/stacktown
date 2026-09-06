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

## Step 3's actor swap: deferred to Phase B, and why

Re-parenting BP_Parcel onto AStacktownParcel today would collide: the
Blueprint's own variables RecipeId (a Name), WidthUU, Tier, Price and Accum
share names with the C++ UPROPERTYs (RecipeId is an FString there), and its
`Owned` displays exactly like the C++ `bOwned`. UE would rename or refuse,
and every graph that reads those variables (ResolveMesh, the tick, the
highlight) would need node-level retargeting - the Blueprint surgery the
whole plan exists to avoid.

So Phase A proves the data path without touching the asset: the agreement
instrument (UStacktownAgreementLibrary::CompareMirrorWithWorld) mirrors the
session file into the C++ economy and compares FactsForLabel with what the
Python sync wrote onto each standing BP_Parcel. Phase B replaces the parcel
rather than re-parenting it: AStacktownParcel grows the mesh resolution
(catalogue lookup) and the highlight swap in C++, a thin Blueprint child with
no variables of its own is created for the pool, and the pool actors in
TestCity are swapped to it in one editor session on the owner's word.

## Two Phase B prerequisites found on 2026-09-06

1. **Resolve the state path when the Python driver does.** The C++ economy
   resolved lazily on first use; the lane marker is gone by then and the
   default is the owner's file. In a game process resolve in
   UStacktownEconomy::Initialize() and cache for the session.
2. **Actor labels are editor-only.** GetActorLabel / GetActorNameOrLabel
   return real labels only in editor builds (UnrealEditor -game included);
   a packaged app strips them, so "identity by label" (Python's pool
   scheme, AStacktownParcel::GetParcelId, the agreement instrument) cannot
   ship. Phase B identities are UPROPERTYs: AStacktownParcel::ParcelId and a
   RoadId on the road actor, set by whoever spawns or claims the actor.
   Runtime-spawned C++ actors keyed by id replace the map pools; the pools
   exist only because Python could not spawn.
