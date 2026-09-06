// Stacktown.Camera.* - the pure pose arithmetic behind the C++ camera
// (StacktownCameraModel.h). Each case states the number it expects and where
// it comes from, and each is a rule input can break.
#include "Misc/AutomationTest.h"
#include "StacktownCameraModel.h"

#if WITH_DEV_AUTOMATION_TESTS

using namespace Stacktown::Camera;

#define STACKTOWN_CAM_TEST(TestClass, PrettyName) \
	IMPLEMENT_SIMPLE_AUTOMATION_TEST(TestClass, PrettyName, EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter) \
	bool TestClass::RunTest(const FString& Parameters)

// The rig's BeginPlay pose (azimuth 250, reach 19000, height 9000) expressed
// as focus/yaw/pitch/distance must land the camera where the rig stood.
STACKTOWN_CAM_TEST(FStacktownCamRigPose, "Stacktown.Camera.RigPoseMatches")
{
	const FVector Loc = LocationForPose(FVector::ZeroVector, 70.0, -25.3459, 21023.8);
	const FVector RigLoc(19000.0 * FMath::Cos(FMath::DegreesToRadians(250.0)), 19000.0 * FMath::Sin(FMath::DegreesToRadians(250.0)), 9000.0);
	TestTrue(TEXT("camera stands where the rig stood (within 5 uu)"), FVector::Dist(Loc, RigLoc) < 5.0);
	const FVector Dir = RotationForPose(70.0, -25.3459).Vector();
	TestTrue(TEXT("and looks at the focus"), FVector::Dist(Loc + Dir * 21023.8, FVector::ZeroVector) < 1.0);
	return true;
}

STACKTOWN_CAM_TEST(FStacktownCamFocal, "Stacktown.Camera.FocalLadder")
{
	FLimits L;
	TestEqual(TEXT("wide stop at max distance"), FocalForDistance(L.MaxDistance, L), 24.0, 1e-6);
	TestEqual(TEXT("close stop at min distance"), FocalForDistance(L.MinDistance, L), 200.0, 1e-6);
	const double Mid = FocalForDistance(FMath::Sqrt(L.MinDistance * L.MaxDistance), L);
	TestEqual(TEXT("geometric midpoint is the arithmetic middle focal"), Mid, 112.0, 1e-6);
	TestTrue(TEXT("longer lens as the camera closes in"), FocalForDistance(3000.0, L) > FocalForDistance(9000.0, L));
	TestEqual(TEXT("the rig's 24 mm is a 73.7 degree field"), FovForFocal(24.0), 73.7398, 0.01);
	return true;
}

STACKTOWN_CAM_TEST(FStacktownCamZoomToward, "Stacktown.Camera.ZoomKeepsCursorPoint")
{
	FLimits L; FBounds2D B;
	FVector Focus(0.0, 0.0, 0.0);
	double Dist = 10000.0;
	const FVector P(2000.0, -1000.0, 0.0);
	ZoomToward(P, 0.5, L, B, Focus, Dist);
	TestEqual(TEXT("distance halves"), Dist, 5000.0, 1e-6);
	TestTrue(TEXT("focus slides halfway to the cursor point"), FVector::Dist(Focus, FVector(1000.0, -500.0, 0.0)) < 1e-6);
	// zooming out again from the same point returns to the start
	ZoomToward(P, 2.0, L, B, Focus, Dist);
	TestTrue(TEXT("and back out is the inverse"), FVector::Dist(Focus, FVector::ZeroVector) < 1e-6 && FMath::IsNearlyEqual(Dist, 10000.0));
	// clamped at the close stop: the ratio follows the clamped distance
	Dist = 1500.0; Focus = FVector::ZeroVector;
	ZoomToward(P, 0.1, L, B, Focus, Dist);
	TestEqual(TEXT("distance clamps at MinDistance"), Dist, L.MinDistance, 1e-6);
	TestTrue(TEXT("focus moved only by the clamped ratio"), FVector::Dist(Focus, P + (FVector::ZeroVector - P) * (L.MinDistance / 1500.0)) < 1e-6);
	return true;
}

STACKTOWN_CAM_TEST(FStacktownCamClamps, "Stacktown.Camera.Clamps")
{
	FLimits L; FBounds2D B;
	TestEqual(TEXT("pitch never flatter than MaxPitch"), ClampPitch(10.0, L), L.MaxPitch, 1e-9);
	TestEqual(TEXT("pitch never past straight down"), ClampPitch(-100.0, L), L.MinPitch, 1e-9);
	const FVector F = ClampFocus(FVector(100000.0, -100000.0, 55.0), B);
	TestTrue(TEXT("focus clamps to the board and sits on the plane"), F.X == B.MaxX && F.Y == B.MinY && F.Z == 0.0);
	TestEqual(TEXT("distance clamps"), ClampDistance(1.0, L), L.MinDistance, 1e-9);
	return true;
}

STACKTOWN_CAM_TEST(FStacktownCamPlane, "Stacktown.Camera.BoardPlaneUnderCursor")
{
	FVector P;
	TestTrue(TEXT("a downward ray hits the plane"), IntersectBoardPlane(FVector(0.0, 0.0, 1000.0), FVector(0.0, 0.6, -0.8), P));
	TestTrue(TEXT("at the expected point"), FVector::Dist(P, FVector(0.0, 750.0, 0.0)) < 1e-6);
	TestFalse(TEXT("a ray looking up never hits"), IntersectBoardPlane(FVector(0.0, 0.0, 1000.0), FVector(0.0, 0.6, 0.8), P));
	TestFalse(TEXT("a level ray never hits"), IntersectBoardPlane(FVector(0.0, 0.0, 1000.0), FVector(1.0, 0.0, 0.0), P));
	return true;
}

STACKTOWN_CAM_TEST(FStacktownCamPan, "Stacktown.Camera.PanBasis")
{
	FVector Fwd, Right;
	PanBasis(90.0, Fwd, Right);
	TestTrue(TEXT("yaw 90 looks along +Y"), FVector::Dist(Fwd, FVector(0.0, 1.0, 0.0)) < 1e-6);
	TestTrue(TEXT("its right is -X"), FVector::Dist(Right, FVector(-1.0, 0.0, 0.0)) < 1e-6);
	TestEqual(TEXT("view width at focus: 2 d tan(fov/2)"), ViewWidthAtFocus(1000.0, 90.0), 2000.0, 1e-6);
	return true;
}

#endif
