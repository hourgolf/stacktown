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
	// THE AVENUE'S carriageway. Since the design lane's ruling of 2026-09-07 05:32
	// the road MESH is drawn this wide - the verge either side is bare plate, not
	// road - while the corridor above stays what placement measures against.
	static constexpr double Carriageway = 1400.0;
	// tan(half-turn) never exceeds this at a joint: a 90 degree turn mitres
	// exactly, anything sharper is cut as if it were 90, so a hairpin in a
	// refused ghost cannot grow a spike the length of the road's width.
	static constexpr double MitreLimit = 1.0;
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

	// ---- THE MITRE (design lane 2026-09-07 05:32: "mitre it, at the carriageway") ----
	// A curved road is a chain of chords. Drawn as plain slabs they fan open on
	// the outside of every bend; overlapped they fatten. A mitre cuts each
	// chord's end along the bisector of the turn into its neighbour, so the two
	// chords share one edge exactly: no gap, no overlap, a fitted polyline.

	/** Unit direction start -> end, or zero for a degenerate chord. */
	STACKTOWNALPHA_API FVector2D Direction(const FRoadSegment& Segment);

	/** tan(turn / 2) for the turn from `DirIn` to `DirOut` (signed: toward the
	 *  chord's +y side positive), clamped to +-MitreLimit; 0 when either
	 *  direction is degenerate. Both chords at a joint use this ONE number. */
	STACKTOWNALPHA_API double JointTangent(const FVector2D& DirIn, const FVector2D& DirOut);

	/** The four plate-plane corners of a chord drawn `Width` across with its
	 *  ends cut by `TanStart` / `TanEnd` (0 = square, a free end):
	 *  Out[0] start +y, Out[1] start -y, Out[2] end -y, Out[3] end +y.
	 *  Two consecutive chords that pass the same JointTangent for their shared
	 *  joint get the same two corners there - that is the whole mitre. */
	STACKTOWNALPHA_API void Corners(const FRoadSegment& Segment, double Width,
		double TanStart, double TanEnd, FVector2D Out[4]);

	struct STACKTOWNALPHA_API FJoint
	{
		double TanStart = 0.0;
		double TanEnd   = 0.0;
		/** Arc length from the path's start to this chord's start, and the whole
		 *  path's length: the stain's U runs 0..1 over the PATH, as it ran over
		 *  the stock cube of a straight road, so a curve's grain is continuous
		 *  across its joints instead of restarting on every chord (frame 06:20). */
		double S0         = 0.0;
		double PathLength = 0.0;
	};

	/** Joints for chords in drawing order (a resolved path, a ghost chain). A
	 *  chord whose start is not where the previous one ended (1 uu) keeps a
	 *  square end there - the chain is a hint, never a claim. */
	STACKTOWNALPHA_API TArray<FJoint> ChainJoints(const TArray<FRoadSegment>& Chords);

	/** Joints for every road in a city, keyed by segment id: chords are grouped
	 *  by path (FRoadSegment::Path, or the id itself - RoadPathId's rule) and
	 *  ordered by the number in their id, which is the order DrawRoadPath
	 *  allocated them. A single-chord road gets two square ends. */
	STACKTOWNALPHA_API TMap<FString, FJoint> PathJoints(const TMap<FString, FRoadSegment>& Roads);
}
}
