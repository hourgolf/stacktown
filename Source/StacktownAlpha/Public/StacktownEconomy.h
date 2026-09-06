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
#include "StacktownStateHandover.h"
#include "StacktownEconomy.generated.h"

namespace Stacktown
{
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
 * TWO SAVE PATHS, RESOLVED (coordinator, 2026-09-06). citytick.py persists to
 * Content/Python/citystate.json and that file stays LIVE AND AUTHORITATIVE for
 * the whole overlap; the oracle comparison reads it read-only. This subsystem
 * writes only to an explicit StatePath under Saved/Stacktown/, never under
 * Content/Python, and DOES NOT WRITE ANYTHING AT ALL until that path is set.
 * The default of writing nothing was confirmed as the right one: while both
 * sides run, a C++ writer that guessed at a path would give the owner two saves
 * drifting apart.
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

	/** Load the ruleset from Stacktown::RulesFilePath() - Content/Stacktown/Rules
	 *  (queue item 4). The file moved there because a packaged build cannot stage
	 *  Config subfolders. One loader, so every caller reads the same file from
	 *  the same place instead of each spelling the path itself. */
	bool LoadRulesFromFile(FString& OutError);

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

	// --- Phase A: mirror the Python-written state, read-only -----------------
	// Docs/STATE_HANDOVER.md. Until Phase B the Python driver is the only writer
	// of the city state. This subsystem re-reads what the Python side resolved
	// and exposes it; it never ticks on its own and never sets StatePath.

	/** Re-read the file at AbsolutePath and replace the mirrored state.
	 *
	 *  READ-ONLY BY CONSTRUCTION: it parses into a local and only commits on
	 *  success, so a truncated file mid-write leaves the previous mirror intact
	 *  rather than blanking every parcel for a frame. Refuses, loudly, if
	 *  StatePath is set - mirroring and owning the file are mutually exclusive,
	 *  and the moment both are true there are two writers, which is the one
	 *  thing this whole contract exists to prevent. */
	bool MirrorFromFile(const FString& AbsolutePath, FString& OutError);

	/** How many times the mirror has been refreshed. The live agreement check
	 *  needs to know a sync actually happened rather than assuming it. */
	int32 GetMirrorSyncCount() const { return MirrorSyncCount; }

	/** The session's state file, by the four rules the Python driver uses
	 *  (override, standalone lock, marker, default).
	 *
	 *  RESOLVED AT Initialize TIME (queue item 2), not lazily on first read, and
	 *  then cached for the session. Lazy resolution meant the answer depended on
	 *  WHEN something first asked - a marker that appeared between startup and
	 *  the first read would decide the session, which is the same hazard in
	 *  slower motion that made the Python cache it: resolving per call once
	 *  flipped a running standalone game onto the test file for a few ticks and
	 *  back, leaving two files carrying the owner's layout four seconds apart.
	 *
	 *  Pass bForceReresolve only when a session genuinely restarts. */
	FString StatePathForSession(Stacktown::EStateSource& OutSource, bool bForceReresolve = false);

	/** The path resolved at Initialize, without re-resolving. */
	const FString& GetSessionStatePath() const { return CachedSessionPath; }
	Stacktown::EStateSource GetSessionStateSource() const { return CachedSessionSource; }

	/** The override route, for a caller driving another lane's session.
	 *
	 *  RE-RESOLVES IMMEDIATELY, because the path is already decided by the time
	 *  anyone can call this. Setting an override that silently did nothing -
	 *  which is what a resolve-once-at-Initialize cache would otherwise do -
	 *  would put a lane on the owner's real save while its log said override. */
	void SetStateOverride(const FString& InAbsolutePath);

	/** Gather the real inputs (marker, lock, process kind) from disk. Exposed so
	 *  the resolution can be logged or asserted without repeating the gathering. */
	Stacktown::FStatePathInputs GatherStatePathInputs() const;

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

	// Phase A mirror state. None of this is written to disk.
	FString StateOverride;
	FString CachedSessionPath;
	Stacktown::EStateSource CachedSessionSource = Stacktown::EStateSource::Default;
	bool    bSessionPathResolved = false;
	int32   MirrorSyncCount = 0;
};
