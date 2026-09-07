// Ported from Content/Python/placement.py, self-tests 1-27. See
// StacktownPlacement.h for the scope boundary against step 4 and for why the
// board is injected rather than derived.

#include "StacktownPlacement.h"
#include "StacktownBoardData.inl"

namespace Stacktown
{

FPlacementBoard FPlacementBoard::Default()
{
	FPlacementBoard Board;
	Board.Rules.PositionQuantum = BoardData::PositionQuantum;
	Board.Rules.V0Width         = BoardData::V0Width;
	Board.Rules.V0Recipe        = FString(BoardData::V0Recipe);
	Board.Rules.PoolSize        = BoardData::PoolSize;
	Board.Rules.RoadHalf        = BoardData::RoadHalf;
	Board.Rules.BlockDepth      = BoardData::BlockDepth;
	Board.Rules.RoadMaxReach    = BoardData::RoadMaxReach;
	Board.Rules.Verge           = BoardData::Verge;
	Board.Rules.ReachSlack      = BoardData::ReachSlack;

	// MEASURED off the board's own ground mesh, never derived - citylayout's
	// procedural union was tried as the authority and the owner's live clicks
	// proved it wrong twice.
	Board.PlateXMin = BoardData::PlateXMin;
	Board.PlateXMax = BoardData::PlateXMax;
	Board.PlateYMin = BoardData::PlateYMin;
	Board.PlateYMax = BoardData::PlateYMax;

	for (int32 i = 0; i < BoardData::RoadsNum; ++i)
	{
		const BoardData::FRoadRow& Row = BoardData::Roads[i];
		FRoad R;
		R.Id = Row.Id;
		R.StartX = Row.StartX; R.StartY = Row.StartY;
		R.EndX = Row.EndX;     R.EndY = Row.EndY;
		R.SidePlus = Row.SidePlus;
		R.SideMinus = Row.SideMinus;
		R.bAxisX = Row.bAxisX;
		Board.Roads.Add(R);
	}
	for (int32 i = 0; i < BoardData::PinnedSpansNum; ++i)
	{
		const BoardData::FPinRow& Row = BoardData::PinnedSpans[i];
		FPinnedSpan S;
		S.Key = Row.Key;
		S.X0 = Row.X0;
		S.X1 = Row.X1;
		S.Side = Row.Side;
		S.Rid = Row.Rid;
		S.Width = Row.Width;
		Board.PinnedSpans.Add(S);
	}
	return Board;
}

FCityState SeedPresetState(const FEconRules& R, const FPlacementBoard& Board)
{
	FCityState S = SeedState(R);
	for (const FPinnedSpan& Span : Board.PinnedSpans)
	{
		FParcelState P;
		P.Rid = Span.Rid;
		P.Tier = 0;          // ALWAYS. See FPinnedSpan for why no tier is carried.
		P.Width = Span.Width;
		P.bOwned = false;    // a city to buy into, not one already owned
		P.Accum = 0.0;
		P.bFailed = false;
		P.Performance = 0.0;

		// An ordinary placement, so these lots pose, render and reconcile
		// through exactly the path a player-placed lot does.
		FLotPlacement Lot;
		if (!PinnedPlacementForKey(Board, Span.Key, Lot))
		{
			// Unreachable: the span came out of this same board. Skipping
			// rather than asserting keeps a malformed board from taking the
			// game down on a fresh start.
			continue;
		}
		P.Placement = Lot;
		S.Parcels.Add(Span.Key, P);
	}
	return S;
}

bool PinnedPlacementForKey(const FPlacementBoard& Board, const FString& Key,
	FLotPlacement& OutPlacement)
{
	for (const FPinnedSpan& Span : Board.PinnedSpans)
	{
		if (Span.Key == Key)
		{
			OutPlacement.X0 = Span.X0;
			OutPlacement.X1 = Span.X1;
			OutPlacement.Side = Span.Side;
			// Every pinned span is on the arterial - PINNED_SPANS has no
			// cross-street entries at all, which is why the click path's own
			// pinned check is gated on the arterial too.
			OutPlacement.RoadId = Board.PinnedRoadId;
			return true;
		}
	}
	return false;
}

void SortRoadIds(TArray<FString>& Ids)
{
	// R1 < R2 < ... < R9 < R10. A plain string sort puts R10 before R2, which
	// would silently change which road a crossing refusal names once ten have
	// been drawn - the kind of thing that reads as a mystery months later.
	Ids.Sort([](const FString& A, const FString& B)
	{
		const bool bNumA = A.StartsWith(TEXT("R"), ESearchCase::CaseSensitive) && A.Len() > 1 && FChar::IsDigit(A[1]);
		const bool bNumB = B.StartsWith(TEXT("R"), ESearchCase::CaseSensitive) && B.Len() > 1 && FChar::IsDigit(B[1]);
		if (bNumA && bNumB)
		{
			const int32 NA = FCString::Atoi(*A.Mid(1));
			const int32 NB = FCString::Atoi(*B.Mid(1));
			if (NA != NB)
			{
				return NA < NB;
			}
		}
		return A < B;
	});
}

FRoad RoadDictFromSegment(const FString& Id, const FRoadSegment& Seg)
{
	FRoad Road;
	Road.Id = Id;
	Road.StartX = Seg.StartX;
	Road.StartY = Seg.StartY;
	Road.EndX = Seg.EndX;
	Road.EndY = Seg.EndY;
	// The TYPE travels with the geometry. Orientation is read off start/end
	// rather than stored; the width class is the one thing a segment genuinely
	// carries that its shape cannot say.
	Road.WidthClass = Seg.WidthClass;
	if (Seg.StartY == Seg.EndY)
	{
		// Horizontal: the arterial's own convention.
		Road.bAxisX = true;
		Road.SidePlus = TEXT("north");
		Road.SideMinus = TEXT("south");
	}
	else
	{
		// Vertical: the cross street's.
		Road.bAxisX = false;
		Road.SidePlus = TEXT("west");
		Road.SideMinus = TEXT("east");
	}
	return Road;
}

TArray<FRoad> FPlacementBoard::AllRoads(const FCityState& State) const
{
	// The built-ins first, then the drawn segments in creation order. A FRESH
	// array every call: roads can be drawn between calls and this struct holds
	// no state of its own to go stale.
	TArray<FRoad> Out = Roads;
	TArray<FString> Ids;
	State.Roads.GetKeys(Ids);
	SortRoadIds(Ids);
	for (const FString& Id : Ids)
	{
		Out.Add(RoadDictFromSegment(Id, State.Roads[Id]));
	}
	return Out;
}

// ---- ROAD TYPES AS MECHANICS ---------------------------------------------

FString RoadTypeOf(const FRoad& Road)
{
	return Road.WidthClass.IsEmpty() ? FString(DefaultRoadType()) : Road.WidthClass;
}

FString RoadTypeOf(const FRoadSegment& Seg)
{
	return Seg.WidthClass.IsEmpty() ? FString(DefaultRoadType()) : Seg.WidthClass;
}

const FRoadTypeRules* RoadRulesFor(const FEconRules& E, const FRoad& Road)
{
	return E.FindRoadType(RoadTypeOf(Road));
}

double RoadHalfForType(const FPlacementRules& R, const FEconRules& E, const FString& WidthClass)
{
	const FRoadTypeRules* T = E.FindRoadType(
		WidthClass.IsEmpty() ? FString(DefaultRoadType()) : WidthClass);
	if (T == nullptr)
	{
		// A MEASUREMENT CANNOT REFUSE. Returning the authored half is the only
		// answer that keeps the board measurable at all; every path that can
		// refuse an unknown type does so before a road with one exists.
		return R.RoadHalf;
	}
	return T->Width / 2.0 + R.Verge;
}

double RoadHalf(const FPlacementRules& R, const FEconRules& E, const FRoad& Road)
{
	return RoadHalfForType(R, E, Road.WidthClass);
}

double RoadCorridor(const FPlacementRules& R, const FEconRules& E, const FString& WidthClass)
{
	return 2.0 * RoadHalfForType(R, E, WidthClass);
}

double RoadMaxReach(const FPlacementRules& R, const FEconRules& E, const FRoad& Road)
{
	return RoadHalf(R, E, Road) + R.BlockDepth + R.ReachSlack;
}

bool RoadHasFrontage(const FEconRules& E, const FRoad& Road)
{
	const FRoadTypeRules* T = RoadRulesFor(E, Road);
	// An unknown type keeps its frontage rather than losing it: this question
	// must never quietly remove a road from the board. The draw path refuses an
	// unknown type outright, so one cannot reach state to be asked about.
	return T == nullptr ? true : T->bFrontage;
}

double RoadLength(const FRoadSegment& Seg)
{
	const double Dx = Seg.EndX - Seg.StartX;
	const double Dy = Seg.EndY - Seg.StartY;
	return FMath::Sqrt(Dx * Dx + Dy * Dy);
}

bool RoadCost(const FEconRules& E, const FRoadSegment& Seg, double& OutCost)
{
	const FRoadTypeRules* T = E.FindRoadType(RoadTypeOf(Seg));
	if (T == nullptr)
	{
		return false;
	}
	OutCost = T->CostPer100uu * RoadLength(Seg) / 100.0;
	return true;
}

FString RoadMaterialName(const FString& WidthClass)
{
	const FString Type = WidthClass.IsEmpty() ? FString(DefaultRoadType()) : WidthClass.ToLower();
	return FString::Printf(TEXT("MI_road_%s"), *Type);
}

double RectDistance(const FLotRect& A, const FLotRect& B)
{
	// Gap on each axis, negative where the spans already intersect, clamped to
	// zero; then the hypotenuse, so a diagonal neighbour is measured corner to
	// corner rather than along whichever axis happens to be larger.
	const double Dx = FMath::Max(0.0, FMath::Max(A.XMin - B.XMax, B.XMin - A.XMax));
	const double Dy = FMath::Max(0.0, FMath::Max(A.YMin - B.YMax, B.YMin - A.YMax));
	return FMath::Sqrt(Dx * Dx + Dy * Dy);
}

FLotRect RoadRect(const FPlacementRules& R, const FEconRules& E, const FRoad& Road)
{
	const double Half = RoadHalf(R, E, Road);
	FLotRect Rect;
	if (Road.StartY == Road.EndY)
	{
		Rect.XMin = FMath::Min(Road.StartX, Road.EndX);
		Rect.XMax = FMath::Max(Road.StartX, Road.EndX);
		Rect.YMin = Road.StartY - Half;
		Rect.YMax = Road.StartY + Half;
		return Rect;
	}
	Rect.XMin = Road.StartX - Half;
	Rect.XMax = Road.StartX + Half;
	Rect.YMin = FMath::Min(Road.StartY, Road.EndY);
	Rect.YMax = FMath::Max(Road.StartY, Road.EndY);
	return Rect;
}

FString NextRoadId(const FCityState& State)
{
	int32 N = 1;
	while (State.Roads.Contains(FString::Printf(TEXT("R%d"), N)))
	{
		++N;
	}
	return FString::Printf(TEXT("R%d"), N);
}

double Snap(const FPlacementRules& R, double Value)
{
	// Python's round() is half-to-even, and the snap grid is what fixes lot
	// spans in JSON, so the tie-breaking rule is part of the contract.
	return FMath::RoundHalfToEven(Value / R.PositionQuantum) * R.PositionQuantum;
}

FRoadProjection ProjectToRoad(const FRoad& Road, double X, double Y)
{
	const double Dx = Road.EndX - Road.StartX;
	const double Dy = Road.EndY - Road.StartY;
	const double Length = FMath::Sqrt(Dx * Dx + Dy * Dy);
	const double Ux = Dx / Length;
	const double Uy = Dy / Length;
	// Normal is direction rotated +90 degrees.
	const double Nx = -Uy;
	const double Ny = Ux;
	const double Tx = X - Road.StartX;
	const double Ty = Y - Road.StartY;

	FRoadProjection P;
	P.Along  = Tx * Ux + Ty * Uy;
	P.Across = Tx * Nx + Ty * Ny;
	P.Length = Length;
	return P;
}

bool InCrossing(const FPlacementRules& R, const FEconRules& E,
	const TArray<FRoad>& Roads, double X, double Y)
{
	int32 Count = 0;
	for (const FRoad& Road : Roads)
	{
		const FRoadProjection P = ProjectToRoad(Road, X, Y);
		// The ROAD'S OWN corridor, not the one avenue constant: a highway is
		// 2000 wide and its pavement has to be 2000 wide here too.
		if (P.Along >= 0.0 && P.Along <= P.Length && FMath::Abs(P.Across) < RoadHalf(R, E, Road))
		{
			++Count;
		}
	}
	return Count > 1;
}

FString LotRoadId(const FLotPlacement& Lot)
{
	// v0 wrote no road_id at all, so the owner's real save has entries without
	// the key. ONE place this fallback lives.
	return Lot.RoadId.IsSet() ? Lot.RoadId.GetValue() : FString(TEXT("arterial"));
}

/** Point-to-SEGMENT distance, with the projection that produced it. Past an
 *  end, measured to the end itself: an infinite-line distance would read 0 for
 *  a click far past the arterial's east end but sitting on y=0, and accept.
 *  Factored out so the frontage search and the no-frontage explanation measure
 *  with one function rather than each carrying its own copy of the clamp. */
static double RoadDistance(const FRoad& Road, double X, double Y, FRoadProjection& OutProj)
{
	OutProj = ProjectToRoad(Road, X, Y);
	if (OutProj.Along >= 0.0 && OutProj.Along <= OutProj.Length)
	{
		return FMath::Abs(OutProj.Across);
	}
	const double Clamped = FMath::Max(0.0, FMath::Min(OutProj.Length, OutProj.Along));
	const double D = OutProj.Along - Clamped;
	return FMath::Sqrt(D * D + OutProj.Across * OutProj.Across);
}

/** The nearest road that REFUSES frontage and whose reach the point is inside,
 *  or nullptr. Exists so a click beside a highway can be told WHY it is
 *  refused - the generic answer is "not within reach of any road", which is
 *  true and useless standing on a highway's verge with the highway in sight. */
static const FRoad* NearestNoFrontage(const FPlacementRules& R, const FEconRules& E,
	const TArray<FRoad>& Roads, double X, double Y)
{
	const FRoad* Best = nullptr;
	double BestDist = 0.0;
	for (const FRoad& Road : Roads)
	{
		if (RoadHasFrontage(E, Road))
		{
			continue;
		}
		FRoadProjection P;
		const double Dist = RoadDistance(Road, X, Y, P);
		if (Dist > RoadMaxReach(R, E, Road))
		{
			continue;
		}
		if (Best == nullptr || Dist < BestDist)
		{
			Best = &Road;
			BestDist = Dist;
		}
	}
	return Best;
}

const FRoad* ResolveRoad(const FPlacementRules& R, const FEconRules& E, const TArray<FRoad>& Roads,
	double X, double Y, FRoadLocal& OutLocal)
{
	if (InCrossing(R, E, Roads, X, Y))
	{
		return nullptr;
	}

	const FRoad* Best = nullptr;
	double BestDist = 0.0;
	double BestAlong = 0.0;
	double BestAcross = 0.0;
	for (const FRoad& Road : Roads)
	{
		// A road that refuses frontage is not a candidate at all: the highway
		// carries traffic past the city and a lot never faces one.
		if (!RoadHasFrontage(E, Road))
		{
			continue;
		}
		FRoadProjection P;
		const double Dist = RoadDistance(Road, X, Y, P);
		// THE ROAD'S OWN reach, applied as a FILTER before nearest-road
		// selection rather than as a test on the winner afterwards. With one
		// reach for every road the two orders are identical (if the nearest is
		// out of reach, all of them are); with per-type reaches a near, narrow
		// road would otherwise win the comparison and then fail the bound,
		// hiding a wider road that legally reaches the point.
		if (Dist > RoadMaxReach(R, E, Road))
		{
			continue;
		}
		if (Best == nullptr || Dist < BestDist)
		{
			Best = &Road;
			BestDist = Dist;
			BestAlong = P.Along;
			BestAcross = P.Across;
		}
	}

	if (Best == nullptr)
	{
		return nullptr;
	}
	OutLocal.Along  = BestAlong;
	OutLocal.Across = BestAcross;
	OutLocal.Side   = BestAcross >= 0.0 ? Best->SidePlus : Best->SideMinus;
	return Best;
}

const FRoad* FindRoad(const TArray<FRoad>& Roads, const FString& Id)
{
	for (const FRoad& Road : Roads)
	{
		if (Road.Id == Id)
		{
			return &Road;
		}
	}
	return nullptr;
}

FLotRect LotRect(const FPlacementRules& R, const FEconRules& E, const FRoad& Road,
	const FLotPlacement& Lot)
{
	// PER-TYPE FRONTAGE LINE: a lot on a dirt track sits 880 uu off its
	// centreline. BlockDepth is unchanged and deliberately so - the block
	// behind a lot is the same block whatever road it faces.
	const double Near = RoadHalf(R, E, Road);
	const double Far  = Near + R.BlockDepth;
	FLotRect Rect;
	if (!Road.bAxisX)
	{
		// Vertical road: the span runs in Y, the depth in X off the centreline.
		// Read off the road's own start rather than the literal 0 this used to
		// hard-code for "cross" - a vertical road a player draws is not
		// structurally different from the built-in one.
		const double Cx = Road.StartX;
		Rect.YMin = Lot.X0;
		Rect.YMax = Lot.X1;
		if (Lot.Side == TEXT("west"))
		{
			Rect.XMin = Cx - Far;  Rect.XMax = Cx - Near;
		}
		else
		{
			Rect.XMin = Cx + Near; Rect.XMax = Cx + Far;
		}
		return Rect;
	}
	const double Cy = Road.StartY;
	Rect.XMin = Lot.X0;
	Rect.XMax = Lot.X1;
	if (Lot.Side == TEXT("north"))
	{
		Rect.YMin = Cy + Near; Rect.YMax = Cy + Far;
	}
	else
	{
		Rect.YMin = Cy - Far;  Rect.YMax = Cy - Near;
	}
	return Rect;
}

bool RectsOverlap(const FLotRect& A, const FLotRect& B)
{
	return A.XMin < B.XMax && B.XMin < A.XMax && A.YMin < B.YMax && B.YMin < A.YMax;
}

static FClickResult Refuse(const FString& Reason)
{
	FClickResult Result;
	Result.bOk = false;
	Result.Reason = Reason;
	return Result;
}

FClickResult ResolveClick(const FPlacementBoard& Board, const FCityState& State,
	double X, double Y, bool bPinsActive, double Width)
{
	const FPlacementRules& R = Board.Rules;
	const FEconRules& E = Board.Econ;
	const TArray<FRoad> Roads = Board.AllRoads(State);

	FRoadLocal Local;
	const FRoad* Road = ResolveRoad(R, E, Roads, X, Y, Local);
	if (Road == nullptr)
	{
		if (InCrossing(R, E, Roads, X, Y))
		{
			return Refuse(FString::Printf(
				TEXT("in the crossing: (%.1f, %.1f) is pavement shared by more than one road"), X, Y));
		}
		// A refusal a player can act on, rather than the true-but-useless
		// 'off-board' they would otherwise get standing on a highway's verge
		// with the highway right in front of them.
		if (const FRoad* Near = NearestNoFrontage(R, E, Roads, X, Y))
		{
			return Refuse(FString::Printf(
				TEXT("no frontage: the %s is a %s and nothing may face it"),
				*Near->Id, *RoadTypeOf(*Near)));
		}
		// There is no separate "too far from a road" refusal: any road
		// ResolveRoad returns is already within RoadMaxReach by construction, so
		// that case can only surface here, never re-derived against a second
		// number that could drift from it.
		return Refuse(FString::Printf(
			TEXT("off-board: (%.1f, %.1f) is not within reach of any road"), X, Y));
	}

	const FRoadProjection Proj = ProjectToRoad(*Road, X, Y);
	const double Half = RoadHalf(R, E, *Road);
	if (Proj.Along >= 0.0 && Proj.Along <= Proj.Length && FMath::Abs(Local.Across) < Half)
	{
		return Refuse(FString::Printf(
			TEXT("in the road: |across|=%.0f is inside the %s corridor (half %.0f)"),
			FMath::Abs(Local.Across), *Road->Id, Half));
	}

	// WORLD SPACE FIRST, THEN SNAP. Neither plate minimum is a multiple of the
	// quantum, so snapping the road-relative offset would shift the grid
	// off-quantum silently. This way the arterial reduces exactly to the
	// pre-multi-road math and the cross street generalizes correctly.
	const double RoadStartOnAxis = Road->bAxisX ? Road->StartX : Road->StartY;
	const double RoadEndOnAxis   = Road->bAxisX ? Road->EndX   : Road->EndY;
	const double WorldCoord = RoadStartOnAxis + Local.Along;
	const double X0 = Snap(R, WorldCoord - Width / 2.0);
	const double X1 = X0 + Width;

	const double AxisMin = FMath::Min(RoadStartOnAxis, RoadEndOnAxis);
	const double AxisMax = FMath::Max(RoadStartOnAxis, RoadEndOnAxis);
	if (X0 < AxisMin || X1 > AxisMax)
	{
		return Refuse(FString::Printf(
			TEXT("off-board: snapped span [%.1f, %.1f] exceeds the %s road"), X0, X1, *Road->Id));
	}

	if (bPinsActive && Road->Id == Board.PinnedRoadId)
	{
		for (const FPinnedSpan& Pin : Board.PinnedSpans)
		{
			if (Pin.Side != Local.Side)
			{
				continue;
			}
			if (X0 < Pin.X1 && Pin.X0 < X1)
			{
				return Refuse(FString::Printf(
					TEXT("overlap: [%.1f, %.1f] crosses a pinned lot at [%.1f, %.1f]"),
					X0, X1, Pin.X0, Pin.X1));
			}
		}
	}

	FLotPlacement Candidate;
	Candidate.X0 = X0;
	Candidate.X1 = X1;
	Candidate.Side = Local.Side;
	Candidate.RoadId = Road->Id;
	const FLotRect Mine = LotRect(R, E, *Road, Candidate);

	// NO-FRONTAGE CORRIDORS. Every other refusal here is reached THROUGH the
	// road a lot faces, so a road nothing may face is unguarded by
	// construction: a highway is not a candidate in ResolveRoad, is not a lot,
	// and is not a pin, so without this a lot fronting some other road could be
	// laid straight across two thousand uu of motorway.
	//
	// DELIBERATELY NOT ALL ROADS. A lot can also overlap a FRONTAGE road's
	// corridor - the oracle's own test 39 places one in the 740 uu the arterial
	// and a road drawn 3000 uu from it leave between their pavements, which is
	// less than BlockDepth. That is a real, PRE-EXISTING gap; closing it moves
	// where lots may go on boards that already exist, which is the owner's call
	// and not part of road types. Raised on the board, not silently fixed here.
	for (const FRoad& Other : Roads)
	{
		if (RoadHasFrontage(E, Other))
		{
			continue;
		}
		if (RectsOverlap(Mine, RoadRect(R, E, Other)))
		{
			return Refuse(FString::Printf(
				TEXT("in the road: [%.1f, %.1f] would run across the %s, a %s"),
				X0, X1, *Other.Id, *RoadTypeOf(Other)));
		}
	}

	// Sorted, so a refusal names the same lot every run. The Python iterates a
	// dict in insertion order; two lots can both overlap, and a message that
	// changes between runs is a message nobody can act on.
	TArray<FString> Ids;
	State.Parcels.GetKeys(Ids);
	Ids.Sort([](const FString& A, const FString& B) { return A < B; });
	for (const FString& Id : Ids)
	{
		const FParcelState& P = State.Parcels[Id];
		if (!P.Placement.IsSet())
		{
			continue;
		}
		const FLotPlacement& Other = P.Placement.GetValue();
		const FString OtherRoadId = LotRoadId(Other);
		const FRoad* OtherRoad = FindRoad(Roads, OtherRoadId);
		if (OtherRoad == nullptr)
		{
			// The Python raises KeyError here. Saying so is better than either
			// crashing or silently treating the lot as absent, which would let a
			// click land on ground something is standing on.
			return Refuse(FString::Printf(
				TEXT("stale lot: '%s' names road '%s', which no longer exists"),
				*Id, *OtherRoadId));
		}
		// WORLD footprints, not per-road spans: the corner is where a
		// cross-street lot and an arterial lot share ground while their spans
		// never compare, because they live on different axes.
		if (RectsOverlap(Mine, LotRect(R, E, *OtherRoad, Other)))
		{
			return Refuse(FString::Printf(
				TEXT("overlap: [%.1f, %.1f] on the %s crosses an existing lot at [%.1f, %.1f] on the %s"),
				X0, X1, *Road->Id, Other.X0, Other.X1, *OtherRoadId));
		}
	}

	FClickResult Result;
	Result.bOk = true;
	Result.Lot = Candidate;
	return Result;
}

/** P1, P2, ... - the first not already taken. A distinct namespace from pinned
 *  ids, which are all letters, so a collision is structurally impossible. */
static FString NextPid(const FCityState& State)
{
	int32 N = 1;
	while (State.Parcels.Contains(FString::Printf(TEXT("P%d"), N)))
	{
		++N;
	}
	return FString::Printf(TEXT("P%d"), N);
}

FPlaceResult Place(const FPlacementBoard& Board, FCityState& State,
	double X, double Y, bool bPinsActive, double Width)
{
	FPlaceResult Result;

	int32 Placed = 0;
	for (const TPair<FString, FParcelState>& Pair : State.Parcels)
	{
		if (Pair.Value.Placement.IsSet())
		{
			++Placed;
		}
	}
	if (Placed >= Board.Rules.PoolSize)
	{
		// Checked BEFORE geometry: real clicks overlap-refuse around 28, so the
		// count check would never outlive the geometry check otherwise.
		Result.Reason = FString::Printf(
			TEXT("pool exhausted: %d/%d placed lots already active"), Placed, Board.Rules.PoolSize);
		return Result;
	}

	const FClickResult Click = ResolveClick(Board, State, X, Y, bPinsActive, Width);
	if (!Click.bOk)
	{
		Result.Reason = Click.Reason;
		return Result;
	}

	const FString Pid = NextPid(State);
	FParcelState P;
	P.Rid    = Board.Rules.V0Recipe;
	P.Tier   = 0;
	P.Width  = Width;
	P.bOwned = false;
	P.Accum  = 0.0;
	P.bFailed = false;
	P.Performance = 0.0;   // the economy's own neutral, not a second copy
	P.Placement = Click.Lot;
	State.Parcels.Add(Pid, P);

	Result.bOk = true;
	Result.Pid = Pid;
	return Result;
}

void PlanReactivation(const TArray<FString>& Pids, const TArray<FString>& PoolLabels,
	TArray<TPair<FString, FString>>& OutPairs, TArray<FString>& OutUnmatched)
{
	OutPairs.Reset();
	OutUnmatched.Reset();

	TArray<FString> SortedPids = Pids;
	TArray<FString> SortedLabels = PoolLabels;
	SortedPids.Sort([](const FString& A, const FString& B) { return A < B; });
	SortedLabels.Sort([](const FString& A, const FString& B) { return A < B; });

	const int32 Paired = FMath::Min(SortedPids.Num(), SortedLabels.Num());
	for (int32 i = 0; i < Paired; ++i)
	{
		OutPairs.Add(TPair<FString, FString>(SortedPids[i], SortedLabels[i]));
	}
	for (int32 i = Paired; i < SortedPids.Num(); ++i)
	{
		OutUnmatched.Add(SortedPids[i]);
	}
}

static FRoadDrawResult RefuseRoad(const FString& Reason)
{
	FRoadDrawResult Result;
	Result.bOk = false;
	Result.Reason = Reason;
	return Result;
}

FRoadDrawResult ResolveRoadDraw(const FPlacementBoard& Board, const FCityState& State,
	double X0, double Y0, double X1, double Y1, const FString& WidthClass, bool bPinsActive)
{
	const FPlacementRules& R = Board.Rules;
	const FEconRules& E = Board.Econ;

	// A BOUNDARY CHECK, not RoadTypeOf's problem: a bad string arriving from a
	// UI deserves a reason, and nothing may reach state carrying a type the
	// ruleset cannot price.
	if (!WidthClass.IsEmpty() && E.FindRoadType(WidthClass) == nullptr)
	{
		FString Known;
		for (const FString& T : RoadTypeNames())
		{
			Known += Known.IsEmpty() ? T : FString::Printf(TEXT(", %s"), *T);
		}
		return RefuseRoad(FString::Printf(
			TEXT("unknown road type '%s': expected one of %s"), *WidthClass, *Known));
	}

	const double Dx = X1 - X0;
	const double Dy = Y1 - Y0;

	// Whichever delta dominates by 3x decides the axis; the minor coordinate is
	// taken from the START point, then both ends snap to the position grid the
	// same way a lot's own span does. Neither dominant is a genuinely diagonal
	// gesture, and reinterpreting one as a straight road the player did not draw
	// is worse than refusing it.
	double SX0, SY0, SX1, SY1;
	if (FMath::Abs(Dx) >= 3.0 * FMath::Abs(Dy))
	{
		SX0 = Snap(R, X0); SY0 = Snap(R, Y0); SX1 = Snap(R, X1); SY1 = Snap(R, Y0);
	}
	else if (FMath::Abs(Dy) >= 3.0 * FMath::Abs(Dx))
	{
		SX0 = Snap(R, X0); SY0 = Snap(R, Y0); SX1 = Snap(R, X0); SY1 = Snap(R, Y1);
	}
	else
	{
		return RefuseRoad(TEXT(
			"too diagonal: roads must run close to north-south or east-west in this version"));
	}

	// CANONICAL DIRECTION, 2026-09-06. Which WAY the player dragged must not
	// change where the road's lots go, and until this line it did - badly.
	// ResolveClick recovers a lot's world position as RoadStartOnAxis + Along,
	// and Along runs along the segment's OWN direction, so a road drawn
	// east-to-west put every lot at 2 * StartX - X: a MIRROR IMAGE about the
	// start point. The same drag also flipped the side names, because the
	// normal is the direction rotated +90 degrees, so a click south of an
	// east-to-west road came back 'north'. Found while generalizing this
	// function to arbitrary directions (curved roads); reachable today by
	// dragging right to left, and silent whenever the mirrored span still
	// landed on the road.
	//
	// Ordering the endpoints fixes it at the SOURCE rather than at each of the
	// three places that read the direction, and changes nothing else: the
	// length is an absolute value, RoadRect takes min/max, and
	// RoadDictFromSegment reads orientation off the shape. The player gets the
	// road they drew.
	if (SX1 < SX0 || (SX1 == SX0 && SY1 < SY0))
	{
		Swap(SX0, SX1);
		Swap(SY0, SY1);
	}

	// Axis-aligned, so exactly one term is non-zero.
	const double Length = FMath::Abs(SX1 - SX0) + FMath::Abs(SY1 - SY0);
	if (Length < R.V0Width)
	{
		// A road shorter than one lot answers no question a player would ask it.
		return RefuseRoad(FString::Printf(
			TEXT("too short: %.0f uu is under the %.0f uu a single lot needs"), Length, R.V0Width));
	}

	if (!(Board.PlateXMin <= SX0 && SX0 <= Board.PlateXMax &&
	      Board.PlateXMin <= SX1 && SX1 <= Board.PlateXMax &&
	      Board.PlateYMin <= SY0 && SY0 <= Board.PlateYMax &&
	      Board.PlateYMin <= SY1 && SY1 <= Board.PlateYMax))
	{
		return RefuseRoad(TEXT("off-board: the drawn road would leave the plate"));
	}

	FRoadDrawResult Result;
	Result.Id = NextRoadId(State);
	Result.Segment.StartX = SX0;
	Result.Segment.StartY = SY0;
	Result.Segment.EndX = SX1;
	Result.Segment.EndY = SY1;
	Result.Segment.WidthClass = WidthClass;

	const TArray<FRoad> Roads = Board.AllRoads(State);
	const FLotRect Mine = RoadRect(R, E, RoadDictFromSegment(Result.Id, Result.Segment));

	for (const FRoad& Road : Roads)
	{
		if (RectsOverlap(Mine, RoadRect(R, E, Road)))
		{
			return RefuseRoad(FString::Printf(
				TEXT("crosses: the drawn road would cross the %s road"), *Road.Id));
		}
	}

	// Placed lots, in id order so the named lot does not depend on insertion.
	TArray<FString> Pids;
	State.Parcels.GetKeys(Pids);
	Pids.Sort([](const FString& A, const FString& B) { return A < B; });
	for (const FString& Pid : Pids)
	{
		const FParcelState& P = State.Parcels[Pid];
		if (!P.Placement.IsSet())
		{
			continue;
		}
		const FLotPlacement& Lot = P.Placement.GetValue();
		const FString LotRoad = LotRoadId(Lot);
		const FRoad* Road = FindRoad(Roads, LotRoad);
		if (Road == nullptr)
		{
			return RefuseRoad(FString::Printf(
				TEXT("stale lot: '%s' names road '%s', which no longer exists"), *Pid, *LotRoad));
		}
		if (RectsOverlap(Mine, LotRect(R, E, *Road, Lot)))
		{
			return RefuseRoad(FString::Printf(
				TEXT("overlap: the drawn road would cross an existing lot at [%.1f, %.1f] on the %s"),
				Lot.X0, Lot.X1, *LotRoad));
		}
	}

	// PINS ARE A SEPARATE SCAN. A pin carries no placement, so the loop above
	// skips every one of them by construction - without this a drawn road could
	// run through a standing building.
	if (bPinsActive)
	{
		const FRoad* Arterial = FindRoad(Roads, Board.PinnedRoadId);
		if (Arterial != nullptr)
		{
			for (const FPinnedSpan& Pin : Board.PinnedSpans)
			{
				FLotPlacement PinLot;
				PinLot.X0 = Pin.X0;
				PinLot.X1 = Pin.X1;
				PinLot.Side = Pin.Side;
				PinLot.RoadId = Board.PinnedRoadId;
				if (RectsOverlap(Mine, LotRect(R, E, *Arterial, PinLot)))
				{
					return RefuseRoad(FString::Printf(
						TEXT("overlap: the drawn road would cross a pinned lot at [%.1f, %.1f]"),
						Pin.X0, Pin.X1));
				}
			}
		}
	}

	// COST LAST, after every geometric refusal: a road that crosses a building
	// is illegal whatever the balance, and quoting the price of a road that
	// could never have been drawn is noise.
	double Cost = 0.0;
	if (!RoadCost(E, Result.Segment, Cost))
	{
		// Unreachable through the guard at the top of this function; said out
		// loud rather than defaulted, because a silently free road is worse
		// than a refused one.
		return RefuseRoad(FString::Printf(
			TEXT("unknown road type '%s': the ruleset cannot price it"),
			*RoadTypeOf(Result.Segment)));
	}
	if (State.Money < Cost)
	{
		return RefuseRoad(FString::Printf(
			TEXT("can't afford: a %.0f uu %s costs %.2f, money is %.2f"),
			Length, *RoadTypeOf(Result.Segment), Cost, State.Money));
	}

	Result.bOk = true;
	return Result;
}

double RoadRentMultiplier(const FPlacementBoard& Board, const FCityState& State,
	const FLotPlacement& Lot)
{
	const FPlacementRules& R = Board.Rules;
	const FEconRules& E = Board.Econ;
	const TArray<FRoad> Roads = Board.AllRoads(State);

	const FRoad* Own = FindRoad(Roads, LotRoadId(Lot));
	if (Own == nullptr)
	{
		// A lot naming a road that no longer exists. Neutral is the only honest
		// answer here; the click path refuses such a lot with a reason, and a
		// multiplier has no way to say anything.
		return 1.0;
	}
	const FRoadTypeRules* OwnType = RoadRulesFor(E, *Own);
	double Mult = OwnType == nullptr ? 1.0 : OwnType->RentMult;

	// THE SECOND MECHANISM. A road that refuses frontage lifts every lot within
	// RoadHighwayReach of its PAVEMENT - proximity, not frontage, because
	// nothing ever fronts one and a frontage-only reading would leave
	// road_rent_mult_highway dead in the rules file. THEY MULTIPLY: a dirt track
	// beside a motorway is 0.75 x 1.1. Flagged for the owner, who may read the
	// table's "rents at 1.1x" as an absolute instead.
	const FLotRect Mine = LotRect(R, E, *Own, Lot);
	for (const FRoad& Road : Roads)
	{
		if (RoadHasFrontage(E, Road))
		{
			continue;
		}
		if (RectDistance(Mine, RoadRect(R, E, Road)) <= E.RoadHighwayReach)
		{
			if (const FRoadTypeRules* T = RoadRulesFor(E, Road))
			{
				Mult *= T->RentMult;
			}
		}
	}
	return Mult;
}

FRoadDrawResult DrawRoad(const FPlacementBoard& Board, FCityState& State,
	double X0, double Y0, double X1, double Y1, const FString& WidthClass, bool bPinsActive)
{
	FRoadDrawResult Result = ResolveRoadDraw(Board, State, X0, Y0, X1, Y1, WidthClass, bPinsActive);
	if (!Result.bOk)
	{
		return Result;
	}
	// THE MONEY MOVES HERE, and only here: ResolveRoadDraw decides whether the
	// city can pay, so the ghost preview can say "can't afford" without
	// spending anything, and this is what actually spends it. Charged from the
	// SAME segment that was quoted, through the same RoadCost, so the amount
	// charged cannot differ from the amount shown.
	double Cost = 0.0;
	if (RoadCost(Board.Econ, Result.Segment, Cost))
	{
		State.Money -= Cost;
	}
	// Inserted UNCHANGED, not re-derived.
	State.Roads.Add(Result.Id, Result.Segment);
	return Result;
}

} // namespace Stacktown
