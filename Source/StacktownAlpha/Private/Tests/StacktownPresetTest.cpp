// The preset start (night item 12, MONDAY_DECISIONS section 3).
//
//   UnrealEditor-Cmd <uproject> -ExecCmds="Automation RunTests Stacktown.Preset; Quit" \
//     -unattended -nopause -nullrhi -log
//
// A new game offers an empty board OR this: the fourteen pinned lots standing
// as FOR-SALE parcels at their pinned poses. They are ordinary lots - each with
// a placement - so they pose, render and reconcile through the same path a
// player-placed lot does and the city sync needs no case for them.

#include "Misc/AutomationTest.h"
#include "StacktownEconomy.h"   // CityStateToJson / FromJson live here (engine-only fix, 2026-09-06 night)
#include "StacktownPlacementTestCommon.h"
#include "StacktownEconomyTestCommon.h"
#include "StacktownLotTransform.h"

#if WITH_DEV_AUTOMATION_TESTS

using namespace Stacktown;
using namespace StacktownTest;

#define STACKTOWN_PRESET_TEST(TestClass, PrettyName) \
	IMPLEMENT_SIMPLE_AUTOMATION_TEST(TestClass, PrettyName, \
		EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter) \
	bool TestClass::RunTest(const FString& Parameters)

// --- fourteen lots, for sale, at tier zero ------------------------------------------
STACKTOWN_PRESET_TEST(FStacktownPresetSeed, "Stacktown.Preset.Seed")
{
	const FPlacementBoard Board = FPlacementBoard::Default();
	FEconRules R = OracleRules();
	const FCityState Preset = SeedPresetState(R, Board);
	const FCityState Empty = SeedState(R);

	TestEqual(TEXT("an empty start really is empty"), Empty.Parcels.Num(), 0);
	TestEqual(TEXT("the preset seeds fourteen"), Preset.Parcels.Num(), Board.PinnedSpans.Num());
	// The money and demand of a FRESH city: the preset is a board to buy into,
	// not a saved game with a head start.
	TestEqual(TEXT("fresh money"), Preset.Money, Empty.Money, 1e-9);
	TestEqual(TEXT("fresh demand"), Preset.Demand, Empty.Demand, 1e-9);
	TestEqual(TEXT("no roads drawn"), Preset.Roads.Num(), 0);
	TestEqual(TEXT("no trades counted"), Preset.TradesProcessed, 0);

	for (const FPinnedSpan& Span : Board.PinnedSpans)
	{
		const FParcelState* P = Preset.Parcels.Find(Span.Key);
		TestNotNull(*FString::Printf(TEXT("%s is present"), *Span.Key), P);
		if (P == nullptr) { continue; }

		TestEqual(*FString::Printf(TEXT("%s rid"), *Span.Key), P->Rid, Span.Rid);
		TestEqual(*FString::Printf(TEXT("%s width"), *Span.Key), P->Width, Span.Width, 1e-9);
		// EVERY ONE UNOWNED AND AT TIER ZERO. Seeding a pin's declared tier is
		// the bug that made a bought lot show its full mature building instantly
		// instead of growing into it; the tier is not even carried in the data.
		TestFalse(*FString::Printf(TEXT("%s is for sale"), *Span.Key), P->bOwned);
		TestEqual(*FString::Printf(TEXT("%s starts at tier 0"), *Span.Key), P->Tier, 0);
		TestEqual(*FString::Printf(TEXT("%s has earned nothing"), *Span.Key), P->Accum, 0.0, 1e-9);
		TestFalse(*FString::Printf(TEXT("%s has not failed"), *Span.Key), P->bFailed);
		TestEqual(*FString::Printf(TEXT("%s age"), *Span.Key), P->AgeTicks, 0.0, 1e-9);

		// It has a placement, which is what makes it an ordinary lot.
		TestTrue(*FString::Printf(TEXT("%s has a placement"), *Span.Key), P->Placement.IsSet());
		if (!P->Placement.IsSet()) { continue; }
		const FLotPlacement& L = P->Placement.GetValue();
		TestEqual(*FString::Printf(TEXT("%s x0"), *Span.Key), L.X0, Span.X0, 1e-9);
		TestEqual(*FString::Printf(TEXT("%s x1"), *Span.Key), L.X1, Span.X1, 1e-9);
		TestEqual(*FString::Printf(TEXT("%s side"), *Span.Key), L.Side, Span.Side);
	}
	return true;
}

