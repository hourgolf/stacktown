// The runtime placement board (board factory, queue item 1).
//
//   UnrealEditor-Cmd <uproject> -ExecCmds="Automation RunTests Stacktown.Board; Quit" \
//     -unattended -nopause -nullrhi -log
//
// FPlacementBoard::Default() is PRODUCTION data - the board the live game stands
// on - generated from citylayout into StacktownBoardData.inl. The tests below do
// two distinct jobs, and the second is the one that matters most:
//
//   1. that the factory carries what it should (two roads, fourteen keyed pins);
//   2. that it AGREES, field for field, with the oracle fixture the ported
//      refusal logic was actually tested against. Generation already
//      cross-checks against placement.PINNED_SPANS, but a generator that stops
//      being run leaves stale output, and this is the assertion that notices.
//
// LotFrame::Pose itself is the coordinator's port and was proven live on the Mac
// (P1 at (1230, 1880), matching the Python). What is tested here is the BRIDGE:
// that a pinned key produces a placement Pose accepts and puts on the pin's own
// frontage - the piece the city sync was missing when it skipped every pin.

#include "Misc/AutomationTest.h"
#include "StacktownPlacementTestCommon.h"
#include "StacktownEconomyTestCommon.h"
#include "StacktownLotTransform.h"

#if WITH_DEV_AUTOMATION_TESTS

using namespace Stacktown;
using namespace StacktownTest;

#define STACKTOWN_BOARD_TEST(TestClass, PrettyName) \
	IMPLEMENT_SIMPLE_AUTOMATION_TEST(TestClass, PrettyName, \
		EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter) \
	bool TestClass::RunTest(const FString& Parameters)

// --- the factory carries the board ------------------------------------------------
STACKTOWN_BOARD_TEST(FStacktownBoardDefault, "Stacktown.Board.Default")
{
	const FPlacementBoard Board = FPlacementBoard::Default();

	TestEqual(TEXT("two built-in roads"), Board.Roads.Num(), StacktownPlacementOracle::RoadsNum);
	TestEqual(TEXT("fourteen pinned spans"), Board.PinnedSpans.Num(),
		StacktownPlacementOracle::PinnedSpansNum);
	TestEqual(TEXT("plate x min"), Board.PlateXMin, StacktownPlacementOracle::PlateXMin, 1e-9);
	TestEqual(TEXT("plate x max"), Board.PlateXMax, StacktownPlacementOracle::PlateXMax, 1e-9);
	TestEqual(TEXT("plate y min"), Board.PlateYMin, StacktownPlacementOracle::PlateYMin, 1e-9);
	TestEqual(TEXT("plate y max"), Board.PlateYMax, StacktownPlacementOracle::PlateYMax, 1e-9);
	TestEqual(TEXT("v0 width"), Board.Rules.V0Width, StacktownPlacementOracle::V0Width, 1e-9);
	TestEqual(TEXT("pool size"), Board.Rules.PoolSize, StacktownPlacementOracle::PoolSize);
	TestEqual(TEXT("v0 recipe"), Board.Rules.V0Recipe, FString(StacktownPlacementOracle::V0Recipe));

	// EVERY pinned span carries its key. Without it a pinned parcel cannot find
	// its own span, which is the whole reason the city sync skipped them.
	for (const FPinnedSpan& Span : Board.PinnedSpans)
	{
		TestFalse(FString::Printf(TEXT("span [%.0f, %.0f] has a key"), Span.X0, Span.X1),
			Span.Key.IsEmpty());
	}
	return true;
}

// --- and it agrees with the board the tests were proved against --------------------
STACKTOWN_BOARD_TEST(FStacktownBoardMatchesOracle, "Stacktown.Board.MatchesOracle")
{
	const FPlacementBoard Board = FPlacementBoard::Default();
	const FPlacementBoard Fixture = OracleBoard();

	TestEqual(TEXT("same road count"), Board.Roads.Num(), Fixture.Roads.Num());
	for (int32 i = 0; i < Board.Roads.Num() && i < Fixture.Roads.Num(); ++i)
	{
		const FRoad& A = Board.Roads[i];
		const FRoad& B = Fixture.Roads[i];
		TestEqual(FString::Printf(TEXT("road %d id"), i), A.Id, B.Id);
		TestEqual(FString::Printf(TEXT("road %d start x"), i), A.StartX, B.StartX, 1e-9);
		TestEqual(FString::Printf(TEXT("road %d start y"), i), A.StartY, B.StartY, 1e-9);
		TestEqual(FString::Printf(TEXT("road %d end x"), i), A.EndX, B.EndX, 1e-9);
		TestEqual(FString::Printf(TEXT("road %d end y"), i), A.EndY, B.EndY, 1e-9);
		TestEqual(FString::Printf(TEXT("road %d side plus"), i), A.SidePlus, B.SidePlus);
		TestEqual(FString::Printf(TEXT("road %d side minus"), i), A.SideMinus, B.SideMinus);
		TestEqual(FString::Printf(TEXT("road %d axis"), i), BoolStr(A.bAxisX), BoolStr(B.bAxisX));
	}

	// Spans are compared as a SET keyed by geometry, because the factory sorts
	// by key and the fixture keeps the oracle's own order - the orders differ
	// legitimately and comparing them positionally would fail on nothing.
	TestEqual(TEXT("same span count"), Board.PinnedSpans.Num(), Fixture.PinnedSpans.Num());
	for (const FPinnedSpan& Want : Fixture.PinnedSpans)
	{
		bool bFound = false;
		for (const FPinnedSpan& Got : Board.PinnedSpans)
		{
			if (FMath::Abs(Got.X0 - Want.X0) < 1e-9 && FMath::Abs(Got.X1 - Want.X1) < 1e-9
				&& Got.Side == Want.Side)
			{
				bFound = true;
				break;
			}
		}
		TestTrue(FString::Printf(TEXT("factory carries the %s span [%.0f, %.0f]"),
			*Want.Side, Want.X0, Want.X1), bFound);
	}
	return true;
}

