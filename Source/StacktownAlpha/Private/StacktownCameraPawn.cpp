#include "StacktownCameraPawn.h"
#include "StacktownAlpha.h"
#include "Camera/CameraComponent.h"
#include "Components/SceneComponent.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"

using namespace Stacktown::Camera;

AStacktownCameraPawn::AStacktownCameraPawn()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;
	bUseControllerRotationPitch = false;
	bUseControllerRotationYaw = false;
	bUseControllerRotationRoll = false;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(Root);
	Camera->bUsePawnControlRotation = false;
	Camera->SetConstraintAspectRatio(false);
}

FLimits AStacktownCameraPawn::Limits() const
{
	FLimits L;
	L.MinDistance = MinDistance; L.MaxDistance = MaxDistance;
	L.MinPitch = MinPitch; L.MaxPitch = MaxPitch;
	L.FocalWide = FocalWide; L.FocalClose = FocalClose;
	return L;
}

FBounds2D AStacktownCameraPawn::Bounds() const
{
	FBounds2D B;
	B.MinX = BoardMin.X; B.MaxX = BoardMax.X; B.MinY = BoardMin.Y; B.MaxY = BoardMax.Y;
	return B;
}

void AStacktownCameraPawn::BeginPlay()
{
	Super::BeginPlay();
	// The board's footprint is the pan clamp; TC_Board is the plate actor.
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		if (It->GetActorNameOrLabel() == TEXT("TC_Board"))
		{
			FVector Origin, Extent;
			It->GetActorBounds(false, Origin, Extent);
			BoardMin = FVector2D(Origin.X - Extent.X, Origin.Y - Extent.Y);
			BoardMax = FVector2D(Origin.X + Extent.X, Origin.Y + Extent.Y);
			TargetFocus = FVector(Origin.X, Origin.Y, 0.0);
			break;
		}
	}
	// The selection outline belongs to the renderer (design lane, 2026-09-06 16:02): the
	// selected lot writes custom depth, and this post-process material draws a
	// screen-constant outline in accept #C08A4E from it. The material is the design
	// lane's to author; until it exists the camera runs without it and says so once.
	if (UMaterialInterface* Outline = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Stacktown/Materials/M_PP_Outline.M_PP_Outline")))
	{
		Camera->PostProcessSettings.AddBlendable(Outline, 1.f);
		UE_LOG(LogStacktown, Log, TEXT("StacktownCameraPawn: selection outline M_PP_Outline blended"));
	}
	else
	{
		UE_LOG(LogStacktown, Log, TEXT("StacktownCameraPawn: no M_PP_Outline yet - selection has no outline"));
	}
	// THE ARRIVAL (design lane, 2026-09-06 20:06): the board whole in frame, one rung in
	// from the wide end (~14,500), three-quarter so the starter roads run diagonal
	// (yaw 35), pitch 42 so the plate's thick edge and shadow show, and STATIC.
	TargetYaw = 35.0; TargetPitch = -42.0; TargetDistance = 14500.0;   // pitch is negative looking down in this model
	SnapToTargets();
	UE_LOG(LogStacktown, Log, TEXT("StacktownCameraPawn: focus (%.0f, %.0f) yaw %.1f pitch %.1f distance %.0f board x[%.0f..%.0f] y[%.0f..%.0f]"),
		Focus.X, Focus.Y, Yaw, Pitch, Distance, BoardMin.X, BoardMax.X, BoardMin.Y, BoardMax.Y);
}

void AStacktownCameraPawn::Orbit(double DeltaYawDeg, double DeltaPitchDeg)
{
	TargetYaw = FRotator::NormalizeAxis(TargetYaw + DeltaYawDeg);
	TargetPitch = ClampPitch(TargetPitch + DeltaPitchDeg, Limits());
}

void AStacktownCameraPawn::ZoomToward(const FVector& BoardPoint, int32 Notches)
{
	if (Notches == 0)
	{
		return;
	}
	const double Factor = FMath::Pow(ZoomStepFactor, (double)Notches);
	Stacktown::Camera::ZoomToward(BoardPoint, Factor, Limits(), Bounds(), TargetFocus, TargetDistance);
}

void AStacktownCameraPawn::Pan(FVector2D ScreenDirection, float DeltaSeconds)
{
	if (ScreenDirection.IsNearlyZero() || DeltaSeconds <= 0.f)
	{
		return;
	}
	ScreenDirection = ScreenDirection.GetSafeNormal();
	FVector Forward, Right;
	PanBasis(TargetYaw, Forward, Right);
	const double Width = ViewWidthAtFocus(TargetDistance, FovForFocal(FocalForDistance(TargetDistance, Limits())));
	const double Step = Width * PanViewWidthsPerSecond * DeltaSeconds;
	TargetFocus = ClampFocus(TargetFocus + (Forward * ScreenDirection.Y + Right * ScreenDirection.X) * Step, Bounds());
}

void AStacktownCameraPawn::SnapToTargets()
{
	TargetPitch = ClampPitch(TargetPitch, Limits());
	TargetDistance = ClampDistance(TargetDistance, Limits());
	TargetFocus = ClampFocus(TargetFocus, Bounds());
	Focus = TargetFocus; Yaw = TargetYaw; Pitch = TargetPitch; Distance = TargetDistance;
	ApplyPose();
}

double AStacktownCameraPawn::GetFocalMm() const
{
	return FocalForDistance(Distance, Limits());
}

double AStacktownCameraPawn::GetFovDeg() const
{
	return FovForFocal(GetFocalMm());
}

void AStacktownCameraPawn::ApplyPose()
{
	const FRotator Rot = RotationForPose(Yaw, Pitch);
	SetActorLocationAndRotation(LocationForPose(Focus, Yaw, Pitch, Distance), Rot, false, nullptr, ETeleportType::TeleportPhysics);
	if (Camera)
	{
		Camera->SetFieldOfView((float)GetFovDeg());
	}
}

void AStacktownCameraPawn::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float A = FMath::Clamp(EaseSpeed * DeltaSeconds, 0.0, 1.0);
	Focus = FMath::Lerp(Focus, TargetFocus, A);
	Yaw = FRotator::NormalizeAxis(Yaw + FRotator::NormalizeAxis(TargetYaw - Yaw) * A);
	Pitch = FMath::Lerp(Pitch, TargetPitch, A);
	Distance = FMath::Lerp(Distance, TargetDistance, A);
	ApplyPose();
}
