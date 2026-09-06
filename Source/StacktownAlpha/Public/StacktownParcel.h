// AStacktownParcel - Phase 1 step 3 (Docs/PLAN_CPP_PORT.md, Docs/STATE_HANDOVER.md
// Phase A). The C++ base a BP_Parcel is re-parented onto.
//
// WHY THE FACTS ARE UPROPERTYs ON A C++ CLASS. This is the fix for a scar, not a
// style choice. A reflected write to a Blueprint actor re-runs its construction
// script, which resets its non-instance-editable variables - so pushing Owned or
// Tier onto BP_Parcel from outside dropped the highlight and re-resolved the
// mesh as a side effect, and the Python sync had to write on CHANGE ONLY to work
// around it. Facts owned by the C++ class have no construction script behind
// them, so nothing resets and the write-on-change dance stops being load-bearing.
// It is kept anyway below, because avoiding pointless work is still worth doing -
// only now it is an optimisation rather than a correctness crutch.
//
// PHASE A: the parcel READS. The Python driver is still the only writer of the
// city state; this actor takes its facts from UStacktownEconomy's read-only
// mirror. Proof of step 3 is that every standing lot agrees with the Python sync
// in a live game - which the coordinator runs, not this seat.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "StacktownStateHandover.h"
#include "StacktownParcel.generated.h"

class UStacktownEconomy;

UCLASS()
class STACKTOWNALPHA_API AStacktownParcel : public AActor
{
	GENERATED_BODY()

public:
	AStacktownParcel();

	// --- identity, set once by the builder at spawn and never written back ----
	// RecipeId and WidthUU are the actor's OWN immutable identity. The sync
	// reads them to register a lot it has not seen; it must never push them
	// back, or the state and the actor start arguing about who a parcel is.

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Stacktown|Parcel")
	FString RecipeId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Stacktown|Parcel")
	double WidthUU = 0.0;

	// --- facts mirrored from the city state ----------------------------------

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Stacktown|Parcel")
	int32 Tier = 0;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Stacktown|Parcel")
	bool bOwned = false;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Stacktown|Parcel")
	bool bFailed = false;

	/** Recomputed from the ruleset every sync, because it depends on Tier. */
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Stacktown|Parcel")
	double Price = 0.0;

	/** The HUD's growth progress. */
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Stacktown|Parcel")
	double Accum = 0.0;

	/** True for a player-placed lot, false for a pinned one. */
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Stacktown|Parcel")
	bool bPlaced = false;

	/** True once a sync has actually found this parcel in the mirror. Until then
	 *  every field above is a default and NOT a fact - a lot the Python side has
	 *  not registered yet is not a lot whose tier is zero. */
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Stacktown|Parcel")
	bool bSynced = false;

	/** The label this parcel is known by in the city state (queue item 3).
	 *
	 *  A UPROPERTY, not a derived string, because the two sources it used to
	 *  fall back on are both unreliable in the places that matter: an actor
	 *  LABEL does not exist in a cooked build at all, and a NAME is uniquified
	 *  by the engine on spawn, so the second parcel spawned as "P1" quietly
	 *  becomes "P1_2" and stops matching its own entry in the city state. The
	 *  spawner sets this explicitly; the fallbacks stay only for actors placed
	 *  by hand in the editor. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|Parcel")
	FString ParcelId;

	/** ParcelId when it is set, otherwise the actor's label (editor) or name
	 *  (cooked). See ParcelId for why the fallbacks are the weaker answer. */
	UFUNCTION(BlueprintPure, Category = "Stacktown|Parcel")
	FString GetParcelId() const;

	/** Copy the facts for this parcel out of a mirrored state.
	 *
	 *  @return true iff any field actually changed. Dormant POOL_ actors and
	 *  labels absent from the mirror change nothing and return false. */
	bool ApplyFacts(const Stacktown::FParcelFacts& Facts);

	/** Read this parcel's facts from the economy's mirror and apply them. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Parcel")
	bool SyncFromEconomy(UStacktownEconomy* Economy);

	/** Set by the builder when the actor is not a parcel at all but a dormant
	 *  pool member. Derived from the label, cached so the string test is not
	 *  repeated for thirty actors every sync. */
	UFUNCTION(BlueprintPure, Category = "Stacktown|Parcel")
	bool IsDormantPoolActor() const;
};
