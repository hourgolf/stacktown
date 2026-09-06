#pragma once

#include "CoreMinimal.h"
#include "StacktownPlacement.h"

namespace Stacktown
{
	/** TEMPORARY (board item 5): the placement board with its two built-in roads
	 *  exactly as the oracle fixture declares them, until the seat's runtime
	 *  factory lands. Coordinator-owned; delete when FPlacementBoard::Default() exists. */
	STACKTOWNALPHA_API FPlacementBoard TemporaryBoard();

	/** The one copy of econrules.json: Content/Stacktown/Rules, staged as UFS so a packaged app carries it. */
	STACKTOWNALPHA_API FString RulesFilePath();
}
