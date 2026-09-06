// Ported from Content/Python/placement.py, self-tests 1-27. See
// StacktownPlacement.h for the scope boundary against step 4 and for why the
// board is injected rather than derived.

#include "StacktownPlacement.h"

namespace Stacktown
{

TArray<FRoad> FPlacementBoard::AllRoads(const FCityState& State) const
{
	// STEP 4 adds the player's drawn segments here, parsed out of
	// State.RoadsJson. Deliberately not silently omitted: the parameter is
	// taken now, and every caller already routes through this, so step 4
	// changes one body instead of hunting call sites - which is exactly what
	// the Python's own _all_roads did when roads became dynamic.
	(void)State;
	return Roads;
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

bool InCrossing(const FPlacementRules& R, const TArray<FRoad>& Roads, double X, double Y)
{
	int32 Count = 0;
	for (const FRoad& Road : Roads)
	{
		const FRoadProjection P = ProjectToRoad(Road, X, Y);
		if (P.Along >= 0.0 && P.Along <= P.Length && FMath::Abs(P.Across) < R.RoadHalf)
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

const FRoad* ResolveRoad(const FPlacementRules& R, const TArray<FRoad>& Roads,
	double X, double Y, FRoadLocal& OutLocal)
{
	if (InCrossing(R, Roads, X, Y))
	{
		return nullptr;
	}

	const FRoad* Best = nullptr;
	double BestDist = 0.0;
	double BestAlong = 0.0;
	double BestAcross = 0.0;
	for (const FRoad& Road : Roads)
	{
		const FRoadProjection P = ProjectToRoad(Road, X, Y);
		double Dist;
		if (P.Along >= 0.0 && P.Along <= P.Length)
		{
			Dist = FMath::Abs(P.Across);
		}
		else
		{
			// Point-to-SEGMENT: past an end, measure to the end itself. An
			// infinite-line distance would read 0 for a click far past the
			// arterial's east end but sitting on y=0, and wrongly accept.
			const double Clamped = FMath::Max(0.0, FMath::Min(P.Length, P.Along));
			const double D = P.Along - Clamped;
			Dist = FMath::Sqrt(D * D + P.Across * P.Across);
		}
		if (Best == nullptr || Dist < BestDist)
		{
			Best = &Road;
			BestDist = Dist;
			BestAlong = P.Along;
			BestAcross = P.Across;
		}
	}

	if (Best == nullptr || BestDist > R.RoadMaxReach)
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

FLotRect LotRect(const FPlacementRules& R, const FRoad& Road, const FLotPlacement& Lot)
{
	const double Near = R.RoadHalf;
	const double Far  = R.RoadHalf + R.BlockDepth;
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
	const TArray<FRoad> Roads = Board.AllRoads(State);

	FRoadLocal Local;
	const FRoad* Road = ResolveRoad(R, Roads, X, Y, Local);
	if (Road == nullptr)
	{
		if (InCrossing(R, Roads, X, Y))
		{
			return Refuse(FString::Printf(
				TEXT("in the crossing: (%.1f, %.1f) is pavement shared by more than one road"), X, Y));
		}
		// There is no separate "too far from a road" refusal: any road
		// ResolveRoad returns is already within RoadMaxReach by construction, so
		// that case can only surface here, never re-derived against a second
		// number that could drift from it.
		return Refuse(FString::Printf(
			TEXT("off-board: (%.1f, %.1f) is not within reach of any road"), X, Y));
	}

	const FRoadProjection Proj = ProjectToRoad(*Road, X, Y);
	if (Proj.Along >= 0.0 && Proj.Along <= Proj.Length && FMath::Abs(Local.Across) < R.RoadHalf)
	{
		return Refuse(FString::Printf(
			TEXT("in the road: |across|=%.0f is inside the %s corridor (half %.0f)"),
			FMath::Abs(Local.Across), *Road->Id, R.RoadHalf));
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
	const FLotRect Mine = LotRect(R, *Road, Candidate);

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
		if (RectsOverlap(Mine, LotRect(R, *OtherRoad, Other)))
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

} // namespace Stacktown
