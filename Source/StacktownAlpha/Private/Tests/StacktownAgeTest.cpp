// Patina's age channel (queue item 7).
//
//   UnrealEditor-Cmd <uproject> -ExecCmds="Automation RunTests Stacktown.Age; Quit" \
//     -unattended -nopause -nullrhi -log
//
// Ported from Content/Python/init_unreal.py's own age block (~530-556), which
// keeps this OUTSIDE econrules.tick deliberately: the economy oracles assert
// exact state equality against hand-computed answers and age has nothing to do
// with the economy they prove. The same separation is kept here - AdvanceAge is
// called from UStacktownEconomy::CityTick, never from Stacktown::Tick.

#include "Misc/AutomationTest.h"
#include "StacktownEconomyTestCommon.h"
#include "StacktownEconomy.h"
#include "StacktownSubsystemTestFixture.h"

#if WITH_DEV_AUTOMATION_TESTS

using namespace Stacktown;
using namespace StacktownTest;

#define STACKTOWN_AGE_TEST(TestClass, PrettyName) \
	IMPLEMENT_SIMPLE_AUTOMATION_TEST(TestClass, PrettyName, \
		EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter) \
	bool TestClass::RunTest(const FString& Parameters)

// --- the advance rule --------------------------------------------------------------
STACKTOWN_AGE_TEST(FStacktownAgeAdvance, "Stacktown.Age.Advance")
{
	// AN UNOWNED LOT DOES NOT AGE, and its recorded tier is left alone - so
	// buying a lot that has sat on the board a while still starts it pale.
	{
		FParcelState P = Parcel(TEXT("vernacular"), 0, 820.0, false);
		AdvanceAge(P);
		TestEqual(TEXT("unowned does not age"), P.AgeTicks, 0.0, 1e-9);
		TestFalse(TEXT("and records no tier"), P.AgeLastTier.IsSet());
	}

	// THE FIRST ADVANCE OF A NEWLY OWNED LOT RESETS rather than counting: its
	// tier has never been recorded, so it takes the reset branch. Counting from
	// one here would start every building a tick old.
	{
		FParcelState P = Parcel(TEXT("vernacular"), 0, 820.0, true);
		AdvanceAge(P);
		TestEqual(TEXT("first advance records zero"), P.AgeTicks, 0.0, 1e-9);
		TestTrue(TEXT("and records the tier"), P.AgeLastTier.IsSet());
		TestEqual(TEXT("the tier it recorded"), P.AgeLastTier.GetValue(), 0);

		// Only from the second advance does it count.
		AdvanceAge(P);
		TestEqual(TEXT("second advance counts one"), P.AgeTicks, 1.0, 1e-9);
		AdvanceAge(P);
		TestEqual(TEXT("third counts two"), P.AgeTicks, 2.0, 1e-9);
	}

	// A TIER CHANGE RESETS TO ZERO. "New/upgraded buildings start pale" is
	// locked doctrine; this was first wired monotonic and cumulative, which was
	// coherent reasoning that had never been checked against it.
	{
		FParcelState P = Parcel(TEXT("vernacular"), 0, 820.0, true);
		for (int32 i = 0; i < 40; ++i) { AdvanceAge(P); }
		TestEqual(TEXT("aged"), P.AgeTicks, 39.0, 1e-9);

		P.Tier = 1;                       // an upgrade landed
		AdvanceAge(P);
		TestEqual(TEXT("a tier change resets to pale"), P.AgeTicks, 0.0, 1e-9);
		TestEqual(TEXT("and records the new tier"), P.AgeLastTier.GetValue(), 1);
		AdvanceAge(P);
		TestEqual(TEXT("then counts again"), P.AgeTicks, 1.0, 1e-9);
	}
	return true;
}

// --- the fraction ------------------------------------------------------------------
STACKTOWN_AGE_TEST(FStacktownAgeFraction, "Stacktown.Age.Fraction")
{
	TestEqual(TEXT("pale at zero"), AgeFraction(0.0), 0.0, 1e-9);
	TestEqual(TEXT("halfway"), AgeFraction(75.0), 0.5, 1e-9);
	TestEqual(TEXT("mature exactly at the maturity mark"), AgeFraction(AgeMatureTicks), 1.0, 1e-9);
	// SATURATES. A lot standing for a thousand ticks is not ten times mature.
	TestEqual(TEXT("saturates above it"), AgeFraction(1000.0), 1.0, 1e-9);
	TestEqual(TEXT("the maturity mark itself"), AgeMatureTicks, 150.0, 1e-9);
	return true;
}

