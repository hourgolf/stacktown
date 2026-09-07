#include "StacktownWorldBoard.h"
#include "Misc/Paths.h"

namespace Stacktown
{
	FString RulesFilePath()
	{
		return FPaths::ProjectContentDir() / TEXT("Stacktown/Rules/econrules.json");
	}
}
