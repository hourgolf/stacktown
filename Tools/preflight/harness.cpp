// Free-standing pre-flight for the ported economy rules. READ CoreMinimal.h in
// this directory before reading a pass line off this program: it is a shim, not
// Unreal, and a green run here is not the proof PLAN_CPP_PORT.md section 3 asks
// for. The proof is the headless Automation pass on the Mac.
//
// What this buys: the ported arithmetic, every refusal string, the tick and the
// ledger are EXECUTED against oracle-generated expectations before the branch
// ever reaches a machine with an engine on it. It compiles the real
// StacktownEconomyRules.cpp and includes the real shared test header, so the
// catalogue, the ruleset and the expectations are the same objects the
// Automation tests use - not a second copy that can drift from them.
//
// It cannot cover the nine CityState boundary tests: those need UObject and the
// Json module, neither of which exists here.
//
//   Tools/preflight/run.sh

#include "StacktownEconomyTestCommon.h"
#include "StacktownPlacementTestCommon.h"
#include "StacktownStateHandover.h"
#include "RoadsOracleFixture.inl"
#include "StacktownLotTransform.h"

#include <cstdio>
#include <string>

using namespace Stacktown;
using namespace StacktownTest;

static int gChecks = 0;
static int gFailures = 0;
static const char* gCase = "";

static void Fail(const std::string& What, const std::string& Detail)
{
	++gFailures;
	printf("  FAIL  [%s] %s: %s\n", gCase, What.c_str(), Detail.c_str());
}

static void CheckNear(const std::string& What, double Actual, double Expected, double Tolerance)
{
	++gChecks;
	if (!(FMath::Abs(Actual - Expected) <= Tolerance))
	{
		Fail(What, std::string("got ") + std::to_string(Actual) + ", expected " + std::to_string(Expected));
	}
}

static void CheckInt(const std::string& What, int32 Actual, int32 Expected)
{
	++gChecks;
	if (Actual != Expected)
	{
		Fail(What, std::string("got ") + std::to_string(Actual) + ", expected " + std::to_string(Expected));
	}
}

static void CheckBool(const std::string& What, bool Actual, bool Expected)
{
	++gChecks;
	if (Actual != Expected)
	{
		Fail(What, std::string("got ") + (Actual ? "true" : "false") + ", expected " + (Expected ? "true" : "false"));
	}
}

static void CheckStr(const std::string& What, const FString& Actual, const FString& Expected)
{
	++gChecks;
	if (!(Actual == Expected))
	{
		Fail(What, std::string("got \"") + *Actual + "\", expected \"" + *Expected + "\"");
	}
}

#define CASE(Name) gCase = Name

