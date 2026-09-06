#include "StacktownGameMode.h"
#include "StacktownCameraPawn.h"
#include "StacktownPlayerController.h"

AStacktownGameMode::AStacktownGameMode()
{
	DefaultPawnClass = AStacktownCameraPawn::StaticClass();
	PlayerControllerClass = AStacktownPlayerController::StaticClass();
}
