#include "StacktownWorldBoard.h"
#include "Misc/Paths.h"

namespace Stacktown
{
	FPlacementBoard TemporaryBoard()
	{
		// SUPERSEDED by FPlacementBoard::Default(), which this now forwards to.
		// Left as a one-line shim rather than deleted so the coordinator's two
		// call sites (StacktownAgreement.cpp, StacktownPlayerController.cpp)
		// pick up the pinned spans without this seat editing their files. Safe
		// to delete once those call Default() directly.
		return FPlacementBoard::Default();
	}

	FPlacementBoard TemporaryBoard(const FEconRules& Rules)
	{
		FPlacementBoard Board = FPlacementBoard::Default();
		Board.Econ = Rules;
		return Board;
	}
}

namespace Stacktown
{
	FString RulesFilePath()
	{
		return FPaths::ProjectContentDir() / TEXT("Stacktown/Rules/econrules.json");
	}
}
