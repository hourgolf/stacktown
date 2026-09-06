// Ported by reading init_unreal.py's _state_path_source / _sync_parcels. See
// the header for why this one has no runnable oracle.

#include "StacktownStateHandover.h"

namespace Stacktown
{

FStatePathResolution ResolveStatePath(const FStatePathInputs& In)
{
	FStatePathResolution Out;

	// 1. An explicit override wins over everything.
	if (!In.Override.IsEmpty())
	{
		Out.Path = In.Override;
		Out.Source = EStateSource::Override;
		return Out;
	}

	// 2. A live standalone game holds the save. An editor session must not
	//    share the owner's file with it - two drivers on one save is the one
	//    thing the two-process world can do that the single-process one could
	//    not. Only an EDITOR session steps aside; the game process itself is
	//    the legitimate holder.
	if (!In.bIsGameProcess && In.bStandalonePidAlive)
	{
		Out.Path = In.TestStatePath;
		Out.Source = EStateSource::StandaloneLock;
		return Out;
	}

	// 3. The marker. Its CONTENT, if non-empty once trimmed, is the path;
	//    empty or whitespace-only means the test path.
	if (In.bMarkerExists)
	{
		const FString Trimmed = In.MarkerContent.TrimStartAndEnd();
		Out.Path = Trimmed.IsEmpty() ? In.TestStatePath : Trimmed;
		Out.Source = EStateSource::Marker;
		return Out;
	}

	// 4. The owner's real file. See the header: this default is deliberately
	//    the unsafe-looking one, because the alternative put the owner on the
	//    test path.
	Out.Path = In.DefaultStatePath;
	Out.Source = EStateSource::Default;
	return Out;
}

FString StateSourceName(EStateSource Source)
{
	switch (Source)
	{
	case EStateSource::Override:       return TEXT("override");
	case EStateSource::StandaloneLock: return TEXT("standalone-lock");
	case EStateSource::Marker:         return TEXT("marker");
	default:                           return TEXT("default");
	}
}

bool IsPoolLabel(const FString& Label)
{
	return Label.StartsWith(TEXT("POOL_"), ESearchCase::CaseSensitive);
}

FParcelFacts FactsForLabel(const FEconRules& R, const FCityState& State, const FString& Label)
{
	FParcelFacts Facts;
	const FParcelState* P = State.Parcels.Find(Label);
	if (P == nullptr)
	{
		// bFound stays false and every other field stays at its default. The
		// caller must write nothing.
		return Facts;
	}
	Facts.bFound  = true;
	Facts.Rid     = P->Rid;
	Facts.Width   = P->Width;
	Facts.Tier    = P->Tier;
	Facts.bOwned  = P->bOwned;
	Facts.bFailed = P->bFailed;
	Facts.Accum   = P->Accum;
	Facts.bPlaced = P->Placement.IsSet();
	// Recomputed, never read from state: it depends on Tier, and a stored copy
	// is one more thing that can disagree with the tier beside it.
	Facts.Price   = Price(R, P->Tier, P->Width);
	return Facts;
}

} // namespace Stacktown
