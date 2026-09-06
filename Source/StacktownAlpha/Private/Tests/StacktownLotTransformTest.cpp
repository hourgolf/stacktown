// Stacktown.LotTransform.* - init_unreal._lot_transform's four frames and the
// two mesh offsets, with the numbers the Python states in its own docstring.
#include "Misc/AutomationTest.h"
#include "StacktownLotTransform.h"

#if WITH_DEV_AUTOMATION_TESTS

using namespace Stacktown;

#define STACKTOWN_LOT_TEST(TestClass, PrettyName) \
	IMPLEMENT_SIMPLE_AUTOMATION_TEST(TestClass, PrettyName, EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter) \
	bool TestClass::RunTest(const FString& Parameters)

namespace
{
	FRoad MakeRoad(const TCHAR* Id, bool bAxisX, double Sx, double Sy, double Ex, double Ey)
	{
		FRoad R; R.Id = Id; R.bAxisX = bAxisX; R.StartX = Sx; R.StartY = Sy; R.EndX = Ex; R.EndY = Ey;
		if (bAxisX) { R.SidePlus = TEXT("north"); R.SideMinus = TEXT("south"); }
		else        { R.SidePlus = TEXT("west");  R.SideMinus = TEXT("east"); }
		return R;
	}
	FLotPlacement MakeLot(double X0, double X1, const TCHAR* Side, const TCHAR* RoadId = nullptr)
	{
		FLotPlacement L; L.X0 = X0; L.X1 = X1; L.Side = Side;
		if (RoadId) { L.RoadId = FString(RoadId); }
		return L;
	}
	TArray<FRoad> BuiltIns()
	{
		return { MakeRoad(TEXT("arterial"), true, -7650.0, 0.0, 7650.0, 0.0), MakeRoad(TEXT("cross"), false, 0.0, -4230.0, 0.0, 4230.0) };
	}
}

STACKTOWN_LOT_TEST(FStacktownLotArterial, "Stacktown.LotTransform.ArterialFrames")
{
	LotFrame::FPose P;
	TestTrue(TEXT("north resolves"), LotFrame::Pose(MakeLot(100.0, 920.0, TEXT("north")), BuiltIns(), P));
	TestEqual(TEXT("north x = x0"), P.X, 100.0, 1e-9); TestEqual(TEXT("north y = +1880"), P.Y, 1880.0, 1e-9); TestEqual(TEXT("north yaw 0"), P.Yaw, 0.0, 1e-9);
	TestTrue(TEXT("south resolves"), LotFrame::Pose(MakeLot(100.0, 920.0, TEXT("south")), BuiltIns(), P));
	TestEqual(TEXT("south x = x1"), P.X, 920.0, 1e-9); TestEqual(TEXT("south y = -1880"), P.Y, -1880.0, 1e-9); TestEqual(TEXT("south yaw 180"), P.Yaw, 180.0, 1e-9);
	return true;
}

STACKTOWN_LOT_TEST(FStacktownLotCross, "Stacktown.LotTransform.CrossFrames")
{
	LotFrame::FPose P;
	TestTrue(TEXT("west resolves"), LotFrame::Pose(MakeLot(-3000.0, -2180.0, TEXT("west"), TEXT("cross")), BuiltIns(), P));
	TestEqual(TEXT("west x = -1880"), P.X, -1880.0, 1e-9); TestEqual(TEXT("west y = x0"), P.Y, -3000.0, 1e-9); TestEqual(TEXT("west yaw 90"), P.Yaw, 90.0, 1e-9);
	TestTrue(TEXT("east resolves"), LotFrame::Pose(MakeLot(-3000.0, -2180.0, TEXT("east"), TEXT("cross")), BuiltIns(), P));
	TestEqual(TEXT("east x = +1880"), P.X, 1880.0, 1e-9); TestEqual(TEXT("east y = x1"), P.Y, -2180.0, 1e-9); TestEqual(TEXT("east yaw -90"), P.Yaw, -90.0, 1e-9);
	return true;
}

STACKTOWN_LOT_TEST(FStacktownLotDrawn, "Stacktown.LotTransform.DrawnRoadFrame")
{
	// the 2026-09-04 scar: a P9 on R1 was activated on the arterial's frame
	TArray<FRoad> Roads = BuiltIns();
	Roads.Add(MakeRoad(TEXT("R1"), true, 2000.0, -5000.0, 6000.0, -5000.0));
	LotFrame::FPose P;
	TestTrue(TEXT("R1 north resolves"), LotFrame::Pose(MakeLot(3110.0, 3930.0, TEXT("north"), TEXT("R1")), Roads, P));
	TestEqual(TEXT("x = x0"), P.X, 3110.0, 1e-9); TestEqual(TEXT("y = -5000 + 1880"), P.Y, -3120.0, 1e-9); TestEqual(TEXT("yaw 0"), P.Yaw, 0.0, 1e-9);
	// an unknown road id falls back to the arterial, as the Python does
	TestTrue(TEXT("unknown road falls back"), LotFrame::Pose(MakeLot(0.0, 820.0, TEXT("south"), TEXT("R9")), Roads, P));
	TestEqual(TEXT("fallback y"), P.Y, -1880.0, 1e-9);
	TestFalse(TEXT("no roads at all: no pose"), LotFrame::Pose(MakeLot(0.0, 820.0, TEXT("north")), {}, P));
	return true;
}

STACKTOWN_LOT_TEST(FStacktownLotOffsets, "Stacktown.LotTransform.MeshOffsets")
{
	TestEqual(TEXT("pad centre line 1880"), LotFrame::PadCentreY, 1880.0, 1e-9);
	TestTrue(TEXT("pad cube: half a width along +x"), LotFrame::PadOffset(1230.0).Equals(FVector(615.0, 0.0, 0.0)));
	TestTrue(TEXT("mass: 750 toward the road"), LotFrame::MassOffset().Equals(FVector(0.0, -750.0, 0.0)));
	return true;
}

#endif
