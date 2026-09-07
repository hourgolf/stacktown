// The economy rules, ported from Content/Python/econrules.py (Phase 1 step 1,
// Docs/PLAN_CPP_PORT.md). That module is the SPECIFICATION and the test oracle;
// this file is a translation of it and nothing more. Where the two disagree,
// the Python is right and this is the bug, until the oracle comparison says
// otherwise and the owner switches the Python side off.
//
// WHY THIS LAYER HAS NO UOBJECT IN IT. Everything here is a pure function over
// plain data: no subsystem, no reflection, no engine singletons. UStacktownEconomy
// (StacktownEconomy.h) is the GameInstance subsystem that owns persistence and the
// Blueprint boundary and calls into these. Keeping the rules free of UObject is
// what lets the same rules compile and run outside the editor, which is how the
// port is checked against the Python oracle without standing up a game.
//
// THREE INVARIANTS CARRIED ACROSS DELIBERATELY, each one a scar in the Python:
//
//   1. GROWTH IS RETIRED FROM Tick(). A tier NEVER changes on a tick, whatever
//      Accum reaches. Upgrade() is the only path a tier climbs. This is a
//      retirement, not a flag: there is no threshold branch here to switch back
//      on. (econrules.py docstring; the owner watched a balance hit 312k in one
//      session at automatic pacing.)
//   2. A TIER-UP WHOSE ASSET IS NOT BAKED REFUSES LOUDLY, with the asset name in
//      the reason. Never a silent null-mesh resolve.
//   3. CONSTANTS ARE DATA, NOT CODE. FEconRules is loaded from econrules.json,
//      never compiled in. The Python reasoning was a stale-bytecode trap; the C++
//      equivalent is worse - a baked-in constant needs a recompile to tune, and
//      ruleset tuning is exactly the edit the owner will be making most.
#pragma once

#include "CoreMinimal.h"

namespace Stacktown
{

/** econrules.json, parsed. Every value is SCAFFOLDING awaiting the owner's
 *  economy notes - the machinery is the part that survives their arrival. */
struct STACKTOWNALPHA_API FEconRules
{
	double MoneyStart        = 100.0;
	double PriceBase         = 50.0;
	double PricePer100uu     = 2.0;
	double PricePerTier      = 25.0;
	double RentPerTier       = 0.75;
	/** Read by NOTHING. Left in place because deleting a key from the owner's
	 *  ruleset is a bigger call than this port's scope - same reasoning the
	 *  Python gives for leaving it in econrules.json. */
	double GrowthThreshold   = 40.0;
	double DemandDefault     = 1.0;
	int32  TradeCreditsPerN  = 10;
	double TradeCreditAmount = 20.0;
	double TradeBonusPerWin  = 5.0;
	/** 2026-09-06 night (NIGHT_PLAN.md, working defaults): demand moves toward
	 *  DemandDefault + DemandGain x owned lots - DemandLoss x for-sale lots by
	 *  DemandRate of the gap per tick, clamped to [DemandMin, DemandMax]; an
	 *  owned lot wears out after WearTicksPerTier x (tier + 1) earning ticks. */
	double DemandGain        = 0.05;
	double DemandLoss        = 0.05;
	double DemandRate        = 0.1;
	double DemandMin         = 0.5;
	double DemandMax         = 2.0;
	double WearTicksPerTier  = 150.0;

