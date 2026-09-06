#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "StacktownGameMode.generated.h"

/** Default pawn and controller for Stacktown: the C++ camera and its controller. */
UCLASS()
class STACKTOWNALPHA_API AStacktownGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AStacktownGameMode();
};
