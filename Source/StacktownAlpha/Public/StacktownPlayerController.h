#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "StacktownPlayerController.generated.h"

class AStacktownCameraPawn;
class UStacktownHudModel;
class UStacktownHud;
class UStacktownNight;

/**
 * Drives AStacktownCameraPawn from raw input (right-drag orbit, wheel zoom
 * toward the cursor, screen-edge and arrow-key pan) and takes possession back
 * from the retired BP_LensRig, whose placed instance still auto-possesses the
 * player at its BeginPlay. The rig's tick is frozen so its old key handling
 * (including the instant N reset) can never fire again; its BeginPlay-built
 * top bar is kept alive by calling its UpdateHUD through reflection.
 */
UCLASS()
class STACKTOWNALPHA_API AStacktownPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	AStacktownPlayerController();

	/** Pixels from the viewport edge that start an edge pan. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera")
	float EdgePanPixels = 14.f;
	/** Seconds between UpdateHUD calls on the frozen rig. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera")
	float RigHudInterval = 0.25f;
	/** Set false to leave the mouse to the widgets (edge pan off). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera")
	bool bEdgePan = true;

	UFUNCTION(BlueprintPure, Category = "Stacktown|Camera")
	AStacktownCameraPawn* GetCameraPawn() const;

	/** The HUD's facts; the Python drivers write it today, C++ later. */
	UFUNCTION(BlueprintPure, Category = "Stacktown|HUD")
	UStacktownHudModel* GetHudModel() const { return HudModel; }

	/** The board point under the cursor, or false when the cursor is off the board plane. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Camera")
	bool BoardPointUnderCursor(FVector& OutPoint) const;

	virtual void BeginPlay() override;
	virtual void PlayerTick(float DeltaTime) override;
	virtual void SetupInputComponent() override;

	// ---- the C++ input port (active only while the city sync owns the city) ----
	/** Place a lot at a board point with the current width; returns the outcome line. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|City")
	FString CityPlaceAt(double X, double Y);
	UFUNCTION(BlueprintCallable, Category = "Stacktown|City")
	FString CitySelect(const FString& Pid);
	/** "B", "U" or "H" on the selected lot; returns the outcome line. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|City")
	FString CityVerb(const FString& Key);
	UFUNCTION(BlueprintCallable, Category = "Stacktown|City")
	FString CityCycleWidth(int32 Step);
	UFUNCTION(BlueprintCallable, Category = "Stacktown|City")
	FString CityReset();
	/** GAME START: BOTH (owner, 2026-09-01). On a fresh city, seed the 14-lot starter preset
	 *  as for-sale lots at their pinned poses (the engineering seat's SeedPresetState). */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|City")
	FString CityPreset();
	UFUNCTION(BlueprintPure, Category = "Stacktown|City")
	double CurrentLotWidth() const;
	/** Road mode on/off (G). */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|City")
	FString CityRoadMode(bool bOn);
	/** A click in road mode: the first sets the start, the second draws; returns the outcome line. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|City")
	FString CityRoadClick(double X, double Y);
	/** Cycle the road class drawn next; returns the new class. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|City")
	FString CityCycleRoadClass();
	/** Cycle the recipe of the next placed lot; returns the new recipe. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|City")
	FString CityCycleRecipe();
	/** Night on/off (L). */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|City")
	FString CityNight(bool bOn);

private:
	void EnsureCameraPossessed();
	void FreezeRigs();
	void PumpRigHud(float DeltaTime);
	void DriveCamera(float DeltaTime);
	void BuildHud();
	void ReadEconomyIntoModel();
	void RetireRigBar(AActor* Rig);
	void ApplyHud();
	void DriveCity(float DeltaTime);
	void HoverGhost(const FVector& BoardPoint, bool bOverLot);
	void HideGhost();
	void RefreshSelection();
	void SetSelectionHighlight(const FString& Pid, bool bOn);
	bool CityOwned() const;
	static FString ClassifyPlaceRefusal(const FString& Reason);
	static FString ClassifyActionRefusal(const FString& Reason);
	static FString ClassifyRoadRefusal(const FString& Reason);
	void RoadGhost(const FVector& BoardPoint);
	void HideRoadGhost();

	bool bRoadMode = false;
	bool bRoadStartSet = false;
	FVector2D RoadStart = FVector2D::ZeroVector;
	UPROPERTY() TObjectPtr<AActor> RoadGhostActor;
	UPROPERTY() TObjectPtr<UStacktownNight> Night;

	int32 WidthIndex = 0;
	FString SelectedPid;
	UPROPERTY() TObjectPtr<AActor> Ghost;
	FVector LastHoverPoint = FVector(1e9, 1e9, 0.0);
	/** Placeholder sound cues (MONDAY_DECISIONS section 5): wood taps in /Game/Stacktown/Audio,
	 *  loaded by path once and cached; a missing asset plays nothing and logs once. */
	void PlayCue(const TCHAR* Name);
	TMap<FString, TObjectPtr<class USoundBase>> Cues;
	TSet<FString> CuesMissing;
	/** A bar message that holds for a minimum time (LOOK 4: an announcement, 3 s or the next input, whichever is longer). */
	FString PinnedBarMessage;
	double PinnedBarUntil = 0.0;
	/** The recipe of the next placed lot (vernacular | office | tower); R cycles it. */
	FString NextRecipe = TEXT("vernacular");
	/** The road class drawn next (dirt | avenue | boulevard | highway); T cycles it in road mode. */
	FString RoadClass = TEXT("avenue");
	/** Goal ladder rungs announced this session; -1 until the first owning tick (a loaded city is not re-announced). */
	int32 GoalsAnnounced = -1;
	/** The fresh-city hint is on the bar (cleared when the first lot exists). */
	bool bHintShowing = false;
	float NHeld = 0.f;
	bool bNFired = false;
	bool bRefusalShowing = false;

	UPROPERTY() TObjectPtr<UStacktownHudModel> HudModel;
	UPROPERTY() TObjectPtr<UStacktownHud> Hud;
	bool bRigBarRetired = false;
	void OnWheelUp();
	void OnWheelDown();

	UPROPERTY()
	TArray<TObjectPtr<AActor>> FrozenRigs;
	float RigHudAccum = 0.f;
	int32 PendingWheelNotches = 0;
	bool bPossessionSettled = false;
};
