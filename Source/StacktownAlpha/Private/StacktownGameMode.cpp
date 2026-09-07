#include "StacktownGameMode.h"
#include "StacktownCameraPawn.h"
#include "StacktownPlayerController.h"

AStacktownGameMode::AStacktownGameMode()
{
	DefaultPawnClass = AStacktownCameraPawn::StaticClass();
	PlayerControllerClass = AStacktownPlayerController::StaticClass();
}

void AStacktownGameMode::InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage)
{
	Super::InitGame(MapName, Options, ErrorMessage);
	// "Preparing SoundWaves" is printed during map load, before the controller's
	// BeginPlay could switch the notices off (frame 21:22 still showed it). A game
	// never shows engine notices; the editor keeps its own.
	if (!GIsEditor) { GAreScreenMessagesEnabled = false; }
}
