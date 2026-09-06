#include "StacktownCitySync.h"
#include "StacktownAlpha.h"
#include "StacktownEconomy.h"
#include "StacktownLotTransform.h"
#include "StacktownLotVisual.h"
#include "StacktownStateHandover.h"
#include "StacktownWorldBoard.h"
#include "StacktownWoodCatalogue.h"
#include "StacktownRoad.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Components/SceneComponent.h"
#include "EngineUtils.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "Misc/ConfigCacheIni.h"
#include "Modules/ModuleManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "TimerManager.h"

bool UStacktownCitySync::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && (World->WorldType == EWorldType::Game || World->WorldType == EWorldType::PIE);
}

bool UStacktownCitySync::PythonDriversEnabled()
{
	// A packaged app has no Python plugin at all (UncookedOnly): the C++ side
	// owns the city there regardless of any setting.
	if (!FModuleManager::Get().IsModuleLoaded(TEXT("PythonScriptPlugin")))
	{
		return false;
	}
	const FString Env = FPlatformMisc::GetEnvironmentVariable(TEXT("STACKTOWN_PYTHON_DRIVERS"));
	if (!Env.IsEmpty())
	{
		return !(Env == TEXT("0") || Env.Equals(TEXT("false"), ESearchCase::IgnoreCase) || Env.Equals(TEXT("no"), ESearchCase::IgnoreCase));
	}
	bool bValue = true;
	if (GConfig && GConfig->GetBool(TEXT("/Script/StacktownAlpha.StacktownRuntime"), TEXT("bPythonDrivers"), bValue, GGameIni))
	{
		return bValue;
	}
	return true;
}

UStacktownEconomy* UStacktownCitySync::Economy() const
{
	const UWorld* World = GetWorld();
	UGameInstance* GI = World ? World->GetGameInstance() : nullptr;
	return GI ? GI->GetSubsystem<UStacktownEconomy>() : nullptr;
}

void UStacktownCitySync::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	bOwnsCity = !PythonDriversEnabled();
	if (!bOwnsCity)
	{
		UE_LOG(LogStacktown, Log, TEXT("CitySync: Python drivers ON - the world stays theirs (Phase A); Reconcile is available on request"));
		return;
	}
	FString Why;
	if (!BeginOwning(Why))
	{
		UE_LOG(LogStacktown, Error, TEXT("CitySync: cannot own the city: %s"), *Why);
		bOwnsCity = false;
		return;
	}
	HideBlueprintLots();
	UE_LOG(LogStacktown, Log, TEXT("CitySync: %s"), *Reconcile(false));
	InWorld.GetTimerManager().SetTimer(Timer, FTimerDelegate::CreateUObject(this, &UStacktownCitySync::OnTimer), 0.5f, true);
}

bool UStacktownCitySync::BeginOwning(FString& OutWhy)
{
	UStacktownEconomy* Econ = Economy();
	if (!Econ) { OutWhy = TEXT("no economy subsystem"); return false; }
	FString RulesText, Err;
	const FString RulesPath = FPaths::ProjectConfigDir() / TEXT("Stacktown/econrules.json");
	if (!FFileHelper::LoadFileToString(RulesText, *RulesPath)) { OutWhy = FString::Printf(TEXT("rules file missing: %s"), *RulesPath); return false; }
	if (!Econ->LoadRules(RulesText, Err)) { OutWhy = Err; return false; }
	Econ->SetCatalogue(MakeShared<Stacktown::FWoodCatalogue>());
	Stacktown::EStateSource Source;
	const FString SessionPath = Econ->StatePathForSession(Source, false);
	// Phase B, step 1: the C++ owner writes under Saved/Stacktown, never under
	// Content/Python; the Python-written file is copied across ONCE, when no
	// owned file exists yet (the migration; ledgered by the log line).
	const FString Owned = FPaths::ProjectSavedDir() / TEXT("Stacktown") / FPaths::GetCleanFilename(SessionPath);
	IFileManager::Get().MakeDirectory(*FPaths::GetPath(Owned), true);
	if (!FPaths::FileExists(Owned) && FPaths::FileExists(SessionPath))
	{
		const bool bCopied = IFileManager::Get().Copy(*Owned, *SessionPath) == COPY_OK;
		UE_LOG(LogStacktown, Log, TEXT("CitySync: migrated %s -> %s (%s)"), *SessionPath, *Owned, bCopied ? TEXT("copied") : TEXT("COPY FAILED"));
	}
	Econ->SetStatePath(Owned);
	if (!Econ->LoadState(Err)) { OutWhy = Err; return false; }
	UE_LOG(LogStacktown, Log, TEXT("CitySync: OWNS the city - state %s (%s), money %.2f, %d parcels"), *Owned, *Stacktown::StateSourceName(Source), Econ->GetState().Money, Econ->GetState().Parcels.Num());
	return true;
}

