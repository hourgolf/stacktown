#include "StacktownPlayerController.h"
#include "StacktownAlpha.h"
#include "StacktownCameraPawn.h"
#include "StacktownCameraModel.h"
#include "StacktownHud.h"
#include "StacktownCitySync.h"
#include "StacktownScore.h"
#include "StacktownEconomy.h"
#include "StacktownEconomyRules.h"
#include "StacktownPlacement.h"
#include "StacktownWorldBoard.h"
#include "StacktownLotTransform.h"
#include "StacktownLotVisual.h"
#include "StacktownCatalogue.h"
#include "StacktownWoodCatalogue.h"
#include "Components/SceneComponent.h"
#include "StacktownRoad.h"
#include "StacktownNight.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
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
	// A Development build prints engine notices ("Preparing SoundWaves") over the board; a stranger must never see them.
	GAreScreenMessagesEnabled = false;   // the console route ran before the viewport existed (frame 20:20 still showed the notice)
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
	if (UStacktownCitySync* Sync = GetWorld() ? GetWorld()->GetSubsystem<UStacktownCitySync>() : nullptr)
	{
		if (Sync->OwnsCity())
		{
			if (UStacktownEconomy* Econ = GI->GetSubsystem<UStacktownEconomy>())
			{
				HudModel->Money = Econ->GetState().Money;
				HudModel->Demand = Econ->GetState().Demand;
				HudModel->Score = Stacktown::Score(Econ->GetRules(), Econ->GetState());   // proposed; see StacktownScore.h
			}
			return;
		}
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
	DriveCity(DeltaTime);
	ApplyHud();
}

// ---------------------------------------------------------------------------
// The C++ input port: what Content/Python/clickdriver.py did, against the
// city sync. Active only while the sync owns the city (Python drivers off);
// otherwise the Python driver keeps the clicks and this does nothing.
// ---------------------------------------------------------------------------

namespace
{
	const double GWidths[5] = { 820.0, 1230.0, 1640.0, 2050.0, 2460.0 };
	constexpr float ResetHoldSeconds = 2.0f;

	bool PinsActive(const UGameInstance* GI)
	{
		if (!GI) { return true; }
		if (FBoolProperty* BP = CastField<FBoolProperty>(GI->GetClass()->FindPropertyByName(TEXT("EmptyStart"))))
		{
			return !BP->GetPropertyValue_InContainer(GI);
		}
		return true;
	}
}

bool AStacktownPlayerController::CityOwned() const
{
	const UStacktownCitySync* Sync = GetWorld() ? GetWorld()->GetSubsystem<UStacktownCitySync>() : nullptr;
	return Sync && Sync->OwnsCity();
}

double AStacktownPlayerController::CurrentLotWidth() const
{
	return GWidths[FMath::Clamp(WidthIndex, 0, 4)];
}

FString AStacktownPlayerController::ClassifyPlaceRefusal(const FString& R)
{
	// init_unreal._place_refusal_message, verbatim (Docs/HUD_V1.md CONTENT 2)
	if (R.StartsWith(TEXT("off-board"))) { return TEXT("Off the board"); }
	if (R.Contains(TEXT("crosses a pinned lot"))) { return TEXT("That's part of the starter city"); }
	if (R.Contains(TEXT("crosses an existing lot"))) { return TEXT("Already built there"); }
	if (R.StartsWith(TEXT("pool exhausted"))) { return TEXT("No more lots available"); }
	if (R.StartsWith(TEXT("in the road"))) { return TEXT("That's the road - click the block beside it"); }
	if (R.StartsWith(TEXT("too far from a road"))) { return TEXT("Too far from a road"); }
	if (R.Contains(TEXT("crossing"))) { return TEXT("That's the crossing - pick one road's frontage"); }
	return TEXT("Can't build here");
}

FString AStacktownPlayerController::ClassifyActionRefusal(const FString& R)
{
	return R.Contains(TEXT("insufficient funds")) ? TEXT("Can't afford it") : TEXT("Can't do that right now");
}

