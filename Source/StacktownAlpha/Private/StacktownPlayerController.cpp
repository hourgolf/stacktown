#include "StacktownPlayerController.h"
#include "StacktownAlpha.h"
#include "StacktownCameraPawn.h"
#include "StacktownCameraModel.h"
#include "StacktownHud.h"
#include "Blueprint/GameViewportSubsystem.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Components/Widget.h"
#include "Components/PanelWidget.h"
#include "Engine/GameInstance.h"
#include "Engine/Engine.h"
#include "Components/InputComponent.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/InputSettings.h"

AStacktownPlayerController::AStacktownPlayerController()
{
	bShowMouseCursor = true;
	bEnableClickEvents = true;
	bEnableMouseOverEvents = true;
	PrimaryActorTick.bCanEverTick = true;
}

void AStacktownPlayerController::BeginPlay()
{
	Super::BeginPlay();
	FInputModeGameAndUI Mode;
	Mode.SetHideCursorDuringCapture(false);
	Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	SetInputMode(Mode);
	bShowMouseCursor = true;
	BuildHud();
}

void AStacktownPlayerController::BuildHud()
{
	HudModel = NewObject<UStacktownHudModel>(this, TEXT("HudModel"));
	Hud = NewObject<UStacktownHud>(this, TEXT("Hud"));
	Hud->Build(GetWorld());
}

void AStacktownPlayerController::ReadEconomyIntoModel()
{
	// Until the C++ economy owns the facts, money and demand are the Blueprint
	// game instance's variables, written by the Python driver every sync.
	UGameInstance* GI = GetGameInstance();
	if (!GI || !HudModel)
	{
		return;
	}
	auto ReadNumber = [GI](const TCHAR* Name, double& Out)
	{
		if (FProperty* P = GI->GetClass()->FindPropertyByName(Name))
		{
			if (FNumericProperty* NP = CastField<FNumericProperty>(P))
			{
				if (NP->IsFloatingPoint())
				{
					Out = NP->GetFloatingPointPropertyValue(P->ContainerPtrToValuePtr<void>(GI));
				}
				else if (NP->IsInteger())
				{
					Out = (double)NP->GetSignedIntPropertyValue(P->ContainerPtrToValuePtr<void>(GI));
				}
			}
		}
	};
	ReadNumber(TEXT("Money"), HudModel->Money);
	ReadNumber(TEXT("Demand"), HudModel->Demand);
}

void AStacktownPlayerController::RetireRigBar(AActor* Rig)
{
	// The rig's BeginPlay built its own top bar and kept its text blocks in
	// variables; walk up from MoneyText to the root widget and remove it, so
	// the C++ bar is the only one on screen.
	if (!Rig)
	{
		return;
	}
	FObjectProperty* P = CastField<FObjectProperty>(Rig->GetClass()->FindPropertyByName(TEXT("MoneyText")));
	if (!P)
	{
		return;
	}
	UWidget* W = Cast<UWidget>(P->GetObjectPropertyValue_InContainer(Rig));
	while (W && W->GetParent())
	{
		W = W->GetParent();
	}
	if (W)
	{
		if (UGameViewportSubsystem* VS = GEngine ? GEngine->GetEngineSubsystem<UGameViewportSubsystem>() : nullptr)
		{
			VS->RemoveWidget(W);
			UE_LOG(LogStacktown, Log, TEXT("StacktownPlayerController: removed the rig's bar (%s)"), *W->GetName());
		}
	}
}

void AStacktownPlayerController::ApplyHud()
{
	if (!Hud || !HudModel || !Hud->IsBuilt())
	{
		return;
	}
	float MX = 0.f, MY = 0.f;
	const bool bCursor = GetMousePosition(MX, MY);
	const float Scale = UWidgetLayoutLibrary::GetViewportScale(GetWorld());
	Hud->Apply(HudModel, FVector2D(MX, MY) / FMath::Max(Scale, 0.01f), bCursor);
}

void AStacktownPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();
	if (InputComponent)
	{
		// Wheel notches arrive as key presses; they are queued and spent on the
		// next PlayerTick against the board point under the cursor.
		InputComponent->BindKey(EKeys::MouseScrollUp, IE_Pressed, this, &AStacktownPlayerController::OnWheelUp);
		InputComponent->BindKey(EKeys::MouseScrollDown, IE_Pressed, this, &AStacktownPlayerController::OnWheelDown);
	}
}

void AStacktownPlayerController::OnWheelUp() { ++PendingWheelNotches; }
void AStacktownPlayerController::OnWheelDown() { --PendingWheelNotches; }

AStacktownCameraPawn* AStacktownPlayerController::GetCameraPawn() const
{
	return Cast<AStacktownCameraPawn>(GetPawn());
}

bool AStacktownPlayerController::BoardPointUnderCursor(FVector& OutPoint) const
{
	FVector Origin, Dir;
	if (!DeprojectMousePositionToWorld(Origin, Dir))
	{
		return false;
	}
	return Stacktown::Camera::IntersectBoardPlane(Origin, Dir, OutPoint);
}

