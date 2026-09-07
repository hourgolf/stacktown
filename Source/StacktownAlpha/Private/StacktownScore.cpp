#include "StacktownScore.h"

namespace Stacktown
{
	static constexpr double RoadBonusPer100uu = 5.0;    // proposed
	static constexpr double FailedLotPenalty  = 50.0;   // proposed

	FScoreBreakdown ScoreBreakdown(const FEconRules& R, const FCityState& S)
	{
		FScoreBreakdown B;
		B.Money = S.Money;
		for (const TPair<FString, FParcelState>& Pair : S.Parcels)
		{
			const FParcelState& P = Pair.Value;
			if (!P.bOwned) { continue; }
			B.LotValue += Price(R, P.Tier, P.Width);
			if (P.bFailed) { B.FailedPenalty += FailedLotPenalty; }
		}
		for (const TPair<FString, FRoadSegment>& Pair : S.Roads)
		{
			const FRoadSegment& Seg = Pair.Value;
			const double Len = FMath::Sqrt(FMath::Square(Seg.EndX - Seg.StartX) + FMath::Square(Seg.EndY - Seg.StartY));
			B.RoadBonus += RoadBonusPer100uu * (Len / 100.0);
		}
		B.Total = B.Money + B.LotValue + B.RoadBonus - B.FailedPenalty;
		return B;
	}

	double Score(const FEconRules& R, const FCityState& S)
	{
		return ScoreBreakdown(R, S).Total;
	}

	const TArray<double>& GoalLadder()
	{
		static const TArray<double> Ladder = { 1000.0, 5000.0, 20000.0, 100000.0 };
		return Ladder;
	}

	int32 GoalsReached(double InScore)
	{
		int32 N = 0;
		for (double Rung : GoalLadder()) { if (InScore >= Rung) { ++N; } }
		return N;
	}
}
