#pragma once

#include "CoreMinimal.h"
#include "StacktownPlacement.h"

namespace Stacktown
{
	// Stacktown::TemporaryBoard lived here until 2026-09-06 (queue item 9). It
	// was a one-line shim forwarding to FPlacementBoard::Default() so the
	// coordinator's call sites could pick up the pinned spans without this seat
	// editing their files; every one of them now calls Default() - or its
	// live-ruleset overload - directly, so the shim is gone rather than left as
	// a second name for the same board.

	/** The one copy of econrules.json: Content/Stacktown/Rules, staged as UFS so a packaged app carries it. */
	STACKTOWNALPHA_API FString RulesFilePath();
}
