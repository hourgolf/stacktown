// Phase 1 step 3: the state handover (Docs/STATE_HANDOVER.md Phase A).
//
//   UnrealEditor-Cmd <uproject> -ExecCmds="Automation RunTests Stacktown.Handover; Quit" \
//     -unattended -nopause -nullrhi -log
//
// THESE EXPECTATIONS ARE HAND-WRITTEN, NOT ORACLE-GENERATED, and that is a real
// difference from every test in Economy and Placement. The rules being ported
// live inside init_unreal.py, which imports `unreal` and cannot run in this
// seat's container, so there is no headless oracle to generate against. They are
// ported by reading _state_path_source / _state_path_for / _sync_parcels. Weaker
// evidence, said plainly: the proof of step 3 is the coordinator's live
// agreement check, where every standing lot must match the Python sync.

#include "Misc/AutomationTest.h"
#include "StacktownStateHandover.h"
#include "StacktownParcel.h"
#include "StacktownEconomy.h"
#include "StacktownRuntimeSettings.h"
#include "StacktownEconomyTestCommon.h"
#include "StacktownSubsystemTestFixture.h"

#if WITH_DEV_AUTOMATION_TESTS

using namespace Stacktown;
using namespace StacktownTest;

#define STACKTOWN_HANDOVER_TEST(TestClass, PrettyName) \
	IMPLEMENT_SIMPLE_AUTOMATION_TEST(TestClass, PrettyName, \
		EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter) \
	bool TestClass::RunTest(const FString& Parameters)

namespace
{
	FStatePathInputs BaseInputs()
	{
		FStatePathInputs In;
		In.DefaultStatePath = TEXT("/proj/Content/Python/citystate.json");
		In.TestStatePath    = TEXT("/proj/Content/Python/citystate_test.json");
		return In;
	}
}

// --- the four rules, in priority order ------------------------------------------
STACKTOWN_HANDOVER_TEST(FStacktownHandoverPathRules, "Stacktown.Handover.StatePathRules")
{
	// THE DEFAULT IS THE OWNER'S REAL FILE. A lane must opt OUT deliberately,
	// every time. An earlier Python cut had this inverted and put the owner on
	// the test path, because a hand-started session sets nothing either.
	{
		const FStatePathResolution R = ResolveStatePath(BaseInputs());
		TestEqual(TEXT("default path"), R.Path, FString(TEXT("/proj/Content/Python/citystate.json")));
		TestEqual(TEXT("default source"), StateSourceName(R.Source), FString(TEXT("default")));
	}
	// An override wins over everything, including the lock and the marker.
	{
		FStatePathInputs In = BaseInputs();
		In.Override = TEXT("/somewhere/else.json");
		In.bStandalonePidAlive = true;
		In.bMarkerExists = true;
		In.MarkerContent = TEXT("/marker/path.json");
		const FStatePathResolution R = ResolveStatePath(In);
		TestEqual(TEXT("override path"), R.Path, FString(TEXT("/somewhere/else.json")));
		TestEqual(TEXT("override source"), StateSourceName(R.Source), FString(TEXT("override")));
	}
	// A live standalone game holds the save, so an EDITOR session steps aside.
	{
		FStatePathInputs In = BaseInputs();
		In.bStandalonePidAlive = true;
		In.bIsGameProcess = false;
		const FStatePathResolution R = ResolveStatePath(In);
		TestEqual(TEXT("lock path"), R.Path, In.TestStatePath);
		TestEqual(TEXT("lock source"), StateSourceName(R.Source), FString(TEXT("standalone-lock")));
	}
	// ...but the game process itself is the legitimate holder and does NOT step
	// aside from its own lock. Getting this backwards would push the running
	// game onto the test file, which is the exact bug the cache exists for.
	{
		FStatePathInputs In = BaseInputs();
		In.bStandalonePidAlive = true;
		In.bIsGameProcess = true;
		const FStatePathResolution R = ResolveStatePath(In);
		TestEqual(TEXT("game process keeps the real file"), R.Path, In.DefaultStatePath);
		TestEqual(TEXT("and says default"), StateSourceName(R.Source), FString(TEXT("default")));
	}
	// The marker's CONTENT is the path when non-empty...
	{
		FStatePathInputs In = BaseInputs();
		In.bMarkerExists = true;
		In.MarkerContent = TEXT("  /lane/own.json\n");
		const FStatePathResolution R = ResolveStatePath(In);
		TestEqual(TEXT("marker content trimmed"), R.Path, FString(TEXT("/lane/own.json")));
		TestEqual(TEXT("marker source"), StateSourceName(R.Source), FString(TEXT("marker")));
	}
	// ...and empty or whitespace-only content means the test path, not an empty
	// path. A marker written with `touch` is the common case.
	for (const TCHAR* Content : { TEXT(""), TEXT("   "), TEXT("\n\t ") })
	{
		FStatePathInputs In = BaseInputs();
		In.bMarkerExists = true;
		In.MarkerContent = Content;
		const FStatePathResolution R = ResolveStatePath(In);
		TestEqual(TEXT("empty marker means the test path"), R.Path, In.TestStatePath);
		TestEqual(TEXT("still the marker source"), StateSourceName(R.Source), FString(TEXT("marker")));
	}
	// The lock outranks the marker.
	{
		FStatePathInputs In = BaseInputs();
		In.bStandalonePidAlive = true;
		In.bMarkerExists = true;
		In.MarkerContent = TEXT("/lane/own.json");
		const FStatePathResolution R = ResolveStatePath(In);
		TestEqual(TEXT("lock beats marker"), StateSourceName(R.Source), FString(TEXT("standalone-lock")));
	}
	return true;
}

