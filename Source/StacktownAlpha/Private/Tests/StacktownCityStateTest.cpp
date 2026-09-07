// The nine citytick.py known-answer tests, ported (Phase 1 step 1).
//
//   UnrealEditor-Cmd <uproject> -ExecCmds="Automation RunTests Stacktown.CityState; Quit" \
//     -unattended -nopause -nullrhi -log
//
// citytick.py's tests prove one claim over and over: THE WRAPPER AND THE RULES
// AGREE, and what got saved is what reloads. In C++ the first half would be
// tautological if it were asserted the way the Python asserts it - the subsystem
// literally delegates to the same functions, so of course it agrees. So every
// test here compares the subsystem's state AFTER A SAVE AND RELOAD against the
// pure rules run on a parallel copy. That puts serialization inside the claim,
// which is the only place a difference could actually live.
//
// STATE FILES GO UNDER Saved/SelfTest AND NOWHERE ELSE. citystate.json is the
// owner's save; a self-test that writes production state is not a self-test, it
// is a bug. The filename is also distinct from the Python's own throwaway, so
// both suites can run at once without one clearing the other's file.

#include "Misc/AutomationTest.h"
#include "StacktownEconomy.h"
#include "StacktownEconomyTestCommon.h"
#include "StacktownSubsystemTestFixture.h"

#if WITH_DEV_AUTOMATION_TESTS

using namespace Stacktown;
using namespace StacktownTest;

#define STACKTOWN_CITY_TEST(TestClass, PrettyName) \
	IMPLEMENT_SIMPLE_AUTOMATION_TEST(TestClass, PrettyName, \
		EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter) \
	bool TestClass::RunTest(const FString& Parameters)

// --- 1: no file yet, so the seed comes straight from the ruleset ----------------
STACKTOWN_CITY_TEST(FStacktownCitySeed, "Stacktown.CityState.Seed")
{
	FScopedEconomy E;
	FString Err;
	TestTrue(TEXT("load with no file succeeds"), E->LoadState(Err));
	TestEqual(TEXT("no error"), Err, FString());

	const FCityState& S = E->GetState();
	TestEqual(TEXT("money"),  S.Money,  StacktownOracle::Seed_Money, Tol);
	TestEqual(TEXT("demand"), S.Demand, StacktownOracle::Seed_Demand, Tol);
	TestEqual(TEXT("no parcels"), S.Parcels.Num(), StacktownOracle::Seed_ParcelCount);
	TestEqual(TEXT("trades_processed starts at zero"), S.TradesProcessed, 0);
	// seed_state() declares 'roads' and readers use it. Empty on a fresh city:
	// drawing is the only writer, and the two built-in roads are constants of
	// the board rather than state.
	TestEqual(TEXT("no roads on a fresh city"), S.Roads.Num(), 0);
	TestFalse(TEXT("loading wrote nothing"), E.FileExists());
	return true;
}

// --- 2 + 3: buy crosses the boundary, persists, and reloads as the same state ---
STACKTOWN_CITY_TEST(FStacktownCityBuy, "Stacktown.CityState.Buy")
{
	FScopedEconomy E;
	E->GetMutableState().Parcels.Add(TEXT("P1"), Parcel(TEXT("vernacular"), 0, 1230.0));

	// The pure rules on a parallel copy: the independent answer this is checked
	// against.
	FCityState Expected = E->GetState();
	const FVerbResult Direct = Buy(E->GetRules(), Expected, TEXT("P1"));
	TestTrue(TEXT("the rules allow this buy"), Direct.bOk);

	FString Reason;
	TestTrue(TEXT("the subsystem allows it too"), E->CityBuy(TEXT("P1"), Reason));
	TestEqual(TEXT("no reason on success"), Reason, FString());
	TestEqual(TEXT("money"), E->GetMoney(), StacktownOracle::BuyThenTick10_AfterBuyMoney, Tol);

	FCityState Reloaded;
	FString Err;
	TestTrue(TEXT("a successful buy persisted"), E.ReloadFromDisk(Reloaded, Err));
	FString Why;
	const bool bSame = StatesEqual(Reloaded, Expected, Tol, Why);
	TestTrue(FString::Printf(TEXT("reloaded state matches the rules' answer (%s)"), *Why), bSame);
	return true;
}

