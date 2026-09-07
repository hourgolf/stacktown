#include "StacktownRoadTransform.h"

namespace Stacktown
{
namespace RoadFrame
{
	FPose Transform(const FRoadSegment& S, double CorridorWidth)
	{
		FPose P;
		const double Dx = S.EndX - S.StartX, Dy = S.EndY - S.StartY;
		P.Length = FMath::Sqrt(Dx * Dx + Dy * Dy);
		P.Location = FVector((S.StartX + S.EndX) * 0.5, (S.StartY + S.EndY) * 0.5, RoadZ);
		P.Rotation = FRotator(0.0, FMath::RadiansToDegrees(FMath::Atan2(Dy, Dx)), 0.0);
		P.Scale = FVector(FMath::Max(P.Length, 1.0) / CubeEdge, CorridorWidth / CubeEdge, HeightScale);
		return P;
	}

	FVector2D Direction(const FRoadSegment& S)
	{
		const FVector2D D(S.EndX - S.StartX, S.EndY - S.StartY);
		const double Len = D.Size();
		return Len > UE_KINDA_SMALL_NUMBER ? D / Len : FVector2D::ZeroVector;
	}

	double JointTangent(const FVector2D& DirIn, const FVector2D& DirOut)
	{
		if (DirIn.IsNearlyZero() || DirOut.IsNearlyZero()) { return 0.0; }
		// The signed turn, in the sense FRotator's yaw turns: +x rotated toward
		// +y is positive, and a chord's +y side is (-d.y, d.x) - the axis the
		// actor's yaw puts its local y on, so the corner arithmetic in Corners
		// and the mesh agree without a second convention.
		const double Cross = DirIn.X * DirOut.Y - DirIn.Y * DirOut.X;
		const double Dot   = DirIn.X * DirOut.X + DirIn.Y * DirOut.Y;
		const double Turn  = FMath::Atan2(Cross, Dot);
		return FMath::Clamp(FMath::Tan(Turn * 0.5), -MitreLimit, MitreLimit);
	}

	void Corners(const FRoadSegment& S, double Width, double TanStart, double TanEnd, FVector2D Out[4])
	{
		const FVector2D C((S.StartX + S.EndX) * 0.5, (S.StartY + S.EndY) * 0.5);
		const FVector2D D = Direction(S);
		const FVector2D N(-D.Y, D.X);
		const double H = Width * 0.5;
		const double L = FVector2D(S.EndX - S.StartX, S.EndY - S.StartY).Size();
		// A joint's bisector leans the cut by half the turn: the +y corner slides
		// along the chord by H * tan(turn/2) and the -y corner the other way.
		Out[0] = C + D * (-L * 0.5 + H * TanStart) + N * H;
		Out[1] = C + D * (-L * 0.5 - H * TanStart) - N * H;
		Out[2] = C + D * ( L * 0.5 + H * TanEnd)   - N * H;
		Out[3] = C + D * ( L * 0.5 - H * TanEnd)   + N * H;
	}

	TArray<FJoint> ChainJoints(const TArray<FRoadSegment>& Chords)
	{
		TArray<FJoint> Out;
		Out.SetNum(Chords.Num());
		double S = 0.0;
		for (int32 i = 0; i < Chords.Num(); ++i)
		{
			Out[i].S0 = S;
			S += FVector2D(Chords[i].EndX - Chords[i].StartX, Chords[i].EndY - Chords[i].StartY).Size();
		}
		for (FJoint& J : Out) { J.PathLength = S; }
		for (int32 i = 0; i + 1 < Chords.Num(); ++i)
		{
			const FRoadSegment& A = Chords[i];
			const FRoadSegment& B = Chords[i + 1];
			if (!FMath::IsNearlyEqual(A.EndX, B.StartX, 1.0) || !FMath::IsNearlyEqual(A.EndY, B.StartY, 1.0)) { continue; }
			const double T = JointTangent(Direction(A), Direction(B));
			Out[i].TanEnd = T;
			Out[i + 1].TanStart = T;
		}
		return Out;
	}

	static int64 IdNumber(const FString& Id)
	{
		FString Digits;
		for (const TCHAR C : Id) { if (FChar::IsDigit(C)) { Digits.AppendChar(C); } }
		return Digits.IsEmpty() ? 0 : FCString::Atoi64(*Digits);
	}

	TMap<FString, FJoint> PathJoints(const TMap<FString, FRoadSegment>& Roads)
	{
		TMap<FString, TArray<FString>> ByPath;
		for (const auto& Pair : Roads)
		{
			ByPath.FindOrAdd(Pair.Value.Path.IsEmpty() ? Pair.Key : Pair.Value.Path).Add(Pair.Key);
		}
		TMap<FString, FJoint> Out;
		for (auto& Pair : ByPath)
		{
			TArray<FString>& Ids = Pair.Value;
			Ids.Sort([](const FString& A, const FString& B)
			{
				const int64 NA = IdNumber(A), NB = IdNumber(B);
				return NA != NB ? NA < NB : A < B;
			});
			TArray<FRoadSegment> Chords;
			for (const FString& Id : Ids) { Chords.Add(Roads[Id]); }
			const TArray<FJoint> J = ChainJoints(Chords);
			for (int32 i = 0; i < Ids.Num(); ++i) { Out.Add(Ids[i], J[i]); }
		}
		return Out;
	}
}
}
