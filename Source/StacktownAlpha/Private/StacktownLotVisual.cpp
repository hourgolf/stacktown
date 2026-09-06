#include "StacktownLotVisual.h"
#include "StacktownAlpha.h"
#include "StacktownCatalogue.h"
#include "StacktownLotTransform.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"

UStacktownLotVisual::UStacktownLotVisual()
{
	SetMobility(EComponentMobility::Movable);
	SetCollisionProfileName(TEXT("BlockAll"));
	SetGenerateOverlapEvents(false);
}

bool UStacktownLotVisual::ShowMass(const FString& Rid, int32 Tier, double Width, bool bCorner, FString& OutError)
{
	const Stacktown::Catalogue::FResolved R = Stacktown::Catalogue::Resolve(Rid, Tier, Width, bCorner);
	if (!R.bOk)
	{
		OutError = R.Error;
		return false;
	}
	UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, *Stacktown::Catalogue::MassAssetPath(R.Asset));
	if (!Mesh)
	{
		OutError = FString::Printf(TEXT("mass asset missing: %s"), *Stacktown::Catalogue::MassAssetPath(R.Asset));
		return false;
	}
	UMaterialInterface* Mat = LoadObject<UMaterialInterface>(nullptr, *Stacktown::Catalogue::SpeciesMaterialPath(R.Species));
	if (!Mat)
	{
		OutError = FString::Printf(TEXT("species material missing: %s"), *Stacktown::Catalogue::SpeciesMaterialPath(R.Species));
		return false;
	}
	SetStaticMesh(Mesh);
	for (int32 i = 0; i < GetNumMaterials(); ++i)
	{
		SetMaterial(i, Mat);
	}
	SetRelativeLocation(Stacktown::LotFrame::MassOffset());
	ShownAsset = R.Asset;
	ShownSpecies = R.Species;
	return true;
}

bool UStacktownLotVisual::ShowPad(double Width, FString& OutError)
{
	double W;
	if (!Stacktown::Catalogue::NearestWidth(Width, W))
	{
		OutError = FString::Printf(TEXT("width %.0f is not on the ladder"), Width);
		return false;
	}
	const FString Path = FString::Printf(TEXT("/Game/Stacktown/BakedWood/SM_GhostPad_w%d.SM_GhostPad_w%d"), (int32)W, (int32)W);
	UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, *Path);
	if (!Mesh)
	{
		OutError = FString::Printf(TEXT("pad asset missing: %s"), *Path);
		return false;
	}
	UMaterialInterface* Mat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Stacktown/Materials/MI_ghost_accept.MI_ghost_accept"));
	SetStaticMesh(Mesh);
	if (Mat) { for (int32 i = 0; i < GetNumMaterials(); ++i) { SetMaterial(i, Mat); } }
	SetRelativeLocation(Stacktown::LotFrame::PadOffset(W));
	ShownAsset = FString::Printf(TEXT("SM_GhostPad_w%d"), (int32)W);
	ShownSpecies.Reset();
	return true;
}
