#include "StacktownAgreement.h"
#include "StacktownAlpha.h"
#include "StacktownEconomy.h"
#include "StacktownStateHandover.h"
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
	const FString RulesPath = FPaths::ProjectConfigDir() / TEXT("Stacktown/econrules.json");
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
		if (!A->GetClass()->GetName().StartsWith(TEXT("BP_Parcel")))
		{
			continue;
		}
		const FString Label = A->GetActorNameOrLabel();
		double Width = 0.0;
		if (!ReadNumber(A, TEXT("WidthUU"), Width) || Width <= 0.0 || Stacktown::IsPoolLabel(Label))
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
		ReadString(A, TEXT("RecipeId"), Rid); ReadNumber(A, TEXT("Tier"), Tier); ReadNumber(A, TEXT("Price"), Price); ReadBool(A, TEXT("Owned"), bOwned);
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
