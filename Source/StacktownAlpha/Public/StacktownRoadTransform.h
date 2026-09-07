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
	// THE AVENUE'S corridor: 1400 carriageway + 2 x 430 footway. Since road
	// types (2026-09-06) each type has its own - Stacktown::RoadCorridor reads
	// it off the ruleset - and this stays as the default a caller that has no
	// ruleset to hand draws with, which is the avenue, which is today's road.
	static constexpr double Corridor = 2260.0;
	static constexpr double RoadZ = -3.0;   // LOOK ruling 2026-09-06: an inlay sits flush; the 8 uu slab's top at +1 uu is the seam (the plate is solid below z = 0)
	static constexpr double HeightScale = 0.08;     // 8 uu thick: a road is not a building
	static constexpr double CubeEdge = 100.0;       // /Engine/BasicShapes/Cube

	struct STACKTOWNALPHA_API FPose
	{
		FVector  Location = FVector::ZeroVector;
		FRotator Rotation = FRotator::ZeroRotator;
		FVector  Scale = FVector::OneVector;
		double   Length = 0.0;
	};

	/** `CorridorWidth` is what the mesh is scaled across: Stacktown::RoadCorridor
	 *  for the segment's own type. Defaulted to the avenue's so a caller with no
	 *  ruleset (the transform's own tests) still draws today's road. */
	STACKTOWNALPHA_API FPose Transform(const FRoadSegment& Segment, double CorridorWidth = Corridor);
}
}
