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

    ('tick-pays-unowned-parcels', 'rent accrues on parcels nobody bought',
     'if (!P.bOwned)\n\t\t{\n\t\t\tcontinue;\n\t\t}',
     'if (false)\n\t\t{\n\t\t\tcontinue;\n\t\t}', True, 'rules'),

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
     'const double Clamped = FMath::Max(0.0, FMath::Min(P.Length, P.Along));\n\t\t\tconst double D = P.Along - Clamped;\n\t\t\tDist = FMath::Sqrt(D * D + P.Across * P.Across);',
     'Dist = FMath::Abs(P.Across);', True, 'placement'),

    ('crossing-never-detected', 'a click on shared pavement resolves to one road anyway',
     'return Count > 1;', 'return Count > 2;', True, 'placement'),

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

    ('lot-rect-vertical-uses-the-wrong-axis', 'the corner overlap check stops working',
     'Rect.YMin = Lot.X0;\n\t\tRect.YMax = Lot.X1;',
     'Rect.YMin = Lot.X0 - 10000.0;\n\t\tRect.YMax = Lot.X1 - 10000.0;', True, 'placement'),

    ('pool-cap-off-by-one', 'one lot more than the pool has actors for',
     'if (Placed >= Board.Rules.PoolSize)', 'if (Placed > Board.Rules.PoolSize)', True, 'placement'),

    ('plan-does-not-sort-labels', 'reactivation pairs a pid with an arbitrary slot',
     'SortedLabels.Sort([](const FString& A, const FString& B) { return A < B; });', '',
     True, 'placement'),

    ('lot-road-id-defaults-wrong', 'a legacy lot is read as belonging to the cross street',
     'return Lot.RoadId.IsSet() ? Lot.RoadId.GetValue() : FString(TEXT("arterial"));',
     'return Lot.RoadId.IsSet() ? Lot.RoadId.GetValue() : FString(TEXT("cross"));', True, 'placement'),

    ('in-road-check-ignores-the-segment', 'a click past a road end refuses as in-the-road',
     'if (Proj.Along >= 0.0 && Proj.Along <= Proj.Length && FMath::Abs(Local.Across) < R.RoadHalf)',
     'if (FMath::Abs(Local.Across) < R.RoadHalf)', True, 'placement'),

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
     'const double X0 = Snap(R, WorldCoord - Width / 2.0);',
     'const double X0 = RoadStartOnAxis + Snap(R, Local.Along - Width / 2.0);', True, 'placement'),

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
     'Facts.Price   = Price(R, P->Tier, P->Width);',
     'Facts.Price   = Price(R, 0, P->Width);', True, 'handover'),

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
     'if (RectsOverlap(Mine, RoadRect(R, Road)))', 'if (false)', True, 'placement'),

    ('road-pin-scan-not-mode-gated', 'empty mode still refuses on a dormant pin',
     'if (bPinsActive)\n\t{\n\t\tconst FRoad* Arterial = FindRoad(Roads, Board.PinnedRoadId);',
     'if (true)\n\t{\n\t\tconst FRoad* Arterial = FindRoad(Roads, Board.PinnedRoadId);',
     True, 'placement'),

    ('road-pin-scan-removed', 'a drawn road runs through a standing pinned building',
     'if (RectsOverlap(Mine, LotRect(R, *Arterial, PinLot)))', 'if (false)', True, 'placement'),

    ('road-corridor-full-width', 'a road corridor is measured at twice its half-width',
     'Rect.YMin = Road.StartY - R.RoadHalf;\n\t\tRect.YMax = Road.StartY + R.RoadHalf;',
     'Rect.YMin = Road.StartY - R.RoadHalf * 2.0;\n\t\tRect.YMax = Road.StartY + R.RoadHalf * 2.0;',
     True, 'placement'),

    ('road-ids-start-at-zero', 'the first drawn road is R0, not R1',
     'int32 N = 1;\n\twhile (State.Roads.Contains(', 'int32 N = 0;\n\twhile (State.Roads.Contains(',
     True, 'placement'),

    ('horizontal-gets-the-vertical-convention', 'north and south become west and east',
     'Road.bAxisX = true;\n\t\tRoad.SidePlus = TEXT("north");\n\t\tRoad.SideMinus = TEXT("south");',
     'Road.bAxisX = true;\n\t\tRoad.SidePlus = TEXT("west");\n\t\tRoad.SideMinus = TEXT("east");',
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