// --- dormant pool actors are not parcels -------------------------------------------
STACKTOWN_HANDOVER_TEST(FStacktownHandoverPoolLabels, "Stacktown.Handover.PoolLabels")
{
	TestTrue(TEXT("POOL_00"), IsPoolLabel(TEXT("POOL_00")));
	TestTrue(TEXT("POOL_PIN_NE0"), IsPoolLabel(TEXT("POOL_PIN_NE0")));
	TestFalse(TEXT("P1 is a real parcel"), IsPoolLabel(TEXT("P1")));
	TestFalse(TEXT("NE0 is a real parcel"), IsPoolLabel(TEXT("NE0")));
	// Case-sensitive on purpose: the builder writes POOL_ exactly, and a
	// case-insensitive test would swallow a differently-named real parcel.
	TestFalse(TEXT("pool_00 is not the prefix"), IsPoolLabel(TEXT("pool_00")));
	return true;
}

// --- the facts an actor shows ---------------------------------------------------
STACKTOWN_HANDOVER_TEST(FStacktownHandoverFacts, "Stacktown.Handover.FactsForLabel")
{
	const FEconRules R = OracleRules();
	FCityState S = SeedState(R);

	FParcelState P = Parcel(TEXT("vernacular"), 2, 1230.0, true, 7.5, true, -0.5);
	S.Parcels.Add(TEXT("NE0"), P);

	const FParcelFacts F = FactsForLabel(R, S, TEXT("NE0"));
	TestTrue(TEXT("found"), F.bFound);
	TestEqual(TEXT("rid"), F.Rid, FString(TEXT("vernacular")));
	TestEqual(TEXT("width"), F.Width, 1230.0, 1e-9);
	TestEqual(TEXT("tier"), F.Tier, 2);
	TestEqual(TEXT("owned"), BoolStr(F.bOwned), BoolStr(true));
	TestEqual(TEXT("failed"), BoolStr(F.bFailed), BoolStr(true));
	TestEqual(TEXT("accum"), F.Accum, 7.5, 1e-9);
	TestFalse(TEXT("a pinned lot is not placed"), F.bPlaced);
	// PRICE IS RECOMPUTED, not read from state - it depends on Tier, and a
	// stored copy is one more thing that can disagree with the tier beside it.
	TestEqual(TEXT("price recomputed from tier and width"),
		F.Price, Price(R, 2, 1230.0), 1e-9);

	// An absent label yields nothing, and every field stays at its default. A
	// lot the Python side has not registered yet is not a lot whose tier is 0.
	const FParcelFacts Missing = FactsForLabel(R, S, TEXT("NOPE"));
	TestFalse(TEXT("absent label is not found"), Missing.bFound);
	TestEqual(TEXT("and carries no tier"), Missing.Tier, 0);
	return true;
}