	/** Parse econrules.json. Returns false and fills OutError on malformed JSON
	 *  or a missing key - never silently falls back to the defaults above, which
	 *  would let a typo in the owner's ruleset run as if it were the ruleset. */
	static bool FromJson(const FString& JsonText, FEconRules& Out, FString& OutError);
};

/** The ONLY three questions the economy asks the catalogue.
 *
 *  recipes.py is 1300 lines and is step 3's to port. The economy needs three
 *  answers out of it, so it takes them through this interface instead of
 *  reaching into a catalogue it does not own. That also fixes a fragility the
 *  Python author flagged in their own test 5 ("if this assert ever fails
 *  because t1 got baked, replace with a synthetic missing asset"): a test can
 *  inject a catalogue and stop depending on what happens to be on disk. */
struct STACKTOWNALPHA_API ICatalogue
{
	virtual ~ICatalogue() = default;
	/** How many tiers this recipe's ladder has. Per-recipe, never assumed
	 *  uniform: the office has four deliberately larger tiers, the catalogue six. */
	virtual int32   TierCount(const FString& Rid) const = 0;
	/** SM_Bld_<rid>_t<tier>_w<width>. recipes.asset_name's default-depth form. */
	virtual FString AssetName(const FString& Rid, int32 Tier, double Width) const = 0;
	/** Is that mesh actually baked? */
	virtual bool    AssetExists(const FString& Rid, int32 Tier, double Width) const = 0;
};

/** ICatalogue driven by plain data: a map of ladder lengths and a set of baked
 *  asset names. Lives in the rules layer, not beside the subsystem, because it
 *  needs nothing from UObject - which is also what lets it be compiled and run
 *  outside the engine when the port is checked against the oracle.
 *
 *  A test can state the catalogue it means instead of inheriting whatever is on
 *  disk. That is the fix for a fragility the Python's own test 5 admits to in a
 *  comment: it asserts office t0->t1 is blocked, and says so will stop being
 *  true the day somebody bakes office_t1. */
struct STACKTOWNALPHA_API FStaticCatalogue : public ICatalogue
{
	TMap<FString, int32> TierCounts;
	/** Asset names, as AssetName() would build them, that count as baked. */
	TSet<FString> BakedAssets;

	virtual int32   TierCount(const FString& Rid) const override;
	virtual FString AssetName(const FString& Rid, int32 Tier, double Width) const override;
	virtual bool    AssetExists(const FString& Rid, int32 Tier, double Width) const override;
};

// FLotPlacement lives HERE, beside FParcelState, rather than in
// StacktownPlacement.h - the same split the Python has. citystate.json owns the
// placement DATA (econrules.py has never known the key exists and does not need
// to); StacktownPlacement.h owns what the data MEANS. A parcel this data
// describes is indistinguishable to the economy from a pinned one.

/** Where a placed lot sits: its span along its road's axis, and which side. */
struct STACKTOWNALPHA_API FLotPlacement
{
	double  X0 = 0.0;
	double  X1 = 0.0;
	FString Side;

	/** ABSENT on lots written before the key existed - the owner's real save has
	 *  four of them. Optional rather than defaulted to "arterial" at parse time
	 *  so that "absent" and "present and equal to arterial" stay distinguishable
	 *  across a save round trip, which the ported test 26 asserts directly.
	 *  LotRoadId() below is the ONE place the fallback rule lives; three call
	 *  sites had independently written their own copy of it before that. */
	TOptional<FString> RoadId;
};

struct STACKTOWNALPHA_API FParcelState
{
	FString Rid;
	int32   Tier        = 0;
	double  Width       = 0.0;
	bool    bOwned      = false;
	double  Accum       = 0.0;
	bool    bFailed     = false;
	/** -1.0 worst to +1.0 best, 0.0 neutral. Written by NOTHING yet: the owner's
	 *  ruling (2) is that performance moves on player trades only, and no trading
	 *  system exists to move it. Read by Premium(). */
	double  Performance = 0.0;

	/** Patina's age channel (DIRECTION_B B3). Ticks while the lot is owned and
	 *  RESETS TO ZERO ON A TIER CHANGE - "new/upgraded buildings start pale",
	 *  locked. It was first wired monotonic and cumulative, which was coherent
	 *  reasoning that had simply never been checked against the owner's own
	 *  doctrine; corrected the same day.
	 *
	 *  Double, not int, because the Python carries it as a float and the state
	 *  file round-trips between the two while both sides run. */
	double AgeTicks = 0.0;

