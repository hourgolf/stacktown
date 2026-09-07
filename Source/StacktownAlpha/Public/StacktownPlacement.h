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

	/** The segment's TYPE - dirt | avenue | boulevard | highway - carried
	 *  through from FRoadSegment::WidthClass, and EMPTY for the two built-ins,
	 *  which predate types entirely. RoadTypeOf() is the one place that empty
	 *  becomes 'avenue'; nothing else may read this field raw. */
	FString WidthClass;
};

/** One pinned lot's frontage span. Position was never citystate.json's to own -
 *  a pin's rid and width are its identity and live in state; where it STANDS has
 *  always been the layout's. */
struct STACKTOWNALPHA_API FPinnedSpan
{
	/** The citylayout key: NE0, SW3, and so on.
	 *
	 *  placement.PINNED_SPANS drops this, because answering "does this click
	 *  cross a pin" never needed it. Posing a pinned lot needs the other
	 *  direction - label to span - so the key is carried here. */
	FString Key;
	double  X0 = 0.0;
	double  X1 = 0.0;
	FString Side;

	/** The recipe this pin was declared with. Read by the preset start; the
	 *  click path never looks at it. */
	FString Rid;
	/** X1 - X0, carried rather than recomputed so the two cannot disagree. */
	double  Width = 0.0;

	/** NO DECLARED TIER, deliberately. A fresh parcel always seeds at tier 0
	 *  (PARCELIZATION_CONTRACT A2) - seeding from a pin's eventual massing was
	 *  the bug that made a bought lot show its full mature building instantly
	 *  instead of growing into it. The field is absent rather than present and
	 *  ignored, so it cannot be read by accident. */
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
	 *  same number as the click reach on purpose, so the two cannot drift.
	 *  THE AVENUE'S. RoadMaxReach() computes it per type; this stays as the
	 *  number the board was authored against and the fixture checks against. */
	double  RoadMaxReach    = 3230.0;
	/** Verge either side of the carriageway: pavement, kerb, and the
	 *  boulevard's trees. RECOVERED, not chosen - today's avenue is 1400 wide
	 *  inside a corridor whose half is RoadHalf, so the verge is 1130 - 700.
	 *  Generated from placement.VERGE rather than re-derived here, so the two
	 *  cannot disagree, and a LITERAL rather than road_width_avenue / 2: it
	 *  records how wide the road was when the board was authored, and must not
	 *  move when the owner retunes the avenue. */
	double  Verge           = 430.0;
	/** Forgiveness behind the block, in RoadMaxReach(). */
	double  ReachSlack      = 600.0;
};

/** Everything about the board this module does not compute for itself. */
struct STACKTOWNALPHA_API FPlacementBoard
{
	FPlacementRules      Rules;

	/** econrules.json, for the road-type table alone. placement.py imports
	 *  econrules for exactly this reason and no other; carrying it on the board
	 *  is how the same dependency crosses.
	 *
	 *  DEFAULTED, not required: FEconRules ships the same table it parses, so a
	 *  board built without a ruleset measures the city correctly rather than
	 *  measuring nothing. A caller holding the LIVE ruleset should still assign
	 *  it - Stacktown.Roads.TypeRulesMatchOracle is what keeps the compiled
	 *  default honest in the meantime. */
	FEconRules           Econ;
	/** The built-in roads: the arterial and the cross street. */
	TArray<FRoad>        Roads;
	TArray<FPinnedSpan>  PinnedSpans;

	/** Which road the pinned spans belong to. In the Python this is an identity
	 *  comparison (`road is ARTERIAL`) that works because PINNED_SPANS carries
	 *  no cross-street entries at all. Naming the road makes that implicit fact
	 *  explicit instead of hiding it in a pointer comparison. */
	FString PinnedRoadId = TEXT("arterial");

	/** The plate: MEASURED off the board's own ground mesh in the editor, never
	 *  derived. The procedural block union was tried as the authority and the
	 *  owner's live clicks proved it wrong twice. Nothing here can re-derive
	 *  them; if the mesh is resized they are re-measured and re-injected. */
	double PlateXMin = -7650.0, PlateXMax = 7650.0;
	double PlateYMin = -4230.0, PlateYMax = 4230.0;

	/** The real board the game stands on: the two built-in roads, the fourteen
	 *  pinned spans, the measured plate and the v0 rules - all generated from
	 *  citylayout into StacktownBoardData.inl and cross-checked at generation
	 *  time against placement.PINNED_SPANS, so the board the game uses is the
	 *  board the ported refusal logic was tested against. */
	static FPlacementBoard Default();

