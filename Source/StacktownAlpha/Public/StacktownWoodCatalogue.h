#pragma once

#include "CoreMinimal.h"
#include "StacktownEconomyRules.h"

namespace Stacktown
{
	/** The economy's ICatalogue over the wooden catalogue rules: seven tiers
	 *  (0..6) for every recipe, and an asset exists when Catalogue::Resolve
	 *  accepts the tier and width (all 36 masses are baked). */
	struct STACKTOWNALPHA_API FWoodCatalogue : public ICatalogue
	{
		virtual int32   TierCount(const FString& Rid) const override;
		virtual FString AssetName(const FString& Rid, int32 Tier, double Width) const override;
		virtual bool    AssetExists(const FString& Rid, int32 Tier, double Width) const override;
	};
}