void AStacktownPlayerController::HideGhost()
{
	if (Ghost) { Ghost->SetActorHiddenInGame(true); }
	if (HudModel && !HudModel->PlaceRefusal.IsEmpty()) { HudModel->PlaceRefusal.Reset(); }
}

void AStacktownPlayerController::HoverGhost(const FVector& BoardPoint, bool bOverLot)
{
	if (bOverLot) { HideGhost(); LastHoverPoint = FVector(1e9, 1e9, 0.0); return; }
	if (FVector::Dist2D(BoardPoint, LastHoverPoint) < 20.0) { return; }
	LastHoverPoint = BoardPoint;
	UStacktownEconomy* Econ = GetGameInstance() ? GetGameInstance()->GetSubsystem<UStacktownEconomy>() : nullptr;
	if (!Econ) { return; }
	const Stacktown::FPlacementBoard Board = Stacktown::TemporaryBoard();
	const Stacktown::FClickResult R = Stacktown::ResolveClick(Board, Econ->GetState(), BoardPoint.X, BoardPoint.Y, (!CityOwned() && PinsActive(GetGameInstance())), CurrentLotWidth());
	if (!R.bOk)
	{
		if (Ghost) { Ghost->SetActorHiddenInGame(true); }
		if (HudModel) { HudModel->PlaceRefusal = ClassifyPlaceRefusal(R.Reason); }
		return;
	}
	if (HudModel) { HudModel->PlaceRefusal.Reset(); }
	Stacktown::LotFrame::FPose Pose;
	if (!Stacktown::LotFrame::Pose(R.Lot, Board.AllRoads(Econ->GetState()), Pose)) { return; }
	if (!Ghost)
	{
		FActorSpawnParameters Params; Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Ghost = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, Params);
		USceneComponent* Root = NewObject<USceneComponent>(Ghost, TEXT("Root")); Ghost->SetRootComponent(Root); Root->RegisterComponent();
		UStacktownLotVisual* V = NewObject<UStacktownLotVisual>(Ghost, TEXT("Pad")); V->AttachToComponent(Root, FAttachmentTransformRules::KeepRelativeTransform); V->RegisterComponent();
		V->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	}
	Ghost->SetActorLocationAndRotation(FVector(Pose.X, Pose.Y, 2.0), FRotator(0.0, Pose.Yaw, 0.0));
	if (UStacktownLotVisual* V = Ghost->FindComponentByClass<UStacktownLotVisual>())
	{
		FString Err;
		if (!V->ShownAsset.EndsWith(FString::Printf(TEXT("w%d"), (int32)CurrentLotWidth()))) { V->ShowPad(CurrentLotWidth(), Err); }
	}
	Ghost->SetActorHiddenInGame(false);
}

void AStacktownPlayerController::SetSelectionHighlight(const FString& Pid, bool bOn)
{
	UStacktownCitySync* Sync = GetWorld() ? GetWorld()->GetSubsystem<UStacktownCitySync>() : nullptr;
	AActor* A = Sync ? Sync->ActorForPid(Pid) : nullptr;
	if (UStacktownLotVisual* V = A ? A->FindComponentByClass<UStacktownLotVisual>() : nullptr)
	{
		V->SetSelected(bOn);   // cpdmap channel 3 (reserved) + custom depth for the post-process outline
	}
}

