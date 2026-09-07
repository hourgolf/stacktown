#pragma once
#include "CoreMinimal.h"
#include "StacktownEconomyRules.h"

/** THE SCORE - PROPOSED, not ruled (Docs/MONDAY_DECISIONS.md section 1, 2026-09-06).
 *  One number a stranger can read on the bar, built only from facts the state
 *  already holds: money + the purchase value of every owned lot at its tier +
 *  a bonus per 100 uu of road drawn - a penalty per failed lot standing. The
 *  design lane's goal-loop one-pager and the owner's Monday word replace these
 *  numbers; the Python oracle gets the ruled formula then. Until then this is a
 *  frame to argue with. */
namespace Stacktown
{
	struct STACKTOWNALPHA_API FScoreBreakdown
	{
		double Money = 0.0, LotValue = 0.0, RoadBonus = 0.0, FailedPenalty = 0.0, Total = 0.0;
	};
	STACKTOWNALPHA_API FScoreBreakdown ScoreBreakdown(const FEconRules& R, const FCityState& S);
	STACKTOWNALPHA_API double Score(const FEconRules& R, const FCityState& S);
	/** The goal ladder (proposed): 1,000 / 5,000 / 20,000 / 100,000. */
	STACKTOWNALPHA_API const TArray<double>& GoalLadder();
	/** How many rungs of the ladder sit at or below the score (0..4). */
	STACKTOWNALPHA_API int32 GoalsReached(double Score);
}
