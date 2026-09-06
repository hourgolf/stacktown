#pragma once

// The wooden catalogue as pure rules (Content/Python/woodmap.py is the oracle):
// a recipe id picks a species by CRC-32 (D3: tone is identity - a building
// never repaints itself when it gains a storey), a tier picks a band, a width
// snaps to the five-rung ladder, and the mass asset name follows from those.
// Nothing here loads an asset; the paths are strings for the caller to load.

#include "CoreMinimal.h"

namespace Stacktown
{
namespace Catalogue
{
	static constexpr int32 NumSpecies = 7;
	STACKTOWNALPHA_API const TCHAR* SpeciesName(int32 Index);

	/** zlib's CRC-32 (IEEE polynomial, reflected), the same bits Python's zlib.crc32 returns. */
	STACKTOWNALPHA_API uint32 Crc32(const FString& Ascii);

	/** SPECIES[crc32(rid) % 7]. */
	STACKTOWNALPHA_API FString SpeciesFor(const FString& Rid);

	/** flat / setback1 / setback2 / tower for tiers 0..6; false outside the ladder. */
	STACKTOWNALPHA_API bool BandForTier(int32 Tier, FString& OutBand);

	/** The ladder rung nearest to Width; false when it is more than 1 uu off any rung. */
	STACKTOWNALPHA_API bool NearestWidth(double Width, double& OutWidth);

	/** True for the widths that have a deep (1500) corner mass baked: 1230, 1640, 2050, 2460. */
	STACKTOWNALPHA_API bool HasCornerMass(double LadderWidth);

	/** SM_WMass_w<width>_<band>[_d1500] */
	STACKTOWNALPHA_API FString AssetName(double LadderWidth, const FString& Band, bool bCorner);

	STACKTOWNALPHA_API FString MassAssetPath(const FString& AssetName);        // /Game/Stacktown/BakedWood/<n>.<n>
	STACKTOWNALPHA_API FString SpeciesMaterialPath(const FString& Species);    // /Game/Stacktown/Materials/MI_wood_<s>.MI_wood_<s>

	struct STACKTOWNALPHA_API FResolved
	{
		bool    bOk = false;
		FString Error;
		FString Asset;
		FString Species;
		FString Band;
		double  Width = 0.0;
		double  Depth = 700.0;
		bool    bCorner = false;
	};

	/** woodmap.resolve(rid, tier, width, corner): errors rather than guesses. */
	STACKTOWNALPHA_API FResolved Resolve(const FString& Rid, int32 Tier, double Width, bool bCorner);
}
}