// A refused buy must leave no file behind. citytick.py persists iff the verb
// succeeded; a port that saved unconditionally would still pass every assertion
// about money, and quietly write on every failed click.
STACKTOWN_CITY_TEST(FStacktownCityRefusalDoesNotPersist, "Stacktown.CityState.RefusalDoesNotPersist")
{
	FScopedEconomy E;
	E->GetMutableState().Money = 1.0;
	E->GetMutableState().Parcels.Add(TEXT("P"), Parcel(TEXT("vernacular"), 0, 1230.0));

	FString Reason;
	TestFalse(TEXT("buy refused"), E->CityBuy(TEXT("P"), Reason));
	TestEqual(TEXT("refusal reason"), Reason, FString(StacktownOracle::Buy_insufficient_Reason));
	TestFalse(TEXT("nothing was written"), E.FileExists());
	return true;
}

// --- 4: ten ticks across the boundary -------------------------------------------
STACKTOWN_CITY_TEST(FStacktownCityTick, "Stacktown.CityState.Tick")
{
	FScopedEconomy E;
	E->GetMutableState().Parcels.Add(TEXT("P1"),
		Parcel(TEXT("vernacular"), 0, 1230.0, true));

	FCityState Expected = E->GetState();
	TArray<FEconEvent> DirectEvents;
	for (int32 i = 0; i < 10; ++i)
	{
		TickCity(E->GetRules(), Expected, DirectEvents);   // what CityTick persists: tick AND age
	}
	for (int32 i = 0; i < 10; ++i)
	{
		E->CityTick();
	}

	FCityState Reloaded;
	FString Err;
	TestTrue(TEXT("ticks persisted"), E.ReloadFromDisk(Reloaded, Err));
	FString Why;
	const bool bSame = StatesEqual(Reloaded, Expected, Tol, Why);
	TestTrue(FString::Printf(TEXT("reloaded matches the rules (%s)"), *Why), bSame);
	TestEqual(TEXT("tier never moved across the boundary either"),
		Reloaded.Parcels[TEXT("P1")].Tier, 0);
	return true;
}

// --- 5: the retired growth case, at the boundary --------------------------------
STACKTOWN_CITY_TEST(FStacktownCityGrowthRetired, "Stacktown.CityState.GrowthRetired")
{
	FScopedEconomy E;
	E->GetMutableState().Money = 0.0;
	E->GetMutableState().Parcels.Add(TEXT("OF"),
		Parcel(TEXT("office"), 0, 2050.0, true, 39.9));

	FCityState Expected = E->GetState();
	TArray<FEconEvent> DirectEvents;
	TickCity(E->GetRules(), Expected, DirectEvents);   // what CityTick persists: tick AND age
	E->CityTick();

	FCityState Reloaded;
	FString Err;
	TestTrue(TEXT("tick persisted"), E.ReloadFromDisk(Reloaded, Err));
	FString Why;
	const bool bSame = StatesEqual(Reloaded, Expected, Tol, Why);
	TestTrue(FString::Printf(TEXT("reloaded matches the rules (%s)"), *Why), bSame);
	TestEqual(TEXT("tier unchanged"), Reloaded.Parcels[TEXT("OF")].Tier,
		StacktownOracle::TickRetired_Tier);
	TestEqual(TEXT("accum still accrued"), Reloaded.Parcels[TEXT("OF")].Accum,
		StacktownOracle::TickRetired_Accum, Tol);
	return true;
}

// --- 6: reset wipes to a fresh seed and the file agrees -------------------------
STACKTOWN_CITY_TEST(FStacktownCityReset, "Stacktown.CityState.Reset")
{
	FScopedEconomy E;
	E->GetMutableState().Money = 99999.0;
	E->GetMutableState().Parcels.Add(TEXT("P1"),
		Parcel(TEXT("vernacular"), 4, 1230.0, true, 500.0));
	E->GetMutableState().TradesProcessed = 42;

	E->ResetCity();
	TestEqual(TEXT("money reseeded"), E->GetMoney(), StacktownOracle::Seed_Money, Tol);
	TestEqual(TEXT("demand reseeded"), E->GetDemand(), StacktownOracle::Seed_Demand, Tol);
	TestEqual(TEXT("parcels cleared"), E->GetState().Parcels.Num(), StacktownOracle::Seed_ParcelCount);
	TestEqual(TEXT("trade count cleared"), E->GetState().TradesProcessed, 0);

	FCityState Reloaded;
	FString Err;
	TestTrue(TEXT("reset persisted"), E.ReloadFromDisk(Reloaded, Err));
	FString Why;
	const bool bSame = StatesEqual(Reloaded, E->GetState(), Tol, Why);
	TestTrue(FString::Printf(TEXT("the file matches what was returned (%s)"), *Why), bSame);
	return true;
}

