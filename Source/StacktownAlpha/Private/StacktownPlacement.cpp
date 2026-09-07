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
	Board.Rules.WidthQuantum    = BoardData::WidthQuantum;
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
	// rather than stored; the width class and the path are the two things a
	// segment genuinely carries that its shape cannot say.
	Road.WidthClass = Seg.WidthClass;
	Road.Path = Seg.Path;
	// ANY DIRECTION since 2026-09-06 (item 11). The names come off the NORMAL,
	// not off a same-X / same-Y test: the normal is the direction rotated +90
	// degrees, whichever of its components dominates decides which pair of
	// names applies, and its sign decides which is SidePlus. Not a third
	// convention - it REDUCES EXACTLY to the two the built-ins already use (a
	// horizontal road's normal is +Y, so plus is north; a vertical one's is -X,
	// so plus is west) - and it is the only rule that stays correct for a road
	// running down and to the right, where the dominant axis of the DIRECTION
	// and the side the normal actually points to disagree.
	//
	// bAxisX is now the dominant axis of the run, kept because the lot frame
	// and the fixtures still read it; nothing decides geometry from it.
	const double Dx = Seg.EndX - Seg.StartX;
	const double Dy = Seg.EndY - Seg.StartY;
	const double Len = FMath::Sqrt(Dx * Dx + Dy * Dy);
	const double Nx = Len > 0.0 ? -Dy / Len : 0.0;
	const double Ny = Len > 0.0 ?  Dx / Len : 1.0;
	if (FMath::Abs(Ny) >= FMath::Abs(Nx))
	{
		Road.bAxisX = true;
		Road.SidePlus  = Ny >= 0.0 ? TEXT("north") : TEXT("south");
		Road.SideMinus = Ny >= 0.0 ? TEXT("south") : TEXT("north");
	}
	else
	{
		Road.bAxisX = false;
		Road.SidePlus  = Nx >= 0.0 ? TEXT("east") : TEXT("west");
		Road.SideMinus = Nx >= 0.0 ? TEXT("west") : TEXT("east");
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

FRoadFrame RoadFrame(const FRoad& Road)
{
	FRoadFrame F;
	F.Ox = Road.StartX;
	F.Oy = Road.StartY;
	const double Dx = Road.EndX - Road.StartX;
	const double Dy = Road.EndY - Road.StartY;
	F.Length = FMath::Sqrt(Dx * Dx + Dy * Dy);
	F.Ux = Dx / F.Length;
	F.Uy = Dy / F.Length;
	F.Nx = -F.Uy;
	F.Ny =  F.Ux;
	F.S0 = F.Ox * F.Ux + F.Oy * F.Uy;
	return F;
}

void PointAt(const FRoadFrame& F, double S, double Offset, double& OutX, double& OutY)
{
	const double T = S - F.S0;
	OutX = F.Ox + F.Ux * T + F.Nx * Offset;
	OutY = F.Oy + F.Uy * T + F.Ny * Offset;
}

/** The band between two projections and two offsets, corners in order ROUND
 *  the shape - which the separating-axis test needs; a figure-eight is not a
 *  convex hull and would separate on axes it should not. */
static FQuad BandQuad(const FRoadFrame& F, double S0, double S1, double Off0, double Off1)
{
	FQuad Q;
	PointAt(F, S0, Off0, Q.X[0], Q.Y[0]);
	PointAt(F, S1, Off0, Q.X[1], Q.Y[1]);
	PointAt(F, S1, Off1, Q.X[2], Q.Y[2]);
	PointAt(F, S0, Off1, Q.X[3], Q.Y[3]);
	return Q;
}

FQuad LotQuad(const FPlacementRules& R, const FEconRules& E, const FRoad& Road,
	const FLotPlacement& Lot)
{
	const FRoadFrame F = RoadFrame(Road);
	const double Near = RoadHalf(R, E, Road);
	const double Far  = Near + R.BlockDepth;
	const double Sign = Lot.Side == Road.SidePlus ? 1.0 : -1.0;
	return BandQuad(F, Lot.X0, Lot.X1, Sign * Near, Sign * Far);
}

FQuad RoadQuad(const FPlacementRules& R, const FEconRules& E, const FRoad& Road)
{
	const FRoadFrame F = RoadFrame(Road);
	const double Half = RoadHalf(R, E, Road);
	return BandQuad(F, F.S0, F.S0 + F.Length, -Half, Half);
}

FLotRect QuadRect(const FQuad& Q)
{
	FLotRect Rect;
	Rect.XMin = Rect.XMax = Q.X[0];
	Rect.YMin = Rect.YMax = Q.Y[0];
	for (int32 i = 1; i < 4; ++i)
	{
		Rect.XMin = FMath::Min(Rect.XMin, Q.X[i]);
		Rect.XMax = FMath::Max(Rect.XMax, Q.X[i]);
		Rect.YMin = FMath::Min(Rect.YMin, Q.Y[i]);
		Rect.YMax = FMath::Max(Rect.YMax, Q.Y[i]);
	}
	return Rect;
}

bool QuadsOverlap(const FQuad& A, const FQuad& B)
{
	const FQuad* Polys[2] = { &A, &B };
	for (int32 P = 0; P < 2; ++P)
	{
		const FQuad& Poly = *Polys[P];
		for (int32 i = 0; i < 4; ++i)
		{
			const int32 j = (i + 1) % 4;
			double Ax = -(Poly.Y[j] - Poly.Y[i]);
			double Ay =   Poly.X[j] - Poly.X[i];
			const double N = FMath::Sqrt(Ax * Ax + Ay * Ay);
			if (N == 0.0)
			{
				continue;
			}
			Ax /= N;
			Ay /= N;
			double AMin = A.X[0] * Ax + A.Y[0] * Ay, AMax = AMin;
			double BMin = B.X[0] * Ax + B.Y[0] * Ay, BMax = BMin;
			for (int32 k = 1; k < 4; ++k)
			{
				const double Pa = A.X[k] * Ax + A.Y[k] * Ay;
				AMin = FMath::Min(AMin, Pa);
				AMax = FMath::Max(AMax, Pa);
				const double Pb = B.X[k] * Ax + B.Y[k] * Ay;
				BMin = FMath::Min(BMin, Pb);
				BMax = FMath::Max(BMax, Pb);
			}
			// Touching is separated, matching RectsOverlap's strict <.
			if (AMax <= BMin || BMax <= AMin)
			{
				return false;
			}
		}
	}
	return true;
}

FLotRect RoadRect(const FPlacementRules& R, const FEconRules& E, const FRoad& Road)
{
	return QuadRect(RoadQuad(R, E, Road));
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
	// COUNTED BY PATH, not by chord (curved roads, item 11). A drawn curve is
	// many chords 410 uu apart whose corridors overlap almost everywhere along
	// it, by construction; counting chords would make the whole of every curve
	// "the crossing" and refuse every lot on it. Chords of ONE road are one
	// road here, and a straight road is its own path, so nothing about the two
	// built-ins or a one-segment draw changes.
	TSet<FString> Seen;
	for (const FRoad& Road : Roads)
	{
		const FRoadProjection P = ProjectToRoad(Road, X, Y);
		// The ROAD'S OWN corridor, not the one avenue constant: a highway is
		// 2000 wide and its pavement has to be 2000 wide here too.
		if (P.Along >= 0.0 && P.Along <= P.Length && FMath::Abs(P.Across) < RoadHalf(R, E, Road))
		{
			Seen.Add(RoadPathId(Road));
		}
	}
	return Seen.Num() > 1;
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
	// NOW THE BOUNDING BOX of LotQuad, which is the same rectangle for an
	// axis-aligned road and the honest envelope for a diagonal one. Every
	// existing caller keeps its four numbers; the OVERLAP scans moved to the
	// quads, because a diagonal lot's box is much bigger than the lot and
	// would refuse clicks that are fine.
	return QuadRect(LotQuad(R, E, Road, Lot));
}

bool RectsOverlap(const FLotRect& A, const FLotRect& B)
{
	return A.XMin < B.XMax && B.XMin < A.XMax && A.YMin < B.YMax && B.YMin < A.YMax;
}

FString RoadPathId(const FRoad& Road)
{
	return Road.Path.IsEmpty() ? Road.Id : Road.Path;
}

TArray<FRoad> PathNeighbours(const TArray<FRoad>& Roads, const FRoad& Road)
{
	TArray<FRoad> Out;
	const FString Pid = RoadPathId(Road);
	for (const FRoad& Other : Roads)
	{
		if (Other.Id == Road.Id || RoadPathId(Other) != Pid)
		{
			continue;
		}
		const bool bJoined =
			(Other.EndX   == Road.StartX && Other.EndY   == Road.StartY) ||
			(Other.StartX == Road.EndX   && Other.StartY == Road.EndY)   ||
			(Other.StartX == Road.StartX && Other.StartY == Road.StartY) ||
			(Other.EndX   == Road.EndX   && Other.EndY   == Road.EndY);
		if (bJoined)
		{
			Out.Add(Other);
		}
	}
	return Out;
}

void PathSpan(const TArray<FRoad>& Roads, const FRoad& Road, double& OutMin, double& OutMax)
{
	const FRoadFrame F = RoadFrame(Road);
	OutMin = F.S0;
	OutMax = F.S0 + F.Length;
	for (const FRoad& Other : PathNeighbours(Roads, Road))
	{
		const double Ends[2][2] = { { Other.StartX, Other.StartY }, { Other.EndX, Other.EndY } };
		for (int32 i = 0; i < 2; ++i)
		{
			const double S = Ends[i][0] * F.Ux + Ends[i][1] * F.Uy;
			OutMin = FMath::Min(OutMin, S);
			OutMax = FMath::Max(OutMax, S);
		}
	}
}

/** A uniform Catmull-Rom through `Nodes`, densely sampled.
 *
 *  THE END TANGENTS ARE EXTRAPOLATED, not duplicated: the phantom control
 *  point before the first node is 2*P0 - P1, which continues the line the
 *  first two nodes make. Duplicating the endpoint instead halves that tangent,
 *  which changes the curve's shape near its ends - so the road would start off
 *  along a curve the player did not draw. */
static TArray<FVector2D> CatmullRom(const TArray<FVector2D>& Nodes, int32 PerSpan)
{
	TArray<FVector2D> Out;
	if (Nodes.Num() < 2)
	{
		for (const FVector2D& N : Nodes) { Out.Add(N); }
		return Out;
	}
	TArray<FVector2D> Ctrl;
	Ctrl.Add(FVector2D(2.0 * Nodes[0].X - Nodes[1].X, 2.0 * Nodes[0].Y - Nodes[1].Y));
	for (const FVector2D& N : Nodes) { Ctrl.Add(N); }
	Ctrl.Add(FVector2D(2.0 * Nodes[Nodes.Num() - 1].X - Nodes[Nodes.Num() - 2].X,
		2.0 * Nodes[Nodes.Num() - 1].Y - Nodes[Nodes.Num() - 2].Y));

	Out.Add(Nodes[0]);
	for (int32 i = 0; i + 1 < Nodes.Num(); ++i)
	{
		const FVector2D& P0 = Ctrl[i];
		const FVector2D& P1 = Ctrl[i + 1];
		const FVector2D& P2 = Ctrl[i + 2];
		const FVector2D& P3 = Ctrl[i + 3];
		for (int32 k = 1; k <= PerSpan; ++k)
		{
			const double T  = static_cast<double>(k) / static_cast<double>(PerSpan);
			const double T2 = T * T;
			const double T3 = T2 * T;
			Out.Add(FVector2D(
				0.5 * ((2.0 * P1.X) + (-P0.X + P2.X) * T
					+ (2.0 * P0.X - 5.0 * P1.X + 4.0 * P2.X - P3.X) * T2
					+ (-P0.X + 3.0 * P1.X - 3.0 * P2.X + P3.X) * T3),
				0.5 * ((2.0 * P1.Y) + (-P0.Y + P2.Y) * T
					+ (2.0 * P0.Y - 5.0 * P1.Y + 4.0 * P2.Y - P3.Y) * T2
					+ (-P0.Y + 3.0 * P1.Y - 3.0 * P2.Y + P3.Y) * T3)));
		}
	}
	return Out;
}

TArray<FVector2D> SamplePath(const FPlacementRules& R, const TArray<FVector2D>& Nodes, double Spacing)
{
	const TArray<FVector2D> Dense = CatmullRom(Nodes, 64);
	TArray<FVector2D> Out;
	if (Dense.Num() < 2)
	{
		for (const FVector2D& P : Dense) { Out.Add(FVector2D(Snap(R, P.X), Snap(R, P.Y))); }
		return Out;
	}

	Out.Add(Dense[0]);
	double Carried = 0.0;
	for (int32 i = 1; i < Dense.Num(); ++i)
	{
		const double Ax = Dense[i - 1].X, Ay = Dense[i - 1].Y;
		const double Bx = Dense[i].X,     By = Dense[i].Y;
		const double Seg = FMath::Sqrt((Bx - Ax) * (Bx - Ax) + (By - Ay) * (By - Ay));
		if (Seg == 0.0)
		{
			continue;
		}
		double Pos = 0.0;
		while (Carried + (Seg - Pos) >= Spacing)
		{
			Pos += Spacing - Carried;
			const double T = Pos / Seg;
			Out.Add(FVector2D(Ax + (Bx - Ax) * T, Ay + (By - Ay) * T));
			Carried = 0.0;
		}
		Carried += Seg - Pos;
	}
	if (Out[Out.Num() - 1] != Dense[Dense.Num() - 1])
	{
		Out.Add(Dense[Dense.Num() - 1]);
	}
	// THE LEFTOVER IS MERGED, not left as a stub: a 50 uu chord is a road
	// segment with a 2260 uu corridor and no length - a bump on the board and
	// a hole in the frontage.
	if (Out.Num() >= 3)
	{
		const FVector2D& A = Out[Out.Num() - 2];
		const FVector2D& B = Out[Out.Num() - 1];
		if (FMath::Sqrt((B.X - A.X) * (B.X - A.X) + (B.Y - A.Y) * (B.Y - A.Y)) < Spacing / 2.0)
		{
			Out.RemoveAt(Out.Num() - 2);
		}
	}

	TArray<FVector2D> Snapped;
	for (const FVector2D& P : Out)
	{
		const FVector2D Q(Snap(R, P.X), Snap(R, P.Y));
		// The snap can collide two vertices that were under a quantum apart.
		if (Snapped.Num() == 0 || Snapped[Snapped.Num() - 1] != Q)
		{
			Snapped.Add(Q);
		}
	}
	return Snapped;
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

	// PROJECTION SPACE, THEN SNAP (2026-09-06, item 11). X0/X1 have always
	// been world coordinates on the road's axis; generalized, they are the
	// scalar projection of the span onto the road's own unit direction, and
	// the world point at projection S is Start + U * (S - S0). For the
	// arterial S0 is PlateXMin and Along is x - PlateXMin, so S0 + Along IS x -
	// the identity the fixture checks - and the same holds in y for the cross
	// street. So this is one line different from the world coordinate it
	// replaces and no lot already saved changes meaning.
	//
	// The snap still happens in this space rather than on Along, and for the
	// same reason as before: round-half-to-even breaks ties on the parity of
	// the integer part, so snapping road-relative can land a quantum away.
	const FRoadFrame Frame = RoadFrame(*Road);
	// THE JOINED RUN, not this chord alone (curved roads, item 11): a curve is
	// sampled at 410 and the narrowest lot is 820, so a lot never fits inside
	// one chord and every click on a curve was refused on open ground.
	double AxisMin = 0.0, AxisMax = 0.0;
	PathSpan(Roads, *Road, AxisMin, AxisMax);
	const double X0 = Snap(R, Frame.S0 + Local.Along - Width / 2.0);
	const double X1 = X0 + Width;

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
	// QUADS, not bounding boxes: a diagonal lot's box is much bigger than the
	// lot and would refuse clicks that are fine. QuadsOverlap reduces exactly
	// to RectsOverlap while everything is axis-aligned.
	const FQuad Mine = LotQuad(R, E, *Road, Candidate);

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
		if (QuadsOverlap(Mine, RoadQuad(R, E, Other)))
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
		if (QuadsOverlap(Mine, LotQuad(R, E, *OtherRoad, Other)))
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
	// ANY DIRECTION since 2026-09-06 (item 11). What used to be a REFUSAL is
	// now a SNAP THRESHOLD, at the same 3x dominance (about 18 degrees off an
	// axis): a drag that close to horizontal or vertical still snaps to
	// exactly that, because a player aiming down a street should get a
	// straight one and not a road two degrees out. Anything else is now the
	// road they drew. The snap branches are UNCHANGED, which is what keeps
	// every earlier case answering exactly as before; only the else arm moved
	// from a refusal to a free-direction road.
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
		SX0 = Snap(R, X0); SY0 = Snap(R, Y0); SX1 = Snap(R, X1); SY1 = Snap(R, Y1);
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

	// The CENTRELINE's length. Axis-aligned roads gave the same answer as the
	// sum of the two deltas; a diagonal does not, and it is the centreline
	// that a lot needs to fit along and that the type prices.
	const double Length = FMath::Sqrt((SX1 - SX0) * (SX1 - SX0) + (SY1 - SY0) * (SY1 - SY0));
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
	const FQuad Mine = RoadQuad(R, E, RoadDictFromSegment(Result.Id, Result.Segment));

	for (const FRoad& Road : Roads)
	{
		if (QuadsOverlap(Mine, RoadQuad(R, E, Road)))
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
		if (QuadsOverlap(Mine, LotQuad(R, E, *Road, Lot)))
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
				if (QuadsOverlap(Mine, LotQuad(R, E, *Arterial, PinLot)))
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

static FRoadPathResult RefusePath(const FString& Reason)
{
	FRoadPathResult Result;
	Result.bOk = false;
	Result.Reason = Reason;
	return Result;
}

/** C1, C2, ... - the first not claimed by any segment in state. A namespace
 *  distinct by construction from the chord ids (R + digits), the placed lots
 *  (P + digits) and the pins (letters). */
static FString NextPathId(const FCityState& State)
{
	TSet<FString> Taken;
	for (const auto& Pair : State.Roads)
	{
		Taken.Add(Pair.Value.Path.IsEmpty() ? Pair.Key : Pair.Value.Path);
	}
	int32 N = 1;
	while (Taken.Contains(FString::Printf(TEXT("C%d"), N)))
	{
		++N;
	}
	return FString::Printf(TEXT("C%d"), N);
}

static const TCHAR* Ordinal(int32 N)
{
	if (N % 100 >= 10 && N % 100 <= 20) { return TEXT("th"); }
	switch (N % 10)
	{
	case 1:  return TEXT("st");
	case 2:  return TEXT("nd");
	case 3:  return TEXT("rd");
	default: return TEXT("th");
	}
}

FRoadPathResult ResolveRoadPath(const FPlacementBoard& Board, const FCityState& State,
	const TArray<FVector2D>& Nodes, const FString& WidthClass, bool bPinsActive)
{
	const FPlacementRules& R = Board.Rules;
	const FEconRules& E = Board.Econ;

	if (!WidthClass.IsEmpty() && E.FindRoadType(WidthClass) == nullptr)
	{
		FString Known;
		for (const FString& T : RoadTypeNames())
		{
			Known += Known.IsEmpty() ? T : FString::Printf(TEXT(", %s"), *T);
		}
		return RefusePath(FString::Printf(
			TEXT("unknown road type '%s': expected one of %s"), *WidthClass, *Known));
	}
	if (Nodes.Num() < 2)
	{
		return RefusePath(TEXT("a road needs at least two nodes"));
	}

	const TArray<FVector2D> Pts = SamplePath(R, Nodes, R.WidthQuantum);
	if (Pts.Num() < 2)
	{
		return RefusePath(FString::Printf(
			TEXT("too short: the nodes are inside one %.0f uu grid step of each other"),
			R.PositionQuantum));
	}

	double Length = 0.0;
	for (int32 i = 0; i + 1 < Pts.Num(); ++i)
	{
		const double Dx = Pts[i + 1].X - Pts[i].X;
		const double Dy = Pts[i + 1].Y - Pts[i].Y;
		Length += FMath::Sqrt(Dx * Dx + Dy * Dy);
	}
	// THE PATH'S length, not each chord's: a 410 chord is under the 820 a lot
	// needs, and refusing every curve for that would measure the wrong thing.
	if (Length < R.V0Width)
	{
		return RefusePath(FString::Printf(
			TEXT("too short: %.0f uu is under the %.0f uu a single lot needs"),
			Length, R.V0Width));
	}

	// ON THE SAMPLED POLYLINE, not on the nodes: a Catmull-Rom reaches past
	// its own nodes on a bend, so nodes that are all inside the plate are not
	// a proof that the road is.
	for (const FVector2D& P : Pts)
	{
		if (!(Board.PlateXMin <= P.X && P.X <= Board.PlateXMax &&
		      Board.PlateYMin <= P.Y && P.Y <= Board.PlateYMax))
		{
			return RefusePath(FString::Printf(
				TEXT("off-board: the curve leaves the plate at [%.0f, %.0f]"), P.X, P.Y));
		}
	}

	FRoadPathResult Result;
	Result.PathId = NextPathId(State);
	{
		TSet<FString> Taken;
		for (const auto& Pair : State.Roads) { Taken.Add(Pair.Key); }
		int32 N = 1;
		for (int32 i = 0; i + 1 < Pts.Num(); ++i)
		{
			while (Taken.Contains(FString::Printf(TEXT("R%d"), N))) { ++N; }
			FRoadSegment Seg;
			Seg.StartX = Pts[i].X;     Seg.StartY = Pts[i].Y;
			Seg.EndX   = Pts[i + 1].X; Seg.EndY   = Pts[i + 1].Y;
			Seg.WidthClass = WidthClass;
			Seg.Path = Result.PathId;
			Result.Segments.Add(Seg);
			Taken.Add(FString::Printf(TEXT("R%d"), N));
			++N;
		}
	}
	// The ids, allocated in the same order as the chords above.
	TArray<FString> Ids;
	{
		TSet<FString> Taken;
		for (const auto& Pair : State.Roads) { Taken.Add(Pair.Key); }
		int32 N = 1;
		for (int32 i = 0; i < Result.Segments.Num(); ++i)
		{
			while (Taken.Contains(FString::Printf(TEXT("R%d"), N))) { ++N; }
			Ids.Add(FString::Printf(TEXT("R%d"), N));
			Taken.Add(Ids[i]);
			++N;
		}
	}

	const TArray<FRoad> Roads = Board.AllRoads(State);
	TArray<FString> Pids;
	State.Parcels.GetKeys(Pids);
	Pids.Sort([](const FString& A, const FString& B) { return A < B; });

	for (int32 k = 0; k < Result.Segments.Num(); ++k)
	{
		const FQuad Mine = RoadQuad(R, E, RoadDictFromSegment(Ids[k], Result.Segments[k]));
		for (const FRoad& Road : Roads)
		{
			if (QuadsOverlap(Mine, RoadQuad(R, E, Road)))
			{
				return RefusePath(FString::Printf(
					TEXT("crosses: the curve would cross the %s road at its %d%s chord"),
					*Road.Id, k + 1, Ordinal(k + 1)));
			}
		}
		for (const FString& Pid : Pids)
		{
			const FParcelState& Pa = State.Parcels[Pid];
			if (!Pa.Placement.IsSet()) { continue; }
			const FLotPlacement& Lot = Pa.Placement.GetValue();
			const FRoad* LotRoad = FindRoad(Roads, LotRoadId(Lot));
			if (LotRoad == nullptr)
			{
				return RefusePath(FString::Printf(
					TEXT("stale lot: '%s' names road '%s', which no longer exists"),
					*Pid, *LotRoadId(Lot)));
			}
			if (QuadsOverlap(Mine, LotQuad(R, E, *LotRoad, Lot)))
			{
				return RefusePath(FString::Printf(
					TEXT("overlap: the curve would cross an existing lot at [%.1f, %.1f] on the %s"),
					Lot.X0, Lot.X1, *LotRoadId(Lot)));
			}
		}
		if (bPinsActive)
		{
			const FRoad* Arterial = FindRoad(Roads, Board.PinnedRoadId);
			if (Arterial != nullptr)
			{
				for (const FPinnedSpan& Pin : Board.PinnedSpans)
				{
					FLotPlacement PinLot;
					PinLot.X0 = Pin.X0; PinLot.X1 = Pin.X1;
					PinLot.Side = Pin.Side; PinLot.RoadId = Board.PinnedRoadId;
					if (QuadsOverlap(Mine, LotQuad(R, E, *Arterial, PinLot)))
					{
						return RefusePath(FString::Printf(
							TEXT("overlap: the curve would cross a pinned lot at [%.1f, %.1f]"),
							Pin.X0, Pin.X1));
					}
				}
			}
		}
	}

	// ONE PRICE, for the whole gesture, from the polyline's own length rather
	// than summed per chord - the same number either way, said once.
	const FRoadTypeRules* Type = E.FindRoadType(
		WidthClass.IsEmpty() ? FString(DefaultRoadType()) : WidthClass);
	if (Type == nullptr)
	{
		return RefusePath(FString::Printf(
			TEXT("unknown road type '%s': the ruleset cannot price it"), *WidthClass));
	}
	const double Cost = Type->CostPer100uu * Length / 100.0;
	if (State.Money < Cost)
	{
		return RefusePath(FString::Printf(
			TEXT("can't afford: a %.0f uu %s costs %.2f, money is %.2f"),
			Length, *RoadTypeOf(Result.Segments[0]), Cost, State.Money));
	}

	Result.bOk = true;
	return Result;
}

FRoadPathResult DrawRoadPath(const FPlacementBoard& Board, FCityState& State,
	const TArray<FVector2D>& Nodes, const FString& WidthClass, bool bPinsActive)
{
	FRoadPathResult Result = ResolveRoadPath(Board, State, Nodes, WidthClass, bPinsActive);
	if (!Result.bOk)
	{
		return Result;
	}
	double Length = 0.0;
	for (const FRoadSegment& Seg : Result.Segments)
	{
		Length += RoadLength(Seg);
	}
	if (const FRoadTypeRules* Type = Board.Econ.FindRoadType(RoadTypeOf(Result.Segments[0])))
	{
		State.Money -= Type->CostPer100uu * Length / 100.0;
	}
	// Ids are re-derived here the same way ResolveRoadPath derived them, off a
	// state that has not changed in between.
	TSet<FString> Taken;
	for (const auto& Pair : State.Roads) { Taken.Add(Pair.Key); }
	int32 N = 1;
	for (const FRoadSegment& Seg : Result.Segments)
	{
		while (Taken.Contains(FString::Printf(TEXT("R%d"), N))) { ++N; }
		const FString Id = FString::Printf(TEXT("R%d"), N);
		State.Roads.Add(Id, Seg);
		Taken.Add(Id);
		++N;
	}
	return Result;
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
