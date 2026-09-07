#include "StacktownRoad.h"
#include "StacktownRoadTransform.h"
#include "StacktownPlacement.h"
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
	// Stacktown::RoadMaterialName is the ONE place MI_road_<type> is formatted -
	// it is the string the oracle checks, so the actor reads it rather than
	// building a second copy that could drift.
	const FString Name = Stacktown::RoadMaterialName(WidthClass);
	if (UMaterialInterface* M = LoadObject<UMaterialInterface>(nullptr, *FString::Printf(TEXT("/Game/Stacktown/Materials/%s.%s"), *Name, *Name))) { return M; }
	if (UMaterialInterface* M = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Stacktown/Materials/MI_road_avenue.MI_road_avenue"))) { return M; }
	return LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Stacktown/Materials/MI_board_road.MI_board_road"));
}

void AStacktownRoad::ShowSegment(const FString& InRoadId, const Stacktown::FRoadSegment& Segment,
	double CorridorWidth)
{
	RoadId = InRoadId;
	WidthClass = Segment.WidthClass;
	if (UMaterialInterface* M = RoadMaterialFor(WidthClass)) { Mesh->SetMaterial(0, M); }
	Stacktown::RoadFrame::FPose P = Stacktown::RoadFrame::Transform(Segment, CorridorWidth);
	if (!Segment.Path.IsEmpty())
	{
		// A CHORD of a curved road (the seat's DrawRoadPath): a full-width slab 410 long
		// fans open on the outside of a bend and shows wedge gaps (frame 23:40). The
		// design lane's road language is a fitted polyline with JOINTS visible, not
		// gaps, so each chord runs half a corridor past both ends - consecutive pieces
		// overlap into one ribbon - and sits a hair higher than the one before, so the
		// overlaps never fight. The seam between pieces stays as the cut.
		// 300 uu past each end closes the outside wedge of a ~30 degree bend between
		// 410 chords; half a corridor (frame 23:42) fattened the whole curve into a slab.
		P.Scale.X += 600.0 / 100.0;
		int32 Index = 0;
		FString Digits; for (const TCHAR C : InRoadId) { if (FChar::IsDigit(C)) { Digits.AppendChar(C); } }
		Index = Digits.IsEmpty() ? 0 : FCString::Atoi(*Digits);
		P.Location.Z += 0.02 * (double)(Index % 64);
	}
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
