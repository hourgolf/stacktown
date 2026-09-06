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

	printf("\n%s: %d checks, %d failures\n",
		gFailures == 0 ? "PRE-FLIGHT PASS (shim, NOT Unreal)" : "PRE-FLIGHT FAIL",
		gChecks, gFailures);
	return gFailures == 0 ? 0 : 1;
}
