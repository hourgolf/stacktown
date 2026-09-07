#include "StacktownLotTransform.h"
#include "StacktownPlacement.h"   // RoadFrame / PointAt: the pose is off the road's own frame now

namespace Stacktown
{
namespace LotFrame
{
	bool Pose(const FLotPlacement& L, const TArray<FRoad>& Roads, FPose& Out, double InRoadHalf)
	{
		// The pad's centre line, off THIS road's frontage rather than the
		// avenue's constant: PadCentreY is that same sum for an avenue.
		const double PadCentre = InRoadHalf + BlockDepth * 0.5;
		const FString WantId = LotRoadId(L);
		const FRoad* Road = nullptr;
		const FRoad* Arterial = nullptr;
		for (const FRoad& R : Roads)
		{
			if (R.Id == WantId) { Road = &R; }
			if (R.Id == TEXT("arterial")) { Arterial = &R; }
		}
		if (!Road) { Road = Arterial; }
		if (!Road) { return false; }

		// ANY DIRECTION, 2026-09-06 (item 11). The anchor is the end of the
		// span the pad's own +x runs FROM - the span's start on the plus side,
		// its end on the minus side - offset to the pad's centre line, and the
		// yaw is the road's own direction (turned round on the minus side).
		//
		// REDUCES EXACTLY to the four axis-aligned cases this replaced, which
		// is what keeps every pose already in the world where it was:
		// horizontal plus -> (X0, Cy + PadCentre) yaw 0; minus -> (X1,
		// Cy - PadCentre) yaw 180; vertical plus -> (Cx - PadCentre, X0) yaw
		// 90; minus -> (Cx + PadCentre, X1) yaw -90. The yaw is normalized
		// into (-180, 180] so the minus-side vertical reads -90 rather than
		// the 270 that is the same rotation and a different number.
		const FRoadFrame F = RoadFrame(*Road);
		const bool bPlus = L.Side == Road->SidePlus;
		const double Sign = bPlus ? 1.0 : -1.0;
		const double SAnchor = bPlus ? L.X0 : L.X1;
		double Px = 0.0, Py = 0.0;
		PointAt(F, SAnchor, Sign * PadCentre, Px, Py);
		double Yaw = FMath::RadiansToDegrees(FMath::Atan2(F.Uy, F.Ux)) + (bPlus ? 0.0 : 180.0);
		while (Yaw > 180.0)  { Yaw -= 360.0; }
		while (Yaw <= -180.0) { Yaw += 360.0; }
		Out = { Px, Py, Yaw };
		return true;
	}

	FVector PadOffset(double Width)
	{
		return FVector(Width * 0.5, 0.0, 0.0);
	}

	FVector MassOffset()
	{
		return FVector(0.0, -(PadCentreY - RoadHalf), 0.0);
	}
}
}
