#include "StacktownParcel.h"

#include "StacktownAlpha.h"
#include "StacktownEconomy.h"

AStacktownParcel::AStacktownParcel()
{
	// Nothing to tick: a parcel is synced by the driver, not by itself. The
	// per-parcel call-out-at-BeginPlay design was tried and is permanently
	// impossible here; one driver pushing to many actors is what works.
	PrimaryActorTick.bCanEverTick = false;
}

FString AStacktownParcel::GetParcelId() const
{
#if WITH_EDITOR
	return GetActorLabel();
#else
	// A cooked build has no actor labels. The name is what survives, and the
	// builder sets it to the same id in both cases.
	return GetName();
#endif
}

bool AStacktownParcel::IsDormantPoolActor() const
{
	return Stacktown::IsPoolLabel(GetParcelId());
}

bool AStacktownParcel::ApplyFacts(const Stacktown::FParcelFacts& Facts)
{
	if (!Facts.bFound)
	{
		// Absent from the mirror. Writing defaults here would show a registered
		// lot as an unowned tier-0 one, which is a lie that looks like data.
		return false;
	}

	bool bChanged = false;
	// Write-on-change. No longer required for correctness now that these are C++
	// UPROPERTYs with no construction script behind them, but still worth not
	// doing pointless work for every parcel every sync.
	if (Tier != Facts.Tier)         { Tier = Facts.Tier;        bChanged = true; }
	if (bOwned != Facts.bOwned)     { bOwned = Facts.bOwned;    bChanged = true; }
	if (bFailed != Facts.bFailed)   { bFailed = Facts.bFailed;  bChanged = true; }
	if (bPlaced != Facts.bPlaced)   { bPlaced = Facts.bPlaced;  bChanged = true; }
	if (Price != Facts.Price)       { Price = Facts.Price;      bChanged = true; }
	if (Accum != Facts.Accum)       { Accum = Facts.Accum;      bChanged = true; }
	if (!bSynced)                   { bSynced = true;           bChanged = true; }

	// RecipeId and WidthUU are deliberately NOT written: they are this actor's
	// own identity, and the state's copies came from it in the first place.
	return bChanged;
}

bool AStacktownParcel::SyncFromEconomy(UStacktownEconomy* Economy)
{
	if (Economy == nullptr)
	{
		return false;
	}
	if (IsDormantPoolActor())
	{
		// Not a parcel. Skipped before anything can register or push onto it.
		return false;
	}
	const Stacktown::FParcelFacts Facts =
		Stacktown::FactsForLabel(Economy->GetRules(), Economy->GetState(), GetParcelId());
	if (!Facts.bFound)
	{
		UE_LOG(LogStacktown, Verbose,
			TEXT("parcel '%s' is not in the mirrored state yet"), *GetParcelId());
		return false;
	}
	return ApplyFacts(Facts);
}