void AStacktownPlayerController::RefreshSelection()
{
	if (!HudModel) { return; }
	UStacktownEconomy* Econ = GetGameInstance() ? GetGameInstance()->GetSubsystem<UStacktownEconomy>() : nullptr;
	const Stacktown::FParcelState* P = Econ ? Econ->GetState().Parcels.Find(SelectedPid) : nullptr;
	if (!P)
	{
		HudModel->bHasSelection = false;
		return;
	}
	const Stacktown::FEconRules& R = Econ->GetRules();
	HudModel->bHasSelection = true;
	HudModel->SelectedName = FString::Printf(TEXT("%s %d"), *P->Rid, (int32)P->Width);
	HudModel->Verb.Reset(); HudModel->VerbKey.Reset(); HudModel->VerbPrice = 0.0;
	if (!P->bOwned)
	{
		HudModel->SelectedState = TEXT("FOR SALE");
		HudModel->Verb = TEXT("BUY"); HudModel->VerbKey = TEXT("B"); HudModel->VerbPrice = Stacktown::PriceFor(R, P->Rid, P->Tier, P->Width);
	}
	else if (P->bFailed)
	{
		HudModel->SelectedState = TEXT("NEEDS REPAIR");
		HudModel->Verb = TEXT("REPAIR"); HudModel->VerbKey = TEXT("H"); HudModel->VerbPrice = Stacktown::RepairPrice(R, P->Tier);
	}
	else
	{
		HudModel->SelectedState = FString::Printf(TEXT("OWNED \u00b7 TIER %d"), P->Tier);
		Stacktown::FWoodCatalogue Cat;
		if (Stacktown::TierUpAllowed(Cat, P->Rid, P->Tier, P->Width).bOk)
		{
			HudModel->Verb = TEXT("UPGRADE"); HudModel->VerbKey = TEXT("U"); HudModel->VerbPrice = Stacktown::UpgradePrice(R, P->Tier, P->Performance);
		}
	}
}

FString AStacktownPlayerController::CitySelect(const FString& Pid)
{
	if (!SelectedPid.IsEmpty()) { SetSelectionHighlight(SelectedPid, false); }
	SelectedPid = Pid;
	if (!Pid.IsEmpty()) { SetSelectionHighlight(Pid, true); }
	RefreshSelection();
	return Pid.IsEmpty() ? TEXT("deselected") : FString::Printf(TEXT("selected %s (%s%s)"), *Pid, *HudModel->SelectedState, HudModel->Verb.IsEmpty() ? TEXT("") : *FString::Printf(TEXT(", %s $%.0f"), *HudModel->Verb, HudModel->VerbPrice));
}

FString AStacktownPlayerController::CityPlaceAt(double X, double Y)
{
	UStacktownEconomy* Econ = GetGameInstance() ? GetGameInstance()->GetSubsystem<UStacktownEconomy>() : nullptr;
	UStacktownCitySync* Sync = GetWorld() ? GetWorld()->GetSubsystem<UStacktownCitySync>() : nullptr;
	if (!Econ || !Sync || !Sync->OwnsCity()) { return TEXT("the C++ port is not driving this city"); }
	const Stacktown::FPlaceResult R = Stacktown::Place(Stacktown::TemporaryBoard(), Econ->GetMutableState(), X, Y, (!CityOwned() && PinsActive(GetGameInstance())), CurrentLotWidth());
	if (!R.bOk)
	{
		if (HudModel) { HudModel->PlaceRefusal = ClassifyPlaceRefusal(R.Reason); }
		PlayCue(TEXT("S_Refuse"));
		return FString::Printf(TEXT("place refused: %s -> \"%s\""), *R.Reason, *ClassifyPlaceRefusal(R.Reason));
	}
	Econ->SaveState();
		if (Stacktown::FParcelState* NewLot = Econ->GetMutableState().Parcels.Find(R.Pid)) { NewLot->Rid = NextRecipe; }   // the chosen recipe: species and economy follow
	const FString Rep = Sync->Reconcile(false);
	CitySelect(R.Pid);
	PlayCue(TEXT("S_Place"));
	return FString::Printf(TEXT("placed %s at (%.0f, %.0f) width %.0f; %s"), *R.Pid, X, Y, CurrentLotWidth(), *Rep);
}

