#include "StacktownNight.h"
#include "StacktownAlpha.h"
#include "Components/LightComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"

namespace
{
	struct FNightFactor { const TCHAR* Name; float Factor; };
	const FNightFactor GFactors[] = {
		{ TEXT("CITY_Sun"), 0.00f }, { TEXT("CITY_Key"), 0.10f }, { TEXT("CITY_Fill"), 0.04f },
		{ TEXT("CITY_StreetKey_A"), 0.04f }, { TEXT("CITY_StreetKey_C"), 0.04f }, { TEXT("CITY_Sky"), 0.15f },
		{ TEXT("LIGHT_BoardKey"), 0.00f } };
	const FLinearColor GNightSky(0.55f, 0.68f, 0.95f, 1.f);   // cooled ambient so a warm window reads warm

	const FNightFactor* FactorFor(const AActor* A)
	{
		const FString Name = A->GetActorNameOrLabel();
		for (const FNightFactor& F : GFactors)
		{
			if (Name == F.Name || A->ActorHasTag(FName(F.Name))) { return &F; }
		}
		return nullptr;
	}
}

int32 UStacktownNight::Apply(UWorld* World, bool bInNight)
{
	if (!World) { return -1; }
	UMaterialParameterCollection* MPC = LoadObject<UMaterialParameterCollection>(nullptr, TEXT("/Game/Stacktown/Materials/MPC_WoodCity.MPC_WoodCity"));
	if (!MPC)
	{
		UE_LOG(LogStacktown, Warning, TEXT("Night: MPC_WoodCity missing; nothing changed"));
		return -1;
	}
	UKismetMaterialLibrary::SetScalarParameterValue(World, MPC, TEXT("NightAmount"), bInNight ? 1.f : 0.f);
	bNight = bInNight;
	int32 N = 0;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		const FNightFactor* F = FactorFor(*It);
		if (!F) { continue; }
		TArray<ULightComponent*> Lights;
		It->GetComponents<ULightComponent>(Lights);
		for (ULightComponent* L : Lights)
		{
			FDayLight* D = Day.Find(F->Name);
			if (!D)
			{
				FDayLight Fresh; Fresh.Intensity = L->Intensity; Fresh.Color = L->GetLightColor();
				D = &Day.Add(F->Name, Fresh);
			}
			L->SetIntensity(bInNight ? D->Intensity * F->Factor : D->Intensity);
			if (FString(F->Name) == TEXT("CITY_Sky"))
			{
				L->SetLightColor(bInNight ? GNightSky : D->Color);
			}
			++N;
		}
	}
	UE_LOG(LogStacktown, Log, TEXT("Night: %s, %d lights %s"), bInNight ? TEXT("night") : TEXT("day"), N, bInNight ? TEXT("dimmed") : TEXT("restored"));
	return N;
}