// --- 7: ensure_parcel seeds tier 0, is idempotent, persists only on the insert ---
STACKTOWN_CITY_TEST(FStacktownCityEnsureParcel, "Stacktown.CityState.EnsureParcel")
{
	FScopedEconomy E;

	TestTrue(TEXT("first call inserts"), E->EnsureParcel(TEXT("SW2"), TEXT("tower"), 1230.0));
	const FParcelState& P = E->GetState().Parcels[TEXT("SW2")];
	// TIER 0 ALWAYS, whatever a pin declares. Seeding from a pin's declared tier
	// is the bug this replaces: buying a parcel whose pin said tier 6 showed the
	// full mature building instantly instead of starting small.
	TestEqual(TEXT("tier seeds at 0"), P.Tier, 0);
	TestEqual(TEXT("rid"), P.Rid, FString(TEXT("tower")));
	TestEqual(TEXT("width"), P.Width, 1230.0, Tol);
	TestFalse(TEXT("not owned"), P.bOwned);
	TestEqual(TEXT("accum"), P.Accum, 0.0, Tol);
	TestFalse(TEXT("not failed"), P.bFailed);
	TestEqual(TEXT("performance neutral"), P.Performance, 0.0, Tol);

	FCityState Reloaded;
	FString Err;
	TestTrue(TEXT("the insert persisted"), E.ReloadFromDisk(Reloaded, Err));

	// Grow it, delete the file, and re-call with the SAME arguments. A no-op
	// must neither roll the tier back nor write - and deleting the file first is
	// what makes "did not write" observable rather than assumed.
	E->GetMutableState().Parcels[TEXT("SW2")].bOwned = true;
	E->GetMutableState().Parcels[TEXT("SW2")].Tier = 3;
	const FCityState Before = E->GetState();
	FPlatformFileManager::Get().GetPlatformFile().DeleteFile(*E.Path);

	TestFalse(TEXT("second call inserts nothing"),
		E->EnsureParcel(TEXT("SW2"), TEXT("tower"), 1230.0));
	TestEqual(TEXT("a no-op did not roll the grown tier back"),
		E->GetState().Parcels[TEXT("SW2")].Tier, 3);
	FString Why;
	const bool bSame = StatesEqual(E->GetState(), Before, Tol, Why);
	TestTrue(FString::Printf(TEXT("a no-op changed nothing at all (%s)"), *Why), bSame);
	TestFalse(TEXT("a no-op wrote nothing"), E.FileExists());
	return true;
}

// --- 8: upgrade across the boundary ---------------------------------------------
STACKTOWN_CITY_TEST(FStacktownCityUpgrade, "Stacktown.CityState.Upgrade")
{
	FScopedEconomy E;
	E->GetMutableState().Money = 200.0;
	E->GetMutableState().Parcels.Add(TEXT("UP1"),
		Parcel(TEXT("vernacular"), 0, 1230.0, true));

	FCityState Expected = E->GetState();
	const TSharedRef<FStaticCatalogue> Cat = OracleCatalogue();
	const FVerbResult Direct = Upgrade(E->GetRules(), *Cat, Expected, TEXT("UP1"));
	TestTrue(TEXT("the rules allow this upgrade"), Direct.bOk);

	FString Reason;
	TestTrue(TEXT("the subsystem allows it too"), E->CityUpgrade(TEXT("UP1"), Reason));
	TestEqual(TEXT("no reason on success"), Reason, FString());
	TestEqual(TEXT("money"), E->GetMoney(), 150.0, Tol);
	TestEqual(TEXT("tier climbed"), E->GetState().Parcels[TEXT("UP1")].Tier, 1);

	FCityState Reloaded;
	FString Err;
	TestTrue(TEXT("upgrade persisted"), E.ReloadFromDisk(Reloaded, Err));
	FString Why;
	const bool bSame = StatesEqual(Reloaded, Expected, Tol, Why);
	TestTrue(FString::Printf(TEXT("reloaded matches the rules (%s)"), *Why), bSame);
	return true;
}