FString AStacktownPlayerController::CityVerb(const FString& Key)
{
	UStacktownEconomy* Econ = GetGameInstance() ? GetGameInstance()->GetSubsystem<UStacktownEconomy>() : nullptr;
	UStacktownCitySync* Sync = GetWorld() ? GetWorld()->GetSubsystem<UStacktownCitySync>() : nullptr;
	if (!Econ || !Sync || !Sync->OwnsCity()) { return TEXT("the C++ port is not driving this city"); }
	if (SelectedPid.IsEmpty())
	{
		if (HudModel) { HudModel->ActionRefusal = TEXT("Select a lot first"); bRefusalShowing = true; }
		PlayCue(TEXT("S_Refuse"));
		return TEXT("no selection");
	}
	FString Reason; bool bOk = false; const TCHAR* Verb = TEXT("?");
	if (Key == TEXT("B")) { Verb = TEXT("buy"); bOk = Econ->CityBuy(SelectedPid, Reason); }
	else if (Key == TEXT("U")) { Verb = TEXT("upgrade"); bOk = Econ->CityUpgrade(SelectedPid, Reason); }
	else if (Key == TEXT("H")) { Verb = TEXT("repair"); bOk = Econ->CityRepair(SelectedPid, Reason); }
	else { return FString::Printf(TEXT("unknown verb key %s"), *Key); }
	if (!bOk)
	{
		if (HudModel) { HudModel->ActionRefusal = ClassifyActionRefusal(Reason); bRefusalShowing = true; }
		PlayCue(TEXT("S_Refuse"));
		return FString::Printf(TEXT("%s %s refused: %s -> \"%s\""), Verb, *SelectedPid, *Reason, *ClassifyActionRefusal(Reason));
	}
	Econ->SaveState();
	const FString Rep = Sync->Reconcile(false);
	SetSelectionHighlight(SelectedPid, true);
	RefreshSelection();
	PlayCue(TEXT("S_Place"));   // LOOK 6: the block set down, the same material sound as placing
	return FString::Printf(TEXT("%s %s ok; money %.2f; %s"), Verb, *SelectedPid, Econ->GetState().Money, *Rep);
}

FString AStacktownPlayerController::CityCycleWidth(int32 Step)
{
	WidthIndex = ((WidthIndex + Step) % 5 + 5) % 5;
	LastHoverPoint = FVector(1e9, 1e9, 0.0);
	if (HudModel) { HudModel->BarMessage = FString::Printf(TEXT("%s \u00b7 width %d"), *NextRecipe, (int32)CurrentLotWidth()); }
	return FString::Printf(TEXT("%s width %d"), *NextRecipe, (int32)CurrentLotWidth());
}

FString AStacktownPlayerController::CityReset()
{
	UStacktownEconomy* Econ = GetGameInstance() ? GetGameInstance()->GetSubsystem<UStacktownEconomy>() : nullptr;
	UStacktownCitySync* Sync = GetWorld() ? GetWorld()->GetSubsystem<UStacktownCitySync>() : nullptr;
	if (!Econ || !Sync || !Sync->OwnsCity()) { return TEXT("the C++ port is not driving this city"); }
	CitySelect(FString());
	Econ->ResetCity();
	Econ->SaveState();
	return FString::Printf(TEXT("city reset; money %.2f; %s"), Econ->GetState().Money, *Sync->Reconcile(false));
}

FString AStacktownPlayerController::ClassifyRoadRefusal(const FString& R)
{
	// Docs/HUD_V1.md CONTENT 2, the draw rows plus the shared overlap rows
	if (R.Contains(TEXT("diagonal")) || R.Contains(TEXT("straight"))) { return TEXT("Roads run straight"); }
	if (R.Contains(TEXT("short"))) { return TEXT("Too short for a road"); }
	if (R.Contains(TEXT("cross"))) { return TEXT("Roads can't cross yet"); }
	if (R.StartsWith(TEXT("off-board"))) { return TEXT("Off the board"); }
	if (R.Contains(TEXT("pinned lot"))) { return TEXT("That's part of the starter city"); }
	if (R.Contains(TEXT("existing lot"))) { return TEXT("Already built there"); }
	return TEXT("Can't build here");
}

FString AStacktownPlayerController::CityRoadMode(bool bOn)
{
	bRoadMode = bOn;
	bRoadStartSet = false;
	HideRoadGhost();
	HideGhost();
	if (HudModel)
	{
		HudModel->bRoadMode = bOn;
		HudModel->BarMessage = bOn ? TEXT("click start, click end \u00b7 G to leave") : TEXT("");
	}
	return bOn ? TEXT("road mode on") : TEXT("road mode off");
}

void AStacktownPlayerController::HideRoadGhost()
{
	if (RoadGhostActor) { RoadGhostActor->SetActorHiddenInGame(true); }
}

