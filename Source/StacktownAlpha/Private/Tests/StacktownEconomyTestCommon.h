// Shared setup for the ported economy tests.
//
// The catalogue and ruleset below are built from EconOracleFixture.inl, which is
// generated from the Python oracle. So a test here is not asking "does my C++
// agree with my C++" - the ladder answers, the baked set and every constant came
// out of the module this port is a translation of.
#pragma once

#include "CoreMinimal.h"
#include "StacktownEconomyRules.h"
#include "EconOracleFixture.inl"

namespace StacktownTest
{

/** econrules.json exactly as the oracle read it. Built field by field rather
 *  than parsed, so a test never depends on finding a file. */
inline Stacktown::FEconRules OracleRules()
{
	Stacktown::FEconRules R;
	R.MoneyStart        = StacktownOracle::MoneyStart;
	R.PriceBase         = StacktownOracle::PriceBase;
	R.PricePer100uu     = StacktownOracle::PricePer100uu;
	R.PricePerTier      = StacktownOracle::PricePerTier;
	R.RentPerTier       = StacktownOracle::RentPerTier;
	R.GrowthThreshold   = StacktownOracle::GrowthThreshold;
	R.DemandDefault     = StacktownOracle::DemandDefault;
	R.TradeCreditsPerN  = StacktownOracle::TradeCreditsPerN;
	R.TradeCreditAmount = StacktownOracle::TradeCreditAmount;
	R.TradeBonusPerWin  = StacktownOracle::TradeBonusPerWin;
	R.DemandGain        = StacktownOracle::DemandGain;
	R.DemandLoss        = StacktownOracle::DemandLoss;
	R.DemandRate        = StacktownOracle::DemandRate;
	R.DemandMin         = StacktownOracle::DemandMin;
	R.DemandMax         = StacktownOracle::DemandMax;
	R.WearTicksPerTier  = StacktownOracle::WearTicksPerTier;
	// ROAD TYPES: the owner's table, as the oracle read it out of
	// econrules.json - not FEconRules' own compiled default, so a placement
	// test measures the shipped ruleset. The two are compared directly by
	// Stacktown.Roads.TypeRulesMatchOracle.
	R.RoadTypes.Reset();
	for (int32 i = 0; i < StacktownOracle::RoadTypeRowsNum; ++i)
	{
		const StacktownOracle::FRoadTypeRow& Row = StacktownOracle::RoadTypeRows[i];
		Stacktown::FRoadTypeRules T;
		T.CostPer100uu = Row.CostPer100uu;
		T.RentMult     = Row.RentMult;
		T.Width        = Row.Width;
		T.bFrontage    = Row.bFrontage;
		R.RoadTypes.Add(FString(Row.Type), T);
	}
	R.RoadHighwayReach = StacktownOracle::RoadHighwayReach;
	{
		Stacktown::FRecipeMult V; V.Price = StacktownOracle::RecipeMult_vernacular_Price; V.Rent = StacktownOracle::RecipeMult_vernacular_Rent; R.RecipeMult.Add(TEXT("vernacular"), V);
		Stacktown::FRecipeMult O; O.Price = StacktownOracle::RecipeMult_office_Price;     O.Rent = StacktownOracle::RecipeMult_office_Rent;     R.RecipeMult.Add(TEXT("office"), O);
		Stacktown::FRecipeMult T; T.Price = StacktownOracle::RecipeMult_tower_Price;      T.Rent = StacktownOracle::RecipeMult_tower_Rent;      R.RecipeMult.Add(TEXT("tower"), T);
	}
	return R;
}

/** The catalogue the oracle was standing on: the three recipes the tests name,
 *  and exactly the meshes that were baked when the fixture was generated.
 *
 *  This is the one deliberate improvement on the Python's own tests. Their test
 *  5 asserts office t0->t1 is blocked and carries a comment admitting the
 *  assert will start failing the day somebody bakes office_t1 - a test that
 *  breaks on unrelated art work. Injecting the catalogue makes the same claim
 *  without the coupling. The real Baked/ directory is still checked, once, by
 *  the parity test rather than by all seventeen. */
inline TSharedRef<Stacktown::FStaticCatalogue> OracleCatalogue()
{
	TSharedRef<Stacktown::FStaticCatalogue> C = MakeShared<Stacktown::FStaticCatalogue>();
	C->TierCounts.Add(TEXT("vernacular"), StacktownOracle::TierCount_vernacular);
	C->TierCounts.Add(TEXT("office"),     StacktownOracle::TierCount_office);
	C->TierCounts.Add(TEXT("tower"),      StacktownOracle::TierCount_tower);
	for (int32 i = 0; i < StacktownOracle::BakedForTestsNum; ++i)
	{
		C->BakedAssets.Add(FString(StacktownOracle::BakedForTests[i]));
	}
	return C;
}

inline Stacktown::FParcelState Parcel(const TCHAR* Rid, int32 Tier, double Width,
	bool bOwned = false, double Accum = 0.0, bool bFailed = false, double Performance = 0.0,
	double AgeTicks = 0.0, const int32* AgeLastTier = nullptr)
{
	Stacktown::FParcelState P;
	P.AgeTicks = AgeTicks;
	if (AgeLastTier != nullptr) { P.AgeLastTier = *AgeLastTier; }
	P.Rid = Rid;
	P.Tier = Tier;
	P.Width = Width;
	P.bOwned = bOwned;
	P.Accum = Accum;
	P.bFailed = bFailed;
	P.Performance = Performance;
	return P;
}

inline Stacktown::FCityState CityWith(const TCHAR* Pid, const Stacktown::FParcelState& P,
	double Money, double Demand = 1.0)
{
	Stacktown::FCityState S;
	S.Money = Money;
	S.Demand = Demand;
	S.Parcels.Add(Pid, P);
	return S;
}

/** Bool as text, so a bool comparison goes through TestEqual's FString overload
 *  instead of relying on which of the int32/float/double overloads a bool
 *  promotes to. Keeps "got false, expected true" in the failure message, which
 *  TestTrue(A == B) would throw away. */
inline FString BoolStr(bool b) { return b ? FString(TEXT("true")) : FString(TEXT("false")); }

/** Field-by-field state comparison. The boundary tests need it because the
 *  claim they carry across from citytick.py is "what the wrapper produced and
 *  what the rules produced are the same state" - and after a save/load round
 *  trip, which is where a serialization bug would hide. Compared with the same
 *  tolerance as every other figure rather than by bit equality: JSON round-trips
 *  a double through decimal. */
inline bool StatesEqual(const Stacktown::FCityState& A, const Stacktown::FCityState& B,
	double Tolerance, FString& OutWhy)
{
	if (FMath::Abs(A.Money - B.Money) > Tolerance)
	{
		OutWhy = FString::Printf(TEXT("money %.12f vs %.12f"), A.Money, B.Money);
		return false;
	}
	if (FMath::Abs(A.Demand - B.Demand) > Tolerance)
	{
		OutWhy = FString::Printf(TEXT("demand %.12f vs %.12f"), A.Demand, B.Demand);
		return false;
	}
	if (A.GoalsReached != B.GoalsReached)
	{
		OutWhy = FString::Printf(TEXT("goals_reached %d vs %d"), A.GoalsReached, B.GoalsReached);
		return false;
	}
	if (A.TradesProcessed != B.TradesProcessed)
	{
		OutWhy = FString::Printf(TEXT("trades_processed %d vs %d"), A.TradesProcessed, B.TradesProcessed);
		return false;
	}
	if (A.Parcels.Num() != B.Parcels.Num())
	{
		OutWhy = FString::Printf(TEXT("parcel count %d vs %d"), A.Parcels.Num(), B.Parcels.Num());
		return false;
	}
	// Roads joined the schema in step 4. Compared here so a round-trip test
	// cannot pass while silently losing a road the player drew.
	if (A.Roads.Num() != B.Roads.Num())
	{
		OutWhy = FString::Printf(TEXT("road count %d vs %d"), A.Roads.Num(), B.Roads.Num());
		return false;
	}
	for (const TPair<FString, Stacktown::FRoadSegment>& Pair : A.Roads)
	{
		const Stacktown::FRoadSegment* Other = B.Roads.Find(Pair.Key);
		if (Other == nullptr)
		{
			OutWhy = FString::Printf(TEXT("road '%s' missing"), *Pair.Key);
			return false;
		}
		const Stacktown::FRoadSegment& S = Pair.Value;
		if (FMath::Abs(S.StartX - Other->StartX) > Tolerance
			|| FMath::Abs(S.StartY - Other->StartY) > Tolerance
			|| FMath::Abs(S.EndX - Other->EndX) > Tolerance
			|| FMath::Abs(S.EndY - Other->EndY) > Tolerance
			|| S.WidthClass != Other->WidthClass)
		{
			OutWhy = FString::Printf(TEXT("road '%s' differs"), *Pair.Key);
			return false;
		}
	}
	for (const TPair<FString, Stacktown::FParcelState>& Pair : A.Parcels)
	{
		const Stacktown::FParcelState* Other = B.Parcels.Find(Pair.Key);
		if (Other == nullptr)
		{
			OutWhy = FString::Printf(TEXT("parcel '%s' missing"), *Pair.Key);
			return false;
		}
		const Stacktown::FParcelState& P = Pair.Value;
		if (P.Rid != Other->Rid || P.Tier != Other->Tier || P.bOwned != Other->bOwned
			|| P.bFailed != Other->bFailed
			|| FMath::Abs(P.Width - Other->Width) > Tolerance
			|| FMath::Abs(P.Accum - Other->Accum) > Tolerance
			|| FMath::Abs(P.Performance - Other->Performance) > Tolerance)
		{
			OutWhy = FString::Printf(TEXT("parcel '%s' differs"), *Pair.Key);
			return false;
		}
		// Age joined the schema in queue item 7. Compared here, ABSENCE
		// included: a round trip that quietly turned an unmeasured lot into one
		// recorded at tier 0 would change when its patina starts.
		if (FMath::Abs(P.Wear - Other->Wear) > Tolerance)
		{
			OutWhy = FString::Printf(TEXT("parcel '%s': wear differs"), *Pair.Key);
			return false;
		}
		if (FMath::Abs(P.AgeTicks - Other->AgeTicks) > Tolerance
			|| P.AgeLastTier.IsSet() != Other->AgeLastTier.IsSet()
			|| (P.AgeLastTier.IsSet() && P.AgeLastTier.GetValue() != Other->AgeLastTier.GetValue()))
		{
			OutWhy = FString::Printf(TEXT("parcel '%s': age differs"), *Pair.Key);
			return false;
		}
		// Placement joined the schema in step 2. Compared here so a round-trip
		// test cannot pass while silently dropping a placed lot's position - and
		// ABSENT road_id is compared as absent, because preserving that
		// distinction is the whole point of it being optional.
		if (P.Placement.IsSet() != Other->Placement.IsSet())
		{
			OutWhy = FString::Printf(TEXT("parcel '%s': placement present on one side only"), *Pair.Key);
			return false;
		}
		if (P.Placement.IsSet())
		{
			const Stacktown::FLotPlacement& L = P.Placement.GetValue();
			const Stacktown::FLotPlacement& M = Other->Placement.GetValue();
			if (FMath::Abs(L.X0 - M.X0) > Tolerance || FMath::Abs(L.X1 - M.X1) > Tolerance
				|| L.Side != M.Side
				|| L.RoadId.IsSet() != M.RoadId.IsSet()
				|| (L.RoadId.IsSet() && L.RoadId.GetValue() != M.RoadId.GetValue()))
			{
				OutWhy = FString::Printf(TEXT("parcel '%s': placement differs"), *Pair.Key);
				return false;
			}
		}
	}
	return true;
}

/** Every comparison of a money/rent figure in these tests. 1e-9 is the Python's
 *  own tolerance, carried across rather than loosened to make a port pass. */
inline constexpr double Tol = 1e-9;

} // namespace StacktownTest
