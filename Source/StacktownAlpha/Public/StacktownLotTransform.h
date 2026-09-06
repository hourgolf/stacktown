#pragma once

// World placement for a lot, ported from init_unreal.py (_lot_transform,
// _apply_lot_offset). The actor sits on the pad's centre line, local +x runs
// ALONG the road from the lot's near corner, local +y points AWAY from the
// road; the pad cube and the catalogue mass have different pivots, so each
// carries its own LOCAL offset and the south side's yaw 180 resolves both.

#include "CoreMinimal.h"
#include "StacktownEconomyRules.h"
#include "StacktownPlacement.h"

namespace Stacktown
{
namespace LotFrame
{
	/** citylayout.HALF (centreline to facade) and BLOCK_DEPTH (facade to back). */
	static constexpr double RoadHalf = 1130.0;
	static constexpr double BlockDepth = 1500.0;
	/** The pad's centre line: HALF + BLOCK_DEPTH / 2. */
	static constexpr double PadCentreY = RoadHalf + BlockDepth * 0.5;

	struct STACKTOWNALPHA_API FPose
	{
		double X = 0.0;
		double Y = 0.0;
		double Yaw = 0.0;
	};

	/** _lot_transform: the pose for a lot given every road (built-ins + drawn).
	 *  Falls back to the arterial when the lot's road is unknown, as the Python
	 *  does; false only when there is no arterial either. */
	STACKTOWNALPHA_API bool Pose(const FLotPlacement& LotPlacement, const TArray<FRoad>& Roads, FPose& Out);

	/** The placeholder cube is centre-pivot: half a width along +x covers the span. */
	STACKTOWNALPHA_API FVector PadOffset(double Width);

	/** A catalogue mass has genbuild's front-left ground pivot: half the block
	 *  depth toward the road puts its front face on the facade line. */
	STACKTOWNALPHA_API FVector MassOffset();
}
}