void AStacktownPlayerController::RoadGhost(const FVector& BoardPoint)
{
	if (!bRoadStartSet) { HideRoadGhost(); return; }
	UStacktownEconomy* Econ = GetGameInstance() ? GetGameInstance()->GetSubsystem<UStacktownEconomy>() : nullptr;
	if (!Econ) { return; }
	const Stacktown::FRoadDrawResult R = Stacktown::ResolveRoadDraw(Stacktown::TemporaryBoard(), Econ->GetState(), RoadStart.X, RoadStart.Y, BoardPoint.X, BoardPoint.Y, RoadClass, (!CityOwned() && PinsActive(GetGameInstance())));
	if (!RoadGhostActor)
	{
		FActorSpawnParameters Params; Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		RoadGhostActor = GetWorld()->SpawnActor<AStacktownRoad>(AStacktownRoad::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, Params);
	}
	if (AStacktownRoad* G = Cast<AStacktownRoad>(RoadGhostActor))
	{
		// the chord as drawn when refused, the validated segment when accepted
		if (R.bOk) { G->ShowSegment(TEXT("ghost"), R.Segment); }
		else { G->Show(TEXT("ghost"), RoadStart.X, RoadStart.Y, BoardPoint.X, BoardPoint.Y); }
		G->SetGhost(true, R.bOk);
		G->SetActorHiddenInGame(false);
	}
	if (HudModel) { HudModel->PlaceRefusal = R.bOk ? FString() : ClassifyRoadRefusal(R.Reason); }
}

FString AStacktownPlayerController::CityRoadClick(double X, double Y)
{
	UStacktownEconomy* Econ = GetGameInstance() ? GetGameInstance()->GetSubsystem<UStacktownEconomy>() : nullptr;
	UStacktownCitySync* Sync = GetWorld() ? GetWorld()->GetSubsystem<UStacktownCitySync>() : nullptr;
	if (!Econ || !Sync || !Sync->OwnsCity()) { return TEXT("the C++ port is not driving this city"); }
	if (!bRoadStartSet)
	{
		bRoadStartSet = true; RoadStart = FVector2D(X, Y);
		if (HudModel) { HudModel->BarMessage = TEXT("road start set \u00b7 click the end"); }
		PlayCue(TEXT("S_Place"));
		return FString::Printf(TEXT("road start (%.0f, %.0f)"), X, Y);
	}
	const Stacktown::FRoadDrawResult R = Stacktown::DrawRoad(Stacktown::TemporaryBoard(), Econ->GetMutableState(), RoadStart.X, RoadStart.Y, X, Y, RoadClass, (!CityOwned() && PinsActive(GetGameInstance())));
	bRoadStartSet = false;
	HideRoadGhost();
	if (!R.bOk)
	{
		if (HudModel) { HudModel->PlaceRefusal = ClassifyRoadRefusal(R.Reason); HudModel->BarMessage = TEXT("click start, click end \u00b7 G to leave"); }
		PlayCue(TEXT("S_Refuse"));
		return FString::Printf(TEXT("road refused: %s -> \"%s\""), *R.Reason, *ClassifyRoadRefusal(R.Reason));
	}
	Econ->SaveState();
	const FString Rep = Sync->Reconcile(false);
	if (HudModel) { HudModel->PlaceRefusal.Reset(); HudModel->BarMessage = TEXT("click start, click end \u00b7 G to leave"); }
	PlayCue(TEXT("S_Place"));
	return FString::Printf(TEXT("road %s drawn (%.0f, %.0f) -> (%.0f, %.0f); %s"), *R.Id, R.Segment.StartX, R.Segment.StartY, R.Segment.EndX, R.Segment.EndY, *Rep);
}

FString AStacktownPlayerController::CityNight(bool bOn)
{
	if (!Night) { Night = NewObject<UStacktownNight>(this, TEXT("Night")); }
	const int32 N = Night->Apply(GetWorld(), bOn);
	if (HudModel) { HudModel->bNight = bOn && N >= 0; }
	return N < 0 ? TEXT("no night yet (parameter collection missing)") : FString::Printf(TEXT("%s, %d lights %s"), bOn ? TEXT("night") : TEXT("day"), N, bOn ? TEXT("dimmed") : TEXT("restored"));
}

