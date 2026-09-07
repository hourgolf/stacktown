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

	/** SAVE SLOTS: the open slot (1-3) and the switch. The city being left is
	 *  saved first, the choice is remembered beside the saves (slot.txt), a slot
	 *  never written opens as a fresh board. False, with the reason, when the
	 *  slot is already open or this subsystem does not own the city. */
	int32 GetSlot() const { return Slot; }
	bool SwitchSlot(int32 NewSlot, FString& OutReport);

	/** The Python-drivers switch: STACKTOWN_PYTHON_DRIVERS in the environment wins,
	 *  then [/Script/StacktownAlpha.StacktownRuntime] bPythonDrivers in the game ini, default true. */
	static bool PythonDriversEnabled();

	/** The economy's tick period the Python driver used (init_unreal._TICK_INTERVAL_S). */
	static constexpr float TickIntervalSeconds = 2.0f;

	int32 NumLots() const { return Lots.Num(); }

	/** Docs/TRADE_ADAPTER.md section 5: the adapter appends one JSON line per
	 *  CLOSED trade here; the game reads it and applies rewards idempotently. */
	static FString TradeLedgerPath();
	/** Read the ledger now and apply any new trades; returns a report line. */
	FString ReadTradeLedger();
	/** The last reward line for the HUD bar (empty when nothing happened this read). */
	FString LastTradeMessage;
	int32 NumRoads() const { return RoadActors.Num(); }
	/** The parcel id a spawned lot actor stands for, or empty. */
	FString PidForActor(const AActor* Actor) const;
	AActor* ActorForPid(const FString& Pid) const;

private:
	bool bOwnsCity = false;
	int32 Slot = 1;
	/** The slot-1 owned file; slots 2 and 3 are Stacktown::SlotStatePath of it. */
	FString OwnedBase;
	FString SlotFilePath() const;
	float TickAccum = 0.f;
	FTimerHandle Timer;
	UPROPERTY() TMap<FString, TObjectPtr<AActor>> Lots;
	UPROPERTY() TMap<FString, TObjectPtr<AActor>> RoadActors;
	TMap<FString, FString> RoadSignatures;
	TMap<FString, FString> Signatures;
	bool bBlueprintLotsHidden = false;
	int32 LedgerLinesSeen = 0;

	UStacktownEconomy* Economy() const;
	void OnTimer();
	void HideBlueprintLots();
	bool BeginOwning(FString& OutWhy);
};
