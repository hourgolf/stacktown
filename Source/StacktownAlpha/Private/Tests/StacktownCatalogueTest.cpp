// Stacktown.Catalogue.* - pinned to woodmap.py's own answers, read from the
// oracle on 2026-09-06 (zlib.crc32 values included so a CRC drift is named).
#include "Misc/AutomationTest.h"
#include "StacktownCatalogue.h"

#if WITH_DEV_AUTOMATION_TESTS

using namespace Stacktown::Catalogue;

#define STACKTOWN_CAT_TEST(TestClass, PrettyName) \
	IMPLEMENT_SIMPLE_AUTOMATION_TEST(TestClass, PrettyName, EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter) \
	bool TestClass::RunTest(const FString& Parameters)

STACKTOWN_CAT_TEST(FStacktownCatCrc, "Stacktown.Catalogue.Crc32MatchesZlib")
{
	TestEqual(TEXT("crc32('vernacular')"), Crc32(TEXT("vernacular")), 4180541801u);
	TestEqual(TEXT("crc32('tower')"), Crc32(TEXT("tower")), 1577756512u);
	TestEqual(TEXT("crc32('civic')"), Crc32(TEXT("civic")), 1852225255u);
	TestEqual(TEXT("crc32('shop')"), Crc32(TEXT("shop")), 2892647586u);
	return true;
}

STACKTOWN_CAT_TEST(FStacktownCatSpecies, "Stacktown.Catalogue.SpeciesIsIdentity")
{
	const TCHAR* Cases[][2] = {
		{ TEXT("vernacular"), TEXT("ash") }, { TEXT("vernacular_a"), TEXT("oak") }, { TEXT("vernacular_b"), TEXT("ash") },
		{ TEXT("contemporary"), TEXT("pine") }, { TEXT("contemporary_a"), TEXT("sapele") }, { TEXT("modern"), TEXT("maple") },
		{ TEXT("modern_a"), TEXT("oak") }, { TEXT("tower"), TEXT("oak") }, { TEXT("office"), TEXT("pine") },
		{ TEXT("house"), TEXT("cherry") }, { TEXT("civic"), TEXT("walnut") }, { TEXT("shop"), TEXT("oak") } };
	for (const auto& C : Cases)
	{
		TestEqual(*FString::Printf(TEXT("species for %s"), C[0]), SpeciesFor(C[0]), FString(C[1]));
	}
	// the same rid at every tier and width: the species never depends on them
	TestEqual(TEXT("tier does not change species"), Resolve(TEXT("tower"), 6, 2460.0, true).Species, FString(TEXT("oak")));
	return true;
}

STACKTOWN_CAT_TEST(FStacktownCatBands, "Stacktown.Catalogue.TierBands")
{
	FString B;
	const TCHAR* Expected[7] = { TEXT("flat"), TEXT("flat"), TEXT("setback1"), TEXT("setback1"), TEXT("setback2"), TEXT("setback2"), TEXT("tower") };
	for (int32 T = 0; T < 7; ++T)
	{
		TestTrue(*FString::Printf(TEXT("tier %d has a band"), T), BandForTier(T, B));
		TestEqual(*FString::Printf(TEXT("tier %d band"), T), B, FString(Expected[T]));
	}
	TestFalse(TEXT("tier 7 is off the ladder"), BandForTier(7, B));
	TestFalse(TEXT("tier -1 is off the ladder"), BandForTier(-1, B));
	return true;
}

STACKTOWN_CAT_TEST(FStacktownCatAssets, "Stacktown.Catalogue.AssetNames")
{
	TestEqual(TEXT("820 flat"), AssetName(820.0, TEXT("flat"), false), FString(TEXT("SM_WMass_w820_flat")));
	TestEqual(TEXT("1230 flat corner"), AssetName(1230.0, TEXT("flat"), true), FString(TEXT("SM_WMass_w1230_flat_d1500")));
	TestEqual(TEXT("mass path"), MassAssetPath(TEXT("SM_WMass_w2460_tower")), FString(TEXT("/Game/Stacktown/BakedWood/SM_WMass_w2460_tower.SM_WMass_w2460_tower")));
	TestEqual(TEXT("material path"), SpeciesMaterialPath(TEXT("ash")), FString(TEXT("/Game/Stacktown/Materials/MI_wood_ash.MI_wood_ash")));
	double W;
	TestTrue(TEXT("1230.4 snaps"), NearestWidth(1230.4, W)); TestEqual(TEXT("to 1230"), W, 1230.0, 1e-9);
	TestFalse(TEXT("1000 is between rungs"), NearestWidth(1000.0, W));
	return true;
}

STACKTOWN_CAT_TEST(FStacktownCatResolve, "Stacktown.Catalogue.ResolveErrorsRatherThanGuesses")
{
	FResolved R = Resolve(TEXT("vernacular"), 3, 1640.0, false);
	TestTrue(TEXT("ok"), R.bOk);
	TestEqual(TEXT("asset"), R.Asset, FString(TEXT("SM_WMass_w1640_setback1")));
	TestEqual(TEXT("species"), R.Species, FString(TEXT("ash")));
	TestEqual(TEXT("depth"), R.Depth, 700.0, 1e-9);
	R = Resolve(TEXT("vernacular"), 3, 1640.0, true);
	TestTrue(TEXT("corner ok at 1640"), R.bOk); TestEqual(TEXT("deep asset"), R.Asset, FString(TEXT("SM_WMass_w1640_setback1_d1500"))); TestEqual(TEXT("deep"), R.Depth, 1500.0, 1e-9);
	TestFalse(TEXT("no corner mass at 820"), Resolve(TEXT("vernacular"), 0, 820.0, true).bOk);
	TestFalse(TEXT("tier 9 refused"), Resolve(TEXT("vernacular"), 9, 820.0, false).bOk);
	TestFalse(TEXT("width 999 refused"), Resolve(TEXT("vernacular"), 0, 999.0, false).bOk);
	return true;
}

#endif
