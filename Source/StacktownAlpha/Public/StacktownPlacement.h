// The click -> lot -> state contract, ported from Content/Python/placement.py
// (Phase 1 step 2, Docs/PLAN_CPP_PORT.md). That module is the SPECIFICATION and
// the test oracle; this is a translation of it.
//
// SCOPE IS STEP 2's, NOT STEP 4's. placement.py's self-tests run 1-39: cases
// 1-27 are the click contract and are ported here; 28-39 are DRAWN ROADS
// (_road_dict, resolve_road_draw, draw_road), which PLAN_CPP_PORT.md assigns to
// step 4. The charter's "placement: 27 tests" is therefore exact, not stale.
// Reading roads in order to place a lot is step 2's; authoring them is step 4's.
//
// WHY THE BOARD IS INJECTED. PINNED_SPANS is derived at import from
// citylayout, which pulls in city and parcelmeta - a layout port that belongs
// to step 3, not here. The economy port took the same shape for the recipe
// catalogue: this module asks the board for ANSWERS (the pinned spans, the
// roads, the constants) rather than carrying a second copy of the module that
// computes them.
//
// THE PLATE BOUNDS ARE MEASURED, NOT DERIVED, and that carries across as a
// warning rather than as code: PLATE_X_MIN/MAX come from get_actor_bounds on
// the board's own ground mesh in the editor. citylayout's procedural union was
// tried as the authority and was PROVEN wrong twice by the owner's live clicks.
// Nothing here can re-derive them; if the board mesh is resized they must be
// re-measured and re-injected by hand. That is a real accepted gap, named in
// placement.py's own comments and repeated here so it survives the port.
#pragma once

#include "CoreMinimal.h"
#include "StacktownEconomyRules.h"

namespace Stacktown
{

/** An axis-aligned road: a centreline segment plus which side is which. */
struct STACKTOWNALPHA_API FRoad
{
	FString Id;
	double  StartX = 0.0, StartY = 0.0;
	double  EndX   = 0.0, EndY   = 0.0;
	/** The side at positive perpendicular offset, and at negative. */
	FString SidePlus, SideMinus;
	/** True for a horizontal road (the arterial's convention), false vertical. */
	bool    bAxisX = true;
};

/** One pinned lot's frontage span. Position was never citystate.json's to own. */
struct STACKTOWNALPHA_API FPinnedSpan
{
	double  X0 = 0.0;
	double  X1 = 0.0;
	FString Side;
};

/** placement.py's module constants, as data. Same reasoning as FEconRules: a
 *  constant compiled into the binary needs a rebuild to tune, and several of
 *  these are expected to move (POOL_SIZE is explicitly marked stale in the
 *  Python, held back only because raising it means editing saved map content). */
struct STACKTOWNALPHA_API FPlacementRules
{
	/** Position is FREE along the road since the owner's "let it slide freely"
	 *  - 10 uu, not the 410 width quantum, which still governs widths only. */
	double  PositionQuantum = 10.0;
	double  V0Width         = 820.0;
	FString V0Recipe        = TEXT("vernacular");
	/** Dormant BP_Parcel actors pre-placed as map content. No Python API in this
	 *  UE build spawns an actor into the running world, so a placed lot can only
	 *  ACTIVATE one of a fixed pool. Marked stale in the Python: the plate now
	 *  physically fits 36, and raising the cap means spawning and saving more
	 *  actors - a map edit, not a constant change. */
	int32   PoolSize        = 30;
	double  RoadHalf        = 1130.0;
	double  BlockDepth      = 1500.0;
	/** The outer claim distance: RoadHalf + BlockDepth + 600 forgiveness. The
	 *  same number as the click reach on purpose, so the two cannot drift. */
	double  RoadMaxReach    = 3230.0;
};

/** Everything about the board this module does not compute for itself. */
struct STACKTOWNALPHA_API FPlacementBoard
{
	FPlacementRules      Rules;
	/** The built-in roads: the arterial and the cross street. */
	TArray<FRoad>        Roads;
	TArray<FPinnedSpan>  PinnedSpans;

	/** Which road the pinned spans belong to. In the Python this is an identity
	 *  comparison (`road is ARTERIAL`) that works because PINNED_SPANS carries
	 *  no cross-street entries at all. Naming the road makes that implicit fact
	 *  explicit instead of hiding it in a pointer comparison. */
	FString PinnedRoadId = TEXT("arterial");

	/** Every road a click should consider. Today: the built-ins. Player-drawn
	 *  segments join this list in STEP 4, when FCityState::RoadsJson stops being
	 *  opaque - the function exists now so step 4 changes one body rather than
	 *  every call site, exactly as the Python's own _all_roads did. */
	TArray<FRoad> AllRoads(const FCityState& State) const;
};

/** (along, across, length) in a road's own frame. `across` is SIGNED: positive
 *  is the SidePlus side. */
struct STACKTOWNALPHA_API FRoadProjection
{
	double Along  = 0.0;
	double Across = 0.0;
	double Length = 0.0;
};

/** The winning road's frame, with `side` already relabelled to that road's own
 *  names - a caller should never need to know which sign convention it picked. */
struct STACKTOWNALPHA_API FRoadLocal
{
	double  Along  = 0.0;
	double  Across = 0.0;
	FString Side;
};

struct STACKTOWNALPHA_API FLotRect
{
	double XMin = 0.0, XMax = 0.0, YMin = 0.0, YMax = 0.0;

