#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "StacktownEconomyRules.h"
#include "StacktownRoad.generated.h"

class UStaticMeshComponent;

/** A drawn road in C++: the pool road's look (a stock cube in the studio grey)
 *  at StacktownRoadTransform's pose. Identity is the RoadId property, never a label. */
UCLASS()
class STACKTOWNALPHA_API AStacktownRoad : public AActor
{
	GENERATED_BODY()

public:
	AStacktownRoad();

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Stacktown|Road")
	FString RoadId;
	/** The segment's width class (dirt | avenue | boulevard | highway): picks MI_road_<class>. */
	UPROPERTY(VisibleInstanceOnly, Category = "Stacktown|Road")
	FString WidthClass;

	/** Pose the road for a segment. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Road")
	void Show(const FString& InRoadId, double StartX, double StartY, double EndX, double EndY);

	/** Preview look (accept / refuse) for the drawing ghost; false restores the road look. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Road")
	void SetGhost(bool bGhost, bool bAccept);

	void ShowSegment(const FString& InRoadId, const Stacktown::FRoadSegment& Segment);

private:
	UPROPERTY(VisibleAnywhere, Category = "Stacktown|Road")
	TObjectPtr<UStaticMeshComponent> Mesh;
};
