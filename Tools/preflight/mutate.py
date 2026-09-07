"""Mutation check: prove the ported tests can actually fail.

ENGINEERING_LANE.md: "A test that cannot fail is not a test: make it fail once
on purpose." A suite that passes tells you nothing until you have seen it go red
for a defect you planted.

Each mutation is applied to a COPY of the file it targets - the committed source
is never touched - and the pre-flight is rebuilt and run against it. A mutation
that does NOT turn the harness red is reported as SURVIVED, which is a hole in
the suite rather than a pass. Read the table BY TEST, not only by mutation: the
first time that was done here it showed three economy cases catching nothing at
all, and they got mutations of their own.

  python3 Tools/preflight/mutate.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
RUN = os.path.join(HERE, 'run.sh')

PRIVATE = os.path.join(ROOT, 'Source', 'StacktownAlpha', 'Private')
TARGETS = {
    'rules':     (os.path.join(PRIVATE, 'StacktownEconomyRules.cpp'), 'STACKTOWN_RULES_CPP'),
    'placement': (os.path.join(PRIVATE, 'StacktownPlacement.cpp'),    'STACKTOWN_PLACEMENT_CPP'),
    'handover':  (os.path.join(PRIVATE, 'StacktownStateHandover.cpp'), 'STACKTOWN_HANDOVER_CPP'),
}

# (name, what it breaks, find, replace, expected_to_be_caught, target)
MUTATIONS = [
    # ---- the economy (Phase 1 step 1) -------------------------------------
    ('rent-drops-the-tier-offset', 'rent no longer scales with tier',
     'return R.RentPerTier * (Tier + 1) * Demand;',
     'return R.RentPerTier * Tier * Demand;', True, 'rules'),

    ('price-wrong-width-divisor', 'width priced per 10uu instead of per 100uu',
     'return R.PriceBase + R.PricePer100uu * (Width / 100.0) + R.PricePerTier * Tier;',
     'return R.PriceBase + R.PricePer100uu * (Width / 10.0) + R.PricePerTier * Tier;', True, 'rules'),

    ('climb-goes-flat', 'upgrade cost stops climbing with tier',
     'return Tier + 1;\n}\n\ndouble Premium', 'return 1;\n}\n\ndouble Premium', True, 'rules'),

    ('premium-grants-a-discount', 'good performance wrongly discounts the upgrade',
     'return 1.0 + (Penalty > 0.0 ? Penalty : 0.0);',
     'return 1.0 + Penalty;', True, 'rules'),

    ('ladder-off-by-one', 'a lot can climb one rung past the top of its ladder',
     'if (Next >= Tiers)', 'if (Next > Tiers)', True, 'rules'),

    ('buy-does-not-transfer', 'a paid-for parcel is never marked owned',
     'P->bOwned = true;\n\tP->Accum = 0.0;', 'P->Accum = 0.0;', True, 'rules'),

    # REFRESHED 2026-09-06: the coordinator's demand pass added a ++ForSale
    # count before this continue, so the old pattern stopped matching.
    ('tick-pays-unowned-parcels', 'rent accrues on parcels nobody bought',
     'if (!P.bOwned)\n\t\t{\n\t\t\t++ForSale;\n\t\t\tcontinue;\n\t\t}',
     'if (false)\n\t\t{\n\t\t\t++ForSale;\n\t\t\tcontinue;\n\t\t}', True, 'rules'),

    ('growth-un-retires', 'a tick advances a tier again, the retired behaviour',
     'P.Accum += Earned;',
     'P.Accum += Earned;\n\t\tif (P.Accum > R.GrowthThreshold) { P.Tier += 1; }', True, 'rules'),

    ('ledger-recounts-from-zero', 'replaying a ledger double-counts every trade',
     'TradeCountReward(Processed, NewCount, R.TradeCreditsPerN, R.TradeCreditAmount)',
     'TradeCountReward(0, LedgerPnls.Num(), R.TradeCreditsPerN, R.TradeCreditAmount)', True, 'rules'),

    ('ledger-loses-idempotency', 'the already-processed prefix is re-read',
     'const int32 Processed = State.TradesProcessed;',
     'const int32 Processed = 0;', True, 'rules'),

    ('refusal-string-drift', 'a refusal reason stops saying what it used to',
     'return FVerbResult::No(TEXT("not failed"));',
     'return FVerbResult::No(TEXT("not broken"));', True, 'rules'),

    ('blocked-growth-loses-the-asset-name', 'the refusal no longer names the missing mesh',
     'FString::Printf(TEXT("GROWTH BLOCKED: %s not baked"),\n\t\t\t*Catalogue.AssetName(Rid, Next, Width))',
     'FString::Printf(TEXT("GROWTH BLOCKED: a mesh is not baked"))', True, 'rules'),

    ('is-win-counts-breakeven', 'a scratch trade farms a bonus',
     'return Pnl > 0.0;', 'return Pnl >= 0.0;', True, 'rules'),

    ('asset-name-grammar-drift', 'the baked-mesh name stops matching recipes.asset_name',
     'return FString::Printf(TEXT("SM_Bld_%s_t%d_w%d"), *Rid, Tier,',
     'return FString::Printf(TEXT("SM_%s_t%d_w%d"), *Rid, Tier,', True, 'rules'),

    ('repair-never-clears-the-flag', 'a paid-for repair leaves the lot still failed',
     'State.Money -= Cost;\n\tP->bFailed = false;', 'State.Money -= Cost;', True, 'rules'),

    ('outcome-bonus-double-pays', 'every winning trade pays twice the declared bonus',
     'Total += BonusPerWin;', 'Total += BonusPerWin * 2.0;', True, 'rules'),

    # ---- placement (Phase 1 step 2) ----------------------------------------
    ('snap-truncates-instead-of-rounding', 'lot spans land on the wrong quantum',
     'return FMath::RoundHalfToEven(Value / R.PositionQuantum) * R.PositionQuantum;',
     'return double(int64(Value / R.PositionQuantum)) * R.PositionQuantum;', True, 'placement'),

    ('normal-rotated-the-wrong-way', 'every side flips: north reads as south',
     'const double Nx = -Uy;\n\tconst double Ny = Ux;',
     'const double Nx = Uy;\n\tconst double Ny = -Ux;', True, 'placement'),

    ('point-to-infinite-line', 'a click far past a road end claims frontage on it',
     # REFRESHED 2026-09-06: the clamp moved into RoadDistance when road types
     # gave the no-frontage explanation a second caller for the same measurement.
     'const double Clamped = FMath::Max(0.0, FMath::Min(OutProj.Length, OutProj.Along));\n\tconst double D = OutProj.Along - Clamped;\n\treturn FMath::Sqrt(D * D + OutProj.Across * OutProj.Across);',
     'return FMath::Abs(OutProj.Across);', True, 'placement'),

    ('crossing-never-detected', 'a click on shared pavement resolves to one road anyway',
     # REFRESHED 2026-09-06: item 11 again - InCrossing counts paths now.
     'return Seen.Num() > 1;', 'return Seen.Num() > 2;', True, 'placement'),

    ('pins-ignore-the-mode-gate', 'empty mode still refuses on a dormant pin',
     'if (bPinsActive && Road->Id == Board.PinnedRoadId)',
     'if (Road->Id == Board.PinnedRoadId)', True, 'placement'),

    # DECLARED SURVIVOR. The side check is correct and necessary, and no test can
    # currently reach it: the pin table's north and south spans are partitioned
    # differently but cover the IDENTICAL union (checked - zero x values on the
    # whole plate where north and south coverage differ), so no click exists that
    # a north pin would refuse and a south pin would not. It goes live the moment
    # a board has asymmetric pins. Left in the code, not deleted.
    ('pinned-scan-ignores-side', 'a north pin refuses a south click',
     'if (Pin.Side != Local.Side)\n\t\t\t{\n\t\t\t\tcontinue;\n\t\t\t}',
     'if (false)\n\t\t\t{\n\t\t\t\tcontinue;\n\t\t\t}', False, 'placement'),

    ('lot-span-shifted', 'the corner overlap check stops working',
     # REFRESHED 2026-09-06: item 11 moved the geometry into quads.
     'return BandQuad(F, Lot.X0, Lot.X1, Sign * Near, Sign * Far);',
     'return BandQuad(F, Lot.X0 - 10000.0, Lot.X1 - 10000.0, Sign * Near, Sign * Far);',
     True, 'placement'),

    ('pool-cap-off-by-one', 'one lot more than the pool has actors for',
     'if (Placed >= Board.Rules.PoolSize)', 'if (Placed > Board.Rules.PoolSize)', True, 'placement'),

    ('plan-does-not-sort-labels', 'reactivation pairs a pid with an arbitrary slot',
     'SortedLabels.Sort([](const FString& A, const FString& B) { return A < B; });', '',
     True, 'placement'),

    ('lot-road-id-defaults-wrong', 'a legacy lot is read as belonging to the cross street',
     'return Lot.RoadId.IsSet() ? Lot.RoadId.GetValue() : FString(TEXT("arterial"));',
     'return Lot.RoadId.IsSet() ? Lot.RoadId.GetValue() : FString(TEXT("cross"));', True, 'placement'),

    ('in-road-check-ignores-the-segment', 'a click past a road end refuses as in-the-road',
     # REFRESHED 2026-09-06: the corridor half became the road's own.
     'if (Proj.Along >= 0.0 && Proj.Along <= Proj.Length && FMath::Abs(Local.Across) < Half)',
     'if (FMath::Abs(Local.Across) < Half)', True, 'placement'),

    # CAUGHT, but only once Placement.Snap existed - and for a different reason
    # than placement.py gives. Its docstring justifies converting to world space
    # before snapping with "neither PLATE_X_MIN nor PLATE_Y_MIN is a multiple of
    # WIDTH_QUANTUM". That was true of WIDTH_QUANTUM (410), but the snap became
    # POSITION_QUANTUM (10) on 2026-09-03 and the rationale was never updated:
    # both plate minima ARE multiples of 10. The ordering still matters, because
    # round() is half-to-EVEN and which way a tie breaks depends on the PARITY of
    # the integer part - so Snap(start + t) != start + Snap(t) at a tie even when
    # start is on the grid. The reasoning in the spec is stale; the code is right.
    ('snap-before-world-space', 'the grid shifts at a tie, and on any off-grid road start',
     # REFRESHED 2026-09-06: item 11 again - the span bound is the joined run.
     'const double X0 = Snap(R, Frame.S0 + Local.Along - Width / 2.0);',
     'const double X0 = Frame.S0 + Snap(R, Local.Along - Width / 2.0);', True, 'placement'),

    ('overlap-scan-unsorted', 'a refusal names whichever lot was added first',
     'TArray<FString> Ids;\n\tState.Parcels.GetKeys(Ids);\n\tIds.Sort([](const FString& A, const FString& B) { return A < B; });',
     'TArray<FString> Ids;\n\tState.Parcels.GetKeys(Ids);', True, 'placement'),

    # ---- the state handover (Phase 1 step 3) --------------------------------
    ('default-flips-to-the-test-path', 'the OWNER lands on the test file by default',
     'Out.Path = In.DefaultStatePath;\n\tOut.Source = EStateSource::Default;',
     'Out.Path = In.TestStatePath;\n\tOut.Source = EStateSource::Default;', True, 'handover'),

    ('lock-steers-the-game-process-too', 'a running standalone game is pushed off its own save',
     'if (!In.bIsGameProcess && In.bStandalonePidAlive)',
     'if (In.bStandalonePidAlive)', True, 'handover'),

    ('empty-marker-yields-an-empty-path', 'a touch-created marker selects nothing at all',
     'Out.Path = Trimmed.IsEmpty() ? In.TestStatePath : Trimmed;',
     'Out.Path = Trimmed;', True, 'handover'),

    ('marker-content-not-trimmed', 'a trailing newline becomes part of the path',
     'const FString Trimmed = In.MarkerContent.TrimStartAndEnd();',
     'const FString Trimmed = In.MarkerContent;', True, 'handover'),

    ('pool-prefix-case-insensitive', 'a real parcel named pool_x is skipped as dormant',
     'return Label.StartsWith(TEXT("POOL_"), ESearchCase::CaseSensitive);',
     'return Label.StartsWith(TEXT("POOL_"), ESearchCase::IgnoreCase)\n\t\t|| Label.StartsWith(TEXT("pool_"), ESearchCase::CaseSensitive);', True, 'handover'),

    # Reports found for a label that is absent, WITHOUT dereferencing the null
    # pointer. An earlier version of this mutation flipped the guard itself,
    # which segfaulted the harness - that scores as "caught" on the exit code
    # while no test actually noticed anything, which is not the claim being made.
    ('missing-label-reports-found', 'an unregistered lot shows as an unowned tier-0 one',
     '\t\t// bFound stays false and every other field stays at its default. The\n\t\t// caller must write nothing.\n\t\treturn Facts;',
     '\t\tFacts.bFound = true;\n\t\treturn Facts;', True, 'handover'),

    ('price-not-recomputed-from-tier', 'the price shown stops tracking the tier',
     # REFRESHED 2026-09-06: the coordinator's building-types pass moved this
     # to PriceFor, which takes the recipe's own multiplier as well.
     'Facts.Price   = PriceFor(R, P->Rid, P->Tier, P->Width);',
     'Facts.Price   = PriceFor(R, P->Rid, 0, P->Width);', True, 'handover'),

    # ---- drawn roads (Phase 1 step 4) ---------------------------------------
    ('diagonal-gate-opens', 'a genuinely diagonal gesture becomes a straight road',
     'if (FMath::Abs(Dx) >= 3.0 * FMath::Abs(Dy))', 'if (FMath::Abs(Dx) >= 0.0 * FMath::Abs(Dy))',
     True, 'placement'),

    ('minor-coordinate-from-the-end', 'a near-axis drag tilts to its end point',
     'SX0 = Snap(R, X0); SY0 = Snap(R, Y0); SX1 = Snap(R, X1); SY1 = Snap(R, Y0);',
     'SX0 = Snap(R, X0); SY0 = Snap(R, Y1); SX1 = Snap(R, X1); SY1 = Snap(R, Y1);',
     True, 'placement'),

    ('min-length-not-enforced', 'a road too short to hold a lot is accepted',
     'if (Length < R.V0Width)', 'if (Length < 0.0)', True, 'placement'),

    ('road-off-board-not-checked', 'a drawn road leaves the plate',
     'if (!(Board.PlateXMin <= SX0 && SX0 <= Board.PlateXMax &&',
     'if (false && !(Board.PlateXMin <= SX0 && SX0 <= Board.PlateXMax &&', True, 'placement'),

    ('road-crossing-not-checked', 'a drawn road runs straight over another road',
     # REFRESHED 2026-09-06: item 11 moved the geometry into quads.
     'if (QuadsOverlap(Mine, RoadQuad(R, E, Road)))', 'if (false)', True, 'placement'),

    ('road-pin-scan-not-mode-gated', 'empty mode still refuses on a dormant pin',
     'if (bPinsActive)\n\t{\n\t\tconst FRoad* Arterial = FindRoad(Roads, Board.PinnedRoadId);',
     'if (true)\n\t{\n\t\tconst FRoad* Arterial = FindRoad(Roads, Board.PinnedRoadId);',
     True, 'placement'),

    ('road-pin-scan-removed', 'a drawn road runs through a standing pinned building',
     # REFRESHED 2026-09-06: item 11 moved the geometry into quads.
     'if (QuadsOverlap(Mine, LotQuad(R, E, *Arterial, PinLot)))', 'if (false)', True, 'placement'),

    ('road-corridor-full-width', 'a road corridor is measured at twice its half-width',
     # REFRESHED 2026-09-06: item 11 moved the geometry into quads.
     'return BandQuad(F, F.S0, F.S0 + F.Length, -Half, Half);',
     'return BandQuad(F, F.S0, F.S0 + F.Length, -Half * 2.0, Half * 2.0);',
     True, 'placement'),

    ('road-ids-start-at-zero', 'the first drawn road is R0, not R1',
     'int32 N = 1;\n\twhile (State.Roads.Contains(', 'int32 N = 0;\n\twhile (State.Roads.Contains(',
     True, 'placement'),

    ('horizontal-gets-the-vertical-convention', 'north and south become west and east',
     # REFRESHED 2026-09-06: item 11 moved the geometry into quads.
     'Road.SidePlus  = Ny >= 0.0 ? TEXT("north") : TEXT("south");',
     'Road.SidePlus  = Ny >= 0.0 ? TEXT("west") : TEXT("east");',
     True, 'placement'),

    ('road-ids-sorted-lexicographically', 'R10 is treated as coming before R2',
     'if (bNumA && bNumB)', 'if (false)', True, 'placement'),

    ('drawn-roads-not-offered-to-clicks', 'a lot cannot be placed against a road just drawn',
     'for (const FString& Id : Ids)\n\t{\n\t\tOut.Add(RoadDictFromSegment(Id, State.Roads[Id]));\n\t}',
     '', True, 'placement'),

    ('refused-draw-still-stores', 'a refused road is written into the state anyway',
     'FRoadDrawResult Result = ResolveRoadDraw(Board, State, X0, Y0, X1, Y1, WidthClass, bPinsActive);\n\tif (!Result.bOk)\n\t{\n\t\treturn Result;\n\t}',
     'FRoadDrawResult Result = ResolveRoadDraw(Board, State, X0, Y0, X1, Y1, WidthClass, bPinsActive);',
     True, 'placement'),

    # ---- the runtime board factory (queue item 1) ----------------------------
    ('board-drops-the-pinned-spans', 'the live board has no pins, so pinned ground is buildable',
     'for (int32 i = 0; i < BoardData::PinnedSpansNum; ++i)', 'for (int32 i = 0; i < 0; ++i)',
     True, 'placement'),

    ('board-spans-lose-their-keys', 'a pinned parcel cannot find its own span',
     'S.Key = Row.Key;', 'S.Key = FString();', True, 'placement'),

    ('board-plate-bounds-swapped', 'the plate bounds are mirrored',
     'Board.PlateXMin = BoardData::PlateXMin;\n\tBoard.PlateXMax = BoardData::PlateXMax;',
     'Board.PlateXMin = BoardData::PlateXMax;\n\tBoard.PlateXMax = BoardData::PlateXMin;',
     True, 'placement'),

    ('pinned-placement-always-north', 'every south pin poses on the north frontage',
     'OutPlacement.Side = Span.Side;', 'OutPlacement.Side = FString(TEXT("north"));',
     True, 'placement'),

    ('pinned-placement-wrong-road', 'a pinned lot poses against the cross street',
     'OutPlacement.RoadId = Board.PinnedRoadId;', 'OutPlacement.RoadId = FString(TEXT("cross"));',
     True, 'placement'),

    ('pinned-key-lookup-always-succeeds', 'an unknown label yields a lot at the origin',
     '	}\n\treturn false;\n}\n\nvoid SortRoadIds', '	}\n\treturn true;\n}\n\nvoid SortRoadIds',
     True, 'placement'),

    # ---- age, and the runtime switches (queue items 5 and 7) ----------------
    ('age-counts-on-the-first-advance', 'every building starts a tick old instead of pale',
     'if (!P.AgeLastTier.IsSet() || P.AgeLastTier.GetValue() != P.Tier)',
     'if (P.AgeLastTier.IsSet() && P.AgeLastTier.GetValue() != P.Tier)', True, 'rules'),

    ('age-does-not-reset-on-upgrade', 'an upgraded building keeps its patina',
     'P.AgeTicks = 0.0;\n\t\tP.AgeLastTier = P.Tier;', 'P.AgeLastTier = P.Tier;', True, 'rules'),

    ('unowned-lots-age', 'a lot nobody bought weathers on the shelf',
     'if (!P.bOwned)\n\t{\n\t\t// An unowned lot does not age.',
     'if (false)\n\t{\n\t\t// An unowned lot does not age.', True, 'rules'),

    ('age-does-not-saturate', 'a long-standing lot reads as many times mature',
     'return Fraction < 1.0 ? Fraction : 1.0;', 'return Fraction;', True, 'rules'),

    ('drivers-plugin-check-is-not-first', 'a packaged app is told it still has Python',
     'if (!In.bPluginLoaded)\n\t{\n\t\treturn false;\n\t}', '', True, 'handover'),

    ('drivers-legacy-section-ignored', 'the shipped ini key stops being honoured',
     'if (In.bFoundInLegacySection)\n\t{\n\t\treturn In.bLegacySectionValue;\n\t}', '',
     True, 'handover'),

    ('drivers-default-off', 'a missing key silently switches who owns the session',
     '\t// Default ON: the Python drivers were the world before Phase B, and a\n\t// missing key must not silently switch a session\'s owner.\n\treturn true;',
     '\treturn false;', True, 'handover'),

    # ---- the preset start (night item 12) ------------------------------------
    ('preset-seeds-them-owned', 'a stranger arrives owning the whole city',
     'P.bOwned = false;    // a city to buy into, not one already owned',
     'P.bOwned = true;', True, 'placement'),

    ('preset-seeds-a-tier', 'a bought lot shows its mature building instantly',
     'P.Tier = 0;          // ALWAYS. See FPinnedSpan for why no tier is carried.',
     'P.Tier = 3;', True, 'placement'),

    ('preset-lots-have-no-placement', 'fourteen buildings silently do not appear',
     'P.Placement = Lot;\n\t\tS.Parcels.Add(Span.Key, P);',
     'S.Parcels.Add(Span.Key, P);', True, 'placement'),

    ('preset-uses-the-wrong-width', 'every preset mass is the wrong size for its lot',
     'P.Width = Span.Width;', 'P.Width = Board.Rules.V0Width;', True, 'placement'),

    # ---- the honest negatives ------------------------------------------------
    # DECLARED SURVIVOR, and now for a PROVEN reason rather than a shim artifact.
    # The shim's TMap preserves insertion order (as UE's does), so this mutation
    # really does change the walk order - and the sum still cannot move: rent is
    # RentPerTier * (tier + 1) * Demand, the spread is at most 7x, every value is
    # exactly representable, and all 5040 orderings of the seven possible rents
    # sum to exactly 21.0. Tick()'s sort is DEFENSIVE - correct to keep, and not
    # something any test can prove. The observable ordering case is the overlap
    # scan, covered by Placement.OverlapOrder above.
    ('tick-iteration-order-unsorted', 'parcels summed in map order instead of sorted',
     'OutIds.Sort([](const FString& A, const FString& B) { return A < B; });', '',
     False, 'rules'),
    # ---- road types as mechanics (queue item 10, self-tests 40-48) --------
    ('road-half-verge-once', 'the verge counted once, not per side',
     'return T->Width / 2.0 + R.Verge;',
     'return (T->Width + R.Verge) / 2.0;', True, 'placement'),

    ('road-half-ignores-type', 'every road measured as an avenue',
     'return T->Width / 2.0 + R.Verge;',
     'return R.RoadHalf;', True, 'placement'),

    ('road-max-reach-constant-half', 'reach built on the avenue constant',
     'return RoadHalf(R, E, Road) + R.BlockDepth + R.ReachSlack;',
     'return R.RoadHalf + R.BlockDepth + R.ReachSlack;', True, 'placement'),

    ('road-frontage-always-true', 'the highway stops refusing frontage',
     'return T == nullptr ? true : T->bFrontage;',
     'return true;', True, 'placement'),

    ('resolve-road-offers-no-frontage-roads', 'a lot may front a highway',
     '\t\tif (!RoadHasFrontage(E, Road))\n\t\t{\n\t\t\tcontinue;\n\t\t}\n\t\tFRoadProjection P;\n\t\tconst double Dist = RoadDistance(Road, X, Y, P);',
     '\t\tFRoadProjection P;\n\t\tconst double Dist = RoadDistance(Road, X, Y, P);', True, 'placement'),

    ('resolve-road-reach-filter-dropped', 'the per-road reach bound stops applying',
     '\t\tif (Dist > RoadMaxReach(R, E, Road))\n\t\t{\n\t\t\tcontinue;\n\t\t}\n\t\tif (Best == nullptr || Dist < BestDist)\n\t\t{\n\t\t\tBest = &Road;\n\t\t\tBestDist = Dist;\n\t\t\tBestAlong = P.Along;',
     '\t\tif (Best == nullptr || Dist < BestDist)\n\t\t{\n\t\t\tBest = &Road;\n\t\t\tBestDist = Dist;\n\t\t\tBestAlong = P.Along;', True, 'placement'),

    ('nearest-no-frontage-reach-dropped', "'no frontage' handed out board-wide",
     '\t\tconst double Dist = RoadDistance(Road, X, Y, P);\n\t\tif (Dist > RoadMaxReach(R, E, Road))\n\t\t{\n\t\t\tcontinue;\n\t\t}\n\t\tif (Best == nullptr || Dist < BestDist)\n\t\t{\n\t\t\tBest = &Road;\n\t\t\tBestDist = Dist;\n\t\t}',
     '\t\tconst double Dist = RoadDistance(Road, X, Y, P);\n\t\tif (Best == nullptr || Dist < BestDist)\n\t\t{\n\t\t\tBest = &Road;\n\t\t\tBestDist = Dist;\n\t\t}', True, 'placement'),

    ('no-frontage-explanation-dropped', "the highway click falls back to 'off-board'",
     'if (const FRoad* Near = NearestNoFrontage(R, E, Roads, X, Y))',
     'if (const FRoad* Near = nullptr)', True, 'placement'),

    # RETIRED 2026-09-07: the scan it targeted was scoped to frontage-refusing
    # roads, and the rule is now every road with the lot's own PATH exempt.
    # corridor-scan-frontage-only-again and corridor-scan-own-path-not-exempt
    # below are its successors; the highway case is one instance of what they
    # cover, so this is retired rather than refreshed into a duplicate.

    ('lot-rect-near-is-the-constant', 'the frontage line stops moving with the type',
     'const double Near = RoadHalf(R, E, Road);',
     'const double Near = R.RoadHalf;', True, 'placement'),

    ('road-rect-half-is-the-constant', "a road's footprint stops moving with its type",
     'const double Half = RoadHalf(R, E, Road);',
     'const double Half = R.RoadHalf;', True, 'placement'),

    ('in-crossing-half-is-the-constant', 'shared pavement measured as an avenue',
     'FMath::Abs(P.Across) < RoadHalf(R, E, Road))',
     'FMath::Abs(P.Across) < R.RoadHalf)', True, 'placement'),

    ('in-road-half-is-the-constant', 'the in-the-road refusal measured as an avenue',
     'const double Half = RoadHalf(R, E, *Road);',
     'const double Half = R.RoadHalf;', True, 'placement'),

    ('road-cost-per-10uu', 'roads priced ten times over',
     'OutCost = T->CostPer100uu * RoadLength(Seg) / 100.0;',
     'OutCost = T->CostPer100uu * RoadLength(Seg) / 10.0;', True, 'placement'),

    ('road-length-manhattan', 'length measured along the axes, not the centreline',
     'return FMath::Sqrt(Dx * Dx + Dy * Dy);\n}\n\nbool RoadCost',
     'return FMath::Abs(Dx) + FMath::Abs(Dy) + 1.0;\n}\n\nbool RoadCost', True, 'placement'),

    ('afford-check-dropped', 'a city may draw a road it cannot pay for',
     'if (State.Money < Cost)',
     'if (false)', True, 'placement'),

    ('draw-road-does-not-charge', 'roads are quoted and then given away',
     'State.Money -= Cost;',
     'State.Money -= 0.0;', True, 'placement'),

    ('unknown-type-guard-dropped', 'a typo reaches state as a road',
     'if (!WidthClass.IsEmpty() && E.FindRoadType(WidthClass) == nullptr)',
     'if (false)', True, 'placement'),

    ('rent-mult-ignores-own-road', "a lot's own road stops mattering",
     'double Mult = OwnType == nullptr ? 1.0 : OwnType->RentMult;',
     'double Mult = 1.0;', True, 'placement'),

    ('rent-mult-max-not-product', 'the highway replaces rather than multiplies',
     'Mult *= T->RentMult;',
     'Mult = FMath::Max(Mult, T->RentMult);', True, 'placement'),

    ('rent-reach-widened', 'the highway bonus reaches ten percent further',
     'if (RectDistance(Mine, RoadRect(R, E, Road)) <= E.RoadHighwayReach)',
     'if (RectDistance(Mine, RoadRect(R, E, Road)) <= E.RoadHighwayReach * 1.1)', True, 'placement'),

    ('rent-proximity-from-frontage-roads', 'every road lifts rent, not just the highway',
     '\t\tif (RoadHasFrontage(E, Road))\n\t\t{\n\t\t\tcontinue;\n\t\t}\n\t\tif (RectDistance(Mine, RoadRect(R, E, Road)) <= E.RoadHighwayReach)',
     '\t\tif (false)\n\t\t{\n\t\t\tcontinue;\n\t\t}\n\t\tif (RectDistance(Mine, RoadRect(R, E, Road)) <= E.RoadHighwayReach)', True, 'placement'),

    ('rect-distance-ignores-y', 'proximity measured on one axis only',
     # REFRESHED 2026-09-06: item 11 moved the geometry into quads.
     'const double Dy = FMath::Max(0.0, FMath::Max(A.YMin - B.YMax, B.YMin - A.YMax));\n\treturn FMath::Sqrt(Dx * Dx + Dy * Dy);',
     'const double Dy = 0.0;\n\treturn FMath::Sqrt(Dx * Dx + Dy * Dy);', True, 'placement'),

    ('material-name-drops-the-type', 'every road wears the avenue stain',
     'return FString::Printf(TEXT("MI_road_%s"), *Type);',
     'return FString(TEXT("MI_road_avenue"));', True, 'placement'),

    ('untyped-road-becomes-dirt', 'the built-ins stop being avenues',
     'return Road.WidthClass.IsEmpty() ? FString(DefaultRoadType()) : Road.WidthClass;',
     'return Road.WidthClass.IsEmpty() ? FString(TEXT("dirt")) : Road.WidthClass;', True, 'placement'),

    ('shipped-table-drifts', 'the compiled default no longer matches econrules.json',
     'M.Add(TEXT("dirt"),      FRoadTypeRules{  5.0, 0.75,  900.0, true  });',
     'M.Add(TEXT("dirt"),      FRoadTypeRules{  5.0, 0.75, 1000.0, true  });', True, 'rules'),

    ('drag-direction-not-canonicalized', 'a road drawn right to left mirrors its lots',
     'if (SX1 < SX0 || (SX1 == SX0 && SY1 < SY0))\n\t{\n\t\tSwap(SX0, SX1);\n\t\tSwap(SY0, SY1);\n\t}',
     'if (false)\n\t{\n\t\tSwap(SX0, SX1);\n\t\tSwap(SY0, SY1);\n\t}', True, 'placement'),

    ('drag-direction-always-swapped', 'the ordering runs unconditionally',
     'if (SX1 < SX0 || (SX1 == SX0 && SY1 < SY0))\n\t{\n\t\tSwap(SX0, SX1);\n\t\tSwap(SY0, SY1);\n\t}',
     'if (true)\n\t{\n\t\tSwap(SX0, SX1);\n\t\tSwap(SY0, SY1);\n\t}', True, 'placement'),

    ('drag-direction-x-only', 'a vertical road drawn downward still mirrors',
     'if (SX1 < SX0 || (SX1 == SX0 && SY1 < SY0))',
     'if (SX1 < SX0)', True, 'placement'),

    # ---- roads at any direction (item 11, self-tests 50-55) --------------
    # WAS 'side-names-from-the-run', comparing |Dx| >= |Dy| instead - which is
    # the SAME test (the normal is the direction rotated 90 degrees, so
    # |Ny| = |Ux| and |Nx| = |Uy|), so the mutation was a no-op and its survival
    # said nothing. Swapping the branches is the real defect.
    ('side-name-pairs-swapped', 'a road gets the other axis pair of side names',
     'if (FMath::Abs(Ny) >= FMath::Abs(Nx))',
     'if (FMath::Abs(Ny) < FMath::Abs(Nx))', True, 'placement'),

    ('side-plus-sign-ignored', 'the plus side is always north',
     "Road.SidePlus  = Ny >= 0.0 ? TEXT(\"north\") : TEXT(\"south\");\n\t\tRoad.SideMinus = Ny >= 0.0 ? TEXT(\"south\") : TEXT(\"north\");",
     "Road.SidePlus  = TEXT(\"north\");\n\t\tRoad.SideMinus = TEXT(\"south\");", True, 'placement'),

    ('side-plus-sign-ignored-x', 'the plus side is always east',
     "Road.SidePlus  = Nx >= 0.0 ? TEXT(\"east\") : TEXT(\"west\");\n\t\tRoad.SideMinus = Nx >= 0.0 ? TEXT(\"west\") : TEXT(\"east\");",
     "Road.SidePlus  = TEXT(\"east\");\n\t\tRoad.SideMinus = TEXT(\"west\");", True, 'placement'),

    ('normal-rotated-minus-90', 'the normal is rotated the other way',
     '\tF.Nx = -F.Uy;\n\tF.Ny =  F.Ux;',
     '\tF.Nx =  F.Uy;\n\tF.Ny = -F.Ux;', True, 'placement'),

    ('frame-s0-dropped', 'the projection origin is lost',
     '\tF.S0 = F.Ox * F.Ux + F.Oy * F.Uy;',
     '\tF.S0 = 0.0;', True, 'placement'),

    ('point-at-ignores-the-offset', 'every point lands on the centreline',
     '\tOutX = F.Ox + F.Ux * T + F.Nx * Offset;\n\tOutY = F.Oy + F.Uy * T + F.Ny * Offset;',
     '\tOutX = F.Ox + F.Ux * T;\n\tOutY = F.Oy + F.Uy * T;', True, 'placement'),

    ('quad-corners-figure-eight', 'the pad is wound as a bow-tie, which SAT cannot separate',
     '\tPointAt(F, S1, Off1, Q.X[2], Q.Y[2]);\n\tPointAt(F, S0, Off1, Q.X[3], Q.Y[3]);',
     '\tPointAt(F, S0, Off1, Q.X[2], Q.Y[2]);\n\tPointAt(F, S1, Off1, Q.X[3], Q.Y[3]);', True, 'placement'),

    ('sat-touching-counts-as-overlap', 'two pads that touch are called overlapping',
     'if (AMax <= BMin || BMax <= AMin)',
     'if (AMax < BMin || BMax < AMin)', True, 'placement'),

    ('sat-one-polygon-only', "only one shape's axes are tested",
     'for (int32 P = 0; P < 2; ++P)',
     'for (int32 P = 0; P < 1; ++P)', True, 'placement'),

    ('lot-side-sign-always-plus', 'every lot sits on the plus side',
     'const double Sign = Lot.Side == Road.SidePlus ? 1.0 : -1.0;',
     'const double Sign = 1.0;', True, 'placement'),

    ('lot-quad-near-far-swapped', 'the pad is laid from the block edge inward',
     'return BandQuad(F, Lot.X0, Lot.X1, Sign * Near, Sign * Far);',
     'return BandQuad(F, Lot.X0, Lot.X1, Sign * Far, Sign * Near);', True, 'placement'),

    ('road-quad-half-length', 'a corridor covers half its road',
     'return BandQuad(F, F.S0, F.S0 + F.Length, -Half, Half);',
     'return BandQuad(F, F.S0, F.S0 + F.Length / 2.0, -Half, Half);', True, 'placement'),

    ('click-span-not-projected', 'the span is recovered as a world x again',
     # REFRESHED 2026-09-06: item 11 again - the span bound is the joined run.
     'const double X0 = Snap(R, Frame.S0 + Local.Along - Width / 2.0);',
     'const double X0 = Snap(R, Road->StartX + Local.Along - Width / 2.0);', True, 'placement'),

    ('diagonal-length-manhattan', 'a diagonal is measured along the axes',
     'const double Length = FMath::Sqrt((SX1 - SX0) * (SX1 - SX0) + (SY1 - SY0) * (SY1 - SY0));',
     'const double Length = FMath::Abs(SX1 - SX0) + FMath::Abs(SY1 - SY0);', True, 'placement'),

    ('diagonal-snapped-to-an-axis', 'a diagonal is straightened anyway',
     '\t\tSX0 = Snap(R, X0); SY0 = Snap(R, Y0); SX1 = Snap(R, X1); SY1 = Snap(R, Y1);\n\t}',
     '\t\tSX0 = Snap(R, X0); SY0 = Snap(R, Y0); SX1 = Snap(R, X1); SY1 = Snap(R, Y0);\n\t}', True, 'placement'),

    ('click-lot-scan-uses-boxes', 'the click overlap scan compares bounding boxes',
     'if (QuadsOverlap(Mine, LotQuad(R, E, *OtherRoad, Other)))',
     'if (RectsOverlap(QuadRect(Mine), LotRect(R, E, *OtherRoad, Other)))', True, 'placement'),

    ('no-frontage-scan-uses-boxes', 'the highway scan compares bounding boxes',
     'if (QuadsOverlap(Mine, RoadQuad(R, E, Other)))',
     'if (RectsOverlap(QuadRect(Mine), RoadRect(R, E, Other)))', True, 'placement'),

    ('draw-lot-scan-uses-boxes', 'the road-vs-lot scan compares bounding boxes',
     'if (QuadsOverlap(Mine, LotQuad(R, E, *Road, Lot)))',
     'if (RectsOverlap(QuadRect(Mine), LotRect(R, E, *Road, Lot)))', True, 'placement'),

    ('draw-crossing-scan-uses-boxes', 'the road-vs-road scan compares bounding boxes',
     'if (QuadsOverlap(Mine, RoadQuad(R, E, Road)))',
     'if (RectsOverlap(QuadRect(Mine), RoadRect(R, E, Road)))', True, 'placement'),

    # ---- curved multi-node roads (item 11, self-tests 56-60) -------------
    ('in-crossing-counts-chords', 'every joint of every curve becomes the crossing',
     'Seen.Add(RoadPathId(Road));', 'Seen.Add(Road.Id);', True, 'placement'),

    ('path-id-has-no-fallback', 'a straight road stops being its own path',
     'return Road.Path.IsEmpty() ? Road.Id : Road.Path;',
     'return Road.Path;', True, 'placement'),

    ('path-not-carried-on-the-chord', 'the chords forget which road they are',
     '\tRoad.Path = Seg.Path;', '\tRoad.Path = FString();', True, 'placement'),

    ('catmull-near-end-duplicated', 'the curve leaves its first node the wrong way',
     'Ctrl.Add(FVector2D(2.0 * Nodes[0].X - Nodes[1].X, 2.0 * Nodes[0].Y - Nodes[1].Y));',
     'Ctrl.Add(Nodes[0]);', True, 'placement'),

    ('catmull-far-end-duplicated', 'the curve reaches its last node the wrong way',
     'Ctrl.Add(FVector2D(2.0 * Nodes[Nodes.Num() - 1].X - Nodes[Nodes.Num() - 2].X,\n\t\t2.0 * Nodes[Nodes.Num() - 1].Y - Nodes[Nodes.Num() - 2].Y));',
     'Ctrl.Add(Nodes[Nodes.Num() - 1]);', True, 'placement'),

    ('sampled-in-parameter-space', 'chords stretch round the outside of a bend',
     'while (Carried + (Seg - Pos) >= Spacing)', 'while (false)', True, 'placement'),

    ('last-node-dropped', 'the road stops short of where the player clicked',
     'if (Out[Out.Num() - 1] != Dense[Dense.Num() - 1])\n\t{\n\t\tOut.Add(Dense[Dense.Num() - 1]);\n\t}',
     'if (false)\n\t{\n\t\tOut.Add(Dense[Dense.Num() - 1]);\n\t}', True, 'placement'),

    ('leftover-stub-left-in', 'a 50 uu chord with a 2260 uu corridor',
     'if (FMath::Sqrt((B.X - A.X) * (B.X - A.X) + (B.Y - A.Y) * (B.Y - A.Y)) < Spacing / 2.0)',
     'if (false)', True, 'placement'),

    ('path-vertices-not-snapped', 'the polyline leaves the position grid',
     'const FVector2D Q(Snap(R, P.X), Snap(R, P.Y));',
     'const FVector2D Q(P.X, P.Y);', True, 'placement'),

    ('path-priced-at-half', 'a curve costs half what it is quoted',
     'const double Cost = Type->CostPer100uu * Length / 100.0;',
     'const double Cost = Type->CostPer100uu * Length / 200.0;', True, 'placement'),

    ('path-draw-charges-nothing', 'a curve is quoted and then given away',
     'State.Money -= Type->CostPer100uu * Length / 100.0;',
     'State.Money -= 0.0;', True, 'placement'),

    ('path-min-length-not-checked', 'a curve shorter than one lot is a road',
     'if (Length < R.V0Width)\n\t{\n\t\treturn RefusePath(FString::Printf(\n\t\t\tTEXT("too short:',
     'if (false)\n\t{\n\t\treturn RefusePath(FString::Printf(\n\t\t\tTEXT("too short:', True, 'placement'),

    ('path-plate-check-on-nodes', 'the overshoot past a node goes off the board',
     'for (const FVector2D& P : Pts)\n\t{\n\t\tif (!(Board.PlateXMin <= P.X',
     'for (const FVector2D& P : Nodes)\n\t{\n\t\tif (!(Board.PlateXMin <= P.X', True, 'placement'),

    ('path-lot-scan-dropped', 'a curve is drawn through a standing building',
     'if (QuadsOverlap(Mine, LotQuad(R, E, *LotRoad, Lot)))',
     'if (false)', True, 'placement'),

    ('path-crossing-scan-dropped', 'a curve is drawn over another road',
     'if (QuadsOverlap(Mine, RoadQuad(R, E, Road)))\n\t\t\t{\n\t\t\t\treturn RefusePath(',
     'if (false)\n\t\t\t{\n\t\t\t\treturn RefusePath(', True, 'placement'),

    # The pattern names ResolveRoadPath's OWN guard: CatmullRom has an early
    # out spelled the same way, and mutating that one is a no-op (resampling a
    # two-point polyline gives the same vertices as resampling the straight
    # curve through them), so its survival said nothing.
    ('path-two-nodes-refused', 'a straight draw through the path door is refused',
     'if (Nodes.Num() < 2)\n\t{\n\t\treturn RefusePath(TEXT("a road needs at least two nodes"));',
     'if (Nodes.Num() < 3)\n\t{\n\t\treturn RefusePath(TEXT("a road needs at least two nodes"));',
     True, 'placement'),

    ('path-span-not-widened', 'no lot can front a curve',
     'for (const FRoad& Other : PathNeighbours(Roads, Road))',
     'for (const FRoad& Other : TArray<FRoad>())', True, 'placement'),

    ('path-span-takes-every-chord', 'a span runs round the bend past its own pad',
     '\t\tconst bool bJoined =\n\t\t\t(Other.EndX   == Road.StartX && Other.EndY   == Road.StartY) ||\n\t\t\t(Other.StartX == Road.EndX   && Other.StartY == Road.EndY)   ||\n\t\t\t(Other.StartX == Road.StartX && Other.StartY == Road.StartY) ||\n\t\t\t(Other.EndX   == Road.EndX   && Other.EndY   == Road.EndY);',
     '\t\tconst bool bJoined = true;', True, 'placement'),

    # ---- the frontage-corridor gap closed (self-test 61, 2026-09-07) ------
    ('corridor-scan-frontage-only-again', 'a lot may stand in the arterial again',
     '\t\tif (RoadPathId(Other) == OwnPath)\n\t\t{\n\t\t\tcontinue;\n\t\t}',
     '\t\tif (RoadHasFrontage(E, Other))\n\t\t{\n\t\t\tcontinue;\n\t\t}', True, 'placement'),

    ('corridor-scan-own-path-not-exempt', 'no lot can front a curve',
     '\t\tif (RoadPathId(Other) == OwnPath)\n\t\t{\n\t\t\tcontinue;\n\t\t}',
     '\t\tif (false)\n\t\t{\n\t\t\tcontinue;\n\t\t}', True, 'placement'),

    ('corridor-scan-exempts-by-chord', 'a lot may stand across the chord next to its own',
     'if (RoadPathId(Other) == OwnPath)', 'if (Other.Id == Road->Id)', True, 'placement'),

    ('article-always-a', 'the refusal reads "a avenue"',
     'return (L == TEXT("a") || L == TEXT("e") || L == TEXT("i")\n\t\t|| L == TEXT("o") || L == TEXT("u")) ? TEXT("an") : TEXT("a");',
     'return TEXT("a");', True, 'placement'),

    ('type-order-scrambled', 'the T-key cycle stops matching the decided order',
     'TEXT("dirt"), TEXT("avenue"), TEXT("boulevard"), TEXT("highway") };',
     'TEXT("avenue"), TEXT("dirt"), TEXT("boulevard"), TEXT("highway") };', True, 'rules'),
]


def run_harness(target, path, out_path):
    env = dict(os.environ)
    if target is not None:
        env[TARGETS[target][1]] = path
    r = subprocess.run([RUN, out_path], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def main():
    originals = {k: open(v[0]).read() for k, v in TARGETS.items()}
    tmp = tempfile.mkdtemp(prefix='stacktown-mutate-')
    try:
        code, out = run_harness(None, None, os.path.join(tmp, 'baseline'))
        if code != 0:
            print('BASELINE IS ALREADY RED - fix that before mutating:\n' + out)
            return 1
        print('baseline: %s' % out.strip().splitlines()[-1])
        print()

        caught = survived = 0
        unexpected = []
        by_test = {}
        for name, what, find, repl, expect_caught, target in MUTATIONS:
            original = originals[target]
            if find not in original:
                print('  ??  %-42s PATTERN NOT FOUND (mutation is stale)' % name)
                unexpected.append(name)
                continue
            mutated = os.path.join(tmp, name + '.cpp')
            with open(mutated, 'w') as f:
                f.write(original.replace(find, repl, 1))
            code, out = run_harness(target, mutated, os.path.join(tmp, name))
            was_caught = (code != 0)
            if was_caught:
                caught += 1
                cases = sorted({l.split(']')[0].split('[')[-1]
                                for l in out.splitlines() if l.strip().startswith('FAIL')})
                for c in cases:
                    by_test.setdefault(c, []).append(name)
                print('  ok  %-42s caught by: %s' % (name, ', '.join(cases)))
            else:
                survived += 1
                print('  --  %-42s SURVIVED (%s)' % (name, what))
            if was_caught != expect_caught:
                unexpected.append(name)

        print()
        print('mutations: %d caught, %d survived, %d total'
              % (caught, survived, len(MUTATIONS)))
        print()
        print('BY TEST (a case with no mutation against it is not yet a test):')
        for case in sorted(by_test):
            print('  %-34s %s' % (case, ', '.join(sorted(by_test[case]))))
        if unexpected:
            print()
            print('UNEXPECTED RESULT for: %s' % ', '.join(unexpected))
            return 1
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