// --- every preset lot poses, which is the whole point of giving them one -------------
STACKTOWN_PRESET_TEST(FStacktownPresetPoses, "Stacktown.Preset.Poses")
{
	const FPlacementBoard Board = FPlacementBoard::Default();
	FEconRules R = OracleRules();
	const FCityState Preset = SeedPresetState(R, Board);
	const TArray<FRoad> RoadsLocal = Board.AllRoads(Preset);

	int32 Posed = 0;
	for (const TPair<FString, FParcelState>& Pair : Preset.Parcels)
	{
		TestTrue(*FString::Printf(TEXT("%s has a placement"), *Pair.Key),
			Pair.Value.Placement.IsSet());
		if (!Pair.Value.Placement.IsSet()) { continue; }
		LotFrame::FPose Pose;
		if (LotFrame::Pose(Pair.Value.Placement.GetValue(), RoadsLocal, Pose)) { ++Posed; }
	}
	// The city sync skips a lot it cannot pose. If this ever drops below
	// fourteen, that many buildings silently do not appear on a fresh start.
	TestEqual(TEXT("all fourteen pose"), Posed, Board.PinnedSpans.Num());
	return true;
}

// --- the preset lots are REAL occupants ----------------------------------------------
STACKTOWN_PRESET_TEST(FStacktownPresetOccupies, "Stacktown.Preset.Occupies")
{
	const FPlacementBoard Board = FPlacementBoard::Default();
	FEconRules R = OracleRules();
	const FCityState Preset = SeedPresetState(R, Board);

	// NE0's own centre. With pins ACTIVE this was already refused by the pinned
	// span check; the claim here is stronger and is what makes the preset lots
	// ordinary: even with pins OFF, a real parcel is standing there and the
	// overlap scan refuses the click on its own.
	const FClickResult Refused = ResolveClick(Board, Preset, 2360.0, 1500.0, false,
		Board.Rules.V0Width);
	TestFalse(TEXT("a click on a preset lot is refused with pins off"), Refused.bOk);
	TestTrue(TEXT("and it is the overlap scan that refused it"),
		Refused.Reason.Contains(TEXT("crosses an existing lot")));

	// On the empty start the same click is accepted, so the refusal above is the
	// preset's doing and not the board's.
	const FCityState Empty = SeedState(R);
	const FClickResult Accepted = ResolveClick(Board, Empty, 2360.0, 1500.0, false,
		Board.Rules.V0Width);
	TestTrue(TEXT("the same click is free on an empty start"), Accepted.bOk);
	return true;
}

// --- and it survives a save -----------------------------------------------------------
STACKTOWN_PRESET_TEST(FStacktownPresetRoundTrip, "Stacktown.Preset.RoundTrip")
{
	const FPlacementBoard Board = FPlacementBoard::Default();
	FEconRules R = OracleRules();
	const FCityState Preset = SeedPresetState(R, Board);

	FCityState Back;
	FString Err;
	TestTrue(TEXT("round trip parses"), Stacktown::CityStateFromJson(Stacktown::CityStateToJson(Preset), Back, Err));
	TestEqual(TEXT("still fourteen"), Back.Parcels.Num(), Preset.Parcels.Num());
	FString Why;
	const bool bSame = StatesEqual(Preset, Back, 1e-9, Why);
	TestTrue(*FString::Printf(TEXT("the whole preset round-trips (%s)"), *Why), bSame);
	return true;
}

#undef STACKTOWN_PRESET_TEST

#endif // WITH_DEV_AUTOMATION_TESTS
