#pragma once

#include "CoreMinimal.h"
#include "StacktownPlacement.h"

namespace Stacktown
{
	/** TEMPORARY (board item 5): the placement board with its two built-in roads
	 *  exactly as the oracle fixture declares them, until the seat's runtime
	 *  factory lands. Coordinator-owned; delete when FPlacementBoard::Default() exists. */
	STACKTOWNALPHA_API FPlacementBoard TemporaryBoard();

	/** The same board carrying the LIVE ruleset, for the road-type mechanics:
	 *  costs, widths, frontage and the rent multiplier are all econrules.json's.
	 *  FPlacementBoard ships the same table as its default, so the no-argument
	 *  form measures the city correctly - this form is what makes an edit to
	 *  econrules.json take effect without a recompile, which is the whole point
	 *  of the numbers being data. */
	STACKTOWNALPHA_API FPlacementBoard TemporaryBoard(const FEconRules& Rules);

	/** The one copy of econrules.json: Content/Stacktown/Rules, staged as UFS so a packaged app carries it. */
	STACKTOWNALPHA_API FString RulesFilePath();
}
