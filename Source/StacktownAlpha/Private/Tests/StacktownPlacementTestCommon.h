// Shared setup for the ported placement tests (Phase 1 step 2).
//
// The board below is built from PlacementOracleFixture.inl, which is generated
// by running placement.py. So the roads, the pinned spans and every constant
// are the oracle's own, not a second copy typed into a test.
#pragma once

#include "CoreMinimal.h"
#include "StacktownPlacement.h"
#include "PlacementOracleFixture.inl"
#include "StacktownEconomyTestCommon.h"   // OracleRules(): the road-type table is econrules.json's

namespace StacktownTest
{

/** The board the oracle was standing on: its two built-in roads, its fourteen
 *  pinned spans, and its constants. */
inline Stacktown::FPlacementBoard OracleBoard()
{
	using namespace StacktownPlacementOracle;

	Stacktown::FPlacementBoard Board;
	Board.Rules.PositionQuantum = PositionQuantum;
	Board.Rules.V0Width         = V0Width;
	Board.Rules.V0Recipe        = FString(V0Recipe);
	Board.Rules.PoolSize        = PoolSize;
	Board.Rules.RoadHalf        = StacktownPlacementOracle::RoadHalf;       // the fixture constant, not Stacktown::RoadHalf(...)
	Board.Rules.BlockDepth      = BlockDepth;
	Board.Rules.RoadMaxReach    = StacktownPlacementOracle::RoadMaxReach;
	Board.Rules.WidthQuantum    = WidthQuantum;
	Board.Rules.Verge           = Verge;
	Board.Rules.ReachSlack      = ReachSlack;
	// The road-type table the ORACLE read, not the one FEconRules compiles in.
	Board.Econ                  = StacktownTest::OracleRules();

	for (int32 i = 0; i < RoadsNum; ++i)
	{
		const FRoadDef& D = Roads[i];
		Stacktown::FRoad R;
		R.Id        = FString(D.Id);
		R.StartX    = D.StartX;
		R.StartY    = D.StartY;
		R.EndX      = D.EndX;
		R.EndY      = D.EndY;
		R.SidePlus  = FString(D.SidePlus);
		R.SideMinus = FString(D.SideMinus);
		R.bAxisX    = D.bAxisX;
		Board.Roads.Add(R);
	}
	for (int32 i = 0; i < PinnedSpansNum; ++i)
	{
		const FPinDef& D = PinnedSpans[i];
		Stacktown::FPinnedSpan S;
		S.X0 = D.X0;
		S.X1 = D.X1;
		S.Side = FString(D.Side);
		Board.PinnedSpans.Add(S);
	}
	return Board;
}

/** One road by id, for the tests that resolve against a SINGLE road - the
 *  "alone" qualifier tests 13 and 14 are specifically about. */
inline TArray<Stacktown::FRoad> OnlyRoad(const Stacktown::FPlacementBoard& Board, const TCHAR* Id)
{
	TArray<Stacktown::FRoad> Out;
	for (const Stacktown::FRoad& R : Board.Roads)
	{
		if (R.Id == Id)
		{
			Out.Add(R);
		}
	}
	return Out;
}

/** A fixture lot definition as the real type. A null RoadId in the fixture
 *  means the key is ABSENT, which is not the same as "arterial". */
inline Stacktown::FLotPlacement LotFrom(const StacktownPlacementOracle::FLotDef& D)
{
	Stacktown::FLotPlacement L;
	L.X0 = D.X0;
	L.X1 = D.X1;
	L.Side = FString(D.Side);
	if (D.RoadId != nullptr)
	{
		L.RoadId = FString(D.RoadId);
	}
	return L;
}

/** Field-by-field, absence included. Returns a reason on mismatch so a failing
 *  test says which field rather than only that something differed. */
inline bool LotMatches(const Stacktown::FLotPlacement& Got,
	const StacktownPlacementOracle::FLotDef& Want, FString& OutWhy)
{
	if (FMath::Abs(Got.X0 - Want.X0) > 1e-9 || FMath::Abs(Got.X1 - Want.X1) > 1e-9)
	{
		OutWhy = FString::Printf(TEXT("span [%.1f, %.1f] vs [%.1f, %.1f]"),
			Got.X0, Got.X1, Want.X0, Want.X1);
		return false;
	}
	if (Got.Side != FString(Want.Side))
	{
		OutWhy = FString::Printf(TEXT("side '%s' vs '%s'"), *Got.Side, Want.Side);
		return false;
	}
	const bool bWantSet = Want.RoadId != nullptr;
	if (Got.RoadId.IsSet() != bWantSet)
	{
		OutWhy = FString::Printf(TEXT("road_id present=%s, expected present=%s"),
			Got.RoadId.IsSet() ? TEXT("true") : TEXT("false"),
			bWantSet ? TEXT("true") : TEXT("false"));
		return false;
	}
	if (bWantSet && Got.RoadId.GetValue() != FString(Want.RoadId))
	{
		OutWhy = FString::Printf(TEXT("road_id '%s' vs '%s'"),
			*Got.RoadId.GetValue(), Want.RoadId);
		return false;
	}
	return true;
}

/** A parcel carrying only a placement, for building the states the corner and
 *  pool-exhaustion cases need directly. */
inline Stacktown::FParcelState PlacedParcel(const Stacktown::FPlacementBoard& Board,
	const StacktownPlacementOracle::FLotDef& D)
{
	Stacktown::FParcelState P;
	P.Rid = Board.Rules.V0Recipe;
	P.Tier = 0;
	P.Width = Board.Rules.V0Width;
	P.Placement = LotFrom(D);
	return P;
}

} // namespace StacktownTest
