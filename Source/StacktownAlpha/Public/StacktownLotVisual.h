#pragma once

#include "CoreMinimal.h"
#include "Components/StaticMeshComponent.h"
#include "StacktownLotVisual.generated.h"

/**
 * The visible side of a lot in C++: loads the wooden mass for (recipe, tier,
 * width, corner) and the species material from Stacktown::Catalogue, and
 * carries the mesh's own local offset (StacktownLotTransform: a mass sits 750
 * toward the road; the placeholder pad half a width along +x). Any actor can
 * own one; AStacktownParcel will, at the actor swap.
 */
UCLASS(ClassGroup = (Stacktown), meta = (BlueprintSpawnableComponent))
class STACKTOWNALPHA_API UStacktownLotVisual : public UStaticMeshComponent
{
	GENERATED_BODY()

public:
	UStacktownLotVisual();

	/** Load and apply the mass and its species material. Returns false, with a reason, when the catalogue refuses or an asset is missing. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Lot")
	bool ShowMass(const FString& Rid, int32 Tier, double Width, bool bCorner, FString& OutError);

	/** The uncarved pad for an unbought lot: the ghost pad mesh for the width, offset half a width along +x. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Lot")
	bool ShowPad(double Width, FString& OutError);

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Stacktown|Lot")
	FString ShownAsset;
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Stacktown|Lot")
	FString ShownSpecies;
};