void AStacktownPlayerController::DriveCity(float DeltaTime)
{
	if (!CityOwned() || !HudModel) { return; }
	UStacktownCitySync* Sync = GetWorld()->GetSubsystem<UStacktownCitySync>();
	if (!Sync->LastTradeMessage.IsEmpty())
	{
		HudModel->BarMessage = Sync->LastTradeMessage;   // stays until the next input, like every bar message
		Sync->LastTradeMessage.Reset();
	}

	// THE GOAL LADDER (proposed): announce a rung the first time the score crosses it
	// this session. A loaded city's standing rungs are not re-announced.
	if (UStacktownEconomy* EconForGoals = GetGameInstance() ? GetGameInstance()->GetSubsystem<UStacktownEconomy>() : nullptr)
	{
		// Persisted in the city (goals_reached): a reloaded city is not congratulated twice.
		const int32 Goals = Stacktown::GoalsReached(HudModel->Score);
		const int32 Already = EconForGoals->GetState().GoalsReached;
		if (Goals > Already)
		{
			// LOOK 4: "GOAL n REACHED" (the rung, not the amount), label size in accept, and it
			// holds until the next input OR 3 seconds, whichever is longer - an announcement
			// arrives unbidden. No sound: LOOK 6 allows the wood to speak only for placement
			// and refusal.
			PinnedBarMessage = FString::Printf(TEXT("GOAL %d REACHED"), Goals);
			PinnedBarUntil = GetWorld()->GetTimeSeconds() + 3.0;
			HudModel->BarMessage = PinnedBarMessage;
			HudModel->bBarMessageAccent = true;
			EconForGoals->SetGoalsReached(Goals);
		}
		GoalsAnnounced = Goals;
		const TArray<double>& Ladder = Stacktown::GoalLadder();
		HudModel->NextGoal = Goals < Ladder.Num() ? Ladder[Goals] : 0.0;
	}
	// THE FRESH CITY: a stranger's first screen has no lots and no instruction. The
	// hint holds the bar until the first lot exists (wording is the design lane's).
	if (UStacktownEconomy* EconForHint = GetGameInstance() ? GetGameInstance()->GetSubsystem<UStacktownEconomy>() : nullptr)
	{
		const bool bFresh = EconForHint->GetState().Parcels.Num() == 0;
		if (bFresh && !bRoadMode && HudModel->BarMessage.IsEmpty()) { HudModel->BarMessage = TEXT("Click the board to place your first lot, or press P for the starter city."); bHintShowing = true; }   // LOOK 4 wording + the preset offer (BOTH starts)
		else if (!bFresh && bHintShowing) { HudModel->BarMessage.Reset(); bHintShowing = false; }
	}

	if (!PinnedBarMessage.IsEmpty())
	{
		if (GetWorld()->GetTimeSeconds() < PinnedBarUntil) { HudModel->BarMessage = PinnedBarMessage; HudModel->bBarMessageAccent = true; }
		else { PinnedBarMessage.Reset(); }
	}
	if (HudModel->BarMessage != PinnedBarMessage) { HudModel->bBarMessageAccent = false; }

	// A lot wearing out is the loop's one bad surprise: the bar says so and the
	// board knocks. The selection panel then reads NEEDS REPAIR and offers H.
	if (UStacktownEconomy* EconForEvents = GetGameInstance() ? GetGameInstance()->GetSubsystem<UStacktownEconomy>() : nullptr)
	{
		for (const Stacktown::FEconEvent& E : EconForEvents->LastTickEvents)
		{
			if (E.Type == Stacktown::EEconEventType::WornOut)
			{
				HudModel->BarMessage = TEXT("a building wore out \u00b7 select it and press H to repair");
				PlayCue(TEXT("S_Refuse"));
				UE_LOG(LogStacktown, Log, TEXT("WEAR: %s wore out"), *E.Pid);
			}
		}
		EconForEvents->LastTickEvents.Reset();
	}

	// any key press clears a showing refusal (LOOK 6: cleared on the next input)
	const bool bAnyKey = WasInputKeyJustPressed(EKeys::LeftMouseButton) || WasInputKeyJustPressed(EKeys::B) || WasInputKeyJustPressed(EKeys::U)
		|| WasInputKeyJustPressed(EKeys::H) || WasInputKeyJustPressed(EKeys::Tab) || WasInputKeyJustPressed(EKeys::N) || WasInputKeyJustPressed(EKeys::G) || WasInputKeyJustPressed(EKeys::L);
	if (bAnyKey && bRefusalShowing) { HudModel->ActionRefusal.Reset(); bRefusalShowing = false; }

	// hover: a lot actor under the cursor, or the board point for the ghost
	FHitResult Hit;
	const bool bHit = GetHitResultUnderCursor(ECC_Visibility, false, Hit);
	AActor* HitActor = bHit ? Hit.GetActor() : nullptr;
	const FString HitPid = HitActor ? Sync->PidForActor(HitActor) : FString();
	FVector Board;
	const bool bBoard = BoardPointUnderCursor(Board);
	if (WasInputKeyJustPressed(EKeys::G)) { UE_LOG(LogStacktown, Log, TEXT("ROAD: %s"), *CityRoadMode(!bRoadMode)); }
	if (WasInputKeyJustPressed(EKeys::L)) { UE_LOG(LogStacktown, Log, TEXT("NIGHT: %s"), *CityNight(!(Night && Night->IsNight()))); }
	if (bRoadMode && WasInputKeyJustPressed(EKeys::T)) { UE_LOG(LogStacktown, Log, TEXT("ROAD CLASS: %s"), *CityCycleRoadClass()); }
	if (!bRoadMode && WasInputKeyJustPressed(EKeys::P)) { UE_LOG(LogStacktown, Log, TEXT("PRESET: %s"), *CityPreset()); }
	if (!bRoadMode && WasInputKeyJustPressed(EKeys::R)) { UE_LOG(LogStacktown, Log, TEXT("RECIPE: %s"), *CityCycleRecipe()); }
	if (bRoadMode)
	{
		HideGhost();
		if (bBoard) { RoadGhost(Board); } else { HideRoadGhost(); }
		if (WasInputKeyJustPressed(EKeys::LeftMouseButton) && bBoard) { UE_LOG(LogStacktown, Log, TEXT("ROAD: %s"), *CityRoadClick(Board.X, Board.Y)); }
	}
	else
	{
		if (!HitPid.IsEmpty()) { HoverGhost(FVector::ZeroVector, true); }
		else if (bBoard) { HoverGhost(Board, false); }
		else { HideGhost(); }

		if (WasInputKeyJustPressed(EKeys::LeftMouseButton))
		{
			if (!HitPid.IsEmpty()) { UE_LOG(LogStacktown, Log, TEXT("CLICK: %s"), *CitySelect(HitPid)); }
			else if (bBoard) { UE_LOG(LogStacktown, Log, TEXT("CLICK: %s"), *CityPlaceAt(Board.X, Board.Y)); }
		}
	}
	if (WasInputKeyJustPressed(EKeys::B)) { UE_LOG(LogStacktown, Log, TEXT("VERB: %s"), *CityVerb(TEXT("B"))); }
	if (WasInputKeyJustPressed(EKeys::U)) { UE_LOG(LogStacktown, Log, TEXT("VERB: %s"), *CityVerb(TEXT("U"))); }
	if (WasInputKeyJustPressed(EKeys::H)) { UE_LOG(LogStacktown, Log, TEXT("VERB: %s"), *CityVerb(TEXT("H"))); }
	if (WasInputKeyJustPressed(EKeys::Tab)) { CityCycleWidth(+1); }

	if (IsInputKeyDown(EKeys::N))
	{
		NHeld += DeltaTime;
		if (!bNFired)
		{
			HudModel->BarMessage = FString::Printf(TEXT("HOLD N TO RESET \u00b7 %.1f"), FMath::Max(0.f, ResetHoldSeconds - NHeld));
			if (NHeld >= ResetHoldSeconds) { bNFired = true; UE_LOG(LogStacktown, Log, TEXT("RESET: %s"), *CityReset()); }
		}
	}
	else if (NHeld > 0.f)
	{
		NHeld = 0.f; bNFired = false; HudModel->BarMessage.Reset();
	}
}