void UStacktownCitySync::OnTimer()
{
	if (!bOwnsCity) { return; }
	UStacktownEconomy* Econ = Economy();
	if (!Econ) { return; }
	TickAccum += 0.5f;
	if (TickAccum >= TickIntervalSeconds)
	{
		TickAccum = 0.f;
		Econ->CityTick();
		Econ->SaveState();
	}
	Reconcile(false);
}

void UStacktownCitySync::HideBlueprintLots()
{
	UWorld* World = GetWorld();
	if (!World || bBlueprintLotsHidden) { return; }
	int32 N = 0;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		if (It->GetClass()->GetName().StartsWith(TEXT("BP_Parcel")))
		{
			It->SetActorHiddenInGame(true);
			It->SetActorEnableCollision(false);
			It->SetActorTickEnabled(false);
			++N;
		}
	}
	bBlueprintLotsHidden = true;
	UE_LOG(LogStacktown, Log, TEXT("CitySync: hid %d Blueprint parcel actors (the C++ lots stand in their place)"), N);
}

FString UStacktownCitySync::Reconcile(bool bHideBlueprintLots)
{
	UWorld* World = GetWorld();
	UStacktownEconomy* Econ = Economy();
	if (!World || !Econ) { return TEXT("reconcile: no world or economy"); }
	if (bHideBlueprintLots) { HideBlueprintLots(); }
	const Stacktown::FCityState& State = Econ->GetState();
	const TArray<Stacktown::FRoad> Roads = Stacktown::TemporaryBoard().AllRoads(State);
	int32 Spawned = 0, Updated = 0, Removed = 0, Skipped = 0;
	TSet<FString> Seen;
	for (const auto& Pair : State.Parcels)
	{
		const FString& Pid = Pair.Key;
		const Stacktown::FParcelState& P = Pair.Value;
		if (!P.Placement.IsSet()) { ++Skipped; continue; }   // pinned lots: poses come with the board factory (item 5)
		Stacktown::LotFrame::FPose Pose;
		if (!Stacktown::LotFrame::Pose(P.Placement.GetValue(), Roads, Pose)) { ++Skipped; continue; }
		Seen.Add(Pid);
		const FString Sig = FString::Printf(TEXT("%s|%d|%.0f|%d|%.0f|%.0f|%.0f"), *P.Rid, P.Tier, P.Width, P.bOwned, Pose.X, Pose.Y, Pose.Yaw);
		TObjectPtr<AActor>* Existing = Lots.Find(Pid);
		AActor* A = (Existing && IsValid(*Existing)) ? Existing->Get() : nullptr;
		if (!A)
		{
			FActorSpawnParameters Params;
			Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			A = World->SpawnActor<AActor>(AActor::StaticClass(), FVector(Pose.X, Pose.Y, 0.0), FRotator(0.0, Pose.Yaw, 0.0), Params);
			if (!A) { continue; }
			// A plain root carries the pose; the visual hangs off it with its OWN
			// local offset. Found live 2026-09-06: with the visual as the root, its
			// mesh offset overwrote the actor's location and every lot sat at the origin.
			USceneComponent* Root = NewObject<USceneComponent>(A, TEXT("Root"));
			A->SetRootComponent(Root);
			Root->RegisterComponent();
			A->SetActorLocationAndRotation(FVector(Pose.X, Pose.Y, 0.0), FRotator(0.0, Pose.Yaw, 0.0));
			UStacktownLotVisual* V = NewObject<UStacktownLotVisual>(A, TEXT("Building"));
			V->AttachToComponent(Root, FAttachmentTransformRules::KeepRelativeTransform);
			V->RegisterComponent();
			Lots.Add(Pid, A);
			Signatures.Remove(Pid);
			++Spawned;
		}
		if (Signatures.FindRef(Pid) != Sig)
		{
			A->SetActorLocationAndRotation(FVector(Pose.X, Pose.Y, 0.0), FRotator(0.0, Pose.Yaw, 0.0));
			if (UStacktownLotVisual* V = A->FindComponentByClass<UStacktownLotVisual>())
			{
				FString Err;
				const bool bShown = P.bOwned ? V->ShowMass(P.Rid, P.Tier, P.Width, false, Err) : V->ShowPad(P.Width, Err);
				if (!bShown) { UE_LOG(LogStacktown, Warning, TEXT("CitySync: %s visual: %s"), *Pid, *Err); }
			}
			if (Signatures.Contains(Pid)) { ++Updated; }
			Signatures.Add(Pid, Sig);
		}
	}
	for (auto It = Lots.CreateIterator(); It; ++It)
	{
		if (!Seen.Contains(It.Key()))
		{
			if (IsValid(It.Value())) { It.Value()->Destroy(); }
			Signatures.Remove(It.Key());
			It.RemoveCurrent();
			++Removed;
		}
	}
	// drawn roads: one AStacktownRoad per segment in the state
	int32 RoadsSpawned = 0, RoadsRemoved = 0;
	TSet<FString> RoadsSeen;
	for (const auto& Pair : State.Roads)
	{
		const FString& Id = Pair.Key;
		const Stacktown::FRoadSegment& Seg = Pair.Value;
		RoadsSeen.Add(Id);
		const FString Sig = FString::Printf(TEXT("%.0f|%.0f|%.0f|%.0f"), Seg.StartX, Seg.StartY, Seg.EndX, Seg.EndY);
		TObjectPtr<AActor>* Existing = RoadActors.Find(Id);
		AStacktownRoad* Road = (Existing && IsValid(*Existing)) ? Cast<AStacktownRoad>(Existing->Get()) : nullptr;
		if (!Road)
		{
			FActorSpawnParameters Params;
			Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			Road = World->SpawnActor<AStacktownRoad>(AStacktownRoad::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, Params);
			if (!Road) { continue; }
			RoadActors.Add(Id, Road);
			RoadSignatures.Remove(Id);
			++RoadsSpawned;
		}
		if (RoadSignatures.FindRef(Id) != Sig)
		{
			Road->ShowSegment(Id, Seg);
			RoadSignatures.Add(Id, Sig);
		}
	}
	for (auto It = RoadActors.CreateIterator(); It; ++It)
	{
		if (!RoadsSeen.Contains(It.Key()))
		{
			if (IsValid(It.Value())) { It.Value()->Destroy(); }
			RoadSignatures.Remove(It.Key());
			It.RemoveCurrent();
			++RoadsRemoved;
		}
	}
	return FString::Printf(TEXT("reconcile: %d lots standing (%d spawned, %d updated, %d removed, %d without a pose), %d roads (%d spawned, %d removed), owner=%s"), Lots.Num(), Spawned, Updated, Removed, Skipped, RoadActors.Num(), RoadsSpawned, RoadsRemoved, bOwnsCity ? TEXT("C++") : TEXT("Python"));
}

void UStacktownCitySync::Deinitialize()
{
	if (UWorld* World = GetWorld()) { World->GetTimerManager().ClearTimer(Timer); }
	Lots.Empty();
	RoadActors.Empty();
	Super::Deinitialize();
}

FString UStacktownCitySync::PidForActor(const AActor* Actor) const
{
	for (const auto& Pair : Lots)
	{
		if (Pair.Value.Get() == Actor) { return Pair.Key; }
	}
	return FString();
}

AActor* UStacktownCitySync::ActorForPid(const FString& Pid) const
{
	const TObjectPtr<AActor>* Found = Lots.Find(Pid);
	return (Found && IsValid(*Found)) ? Found->Get() : nullptr;
}