	/** Every road a click should consider: the two built-ins PLUS whatever the
	 *  player has drawn. A FRESH array every call, never cached - roads can be
	 *  drawn between calls and this struct holds no state of its own to go
	 *  stale. Drawn segments come after the built-ins, in id order. */
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
STACKTOWNALPHA_API bool InCrossing(const FPlacementRules& R, const FEconRules& E,
	const TArray<FRoad>& Roads,
	double X, double Y);

/** A placed lot's road, defaulting to "arterial" when the key is absent. */
STACKTOWNALPHA_API FString LotRoadId(const FLotPlacement& Lot);

/** The nearest road by point-to-SEGMENT distance, or nullptr.
 *
 *  Point-to-segment, not point-to-infinite-line: a click well past a short
 *  segment's end must not claim frontage on a road that does not reach that far.
 *  Refuses in the crossing before nearest-road selection runs, and refuses
 *  beyond RoadMaxReach. The returned pointer aliases into `Roads`. */
STACKTOWNALPHA_API const FRoad* ResolveRoad(const FPlacementRules& R, const FEconRules& E,
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
STACKTOWNALPHA_API FLotRect LotRect(const FPlacementRules& R, const FEconRules& E, const FRoad& Road,
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
// --- drawn roads (Phase 1 step 4) ------------------------------------------------

/** A stored segment as a road, with the side conventions READ OFF its geometry:
 *  a horizontal segment (same Y) gets the arterial's north/south convention, a
 *  vertical one (same X) gets the cross street's west/east. Not two conventions
 *  invented here - the same two the built-ins already use, extended to whichever
 *  a segment's own shape matches.
 *
 *  Trusts that the segment IS axis-aligned; DrawRoad is what enforces that
 *  before one ever reaches state. */
STACKTOWNALPHA_API FRoad RoadDictFromSegment(const FString& Id, const FRoadSegment& Seg);

// ---- ROAD TYPES AS MECHANICS (MONDAY_DECISIONS section 2) -----------------
// The type is the width class the segment already carried; no schema changed.
// Every number comes from FEconRules::RoadTypes, so the owner retunes the table
// without a recompile.

/** A road's type. An EMPTY width class means the avenue (the two built-ins, and
 *  any segment written before types existed); an UNRECOGNISED one is returned
 *  UNCHANGED so the caller can name it in a refusal rather than have it quietly
 *  become something else. */
STACKTOWNALPHA_API FString RoadTypeOf(const FRoad& Road);
STACKTOWNALPHA_API FString RoadTypeOf(const FRoadSegment& Seg);

/** This ruleset's row for a road, or nullptr when the ruleset has no such type.
 *  Callers REFUSE on nullptr; none of them substitutes the avenue. */
STACKTOWNALPHA_API const FRoadTypeRules* RoadRulesFor(const FEconRules& E, const FRoad& Road);

/** Centreline to facade line for THIS road: its own carriageway plus the verge
 *  either side. Reduces EXACTLY to Rules.RoadHalf for an avenue and for a road
 *  carrying no type, which is what keeps the authored board measuring the same.
 *  Falls back to Rules.RoadHalf when the ruleset has no row for the type - a
 *  measurement cannot refuse, so the callers that CAN refuse do it first. */
STACKTOWNALPHA_API double RoadHalf(const FPlacementRules& R, const FEconRules& E, const FRoad& Road);
STACKTOWNALPHA_API double RoadHalfForType(const FPlacementRules& R, const FEconRules& E,
	const FString& WidthClass);

/** The full corridor a road occupies on the board - twice its half. What the
 *  road MESH is scaled across, so a highway looks like a highway; RoadFrame's
 *  own constant is this number for an avenue. */
STACKTOWNALPHA_API double RoadCorridor(const FPlacementRules& R, const FEconRules& E,
	const FString& WidthClass);

/** RoadHalf + BlockDepth + ReachSlack, for THIS road. */
STACKTOWNALPHA_API double RoadMaxReach(const FPlacementRules& R, const FEconRules& E, const FRoad& Road);

/** False for a road no lot may face - the highway, and only the highway, today.
 *  A road whose type the ruleset does not know is treated as frontage-bearing
 *  so this question never silently deletes a road from the board; the draw path
 *  refuses the unknown type outright before one can be created. */
STACKTOWNALPHA_API bool RoadHasFrontage(const FEconRules& E, const FRoad& Road);

/** Centreline length. Axis-aligned today, written as a true distance so it is
 *  already right when segments stop being. */
STACKTOWNALPHA_API double RoadLength(const FRoadSegment& Seg);

/** What drawing this segment costs: its type's price per 100 uu times its own
 *  length. DERIVED every time, never stored on the segment - a stored cost is
 *  one more copy that can disagree with the geometry it prices. Returns false
 *  when the ruleset has no row for the type. */
STACKTOWNALPHA_API bool RoadCost(const FEconRules& E, const FRoadSegment& Seg, double& OutCost);

/** MI_road_dirt / _avenue / _boulevard / _highway. Formatted HERE so the road
 *  actor, the design lane and the oracle all read one string off one type. */
STACKTOWNALPHA_API FString RoadMaterialName(const FString& WidthClass);

/** Shortest distance between two rectangles, 0 when they touch or overlap. */
STACKTOWNALPHA_API double RectDistance(const FLotRect& A, const FLotRect& B);

/** What the roads around a lot do to its rent. Its OWN road's multiplier, times
 *  the multiplier of every frontage-refusing road within RoadHighwayReach of
 *  its pavement - two mechanisms, because MONDAY_DECISIONS section 2 describes
 *  two, and the second HAS to be proximity: nothing ever fronts a highway.
 *
 *  NOT APPLIED BY Tick(). This is the pure function rent is multiplied by; the
 *  one line that applies it is the economy loop's, deliberately left. */
STACKTOWNALPHA_API double RoadRentMultiplier(const FPlacementBoard& Board,
	const FCityState& State, const FLotPlacement& Lot);

/** Drawn-road ids in creation order: R1, R2, ... R9, R10 - numerically, not
 *  lexicographically, which would put R10 before R2. The Python gets this free
 *  from dict insertion order; a C++ port that reloads from JSON cannot, and the
 *  order decides WHICH road a crossing refusal names. */
STACKTOWNALPHA_API void SortRoadIds(TArray<FString>& Ids);

/** World footprint of a road's OWN corridor: RoadHalf either side of its
 *  centreline, for its full length. Deliberately the same rectangle shape a lot
 *  gets, so one overlap test compares a candidate road against a road OR a lot
 *  with nothing road-specific in the comparison itself. */
STACKTOWNALPHA_API FLotRect RoadRect(const FPlacementRules& R, const FEconRules& E, const FRoad& Road);

/** R1, R2, ... - the first not taken. A namespace distinct by construction from
 *  the built-ins, from placed lots (P + digits) and from pins (letters). */
STACKTOWNALPHA_API FString NextRoadId(const FCityState& State);

struct STACKTOWNALPHA_API FRoadDrawResult
{
	bool         bOk = false;
	FString      Reason;
	FString      Id;
	FRoadSegment Segment;
};

/** The click-click -> road decision: the ONE place a drawn road is accepted or
 *  refused, so the ghost preview and the commit can never disagree.
 *
 *  AXIS-ALIGNED ONLY, and that is a named limit rather than an oversight:
 *  ResolveClick recovers a world point as `road start on axis + along`, which is
 *  only correct when a road's direction IS a world axis. A true diagonal would
 *  need `along` recovered as a full 2D point along the road's own direction
 *  vector, which nothing does today - so this refuses input that would need it
 *  rather than quietly reinterpreting a diagonal gesture as a straight one.
 *  Orientation goes to whichever delta dominates by 3x; neither dominant
 *  refuses.
 *
 *  PINNED LOTS ARE CHECKED SEPARATELY, and that is not redundant with the lot
 *  scan: a pin is registered with no placement at all, so the placed-lot loop
 *  skips every pin by construction. Without this check a drawn road could run
 *  straight through a standing pinned building. */
STACKTOWNALPHA_API FRoadDrawResult ResolveRoadDraw(const FPlacementBoard& Board,
	const FCityState& State, double X0, double Y0, double X1, double Y1,
	const FString& WidthClass, bool bPinsActive);

/** One road-drawing attempt. On success the segment ResolveRoadDraw validated is
 *  inserted UNCHANGED - not re-derived, the same discipline Place holds for a lot. */
STACKTOWNALPHA_API FRoadDrawResult DrawRoad(const FPlacementBoard& Board, FCityState& State,
	double X0, double Y0, double X1, double Y1, const FString& WidthClass, bool bPinsActive);

/** The placement a PINNED lot would have if it carried one.
 *
 *  A pin has no 'placement' key in state at all - only a player-placed lot gets
 *  one - which is why the city sync skips every pin when it looks for a pose.
 *  Its span and its side on the arterial are all a pose needs, so this
 *  synthesizes the same shape LotFrame::Pose already takes rather than teaching
 *  the pose path a second way to describe where a lot is.
 *
 *  @return false when no pinned span carries that key. */
/** A fresh city with the fourteen pinned lots standing on it as FOR-SALE
 *  parcels at their pinned poses - the preset start (queue item 12,
 *  MONDAY_DECISIONS section 3: a new game offers an empty board OR this).
 *
 *  They are ORDINARY LOTS, not a special kind: each gets a placement, so it
 *  poses, renders and reconciles through exactly the path a player-placed lot
 *  does, and the city sync needs no case for them. Every one seeds unowned at
 *  tier 0 - the board is a city to buy into, not one already owned.
 *
 *  NOTE FOR THE WIRING: with the preset seeded, those spans are occupied by real
 *  parcels, so ResolveClick's overlap scan already refuses clicks on them. The
 *  separate pinned-span check would then refuse them a second time under a
 *  different message; whether the preset start should pass bPinsActive=false is
 *  the caller's call, and is why this function does not decide it. */
STACKTOWNALPHA_API FCityState SeedPresetState(const FEconRules& R, const FPlacementBoard& Board);

STACKTOWNALPHA_API bool PinnedPlacementForKey(const FPlacementBoard& Board,
	const FString& Key, FLotPlacement& OutPlacement);

STACKTOWNALPHA_API void PlanReactivation(const TArray<FString>& Pids,
	const TArray<FString>& PoolLabels,
	TArray<TPair<FString, FString>>& OutPairs, TArray<FString>& OutUnmatched);

} // namespace Stacktown
