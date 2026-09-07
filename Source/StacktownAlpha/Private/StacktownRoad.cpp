#include "StacktownRoad.h"
#include "StacktownRoadTransform.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"

AStacktownRoad::AStacktownRoad()
{
	PrimaryActorTick.bCanEverTick = false;
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Road"));
	SetRootComponent(Mesh);
	Mesh->SetMobility(EComponentMobility::Movable);
	Mesh->SetCollisionProfileName(TEXT("BlockAll"));
	if (UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")))
	{
		Mesh->SetStaticMesh(Cube);
	}
	if (UMaterialInterface* Grey = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Stacktown/Materials/MI_board_road.MI_board_road")))
	{
		Mesh->SetMaterial(0, Grey);
	}
}

static UMaterialInterface* RoadMaterialFor(const FString& WidthClass)
{
	// The design lane's four stains of one stock (2026-09-06 night): MI_road_<class>.
	// An unknown or empty class wears the avenue; if even that is missing, the old inlay.
	const FString Class = WidthClass.IsEmpty() ? TEXT("avenue") : WidthClass.ToLower();
	if (UMaterialInterface* M = LoadObject<UMaterialInterface>(nullptr, *FString::Printf(TEXT("/Game/Stacktown/Materials/MI_road_%s.MI_road_%s"), *Class, *Class))) { return M; }
	if (UMaterialInterface* M = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Stacktown/Materials/MI_road_avenue.MI_road_avenue"))) { return M; }
	return LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Stacktown/Materials/MI_board_road.MI_board_road"));
}

void AStacktownRoad::ShowSegment(const FString& InRoadId, const Stacktown::FRoadSegment& Segment)
{
	RoadId = InRoadId;
	WidthClass = Segment.WidthClass;
	if (UMaterialInterface* M = RoadMaterialFor(WidthClass)) { Mesh->SetMaterial(0, M); }
	const Stacktown::RoadFrame::FPose P = Stacktown::RoadFrame::Transform(Segment);
	SetActorLocationAndRotation(P.Location, P.Rotation);
	SetActorScale3D(P.Scale);
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
