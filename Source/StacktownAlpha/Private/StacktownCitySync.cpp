#include "StacktownCitySync.h"
#include "StacktownParcel.h"
#include "StacktownRuntimeSettings.h"
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
#include "HAL/PlatformProcess.h"
#include "Misc/ConfigCacheIni.h"
#include "Modules/ModuleManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "TimerManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

bool UStacktownCitySync::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && (World->WorldType == EWorldType::Game || World->WorldType == EWorldType::PIE);
}

bool UStacktownCitySync::PythonDriversEnabled()
{
	// The rule itself lives on UStacktownRuntimeSettings now (queue item 5), so
	// there is one place it can be read from and one place it can be wrong.
	return UStacktownRuntimeSettings::PythonDriversEnabled();
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
	FString Err;
	// One loader (queue item 4): the path lives in Stacktown::RulesFilePath and
	// is spelled in exactly one place.
	if (!Econ->LoadRulesFromFile(Err)) { OutWhy = Err; return false; }
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
	// The standalone lock the Python driver used to write at registration: a
	// real game process records its pid so an editor PIE started meanwhile
	// resolves to the test file instead of sharing this save (the C++ path
	// rules already read it; nobody wrote it once Python was off).
	if (!GIsEditor)
	{
		const FString LockPath = FPaths::ProjectSavedDir() / TEXT("standalone.lock");
		FFileHelper::SaveStringToFile(FString::FromInt((int32)FPlatformProcess::GetCurrentProcessId()), *LockPath);
		UE_LOG(LogStacktown, Log, TEXT("CitySync: standalone lock written (%s)"), *LockPath);
	}
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
		ReadTradeLedger();
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

/** The lot's own road's frontage distance, for LotFrame::Pose - the one line
 *  that keeps a building standing on its pad when its road is not an avenue. */
static double LotRoadHalf(const Stacktown::FPlacementBoard& Board,
	const TArray<Stacktown::FRoad>& Roads, const Stacktown::FLotPlacement& Lot)
{
	const Stacktown::FRoad* Road = Stacktown::FindRoad(Roads, Stacktown::LotRoadId(Lot));
	return Road ? Stacktown::RoadHalf(Board.Rules, Board.Econ, *Road)
	            : Stacktown::LotFrame::RoadHalf;
}

FString UStacktownCitySync::Reconcile(bool bHideBlueprintLots)
{
	UWorld* World = GetWorld();
	UStacktownEconomy* Econ = Economy();
	if (!World || !Econ) { return TEXT("reconcile: no world or economy"); }
	if (bHideBlueprintLots) { HideBlueprintLots(); }
	const Stacktown::FCityState& State = Econ->GetState();
	const Stacktown::FPlacementBoard Board = Stacktown::FPlacementBoard::Default(Econ->GetRules());
	const TArray<Stacktown::FRoad> Roads = Board.AllRoads(State);
	int32 Spawned = 0, Updated = 0, Removed = 0, Skipped = 0;
	TSet<FString> Seen;
	for (const auto& Pair : State.Parcels)
	{
		const FString& Pid = Pair.Key;
		const Stacktown::FParcelState& P = Pair.Value;
		if (!P.Placement.IsSet()) { ++Skipped; continue; }   // pinned lots: poses come with the board factory (item 5)
		Stacktown::LotFrame::FPose Pose;
		if (!Stacktown::LotFrame::Pose(P.Placement.GetValue(), Roads, Pose,
			LotRoadHalf(Board, Roads, P.Placement.GetValue()))) { ++Skipped; continue; }
		Seen.Add(Pid);
		const FString Sig = FString::Printf(TEXT("%s|%d|%.0f|%d|%.0f|%.0f|%.0f"), *P.Rid, P.Tier, P.Width, P.bOwned, Pose.X, Pose.Y, Pose.Yaw);
		TObjectPtr<AActor>* Existing = Lots.Find(Pid);
		AActor* A = (Existing && IsValid(*Existing)) ? Existing->Get() : nullptr;
		if (!A)
		{
			FActorSpawnParameters Params;
			Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			// AStacktownParcel, not a plain AActor (queue item 8, the actor swap
			// STATE_HANDOVER deferred). What it buys is IDENTITY: the parcel
			// carries its own ParcelId, so every reader that needs to know which
			// lot an actor is - PidForActor for the click hit test, the mirror
			// comparison in StacktownAgreement, ApplyFacts - asks the actor
			// instead of searching a map, and a lot cannot be misidentified
			// because a spawn order changed.
			//
			// ParcelId IS SET AT SPAWN, from the state key, and this is the whole
			// reason item 3 made it a UPROPERTY: an actor LABEL does not exist in
			// a cooked build, and a NAME is uniquified by the engine, so the
			// second parcel spawned as "P1" quietly becomes "P1_2" and stops
			// matching its own entry in the city state.
			AStacktownParcel* Parcel = World->SpawnActor<AStacktownParcel>(
				AStacktownParcel::StaticClass(), FVector(Pose.X, Pose.Y, 0.0),
				FRotator(0.0, Pose.Yaw, 0.0), Params);
			A = Parcel;
			if (!A) { continue; }
			Parcel->ParcelId = Pid;
			// The actor's own immutable identity, set once by the builder and
			// never written back - the sync must not push these, or the state and
			// the actor start arguing about who a parcel is.
			Parcel->RecipeId = P.Rid;
			Parcel->WidthUU = P.Width;
			// UNCHANGED FROM THE PLAIN ACTOR: a plain root carries the pose and
			// the visual hangs off it with its OWN local offset. Found live
			// 2026-09-06 - with the visual as the root, its mesh offset overwrote
			// the actor's location and every lot sat at the origin. The parcel
			// class does not create a root of its own, so this is still the one
			// place the root comes from.
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
				const bool bShown = P.bOwned ? V->ShowMass(P.Rid, P.Tier, P.Width, false, Err) : V->ShowPad(P.Width, Err, true);
				if (!bShown) { UE_LOG(LogStacktown, Warning, TEXT("CitySync: %s visual: %s"), *Pid, *Err); }
			}
			if (Signatures.Contains(Pid)) { ++Updated; }
			Signatures.Add(Pid, Sig);
		}
		if (UStacktownLotVisual* V = A->FindComponentByClass<UStacktownLotVisual>())
		{
			// Age has no home in the C++ state yet (the Python driver kept age_ticks
			// beside the parcel, outside the economy's exact-equality oracles); 0 = pale,
			// which is B3's own rule for a new building. Wired when age lands in state.
			// Age from the state (queue item 7); this passed a hard 0 before,
			// so every mass rendered pale no matter how long it had stood.
			const double WearLimit = Econ->GetRules().WearTicksPerTier * (double)(P.Tier + 1);
			const float Wear01 = WearLimit > 0.0 ? (float)(P.Wear / WearLimit) : 0.f;
			V->ApplyState(P.bOwned, static_cast<float>(Stacktown::AgeFraction(P.AgeTicks)), Wear01, P.bFailed);
		}
		// THE PARCEL'S OWN FACTS (queue item 8). ApplyFacts is the same function
		// a hand-placed BP_Parcel goes through, fed from the same mirror, so a
		// spawned lot and a placed one answer the agreement instrument
		// identically. It returns whether anything changed and writes only then.
		if (AStacktownParcel* Parcel = Cast<AStacktownParcel>(A))
		{
			Parcel->ApplyFacts(Stacktown::FactsForLabel(Econ->GetRules(), State, Pid));
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
	// drawn roads: one AStacktownRoad per segment in the state, each chord of a
	// path cut to meet its neighbours (design lane 2026-09-07 05:32: mitre it,
	// and draw it at the carriageway - the verge is bare plate)
	int32 RoadsSpawned = 0, RoadsRemoved = 0;
	TSet<FString> RoadsSeen;
	const TMap<FString, Stacktown::RoadFrame::FJoint> Joints = Stacktown::RoadFrame::PathJoints(State.Roads);
	for (const auto& Pair : State.Roads)
	{
		const FString& Id = Pair.Key;
		const Stacktown::FRoadSegment& Seg = Pair.Value;
		RoadsSeen.Add(Id);
		const Stacktown::RoadFrame::FJoint Joint = Joints.FindRef(Id);
		// The TYPE is part of the signature since road types (2026-09-06): it
		// decides the width and the stain, so a segment that changed type
		// without moving must still be re-shown. The JOINTS are part of it too:
		// a chord that did not move still needs a new cut when its neighbour did.
		const FString Sig = FString::Printf(TEXT("%.0f|%.0f|%.0f|%.0f|%s|%.4f|%.4f"),
			Seg.StartX, Seg.StartY, Seg.EndX, Seg.EndY, *Seg.WidthClass, Joint.TanStart, Joint.TanEnd);
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
			Road->ShowSegment(Id, Seg,
				Stacktown::RoadCarriageway(Board.Econ, Seg.WidthClass), Joint.TanStart, Joint.TanEnd,
				Joint.S0, Joint.PathLength);
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
	// THE ACTOR'S OWN ID FIRST (queue item 8). A spawned parcel knows which lot
	// it is, so a click on the mass does not depend on this subsystem's map
	// being in step with the world - which it is not, for anything spawned by
	// something else, and which is exactly the case the map scan below is
	// still here for (hand-placed actors, and anything a future spawner adds).
	if (const AStacktownParcel* Parcel = Cast<AStacktownParcel>(Actor))
	{
		const FString Id = Parcel->GetParcelId();
		if (!Id.IsEmpty()) { return Id; }
	}
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

FString UStacktownCitySync::TradeLedgerPath()
{
	return FPaths::ProjectSavedDir() / TEXT("Stacktown") / TEXT("trade_ledger.jsonl");
}

FString UStacktownCitySync::ReadTradeLedger()
{
	// The message is NOT cleared here: the controller consumes it on its next tick
	// and clears it then. Found by the live probe 2026-09-06: two reads in one frame
	// (before any tick) wiped the message before the bar ever saw it.
	UStacktownEconomy* Econ = Economy();
	if (!Econ || !bOwnsCity) { return TEXT("ledger: not owning"); }
	const FString Path = TradeLedgerPath();
	if (!FPaths::FileExists(Path)) { return TEXT("ledger: no file"); }
	TArray<FString> Lines;
	if (!FFileHelper::LoadFileToStringArray(Lines, *Path)) { return TEXT("ledger: unreadable"); }
	// Every CLOSED trade's pnl, in file order; the economy's TradesProcessed makes
	// re-reading the whole file each time a no-op for what it has already counted.
	TArray<double> Pnls;
	int32 Bad = 0;
	for (const FString& Line : Lines)
	{
		if (Line.TrimStartAndEnd().IsEmpty()) { continue; }
		TSharedPtr<FJsonObject> Obj;
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Line);
		double Pnl = 0.0;
		if (FJsonSerializer::Deserialize(Reader, Obj) && Obj.IsValid() && Obj->TryGetNumberField(TEXT("pnl"), Pnl)) { Pnls.Add(Pnl); }
		else { ++Bad; }   // a torn last line (append-only file, crash mid-write) is tolerated, never counted
	}
	const int32 Before = Econ->GetState().TradesProcessed;
	TArray<Stacktown::FEconEvent> Events;
	Econ->ApplyTradeLedger(Pnls, Events);
	const int32 After = Econ->GetState().TradesProcessed;
	if (Events.Num() > 0)
	{
		double Credits = 0.0, Bonus = 0.0;
		for (const Stacktown::FEconEvent& E : Events)
		{
			if (E.Type == Stacktown::EEconEventType::TradeCredits) { Credits += E.Amount; } else { Bonus += E.Amount; }
		}
		if (Credits > 0.0 && Bonus > 0.0) { LastTradeMessage = FString::Printf(TEXT("trades: +$%.0f credits, +$%.0f win bonus"), Credits, Bonus); }
		else if (Credits > 0.0) { LastTradeMessage = FString::Printf(TEXT("trades: +$%.0f credits"), Credits); }
		else { LastTradeMessage = FString::Printf(TEXT("trades: +$%.0f win bonus"), Bonus); }
		UE_LOG(LogStacktown, Log, TEXT("CitySync: %s (%d new closed trades)"), *LastTradeMessage, After - Before);
	}
	LedgerLinesSeen = Pnls.Num();
	return FString::Printf(TEXT("ledger: %d closed trades on file (%d unreadable lines), %d newly counted, %d events, money %.2f"), Pnls.Num(), Bad, After - Before, Events.Num(), Econ->GetState().Money);
}
