#include "Misc/AutomationTest.h"
#include "StacktownRoadTransform.h"
#include "StacktownPlacement.h"

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

// The mitre (design lane 2026-09-07 05:32): two chords that share a joint and
// are each given JointTangent for it get the SAME two corners there.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStacktownRoadMitreTest, "Stacktown.RoadTransform.Mitre", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FStacktownRoadMitreTest::RunTest(const FString& Parameters)
{
	// a straight joint is square
	TestEqual(TEXT("straight: tan 0"), RoadFrame::JointTangent(FVector2D(1, 0), FVector2D(1, 0)), 0.0, 1e-12);
	// a 90 degree turn toward +y: tan(45) = 1, and it is the limit
	TestEqual(TEXT("quarter turn toward +y: tan 1"), RoadFrame::JointTangent(FVector2D(1, 0), FVector2D(0, 1)), 1.0, 1e-9);
	TestEqual(TEXT("quarter turn toward -y: tan -1"), RoadFrame::JointTangent(FVector2D(1, 0), FVector2D(0, -1)), -1.0, 1e-9);
	TestEqual(TEXT("a hairpin is cut as a quarter turn"), RoadFrame::JointTangent(FVector2D(1, 0), FVector2D(-1, 0.01)), RoadFrame::MitreLimit, 1e-9);
	TestEqual(TEXT("a degenerate direction is square"), RoadFrame::JointTangent(FVector2D::ZeroVector, FVector2D(0, 1)), 0.0, 1e-12);

	// A east 100 then B north 100, 20 wide: the joint corners coincide.
	FRoadSegment A; A.StartX = 0; A.StartY = 0; A.EndX = 100; A.EndY = 0;
	FRoadSegment B; B.StartX = 100; B.StartY = 0; B.EndX = 100; B.EndY = 100;
	const double T = RoadFrame::JointTangent(RoadFrame::Direction(A), RoadFrame::Direction(B));
	FVector2D CA[4], CB[4];
	RoadFrame::Corners(A, 20.0, 0.0, T, CA);
	RoadFrame::Corners(B, 20.0, T, 0.0, CB);
	TestEqual(TEXT("A end +y == B start +y (x)"), CA[3].X, CB[0].X, 1e-9); TestEqual(TEXT("A end +y == B start +y (y)"), CA[3].Y, CB[0].Y, 1e-9);
	TestEqual(TEXT("A end -y == B start -y (x)"), CA[2].X, CB[1].X, 1e-9); TestEqual(TEXT("A end -y == B start -y (y)"), CA[2].Y, CB[1].Y, 1e-9);
	TestEqual(TEXT("the inner corner sits back on the bisector"), CA[3].X, 90.0, 1e-9); TestEqual(TEXT("inner corner y"), CA[3].Y, 10.0, 1e-9);
	TestEqual(TEXT("the outer corner reaches past the joint"), CA[2].X, 110.0, 1e-9); TestEqual(TEXT("outer corner y"), CA[2].Y, -10.0, 1e-9);
	// A's free start stays square
	TestEqual(TEXT("free start +y x"), CA[0].X, 0.0, 1e-9); TestEqual(TEXT("free start -y x"), CA[1].X, 0.0, 1e-9);

	// ChainJoints: the shared joint carries one number on both sides; a break
	// in the chain (B2 does not start where A ended) keeps square ends.
	TArray<FRoadSegment> Chain; Chain.Add(A); Chain.Add(B);
	const TArray<RoadFrame::FJoint> J = RoadFrame::ChainJoints(Chain);
	TestEqual(TEXT("chain: A.TanEnd"), J[0].TanEnd, T, 1e-12); TestEqual(TEXT("chain: B.TanStart"), J[1].TanStart, T, 1e-12);
	TestEqual(TEXT("chain: A.TanStart free"), J[0].TanStart, 0.0, 1e-12); TestEqual(TEXT("chain: B.TanEnd free"), J[1].TanEnd, 0.0, 1e-12);
	FRoadSegment B2 = B; B2.StartX = 130.0;
	TArray<FRoadSegment> Broken; Broken.Add(A); Broken.Add(B2);
	const TArray<RoadFrame::FJoint> JB = RoadFrame::ChainJoints(Broken);
	TestEqual(TEXT("a gap in the chain is not a joint"), JB[0].TanEnd, 0.0, 1e-12);

	// PathJoints: a three-chord path held out of order in a map, plus a lone road.
	TMap<FString, FRoadSegment> Roads;
	FRoadSegment C; C.StartX = 100; C.StartY = 100; C.EndX = 0; C.EndY = 100;   // west after the north chord
	A.Path = B.Path = C.Path = TEXT("C1");
	Roads.Add(TEXT("R9"), C); Roads.Add(TEXT("R7"), A); Roads.Add(TEXT("R8"), B);
	FRoadSegment Lone; Lone.StartX = 5000; Lone.StartY = 5000; Lone.EndX = 6000; Lone.EndY = 5000;
	Roads.Add(TEXT("R3"), Lone);
	const TMap<FString, RoadFrame::FJoint> PJ = RoadFrame::PathJoints(Roads);
	TestEqual(TEXT("path: first chord start free"), PJ[TEXT("R7")].TanStart, 0.0, 1e-12);
	TestEqual(TEXT("path: first chord end"), PJ[TEXT("R7")].TanEnd, 1.0, 1e-9);
	TestEqual(TEXT("path: middle chord start"), PJ[TEXT("R8")].TanStart, 1.0, 1e-9);
	TestEqual(TEXT("path: middle chord end (another turn toward +y)"), PJ[TEXT("R8")].TanEnd, 1.0, 1e-9);
	TestEqual(TEXT("path: last chord end free"), PJ[TEXT("R9")].TanEnd, 0.0, 1e-12);
	TestEqual(TEXT("lone road: square"), PJ[TEXT("R3")].TanStart, 0.0, 1e-12); TestEqual(TEXT("lone road: square end"), PJ[TEXT("R3")].TanEnd, 0.0, 1e-12);
	return true;
}

// The carriageway is what the mesh draws (05:32: the verge is bare plate); the
// corridor - carriageway plus a verge either side - stays what placement measures.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStacktownRoadCarriagewayTest, "Stacktown.RoadTransform.Carriageway", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FStacktownRoadCarriagewayTest::RunTest(const FString& Parameters)
{
	const FPlacementBoard Board = FPlacementBoard::Default();
	const FEconRules& E = Board.Econ;
	TestEqual(TEXT("avenue carriageway 1400"), RoadCarriageway(E, TEXT("avenue")), 1400.0, 1e-9);
	TestEqual(TEXT("empty type = the avenue"), RoadCarriageway(E, FString()), 1400.0, 1e-9);
	TestEqual(TEXT("unknown type cannot refuse: the avenue's"), RoadCarriageway(E, TEXT("skyway")), 1400.0, 1e-9);
	TestEqual(TEXT("the default constant is the avenue's"), RoadFrame::Carriageway, RoadCarriageway(E, TEXT("avenue")), 1e-9);
	for (const auto& Pair : E.RoadTypes)
	{
		TestEqual(*FString::Printf(TEXT("%s: corridor = carriageway + 2 verges"), *Pair.Key),
			RoadCorridor(Board.Rules, E, Pair.Key), RoadCarriageway(E, Pair.Key) + 2.0 * Board.Rules.Verge, 1e-9);
	}
	return true;
}

#endif
