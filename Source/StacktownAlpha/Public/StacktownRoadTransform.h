#pragma once

// A drawn road's world transform, ported from init_unreal._road_transform
// (Docs/ROAD_BUILD_CONTRACT.md section 5): one yaw per segment - the centre of
// the chord, the yaw from start to end, and a stock cube scaled to
// length / 100 along, CORRIDOR / 100 across, thin in z.

#include "CoreMinimal.h"
#include "StacktownEconomyRules.h"

namespace Stacktown
{
namespace RoadFrame
{
	static constexpr double Corridor = 2260.0;      // citylayout: 1400 carriageway + 2 * 430 footway
	static constexpr double RoadZ = 4.0;
	static constexpr double HeightScale = 0.08;     // 8 uu thick: a road is not a building
	static constexpr double CubeEdge = 100.0;       // /Engine/BasicShapes/Cube

	struct STACKTOWNALPHA_API FPose
	{
		FVector  Location = FVector::ZeroVector;
		FRotator Rotation = FRotator::ZeroRotator;
		FVector  Scale = FVector::OneVector;
		double   Length = 0.0;
	};

	STACKTOWNALPHA_API FPose Transform(const FRoadSegment& Segment);
}
}
