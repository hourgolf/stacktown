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

bool ResolvePythonDrivers(const FPythonDriversInputs& In)
{
	// No plugin, no drivers - checked FIRST so no ini or environment value can
	// claim a packaged app still has Python in it.
	if (!In.bPluginLoaded)
	{
		return false;
	}
	if (!In.EnvValue.IsEmpty())
	{
		return !(In.EnvValue == TEXT("0")
			|| In.EnvValue.Equals(TEXT("false"), ESearchCase::IgnoreCase)
			|| In.EnvValue.Equals(TEXT("no"), ESearchCase::IgnoreCase));
	}
	if (In.bFoundInNewSection)
	{
		return In.bNewSectionValue;
	}
	if (In.bFoundInLegacySection)
	{
		return In.bLegacySectionValue;
	}
	// Default ON: the Python drivers were the world before Phase B, and a
	// missing key must not silently switch a session's owner.
	return true;
}

int32 ParseSlot(const FString& Text)
{
	// Digits only, read by hand over the raw characters: this file compiles
	// under the host pre-flight's mock CoreMinimal, which has no FCString, no
	// range-for and no FindLastChar.
	const TCHAR* S = *Text;
	const int32 Len = Text.Len();
	int32 N = 0;
	bool bAny = false;
	for (int32 i = 0; i < Len; ++i)
	{
		const TCHAR C = S[i];
		if (C >= TEXT('0') && C <= TEXT('9')) { N = N * 10 + (int32)(C - TEXT('0')); bAny = true; if (N > 9) { break; } }
		else if (bAny) { break; }
	}
	return (bAny && N >= 1 && N <= SlotCount) ? N : 1;
}

FString SlotStatePath(const FString& Path, int32 Slot)
{
	if (Slot < 2 || Slot > SlotCount) { return Path; }
	const TCHAR* S = *Path;
	const int32 Len = Path.Len();
	int32 Dot = -1;
	int32 Slash = -1;
	for (int32 i = 0; i < Len; ++i)
	{
		if (S[i] == TEXT('.')) { Dot = i; }
		else if (S[i] == TEXT('/')) { Slash = i; }
	}
	const bool bHasExt = Dot >= 0 && Dot > Slash;
	const FString Stem = bHasExt ? Path.Left(Dot) : Path;
	const FString Ext  = bHasExt ? Path.Mid(Dot) : FString();
	return FString::Printf(TEXT("%s_s%d%s"), *Stem, Slot, *Ext);
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
	Facts.Price   = PriceFor(R, P->Rid, P->Tier, P->Width);
	return Facts;
}

} // namespace Stacktown