void AStacktownPlayerController::PlayCue(const TCHAR* Name)
{
	const FString Key(Name);
	if (CuesMissing.Contains(Key)) { return; }
	TObjectPtr<USoundBase>* Found = Cues.Find(Key);
	USoundBase* Cue = Found ? Found->Get() : nullptr;
	if (!Cue)
	{
		Cue = LoadObject<USoundBase>(nullptr, *FString::Printf(TEXT("/Game/Stacktown/Audio/%s.%s"), Name, Name));
		if (!Cue)
		{
			CuesMissing.Add(Key);
			UE_LOG(LogStacktown, Log, TEXT("SOUND: no cue %s - silent"), Name);
			return;
		}
		Cues.Add(Key, Cue);
	}
	UGameplayStatics::PlaySound2D(this, Cue);
	UE_LOG(LogStacktown, Log, TEXT("SOUND: %s"), Name);
}

FString AStacktownPlayerController::CityCycleRoadClass()
{
	static const TCHAR* Classes[] = { TEXT("dirt"), TEXT("avenue"), TEXT("boulevard"), TEXT("highway") };
	int32 Index = 1;
	for (int32 i = 0; i < 4; ++i) { if (RoadClass == Classes[i]) { Index = i; break; } }
	RoadClass = Classes[(Index + 1) % 4];
	if (HudModel) { HudModel->RoadClass = RoadClass; HudModel->BarMessage = TEXT("click start, click end \u00b7 T next type \u00b7 G to leave"); }
	PlayCue(TEXT("S_Place"));
	return RoadClass;
}