	/** The tier age was last measured against. OPTIONAL because absent and zero
	 *  mean different things: a freshly owned tier-0 lot has no recorded tier,
	 *  so its first advance takes the RESET branch and sets zero, and only the
	 *  advance after that begins counting. A plain int defaulting to 0 would
	 *  compare equal on that first pass and start counting a tick early. */
	TOptional<int32> AgeLastTier;

	/** Earning ticks since the lot was last bought, upgraded or repaired. At
	 *  WearTicksPerTier x (tier + 1) the lot WEARS OUT (bFailed) and earns
	 *  nothing until repaired. Double for the same round-trip reason as AgeTicks. */
	double Wear = 0.0;

	/** Present only on PLAYER-PLACED lots; a pinned parcel never carries it.
	 *  This is the one key that distinguishes the two paths, and it is additive
	 *  by construction - everything that reads the seven fields above was never
	 *  written to care about an eighth. */
	TOptional<FLotPlacement> Placement;
};

/** One player-drawn road: a centreline segment and how wide a class it is.
 *
 *  ORIENTATION IS NOT STORED. Which side is north and which is south is READ
 *  OFF the geometry (RoadDictFromSegment), because a stored copy is one more
 *  thing that can disagree with the segment it describes. Axis-aligned only in
 *  this version, and enforced at the point of drawing rather than assumed here. */
struct STACKTOWNALPHA_API FRoadSegment
{
	double  StartX = 0.0, StartY = 0.0;
	double  EndX   = 0.0, EndY   = 0.0;
	FString WidthClass;
};

/** The live city. Mirrors the dict econrules.tick()/buy()/upgrade() operate on. */
struct STACKTOWNALPHA_API FCityState
{
	double Money   = 0.0;
	double Demand  = 1.0;
	TMap<FString, FParcelState> Parcels;
	/** How many leading ledger entries ApplyTradeLedger has already counted.
	 *  Top-level, not per-parcel: this is what makes the ledger idempotent. */
	int32  TradesProcessed = 0;
	/** Rungs of the goal ladder already announced (StacktownScore.h); persisted
	 *  so a reloaded city is not congratulated twice. Written by the controller. */
	int32  GoalsReached = 0;

	/** PLAYER-DRAWN segments only, keyed by id. The two built-in roads (the
	 *  arterial and the cross street) are constants of the board, never state -
	 *  they have never been in this file and must not start being.
	 *
	 *  Was an opaque JSON string through steps 1-3, so a road could not be lost
	 *  while roads were nobody's to interpret; step 4 parses it for real. Empty
	 *  by default: drawing is the only thing that adds one. */
	TMap<FString, FRoadSegment> Roads;
};

// NO UNKNOWN-FIELD PASSTHROUGH, AND THAT IS DELIBERATE. An earlier draft of this
// header carried every unrecognised JSON key through a load/save round trip so a
// C++ writer could not drop a field Python had written. It is gone because the
// risk it guards against is not reachable: UStacktownEconomy refuses to write
// anything until its StatePath is set explicitly, so this port never writes the
// owner's save. Preservation gets designed - and tested - when the switch-over
// makes C++ the writer, with the coordinator, rather than shipping now as
// machinery nobody has run.

enum class EEconEventType : uint8
{
	TradeCredits,
	TradeBonus,
	WornOut,   // a lot wore out this tick; Pid names it, Amount is 0
};

struct STACKTOWNALPHA_API FEconEvent
{
	EEconEventType Type   = EEconEventType::TradeCredits;
	double         Amount = 0.0;
	FString        Pid;

	bool operator==(const FEconEvent& Other) const
	{
		return Type == Other.Type && Amount == Other.Amount && Pid == Other.Pid;
	}
};

/** (ok, reason). Every refusal is named; the reason strings are byte-identical
 *  to the Python's, because the HUD shows them and the oracle comparison
 *  asserts on them. */
struct STACKTOWNALPHA_API FVerbResult
{
	bool    bOk = false;
	FString Reason;

