#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "StacktownCameraModel.h"
#include "StacktownCameraPawn.generated.h"

class UCameraComponent;
class USceneComponent;

/**
 * The Stacktown camera (owner's word 2026-09-05, PLAN_CPP_PORT.md §6):
 * right-drag orbits, the wheel zooms toward the cursor, screen edges and
 * arrow keys pan. Targets ease; the pose arithmetic is in
 * StacktownCameraModel.h. Replaces BP_LensRig, which is retired.
 */
UCLASS()
class STACKTOWNALPHA_API AStacktownCameraPawn : public APawn
{
	GENERATED_BODY()

public:
	AStacktownCameraPawn();

	// ---- pose (current, eased) ----
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Stacktown|Camera")
	FVector Focus = FVector::ZeroVector;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Stacktown|Camera")
	double Yaw = 70.0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Stacktown|Camera")
	double Pitch = -25.3;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Stacktown|Camera")
	double Distance = 21024.0;

	// ---- targets (what input writes) ----
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera")
	FVector TargetFocus = FVector::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera")
	double TargetYaw = 70.0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera")
	double TargetPitch = -25.3;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera")
	double TargetDistance = 21024.0;

	// ---- tuning ----
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera|Tuning")
	double MinDistance = 1200.0;
	/** The arrival distance is also the wide limit, so the arrival lens is the rig's 24 mm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera|Tuning")
	double MaxDistance = 21024.0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera|Tuning")
	double MinPitch = -85.0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera|Tuning")
	double MaxPitch = -8.0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera|Tuning")
	double FocalWide = 24.0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera|Tuning")
	double FocalClose = 200.0;
	/** Degrees of yaw per pixel of right-drag. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera|Tuning")
	double OrbitDegPerPixel = 0.25;
	/** Distance multiplier per wheel notch toward the cursor (< 1 closes in). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera|Tuning")
	double ZoomStepFactor = 0.82;
	/** Pan speed as a fraction of the visible board width per second. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera|Tuning")
	double PanViewWidthsPerSecond = 0.6;
	/** Easing speed for focus, angles and distance. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera|Tuning")
	double EaseSpeed = 8.0;
	/** Board extent the focus is clamped to; filled from TC_Board at BeginPlay when found. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera|Tuning")
	FVector2D BoardMin = FVector2D(-7650.0, -4230.0);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Camera|Tuning")
	FVector2D BoardMax = FVector2D(7650.0, 4230.0);

	// ---- verbs the controller (and Python, headless) call ----
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Camera")
	void Orbit(double DeltaYawDeg, double DeltaPitchDeg);
	/** Instruments only: set the whole view at once (focus, yaw, pitch, distance) and snap, so a
	 *  probe's frame is a stated pose rather than a zoom ladder's outcome. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Camera")
	void SetView(FVector InFocus, double InYaw, double InPitch, double InDistance);

	/** Zoom by Notches (positive closes in) toward a board point. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Camera")
	void ZoomToward(const FVector& BoardPoint, int32 Notches);

	/** Pan by a screen-space direction (x right, y up, each -1..1) for DeltaSeconds. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Camera")
	void Pan(FVector2D ScreenDirection, float DeltaSeconds);

	/** Jump the current pose to the targets (no easing). */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Camera")
	void SnapToTargets();

	UFUNCTION(BlueprintPure, Category = "Stacktown|Camera")
	double GetFocalMm() const;

	UFUNCTION(BlueprintPure, Category = "Stacktown|Camera")
	double GetFovDeg() const;

	Stacktown::Camera::FLimits Limits() const;
	Stacktown::Camera::FBounds2D Bounds() const;

	virtual void Tick(float DeltaSeconds) override;
	virtual void BeginPlay() override;

private:
	UPROPERTY(VisibleAnywhere, Category = "Stacktown|Camera")
	TObjectPtr<USceneComponent> Root;
	UPROPERTY(VisibleAnywhere, Category = "Stacktown|Camera")
	TObjectPtr<UCameraComponent> Camera;

	void ApplyPose();
};
