#include "StacktownLotTransform.h"

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
		if (!Road->bAxisX)
		{
			const double Cx = Road->StartX;
			if (L.Side == Road->SidePlus) { Out = { Cx - PadCentre, L.X0, 90.0 }; }
			else                          { Out = { Cx + PadCentre, L.X1, -90.0 }; }
			return true;
		}
		const double Cy = Road->StartY;
		if (L.Side == Road->SidePlus) { Out = { L.X0, Cy + PadCentre, 0.0 }; }
		else                          { Out = { L.X1, Cy - PadCentre, 180.0 }; }
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