	static FVerbResult Ok()                          { return FVerbResult{ true,  FString() }; }
	static FVerbResult No(const FString& InReason)    { return FVerbResult{ false, InReason }; }
};

/** A fresh city, straight from the ruleset's declared start. Roads is an empty
 *  object, matching seed_state(). Lives in the rules layer, not beside the
 *  subsystem: it reads a ruleset and returns a struct, with no disk and no
 *  UObject anywhere in it - which is also what lets the placement port seed a
 *  city when the port is checked against the oracle outside the engine. */
STACKTOWNALPHA_API FCityState SeedState(const FEconRules& R);

/** Ticks at which patina is fully mature. Age saturates here. */
inline constexpr double AgeMatureTicks = 150.0;

/** One parcel's age advance for one CityTick.
 *
 *  DELIBERATELY NOT PART OF Tick(). The Python keeps this outside
 *  econrules.tick for a reason worth preserving: the economy oracles assert
 *  EXACT state equality against hand-computed answers, and age has nothing to do
 *  with the economy they prove. Folding it in would make every one of those
 *  known answers wrong for a reason unrelated to what they test. */
STACKTOWNALPHA_API void AdvanceAge(FParcelState& P);

/** min(1, ticks / AgeMatureTicks). Defined for an unowned lot too, which simply
 *  never advances. */
STACKTOWNALPHA_API double AgeFraction(double AgeTicks);

// --- pure pricing --------------------------------------------------------------
// price() and rent() take a recipe id in the Python and never read it. The
// parameter is dropped here rather than carried as a lie about what the
// arithmetic depends on.

/** price_base + price_per_100uu * (width/100) + price_per_tier * tier. */
STACKTOWNALPHA_API double Price(const FEconRules& R, int32 Tier, double Width);

/** rent_per_tier * (tier + 1) * demand. */
STACKTOWNALPHA_API double Rent(const FEconRules& R, int32 Tier, double Demand);

/** Upgrade cost multiplier that CLIMBS with each level (owner's word): linear in
 *  the tier being climbed FROM, so a tier-3 lot costs 4x a tier-0 lot's first
 *  upgrade. The curve is the part the owner's word requires; its exact shape is
 *  a placeholder like every other number here. */
STACKTOWNALPHA_API int32 Climb(int32 Tier);

/** Upgrade cost multiplier from a lot's own performance. Owner's ruling (3):
 *  poor performance costs more and NEVER blocks. Always >= 1.0 - 1.0 at neutral
 *  or better, climbing to 2.0 at the worst. No discount for good performance:
 *  the owner named a penalty only, so this does not invent a bonus. */
STACKTOWNALPHA_API double Premium(double Performance);

STACKTOWNALPHA_API double UpgradePrice(const FEconRules& R, int32 Tier, double Performance);
STACKTOWNALPHA_API double RepairPrice(const FEconRules& R, int32 Tier);

/** Ladder-top and not-baked checks. Loud about every distinct refusal. */
STACKTOWNALPHA_API FVerbResult TierUpAllowed(const ICatalogue& Catalogue,
	const FString& Rid, int32 Tier, double Width);

// --- the verbs ------------------------------------------------------------------
// The Python returns a modified COPY and leaves the caller's state alone; these
// mutate in place and mutate NOTHING on refusal, which is the same contract with
// one fewer allocation. Every one of them is pure in the sense that matters:
// no disk, no editor, no globals. Persistence belongs to UStacktownEconomy.

/** One CityTick: accrue rent into Money and each owned parcel's Accum. A tier
 *  NEVER changes here - see invariant 1 at the top of this file. OutEvents is
 *  always emptied and never appended to; the parameter is kept because every
 *  caller of the Python destructures (state, events) and step 3's parcel sync
 *  will want the shape when something does start emitting.
 *
 *  Parcels are visited in SORTED KEY ORDER, matching the Python's
 *  sorted(s['parcels'].items()). TMap iteration order is unspecified, and
 *  floating-point addition is not associative, so an unsorted walk would make
 *  Money depend on hash order - a difference that hides until the oracle
 *  comparison runs on a big save. */
STACKTOWNALPHA_API void Tick(const FEconRules& R, FCityState& State, TArray<FEconEvent>& OutEvents);

/** ONE CITY TICK as the game performs it: the economy's Tick, then AdvanceAge on
 *  every parcel by key. Age stays outside Tick (the economy oracles assert exact
 *  equality and age sits outside them), but the subsystem and any test that
 *  predicts what the subsystem persists must call the SAME composite - the engine
 *  suite found the two CityState round-trip tests predicting with Tick alone
 *  (2026-09-06: "reloaded matches the rules (parcel 'P1': age differs)"). */
STACKTOWNALPHA_API void TickCity(const FEconRules& R, FCityState& State, TArray<FEconEvent>& OutEvents);

STACKTOWNALPHA_API FVerbResult Buy(const FEconRules& R, FCityState& State, const FString& Pid);

/** Player-initiated and priced - since the retirement, the ONLY way a tier
 *  advances. Refuses on ownership, an unrepaired failure, the ladder top, an
 *  unbaked asset, and affordability. NEVER on performance alone (ruling 3).
 *  Does not touch any age/patina field: that lives outside this module's schema
 *  entirely, and the same boundary in the Python is what lets these tests assert
 *  exact state equality. */
STACKTOWNALPHA_API FVerbResult Upgrade(const FEconRules& R, const ICatalogue& Catalogue,
	FCityState& State, const FString& Pid);

/** Owner's ruling (4): failure = pay to repair. Clears bFailed on success.
 *  Nothing SETS that flag yet, so this is unreachable in real play today -
 *  built and tested ahead of what will drive it, deliberately. */
STACKTOWNALPHA_API FVerbResult Repair(const FEconRules& R, FCityState& State, const FString& Pid);

// --- trade ledger ----------------------------------------------------------------
// This code NEVER places an order and NEVER touches Alpaca, credentials, or market
// data. It reads an already-written ledger of CLOSED trades - a separate process's
// output - and converts new entries into game value. The game consumes outcomes.

/** A trade is a WIN if it closed with pnl > 0. This is the PROPOSED DEFAULT for
 *  the owner's own open question ("what does successful mean - closed profit?"),
 *  named as a default rather than asserted as final. Breakeven does not count,
 *  so a string of scratch trades cannot farm bonuses. */
STACKTOWNALPHA_API bool IsWin(double Pnl);

/** Credits for NewTradeCount more closed trades on top of TradesBefore, outcome
 *  irrelevant. Counts N-trade MILESTONES crossed, never per-trade. */
STACKTOWNALPHA_API double TradeCountReward(int32 TradesBefore, int32 NewTradeCount,
	int32 CreditsPerN, double CreditAmount);

/** Flat BonusPerWin for each winning trade. Escalating by size or P&L is
 *  explicitly among the factors the owner left open; not decided here. */
STACKTOWNALPHA_API double TradeOutcomeBonus(const TArray<double>& NewPnls, double BonusPerWin);

/** IDEMPOTENT BY CONSTRUCTION: only entries past State.TradesProcessed are read,
 *  so replaying the same or a longer ledger never double-counts, even across a
 *  restart. Awards land as Money today - whether a bonus should instead move a
 *  lot's Performance is the owner's open question, not this port's to settle. */
STACKTOWNALPHA_API void ApplyTradeLedger(const FEconRules& R, FCityState& State,
	const TArray<double>& LedgerPnls, TArray<FEconEvent>& OutEvents);

} // namespace Stacktown
