#pragma once

#include "CoreMinimal.h"
#include "StacktownNight.generated.h"

/**
 * Night, ported from init_unreal._set_night / _apply_night_lights: the
 * design lane's NightAmount on MPC_WoodCity (0 day, 1 night) plus the rig's
 * lights dimmed by per-light factors, with day values captured once from the
 * actors themselves. Lights are found by actor name or label (editor builds)
 * or by an actor tag equal to that name (packaged builds, once the map
 * carries the tags).
 */
UCLASS()
class STACKTOWNALPHA_API UStacktownNight : public UObject
{
	GENERATED_BODY()

public:
	/** Apply day (false) or night (true) to the world. Returns how many lights were touched, -1 when the parameter collection is missing. */
	int32 Apply(UWorld* World, bool bNight);
	bool IsNight() const { return bNight; }

private:
	bool bNight = false;
	struct FDayLight { float Intensity = 0.f; FLinearColor Color = FLinearColor::White; };
	TMap<FString, FDayLight> Day;
};
