#include "StacktownWoodCatalogue.h"
#include "StacktownCatalogue.h"

namespace Stacktown
{
	int32 FWoodCatalogue::TierCount(const FString& Rid) const { return 7; }

	FString FWoodCatalogue::AssetName(const FString& Rid, int32 Tier, double Width) const
	{
		const Catalogue::FResolved R = Catalogue::Resolve(Rid, Tier, Width, false);
		return R.bOk ? R.Asset : FString();
	}

	bool FWoodCatalogue::AssetExists(const FString& Rid, int32 Tier, double Width) const
	{
		return Catalogue::Resolve(Rid, Tier, Width, false).bOk;
	}
}