// --- 9: repair across the boundary ----------------------------------------------
STACKTOWN_CITY_TEST(FStacktownCityRepair, "Stacktown.CityState.Repair")
{
	FScopedEconomy E;
	E->GetMutableState().Money = 200.0;
	E->GetMutableState().Parcels.Add(TEXT("RP1"),
		Parcel(TEXT("vernacular"), 0, 1230.0, true, 0.0, true));

	FCityState Expected = E->GetState();
	const FVerbResult Direct = Repair(E->GetRules(), Expected, TEXT("RP1"));
	TestTrue(TEXT("the rules allow this repair"), Direct.bOk);

	FString Reason;
	TestTrue(TEXT("the subsystem allows it too"), E->CityRepair(TEXT("RP1"), Reason));
	TestEqual(TEXT("money"), E->GetMoney(), 150.0, Tol);
	TestFalse(TEXT("failed cleared"), E->GetState().Parcels[TEXT("RP1")].bFailed);

	FCityState Reloaded;
	FString Err;
	TestTrue(TEXT("repair persisted"), E.ReloadFromDisk(Reloaded, Err));
	FString Why;
	const bool bSame = StatesEqual(Reloaded, Expected, Tol, Why);
	TestTrue(FString::Printf(TEXT("reloaded matches the rules (%s)"), *Why), bSame);
	return true;
}

// --- ADDED BY THE PORT, not one of the nine -------------------------------------
// The Python has no equivalent because Python dicts round-trip through json
// without a schema. This port hand-writes both directions, so the round trip is
// a place a field can silently go missing. Every field, one save and reload.
STACKTOWN_CITY_TEST(FStacktownCityRoundTrip, "Stacktown.CityState.RoundTrip")
{
	FCityState S;
	S.Money = 1234.5;
	S.Demand = 1.75;
	S.TradesProcessed = 7;
	Stacktown::FRoadSegment R1;
	R1.StartX = 6200.0; R1.StartY = 3000.0; R1.EndX = 7600.0; R1.EndY = 3000.0;
	R1.WidthClass = TEXT("avenue");
	S.Roads.Add(TEXT("R1"), R1);
	S.Parcels.Add(TEXT("A"), Parcel(TEXT("vernacular"), 3, 1230.0, true, 12.25, false, -0.5));
	S.Parcels.Add(TEXT("B"), Parcel(TEXT("office"), 0, 2050.0, false, 0.0, true, 0.75));

	FCityState Back;
	FString Err;
	TestTrue(TEXT("round trip parses"), CityStateFromJson(CityStateToJson(S), Back, Err));
	TestEqual(TEXT("no error"), Err, FString());
	FString Why;
	const bool bSame = StatesEqual(S, Back, Tol, Why);
	TestTrue(FString::Printf(TEXT("every field survived (%s)"), *Why), bSame);
	// Roads survive a second trip too, field by field - a writer that dropped
	// width_class or swapped a coordinate would pass a single round trip.
	FCityState Roads;
	TestTrue(TEXT("roads re-parse"), CityStateFromJson(CityStateToJson(Back), Roads, Err));
	TestEqual(TEXT("road count"), Roads.Roads.Num(), 1);
	const Stacktown::FRoadSegment& Got = Roads.Roads[TEXT("R1")];
	TestEqual(TEXT("start x"), Got.StartX, 6200.0, Tol);
	TestEqual(TEXT("start y"), Got.StartY, 3000.0, Tol);
	TestEqual(TEXT("end x"), Got.EndX, 7600.0, Tol);
	TestEqual(TEXT("end y"), Got.EndY, 3000.0, Tol);
	TestEqual(TEXT("width class"), Got.WidthClass, FString(TEXT("avenue")));

	// A malformed ruleset or state must be refused, never half-read.
	FCityState Junk;
	TestFalse(TEXT("malformed JSON is refused"), CityStateFromJson(TEXT("{not json"), Junk, Err));
	TestFalse(TEXT("and says why"), Err.IsEmpty());
	return true;
}

#undef STACKTOWN_CITY_TEST

#endif // WITH_DEV_AUTOMATION_TESTS
