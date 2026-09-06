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
	if (UMaterialInterface* Grey = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Stacktown/Materials/MI_studio_grey.MI_studio_grey")))
	{
		Mesh->SetMaterial(0, Grey);
	}
}

void AStacktownRoad::ShowSegment(const FString& InRoadId, const Stacktown::FRoadSegment& Segment)
{
	RoadId = InRoadId;
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
	const TCHAR* Path = !bGhost ? TEXT("/Game/Stacktown/Materials/MI_studio_grey.MI_studio_grey")
		: (bAccept ? TEXT("/Game/Stacktown/Materials/MI_ghost_accept.MI_ghost_accept") : TEXT("/Game/Stacktown/Materials/MI_ghost_refuse.MI_ghost_refuse"));
	if (UMaterialInterface* M = LoadObject<UMaterialInterface>(nullptr, Path))
	{
		Mesh->SetMaterial(0, M);
	}
	Mesh->SetCollisionEnabled(bGhost ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryAndPhysics);
}
