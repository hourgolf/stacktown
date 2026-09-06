#pragma once

// Pure camera arithmetic for the Stacktown camera (Docs/PLAN_CPP_PORT.md §6).
// No UObject, no engine state: every rule the pawn applies lives here so the
// automation tests (Stacktown.Camera.*) and the seat's pre-flight can run it.
//
// Pose: a focus point on the board plane (z = 0), a yaw and a pitch in
// degrees, and a distance along the view ray. The camera sits at
//   Location = Focus - Rotation(Pitch, Yaw).Vector() * Distance
// and looks along that rotation, so it always looks at the focus point.

#include "CoreMinimal.h"

namespace Stacktown
{
namespace Camera
{
	struct FBounds2D
	{
		double MinX = -7650.0;
		double MaxX = 7650.0;
		double MinY = -4230.0;
		double MaxY = 4230.0;
	};

	struct FLimits
	{
		double MinDistance = 1200.0;
		double MaxDistance = 21024.0;  // the rig's arrival reach, also the wide stop
		double MinPitch = -85.0;   // looking straight down is -90
		double MaxPitch = -8.0;    // never flatter than this: the board must stay a board
		double FocalWide = 24.0;   // mm at MaxDistance (the rig's stop 0)
		double FocalClose = 200.0; // mm at MinDistance (the rig's stop 4)
	};

	inline double ClampPitch(double Pitch, const FLimits& L)
	{
		return FMath::Clamp(Pitch, L.MinPitch, L.MaxPitch);
	}

	inline double ClampDistance(double Distance, const FLimits& L)
	{
		return FMath::Clamp(Distance, L.MinDistance, L.MaxDistance);
	}

	inline FVector ClampFocus(const FVector& Focus, const FBounds2D& B)
	{
		return FVector(FMath::Clamp(Focus.X, B.MinX, B.MaxX), FMath::Clamp(Focus.Y, B.MinY, B.MaxY), 0.0);
	}

	/** Focal length in mm for a distance: log-interpolated between the wide
	 *  and close stops so the lens gets longer as the camera closes in, which
	 *  is what keeps the miniature framing (LENSRIG_P0.md). */
	inline double FocalForDistance(double Distance, const FLimits& L)
	{
		const double D = ClampDistance(Distance, L);
		const double T = (FMath::Loge(D) - FMath::Loge(L.MinDistance)) / (FMath::Loge(L.MaxDistance) - FMath::Loge(L.MinDistance));
		// T = 0 at MinDistance (close, long lens), 1 at MaxDistance (wide)
		return FMath::Lerp(L.FocalClose, L.FocalWide, T);
	}

	/** Horizontal field of view in degrees for a focal length on the rig's
	 *  36 mm-wide sensor (the rig used 2 * atan(18 / focal)). */
	inline double FovForFocal(double FocalMm)
	{
		return 2.0 * FMath::RadiansToDegrees(FMath::Atan(18.0 / FMath::Max(FocalMm, 1.0)));
	}

	inline FRotator RotationForPose(double Yaw, double Pitch)
	{
		return FRotator(Pitch, Yaw, 0.0);
	}

	inline FVector LocationForPose(const FVector& Focus, double Yaw, double Pitch, double Distance)
	{
		return Focus - RotationForPose(Yaw, Pitch).Vector() * Distance;
	}

	/** Where a ray from Origin along Direction meets the board plane z = 0.
	 *  Returns false when the ray points away from the plane. */
	inline bool IntersectBoardPlane(const FVector& Origin, const FVector& Direction, FVector& OutPoint)
	{
		if (Direction.Z >= -1e-6)
		{
			return false;
		}
		const double T = -Origin.Z / Direction.Z;
		if (T < 0.0)
		{
			return false;
		}
		OutPoint = Origin + Direction * T;
		OutPoint.Z = 0.0;
		return true;
	}

	/** Zoom by Factor (< 1 closes in) keeping the board point under the cursor
	 *  where it is: the focus slides toward that point by the same ratio the
	 *  distance shrinks. Clamped to the limits and the board. */
	inline void ZoomToward(const FVector& Point, double Factor, const FLimits& L, const FBounds2D& B,
		FVector& InOutFocus, double& InOutDistance)
	{
		const double OldD = ClampDistance(InOutDistance, L);
		const double NewD = ClampDistance(OldD * Factor, L);
		const double Ratio = (OldD > 1e-6) ? (NewD / OldD) : 1.0;
		const FVector P(Point.X, Point.Y, 0.0);
		InOutFocus = ClampFocus(P + (InOutFocus - P) * Ratio, B);
		InOutDistance = NewD;
	}

	/** Board-plane pan basis for a yaw: "up" on screen moves the focus along
	 *  the view direction projected on the board, "right" along its right. */
	inline void PanBasis(double Yaw, FVector& OutForward, FVector& OutRight)
	{
		const FRotator Flat(0.0, Yaw, 0.0);
		OutForward = Flat.Vector();
		OutRight = FRotationMatrix(Flat).GetScaledAxis(EAxis::Y);
	}

	/** Width of the board visible at the focus, used to scale pan speed. */
	inline double ViewWidthAtFocus(double Distance, double FovDeg)
	{
		return 2.0 * Distance * FMath::Tan(FMath::DegreesToRadians(FovDeg * 0.5));
	}
}
}
