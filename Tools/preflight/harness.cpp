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
		S.Demand = StacktownOracle::TickMulti_DemandStart;   // the scenario STARTS at 1.5; TickMulti_Demand is where the oracle left it
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
			const FRoad* Got = ResolveRoad(Board.Rules, Board.Econ, Roads, C.X, C.Y, Local);
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
				const FLotRect R0 = LotRect(Board.Rules, Board.Econ, *Art, LotFrom(T27_Lot0));
				CheckNear("R0 xmin", R0.XMin, T27_Rect0.XMin, Tol);
				CheckNear("R0 xmax", R0.XMax, T27_Rect0.XMax, Tol);
				CheckNear("R0 ymin", R0.YMin, T27_Rect0.YMin, Tol);
				CheckNear("R0 ymax", R0.YMax, T27_Rect0.YMax, Tol);
				const FLotRect R1 = LotRect(Board.Rules, Board.Econ, *Crs, LotFrom(T27_Lot1));
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
		// GeometryMoney: roads cost money since road types, and a case about
		// geometry must not refuse for want of a balance. The oracle funded its
		// own states with the same number; the PRICE is checked on its own.
		auto RoadSeed = [&R]() { FCityState S = SeedState(R); S.Money = GeometryMoney; return S; };

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
				const FLotRect A = LotRect(Board.Rules, Board.Econ, *Art, LotFrom2(T28_Lot0));
				CheckNear("A xmin", A.XMin, T28_Rect0.XMin, Tol);
				CheckNear("A xmax", A.XMax, T28_Rect0.XMax, Tol);
				CheckNear("A ymin", A.YMin, T28_Rect0.YMin, Tol);
				CheckNear("A ymax", A.YMax, T28_Rect0.YMax, Tol);
				const FLotRect B = LotRect(Board.Rules, Board.Econ, *Crs, LotFrom2(T28_Lot1));
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
			// WAS "too diagonal", until item 11 removed that refusal; these
			// coordinates start on the cross street and refuse for that.
			CheckDraw("starts on the cross street", S, T32);
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
				const FLotRect Rect = LotRect(Board.Rules, Board.Econ, *R1, Lot);
				CheckNear("rect xmin", Rect.XMin, T39_Rect.XMin, Tol);
				CheckNear("rect xmax", Rect.XMax, T39_Rect.XMax, Tol);
				CheckNear("rect ymin", Rect.YMin, T39_Rect.YMin, Tol);
				CheckNear("rect ymax", Rect.YMax, T39_Rect.YMax, Tol);
			}
		}
	}


	// =====================================================================
	// ROAD TYPES AS MECHANICS (queue item 10, MONDAY_DECISIONS section 2).
	// placement.py self-tests 40-48. The type is the width class the segment
	// already carried; every number is econrules.json's, so the owner retunes
	// the table without a recompile.
	// =====================================================================
	{
		using namespace StacktownRoadsOracle;
		const FPlacementBoard Board = OracleBoard();
		auto RoadSeed = [&R]() { FCityState S = SeedState(R); S.Money = GeometryMoney; return S; };
		auto SegOf = [](const FSegDef& D) {
			FRoadSegment S;
			S.StartX = D.StartX; S.StartY = D.StartY; S.EndX = D.EndX; S.EndY = D.EndY;
			if (D.WidthClass != nullptr) { S.WidthClass = FString(D.WidthClass); }
			return S;
		};

		CASE("Roads.TypeRulesMatchOracle");
		{
			// THE COMPILED DEFAULT, checked against the owner's file. FEconRules
			// ships the table it parses so a board built without a ruleset still
			// measures the city; this is what stops that default going stale.
			const TMap<FString, FRoadTypeRules> Shipped = DefaultRoadTypes();
			const TArray<FString>& Names = RoadTypeNames();
			CheckInt("four types", Names.Num(), OracleTypeNamesNum);
			CheckStr("default type", FString(DefaultRoadType()), FString(OracleDefaultType));
			for (int32 i = 0; i < OracleTypeNamesNum; ++i)
			{
				CheckStr("type name in order", Names[i], FString(OracleTypeNames[i]));
			}
			for (int32 i = 0; i < T40_TypesNum; ++i)
			{
				const FTypeRow& Row = T40_Types[i];
				const FRoadTypeRules* T = Shipped.Find(FString(Row.Type));
				CheckBool("shipped table has the type", T != nullptr, true);
				if (T == nullptr) { continue; }
				CheckNear("cost per 100uu", T->CostPer100uu, Row.CostPer100uu, Tol);
				CheckNear("rent mult", T->RentMult, Row.RentMult, Tol);
				CheckNear("carriageway", T->Width, Row.Width, Tol);
				CheckBool("frontage", T->bFrontage, Row.bFrontage);
			}
		}

		CASE("Roads.TypeGeometry");
		{
			// 40: the per-type corridor, and the reduction that makes this change
			// safe - an avenue, and a road with NO type at all, are exactly the
			// constants the board was authored against.
			CheckNear("verge", Board.Rules.Verge, Verge, Tol);
			for (int32 i = 0; i < T40_TypesNum; ++i)
			{
				const FTypeRow& Row = T40_Types[i];
				FRoad Probe;
				Probe.WidthClass = FString(Row.Type);
				CheckStr("type of", RoadTypeOf(Probe), FString(Row.Type));
				CheckNear("half", RoadHalf(Board.Rules, Board.Econ, Probe), Row.Half, Tol);
				CheckNear("max reach", RoadMaxReach(Board.Rules, Board.Econ, Probe), Row.MaxReach, Tol);
				CheckNear("corridor", RoadCorridor(Board.Rules, Board.Econ, Probe.WidthClass), 2.0 * Row.Half, Tol);
				CheckBool("frontage", RoadHasFrontage(Board.Econ, Probe), Row.bFrontage);
				CheckStr("material", RoadMaterialName(Probe.WidthClass), FString(Row.Material));
			}
			const FRoad* Arterial = FindRoad(Board.Roads, FString(TEXT("arterial")));
			CheckBool("arterial found", Arterial != nullptr, true);
			if (Arterial != nullptr)
			{
				CheckStr("no width class means avenue", RoadTypeOf(*Arterial), FString(OracleDefaultType));
				CheckNear("untyped half is the constant", RoadHalf(Board.Rules, Board.Econ, *Arterial), T40_UntypedHalf, Tol);
				CheckNear("untyped half IS RoadHalf", RoadHalf(Board.Rules, Board.Econ, *Arterial), Board.Rules.RoadHalf, Tol);
				CheckNear("untyped reach is the constant", RoadMaxReach(Board.Rules, Board.Econ, *Arterial), T40_UntypedReach, Tol);
				CheckNear("untyped reach IS RoadMaxReach", RoadMaxReach(Board.Rules, Board.Econ, *Arterial), Board.Rules.RoadMaxReach, Tol);
			}
		}

		CASE("Roads.TypeCost");
		{
			// 41: price is derived from type and geometry, never stored.
			for (int32 i = 0; i < T40_TypesNum; ++i)
			{
				const FTypeRow& Row = T40_Types[i];
				FRoadSegment S;
				S.EndX = 1400.0;
				S.WidthClass = FString(Row.Type);
				CheckNear("length", RoadLength(S), 1400.0, Tol);
				double Cost = 0.0;
				CheckBool("priced", RoadCost(Board.Econ, S, Cost), true);
				CheckNear("cost of 1400 uu", Cost, Row.Cost1400, Tol);
			}
			// A vertical run prices identically to a horizontal one of the span.
			double VCost = 0.0;
			CheckNear("vertical length", RoadLength(SegOf(T41_VerticalSeg)), T41_VerticalLength, Tol);
			CheckBool("vertical priced", RoadCost(Board.Econ, SegOf(T41_VerticalSeg), VCost), true);
			CheckNear("vertical cost", VCost, T40_Types[1].Cost1400, Tol);
			double SCost = 0.0;
			CheckBool("short dirt priced", RoadCost(Board.Econ, SegOf(T41_ShortDirtSeg), SCost), true);
			CheckNear("short dirt cost", SCost, T41_ShortDirtCost, Tol);
		}

		CASE("Roads.HighwayRefusesFrontage");
		{
			// 42: the SAME segment as a highway and as an avenue, and one click.
			FCityState S = RoadSeed();
			const FRoadDrawResult D = DrawRoad(Board, S, T42_Seg[0], T42_Seg[1], T42_Seg[2], T42_Seg[3],
				FString(T42_HighwayStored.WidthClass), true);
			CheckBool("highway drawn", D.bOk, true);
			CheckStr("stored class", S.Roads[D.Id].WidthClass, FString(T42_HighwayStored.WidthClass));
			CheckNear("money after", S.Money, T42_MoneyAfterHighway, Tol);

			const FClickResult Beside = ResolveClick(Board, S, T42_BesideHighway.X, T42_BesideHighway.Y,
				T42_BesideHighway.bPinsActive, Board.Rules.V0Width);
			CheckBool("refused", Beside.bOk, T42_BesideHighway.bOk);
			CheckStr("reason names the type", Beside.Reason, FString(T42_BesideHighway.Reason));

			FCityState A = RoadSeed();
			const FRoadDrawResult AD = DrawRoad(Board, A, T42_Seg[0], T42_Seg[1], T42_Seg[2], T42_Seg[3],
				FString(TEXT("avenue")), true);
			CheckBool("avenue drawn", AD.bOk, true);
			const FClickResult OnAvenue = ResolveClick(Board, A, T42_BesideAvenue.X, T42_BesideAvenue.Y,
				T42_BesideAvenue.bPinsActive, Board.Rules.V0Width);
			CheckBool("the identical click places", OnAvenue.bOk, T42_BesideAvenue.bOk);
			CheckNear("x0", OnAvenue.Lot.X0, T42_BesideAvenue.Lot.X0, Tol);
			CheckNear("x1", OnAvenue.Lot.X1, T42_BesideAvenue.Lot.X1, Tol);
			CheckStr("side", OnAvenue.Lot.Side, FString(T42_BesideAvenue.Lot.Side));
			CheckStr("road", LotRoadId(OnAvenue.Lot), FString(T42_BesideAvenue.Lot.RoadId));

			// 'no frontage' is bounded by the highway's OWN reach, not board-wide.
			const FClickResult Far = ResolveClick(Board, S, T42_FarFromEverything.X, T42_FarFromEverything.Y,
				T42_FarFromEverything.bPinsActive, Board.Rules.V0Width);
			CheckBool("far refused", Far.bOk, T42_FarFromEverything.bOk);
			CheckStr("far reason is off-board", Far.Reason, FString(T42_FarFromEverything.Reason));

			// 43: and nothing may be laid ACROSS one.
			const FClickResult Across = ResolveClick(Board, S, T43_WithHighway.X, T43_WithHighway.Y,
				T43_WithHighway.bPinsActive, Board.Rules.V0Width);
			CheckBool("across refused", Across.bOk, T43_WithHighway.bOk);
			CheckStr("across reason", Across.Reason, FString(T43_WithHighway.Reason));
			FCityState Bare = RoadSeed();
			const FClickResult Control = ResolveClick(Board, Bare, T43_Without.X, T43_Without.Y,
				T43_Without.bPinsActive, Board.Rules.V0Width);
			CheckBool("the same click without a highway places", Control.bOk, T43_Without.bOk);
			CheckStr("control road", LotRoadId(Control.Lot), FString(T43_Without.Lot.RoadId));
		}

		CASE("Roads.Afford");
		{
			// 44: on a state left at money_start deliberately.
			FEconRules Rules = OracleRules();
			FCityState S = SeedState(Rules);
			CheckNear("money_start", S.Money, T44_MoneyStart, Tol);
			const FRoadDrawResult Quote = ResolveRoadDraw(Board, S, T44_AvenueRefused.X0, T44_AvenueRefused.Y0,
				T44_AvenueRefused.X1, T44_AvenueRefused.Y1, FString(T44_AvenueClass), T44_AvenueRefused.bPinsActive);
			CheckBool("avenue refused", Quote.bOk, T44_AvenueRefused.bOk);
			CheckStr("reason", Quote.Reason, FString(T44_AvenueRefused.Reason));
			const FRoadDrawResult Tried = DrawRoad(Board, S, T44_AvenueRefused.X0, T44_AvenueRefused.Y0,
				T44_AvenueRefused.X1, T44_AvenueRefused.Y1, FString(T44_AvenueClass), T44_AvenueRefused.bPinsActive);
			CheckBool("draw refused too", Tried.bOk, false);
			CheckNear("a refusal spends nothing", S.Money, T44_MoneyAfterRefusal, Tol);
			CheckInt("and adds no road", S.Roads.Num(), 0);
			const FRoadDrawResult Dirt = DrawRoad(Board, S, T44_AvenueRefused.X0, T44_AvenueRefused.Y0,
				T44_AvenueRefused.X1, T44_AvenueRefused.Y1, FString(T44_DirtStored.WidthClass),
				T44_AvenueRefused.bPinsActive);
			CheckBool("the same road as dirt draws", Dirt.bOk, true);
			CheckStr("dirt id", Dirt.Id, FString(T44_DirtStored.Id));
			CheckStr("dirt stored class", S.Roads[Dirt.Id].WidthClass, FString(T44_DirtStored.WidthClass));
			CheckNear("money after", S.Money, T44_MoneyAfter, Tol);
		}

		CASE("Roads.NarrowerFrontage");
		{
			// 45: a dirt road's own corridor and its own frontage line.
			FCityState S = RoadSeed();
			const FRoadDrawResult D = DrawRoad(Board, S, T44_AvenueRefused.X0, T44_AvenueRefused.Y0,
				T44_AvenueRefused.X1, T44_AvenueRefused.Y1, FString(T44_DirtStored.WidthClass), true);
			CheckBool("dirt drawn", D.bOk, true);
			const FLotRect RoadR = RoadRect(Board.Rules, Board.Econ,
				RoadDictFromSegment(D.Id, S.Roads[D.Id]));
			CheckNear("road rect ymin", RoadR.YMin, T45_DirtRoadRect.YMin, Tol);
			CheckNear("road rect ymax", RoadR.YMax, T45_DirtRoadRect.YMax, Tol);
			const FPlaceResult P = Place(Board, S, T45_ClickX, T45_ClickY, true, Board.Rules.V0Width);
			CheckBool("placed", P.bOk, true);
			const FLotPlacement& Lot = S.Parcels[P.Pid].Placement.GetValue();
			CheckStr("side", Lot.Side, FString(T45_Lot.Side));
			CheckStr("road", LotRoadId(Lot), FString(T45_Lot.RoadId));
			const TArray<FRoad> Roads = Board.AllRoads(S);
			const FRoad* Own = FindRoad(Roads, LotRoadId(Lot));
			CheckBool("own road found", Own != nullptr, true);
			if (Own != nullptr)
			{
				const FLotRect Rect = LotRect(Board.Rules, Board.Econ, *Own, Lot);
				CheckNear("lot rect ymin", Rect.YMin, T45_LotRect.YMin, Tol);
				CheckNear("lot rect ymax", Rect.YMax, T45_LotRect.YMax, Tol);
			}
		}

		CASE("Roads.RentMultiplier");
		{
			// 46: own type, then the highway's proximity bonus, which MULTIPLIES
			// and is measured pavement to pad.
			CheckNear("highway reach", Board.Econ.RoadHighwayReach, HighwayReach, Tol);
			FLotPlacement Lot;
			Lot.X0 = T46_Lot.X0; Lot.X1 = T46_Lot.X1;
			Lot.Side = FString(T46_Lot.Side);
			Lot.RoadId = FString(T46_Lot.RoadId);
			for (int32 i = 0; i < T46_CasesNum; ++i)
			{
				const FRentCase& C = T46_Cases[i];
				FCityState S;
				FRoadSegment D;
				D.StartX = 6200.0; D.StartY = 3000.0; D.EndX = 7600.0; D.EndY = 3000.0;
				D.WidthClass = FString(C.Own);
				S.Roads.Add(FString(TEXT("D")), D);
				if (C.Highway != nullptr)
				{
					const FSegDef& H = FString(C.Highway) == FString(TEXT("near"))
						? T46_NearHighway : T46_FarHighway;
					S.Roads.Add(FString(TEXT("HW")), SegOf(H));
				}
				CheckNear("multiplier", RoadRentMultiplier(Board, S, Lot), C.Mult, Tol);
			}
			// The near miss the reach is bounded by: 2120 against a 2000 reach.
			const FLotRect LotR = { T46_DirtLotRect.XMin, T46_DirtLotRect.XMax,
				T46_DirtLotRect.YMin, T46_DirtLotRect.YMax };
			CheckNear("far distance", RectDistance(LotR,
				RoadRect(Board.Rules, Board.Econ, RoadDictFromSegment(FString(TEXT("HW")), SegOf(T46_FarHighway)))),
				T46_FarDistance, Tol);
		}

		CASE("Roads.UnknownType");
		{
			// 47: refused at the boundary with a reason, nothing spent, no road.
			FCityState S = RoadSeed();
			const double Before = S.Money;
			const FRoadDrawResult D = DrawRoad(Board, S, T47_Unknown.X0, T47_Unknown.Y0,
				T47_Unknown.X1, T47_Unknown.Y1, FString(T47_Class), T47_Unknown.bPinsActive);
			CheckBool("refused", D.bOk, T47_Unknown.bOk);
			CheckStr("reason", D.Reason, FString(T47_Unknown.Reason));
			CheckNear("nothing spent", S.Money, Before, Tol);
			CheckInt("no road added", S.Roads.Num(), 0);
		}

		CASE("Roads.DragDirection");
		{
			// 49: which way the player dragged must not matter, and until the
			// endpoint ordering landed it did - a road drawn right to left put
			// every lot at 2 * StartX - X, a mirror about the start point, and
			// flipped its side name with it. BOTH orders are run against the
			// ONE expected answer; a fixture with two answers would be
			// recording the bug.
			for (int32 i = 0; i < T49_DragNum; ++i)
			{
				const FDragCase& C = T49_Drag[i];
				for (int32 Order = 0; Order < 2; ++Order)
				{
					const double AX = Order == 0 ? C.FX0 : C.FX1;
					const double AY = Order == 0 ? C.FY0 : C.FY1;
					const double BX = Order == 0 ? C.FX1 : C.FX0;
					const double BY = Order == 0 ? C.FY1 : C.FY0;
					FCityState S = RoadSeed();
					const FRoadDrawResult D = DrawRoad(Board, S, AX, AY, BX, BY,
						FString(TEXT("avenue")), true);
					CheckBool("road drawn", D.bOk, true);
					if (!D.bOk) { continue; }
					const FRoadSegment& Seg = S.Roads[D.Id];
					CheckNear("segment start x", Seg.StartX, C.Segment.StartX, Tol);
					CheckNear("segment start y", Seg.StartY, C.Segment.StartY, Tol);
					CheckNear("segment end x", Seg.EndX, C.Segment.EndX, Tol);
					CheckNear("segment end y", Seg.EndY, C.Segment.EndY, Tol);
					CheckNear("money", S.Money, C.Money, Tol);
					const FPlaceResult Pl = Place(Board, S, C.ClickX, C.ClickY, true, Board.Rules.V0Width);
					CheckBool("lot placed", Pl.bOk, true);
					if (!Pl.bOk) { continue; }
					const FLotPlacement& Lot = S.Parcels[Pl.Pid].Placement.GetValue();
					CheckNear("lot x0", Lot.X0, C.Lot.X0, Tol);
					CheckNear("lot x1", Lot.X1, C.Lot.X1, Tol);
					CheckStr("lot side", Lot.Side, FString(C.Lot.Side));
					CheckStr("lot road", LotRoadId(Lot), FString(C.Lot.RoadId));
				}
			}
		}

		CASE("Roads.CrossingUsesOwnHalf");
		{
			// 48: a point 1300 uu from a centreline is ON a highway (half 1430)
			// and NOT on an avenue (half 1130) - so whether it is shared pavement
			// depends on the type. Direct, on a hand-built road list: no state
			// reachable through DrawRoad can have two corridors sharing ground.
			const FRoad* Arterial = FindRoad(Board.Roads, FString(TEXT("arterial")));
			const FRoad* Cross = FindRoad(Board.Roads, FString(TEXT("cross")));
			CheckBool("built-ins found", Arterial != nullptr && Cross != nullptr, true);
			if (Arterial == nullptr || Cross == nullptr) { }
			else
			{
				const FRoad Hw = RoadDictFromSegment(FString(TEXT("HW")), SegOf(T48_Segment));
				FRoadSegment AvSeg = SegOf(T48_Segment);
				AvSeg.WidthClass = FString(TEXT("avenue"));
				const FRoad Av = RoadDictFromSegment(FString(TEXT("HW")), AvSeg);
				TArray<FRoad> WithHw; WithHw.Add(*Arterial); WithHw.Add(Hw);
				TArray<FRoad> WithAv; WithAv.Add(*Arterial); WithAv.Add(Av);
				CheckBool("on a highway's pavement", InCrossing(Board.Rules, Board.Econ, WithHw, T48_X, T48_Y), T48_Highway);
				CheckBool("not on an avenue's", InCrossing(Board.Rules, Board.Econ, WithAv, T48_X, T48_Y), T48_Avenue);
				TArray<FRoad> BuiltIns; BuiltIns.Add(*Arterial); BuiltIns.Add(*Cross);
				CheckBool("the built-in crossing is still a crossing",
					InCrossing(Board.Rules, Board.Econ, BuiltIns, 0.0, 0.0), T48_BuiltinsAtOrigin);
			}
		}
	}

	// =====================================================================
	// ROADS AT ANY DIRECTION (queue item 11, first half). placement.py
	// self-tests 50-55. The resolver works in PROJECTION space, lot and road
	// footprints are quads with a separating-axis test, and side names come
	// off the normal - all of which reduce EXACTLY to the axis-aligned
	// answers above, which is the check that matters.
	// =====================================================================
	{
		using namespace StacktownRoadsOracle;
		const FPlacementBoard Board = OracleBoard();
		auto RoadSeed = [&R]() { FCityState S = SeedState(R); S.Money = GeometryMoney; return S; };
		auto LotOf = [](const FLotDef2& D) {
			FLotPlacement L;
			L.X0 = D.X0; L.X1 = D.X1; L.Side = FString(D.Side);
			if (D.RoadId != nullptr) { L.RoadId = FString(D.RoadId); }
			return L;
		};
		auto RoadOf = [&Board](const FCityState& S, const FString& Id) {
			const TArray<FRoad> Rs = Board.AllRoads(S);
			return *FindRoad(Rs, Id);
		};

		CASE("Roads.DiagonalAccepted");
		{
			// 32b/33b: the "too diagonal" refusal is gone, and a diagonal is
			// measured along its CENTRELINE - 500 by 500 is 707 uu, under the
			// 820 a lot needs, where the sum of the deltas would say 1000.
			FCityState S = RoadSeed();
			const FRoadDrawResult D = ResolveRoadDraw(Board, S, T32b_Diagonal.X0,
				T32b_Diagonal.Y0, T32b_Diagonal.X1, T32b_Diagonal.Y1,
				FString(TEXT("avenue")), T32b_Diagonal.bPinsActive);
			CheckBool("a 45 degree road draws", D.bOk, T32b_Diagonal.bOk);
			CheckNear("start x kept", D.Segment.StartX, T32b_Diagonal.Road.StartX, Tol);
			CheckNear("start y kept", D.Segment.StartY, T32b_Diagonal.Road.StartY, Tol);
			CheckNear("end x not pulled onto an axis", D.Segment.EndX, T32b_Diagonal.Road.EndX, Tol);
			CheckNear("end y not pulled onto an axis", D.Segment.EndY, T32b_Diagonal.Road.EndY, Tol);
			const FRoadDrawResult Sh = ResolveRoadDraw(Board, S, T33b_DiagonalTooShort.X0,
				T33b_DiagonalTooShort.Y0, T33b_DiagonalTooShort.X1, T33b_DiagonalTooShort.Y1,
				FString(TEXT("avenue")), T33b_DiagonalTooShort.bPinsActive);
			CheckBool("707 uu is too short", Sh.bOk, T33b_DiagonalTooShort.bOk);
			CheckStr("and says 707", Sh.Reason, FString(T33b_DiagonalTooShort.Reason));
		}

		CASE("Roads.QuadsReduceToRects");
		{
			// 50: not an argument about separating axes - the two functions run
			// against each other on real lot geometry, including a pair that
			// only TOUCHES, which must be a miss.
			FCityState S = RoadSeed();
			for (int32 i = 0; i < T50_PairsNum; ++i)
			{
				const FQuadPair& C = T50_Pairs[i];
				const FLotPlacement A = LotOf(C.A), B2 = LotOf(C.B);
				const FRoad RA = RoadOf(S, LotRoadId(A));
				const FRoad RB = RoadOf(S, LotRoadId(B2));
				const FQuad QA = LotQuad(Board.Rules, Board.Econ, RA, A);
				const FQuad QB = LotQuad(Board.Rules, Board.Econ, RB, B2);
				CheckBool("quads agree with the oracle", QuadsOverlap(QA, QB), C.bQuads);
				CheckBool("rects agree with the oracle",
					RectsOverlap(LotRect(Board.Rules, Board.Econ, RA, A),
						LotRect(Board.Rules, Board.Econ, RB, B2)), C.bRects);
				CheckBool("and with each other", QuadsOverlap(QA, QB), C.bRects);
			}
		}

		CASE("Roads.ProjectionIdentity");
		{
			// 51: S0 + Along IS the world coordinate for both built-ins, which
			// is why no lot already saved changes meaning.
			FCityState S = RoadSeed();
			for (int32 i = 0; i < T51_ProjectionNum; ++i)
			{
				const FProjCase& C = T51_Projection[i];
				const FRoad Road = RoadOf(S, FString(C.Road));
				const FRoadFrame F = RoadFrameOf(Road);
				CheckNear("s0", F.S0, C.S0, Tol);
				CheckNear("length", F.Length, C.Length, Tol);
				CheckNear("ux", F.Ux, C.Ux, Tol);
				CheckNear("uy", F.Uy, C.Uy, Tol);
				CheckNear("nx", F.Nx, C.Nx, Tol);
				CheckNear("ny", F.Ny, C.Ny, Tol);
				for (int32 k = 0; k < 5; ++k)
				{
					const FProjRow& Row = C.Points[k];
					const FRoadProjection Pr = ProjectToRoad(Road, Row.X, Row.Y);
					CheckNear("along", Pr.Along, Row.Along, Tol);
					CheckNear("s0 + along IS the world coordinate",
						F.S0 + Pr.Along, Row.World, Tol);
					double Wx = 0.0, Wy = 0.0;
					PointAt(F, F.S0 + Pr.Along, 0.0, Wx, Wy);
					CheckNear("and recovers the point", Road.bAxisX ? Wx : Wy, Row.World, Tol);
				}
			}
		}

		CASE("Roads.DiagonalLot");
		{
			// 52: a lot on a 45 degree road, end to end. Before this the world
			// position was recovered as start[axis] + along and could not have
			// produced these corners at all.
			FCityState S = SeedState(R);
			S.Money = T52_MoneyBefore;
			const FRoadDrawResult D = DrawRoad(Board, S, T52_Segment.StartX, T52_Segment.StartY,
				T52_Segment.EndX, T52_Segment.EndY, FString(T52_Segment.WidthClass), true);
			CheckBool("diagonal drawn", D.bOk, true);
			CheckNear("priced by its true length", S.Money, T52_MoneyAfter, Tol);
			const FPlaceResult P = Place(Board, S, T52_ClickX, T52_ClickY, true, Board.Rules.V0Width);
			CheckBool("lot placed", P.bOk, true);
			if (P.bOk)
			{
				const FLotPlacement& Lot = S.Parcels[P.Pid].Placement.GetValue();
				CheckNear("x0", Lot.X0, T52_Lot.X0, Tol);
				CheckNear("x1", Lot.X1, T52_Lot.X1, Tol);
				CheckStr("side", Lot.Side, FString(T52_Lot.Side));
				const FQuad Q = LotQuad(Board.Rules, Board.Econ, RoadOf(S, LotRoadId(Lot)), Lot);
				for (int32 k = 0; k < 4; ++k)
				{
					CheckNear("pad corner x", Q.X[k], T52_Quad.X[k], 0.01);
					CheckNear("pad corner y", Q.Y[k], T52_Quad.Y[k], 0.01);
				}
				// AND IT POSES. The pad's anchor is the midpoint of the quad
				// edge the pad's own +x runs FROM (corners 0-3 on the plus
				// side), and the yaw is the direction from corner 0 to corner
				// 1 - both read off the oracle's OWN corners, so this ties the
				// world transform to the fixture rather than to a second
				// hand-computed answer. Without it a diagonal lot would resolve
				// correctly and still stand in the wrong place.
				LotFrame::FPose Pose;
				const TArray<FRoad> PoseRoads = Board.AllRoads(S);
				const FRoad* Own = FindRoad(PoseRoads, LotRoadId(Lot));
				CheckBool("pose resolves", Own != nullptr && LotFrame::Pose(Lot, PoseRoads, Pose,
					RoadHalf(Board.Rules, Board.Econ, *Own)), true);
				CheckNear("pose x is the pad edge midpoint",
					Pose.X, (T52_Quad.X[0] + T52_Quad.X[3]) * 0.5, 0.01);
				CheckNear("pose y is the pad edge midpoint",
					Pose.Y, (T52_Quad.Y[0] + T52_Quad.Y[3]) * 0.5, 0.01);
				CheckNear("pose yaw is the road's own direction", Pose.Yaw,
					FMath::RadiansToDegrees(FMath::Atan2(T52_Quad.Y[1] - T52_Quad.Y[0],
						T52_Quad.X[1] - T52_Quad.X[0])), 0.01);

				FCityState Other = S;
				const FPlaceResult P2 = Place(Board, Other, T52_OtherX, T52_OtherY, true, Board.Rules.V0Width);
				CheckBool("the other side of the same span places", P2.bOk, true);
				if (P2.bOk)
				{
					CheckStr("other side", Other.Parcels[P2.Pid].Placement.GetValue().Side,
						FString(T52_OtherLot.Side));
				}
				FCityState Again = S;
				const FPlaceResult P3 = Place(Board, Again, T52_ClickX, T52_ClickY, true, Board.Rules.V0Width);
				CheckBool("the same span twice refuses", P3.bOk, T52_AgainOk);
				CheckStr("and says why", P3.Reason, FString(T52_AgainReason));
			}
		}

		CASE("Roads.SideNames");
		{
			// 53: the names come off the NORMAL. The 2:1 case is where a
			// dominant-axis rule would say 'west' and the lots are east; the
			// reversed segments are unreachable through the draw path (the
			// endpoints are ordered) but RoadDictFromSegment must still answer.
			for (int32 i = 0; i < T53_SidesNum; ++i)
			{
				const FSideRow& Row = T53_Sides[i];
				FRoadSegment Seg;
				Seg.StartX = Row.StartX; Seg.StartY = Row.StartY;
				Seg.EndX = Row.EndX;     Seg.EndY = Row.EndY;
				const FRoad Road = RoadDictFromSegment(FString(TEXT("X")), Seg);
				CheckStr("side plus", Road.SidePlus, FString(Row.Plus));
				CheckStr("side minus", Road.SideMinus, FString(Row.Minus));
				CheckBool("dominant axis", Road.bAxisX, Row.bAxisX);
				const FRoadFrame F = RoadFrameOf(Road);
				CheckNear("normal x", F.Nx, Row.Nx, 1e-6);
				CheckNear("normal y", F.Ny, Row.Ny, 1e-6);
			}
		}

		CASE("Roads.TwoLotsOnADiagonal");
		{
			// 54: two houses along one diagonal street. Their pads miss and
			// their boxes overlap, so a bounding-box scan refuses the second
			// click on visibly empty ground. Empty mode, because the pinned
			// frontage is wall to wall and a diagonal long enough for two lots
			// cannot avoid it on this board.
			FCityState S = RoadSeed();
			S.Money = 9000.0;
			const FRoadDrawResult D = DrawRoad(Board, S, T54_Segment.StartX, T54_Segment.StartY,
				T54_Segment.EndX, T54_Segment.EndY, FString(T54_Segment.WidthClass), false);
			CheckBool("diagonal drawn", D.bOk, true);
			for (int32 i = 0; i < 2; ++i)
			{
				const FPlaceResult P = Place(Board, S, T54_Clicks[i][0], T54_Clicks[i][1],
					false, Board.Rules.V0Width);
				CheckBool("lot placed", P.bOk, true);
				if (!P.bOk) { continue; }
				const FLotPlacement& Lot = S.Parcels[P.Pid].Placement.GetValue();
				CheckNear("x0", Lot.X0, T54_Lots[i].X0, Tol);
				CheckNear("x1", Lot.X1, T54_Lots[i].X1, Tol);
			}
			if (S.Parcels.Contains(FString(TEXT("P2"))))
			{
				const FLotPlacement& A = S.Parcels[FString(TEXT("P1"))].Placement.GetValue();
				const FLotPlacement& B2 = S.Parcels[FString(TEXT("P2"))].Placement.GetValue();
				const FRoad Rd = RoadOf(S, LotRoadId(A));
				const FQuad QA = LotQuad(Board.Rules, Board.Econ, Rd, A);
				const FQuad QB = LotQuad(Board.Rules, Board.Econ, Rd, B2);
				CheckBool("pads miss", QuadsOverlap(QA, QB), T54_Quads);
				CheckBool("boxes do not", RectsOverlap(QuadRect(QA), QuadRect(QB)), T54_Rects);
			}
		}

		CASE("Roads.ScansComparePads");
		{
			// 55: the other three scans compare pads too - something
			// axis-aligned standing in one of a diagonal's empty box corners.
			// (a) a drawn road against an existing lot
			FCityState A = RoadSeed();
			A.Money = 40000.0;
			const FPlaceResult PA = Place(Board, A, T55_RvL_Click[0], T55_RvL_Click[1],
				false, Board.Rules.V0Width);
			CheckBool("arterial lot placed", PA.bOk, true);
			const FRoadDrawResult DA = ResolveRoadDraw(Board, A, T55_RvL_Draw[0], T55_RvL_Draw[1],
				T55_RvL_Draw[2], T55_RvL_Draw[3], FString(TEXT("avenue")), false);
			CheckBool("the diagonal draws past it", DA.bOk, true);
			if (PA.bOk && DA.bOk)
			{
				const FLotPlacement& Lot = A.Parcels[PA.Pid].Placement.GetValue();
				const FQuad QR = RoadQuad(Board.Rules, Board.Econ,
					RoadDictFromSegment(DA.Id, DA.Segment));
				const FQuad QL = LotQuad(Board.Rules, Board.Econ, RoadOf(A, LotRoadId(Lot)), Lot);
				CheckBool("corridor misses the pad", QuadsOverlap(QR, QL), T55_RvL_Quads);
				CheckBool("boxes overlap", RectsOverlap(QuadRect(QR), QuadRect(QL)), T55_RvL_Rects);
			}
			// (b) a drawn road against another road
			FCityState B3 = RoadSeed();
			B3.Money = 40000.0;
			const FRoadDrawResult D1 = DrawRoad(Board, B3, T55_RvR_First[0], T55_RvR_First[1],
				T55_RvR_First[2], T55_RvR_First[3], FString(TEXT("avenue")), false);
			CheckBool("diagonal drawn", D1.bOk, true);
			const FRoadDrawResult D2 = ResolveRoadDraw(Board, B3, T55_RvR_Second[0], T55_RvR_Second[1],
				T55_RvR_Second[2], T55_RvR_Second[3], FString(TEXT("avenue")), false);
			CheckBool("a road in its box corner draws", D2.bOk, true);
			if (D1.bOk && D2.bOk)
			{
				const FQuad Q1 = RoadQuad(Board.Rules, Board.Econ,
					RoadDictFromSegment(D1.Id, B3.Roads[D1.Id]));
				const FQuad Q2 = RoadQuad(Board.Rules, Board.Econ,
					RoadDictFromSegment(D2.Id, D2.Segment));
				CheckBool("corridors miss", QuadsOverlap(Q1, Q2), T55_RvR_Quads);
				CheckBool("boxes overlap", RectsOverlap(QuadRect(Q1), QuadRect(Q2)), T55_RvR_Rects);
			}
			// (c) a lot against a highway's corridor - the no-frontage scan
			FCityState C = RoadSeed();
			C.Money = 40000.0;
			const FRoadDrawResult DC = DrawRoad(Board, C, T55_LvH_Road[0], T55_LvH_Road[1],
				T55_LvH_Road[2], T55_LvH_Road[3], FString(TEXT("avenue")), false);
			CheckBool("diagonal drawn", DC.bOk, true);
			const FRoadDrawResult DH = DrawRoad(Board, C, T55_LvH_Highway[0], T55_LvH_Highway[1],
				T55_LvH_Highway[2], T55_LvH_Highway[3], FString(TEXT("highway")), false);
			CheckBool("highway drawn", DH.bOk, true);
			const FClickResult CR = ResolveClick(Board, C, T55_LvH_Click[0], T55_LvH_Click[1],
				false, Board.Rules.V0Width);
			CheckBool("the click still places", CR.bOk, T55_LvH_StillPlaces);
			if (CR.bOk && DH.bOk)
			{
				CheckNear("x0", CR.Lot.X0, T55_LvH_Lot.X0, Tol);
				const FQuad QL = LotQuad(Board.Rules, Board.Econ, RoadOf(C, LotRoadId(CR.Lot)), CR.Lot);
				const FQuad QH = RoadQuad(Board.Rules, Board.Econ,
					RoadDictFromSegment(DH.Id, C.Roads[DH.Id]));
				CheckBool("pad misses the motorway", QuadsOverlap(QL, QH), T55_LvH_Quads);
				CheckBool("boxes overlap", RectsOverlap(QuadRect(QL), QuadRect(QH)), T55_LvH_Rects);
			}
		}
	}

	// =====================================================================
	// CURVED MULTI-NODE ROADS (queue item 11, second half). placement.py
	// self-tests 56-60, ROADS_AS_MECHANIC section 5's own shape: a
	// Catmull-Rom through the committed nodes, resampled by ARC LENGTH at the
	// 410 quantum into straight chords, drawn as ONE road.
	// =====================================================================
	{
		using namespace StacktownRoadsOracle;
		const FPlacementBoard Board = OracleBoard();
		auto Nodes = [](const FNode* Src, int32 Count) {
			TArray<FVector2D> Out;
			for (int32 i = 0; i < Count; ++i) { Out.Add(FVector2D(Src[i].X, Src[i].Y)); }
			return Out;
		};
		const FString Avenue(TEXT("avenue"));

		CASE("Roads.Sampler");
		{
			// 56: vertex for vertex against the oracle - the arc-length
			// resampling, the merged leftover and the snap all in one answer.
			const TArray<FVector2D> Pts = SamplePath(Board.Rules,
				Nodes(Curve, CurveNum), Board.Rules.WidthQuantum);
			CheckInt("vertex count", Pts.Num(), T56_SampledNum);
			for (int32 i = 0; i < Pts.Num() && i < T56_SampledNum; ++i)
			{
				CheckNear("vertex x", Pts[i].X, T56_Sampled[i].X, Tol);
				CheckNear("vertex y", Pts[i].Y, T56_Sampled[i].Y, Tol);
			}
			// Two nodes is a straight line through them, not a curve.
			const TArray<FVector2D> Str = SamplePath(Board.Rules,
				Nodes(T56_StraightNodes, T56_StraightNodesNum), Board.Rules.WidthQuantum);
			CheckInt("straight vertex count", Str.Num(), T56_StraightNum);
			for (int32 i = 0; i < Str.Num() && i < T56_StraightNum; ++i)
			{
				CheckNear("straight x", Str[i].X, T56_Straight[i].X, Tol);
				CheckNear("straight y", Str[i].Y, T56_Straight[i].Y, Tol);
			}
		}

		CASE("Roads.PathIsOneRoad");
		{
			// 57 + 58: one gesture, one road, one price - and one road to
			// everything downstream, which is what makes a curve buildable.
			FCityState S = SeedState(R);
			S.Money = T57_MoneyBefore;
			const FRoadPathResult D = DrawRoadPath(Board, S, Nodes(Curve, CurveNum),
				Avenue, false);
			CheckBool("curve drawn", D.bOk, true);
			CheckStr("path id", D.PathId, FString(T57_PathId));
			CheckInt("chord count", D.Segments.Num(), T57_IdsNum);
			CheckNear("priced once, for the polyline", S.Money, T57_MoneyAfter, Tol);
			for (int32 i = 0; i < D.Segments.Num() && i < T57_IdsNum; ++i)
			{
				CheckBool("chord in state", S.Roads.Contains(FString(T57_Ids[i])), true);
				const FRoadSegment& Seg = S.Roads[FString(T57_Ids[i])];
				CheckNear("chord start x", Seg.StartX, T57_Segments[i].StartX, Tol);
				CheckNear("chord start y", Seg.StartY, T57_Segments[i].StartY, Tol);
				CheckNear("chord end x", Seg.EndX, T57_Segments[i].EndX, Tol);
				CheckNear("chord end y", Seg.EndY, T57_Segments[i].EndY, Tol);
				CheckStr("chord path", Seg.Path, FString(T57_Segments[i].Path));
			}

			// The joints sit in more than one CHORD - so counting chords would
			// call every one of them "the crossing", and there is one every
			// 410 uu. Counting PATHS is what makes a curve carry lots at all.
			const TArray<FRoad> Roads = Board.AllRoads(S);
			for (int32 j = 0; j < T58_JointsNum; ++j)
			{
				int32 Chords = 0;
				for (const FRoad& Rd : Roads)
				{
					const FRoadProjection Pr = ProjectToRoad(Rd, T58_Joints[j].X, T58_Joints[j].Y);
					if (Pr.Along >= 0.0 && Pr.Along <= Pr.Length
						&& FMath::Abs(Pr.Across) < RoadHalf(Board.Rules, Board.Econ, Rd))
					{
						++Chords;
					}
				}
				CheckBool("the joint sits in more than one chord", Chords > 1, true);
				CheckBool("and is not the crossing",
					InCrossing(Board.Rules, Board.Econ, Roads, T58_Joints[j].X, T58_Joints[j].Y), false);
			}

			// A lot fronts a chord, spanning the JOINED RUN rather than the one
			// chord - which it must, because the curve is sampled at 410 and
			// the narrowest lot is 820.
			const FClickResult CR = ResolveClick(Board, S, T58_ClickX, T58_ClickY,
				false, Board.Rules.V0Width);
			CheckBool("a lot fronts the curve", CR.bOk, true);
			if (CR.bOk)
			{
				CheckNear("lot x0", CR.Lot.X0, T58_Lot.X0, Tol);
				CheckNear("lot x1", CR.Lot.X1, T58_Lot.X1, Tol);
				CheckStr("lot road", LotRoadId(CR.Lot), FString(T58_Lot.RoadId));
				const FRoad* Own = FindRoad(Roads, LotRoadId(CR.Lot));
				CheckBool("own chord", Own != nullptr, true);
				if (Own != nullptr)
				{
					const FRoadFrame F = RoadFrameOf(*Own);
					CheckNear("the chord is shorter than a lot", F.Length, T58_ChordLength, Tol);
					CheckBool("shorter than V0Width", F.Length < Board.Rules.V0Width, true);
					double Lo = 0.0, Hi = 0.0;
					PathSpan(Roads, *Own, Lo, Hi);
					CheckNear("span min", Lo, T58_SpanMin, Tol);
					CheckNear("span max", Hi, T58_SpanMax, Tol);
					CheckBool("the span is wider than the chord", Hi - Lo > F.Length, true);
				}
			}
		}

		CASE("Roads.PathIsOneDecision");
		{
			// 59: ANY chord failing refuses the WHOLE path, and nothing is
			// added or spent. A path that half-built where it first hit
			// something would leave the player a road they did not draw.
			FCityState S = SeedState(R);
			S.Money = 40000.0;
			const FRoadPathResult X = DrawRoadPath(Board, S,
				Nodes(T59_Crosses_Nodes, T59_Crosses_NodesNum), Avenue, false);
			CheckBool("refused", X.bOk, T59_Crosses_Ok);
			CheckStr("reason names the road and the chord", X.Reason, FString(T59_Crosses_Reason));
			CheckInt("no segments handed back", X.Segments.Num(), T59_CrossesSegments);
			CheckNear("nothing spent", S.Money, 40000.0, Tol);
			CheckInt("no road added", S.Roads.Num(), 0);

			// The price is the PATH's, and checked at the boundary so a price
			// that is merely WRONG is caught and not just one that is absent.
			FCityState Fresh = SeedState(R);
			const FRoadPathResult A = ResolveRoadPath(Board, Fresh, Nodes(Curve, CurveNum),
				Avenue, false);
			CheckBool("a fresh city cannot afford it", A.bOk, T59_Afford_Ok);
			CheckStr("and is told the price", A.Reason, FString(T59_Afford_Reason));
			FCityState Under = SeedState(R);
			Under.Money = T59_Cost - 1.0;
			CheckBool("one uu under refuses",
				ResolveRoadPath(Board, Under, Nodes(Curve, CurveNum), Avenue, false).bOk,
				T59_UnderOk);
			FCityState Exact = SeedState(R);
			Exact.Money = T59_Cost;
			const FRoadPathResult Ex = DrawRoadPath(Board, Exact, Nodes(Curve, CurveNum),
				Avenue, false);
			CheckBool("the exact quote draws", Ex.bOk, T59_ExactOk);
			CheckNear("and spends all of it", Exact.Money, 0.0, 1e-6);

			// The boundary refusals, each with its own words.
			FCityState S2 = SeedState(R);
			S2.Money = 40000.0;
			const FRoadPathResult U = ResolveRoadPath(Board, S2, Nodes(Curve, CurveNum),
				FString(TEXT("motorway")), false);
			CheckBool("unknown type refused", U.bOk, T59_Unknown_Ok);
			CheckStr("unknown type reason", U.Reason, FString(T59_Unknown_Reason));
			TArray<FVector2D> One;
			One.Add(FVector2D(0.0, 0.0));
			const FRoadPathResult O = ResolveRoadPath(Board, S2, One, Avenue, false);
			CheckBool("one node refused", O.bOk, T59_OneNode_Ok);
			CheckStr("one node reason", O.Reason, FString(T59_OneNode_Reason));
			const FRoadPathResult Sh = ResolveRoadPath(Board, S2,
				Nodes(T59_TooShort_Nodes, T59_TooShort_NodesNum), Avenue, false);
			CheckBool("too short refused", Sh.bOk, T59_TooShort_Ok);
			CheckStr("too short reason", Sh.Reason, FString(T59_TooShort_Reason));

			// THE PLATE CHECK IS ON THE POLYLINE, not the nodes: every node
			// here is on the plate and the curve still leaves it.
			for (int32 i = 0; i < T59_Overshoot_NodesNum; ++i)
			{
				CheckBool("node is on the plate",
					T59_Overshoot_Nodes[i].Y >= T59_Overshoot_PlateYMin, true);
			}
			CheckBool("and the curve is not",
				T59_Overshoot_MinY < T59_Overshoot_PlateYMin, true);
			FCityState S3 = SeedState(R);
			S3.Money = 40000.0;
			const FRoadPathResult Ov = ResolveRoadPath(Board, S3,
				Nodes(T59_Overshoot_Nodes, T59_Overshoot_NodesNum), Avenue, false);
			CheckBool("overshoot refused", Ov.bOk, T59_Overshoot_Ok);
			CheckStr("overshoot reason", Ov.Reason, FString(T59_Overshoot_Reason));

			// And a curve may not be drawn through a standing building.
			FCityState S4 = SeedState(R);
			S4.Money = 40000.0;
			const FPlaceResult PL = Place(Board, S4, T59_Lot_ClickX, T59_Lot_ClickY,
				false, Board.Rules.V0Width);
			CheckBool("lot placed", PL.bOk, true);
			const FRoadPathResult Th = ResolveRoadPath(Board, S4,
				Nodes(T59_Lot_Nodes, T59_Lot_NodesNum), Avenue, false);
			CheckBool("through a building refused", Th.bOk, T59_Lot_Ok);
			CheckStr("and names the lot", Th.Reason, FString(T59_Lot_Reason));

			// TWO NODES IS A ROAD - the straight case through the same door.
			FCityState S5 = SeedState(R);
			S5.Money = 40000.0;
			const FRoadPathResult Two = DrawRoadPath(Board, S5,
				Nodes(T59_Two_Nodes, T59_Two_NodesNum), Avenue, false);
			CheckBool("two nodes draw", Two.bOk, true);
			CheckStr("path id", Two.PathId, FString(T59_Two_PathId));
			CheckInt("chord count", Two.Segments.Num(), T59_Two_Count);
			for (int32 i = 0; i < Two.Segments.Num() && i < T59_Two_Count; ++i)
			{
				CheckNear("chord start x", Two.Segments[i].StartX, T59_Two_Segments[i].StartX, Tol);
				CheckNear("chord end x", Two.Segments[i].EndX, T59_Two_Segments[i].EndX, Tol);
				CheckNear("chord y", Two.Segments[i].StartY, T59_Two_Segments[i].StartY, Tol);
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

		CASE("Preset.Seed");
		{
			const FCityState Preset = SeedPresetState(R, Real);
			const FCityState Empty = SeedState(R);
			CheckInt("empty start is empty", Empty.Parcels.Num(), 0);
			CheckInt("preset seeds fourteen", Preset.Parcels.Num(), Real.PinnedSpans.Num());
			CheckNear("fresh money", Preset.Money, Empty.Money, Tol);
			CheckNear("fresh demand", Preset.Demand, Empty.Demand, Tol);
			CheckInt("no roads", Preset.Roads.Num(), 0);
			for (int32 i = 0; i < Real.PinnedSpans.Num(); ++i)
			{
				const FPinnedSpan& Span = Real.PinnedSpans[i];
				const FParcelState* P = Preset.Parcels.Find(Span.Key);
				CheckBool("present", P != nullptr, true);
				if (P == nullptr) { continue; }
				CheckStr("rid", P->Rid, Span.Rid);
				CheckNear("width", P->Width, Span.Width, Tol);
				CheckBool("for sale", P->bOwned, false);
				CheckInt("tier 0", P->Tier, 0);
				CheckBool("has a placement", P->Placement.IsSet(), true);
				if (!P->Placement.IsSet()) { continue; }
				CheckNear("x0", P->Placement.GetValue().X0, Span.X0, Tol);
				CheckNear("x1", P->Placement.GetValue().X1, Span.X1, Tol);
				CheckStr("side", P->Placement.GetValue().Side, Span.Side);
			}
		}

		CASE("Preset.Poses");
		{
			const FCityState Preset = SeedPresetState(R, Real);
			const TArray<FRoad> Roads = Real.AllRoads(Preset);
			int32 Posed = 0;
			TArray<FString> Ids;
			Preset.Parcels.GetKeys(Ids);
			for (int32 i = 0; i < Ids.Num(); ++i)
			{
				const FParcelState& P = Preset.Parcels[Ids[i]];
				if (!P.Placement.IsSet()) { continue; }
				LotFrame::FPose Pose;
				if (LotFrame::Pose(P.Placement.GetValue(), Roads, Pose)) { ++Posed; }
			}
			// A lot the sync cannot pose is a building that silently does not
			// appear on a fresh start.
			CheckInt("all fourteen pose", Posed, Real.PinnedSpans.Num());
		}

		CASE("Preset.Occupies");
		{
			const FCityState Preset = SeedPresetState(R, Real);
			// Even with pins OFF, a real parcel stands there and the overlap
			// scan refuses on its own - that is what makes these ordinary lots.
			const FClickResult Refused = ResolveClick(Real, Preset, 2360.0, 1500.0, false, Real.Rules.V0Width);
			CheckBool("refused with pins off", Refused.bOk, false);
			CheckBool("by the overlap scan",
				Refused.Reason.S.find("crosses an existing lot") != std::string::npos, true);
			const FClickResult Accepted = ResolveClick(Real, SeedState(R), 2360.0, 1500.0, false, Real.Rules.V0Width);
			CheckBool("free on an empty start", Accepted.bOk, true);
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
