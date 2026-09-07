#include "StacktownAgreement.h"
#include "StacktownParcel.h"
#include "StacktownAlpha.h"
#include "StacktownEconomy.h"
#include "StacktownStateHandover.h"
#include "StacktownLotTransform.h"
#include "StacktownLotVisual.h"
#include "StacktownPlacement.h"
#include "StacktownWorldBoard.h"
#include "StacktownCitySync.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "UObject/UnrealType.h"

namespace
{
	bool ReadNumber(const UObject* Obj, const TCHAR* Name, double& Out)
	{
		FProperty* P = Obj->GetClass()->FindPropertyByName(Name);
		FNumericProperty* NP = CastField<FNumericProperty>(P);
		if (!NP) { return false; }
		const void* V = P->ContainerPtrToValuePtr<void>(Obj);
		Out = NP->IsFloatingPoint() ? NP->GetFloatingPointPropertyValue(V) : (double)NP->GetSignedIntPropertyValue(V);
		return true;
	}
	bool ReadBool(const UObject* Obj, const TCHAR* Name, bool& Out)
	{
		FBoolProperty* BP = CastField<FBoolProperty>(Obj->GetClass()->FindPropertyByName(Name));
		if (!BP) { return false; }
		Out = BP->GetPropertyValue_InContainer(Obj);
		return true;
	}
	bool ReadString(const UObject* Obj, const TCHAR* Name, FString& Out)
	{
		FProperty* P = Obj->GetClass()->FindPropertyByName(Name);
		if (!P) { return false; }
		const void* V = P->ContainerPtrToValuePtr<void>(Obj);
		if (FNameProperty* NP = CastField<FNameProperty>(P)) { Out = NP->GetPropertyValue(V).ToString(); return true; }
		if (FStrProperty* SP = CastField<FStrProperty>(P)) { Out = SP->GetPropertyValue(V); return true; }
		if (FTextProperty* TP = CastField<FTextProperty>(P)) { Out = TP->GetPropertyValue(V).ToString(); return true; }
		return false;
	}
}