// --- the actor applies them ------------------------------------------------------
STACKTOWN_HANDOVER_TEST(FStacktownHandoverParcelApply, "Stacktown.Handover.ParcelApplyFacts")
{
	TStrongObjectPtr<AStacktownParcel> P(NewObject<AStacktownParcel>(GetTransientPackage()));
	P->RecipeId = TEXT("vernacular");
	P->WidthUU = 1230.0;

	TestFalse(TEXT("nothing is a fact before the first sync"), P->bSynced);

	FParcelFacts F;
	F.bFound = true;
	F.Tier = 3;
	F.bOwned = true;
	F.bFailed = false;
	F.Price = 137.5;
	F.Accum = 9.25;
	F.bPlaced = true;

	TestTrue(TEXT("first apply changes something"), P->ApplyFacts(F));
	TestEqual(TEXT("tier"), P->Tier, 3);
	TestEqual(TEXT("owned"), BoolStr(P->bOwned), BoolStr(true));
	TestEqual(TEXT("price"), P->Price, 137.5, 1e-9);
	TestEqual(TEXT("accum"), P->Accum, 9.25, 1e-9);
	TestTrue(TEXT("synced"), P->bSynced);
	// IDENTITY IS NEVER WRITTEN BACK. The state's copies came from the actor in
	// the first place; a sync that pushed them back would let the two argue
	// about who a parcel is.
	TestEqual(TEXT("rid untouched"), P->RecipeId, FString(TEXT("vernacular")));
	TestEqual(TEXT("width untouched"), P->WidthUU, 1230.0, 1e-9);

	// WRITE ON CHANGE: the same facts again change nothing.
	TestFalse(TEXT("re-applying identical facts is a no-op"), P->ApplyFacts(F));

	// A label absent from the mirror must not blank a parcel that already synced.
	const FParcelFacts NotFound;
	TestFalse(TEXT("absent facts change nothing"), P->ApplyFacts(NotFound));
	TestEqual(TEXT("tier survived"), P->Tier, 3);
	TestTrue(TEXT("still synced"), P->bSynced);
	return true;
}

// --- mirroring: read-only, and never a second writer ------------------------------
STACKTOWN_HANDOVER_TEST(FStacktownHandoverMirror, "Stacktown.Handover.MirrorFromFile")
{
	// bPersist=false: a mirroring subsystem must NOT have a StatePath.
	FScopedEconomy E(false, TEXT("_selftest_mirror_cpp.json"));

	FCityState Source = SeedState(E->GetRules());
	Source.Money = 321.5;
	Source.Parcels.Add(TEXT("NE0"), Parcel(TEXT("vernacular"), 4, 1230.0, true, 3.25));
	TestTrue(TEXT("wrote a source file"), E.WriteRaw(CityStateToJson(Source)));

	FString Err;
	TestTrue(TEXT("mirror succeeds"), E->MirrorFromFile(E.Path, Err));
	TestEqual(TEXT("no error"), Err, FString());
	TestEqual(TEXT("sync counted"), E->GetMirrorSyncCount(), 1);
	TestEqual(TEXT("money mirrored"), E->GetMoney(), 321.5, 1e-9);
	TestEqual(TEXT("parcel mirrored"), E->GetState().Parcels[TEXT("NE0")].Tier, 4);

	// A TRUNCATED FILE MUST NOT BLANK THE MIRROR. The Python side rewrites this
	// file whole, so a read can land mid-write; committing that would show every
	// parcel as gone for a frame.
	TestTrue(TEXT("wrote a truncated file"), E.WriteRaw(TEXT("{\"money\": 32")));
	FString TruncErr;
	TestFalse(TEXT("mirror refuses a truncated file"), E->MirrorFromFile(E.Path, TruncErr));
	TestFalse(TEXT("and says why"), TruncErr.IsEmpty());
	TestEqual(TEXT("previous mirror intact"), E->GetMoney(), 321.5, 1e-9);
	TestEqual(TEXT("and was not counted as a sync"), E->GetMirrorSyncCount(), 1);

	// A missing file is refused rather than treated as an empty city.
	FString MissingErr;
	TestFalse(TEXT("missing file refused"),
		E->MirrorFromFile(E.Path + TEXT(".nope"), MissingErr));
	TestEqual(TEXT("money still intact"), E->GetMoney(), 321.5, 1e-9);
	return true;
}