// --- age advances on CityTick, and NOT inside the economy tick ----------------------
STACKTOWN_AGE_TEST(FStacktownAgeOnCityTick, "Stacktown.Age.OnCityTick")
{
	FScopedEconomy E(true, TEXT("_selftest_age_cpp.json"));
	E->GetMutableState().Parcels.Add(TEXT("P1"), Parcel(TEXT("vernacular"), 0, 1230.0, true));

	// THE ECONOMY TICK MUST NOT TOUCH AGE. Every known answer in the economy
	// oracles asserts exact state equality; if Tick advanced age they would all
	// be wrong for a reason that has nothing to do with the economy.
	{
		FCityState Direct = E->GetState();
		TArray<FEconEvent> Events;
		Tick(E->GetRules(), Direct, Events);
		TestEqual(TEXT("Tick left age alone"), Direct.Parcels[TEXT("P1")].AgeTicks, 0.0, 1e-9);
		TestFalse(TEXT("and recorded no tier"), Direct.Parcels[TEXT("P1")].AgeLastTier.IsSet());
	}

	// CityTick does advance it.
	E->CityTick();
	TestTrue(TEXT("CityTick recorded the tier"), E->GetState().Parcels[TEXT("P1")].AgeLastTier.IsSet());
	TestEqual(TEXT("first CityTick is the reset"), E->GetState().Parcels[TEXT("P1")].AgeTicks, 0.0, 1e-9);
	E->CityTick();
	E->CityTick();
	TestEqual(TEXT("then it counts"), E->GetState().Parcels[TEXT("P1")].AgeTicks, 2.0, 1e-9);

	// And it survives the save the tick performs.
	FCityState Reloaded;
	FString Err;
	TestTrue(TEXT("persisted"), E.ReloadFromDisk(Reloaded, Err));
	TestEqual(TEXT("age on disk"), Reloaded.Parcels[TEXT("P1")].AgeTicks, 2.0, 1e-9);
	TestEqual(TEXT("tier on disk"), Reloaded.Parcels[TEXT("P1")].AgeLastTier.GetValue(), 0);
	return true;
}

// --- the round trip, absence included ------------------------------------------------
STACKTOWN_AGE_TEST(FStacktownAgeRoundTrip, "Stacktown.Age.RoundTrip")
{
	FEconRules R = OracleRules();
	FCityState S = SeedState(R);

	const int32 RecordedTier = 2;
	S.Parcels.Add(TEXT("AGED"),
		Parcel(TEXT("vernacular"), 2, 1230.0, true, 4.0, false, 0.0, 37.0, &RecordedTier));
	// A lot that has never been measured: age_last_tier must stay ABSENT across
	// the trip, or its next advance would count instead of resetting.
	S.Parcels.Add(TEXT("UNMEASURED"), Parcel(TEXT("vernacular"), 0, 820.0, true));

	FCityState Back;
	FString Err;
	TestTrue(TEXT("round trip parses"), CityStateFromJson(CityStateToJson(S), Back, Err));

	TestEqual(TEXT("age ticks survived"), Back.Parcels[TEXT("AGED")].AgeTicks, 37.0, 1e-9);
	TestTrue(TEXT("recorded tier survived"), Back.Parcels[TEXT("AGED")].AgeLastTier.IsSet());
	TestEqual(TEXT("its value"), Back.Parcels[TEXT("AGED")].AgeLastTier.GetValue(), 2);

	TestFalse(TEXT("an unmeasured lot stays unmeasured"),
		Back.Parcels[TEXT("UNMEASURED")].AgeLastTier.IsSet());

	FString Why;
	const bool bSame = StatesEqual(S, Back, 1e-9, Why);
	TestTrue(FString::Printf(TEXT("whole state round-trips (%s)"), *Why), bSame);
	return true;
}

#undef STACKTOWN_AGE_TEST

#endif // WITH_DEV_AUTOMATION_TESTS
