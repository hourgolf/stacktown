// Stacktown.Score.* - the PROPOSED score (MONDAY_DECISIONS section 1), hand-computed.
#include "Misc/AutomationTest.h"
#include "StacktownScore.h"
#include "StacktownEconomyTestCommon.h"

#if WITH_DEV_AUTOMATION_TESTS

using namespace Stacktown;
using namespace StacktownTest;

#define STACKTOWN_SCORE_TEST(TestClass, PrettyName) \
	IMPLEMENT_SIMPLE_AUTOMATION_TEST(TestClass, PrettyName, EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter) \
	bool TestClass::RunTest(const FString& Parameters)

STACKTOWN_SCORE_TEST(FStacktownScoreFresh, "Stacktown.Score.FreshCityIsItsMoney")
{
	FCityState S; S.Money = 100.0;
	TestEqual(TEXT("fresh city scores its money"), Score(OracleRules(), S), 100.0, Tol);
	TestEqual(TEXT("no goal reached"), GoalsReached(Score(OracleRules(), S)), 0);
	return true;
}

STACKTOWN_SCORE_TEST(FStacktownScoreOwned, "Stacktown.Score.OwnedLotAddsItsPrice")
{
	FCityState S; S.Money = 33.6;
	S.Parcels.Add(TEXT("P1"), Parcel(TEXT("vernacular"), 0, 820.0, true));
	S.Parcels.Add(TEXT("P2"), Parcel(TEXT("vernacular"), 0, 820.0, false));   // for sale: worth nothing to the score
	// price_base 50 + 2 x 8.2 = 66.4 at tier 0: buying a lot moves money into value, the score holds
	TestEqual(TEXT("money + the owned lot's price"), Score(OracleRules(), S), 33.6 + 66.4, Tol);
	return true;
}

STACKTOWN_SCORE_TEST(FStacktownScoreFailed, "Stacktown.Score.FailedLotSubtracts")
{
	FCityState S; S.Money = 500.0;
	FParcelState P = Parcel(TEXT("vernacular"), 2, 1230.0, true);
	P.bFailed = true;
	S.Parcels.Add(TEXT("P1"), P);
	const FScoreBreakdown B = ScoreBreakdown(OracleRules(), S);
	TestEqual(TEXT("penalty"), B.FailedPenalty, 50.0, Tol);
	TestEqual(TEXT("value still counted"), B.LotValue, Price(OracleRules(), 2, 1230.0), Tol);
	TestEqual(TEXT("total"), B.Total, 500.0 + Price(OracleRules(), 2, 1230.0) - 50.0, Tol);
	return true;
}

STACKTOWN_SCORE_TEST(FStacktownScoreRoads, "Stacktown.Score.RoadsAndLadder")
{
	FCityState S; S.Money = 800.0;
	FRoadSegment R; R.StartX = 2000.0; R.StartY = -3000.0; R.EndX = 6000.0; R.EndY = -3000.0;   // 4000 uu = 40 x $5
	S.Roads.Add(TEXT("R1"), R);
	TestEqual(TEXT("road bonus"), ScoreBreakdown(OracleRules(), S).RoadBonus, 200.0, Tol);
	TestEqual(TEXT("total crosses the first rung"), Score(OracleRules(), S), 1000.0, Tol);
	TestEqual(TEXT("first goal"), GoalsReached(1000.0), 1);
	TestEqual(TEXT("just under"), GoalsReached(999.99), 0);
	TestEqual(TEXT("all four"), GoalsReached(100000.0), 4);
	return true;
}

#undef STACKTOWN_SCORE_TEST
#endif