FString UStacktownAgreementLibrary::CompareMirrorWithWorld(const UObject* WorldContextObject)
{
	UWorld* World = WorldContextObject ? WorldContextObject->GetWorld() : nullptr;
	UGameInstance* GI = World ? World->GetGameInstance() : nullptr;
	UStacktownEconomy* Econ = GI ? GI->GetSubsystem<UStacktownEconomy>() : nullptr;
	if (!Econ)
	{
		return TEXT("VERDICT: no economy subsystem in this world");
	}
	TArray<FString> Lines;

	// Rules: Phase A loads them from the Python oracle's own file (editor/game on this machine only).
	FString RulesText, Err;
	const FString RulesPath = Stacktown::RulesFilePath();
	if (!FFileHelper::LoadFileToString(RulesText, *RulesPath) || !Econ->LoadRules(RulesText, Err))
	{
		return FString::Printf(TEXT("VERDICT: rules not loaded from %s: %s"), *RulesPath, *Err);
	}

	Stacktown::EStateSource Source;
	// The session's cached resolution, never a forced re-resolve: the Python
	// driver resolves ONCE at registration (marker present at launch, removed
	// seconds later), and a re-resolve here would land on the owner's file.
	// Found live 2026-09-06: the first run of this instrument did exactly that.
	const FString Path = Econ->StatePathForSession(Source, false);
	Lines.Add(FString::Printf(TEXT("state path: %s (%s)"), *Path, *Stacktown::StateSourceName(Source)));
	if (!Econ->MirrorFromFile(Path, Err))
	{
		Lines.Insert(FString::Printf(TEXT("VERDICT: mirror failed: %s"), *Err), 0);
		return FString::Join(Lines, TEXT("\n"));
	}
	const Stacktown::FCityState& State = Econ->GetState();
	Lines.Add(FString::Printf(TEXT("mirror: money %.2f demand %.2f parcels %d"), State.Money, State.Demand, State.Parcels.Num()));

	int32 Compared = 0, Agree = 0, Missing = 0;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* A = *It;
		// BOTH KINDS (queue item 8, the actor swap). A spawned AStacktownParcel
		// carries its own ParcelId and typed facts; a hand-placed BP_Parcel is
		// read reflectively off its label, as before. Comparing by ParcelId
		// rather than by label is the point: a label does not exist in a cooked
		// build at all, and a NAME is uniquified on spawn, so the second parcel
		// spawned as "P1" quietly becomes "P1_2" and this instrument would
		// report it ABSENT from a mirror that has it.
		AStacktownParcel* Parcel = Cast<AStacktownParcel>(A);
		if (Parcel == nullptr && !A->GetClass()->GetName().StartsWith(TEXT("BP_Parcel")))
		{
			continue;
		}
		const FString Label = Parcel ? Parcel->GetParcelId() : A->GetActorNameOrLabel();
		double Width = 0.0;
		if (Parcel)
		{
			Width = Parcel->WidthUU;
		}
		else if (!ReadNumber(A, TEXT("WidthUU"), Width))
		{
			continue;
		}
		if (Width <= 0.0 || Label.IsEmpty() || Stacktown::IsPoolLabel(Label))
		{
			continue;
		}
		const Stacktown::FParcelFacts F = Stacktown::FactsForLabel(Econ->GetRules(), State, Label);
		++Compared;
		if (!F.bFound)
		{
			++Missing;
			Lines.Add(FString::Printf(TEXT("  %s: standing in the world, ABSENT from the mirror"), *Label));
			continue;
		}
		FString Rid; double Tier = 0.0, Price = 0.0; bool bOwned = false;
		if (Parcel)
		{
			// Typed, not reflected: the parcel's fields ARE the facts, and the
			// reflected read of a bool UPROPERTY named bOwned does not answer to
			// "Owned" anyway - the name the Blueprint path uses.
			Rid = Parcel->RecipeId; Tier = Parcel->Tier;
			Price = Parcel->Price;  bOwned = Parcel->bOwned;
		}
		else
		{
			ReadString(A, TEXT("RecipeId"), Rid); ReadNumber(A, TEXT("Tier"), Tier); ReadNumber(A, TEXT("Price"), Price); ReadBool(A, TEXT("Owned"), bOwned);
		}
		TArray<FString> Diffs;
		if (!Rid.Equals(F.Rid)) { Diffs.Add(FString::Printf(TEXT("rid bp=%s mirror=%s"), *Rid, *F.Rid)); }
		if (FMath::Abs(Width - F.Width) > 0.5) { Diffs.Add(FString::Printf(TEXT("width bp=%.0f mirror=%.0f"), Width, F.Width)); }
		if ((int32)Tier != F.Tier) { Diffs.Add(FString::Printf(TEXT("tier bp=%d mirror=%d"), (int32)Tier, F.Tier)); }
		if (bOwned != F.bOwned) { Diffs.Add(FString::Printf(TEXT("owned bp=%d mirror=%d"), bOwned, F.bOwned)); }
		if (FMath::Abs(Price - F.Price) > 0.01) { Diffs.Add(FString::Printf(TEXT("price bp=%.2f mirror=%.2f"), Price, F.Price)); }
		if (Diffs.Num() == 0)
		{
			++Agree;
			Lines.Add(FString::Printf(TEXT("  %s: agree (%s %.0f tier %d owned %d price %.0f)"), *Label, *F.Rid, F.Width, F.Tier, F.bOwned, F.Price));
		}
		else
		{
			Lines.Add(FString::Printf(TEXT("  %s: MISMATCH %s"), *Label, *FString::Join(Diffs, TEXT("; "))));
		}
	}
	const bool bAllAgree = Compared > 0 && Agree == Compared;
	Lines.Insert(FString::Printf(TEXT("VERDICT: %s - %d standing lots compared, %d agree, %d absent from the mirror"),
		bAllAgree ? TEXT("AGREE") : TEXT("DISAGREE"), Compared, Agree, Missing), 0);
	return FString::Join(Lines, TEXT("\n"));
}