FString AStacktownPlayerController::CityPreset()
{
	UStacktownEconomy* Econ = GetGameInstance() ? GetGameInstance()->GetSubsystem<UStacktownEconomy>() : nullptr;
	UStacktownCitySync* Sync = GetWorld() ? GetWorld()->GetSubsystem<UStacktownCitySync>() : nullptr;
	if (!Econ || !Sync || !Sync->OwnsCity()) { return TEXT("the C++ port is not driving this city"); }
	if (Econ->GetState().Parcels.Num() > 0)
	{
		if (HudModel) { HudModel->ActionRefusal = TEXT("The board is not empty"); bRefusalShowing = true; }
		PlayCue(TEXT("S_Refuse"));
		return TEXT("preset refused: the board is not empty");
	}
	const Stacktown::FCityState Fresh = Econ->GetState();
	Stacktown::FCityState Seeded = Stacktown::SeedPresetState(Econ->GetRules(), Stacktown::TemporaryBoard());
	Seeded.Money = Fresh.Money; Seeded.Demand = Fresh.Demand; Seeded.TradesProcessed = Fresh.TradesProcessed; Seeded.GoalsReached = Fresh.GoalsReached; Seeded.Roads = Fresh.Roads;
	Econ->GetMutableState() = Seeded;
	Econ->SaveState();
	if (HudModel) { HudModel->BarMessage = FString::Printf(TEXT("%d lots for sale \u00b7 click one, B to buy"), Seeded.Parcels.Num()); bHintShowing = false; }
	PlayCue(TEXT("S_Place"));
	return FString::Printf(TEXT("preset seeded: %d lots for sale; %s"), Seeded.Parcels.Num(), *Sync->Reconcile(false));
}

FString AStacktownPlayerController::CityCycleRecipe()
{
	static const TCHAR* Recipes[] = { TEXT("vernacular"), TEXT("office"), TEXT("tower") };
	int32 Index = 0;
	for (int32 i = 0; i < 3; ++i) { if (NextRecipe == Recipes[i]) { Index = i; break; } }
	NextRecipe = Recipes[(Index + 1) % 3];
	if (HudModel) { HudModel->BarMessage = FString::Printf(TEXT("%s \u00b7 width %d"), *NextRecipe, (int32)CurrentLotWidth()); }
	PlayCue(TEXT("S_Place"));
	return NextRecipe;
}
