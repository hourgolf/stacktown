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
	ClearScoreBars();
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

bool UStacktownLotVisual::ShowPad(double Width, FString& OutError, bool bScored)
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
	if (bScored)
	{
		// Design lane 22:00: a FOR-SALE lot is a standing fact, not a preview - a scored
		// outline and no fill, the maker's knife-mark where a block will go. Four thin
		// bars of the engine cube around the pad's footprint; the line wears the lane's
		// MI_pad_score when it exists, else the darkest road stain.
		ClearScoreBars();
		UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
		UMaterialInterface* Line = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Stacktown/Materials/MI_pad_score.MI_pad_score"));
		if (!Line) { Line = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Stacktown/Materials/MI_road_highway.MI_road_highway")); }
		if (!Cube) { OutError = TEXT("engine cube missing"); return false; }
		const FVector Ext = Mesh->GetBounds().BoxExtent;   // the pad's footprint, from the pad mesh itself
		SetStaticMesh(nullptr);
		SetRelativeLocation(Stacktown::LotFrame::PadOffset(W));
		const double Lw = 12.0, Lz = 3.0;                  // a fine line, 12 uu wide, 3 uu proud
		const double Hx = Ext.X, Hy = Ext.Y;
		const struct { FVector C; FVector S; } Bars[4] = {
			{ FVector( 0.0,  Hy, 0.0), FVector(2.0 * Hx / 100.0, Lw / 100.0, Lz / 100.0) },
			{ FVector( 0.0, -Hy, 0.0), FVector(2.0 * Hx / 100.0, Lw / 100.0, Lz / 100.0) },
			{ FVector( Hx,  0.0, 0.0), FVector(Lw / 100.0, 2.0 * Hy / 100.0, Lz / 100.0) },
			{ FVector(-Hx,  0.0, 0.0), FVector(Lw / 100.0, 2.0 * Hy / 100.0, Lz / 100.0) } };
		for (int32 i = 0; i < 4; ++i)
		{
			UStaticMeshComponent* Bar = NewObject<UStaticMeshComponent>(GetOwner());
			Bar->SetStaticMesh(Cube);
			if (Line) { Bar->SetMaterial(0, Line); }
			Bar->SetCollisionProfileName(TEXT("BlockAll"));
			Bar->SetMobility(EComponentMobility::Movable);
			Bar->AttachToComponent(this, FAttachmentTransformRules::KeepRelativeTransform);
			Bar->SetRelativeLocation(Bars[i].C + FVector(0.0, 0.0, Lz * 0.5));
			Bar->SetRelativeScale3D(Bars[i].S);
			Bar->RegisterComponent();
			ScoreBars.Add(Bar);
		}
		ShownAsset = FString::Printf(TEXT("SCORED_w%d"), (int32)W);
		ShownSpecies.Reset();
		return true;
	}
	ClearScoreBars();
	UMaterialInterface* Mat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Stacktown/Materials/MI_ghost_accept.MI_ghost_accept"));
	SetStaticMesh(Mesh);
	if (Mat) { for (int32 i = 0; i < GetNumMaterials(); ++i) { SetMaterial(i, Mat); } }
	SetRelativeLocation(Stacktown::LotFrame::PadOffset(W));
	ShownAsset = FString::Printf(TEXT("SM_GhostPad_w%d"), (int32)W);
	ShownSpecies.Reset();
	return true;
}

void UStacktownLotVisual::ApplyState(bool bOwned, float Age, float Wear01, bool bFailed)
{
	// Written through the function, never the property: the shader reads the runtime
	// per-instance array, which only SetCustomPrimitiveDataFloat sets (the Python
	// driver's own hard-won note). Same-value writes are cheap; re-applied every reconcile
	// so a mesh swap (ShowMass on a tier-up) can never leave the channels behind.
	SetCustomPrimitiveDataFloat(0, FMath::Clamp(Age, 0.f, 1.f));
	SetCustomPrimitiveDataFloat(1, bOwned ? 0.45f : 0.f);
	SetCustomPrimitiveDataFloat(2, 0.5f);
	SetCustomPrimitiveDataFloat(4, 0.f);
	// cpdmap channel 5: 0 -> 0.6 weathers toward this species' grey, 0.6 -> 1 chars. A
	// lot greys as it wears (a stranger sees decay coming) and chars when worn out.
	// Design lane 22:00: 0.6 for a newly failed lot (D16's boundary: the most degraded a
	// mass can look and still be weathered wood), climbing to 0.8 (char) the longer it is
	// left - Wear01 runs past 1.0 while failed. Before failure it greys as 0.6 x wear.
	const float Failure = bFailed ? 0.6f + 0.2f * FMath::Clamp(Wear01 - 1.f, 0.f, 1.f) : 0.6f * FMath::Clamp(Wear01, 0.f, 1.f);
	SetCustomPrimitiveDataFloat(5, Failure);
	SetCustomPrimitiveDataFloat(6, 0.f);
}

void UStacktownLotVisual::SetSelected(bool bSelected)
{
	SetCustomPrimitiveDataFloat(3, bSelected ? 1.f : 0.f);
	SetRenderCustomDepth(bSelected);
	SetCustomDepthStencilValue(bSelected ? 1 : 0);
}

void UStacktownLotVisual::ClearScoreBars()
{
	for (UStaticMeshComponent* Bar : ScoreBars) { if (Bar) { Bar->DestroyComponent(); } }
	ScoreBars.Reset();
}