FString UStacktownAgreementLibrary::SpawnLotVisualFor(const UObject* WorldContextObject, const FString& Pid, bool bHideBlueprintTwin)
{
	UWorld* World = WorldContextObject ? WorldContextObject->GetWorld() : nullptr;
	UGameInstance* GI = World ? World->GetGameInstance() : nullptr;
	UStacktownEconomy* Econ = GI ? GI->GetSubsystem<UStacktownEconomy>() : nullptr;
	if (!Econ)
	{
		return TEXT("no economy subsystem");
	}
	const Stacktown::FCityState& State = Econ->GetState();
	const Stacktown::FParcelState* P = State.Parcels.Find(Pid);
	if (!P)
	{
		return FString::Printf(TEXT("%s is not in the mirror (run CompareMirrorWithWorld first)"), *Pid);
	}
	if (!P->Placement.IsSet())
	{
		return FString::Printf(TEXT("%s is a pinned lot with no placement; its transform is the builder's"), *Pid);
	}
	const Stacktown::FPlacementBoard Board = Stacktown::FPlacementBoard::Default();
	Stacktown::LotFrame::FPose Pose;
	if (!Stacktown::LotFrame::Pose(P->Placement.GetValue(), Board.AllRoads(State), Pose))
	{
		return TEXT("no road frame for the lot");
	}
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AActor* A = World->SpawnActor<AActor>(AActor::StaticClass(), FVector(Pose.X, Pose.Y, 0.0), FRotator(0.0, Pose.Yaw, 0.0), Params);
	if (!A)
	{
		return TEXT("spawn failed");
	}
	USceneComponent* Root = NewObject<USceneComponent>(A, TEXT("Root"));
	A->SetRootComponent(Root);
	Root->RegisterComponent();
	A->SetActorLocationAndRotation(FVector(Pose.X, Pose.Y, 0.0), FRotator(0.0, Pose.Yaw, 0.0));
	UStacktownLotVisual* V = NewObject<UStacktownLotVisual>(A, TEXT("Building"));
	V->AttachToComponent(Root, FAttachmentTransformRules::KeepRelativeTransform);
	V->RegisterComponent();
	FString Err;
	const bool bShown = P->bOwned ? V->ShowMass(P->Rid, P->Tier, P->Width, false, Err) : V->ShowPad(P->Width, Err, true);
	TArray<FString> Lines;
	const FVector AL = A->GetActorLocation();
	Lines.Add(FString::Printf(TEXT("C++ lot %s: actor READ BACK at (%.0f, %.0f, yaw %.0f) shows %s%s%s"), *Pid, AL.X, AL.Y, A->GetActorRotation().Yaw,
		bShown ? *V->ShownAsset : TEXT("NOTHING"), V->ShownSpecies.IsEmpty() ? TEXT("") : TEXT(" in "), *V->ShownSpecies));
	if (!bShown) { Lines.Add(FString::Printf(TEXT("  visual error: %s"), *Err)); }
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		if (It->GetClass()->GetName().StartsWith(TEXT("BP_Parcel")) && It->GetActorNameOrLabel() == Pid)
		{
			const FVector L = It->GetActorLocation(); const FRotator R = It->GetActorRotation();
			Lines.Add(FString::Printf(TEXT("BP  lot %s: actor (%.0f, %.0f, yaw %.0f)"), *Pid, L.X, L.Y, R.Yaw));
			if (bHideBlueprintTwin) { It->SetActorHiddenInGame(true); Lines.Add(TEXT("  (Blueprint twin hidden for the capture)")); }
		}
	}
	return FString::Join(Lines, TEXT("\n"));
}

FString UStacktownAgreementLibrary::ReconcileNow(const UObject* WorldContextObject, bool bHideBlueprintLots)
{
	UWorld* World = WorldContextObject ? WorldContextObject->GetWorld() : nullptr;
	UStacktownCitySync* Sync = World ? World->GetSubsystem<UStacktownCitySync>() : nullptr;
	return Sync ? Sync->Reconcile(bHideBlueprintLots) : FString(TEXT("no city sync in this world"));
}

FString UStacktownAgreementLibrary::ReadTradeLedgerNow(const UObject* WorldContextObject)
{
	UWorld* World = WorldContextObject ? WorldContextObject->GetWorld() : nullptr;
	UStacktownCitySync* Sync = World ? World->GetSubsystem<UStacktownCitySync>() : nullptr;
	return Sync ? Sync->ReadTradeLedger() : FString(TEXT("no city sync in this world"));
}
