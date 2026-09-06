#include "Misc/AutomationTest.h"
#include "StacktownRoadTransform.h"

#if WITH_DEV_AUTOMATION_TESTS

using namespace Stacktown;

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStacktownRoadFrameTest, "Stacktown.RoadTransform.SegmentPose", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FStacktownRoadFrameTest::RunTest(const FString& Parameters)
{
	FRoadSegment S; S.StartX = 2000.0; S.StartY = -5000.0; S.EndX = 6000.0; S.EndY = -5000.0;
	RoadFrame::FPose P = RoadFrame::Transform(S);
	TestEqual(TEXT("centre x"), P.Location.X, 4000.0, 1e-9); TestEqual(TEXT("centre y"), P.Location.Y, -5000.0, 1e-9); TestEqual(TEXT("z = -3 (top at +1, an inlay)"), P.Location.Z, -3.0, 1e-9);
	TestEqual(TEXT("yaw 0 east"), P.Rotation.Yaw, 0.0, 1e-9);
	TestEqual(TEXT("scale x = length / 100"), P.Scale.X, 40.0, 1e-9); TestEqual(TEXT("scale y = corridor / 100"), P.Scale.Y, 22.6, 1e-9); TestEqual(TEXT("thin z"), P.Scale.Z, 0.08, 1e-9);
	FRoadSegment V; V.StartX = 3000.0; V.StartY = 1000.0; V.EndX = 3000.0; V.EndY = -2000.0;
	P = RoadFrame::Transform(V);
	TestEqual(TEXT("vertical yaw -90"), P.Rotation.Yaw, -90.0, 1e-9); TestEqual(TEXT("vertical length"), P.Length, 3000.0, 1e-9);
	FRoadSegment Z; P = RoadFrame::Transform(Z);
	TestEqual(TEXT("a zero chord still scales to one unit"), P.Scale.X, 0.01, 1e-9);
	return true;
}

#endif
