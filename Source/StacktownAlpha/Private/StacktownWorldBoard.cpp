#include "StacktownWorldBoard.h"

namespace Stacktown
{
	FPlacementBoard TemporaryBoard()
	{
		FPlacementBoard Board;
		{ FRoad R; R.Id = TEXT("arterial"); R.StartX = -7650.0; R.StartY = 0.0; R.EndX = 7650.0; R.EndY = 0.0; R.SidePlus = TEXT("north"); R.SideMinus = TEXT("south"); R.bAxisX = true; Board.Roads.Add(R); }
		{ FRoad R; R.Id = TEXT("cross"); R.StartX = 0.0; R.StartY = -4230.0; R.EndX = 0.0; R.EndY = 4230.0; R.SidePlus = TEXT("west"); R.SideMinus = TEXT("east"); R.bAxisX = false; Board.Roads.Add(R); }
		return Board;
	}
}