	bool operator==(const FLotRect& O) const
	{
		return XMin == O.XMin && XMax == O.XMax && YMin == O.YMin && YMax == O.YMax;
	}
};

struct STACKTOWNALPHA_API FClickResult
{
	bool          bOk = false;
	FString       Reason;
	/** Only meaningful when bOk. */
	FLotPlacement Lot;
};

struct STACKTOWNALPHA_API FPlaceResult
{
	bool    bOk = false;
	FString Reason;
	/** Empty on refusal. */
	FString Pid;
};

/** Nearest PositionQuantum. */
STACKTOWNALPHA_API double Snap(const FPlacementRules& R, double Value);

/** Pure vector projection, no trig. The normal is the direction rotated +90
 *  degrees, so along the arterial (direction +X) the normal is +Y and across>=0
 *  means y>=0 - which is the same north/south rule the click path used before
 *  roads generalized, recovered from the geometry rather than restated. */
STACKTOWNALPHA_API FRoadProjection ProjectToRoad(const FRoad& Road, double X, double Y);

/** True when the point stands on pavement MORE THAN ONE road shares, so no
 *  single road's claim is honest. Not the corner-lot question, which is still
 *  open - the narrower, unambiguous case. Factored out so ResolveRoad and
 *  ResolveClick (which wants its own distinctly-worded refusal) cannot disagree
 *  about the rule. */
STACKTOWNALPHA_API bool InCrossing(const FPlacementRules& R, const TArray<FRoad>& Roads,
	double X, double Y);

/** A placed lot's road, defaulting to "arterial" when the key is absent. */
STACKTOWNALPHA_API FString LotRoadId(const FLotPlacement& Lot);

/** The nearest road by point-to-SEGMENT distance, or nullptr.
 *
 *  Point-to-segment, not point-to-infinite-line: a click well past a short
 *  segment's end must not claim frontage on a road that does not reach that far.
 *  Refuses in the crossing before nearest-road selection runs, and refuses
 *  beyond RoadMaxReach. The returned pointer aliases into `Roads`. */
STACKTOWNALPHA_API const FRoad* ResolveRoad(const FPlacementRules& R,
	const TArray<FRoad>& Roads, double X, double Y, FRoadLocal& OutLocal);

/** The road named Id, or nullptr. The Python raises KeyError here; callers
 *  below turn a miss into a named refusal instead, because crashing the game on
 *  a save that names a road it no longer has is a worse answer than saying so.
 *  Unreachable from the ported tests either way - no case in 1-27 has a lot
 *  whose road is absent - so this is a divergence in the failure mode only. */
STACKTOWNALPHA_API const FRoad* FindRoad(const TArray<FRoad>& Roads, const FString& Id);

/** World footprint of a lot's pad: its span along the road's axis, and facade
 *  line to block back edge across it, on the lot's side. Reduces exactly to the
 *  old hard-coded constants for both built-ins, whose centrelines are 0. */
STACKTOWNALPHA_API FLotRect LotRect(const FPlacementRules& R, const FRoad& Road,
	const FLotPlacement& Lot);

STACKTOWNALPHA_API bool RectsOverlap(const FLotRect& A, const FLotRect& B);

/** The click -> lot decision. Road and side selection and the outer reach bound
 *  are ResolveRoad's; this adds what it deliberately leaves open: the
 *  in-the-road refusal read off the WINNING road's corridor, the conversion back
 *  to world space BEFORE snapping (snapping the road-relative offset would shift
 *  the grid off-quantum, since neither plate minimum is a multiple of the
 *  quantum), the pinned-span check, and the placed-lot overlap check.
 *
 *  Overlap is compared as WORLD RECTANGLES, not per-road spans. That is the
 *  corner fix: a cross-street lot and an arterial lot share ground at a corner
 *  while their spans live on different axes, so a span scan never compared them
 *  and the owner placed a lot onto a standing building. */
STACKTOWNALPHA_API FClickResult ResolveClick(const FPlacementBoard& Board,
	const FCityState& State, double X, double Y, bool bPinsActive, double Width);

/** One placement attempt. On success the new parcel has EXACTLY the shape
 *  EnsureParcel produces for a pinned parcel, plus one key a pinned parcel never
 *  carries. Additive by construction, not a schema migration. */
STACKTOWNALPHA_API FPlaceResult Place(const FPlacementBoard& Board, FCityState& State,
	double X, double Y, bool bPinsActive, double Width);

/** Pairs pids with dormant pool labels for session-start reactivation, both
 *  sorted, lowest pid to lowest label. Placed lots must survive a PIE restart
 *  the way purchases already do; without this a placed lot's saved entry
 *  outlives the restart while the pool boots dormant, and the ghost keeps
 *  refusing real clicks with nothing visible to explain why.
 *
 *  Generic over WHICH pids: it takes bare strings and never sees a placement, so
 *  it is oblivious to road_id by construction rather than merely untested
 *  against it. OutUnmatched is any pid with no label left - a state/pool desync
 *  that must refuse loudly rather than silently drop a lot. */
STACKTOWNALPHA_API void PlanReactivation(const TArray<FString>& Pids,
	const TArray<FString>& PoolLabels,
	TArray<TPair<FString, FString>>& OutPairs, TArray<FString>& OutUnmatched);

} // namespace Stacktown
