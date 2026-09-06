#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "StacktownCitySync.generated.h"

class UStacktownEconomy;

/**
 * The world side of the city in C++ (Docs/STATE_HANDOVER.md). Keeps one actor
 * per parcel in the state, posed by StacktownLotTransform and dressed by
 * UStacktownLotVisual; identities live in this subsystem's map, never in actor
 * labels (editor-only). When the Python drivers are off it OWNS the city: it
 * loads the session's state file (migrating the Python-written one into
 * Saved/Stacktown once), ticks the economy every two seconds, saves, and
 * reconciles. When the Python drivers are on it does nothing on its own;
 * Reconcile() can still be called for the agreement checks.
 */
UCLASS()
class STACKTOWNALPHA_API UStacktownCitySync : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Deinitialize() override;

	/** True when the Python drivers are off and this subsystem owns the state. */
	bool OwnsCity() const { return bOwnsCity; }

	/** Spawn, update and remove lot actors to match the economy's state. Returns a one-line report. */
	FString Reconcile(bool bHideBlueprintLots);

	/** The Python-drivers switch: STACKTOWN_PYTHON_DRIVERS in the environment wins,
	 *  then [/Script/StacktownAlpha.StacktownRuntime] bPythonDrivers in the game ini, default true. */
	static bool PythonDriversEnabled();

	/** The economy's tick period the Python driver used (init_unreal._TICK_INTERVAL_S). */
	static constexpr float TickIntervalSeconds = 2.0f;

	int32 NumLots() const { return Lots.Num(); }
	/** The parcel id a spawned lot actor stands for, or empty. */
	FString PidForActor(const AActor* Actor) const;
	AActor* ActorForPid(const FString& Pid) const;

private:
	bool bOwnsCity = false;
	float TickAccum = 0.f;
	FTimerHandle Timer;
	UPROPERTY() TMap<FString, TObjectPtr<AActor>> Lots;
	TMap<FString, FString> Signatures;
	bool bBlueprintLotsHidden = false;

	UStacktownEconomy* Economy() const;
	void OnTimer();
	void HideBlueprintLots();
	bool BeginOwning(FString& OutWhy);
};
