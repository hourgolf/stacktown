#include "StacktownCatalogue.h"

namespace Stacktown
{
namespace Catalogue
{
	static const TCHAR* GSpecies[NumSpecies] = { TEXT("maple"), TEXT("pine"), TEXT("ash"), TEXT("oak"), TEXT("cherry"), TEXT("sapele"), TEXT("walnut") };
	static const double GWidths[5] = { 820.0, 1230.0, 1640.0, 2050.0, 2460.0 };

	const TCHAR* SpeciesName(int32 Index)
	{
		return (Index >= 0 && Index < NumSpecies) ? GSpecies[Index] : TEXT("");
	}

	uint32 Crc32(const FString& Ascii)
	{
		static uint32 Table[256];
		static bool bInit = false;
		if (!bInit)
		{
			for (uint32 i = 0; i < 256; ++i)
			{
				uint32 C = i;
				for (int32 k = 0; k < 8; ++k) { C = (C & 1u) ? (0xEDB88320u ^ (C >> 1)) : (C >> 1); }
				Table[i] = C;
			}
			bInit = true;
		}
		uint32 Crc = 0xFFFFFFFFu;
		for (int32 i = 0; i < Ascii.Len(); ++i)
		{
			const uint8 B = (uint8)(Ascii[i] & 0xFF);   // rids are ASCII; Python encodes them as UTF-8 bytes
			Crc = Table[(Crc ^ B) & 0xFFu] ^ (Crc >> 8);
		}
		return Crc ^ 0xFFFFFFFFu;
	}

	FString SpeciesFor(const FString& Rid)
	{
		return GSpecies[Crc32(Rid) % NumSpecies];
	}

	bool BandForTier(int32 Tier, FString& OutBand)
	{
		switch (Tier)
		{
		case 0: case 1: OutBand = TEXT("flat"); return true;
		case 2: case 3: OutBand = TEXT("setback1"); return true;
		case 4: case 5: OutBand = TEXT("setback2"); return true;
		case 6: OutBand = TEXT("tower"); return true;
		default: OutBand.Reset(); return false;
		}
	}

	bool NearestWidth(double Width, double& OutWidth)
	{
		double Best = GWidths[0];
		for (double W : GWidths) { if (FMath::Abs(W - Width) < FMath::Abs(Best - Width)) { Best = W; } }
		OutWidth = Best;
		return FMath::Abs(Best - Width) <= 1.0;
	}

	bool HasCornerMass(double LadderWidth)
	{
		return LadderWidth == 1230.0 || LadderWidth == 1640.0 || LadderWidth == 2050.0 || LadderWidth == 2460.0;
	}

	FString AssetName(double LadderWidth, const FString& Band, bool bCorner)
	{
		return FString::Printf(TEXT("SM_WMass_w%d_%s%s"), (int32)FMath::RoundToDouble(LadderWidth), *Band, bCorner ? TEXT("_d1500") : TEXT(""));
	}

	FString MassAssetPath(const FString& Name)
	{
		return FString::Printf(TEXT("/Game/Stacktown/BakedWood/%s.%s"), *Name, *Name);
	}

	FString SpeciesMaterialPath(const FString& Species)
	{
		return FString::Printf(TEXT("/Game/Stacktown/Materials/MI_wood_%s.MI_wood_%s"), *Species, *Species);
	}

	FResolved Resolve(const FString& Rid, int32 Tier, double Width, bool bCorner)
	{
		FResolved R;
		if (!BandForTier(Tier, R.Band))
		{
			R.Error = FString::Printf(TEXT("tier %d outside the flagship ladder 0..6"), Tier);
			return R;
		}
		if (!NearestWidth(Width, R.Width))
		{
			R.Error = FString::Printf(TEXT("width %.0f is not on the ladder 820/1230/1640/2050/2460"), Width);
			return R;
		}
		if (bCorner && !HasCornerMass(R.Width))
		{
			R.Error = FString::Printf(TEXT("corner lot at width %.0f - no deep mass is baked for it"), R.Width);
			return R;
		}
		R.bCorner = bCorner;
		R.Depth = bCorner ? 1500.0 : 700.0;
		R.Species = SpeciesFor(Rid);
		R.Asset = AssetName(R.Width, R.Band, bCorner);
		R.bOk = true;
		return R;
	}
}
}