// TWO WRITERS IS THE ONE THING THIS CONTRACT EXISTS TO PREVENT. A subsystem that
// owns a file must refuse to also mirror one.
STACKTOWN_HANDOVER_TEST(FStacktownHandoverNoTwoWriters, "Stacktown.Handover.MirrorRefusesWhenOwning")
{
	FScopedEconomy E(true, TEXT("_selftest_twowriters_cpp.json"));   // StatePath IS set
	FCityState Source = SeedState(E->GetRules());
	Source.Money = 99.0;
	TestTrue(TEXT("wrote a source file"), E.WriteRaw(CityStateToJson(Source)));

	// The refusal logs at Error, deliberately - two writers is the failure this
	// whole contract exists to prevent, and it should be loud. The automation
	// framework fails any test that logs an Error unless the test declares it,
	// so the expectation is declared rather than the log quietened.
	AddExpectedError(TEXT("refusing to mirror"), EAutomationExpectedErrorFlags::Contains, 1);

	FString Err;
	TestFalse(TEXT("mirroring is refused while owning a path"), E->MirrorFromFile(E.Path, Err));
	TestFalse(TEXT("and says why"), Err.IsEmpty());
	TestEqual(TEXT("no sync counted"), E->GetMirrorSyncCount(), 0);
	return true;
}

// --- the Python-drivers switch, precedence exhausted --------------------------------
STACKTOWN_HANDOVER_TEST(FStacktownHandoverPythonDrivers, "Stacktown.Handover.PythonDrivers")
{
	// NO PLUGIN WINS OVER EVERYTHING. A packaged app has no Python at all, so no
	// ini key and no environment variable may claim otherwise.
	{
		FPythonDriversInputs In;
		In.bPluginLoaded = false;
		In.EnvValue = TEXT("1");
		In.bFoundInNewSection = true;
		In.bNewSectionValue = true;
		TestFalse(TEXT("no plugin, no drivers"), ResolvePythonDrivers(In));
	}
	// The environment beats both ini sections, in either direction.
	for (const TCHAR* Off : { TEXT("0"), TEXT("false"), TEXT("FALSE"), TEXT("no") })
	{
		FPythonDriversInputs In;
		In.EnvValue = Off;
		In.bFoundInLegacySection = true;
		In.bLegacySectionValue = true;
		TestFalse(FString::Printf(TEXT("env '%s' turns them off"), Off), ResolvePythonDrivers(In));
	}
	{
		FPythonDriversInputs In;
		In.EnvValue = TEXT("1");
		In.bFoundInNewSection = true;
		In.bNewSectionValue = false;
		TestTrue(TEXT("env beats the ini"), ResolvePythonDrivers(In));
	}
	// The new section beats the legacy one...
	{
		FPythonDriversInputs In;
		In.bFoundInNewSection = true;
		In.bNewSectionValue = false;
		In.bFoundInLegacySection = true;
		In.bLegacySectionValue = true;
		TestFalse(TEXT("the new section wins"), ResolvePythonDrivers(In));
	}
	// ...and the legacy one is still honoured on its own, which is the whole
	// point: Config/ is not this seat's to edit and the shipped key must work.
	{
		FPythonDriversInputs In;
		In.bFoundInLegacySection = true;
		In.bLegacySectionValue = false;
		TestFalse(TEXT("the legacy section is honoured"), ResolvePythonDrivers(In));
	}
	// DEFAULT ON. The Python drivers were the world before Phase B; a missing
	// key must not silently switch who owns a session.
	{
		FPythonDriversInputs In;
		TestTrue(TEXT("nothing set means on"), ResolvePythonDrivers(In));
	}
	return true;
}

