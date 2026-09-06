#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "StacktownAgreement.generated.h"

/**
 * The live agreement instrument for Docs/STATE_HANDOVER.md Phase A: mirrors
 * the session's state file into the C++ economy and compares, lot by lot, what
 * the Python sync wrote onto the Blueprint parcels with what FactsForLabel
 * derives from the mirror. Coordinator tooling; callable from Python in a
 * running game. Returns a human-readable report; the first line is the verdict.
 */
UCLASS()
class STACKTOWNALPHA_API UStacktownAgreementLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Debug", meta = (WorldContext = "WorldContextObject"))
	static FString CompareMirrorWithWorld(const UObject* WorldContextObject);

	/** Spawn a C++ lot (StacktownLotVisual) for a placed parcel in the mirrored
	 *  state, posed by Stacktown::Lot, and report its pose beside the Blueprint
	 *  actor's transform for the same label. Debug only; the actor is transient. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Debug", meta = (WorldContext = "WorldContextObject"))
	static FString SpawnLotVisualFor(const UObject* WorldContextObject, const FString& Pid, bool bHideBlueprintTwin);
};