void AStacktownPlayerController::EnsureCameraPossessed()
{
	if (GetCameraPawn())
	{
		if (!bPossessionSettled)
		{
			bPossessionSettled = true;
			UE_LOG(LogStacktown, Log, TEXT("StacktownPlayerController: possessing %s"), *GetPawn()->GetName());
		}
		return;
	}
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	AStacktownCameraPawn* Found = nullptr;
	if (TActorIterator<AStacktownCameraPawn> It(World); It)
	{
		Found = *It;
	}
	if (!Found)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Found = World->SpawnActor<AStacktownCameraPawn>(AStacktownCameraPawn::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, Params);
		UE_LOG(LogStacktown, Log, TEXT("StacktownPlayerController: spawned the camera pawn"));
	}
	if (Found && GetPawn() != Found)
	{
		Possess(Found);
		SetViewTarget(Found);
	}
}

void AStacktownPlayerController::FreezeRigs()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	for (TActorIterator<APawn> It(World); It; ++It)
	{
		APawn* P = *It;
		if (P == GetPawn() || P->IsA<AStacktownCameraPawn>())
		{
			continue;
		}
		if (P->GetClass()->GetName().StartsWith(TEXT("BP_LensRig")) && !FrozenRigs.Contains(P))
		{
			P->SetActorTickEnabled(false);
			FrozenRigs.Add(P);
			UE_LOG(LogStacktown, Log, TEXT("StacktownPlayerController: froze %s (retired rig: tick off)"), *P->GetName());
			if (Hud && Hud->IsBuilt())
			{
				RetireRigBar(P);
				bRigBarRetired = true;
			}
		}
	}
}

void AStacktownPlayerController::PumpRigHud(float DeltaTime)
{
	if (bRigBarRetired)
	{
		return;
	}
	RigHudAccum += DeltaTime;
	if (RigHudAccum < RigHudInterval)
	{
		return;
	}
	RigHudAccum = 0.f;
	for (AActor* Rig : FrozenRigs)
	{
		if (!IsValid(Rig))
		{
			continue;
		}
		if (UFunction* Fn = Rig->FindFunction(TEXT("UpdateHUD")))
		{
			if (Fn->NumParms == 0)
			{
				Rig->ProcessEvent(Fn, nullptr);
			}
		}
	}
}

void AStacktownPlayerController::DriveCamera(float DeltaTime)
{
	AStacktownCameraPawn* Cam = GetCameraPawn();
	if (!Cam)
	{
		return;
	}

	// Right-drag: orbit.
	if (IsInputKeyDown(EKeys::RightMouseButton))
	{
		float DX = 0.f, DY = 0.f;
		GetInputMouseDelta(DX, DY);
		if (DX != 0.f || DY != 0.f)
		{
			// dragging right turns the camera around the focus to the right; dragging up tilts down
			Cam->Orbit(-DX * Cam->OrbitDegPerPixel, DY * Cam->OrbitDegPerPixel);
		}
	}

	// Wheel: zoom toward the board point under the cursor (or the focus when off-board).
	if (PendingWheelNotches != 0)
	{
		FVector Point;
		if (!BoardPointUnderCursor(Point))
		{
			Point = Cam->TargetFocus;
		}
		Cam->ZoomToward(Point, PendingWheelNotches);
		PendingWheelNotches = 0;
	}

	// Pan: arrow keys, and the screen edges while the cursor is inside the viewport.
	FVector2D Dir(0.0, 0.0);
	if (IsInputKeyDown(EKeys::Left))  { Dir.X -= 1.0; }
	if (IsInputKeyDown(EKeys::Right)) { Dir.X += 1.0; }
	if (IsInputKeyDown(EKeys::Up))    { Dir.Y += 1.0; }
	if (IsInputKeyDown(EKeys::Down))  { Dir.Y -= 1.0; }
	if (bEdgePan && !IsInputKeyDown(EKeys::RightMouseButton))
	{
		float MX = 0.f, MY = 0.f;
		int32 VX = 0, VY = 0;
		GetViewportSize(VX, VY);
		if (VX > 0 && VY > 0 && GetMousePosition(MX, MY) && MX >= 0.f && MY >= 0.f && MX <= VX && MY <= VY)
		{
			if (MX <= EdgePanPixels)        { Dir.X -= 1.0; }
			if (MX >= VX - EdgePanPixels)   { Dir.X += 1.0; }
			if (MY <= EdgePanPixels)        { Dir.Y += 1.0; }
			if (MY >= VY - EdgePanPixels)   { Dir.Y -= 1.0; }
		}
	}
	if (!Dir.IsNearlyZero())
	{
		Cam->Pan(Dir, DeltaTime);
	}
}

void AStacktownPlayerController::PlayerTick(float DeltaTime)
{
	Super::PlayerTick(DeltaTime);
	EnsureCameraPossessed();
	FreezeRigs();
	PumpRigHud(DeltaTime);
	DriveCamera(DeltaTime);
	ReadEconomyIntoModel();
	ApplyHud();
}