// --- the session path is decided once, and an override re-decides it ----------------
STACKTOWN_HANDOVER_TEST(FStacktownHandoverSessionPathCached, "Stacktown.Handover.SessionPathCached")
{
	FScopedEconomy E(false, TEXT("_selftest_sessionpath_cpp.json"));

	// Initialize resolves it (queue item 2); the fixture builds the subsystem
	// without the engine lifecycle, so this stands in for that call. What is
	// tested is the CONTRACT: resolved once, then read from the cache.
	EStateSource Source = EStateSource::Override;
	const FString First = E->StatePathForSession(Source, true);
	TestFalse(TEXT("a path was resolved"), First.IsEmpty());
	TestEqual(TEXT("the cache agrees"), E->GetSessionStatePath(), First);
	TestEqual(TEXT("and so does the source"),
		StateSourceName(E->GetSessionStateSource()), StateSourceName(Source));

	// A second read does not re-resolve.
	EStateSource Again = EStateSource::Override;
	TestEqual(TEXT("second read is the cache"), E->StatePathForSession(Again, false), First);

	// AN OVERRIDE MUST TAKE EFFECT IMMEDIATELY. The path is already decided by
	// the time anyone can set one, so an override that waited for a re-resolve
	// would leave a lane on the owner's real save while its log said override.
	E->SetStateOverride(TEXT("/tmp/stacktown_override.json"));
	TestEqual(TEXT("override applied at once"), E->GetSessionStatePath(),
		FString(TEXT("/tmp/stacktown_override.json")));
	TestEqual(TEXT("and is reported as the source"),
		StateSourceName(E->GetSessionStateSource()), FString(TEXT("override")));
	return true;
}

// --- ParcelId is explicit, not derived ----------------------------------------------
STACKTOWN_HANDOVER_TEST(FStacktownHandoverParcelId, "Stacktown.Handover.ParcelId")
{
	TStrongObjectPtr<AStacktownParcel> P(NewObject<AStacktownParcel>(GetTransientPackage()));

	// With nothing set it falls back - the weak path, kept only for actors a
	// person placed by hand.
	TestFalse(TEXT("a fallback id is still something"), P->GetParcelId().IsEmpty());

	// Set explicitly, it wins. This is what the spawner does, and it is why a
	// second parcel spawned as "P1" - which the engine uniquifies to "P1_2" -
	// still matches its own entry in the city state.
	P->ParcelId = TEXT("P7");
	TestEqual(TEXT("the explicit id wins"), P->GetParcelId(), FString(TEXT("P7")));

	// And it is what the pool check reads, so a dormant actor is still skipped.
	P->ParcelId = TEXT("POOL_03");
	TestTrue(TEXT("a pool id is recognised through ParcelId"), P->IsDormantPoolActor());
	P->ParcelId = TEXT("NE0");
	TestFalse(TEXT("a real parcel is not"), P->IsDormantPoolActor());
	return true;
}

#undef STACKTOWN_HANDOVER_TEST

#endif // WITH_DEV_AUTOMATION_TESTS
