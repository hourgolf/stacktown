// UStacktownEconomy - the GameInstance subsystem that owns the live city state,
// its persistence, and the Blueprint boundary. Ported from
// Content/Python/citytick.py (Phase 1 step 1, Docs/PLAN_CPP_PORT.md).
//
// The split: StacktownEconomyRules.h is the arithmetic and the verbs, pure and
// UObject-free; this is the part that has a lifetime, a file on disk, and
// callers. citytick.py drew the same line ("econrules.py stays the sole
// EXECUTED authority, never re-derived") and this port keeps it, because the
// moment a rule gets re-implemented on this side there are two answers to the
// same question and the oracle comparison stops meaning anything.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "StacktownEconomyRules.h"
#include "StacktownEconomy.generated.h"

namespace Stacktown
{
	/** A fresh city, straight from the ruleset's declared start. Roads is an
	 *  empty object, matching seed_state(). */
	STACKTOWNALPHA_API FCityState SeedState(const FEconRules& R);

	/** Parse citystate.json. Missing optional keys take the struct's defaults;
	 *  'roads' is round-tripped verbatim without being interpreted (step 4 owns
	 *  road semantics). Keys this port does not recognise are NOT preserved -
	 *  see the note at the end of StacktownEconomyRules.h for why that is safe
	 *  here and what has to happen before C++ becomes the writer. */
	STACKTOWNALPHA_API bool CityStateFromJson(const FString& JsonText, FCityState& Out, FString& OutError);

	/** Serialize for persistence. Round-trips CityStateFromJson semantically;
	 *  byte-equality with the Python's json.dump is NOT claimed or required -
	 *  citytick.py's own boundary test asserts the reloaded VALUE matches, which
	 *  is the property that actually protects the save. */
	STACKTOWNALPHA_API FString CityStateToJson(const FCityState& State);
}

/**
 * The city's economy for the running game.
 *
 * PERSISTENCE. State survives PIE stop/start and editor restarts by living on
 * disk - the owner's word, on the condition of a loud way out of it, which is
 * ResetCity() below.
 *
 * TWO SAVE PATHS EXIST RIGHT NOW AND THAT IS A COORDINATION ITEM, NOT A
 * DECISION THIS PORT MADE. citytick.py persists to Content/Python/citystate.json;
 * PLAN_CPP_PORT.md step 1 says the C++ state is "FCityState JSON in Saved/".
 * While both sides run - which the plan requires until the oracle comparison
 * passes - they are two files that will drift apart the moment both are live.
 * This subsystem therefore DOES NOT WRITE ANYTHING until StatePath is set
 * explicitly. It never guesses at the owner's save.
 */
UCLASS()
class STACKTOWNALPHA_API UStacktownEconomy : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** Absolute path this subsystem loads from and saves to. Empty (the default)
	 *  means no persistence at all: every verb still works, nothing is written.
	 *  Tests point this at Saved/SelfTest. */
	void SetStatePath(const FString& InAbsolutePath);
	const FString& GetStatePath() const { return StatePath; }

	/** Replace the catalogue the ladder checks consult. */
	void SetCatalogue(const TSharedPtr<Stacktown::ICatalogue>& InCatalogue);

	/** Reload the ruleset from JSON text. Returns false and leaves the previous
	 *  ruleset in place on a parse error - a malformed ruleset must never run as
	 *  if it were the ruleset. */
	bool LoadRules(const FString& JsonText, FString& OutError);

	/** Set the ruleset directly, bypassing the JSON. LoadRules is the validating
	 *  entry point and is what production uses; this exists so a test can state
	 *  the ruleset it means without needing a file on disk. */
	void SetRules(const Stacktown::FEconRules& InRules) { Rules = InRules; }

	/** Seed a fresh city WITHOUT writing anything. Initialize() calls this; a
	 *  test that constructs the subsystem directly (no GameInstance to run the
	 *  subsystem lifecycle) calls it too. ResetCity() is the same thing plus the
	 *  save and the loud log, which is why they are not the same function. */
	void SeedFresh() { State = Stacktown::SeedState(Rules); }

	const Stacktown::FEconRules& GetRules() const { return Rules; }
	const Stacktown::FCityState& GetState() const { return State; }
	Stacktown::FCityState& GetMutableState() { return State; }

	// --- the verbs, mirroring citytick.py's wrappers one for one --------------
	// Each applies via the rules layer and persists IFF it succeeded, which is
	// citytick.py's own "persist iff something changed" idiom.

	UFUNCTION(BlueprintCallable, Category = "Stacktown|Economy")
	void CityTick();

	UFUNCTION(BlueprintCallable, Category = "Stacktown|Economy")
	bool CityBuy(const FString& Pid, FString& OutReason);

	UFUNCTION(BlueprintCallable, Category = "Stacktown|Economy")
	bool CityUpgrade(const FString& Pid, FString& OutReason);

	UFUNCTION(BlueprintCallable, Category = "Stacktown|Economy")
	bool CityRepair(const FString& Pid, FString& OutReason);

	/** Register a parcel the first time the driver sees its actor. Idempotent:
	 *  if Pid already exists the existing entry wins UNTOUCHED and this is a
	 *  no-op that persists nothing.
	 *
	 *  TIER ALWAYS SEEDS AT 0, whatever tier the caller associates with Rid. A
	 *  pin's declared tier describes an intended eventual massing and is
	 *  deliberately never read here - seeding from it was the bug this function
	 *  replaces, where buying a parcel whose pin declared tier 6 showed the full
	 *  mature building instantly instead of starting small.
	 *
	 *  @return true iff a parcel was actually inserted. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Economy")
	bool EnsureParcel(const FString& Pid, const FString& Rid, double Width);

	/** Wipe persisted state and reseed. LOUD by design: the owner chose
	 *  persistence on the condition of an easy way out of it, so a deliberate
	 *  reset must never be mistakable for a bug in the evidence. */
	UFUNCTION(BlueprintCallable, Category = "Stacktown|Economy")
	void ResetCity();

	/** Convert an already-written ledger of CLOSED trades into game value. This
	 *  subsystem never places an order and never touches Alpaca, credentials, or
	 *  market data - it reads outcomes a separate process already closed. */
	void ApplyTradeLedger(const TArray<double>& LedgerPnls, TArray<Stacktown::FEconEvent>& OutEvents);

	UFUNCTION(BlueprintPure, Category = "Stacktown|Economy")
	double GetMoney() const { return State.Money; }

	UFUNCTION(BlueprintPure, Category = "Stacktown|Economy")
	double GetDemand() const { return State.Demand; }

	/** Load from StatePath, seeding fresh if there is no file yet. No-op when
	 *  StatePath is empty. */
	bool LoadState(FString& OutError);

	/** Write to StatePath. No-op returning true when StatePath is empty. */
	bool SaveState() const;

private:
	Stacktown::FEconRules Rules;
	Stacktown::FCityState State;
	TSharedPtr<Stacktown::ICatalogue> Catalogue;
	FString StatePath;
};