// --- a pinned key produces a placement, and that placement poses -------------------
STACKTOWN_BOARD_TEST(FStacktownBoardPinnedPose, "Stacktown.Board.PinnedPose")
{
	const FPlacementBoard Board = FPlacementBoard::Default();
	const FCityState Empty;
	const TArray<FRoad> Roads = Board.AllRoads(Empty);

	const FRoad* Arterial = FindRoad(Roads, TEXT("arterial"));
	TestNotNull(TEXT("arterial"), Arterial);
	if (Arterial == nullptr) { return false; }

	int32 Posed = 0;
	for (const FPinnedSpan& Span : Board.PinnedSpans)
	{
		FLotPlacement Lot;
		TestTrue(FString::Printf(TEXT("%s resolves"), *Span.Key),
			PinnedPlacementForKey(Board, Span.Key, Lot));

		TestEqual(FString::Printf(TEXT("%s x0"), *Span.Key), Lot.X0, Span.X0, 1e-9);
		TestEqual(FString::Printf(TEXT("%s x1"), *Span.Key), Lot.X1, Span.X1, 1e-9);
		TestEqual(FString::Printf(TEXT("%s side"), *Span.Key), Lot.Side, Span.Side);
		// Every pinned span is on the arterial: PINNED_SPANS has no cross-street
		// entries at all, which is also why the click path gates its pinned
		// check on the arterial.
		TestEqual(FString::Printf(TEXT("%s road"), *Span.Key), LotRoadId(Lot),
			FString(TEXT("arterial")));

		// THE POINT OF THE WHOLE ITEM: the city sync skipped pins because they
		// had no pose. Now they do.
		LotFrame::FPose Pose;
		const bool bPosed = LotFrame::Pose(Lot, Roads, Pose);
		TestTrue(FString::Printf(TEXT("%s poses"), *Span.Key), bPosed);
		if (!bPosed) { continue; }
		++Posed;

		// The pad sits on the pin's own frontage, on its own side. These follow
		// from the span plus the arterial's centreline; Pose itself is the
		// coordinator's port and was proven live on the Mac.
		const double Expected = LotFrame::RoadHalf + LotFrame::BlockDepth * 0.5;
		if (Span.Side == TEXT("north"))
		{
			TestEqual(FString::Printf(TEXT("%s pad x"), *Span.Key), Pose.X, Span.X0, 1e-9);
			TestEqual(FString::Printf(TEXT("%s pad y"), *Span.Key), Pose.Y, Expected, 1e-9);
			TestEqual(FString::Printf(TEXT("%s yaw"), *Span.Key), Pose.Yaw, 0.0, 1e-9);
		}
		else
		{
			TestEqual(FString::Printf(TEXT("%s pad x"), *Span.Key), Pose.X, Span.X1, 1e-9);
			TestEqual(FString::Printf(TEXT("%s pad y"), *Span.Key), Pose.Y, -Expected, 1e-9);
			TestEqual(FString::Printf(TEXT("%s yaw"), *Span.Key), Pose.Yaw, 180.0, 1e-9);
		}
	}
	TestEqual(TEXT("all fourteen posed"), Posed, Board.PinnedSpans.Num());

	// An unknown key resolves nothing rather than yielding a lot at the origin.
	FLotPlacement Nope;
	TestFalse(TEXT("an unknown key resolves nothing"),
		PinnedPlacementForKey(Board, TEXT("NOPE"), Nope));
	return true;
}

// --- the factory's pins actually bite ----------------------------------------------
// TemporaryBoard carried no pinned spans, so the C++ game accepted clicks on
// pinned frontage that the Python refuses. With the factory in, it refuses them.
STACKTOWN_BOARD_TEST(FStacktownBoardPinsRefuse, "Stacktown.Board.PinsRefuse")
{
	const FPlacementBoard Board = FPlacementBoard::Default();
	FEconRules R = OracleRules();
	const FCityState S = SeedState(R);

	// NE0's own centre, the same click the ported placement test 11 uses.
	const FClickResult Refused = ResolveClick(Board, S, 2360.0, 1500.0, true, Board.Rules.V0Width);
	TestFalse(TEXT("a click on pinned frontage is refused"), Refused.bOk);
	TestTrue(TEXT("and says it crossed a pinned lot"),
		Refused.Reason.Contains(TEXT("pinned lot")));

	// The same click in empty mode still accepts - the mode gate is unchanged.
	const FClickResult Accepted = ResolveClick(Board, S, 2360.0, 1500.0, false, Board.Rules.V0Width);
	TestTrue(TEXT("empty mode still accepts"), Accepted.bOk);
	return true;
}

#undef STACKTOWN_BOARD_TEST

#endif // WITH_DEV_AUTOMATION_TESTS
