#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "StacktownEconomyRules.h"
#include "StacktownRoadTransform.h"
#include "StacktownRoad.generated.h"

class UProceduralMeshComponent;

/** A drawn road in C++: one chord of a path as a mitred slab, the carriageway
 *  wide and 8 uu thick, flush with the plate, in the stain for its type
 *  (MI_road_<class>). Identity is the RoadId property, never a label.
 *
 *  Why a procedural mesh and not the stock cube (2026-09-07): the design lane
 *  ruled a curve's chords must MITRE - each end cut along the bisector of the
 *  turn into the next chord so consecutive chords share an edge - and a cube
 *  cannot be cut on the bias by scale and rotation alone. */
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

	/** Pose the road for a straight, square-ended segment at the avenue's width. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Road")
	void Show(const FString& InRoadId, double StartX, double StartY, double EndX, double EndY);

	/** Preview look (accept / refuse) for the drawing ghost; false restores the road look. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Road")
	void SetGhost(bool bGhost, bool bAccept);

	/** `Width` is what the slab is drawn across: Stacktown::RoadCarriageway for
	 *  the segment's own type (the verge either side is bare plate). `TanStart`
	 *  and `TanEnd` are Stacktown::RoadFrame::JointTangent at each end - the
	 *  same number the neighbouring chord was given for that joint - and 0 for
	 *  a free end, which is cut square. */
	void ShowSegment(const FString& InRoadId, const Stacktown::FRoadSegment& Segment,
		double Width = Stacktown::RoadFrame::Carriageway, double TanStart = 0.0, double TanEnd = 0.0);

private:
	UPROPERTY(VisibleAnywhere, Category = "Stacktown|Road")
	TObjectPtr<UProceduralMeshComponent> Mesh;
};