int main()
{
	const FEconRules R = OracleRules();
	const TSharedRef<FStaticCatalogue> Cat = OracleCatalogue();

	// --- 1 price -----------------------------------------------------------
	CASE("Price");
	for (const StacktownOracle::FTierWidthCase& C : StacktownOracle::PriceCases)
	{
		CheckNear("price", Price(R, C.Tier, C.Width), C.Expected, Tol);
	}

	// --- 2 rent ------------------------------------------------------------
	CASE("Rent");
	for (const StacktownOracle::FTierDemandCase& C : StacktownOracle::RentCases)
	{
		CheckNear("rent", Rent(R, C.Tier, C.Demand), C.Expected, Tol);
	}

	// --- 3 buy then ten ticks ----------------------------------------------
	CASE("BuyThenTick");
	{
		FCityState S = CityWith(TEXT("P1"), Parcel(TEXT("vernacular"), 0, 1230.0), 100.0);
		CheckBool("buy ok", Buy(R, S, TEXT("P1")).bOk, true);
		CheckNear("money after buy", S.Money, StacktownOracle::BuyThenTick10_AfterBuyMoney, Tol);
		int32 Events = 0;
		TArray<FEconEvent> E;
		for (int32 i = 0; i < 10; ++i) { Tick(R, S, E); Events += E.Num(); }
		CheckNear("money", S.Money, StacktownOracle::BuyThenTick10_Money, Tol);
		CheckNear("accum", S.Parcels[TEXT("P1")].Accum, StacktownOracle::BuyThenTick10_Accum, Tol);
		CheckInt("tier", S.Parcels[TEXT("P1")].Tier, StacktownOracle::BuyThenTick10_Tier);
		CheckInt("events", Events, StacktownOracle::BuyThenTick10_Events);
	}

	// --- 4 + 5 ladder ------------------------------------------------------
	CASE("Ladder");
	for (const StacktownOracle::FLadderCase& C : StacktownOracle::LadderCases)
	{
		const FVerbResult Got = TierUpAllowed(*Cat, C.Rid, C.Tier, C.Width);
		CheckBool("ok", Got.bOk, C.bOk);
		CheckStr("reason", Got.Reason, FString(C.Reason));
	}

	CASE("AssetName");
	CheckStr("office t0", Cat->AssetName(TEXT("office"), 0, 2050.0),
		FString(StacktownOracle::AssetName_office_t0_w2050));
	CheckStr("office t1", Cat->AssetName(TEXT("office"), 1, 2050.0),
		FString(StacktownOracle::AssetName_office_t1_w2050));
	CheckStr("vernacular t0", Cat->AssetName(TEXT("vernacular"), 0, 1230.0),
		FString(StacktownOracle::AssetName_vernacular_t0_w1230));
	CheckBool("office t0 baked", Cat->AssetExists(TEXT("office"), 0, 2050.0),
		StacktownOracle::AssetExists_office_t0_w2050);
	CheckBool("office t1 not baked", Cat->AssetExists(TEXT("office"), 1, 2050.0),
		StacktownOracle::AssetExists_office_t1_w2050);

	// --- 6 the retired growth branch ---------------------------------------
	CASE("GrowthRetired");
	{
		FCityState S = CityWith(TEXT("OF"), Parcel(TEXT("office"), 0, 2050.0, true, 39.9), 0.0);
		TArray<FEconEvent> E;
		Tick(R, S, E);
		CheckNear("money", S.Money, StacktownOracle::TickRetired_Money, Tol);
		CheckNear("accum", S.Parcels[TEXT("OF")].Accum, StacktownOracle::TickRetired_Accum, Tol);
		CheckInt("tier", S.Parcels[TEXT("OF")].Tier, StacktownOracle::TickRetired_Tier);
		CheckInt("events", E.Num(), StacktownOracle::TickRetired_Events);
	}

	// --- 7 buy refusals ----------------------------------------------------
	CASE("BuyRefusals");
	{
		FCityState S = CityWith(TEXT("P"), Parcel(TEXT("vernacular"), 0, 1230.0), 1.0);
		const FVerbResult G = Buy(R, S, TEXT("P"));
		CheckBool("ok", G.bOk, StacktownOracle::Buy_insufficient_Ok);
		CheckStr("reason", G.Reason, FString(StacktownOracle::Buy_insufficient_Reason));
		CheckNear("spent nothing", S.Money, 1.0, Tol);
		CheckBool("transferred nothing", S.Parcels[TEXT("P")].bOwned, false);
	}
	{
		FCityState S; S.Money = 100.0;
		const FVerbResult G = Buy(R, S, TEXT("NOPE"));
		CheckBool("ok", G.bOk, StacktownOracle::Buy_missing_Ok);
		CheckStr("reason", G.Reason, FString(StacktownOracle::Buy_missing_Reason));
	}
	{
		FCityState S = CityWith(TEXT("P"), Parcel(TEXT("vernacular"), 0, 1230.0, true), 100.0);
		const FVerbResult G = Buy(R, S, TEXT("P"));
		CheckBool("ok", G.bOk, StacktownOracle::Buy_already_Ok);
		CheckStr("reason", G.Reason, FString(StacktownOracle::Buy_already_Reason));
		CheckNear("not charged", S.Money, 100.0, Tol);
	}

	// --- 8 a thousand ticks -------------------------------------------------
	CASE("ThousandTicks");
	{
		FCityState S = CityWith(TEXT("P1"), Parcel(TEXT("vernacular"), 0, 1230.0, true), 0.0);
		int32 Events = 0;
		TArray<FEconEvent> E;
		for (int32 i = 0; i < 1000; ++i) { Tick(R, S, E); Events += E.Num(); }
		CheckNear("money", S.Money, StacktownOracle::Tick1000_Money, 1e-6);
		CheckNear("accum", S.Parcels[TEXT("P1")].Accum, StacktownOracle::Tick1000_Accum, 1e-6);
		CheckInt("tier", S.Parcels[TEXT("P1")].Tier, StacktownOracle::Tick1000_Tier);
		CheckInt("events", Events, StacktownOracle::Tick1000_Events);
	}

	// --- 9 climb / premium / prices -----------------------------------------
	CASE("ClimbAndPremium");
	for (const StacktownOracle::FIntCase& C : StacktownOracle::ClimbCases)
	{
		CheckInt("climb", Climb(C.In), C.Expected);
	}
	for (const StacktownOracle::FDoubleCase& C : StacktownOracle::PremiumCases)
	{
		CheckNear("premium", Premium(C.In), C.Expected, Tol);
	}
	for (const StacktownOracle::FTierPerfCase& C : StacktownOracle::UpgradePriceCases)
	{
		CheckNear("upgrade_price", UpgradePrice(R, C.Tier, C.Performance), C.Expected, Tol);
	}
	for (const StacktownOracle::FIntCase& C : StacktownOracle::RepairPriceCases)
	{
		CheckNear("repair_price", RepairPrice(R, C.In), static_cast<double>(C.Expected), Tol);
	}

	// --- 10 upgrade pricing --------------------------------------------------
	CASE("UpgradePricing");
	{
		FCityState S = CityWith(TEXT("P1"), Parcel(TEXT("vernacular"), 0, 1230.0, true), 100.0);
		CheckBool("first upgrade", Upgrade(R, *Cat, S, TEXT("P1")).bOk, true);
		CheckNear("money", S.Money, StacktownOracle::UpgradeHappy_Money, Tol);
		CheckInt("tier", S.Parcels[TEXT("P1")].Tier, StacktownOracle::UpgradeHappy_Tier);

		const FVerbResult Second = Upgrade(R, *Cat, S, TEXT("P1"));
		CheckBool("climb refuses", Second.bOk, StacktownOracle::Upgrade_CLIMB_REFUSES_Ok);
		CheckStr("climb reason", Second.Reason, FString(StacktownOracle::Upgrade_CLIMB_REFUSES_Reason));

		FCityState W = CityWith(TEXT("P2"),
			Parcel(TEXT("vernacular"), 0, 1230.0, true, 0.0, false, -1.0), 100.0);
		CheckBool("worst still affords", Upgrade(R, *Cat, W, TEXT("P2")).bOk, true);
		CheckNear("worst money", W.Money, StacktownOracle::UpgradeWorst_Money, Tol);
		CheckInt("worst tier", W.Parcels[TEXT("P2")].Tier, StacktownOracle::UpgradeWorst_Tier);
	}

	// --- 11 upgrade refusals -------------------------------------------------
	CASE("UpgradeRefusals");
	{
		FCityState S;
		S.Money = 1000.0;
		S.Demand = 1.0;
		S.Parcels.Add(TEXT("UNOWNED"), Parcel(TEXT("vernacular"), 0, 1230.0));
		S.Parcels.Add(TEXT("FAILED"),  Parcel(TEXT("vernacular"), 0, 1230.0, true, 0.0, true));
		S.Parcels.Add(TEXT("TOPPED"),  Parcel(TEXT("office"), 3, 2050.0, true));
		S.Parcels.Add(TEXT("UNBAKED"), Parcel(TEXT("office"), 0, 2050.0, true));
		S.Parcels.Add(TEXT("WORST"),   Parcel(TEXT("vernacular"), 0, 1230.0, true, 0.0, false, -1.0));

		struct FRefusal { const TCHAR* Pid; bool bOk; const TCHAR* Reason; };
		const FRefusal Refusals[] = {
			{ TEXT("UNOWNED"), StacktownOracle::Upgrade_UNOWNED_Ok, StacktownOracle::Upgrade_UNOWNED_Reason },
			{ TEXT("FAILED"),  StacktownOracle::Upgrade_FAILED_Ok,  StacktownOracle::Upgrade_FAILED_Reason  },
			{ TEXT("TOPPED"),  StacktownOracle::Upgrade_TOPPED_Ok,  StacktownOracle::Upgrade_TOPPED_Reason  },
			{ TEXT("UNBAKED"), StacktownOracle::Upgrade_UNBAKED_Ok, StacktownOracle::Upgrade_UNBAKED_Reason },
			{ TEXT("NOPE"),    StacktownOracle::Upgrade_NOPE_Ok,    StacktownOracle::Upgrade_NOPE_Reason    },
		};
		for (const FRefusal& C : Refusals)
		{
			const double Before = S.Money;
			const FVerbResult G = Upgrade(R, *Cat, S, C.Pid);
			CheckBool("ok", G.bOk, C.bOk);
			CheckStr("reason", G.Reason, FString(C.Reason));
			CheckNear("charged nothing", S.Money, Before, Tol);
		}
		CheckBool("worst does not block", Upgrade(R, *Cat, S, TEXT("WORST")).bOk,
			StacktownOracle::Upgrade_WORST_Ok);
		CheckInt("worst climbed", S.Parcels[TEXT("WORST")].Tier, 1);
	}

	// --- 12 + 13 repair -------------------------------------------------------
	CASE("Repair");
	{
		FCityState S = CityWith(TEXT("P1"),
			Parcel(TEXT("vernacular"), 1, 1230.0, true, 0.0, true), 150.0);
		CheckBool("ok", Repair(R, S, TEXT("P1")).bOk, true);
		CheckNear("money", S.Money, StacktownOracle::RepairHappy_Money, Tol);
		CheckBool("cleared", S.Parcels[TEXT("P1")].bFailed, StacktownOracle::RepairHappy_Failed);
	}
	CASE("RepairRefusals");
	{
		FCityState S;
		S.Money = 1.0;
		S.Demand = 1.0;
		S.Parcels.Add(TEXT("UNOWNED"), Parcel(TEXT("vernacular"), 0, 1230.0));
		S.Parcels.Add(TEXT("FINE"),    Parcel(TEXT("vernacular"), 0, 1230.0, true));
		S.Parcels.Add(TEXT("POOR"),    Parcel(TEXT("vernacular"), 0, 1230.0, true, 0.0, true));

		struct FRefusal { const TCHAR* Pid; bool bOk; const TCHAR* Reason; };
		const FRefusal Refusals[] = {
			{ TEXT("UNOWNED"), StacktownOracle::Repair_UNOWNED_Ok, StacktownOracle::Repair_UNOWNED_Reason },
			{ TEXT("FINE"),    StacktownOracle::Repair_FINE_Ok,    StacktownOracle::Repair_FINE_Reason    },
			{ TEXT("POOR"),    StacktownOracle::Repair_POOR_Ok,    StacktownOracle::Repair_POOR_Reason    },
			{ TEXT("NOPE"),    StacktownOracle::Repair_NOPE_Ok,    StacktownOracle::Repair_NOPE_Reason    },
		};
		for (const FRefusal& C : Refusals)
		{
			const FVerbResult G = Repair(R, S, C.Pid);
			CheckBool("ok", G.bOk, C.bOk);
			CheckStr("reason", G.Reason, FString(C.Reason));
		}
		CheckNear("no refusal spent money", S.Money, 1.0, Tol);
	}

	// --- 14 is_win --------------------------------------------------------------
	CASE("IsWin");
	for (const StacktownOracle::FPnlCase& C : StacktownOracle::IsWinCases)
	{
		CheckBool("is_win", IsWin(C.Pnl), C.bExpected);
	}

	// --- 15 + 16 trade arithmetic ----------------------------------------------
	CASE("TradeArithmetic");
	for (const StacktownOracle::FCountRewardCase& C : StacktownOracle::CountRewardCases)
	{
		CheckNear("count reward", TradeCountReward(C.Before, C.New, C.PerN, C.Amount), C.Expected, Tol);
	}
	{
		TArray<double> Three;
		Three.Add(5.0); Three.Add(-2.0); Three.Add(10.0);
		CheckNear("bonus", TradeOutcomeBonus(Three, 5.0), 10.0, Tol);
		CheckNear("bonus over nothing", TradeOutcomeBonus(TArray<double>(), 5.0), 0.0, Tol);
	}

	// --- 17 the ledger, and its idempotency ------------------------------------
	CASE("TradeLedger");
	{
		TArray<double> Ledger;
		Ledger.Append(StacktownOracle::LedgerPnls, StacktownOracle::LedgerPnlsNum);

		FCityState S;
		TArray<FEconEvent> E;
		ApplyTradeLedger(R, S, Ledger, E);
		CheckNear("money", S.Money, StacktownOracle::Ledger_Money, Tol);
		CheckInt("processed", S.TradesProcessed, StacktownOracle::Ledger_Processed);
		CheckInt("events", E.Num(), StacktownOracle::LedgerEvents_First_Num);
		if (E.Num() == 2)
		{
			CheckBool("credits first", E[0].Type == EEconEventType::TradeCredits, true);
			CheckNear("credit amount", E[0].Amount, StacktownOracle::LedgerEvents_First_0_Amount, Tol);
			CheckBool("bonus second", E[1].Type == EEconEventType::TradeBonus, true);
			CheckNear("bonus amount", E[1].Amount, StacktownOracle::LedgerEvents_First_1_Amount, Tol);
		}

		const double MoneyBefore = S.Money;
		const int32 ProcessedBefore = S.TradesProcessed;
		TArray<FEconEvent> Replay;
		ApplyTradeLedger(R, S, Ledger, Replay);
		CheckNear("replay money", S.Money, MoneyBefore, Tol);
		CheckInt("replay processed", S.TradesProcessed, ProcessedBefore);
		CheckInt("replay events", Replay.Num(), StacktownOracle::LedgerEvents_Replay_Num);

		TArray<double> Longer;
		Longer.Append(StacktownOracle::LedgerPnlsLonger, StacktownOracle::LedgerPnlsLongerNum);
		TArray<FEconEvent> LE;
		ApplyTradeLedger(R, S, Longer, LE);
		CheckNear("longer money", S.Money, StacktownOracle::LedgerLonger_Money, Tol);
		CheckInt("longer processed", S.TradesProcessed, StacktownOracle::LedgerLonger_Processed);
		CheckInt("longer events", LE.Num(), StacktownOracle::LedgerEvents_Longer_Num);
		if (LE.Num() == 1)
		{
			CheckBool("the one event is a bonus", LE[0].Type == EEconEventType::TradeBonus, true);
			CheckNear("its amount", LE[0].Amount, StacktownOracle::LedgerEvents_Longer_0_Amount, Tol);
		}
	}

	// --- added by the port: multi-parcel tick ------------------------------------
	CASE("MultiParcelOrder");
	{
		FCityState S;
		S.Money = 0.0;
		S.Demand = StacktownOracle::TickMulti_Demand;
		S.Parcels.Add(TEXT("C"), Parcel(TEXT("vernacular"), 2, 1230.0, true));
		S.Parcels.Add(TEXT("A"), Parcel(TEXT("vernacular"), 0, 1230.0, true));
		S.Parcels.Add(TEXT("B"), Parcel(TEXT("office"), 1, 2050.0, false));
		TArray<FEconEvent> E;
		Tick(R, S, E);
		CheckNear("money", S.Money, StacktownOracle::TickMulti_Money, Tol);
		CheckNear("A accum", S.Parcels[TEXT("A")].Accum, StacktownOracle::TickMulti_Accum_A, Tol);
		CheckNear("C accum", S.Parcels[TEXT("C")].Accum, StacktownOracle::TickMulti_Accum_C, Tol);
		CheckNear("B accrues nothing", S.Parcels[TEXT("B")].Accum, StacktownOracle::TickMulti_Accum_B, Tol);
	}

	// =====================================================================
	// PLACEMENT (Phase 1 step 2) - placement.py self-tests 1-27.
	// Tests 28-39 (drawn roads) are step 4's and are not here. Tests 6 and 26
	// are also absent: both are about serialization, which needs the Json
	// module, so they run only on the Mac.
	// =====================================================================
	{
		using namespace StacktownPlacementOracle;
		const FPlacementBoard Board = OracleBoard();
		auto Seed = [&R]() { return SeedState(R); };

		auto CheckLot = [&](const char* What, const FLotPlacement& Got, const FLotDef& Want) {
			FString Why;
			++gChecks;
			if (!LotMatches(Got, Want, Why)) { Fail(What, Why.S); }
		};

		CASE("Placement.FirstPlace");
		{
			FCityState S = Seed();
			const FPlaceResult Res = Place(Board, S, T1_X, T1_Y, true, V0Width);
			CheckBool("ok", Res.bOk, T1_Ok);
			CheckStr("pid", Res.Pid, FString(T1_Pid));
			CheckStr("reason", Res.Reason, FString(T1_Reason));
			const FParcelState& P = S.Parcels[FString(T1_Pid)];
			CheckStr("rid", P.Rid, FString(T1_Rid));
			CheckInt("tier", P.Tier, T1_Tier);
			CheckNear("width", P.Width, T1_Width, Tol);
			CheckBool("placement present", P.Placement.IsSet(), true);
			if (P.Placement.IsSet()) { CheckLot("lot", P.Placement.GetValue(), T1_Lot); }
		}

		CASE("Placement.OffBoard");
		{
			FCityState S = Seed();
			Place(Board, S, T1_X, T1_Y, true, V0Width);
			const int32 Before = S.Parcels.Num();
			const FPlaceResult Res = Place(Board, S, T2_X, T2_Y, true, V0Width);
			CheckBool("ok", Res.bOk, T2_Ok);
			CheckStr("reason", Res.Reason, FString(T2_Reason));
			CheckInt("nothing registered", S.Parcels.Num(), Before);
		}

		CASE("Placement.Sides");
		{
			FCityState Base = Seed();
			Place(Board, Base, T1_X, T1_Y, true, V0Width);
			FCityState A = Base;
			const FPlaceResult Over = Place(Board, A, T3_X, T3_Y, true, V0Width);
			CheckBool("overlap ok", Over.bOk, T3_Ok);
			CheckStr("overlap reason", Over.Reason, FString(T3_Reason));
			FCityState B = Base;
			const FPlaceResult South = Place(Board, B, T4_X, T4_Y, true, V0Width);
			CheckBool("south ok", South.bOk, T4_Ok);
			CheckStr("south pid", South.Pid, FString(T4_Pid));
			CheckLot("south lot", B.Parcels[FString(T4_Pid)].Placement.GetValue(), T4_Lot);
		}

		CASE("Placement.NextPid");
		{
			FCityState S = Seed();
			Place(Board, S, T1_X, T1_Y, true, V0Width);
			Place(Board, S, T4_X, T4_Y, true, V0Width);
			const FPlaceResult Res = Place(Board, S, T5_X, T5_Y, true, V0Width);
			CheckBool("ok", Res.bOk, T5_Ok);
			CheckStr("pid", Res.Pid, FString(T5_Pid));
			CheckLot("lot", S.Parcels[FString(T5_Pid)].Placement.GetValue(), T5_Lot);
		}

		CASE("Placement.PlateContainsBlocks");
		CheckBool("west", PlateXMin <= BlockEnvXMin, true);
		CheckBool("east", BlockEnvXMax <= PlateXMax, true);

		CASE("Placement.PoolExhausted");
		{
			FCityState S = Seed();
			const FLotDef Degenerate = { 0.0, 0.0, TEXT("north"), nullptr };
			for (int32 i = 0; i < PoolSize; ++i)
			{
				S.Parcels.Add(FString::Printf(TEXT("ZZ%d"), i), PlacedParcel(Board, Degenerate));
			}
			const FPlaceResult Res = Place(Board, S, T8_X, T8_Y, true, V0Width);
			CheckBool("ok", Res.bOk, T8_Ok);
			CheckStr("reason", Res.Reason, FString(T8_Reason));
		}

		CASE("Placement.PlanReactivation");
		{
			auto RunPlan = [&](const TCHAR* const* Pids, int32 PidsNum,
			                   const TCHAR* const* Labels, int32 LabelsNum,
			                   const TCHAR* const* WantPids, const TCHAR* const* WantLabels,
			                   int32 PairsNum, const TCHAR* const* WantUn, int32 UnNum) {
				TArray<FString> P, L;
				for (int32 i = 0; i < PidsNum; ++i)   { P.Add(FString(Pids[i])); }
				for (int32 i = 0; i < LabelsNum; ++i) { L.Add(FString(Labels[i])); }
				TArray<TPair<FString, FString>> Pairs;
				TArray<FString> Un;
				PlanReactivation(P, L, Pairs, Un);
				CheckInt("pair count", Pairs.Num(), PairsNum);
				for (int32 i = 0; i < PairsNum && i < Pairs.Num(); ++i)
				{
					CheckStr("pair pid", Pairs[i].Key, FString(WantPids[i]));
					CheckStr("pair label", Pairs[i].Value, FString(WantLabels[i]));
				}
				CheckInt("unmatched count", Un.Num(), UnNum);
				for (int32 i = 0; i < UnNum && i < Un.Num(); ++i)
				{
					CheckStr("unmatched", Un[i], FString(WantUn[i]));
				}
			};
			RunPlan(T9_Pids, T9_PidsNum, T9_Labels, T9_LabelsNum,
			        T9_PairPids, T9_PairLabels, T9_PairsNum, T9_Unmatched, T9_UnmatchedNum);
			RunPlan(T10_Pids, T10_PidsNum, T10_Labels, T10_LabelsNum,
			        T10_PairPids, T10_PairLabels, T10_PairsNum, T10_Unmatched, T10_UnmatchedNum);
			RunPlan(T12_Pids, T12_PidsNum, T12_Labels, T12_LabelsNum,
			        T12_PairPids, T12_PairLabels, T12_PairsNum, T12_Unmatched, T12_UnmatchedNum);
		}

		CASE("Placement.PinnedSpans");
		{
			const FCityState S = Seed();
			const FClickResult Ref = ResolveClick(Board, S, T11.X, T11.Y, T11.bPinsActive, V0Width);
			CheckBool("pins active ok", Ref.bOk, T11.bOk);
			CheckStr("pins active reason", Ref.Reason, FString(T11.Reason));
			const FClickResult Acc = ResolveClick(Board, S, T11b.X, T11b.Y, T11b.bPinsActive, V0Width);
			CheckBool("empty mode ok", Acc.bOk, T11b.bOk);
			CheckStr("empty mode reason", Acc.Reason, FString(T11b.Reason));
			CheckLot("empty mode lot", Acc.Lot, T11b.Lot);
		}

		auto CheckResolve = [&](const char* What, const TArray<FRoad>& Roads, const FResolveCase& C) {
			FRoadLocal Local;
			const FRoad* Got = ResolveRoad(Board.Rules, Roads, C.X, C.Y, Local);
			if (C.Road == nullptr) { CheckBool(What, Got == nullptr, true); return; }
			++gChecks;
			if (Got == nullptr) { Fail(What, "expected a road, got none"); return; }
			CheckStr("road", Got->Id, FString(C.Road));
			CheckNear("along", Local.Along, C.Along, Tol);
			CheckNear("across", Local.Across, C.Across, Tol);
			CheckStr("side", Local.Side, FString(C.Side));
		};

		CASE("Placement.ResolveRoadAlone");
		{
			const TArray<FRoad> Arterial = OnlyRoad(Board, TEXT("arterial"));
			const TArray<FRoad> Cross    = OnlyRoad(Board, TEXT("cross"));
			for (int32 i = 0; i < T13ArterialAloneNum; ++i) { CheckResolve("arterial alone", Arterial, T13ArterialAlone[i]); }
			for (int32 i = 0; i < T14CrossAloneNum; ++i)    { CheckResolve("cross alone", Cross, T14CrossAlone[i]); }
		}

		CASE("Placement.ResolveRoadSelection");
		{
			CheckResolve("nearest wins", Board.Roads, T15);
			CheckResolve("past the band", Board.Roads, T17);
			CheckResolve("point to segment", OnlyRoad(Board, TEXT("arterial")), T18);
			for (int32 i = 0; i < T19TooFarNum; ++i) { CheckResolve("too far", Board.Roads, T19TooFar[i]); }
		}

		CASE("Placement.ResolveRoadCrossing");
		for (int32 i = 0; i < T16CrossingNum; ++i) { CheckResolve("crossing", Board.Roads, T16Crossing[i]); }

		CASE("Placement.CrossStreet");
		{
			FCityState S = Seed();
			const FPlaceResult W = Place(Board, S, T20_X, T20_Y, true, V0Width);
			CheckBool("west ok", W.bOk, T20_Ok);
			CheckStr("west pid", W.Pid, FString(T20_Pid));
			CheckLot("west lot", S.Parcels[FString(T20_Pid)].Placement.GetValue(), T20_Lot);
			const FPlaceResult E = Place(Board, S, T21_X, T21_Y, true, V0Width);
			CheckBool("east ok", E.bOk, T21_Ok);
			CheckStr("east pid", E.Pid, FString(T21_Pid));
			CheckLot("east lot", S.Parcels[FString(T21_Pid)].Placement.GetValue(), T21_Lot);
		}

		CASE("Placement.InTheRoad");
		{
			const FClickResult A = ResolveClick(Board, Seed(), T22.X, T22.Y, T22.bPinsActive, V0Width);
			CheckBool("arterial ok", A.bOk, T22.bOk);
			CheckStr("arterial reason", A.Reason, FString(T22.Reason));
			const FClickResult C = ResolveClick(Board, Seed(), T23.X, T23.Y, T23.bPinsActive, V0Width);
			CheckBool("cross ok", C.bOk, T23.bOk);
			CheckStr("cross reason", C.Reason, FString(T23.Reason));
		}

		CASE("Placement.CrossingClick");
		for (int32 i = 0; i < T24CrossingNum; ++i)
		{
			const FClickCase& C = T24Crossing[i];
			const FClickResult Res = ResolveClick(Board, Seed(), C.X, C.Y, C.bPinsActive, V0Width);
			CheckBool("ok", Res.bOk, C.bOk);
			CheckStr("reason", Res.Reason, FString(C.Reason));
		}

		CASE("Placement.Snap");
		{
			for (int32 i = 0; i < SnapCasesNum; ++i)
			{
				CheckNear("snap", Snap(Board.Rules, SnapCases[i].In), SnapCases[i].Expected, Tol);
			}
			const FClickResult A = ResolveClick(Board, Seed(), SnapClick.X, SnapClick.Y, SnapClick.bPinsActive, V0Width);
			CheckBool("off-grid ok", A.bOk, SnapClick.bOk);
			CheckLot("off-grid lot", A.Lot, SnapClick.Lot);
			const FClickResult B = ResolveClick(Board, Seed(), SnapClickHalf.X, SnapClickHalf.Y, SnapClickHalf.bPinsActive, V0Width);
			CheckBool("half-case ok", B.bOk, SnapClickHalf.bOk);
			CheckLot("half-case lot", B.Lot, SnapClickHalf.Lot);
		}

		CASE("Placement.LotRoadId");
		for (int32 i = 0; i < T25Num; ++i)
		{
			CheckStr("road id", LotRoadId(LotFrom(T25_Lots[i])), FString(T25_Expected[i]));
		}

		CASE("Placement.OverlapOrder");
		{
			FCityState S = Seed();
			S.Parcels.Add(TEXT("B"), PlacedParcel(Board, OverlapLotB));
			S.Parcels.Add(TEXT("A"), PlacedParcel(Board, OverlapLotA));
			const FClickResult Res = ResolveClick(Board, S, OverlapAOnly.X, OverlapAOnly.Y,
				OverlapAOnly.bPinsActive, V0Width);
			CheckBool("refused", Res.bOk, OverlapAOnly.bOk);
			CheckStr("names the sorted-first lot", Res.Reason, FString(OverlapAOnly.Reason));
			CheckBool("not the insertion-first one",
				Res.Reason == FString(OverlapBOnly.Reason), false);
		}

		CASE("Placement.Corner");
		{
			FCityState S = Seed();
			S.Parcels.Add(TEXT("A"), PlacedParcel(Board, T27_Lot0));
			const FClickResult A = ResolveClick(Board, S, T27Cross.X, T27Cross.Y, T27Cross.bPinsActive, V0Width);
			CheckBool("cross click ok", A.bOk, T27Cross.bOk);
			CheckStr("cross click reason", A.Reason, FString(T27Cross.Reason));

			FCityState S2 = Seed();
			S2.Parcels.Add(TEXT("C"), PlacedParcel(Board, T27_Lot1));
			const FClickResult B = ResolveClick(Board, S2, T27Arterial.X, T27Arterial.Y, T27Arterial.bPinsActive, V0Width);
			CheckBool("arterial click ok", B.bOk, T27Arterial.bOk);
			CheckStr("arterial click reason", B.Reason, FString(T27Arterial.Reason));

			const FRoad* Art = FindRoad(Board.Roads, TEXT("arterial"));
			const FRoad* Crs = FindRoad(Board.Roads, TEXT("cross"));
			CheckBool("roads found", Art != nullptr && Crs != nullptr, true);
			if (Art != nullptr && Crs != nullptr)
			{
				const FLotRect R0 = LotRect(Board.Rules, *Art, LotFrom(T27_Lot0));
				CheckNear("R0 xmin", R0.XMin, T27_Rect0.XMin, Tol);
				CheckNear("R0 xmax", R0.XMax, T27_Rect0.XMax, Tol);
				CheckNear("R0 ymin", R0.YMin, T27_Rect0.YMin, Tol);
				CheckNear("R0 ymax", R0.YMax, T27_Rect0.YMax, Tol);
				const FLotRect R1 = LotRect(Board.Rules, *Crs, LotFrom(T27_Lot1));
				CheckNear("R1 xmin", R1.XMin, T27_Rect1.XMin, Tol);
				CheckNear("R1 xmax", R1.XMax, T27_Rect1.XMax, Tol);
				CheckNear("R1 ymin", R1.YMin, T27_Rect1.YMin, Tol);
				CheckNear("R1 ymax", R1.YMax, T27_Rect1.YMax, Tol);
			}
		}
	}

	// =====================================================================
	// STATE HANDOVER (Phase 1 step 3, Docs/STATE_HANDOVER.md Phase A).
	// The pure half only: ResolveStatePath, IsPoolLabel, FactsForLabel.
	// MirrorFromFile and AStacktownParcel need the engine and run on the Mac.
	// These expectations are HAND-WRITTEN, not oracle-generated - the Python
	// rules live in init_unreal.py, which imports `unreal` and cannot run here.
	// =====================================================================
	{
		auto Base = []() {
			FStatePathInputs In;
			In.DefaultStatePath = TEXT("/proj/Content/Python/citystate.json");
			In.TestStatePath    = TEXT("/proj/Content/Python/citystate_test.json");
			return In;
		};

		CASE("Handover.StatePathRules");
		{
			// The default is the owner's real file, unconditionally.
			FStatePathResolution R = ResolveStatePath(Base());
			CheckStr("default path", R.Path, FString("/proj/Content/Python/citystate.json"));
			CheckStr("default source", StateSourceName(R.Source), FString("default"));

			// Override wins over the lock and the marker both.
			FStatePathInputs Ov = Base();
			Ov.Override = TEXT("/somewhere/else.json");
			Ov.bStandalonePidAlive = true;
			Ov.bMarkerExists = true;
			Ov.MarkerContent = TEXT("/marker/path.json");
			R = ResolveStatePath(Ov);
			CheckStr("override path", R.Path, FString("/somewhere/else.json"));
			CheckStr("override source", StateSourceName(R.Source), FString("override"));

			// An editor session steps aside for a live standalone game...
			FStatePathInputs Lk = Base();
			Lk.bStandalonePidAlive = true;
			Lk.bIsGameProcess = false;
			R = ResolveStatePath(Lk);
			CheckStr("lock path", R.Path, Lk.TestStatePath);
			CheckStr("lock source", StateSourceName(R.Source), FString("standalone-lock"));

			// ...but the game process itself is the legitimate holder.
			FStatePathInputs Gp = Base();
			Gp.bStandalonePidAlive = true;
			Gp.bIsGameProcess = true;
			R = ResolveStatePath(Gp);
			CheckStr("game keeps the real file", R.Path, Gp.DefaultStatePath);
			CheckStr("and says default", StateSourceName(R.Source), FString("default"));

			// Marker content is the path, trimmed.
			FStatePathInputs Mk = Base();
			Mk.bMarkerExists = true;
			Mk.MarkerContent = TEXT("  /lane/own.json\n");
			R = ResolveStatePath(Mk);
			CheckStr("marker content", R.Path, FString("/lane/own.json"));
			CheckStr("marker source", StateSourceName(R.Source), FString("marker"));

			// Empty or whitespace-only means the test path, not an empty path.
			const char* Empties[] = { "", "   ", "\n\t " };
			for (int i = 0; i < 3; ++i)
			{
				FStatePathInputs E = Base();
				E.bMarkerExists = true;
				E.MarkerContent = FString(Empties[i]);
				R = ResolveStatePath(E);
				CheckStr("empty marker means test path", R.Path, E.TestStatePath);
				CheckStr("still marker", StateSourceName(R.Source), FString("marker"));
			}

			// The lock outranks the marker.
			FStatePathInputs Both = Base();
			Both.bStandalonePidAlive = true;
			Both.bMarkerExists = true;
			Both.MarkerContent = TEXT("/lane/own.json");
			R = ResolveStatePath(Both);
			CheckStr("lock beats marker", StateSourceName(R.Source), FString("standalone-lock"));
		}

		CASE("Handover.PoolLabels");
		{
			CheckBool("POOL_00", IsPoolLabel(TEXT("POOL_00")), true);
			CheckBool("POOL_PIN_NE0", IsPoolLabel(TEXT("POOL_PIN_NE0")), true);
			CheckBool("P1", IsPoolLabel(TEXT("P1")), false);
			CheckBool("NE0", IsPoolLabel(TEXT("NE0")), false);
			CheckBool("pool_00 lowercase", IsPoolLabel(TEXT("pool_00")), false);
		}

		CASE("Handover.PythonDrivers");
		{
			{
				FPythonDriversInputs In;
				In.bPluginLoaded = false;
				In.EnvValue = TEXT("1");
				In.bFoundInNewSection = true; In.bNewSectionValue = true;
				CheckBool("no plugin, no drivers", ResolvePythonDrivers(In), false);
			}
			const char* Offs[] = { "0", "false", "FALSE", "no" };
			for (int i = 0; i < 4; ++i)
			{
				FPythonDriversInputs In;
				In.EnvValue = FString(Offs[i]);
				In.bFoundInLegacySection = true; In.bLegacySectionValue = true;
				CheckBool("env turns them off", ResolvePythonDrivers(In), false);
			}
			{
				FPythonDriversInputs In;
				In.EnvValue = TEXT("1");
				In.bFoundInNewSection = true; In.bNewSectionValue = false;
				CheckBool("env beats the ini", ResolvePythonDrivers(In), true);
			}
			{
				FPythonDriversInputs In;
				In.bFoundInNewSection = true; In.bNewSectionValue = false;
				In.bFoundInLegacySection = true; In.bLegacySectionValue = true;
				CheckBool("new section wins", ResolvePythonDrivers(In), false);
			}
			{
				FPythonDriversInputs In;
				In.bFoundInLegacySection = true; In.bLegacySectionValue = false;
				CheckBool("legacy honoured", ResolvePythonDrivers(In), false);
			}
			{
				FPythonDriversInputs In;
				CheckBool("default on", ResolvePythonDrivers(In), true);
			}
		}

		CASE("Age.Advance");
		{
			{
				FParcelState P = Parcel(TEXT("vernacular"), 0, 820.0, false);
				AdvanceAge(P);
				CheckNear("unowned does not age", P.AgeTicks, 0.0, Tol);
				CheckBool("records no tier", P.AgeLastTier.IsSet(), false);
			}
			{
				FParcelState P = Parcel(TEXT("vernacular"), 0, 820.0, true);
				AdvanceAge(P);
				CheckNear("first advance resets", P.AgeTicks, 0.0, Tol);
				CheckBool("records the tier", P.AgeLastTier.IsSet(), true);
				AdvanceAge(P);
				CheckNear("second counts one", P.AgeTicks, 1.0, Tol);
				AdvanceAge(P);
				CheckNear("third counts two", P.AgeTicks, 2.0, Tol);
			}
			{
				FParcelState P = Parcel(TEXT("vernacular"), 0, 820.0, true);
				for (int32 i = 0; i < 40; ++i) { AdvanceAge(P); }
				CheckNear("aged", P.AgeTicks, 39.0, Tol);
				P.Tier = 1;
				AdvanceAge(P);
				CheckNear("a tier change resets", P.AgeTicks, 0.0, Tol);
				CheckInt("and records the new tier", P.AgeLastTier.GetValue(), 1);
				AdvanceAge(P);
				CheckNear("then counts again", P.AgeTicks, 1.0, Tol);
			}
		}

		CASE("Age.Fraction");
		{
			CheckNear("pale at zero", AgeFraction(0.0), 0.0, Tol);
			CheckNear("halfway", AgeFraction(75.0), 0.5, Tol);
			CheckNear("mature at the mark", AgeFraction(AgeMatureTicks), 1.0, Tol);
			CheckNear("saturates above", AgeFraction(1000.0), 1.0, Tol);
			CheckNear("the mark", AgeMatureTicks, 150.0, Tol);
		}

		CASE("Handover.FactsForLabel");
		{
			FCityState S = SeedState(R);
			S.Parcels.Add(TEXT("NE0"), Parcel(TEXT("vernacular"), 2, 1230.0, true, 7.5, true, -0.5));
			const FParcelFacts F = FactsForLabel(R, S, TEXT("NE0"));
			CheckBool("found", F.bFound, true);
			CheckStr("rid", F.Rid, FString("vernacular"));
			CheckNear("width", F.Width, 1230.0, Tol);
			CheckInt("tier", F.Tier, 2);
			CheckBool("owned", F.bOwned, true);
			CheckBool("failed", F.bFailed, true);
			CheckNear("accum", F.Accum, 7.5, Tol);
			CheckBool("not placed", F.bPlaced, false);
			// Recomputed from tier and width, never read from state.
			CheckNear("price", F.Price, Price(R, 2, 1230.0), Tol);

			const FParcelFacts Missing = FactsForLabel(R, S, TEXT("NOPE"));
			CheckBool("absent not found", Missing.bFound, false);
			CheckInt("absent carries no tier", Missing.Tier, 0);
		}
	}

	// =====================================================================
	// DRAWN ROADS (Phase 1 step 4) - placement.py self-tests 28-39, the pure
	// resolver only. The road world side (POOL_ROAD actors, _road_transform)
	// is the coordinator's engine work.
	// =====================================================================
	{
		using namespace StacktownRoadsOracle;
		const FPlacementBoard Board = OracleBoard();
		auto RoadSeed = [&R]() { return SeedState(R); };

		auto LotFrom2 = [](const FLotDef2& D) {
			FLotPlacement L;
			L.X0 = D.X0; L.X1 = D.X1; L.Side = FString(D.Side);
			if (D.RoadId != nullptr) { L.RoadId = FString(D.RoadId); }
			return L;
		};
		auto CheckSeg = [&](const char* What, const FString& GotId,
		                    const FRoadSegment& Got, const FSegDef& Want) {
			CheckStr(What, GotId, FString(Want.Id));
			CheckNear("start x", Got.StartX, Want.StartX, Tol);
			CheckNear("start y", Got.StartY, Want.StartY, Tol);
			CheckNear("end x", Got.EndX, Want.EndX, Tol);
			CheckNear("end y", Got.EndY, Want.EndY, Tol);
			CheckStr("width class", Got.WidthClass, FString(Want.WidthClass));
		};
		auto CheckDraw = [&](const char* What, const FCityState& S, const FDrawCase& C) {
			const FRoadDrawResult Res = ResolveRoadDraw(Board, S, C.X0, C.Y0, C.X1, C.Y1,
				FString("avenue"), C.bPinsActive);
			CheckBool(What, Res.bOk, C.bOk);
			CheckStr("reason", Res.Reason, FString(C.Reason));
			if (C.bOk && C.Road.Id != nullptr) { CheckSeg(What, Res.Id, Res.Segment, C.Road); }
		};

		CASE("Roads.LotRectReduces");
		{
			const FRoad* Art = FindRoad(Board.Roads, TEXT("arterial"));
			const FRoad* Crs = FindRoad(Board.Roads, TEXT("cross"));
			CheckBool("built-ins present", Art != nullptr && Crs != nullptr, true);
			if (Art != nullptr && Crs != nullptr)
			{
				const FLotRect A = LotRect(Board.Rules, *Art, LotFrom2(T28_Lot0));
				CheckNear("A xmin", A.XMin, T28_Rect0.XMin, Tol);
				CheckNear("A xmax", A.XMax, T28_Rect0.XMax, Tol);
				CheckNear("A ymin", A.YMin, T28_Rect0.YMin, Tol);
				CheckNear("A ymax", A.YMax, T28_Rect0.YMax, Tol);
				const FLotRect B = LotRect(Board.Rules, *Crs, LotFrom2(T28_Lot1));
				CheckNear("B xmin", B.XMin, T28_Rect1.XMin, Tol);
				CheckNear("B xmax", B.XMax, T28_Rect1.XMax, Tol);
				CheckNear("B ymin", B.YMin, T28_Rect1.YMin, Tol);
				CheckNear("B ymax", B.YMax, T28_Rect1.YMax, Tol);
			}
		}

		CASE("Roads.Orientation");
		for (int32 i = 0; i < T29OrientationNum; ++i)
		{
			const FOrientCase& C = T29Orientation[i];
			FRoadSegment Seg;
			Seg.StartX = C.Seg.StartX; Seg.StartY = C.Seg.StartY;
			Seg.EndX = C.Seg.EndX;     Seg.EndY = C.Seg.EndY;
			Seg.WidthClass = FString(C.Seg.WidthClass);
			const FRoad Road = RoadDictFromSegment(FString(C.Seg.Id), Seg);
			CheckStr("side_plus", Road.SidePlus, FString(C.SidePlus));
			CheckStr("side_minus", Road.SideMinus, FString(C.SideMinus));
			CheckBool("axis", Road.bAxisX, C.bAxisX);
		}

		CASE("Roads.AllRoads");
		{
			FCityState S = RoadSeed();
			TArray<FRoad> Before = Board.AllRoads(S);
			CheckInt("built-ins only", Before.Num(), T30_BeforeNum);
			for (int32 i = 0; i < T30_BeforeNum && i < Before.Num(); ++i)
			{
				CheckStr("before", Before[i].Id, FString(T30_Before[i]));
			}
			FRoadSegment Seg;
			Seg.StartX = T30_Drawn.StartX; Seg.StartY = T30_Drawn.StartY;
			Seg.EndX = T30_Drawn.EndX;     Seg.EndY = T30_Drawn.EndY;
			Seg.WidthClass = FString(T30_Drawn.WidthClass);
			S.Roads.Add(FString(T30_Drawn.Id), Seg);
			TArray<FRoad> After = Board.AllRoads(S);
			CheckInt("drawn joins", After.Num(), T30_AfterNum);
			for (int32 i = 0; i < T30_AfterNum && i < After.Num(); ++i)
			{
				CheckStr("after", After[i].Id, FString(T30_After[i]));
			}
		}

		CASE("Roads.IdOrder");
		{
			TArray<FString> Ids;
			Ids.Add(FString("R10")); Ids.Add(FString("R2"));
			Ids.Add(FString("R1"));  Ids.Add(FString("R11"));
			SortRoadIds(Ids);
			CheckStr("R1", Ids[0], FString("R1"));
			CheckStr("R2", Ids[1], FString("R2"));
			CheckStr("R10", Ids[2], FString("R10"));
			CheckStr("R11", Ids[3], FString("R11"));
		}

		CASE("Roads.DrawRules");
		{
			const FCityState S = RoadSeed();
			CheckDraw("happy horizontal", S, T31);
			CheckDraw("too diagonal", S, T32);
			CheckDraw("too short", S, T33);
			CheckDraw("off board", S, T34);
			CheckDraw("crosses a built-in", S, T35);
			CheckDraw("crosses a pin", S, T36);
			CheckDraw("empty mode accepts", S, T36b);
			CheckDraw("happy vertical", S, T37);
			// The minor coordinate comes from the START point.
			CheckDraw("near horizontal", S, NearHorizontal);
			CheckDraw("near vertical", S, NearVertical);
		}

		CASE("Roads.DrawRoad");
		{
			FCityState S = RoadSeed();
			const FRoadDrawResult First = DrawRoad(Board, S, T31.X0, T31.Y0, T31.X1, T31.Y1,
				FString("avenue"), true);
			CheckBool("first ok", First.bOk, true);
			CheckStr("first id", First.Id, FString(T38_FirstId));
			CheckSeg("stored R1", First.Id, S.Roads[First.Id], T38_FirstStored);
			CheckDraw("crosses R1", S, T38_CrossesR1);
			const FRoadDrawResult Second = DrawRoad(Board, S, T37.X0, T37.Y0, T37.X1, T37.Y1,
				FString("avenue"), true);
			CheckBool("second ok", Second.bOk, true);
			CheckStr("second id", Second.Id, FString(T38_SecondId));
			CheckSeg("stored R2", Second.Id, S.Roads[Second.Id], T38_SecondStored);
			CheckInt("two roads", S.Roads.Num(), T38_IdsNum);
			const int32 Before = S.Roads.Num();
			DrawRoad(Board, S, T32.X0, T32.Y0, T32.X1, T32.Y1, FString("avenue"), true);
			CheckInt("a refused draw stores nothing", S.Roads.Num(), Before);
		}

		CASE("Roads.PlaceAgainstDrawn");
		{
			FCityState S = RoadSeed();
			const FRoadDrawResult Drawn = DrawRoad(Board, S, T31.X0, T31.Y0, T31.X1, T31.Y1,
				FString("avenue"), true);
			CheckBool("road drawn", Drawn.bOk, true);
			const FPlaceResult P = Place(Board, S, T39_ClickX, T39_ClickY, true, Board.Rules.V0Width);
			CheckBool("placed", P.bOk, T39_Ok);
			CheckStr("pid", P.Pid, FString(T39_Pid));
			const FLotPlacement& Lot = S.Parcels[FString(T39_Pid)].Placement.GetValue();
			CheckNear("x0", Lot.X0, T39_Lot.X0, Tol);
			CheckNear("x1", Lot.X1, T39_Lot.X1, Tol);
			CheckStr("side", Lot.Side, FString(T39_Lot.Side));
			CheckStr("road id", LotRoadId(Lot), FString(T39_Lot.RoadId));
			const TArray<FRoad> Roads = Board.AllRoads(S);
			const FRoad* R1 = FindRoad(Roads, LotRoadId(Lot));
			CheckBool("drawn road is a candidate", R1 != nullptr, true);
			if (R1 != nullptr)
			{
				const FLotRect Rect = LotRect(Board.Rules, *R1, Lot);
				CheckNear("rect xmin", Rect.XMin, T39_Rect.XMin, Tol);
				CheckNear("rect xmax", Rect.XMax, T39_Rect.XMax, Tol);
				CheckNear("rect ymin", Rect.YMin, T39_Rect.YMin, Tol);
				CheckNear("rect ymax", Rect.YMax, T39_Rect.YMax, Tol);
			}
		}
	}

	// =====================================================================
	// THE RUNTIME BOARD (queue item 1). FPlacementBoard::Default() is
	// PRODUCTION data generated from citylayout, not a test fixture - so the
	// interesting assertion is that it AGREES with the fixture the ported
	// refusal logic was proved against.
	// =====================================================================
	{
		const FPlacementBoard Real = FPlacementBoard::Default();
		const FPlacementBoard Fixture = OracleBoard();

		CASE("Board.Default");
		{
			CheckInt("two roads", Real.Roads.Num(), StacktownPlacementOracle::RoadsNum);
			CheckInt("fourteen pins", Real.PinnedSpans.Num(), StacktownPlacementOracle::PinnedSpansNum);
			CheckNear("plate x min", Real.PlateXMin, StacktownPlacementOracle::PlateXMin, Tol);
			CheckNear("plate x max", Real.PlateXMax, StacktownPlacementOracle::PlateXMax, Tol);
			CheckNear("v0 width", Real.Rules.V0Width, StacktownPlacementOracle::V0Width, Tol);
			CheckInt("pool size", Real.Rules.PoolSize, StacktownPlacementOracle::PoolSize);
			CheckStr("v0 recipe", Real.Rules.V0Recipe, FString(StacktownPlacementOracle::V0Recipe));
			for (int32 i = 0; i < Real.PinnedSpans.Num(); ++i)
			{
				CheckBool("span has a key", !Real.PinnedSpans[i].Key.IsEmpty(), true);
			}
		}

		CASE("Board.MatchesOracle");
		{
			CheckInt("same road count", Real.Roads.Num(), Fixture.Roads.Num());
			for (int32 i = 0; i < Real.Roads.Num() && i < Fixture.Roads.Num(); ++i)
			{
				CheckStr("road id", Real.Roads[i].Id, Fixture.Roads[i].Id);
				CheckNear("start x", Real.Roads[i].StartX, Fixture.Roads[i].StartX, Tol);
				CheckNear("start y", Real.Roads[i].StartY, Fixture.Roads[i].StartY, Tol);
				CheckNear("end x", Real.Roads[i].EndX, Fixture.Roads[i].EndX, Tol);
				CheckNear("end y", Real.Roads[i].EndY, Fixture.Roads[i].EndY, Tol);
				CheckStr("side plus", Real.Roads[i].SidePlus, Fixture.Roads[i].SidePlus);
				CheckBool("axis", Real.Roads[i].bAxisX, Fixture.Roads[i].bAxisX);
			}
			CheckInt("same span count", Real.PinnedSpans.Num(), Fixture.PinnedSpans.Num());
			for (int32 i = 0; i < Fixture.PinnedSpans.Num(); ++i)
			{
				const FPinnedSpan& Want = Fixture.PinnedSpans[i];
				bool bFound = false;
				for (int32 j = 0; j < Real.PinnedSpans.Num(); ++j)
				{
					const FPinnedSpan& Got = Real.PinnedSpans[j];
					if (FMath::Abs(Got.X0 - Want.X0) < 1e-9 && FMath::Abs(Got.X1 - Want.X1) < 1e-9
						&& Got.Side == Want.Side) { bFound = true; break; }
				}
				CheckBool("factory carries the fixture's span", bFound, true);
			}
		}

		CASE("Board.PinnedPose");
		{
			const FCityState Empty;
			const TArray<FRoad> Roads = Real.AllRoads(Empty);
			int32 Posed = 0;
			for (int32 i = 0; i < Real.PinnedSpans.Num(); ++i)
			{
				const FPinnedSpan& Span = Real.PinnedSpans[i];
				FLotPlacement Lot;
				CheckBool("key resolves", PinnedPlacementForKey(Real, Span.Key, Lot), true);
				CheckNear("x0", Lot.X0, Span.X0, Tol);
				CheckNear("x1", Lot.X1, Span.X1, Tol);
				CheckStr("side", Lot.Side, Span.Side);
				CheckStr("road", LotRoadId(Lot), FString("arterial"));

				LotFrame::FPose Pose;
				const bool bPosed = LotFrame::Pose(Lot, Roads, Pose);
				CheckBool("poses", bPosed, true);
				if (!bPosed) { continue; }
				++Posed;
				const double Expected = LotFrame::RoadHalf + LotFrame::BlockDepth * 0.5;
				if (Span.Side == FString("north"))
				{
					CheckNear("pad x", Pose.X, Span.X0, Tol);
					CheckNear("pad y", Pose.Y, Expected, Tol);
					CheckNear("yaw", Pose.Yaw, 0.0, Tol);
				}
				else
				{
					CheckNear("pad x", Pose.X, Span.X1, Tol);
					CheckNear("pad y", Pose.Y, -Expected, Tol);
					CheckNear("yaw", Pose.Yaw, 180.0, Tol);
				}
			}
			CheckInt("all fourteen posed", Posed, Real.PinnedSpans.Num());
			FLotPlacement Nope;
			CheckBool("unknown key resolves nothing",
				PinnedPlacementForKey(Real, TEXT("NOPE"), Nope), false);
		}

		CASE("Board.PinsRefuse");
		{
			// TemporaryBoard carried no pins, so the C++ game accepted clicks on
			// pinned frontage the Python refuses. With the factory in, it does not.
			const FCityState S = SeedState(R);
			const FClickResult Refused = ResolveClick(Real, S, 2360.0, 1500.0, true, Real.Rules.V0Width);
			CheckBool("refused", Refused.bOk, false);
			CheckBool("says pinned lot",
				Refused.Reason.S.find("pinned lot") != std::string::npos, true);
			const FClickResult Accepted = ResolveClick(Real, S, 2360.0, 1500.0, false, Real.Rules.V0Width);
			CheckBool("empty mode still accepts", Accepted.bOk, true);
		}
	}

	printf("\n%s: %d checks, %d failures\n",
		gFailures == 0 ? "PRE-FLIGHT PASS (shim, NOT Unreal)" : "PRE-FLIGHT FAIL",
		gChecks, gFailures);
	return gFailures == 0 ? 0 : 1;
}
