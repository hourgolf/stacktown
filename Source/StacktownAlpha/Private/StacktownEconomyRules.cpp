// Ported from Content/Python/econrules.py. See StacktownEconomyRules.h for the
// invariants this translation is required to preserve.
//
// Nothing in this file touches disk, the editor, or a UObject. That is on
// purpose: it is what lets the rules be checked against the Python oracle
// without standing up a game.

#include "StacktownEconomyRules.h"

namespace Stacktown
{

FCityState SeedState(const FEconRules& R)
{
	FCityState S;
	S.Money = R.MoneyStart;
	S.Demand = R.DemandDefault;
	S.TradesProcessed = 0;
	// Roads start empty: drawing is the only writer.
	return S;
}

void AdvanceAge(FParcelState& P)
{
	if (!P.bOwned)
	{
		// An unowned lot does not age. Its recorded tier is left alone too, so
		// buying a lot that has sat for a while still starts it pale.
		return;
	}
	if (!P.AgeLastTier.IsSet() || P.AgeLastTier.GetValue() != P.Tier)
	{
		// The tier moved (or was never recorded): start pale.
		P.AgeTicks = 0.0;
		P.AgeLastTier = P.Tier;
		return;
	}
	P.AgeTicks += 1.0;
}

double AgeFraction(double AgeTicks)
{
	const double Fraction = AgeTicks / AgeMatureTicks;
	return Fraction < 1.0 ? Fraction : 1.0;
}

double Price(const FEconRules& R, int32 Tier, double Width)
{
	return R.PriceBase + R.PricePer100uu * (Width / 100.0) + R.PricePerTier * Tier;
}

double Rent(const FEconRules& R, int32 Tier, double Demand)
{
	return R.RentPerTier * (Tier + 1) * Demand;
}

int32 Climb(int32 Tier)
{
	return Tier + 1;
}

double Premium(double Performance)
{
	// max(0, -performance): a penalty for poor performance, never a discount
	// for good. 1.0 at neutral or better, 2.0 at the worst.
	const double Penalty = -Performance;
	return 1.0 + (Penalty > 0.0 ? Penalty : 0.0);
}

double UpgradePrice(const FEconRules& R, int32 Tier, double Performance)
{
	return R.PriceBase * Climb(Tier) * Premium(Performance);
}

double RepairPrice(const FEconRules& R, int32 Tier)
{
	return R.PriceBase * (Tier + 1);
}

FVerbResult TierUpAllowed(const ICatalogue& Catalogue, const FString& Rid, int32 Tier, double Width)
{
	const int32 Next = Tier + 1;
	const int32 Tiers = Catalogue.TierCount(Rid);
	if (Next >= Tiers)
	{
		return FVerbResult::No(FString::Printf(TEXT("top of ladder (%s has %d tiers)"), *Rid, Tiers));
	}
	if (!Catalogue.AssetExists(Rid, Next, Width))
	{
		// The asset NAME goes in the reason. A refusal that does not say which
		// mesh is missing is the silent null-mesh resolve this check exists to
		// prevent, wearing a message.
		return FVerbResult::No(FString::Printf(TEXT("GROWTH BLOCKED: %s not baked"),
			*Catalogue.AssetName(Rid, Next, Width)));
	}
	return FVerbResult::Ok();
}

/** The Python formats both sides with %.0f. The HUD shows this string and the
 *  oracle comparison asserts on it, so the rounding is part of the contract. */
static FString InsufficientFunds(double Money, double Cost)
{
	return FString::Printf(TEXT("insufficient funds (%.0f < %.0f)"), Money, Cost);
}

/** Parcel keys in sorted order. See Tick()'s comment in the header for why the
 *  order is load-bearing rather than cosmetic. */
static void SortedParcelIds(const FCityState& State, TArray<FString>& OutIds)
{
	OutIds.Reset();
	State.Parcels.GetKeys(OutIds);
	OutIds.Sort([](const FString& A, const FString& B) { return A < B; });
}

void Tick(const FEconRules& R, FCityState& State, TArray<FEconEvent>& OutEvents)
{
	// Mirrors econrules.tick() line for line (2026-09-06 night): rent at the demand
	// the tick STARTED with, only for owned un-failed lots; wear by one, and at
	// WearTicksPerTier x (tier + 1) the lot wears out (event WornOut); then demand
	// moves toward its target by DemandRate of the gap and clamps. Sorted ids, so
	// the sums are the Python's sums bit for bit.
	OutEvents.Reset();
	const double Demand = State.Demand;
	int32 Owned = 0, ForSale = 0;
	TArray<FString> Ids;
	SortedParcelIds(State, Ids);
	for (const FString& Id : Ids)
	{
		FParcelState& P = State.Parcels[Id];
		if (!P.bOwned)
		{
			++ForSale;
			continue;
		}
		++Owned;
		if (P.bFailed)
		{
			continue;
		}
		const double Earned = Rent(R, P.Tier, Demand);
		State.Money += Earned;
		P.Accum += Earned;
		P.Wear += 1.0;
		if (P.Wear >= R.WearTicksPerTier * (double)(P.Tier + 1))
		{
			P.bFailed = true;
			FEconEvent E; E.Type = EEconEventType::WornOut; E.Amount = 0.0; E.Pid = Id;
			OutEvents.Add(E);
		}
		// P.Tier is deliberately untouched (growth by purchase only, D20).
	}
	const double Target = R.DemandDefault + R.DemandGain * (double)Owned - R.DemandLoss * (double)ForSale;
	double NewDemand = Demand + R.DemandRate * (Target - Demand);
	NewDemand = FMath::Min(R.DemandMax, FMath::Max(R.DemandMin, NewDemand));
	State.Demand = NewDemand;
}

void TickCity(const FEconRules& R, FCityState& State, TArray<FEconEvent>& OutEvents)
{
	Tick(R, State, OutEvents);
	TArray<FString> Ids;
	State.Parcels.GetKeys(Ids);
	for (const FString& Id : Ids)
	{
		AdvanceAge(State.Parcels[Id]);
	}
}

FVerbResult Buy(const FEconRules& R, FCityState& State, const FString& Pid)
{
	FParcelState* P = State.Parcels.Find(Pid);
	if (P == nullptr)
	{
		return FVerbResult::No(TEXT("no such parcel"));
	}
	if (P->bOwned)
	{
		return FVerbResult::No(TEXT("already owned"));
	}
	const double Cost = Price(R, P->Tier, P->Width);
	if (State.Money < Cost)
	{
		return FVerbResult::No(InsufficientFunds(State.Money, Cost));
	}
	State.Money -= Cost;
	P->bOwned = true;
	P->Accum = 0.0;
	P->Wear = 0.0;
	P->bFailed = false;
	return FVerbResult::Ok();
}

FVerbResult Upgrade(const FEconRules& R, const ICatalogue& Catalogue,
	FCityState& State, const FString& Pid)
{
	FParcelState* P = State.Parcels.Find(Pid);
	if (P == nullptr)
	{
		return FVerbResult::No(TEXT("no such parcel"));
	}
	if (!P->bOwned)
	{
		return FVerbResult::No(TEXT("not owned"));
	}
	if (P->bFailed)
	{
		return FVerbResult::No(TEXT("failed: repair before upgrading"));
	}
	const FVerbResult Ladder = TierUpAllowed(Catalogue, P->Rid, P->Tier, P->Width);
	if (!Ladder.bOk)
	{
		return Ladder;
	}
	// Performance surcharges (Premium) and never gates: the affordability check
	// below is the only thing it can cause to fail, which is ruling (3) exactly.
	const double Cost = UpgradePrice(R, P->Tier, P->Performance);
	if (State.Money < Cost)
	{
		return FVerbResult::No(InsufficientFunds(State.Money, Cost));
	}
	State.Money -= Cost;
	P->Tier += 1;
	P->Wear = 0.0;
	return FVerbResult::Ok();
}

FVerbResult Repair(const FEconRules& R, FCityState& State, const FString& Pid)
{
	FParcelState* P = State.Parcels.Find(Pid);
	if (P == nullptr)
	{
		return FVerbResult::No(TEXT("no such parcel"));
	}
	if (!P->bOwned)
	{
		return FVerbResult::No(TEXT("not owned"));
	}
	if (!P->bFailed)
	{
		return FVerbResult::No(TEXT("not failed"));
	}
	const double Cost = RepairPrice(R, P->Tier);
	if (State.Money < Cost)
	{
		return FVerbResult::No(InsufficientFunds(State.Money, Cost));
	}
	State.Money -= Cost;
	P->bFailed = false;
	P->Wear = 0.0;
	return FVerbResult::Ok();
}

bool IsWin(double Pnl)
{
	return Pnl > 0.0;
}

double TradeCountReward(int32 TradesBefore, int32 NewTradeCount,
	int32 CreditsPerN, double CreditAmount)
{
	if (CreditsPerN <= 0)
	{
		// The Python would raise here. A ruleset with a non-positive
		// credits_per_n is a broken ruleset, and FEconRules::FromJson rejects
		// it before it can reach this far; this is the belt to that braces.
		return 0.0;
	}
	const int32 Before = TradesBefore / CreditsPerN;
	const int32 After  = (TradesBefore + NewTradeCount) / CreditsPerN;
	return (After - Before) * CreditAmount;
}

double TradeOutcomeBonus(const TArray<double>& NewPnls, double BonusPerWin)
{
	double Total = 0.0;
	for (const double Pnl : NewPnls)
	{
		if (IsWin(Pnl))
		{
			Total += BonusPerWin;
		}
	}
	return Total;
}

void ApplyTradeLedger(const FEconRules& R, FCityState& State,
	const TArray<double>& LedgerPnls, TArray<FEconEvent>& OutEvents)
{
	OutEvents.Reset();

	const int32 Processed = State.TradesProcessed;
	const int32 NewCount = LedgerPnls.Num() - Processed;
	if (NewCount <= 0)
	{
		// Nothing beyond what has already been counted. A true no-op: this is
		// the idempotency, and it is structural rather than a guard bolted on.
		return;
	}

	TArray<double> NewPnls;
	NewPnls.Reserve(NewCount);
	for (int32 i = Processed; i < LedgerPnls.Num(); ++i)
	{
		NewPnls.Add(LedgerPnls[i]);
	}

	const double Credits = TradeCountReward(Processed, NewCount, R.TradeCreditsPerN, R.TradeCreditAmount);
	const double Bonus   = TradeOutcomeBonus(NewPnls, R.TradeBonusPerWin);

	State.Money += Credits + Bonus;
	State.TradesProcessed = Processed + NewCount;

	// Credits before bonus, matching the Python's append order: one of the
	// oracle cases asserts the event list exactly, not as a set.
	if (Credits != 0.0)
	{
		OutEvents.Add(FEconEvent{ EEconEventType::TradeCredits, Credits, FString() });
	}
	if (Bonus != 0.0)
	{
		OutEvents.Add(FEconEvent{ EEconEventType::TradeBonus, Bonus, FString() });
	}
}

int32 FStaticCatalogue::TierCount(const FString& Rid) const
{
	const int32* Found = TierCounts.Find(Rid);
	// An unknown recipe has no ladder, so nothing can climb one. Silently
	// answering some default here would let a typo in a recipe id look like a
	// successful upgrade.
	return Found != nullptr ? *Found : 0;
}

FString FStaticCatalogue::AssetName(const FString& Rid, int32 Tier, double Width) const
{
	// recipes.asset_name's default-depth form: SM_Bld_<rid>_t<tier>_w<width>,
	// width rounded to the nearest integer exactly as the Python does.
	return FString::Printf(TEXT("SM_Bld_%s_t%d_w%d"), *Rid, Tier,
		static_cast<int32>(FMath::RoundHalfToEven(Width)));
}

bool FStaticCatalogue::AssetExists(const FString& Rid, int32 Tier, double Width) const
{
	return BakedAssets.Contains(AssetName(Rid, Tier, Width));
}

} // namespace Stacktown
