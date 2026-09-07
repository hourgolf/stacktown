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
	bool ShowPad(double Width, FString& OutError, bool bScored = false);

	/** The four thin bars of a scored (for-sale) outline; cleared when the lot shows anything else. */
	UPROPERTY() TArray<TObjectPtr<UStaticMeshComponent>> ScoreBars;
	void ClearScoreBars();

	/** The per-instance state channels the wood master reads (Content/Python/cpdmap.py is
	 *  the one authority; the values are the Python driver's, init_unreal.py):
	 *    0 Age        oxidation 0..1 along the species curve
	 *    1 GlowLevel  night window emission - 0.45 owned (D24 ladder, GlowScale 40), 0 for sale (D20: bare board)
	 *    2 GlowState  encoded hue, 0.5 neutral warm until the economy can say activity
	 *    4 Attention 0 today
	 *    5 Failure    0.6 x wear (weathers toward the species grey as the lot wears), 0.8 worn out (chars) until repaired
	 *    6 Scorch     0 today
	 *  Found by the design lane's night frame (2026-09-06 16:02): channels 1 and 2 were
	 *  READ by the material and WRITTEN by nothing in C++, so every window was black. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Lot")
	void ApplyState(bool bOwned, float Age, float Wear01 = 0.f, bool bFailed = false);

	/** Selection: cpdmap channel 3 (reserved, the material does not draw it) plus custom
	 *  depth for the renderer outline the design lane ruled (post-process, accept #C08A4E). */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Lot")
	void SetSelected(bool bSelected);

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Stacktown|Lot")
	FString ShownAsset;
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Stacktown|Lot")
	FString ShownSpecies;
};
