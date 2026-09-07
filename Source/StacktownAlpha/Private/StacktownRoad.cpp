#include "StacktownRoad.h"
#include "StacktownRoadTransform.h"
#include "StacktownPlacement.h"
#include "ProceduralMeshComponent.h"
#include "KismetProceduralMeshLibrary.h"
#include "Materials/MaterialInterface.h"

AStacktownRoad::AStacktownRoad()
{
	PrimaryActorTick.bCanEverTick = false;
	Mesh = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("Road"));
	SetRootComponent(Mesh);
	Mesh->SetMobility(EComponentMobility::Movable);
	Mesh->SetCollisionProfileName(TEXT("BlockAll"));
	Mesh->bUseAsyncCooking = false;
}

static UMaterialInterface* RoadMaterialFor(const FString& WidthClass)
{
	// The design lane's four stains of one stock (2026-09-06 night): MI_road_<class>.
	// An unknown or empty class wears the avenue; if even that is missing, the old inlay.
	// Stacktown::RoadMaterialName is the ONE place MI_road_<type> is formatted -
	// it is the string the oracle checks, so the actor reads it rather than
	// building a second copy that could drift.
	const FString Name = Stacktown::RoadMaterialName(WidthClass);
	if (UMaterialInterface* M = LoadObject<UMaterialInterface>(nullptr, *FString::Printf(TEXT("/Game/Stacktown/Materials/%s.%s"), *Name, *Name))) { return M; }
	if (UMaterialInterface* M = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Stacktown/Materials/MI_road_avenue.MI_road_avenue"))) { return M; }
	return LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Stacktown/Materials/MI_board_road.MI_board_road"));
}

void AStacktownRoad::ShowSegment(const FString& InRoadId, const Stacktown::FRoadSegment& Segment,
	double Width, double TanStart, double TanEnd, double S0, double PathLength)
{
	RoadId = InRoadId;
	WidthClass = Segment.WidthClass;
	if (UMaterialInterface* M = RoadMaterialFor(WidthClass)) { Mesh->SetMaterial(0, M); }

	// The pose is the contract's (StacktownRoadTransform: chord centre, yaw
	// start->end, z = -3 so the 8 uu slab's top is the +1 seam); the geometry
	// is built in that frame - x along the chord, y across, z up - so the
	// corners here are RoadFrame::Corners in local coordinates.
	const Stacktown::RoadFrame::FPose P = Stacktown::RoadFrame::Transform(Segment, Width);
	const double L = FMath::Max(P.Length, 1.0);
	const double H = Width * 0.5;
	const double T = Stacktown::RoadFrame::HeightScale * Stacktown::RoadFrame::CubeEdge * 0.5;

	TArray<FVector> Vertices;
	TArray<int32> Triangles;
	TArray<FVector> Normals;
	TArray<FVector2D> UVs;
	TArray<FProcMeshTangent> Tangents;
	// A box with the stock cube's winding, normals and per-face 0..1 UVs (so the
	// stain reads exactly as it did on the cube), then each end face slid along
	// the chord by H * tan(turn / 2): the +y corner one way, the -y corner the
	// other, which is the bisector cut. A free end (tan 0) stays square.
	UKismetProceduralMeshLibrary::GenerateBoxMesh(FVector(L * 0.5, H, T), Vertices, Triangles, Normals, UVs, Tangents);
	// The stain's UV: U 0..1 over the whole PATH (the stock cube gave a straight
	// road 0..1 over its length, so this is the same stretch, now continuous
	// across a curve's joints), V 0..1 across the carriageway.
	const double Along = FMath::Max(PathLength, L);
	for (int32 i = 0; i < Vertices.Num(); ++i)
	{
		FVector& V = Vertices[i];
		const bool bStart = V.X < 0.0;
		const bool bPlus  = V.Y > 0.0;
		const double Slide = (bStart ? H * TanStart : -H * TanEnd) * (bPlus ? 1.0 : -1.0);
		V.X += Slide;
		if (UVs.IsValidIndex(i))
		{
			UVs[i] = FVector2D((S0 + V.X + L * 0.5) / Along, (V.Y + H) / (2.0 * H));
		}
	}
	const TArray<FLinearColor> NoColors;
	Mesh->CreateMeshSection_LinearColor(0, Vertices, Triangles, Normals, UVs, NoColors, Tangents, /*bCreateCollision*/ true);

	SetActorLocationAndRotation(P.Location, P.Rotation);
	SetActorScale3D(FVector::OneVector);
}

void AStacktownRoad::Show(const FString& InRoadId, double StartX, double StartY, double EndX, double EndY)
{
	Stacktown::FRoadSegment S; S.StartX = StartX; S.StartY = StartY; S.EndX = EndX; S.EndY = EndY;
	ShowSegment(InRoadId, S);
}

void AStacktownRoad::SetGhost(bool bGhost, bool bAccept)
{
	if (!bGhost)
	{
		if (UMaterialInterface* M = RoadMaterialFor(WidthClass)) { Mesh->SetMaterial(0, M); }
	}
	else if (UMaterialInterface* M = LoadObject<UMaterialInterface>(nullptr, bAccept ? TEXT("/Game/Stacktown/Materials/MI_ghost_accept.MI_ghost_accept") : TEXT("/Game/Stacktown/Materials/MI_ghost_refuse.MI_ghost_refuse")))
	{
		Mesh->SetMaterial(0, M);
	}
	Mesh->SetCollisionEnabled(bGhost ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryAndPhysics);
}
