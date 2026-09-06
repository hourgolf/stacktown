#include "StacktownRoadTransform.h"

namespace Stacktown
{
namespace RoadFrame
{
	FPose Transform(const FRoadSegment& S)
	{
		FPose P;
		const double Dx = S.EndX - S.StartX, Dy = S.EndY - S.StartY;
		P.Length = FMath::Sqrt(Dx * Dx + Dy * Dy);
		P.Location = FVector((S.StartX + S.EndX) * 0.5, (S.StartY + S.EndY) * 0.5, RoadZ);
		P.Rotation = FRotator(0.0, FMath::RadiansToDegrees(FMath::Atan2(Dy, Dx)), 0.0);
		P.Scale = FVector(FMath::Max(P.Length, 1.0) / CubeEdge, Corridor / CubeEdge, HeightScale);
		return P;
	}
}
}
