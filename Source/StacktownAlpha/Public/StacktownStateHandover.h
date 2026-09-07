// Phase A of Docs/STATE_HANDOVER.md: the C++ economy MIRRORS the Python-written
// city state read-only, and the parcel actor reads its facts from that mirror.
//
// Everything in this header is pure. The two things step 3 needs that are not
// engine work - deciding WHICH file the session is on, and turning a mirrored
// state plus a label into the facts an actor shows - live here so they can be
// tested without a game, exactly as the economy and placement rules are.
//
// ONE HONEST DIFFERENCE FROM STEPS 1 AND 2. Those were ported against a Python
// oracle that runs headless, so every expectation was generated. These path
// rules live inside init_unreal.py, which imports `unreal` and therefore cannot
// run in the port's container at all. They are ported by READING the spec
// (init_unreal._state_path_source / _state_path_for), and the tests below are
// hand-written from that reading rather than oracle-generated. That is a weaker
// guarantee and is stated rather than glossed: the real proof is the
// coordinator's live agreement check, where every standing lot must agree with
// the Python sync.
#pragma once

#include "CoreMinimal.h"
#include "StacktownEconomyRules.h"

namespace Stacktown
{

/** Which rule chose the session's state file. The label is an AUDIT TRAIL, not
 *  decoration: a lane that forgot its marker shows Default against its own
 *  session in the log, which is catchable after the fact rather than only
 *  preventable in the good case. */
enum class EStateSource : uint8
{
	/** An explicit override, set before the session starts. Wins over all. */
	Override,
	/** A standalone game process holds the lock, so an editor session must not
	 *  share the owner's save with it. */
	StandaloneLock,
	/** A lane marker file selected the path. */
	Marker,
	/** Nothing opted out, so the owner's real file. */
	Default,
};

/** Everything the decision depends on, gathered by the caller. Separated from
 *  the decision so the rule is testable without a filesystem, a running game or
 *  a live pid - the parts that make it untestable are exactly the parts that
 *  are not the rule. */
struct STACKTOWNALPHA_API FStatePathInputs
{
	/** Empty means unset. */
	FString Override;
	/** True in a standalone game process; editor subsystems do not exist there. */
	bool    bIsGameProcess = false;
	/** True when Saved/standalone.lock holds a live pid that is not this one. */
	bool    bStandalonePidAlive = false;
	bool    bMarkerExists = false;
	/** The marker's RAW content. Trimmed here, not by the caller: "empty or
	 *  whitespace-only means the test path" is part of the rule. */
	FString MarkerContent;

	FString TestStatePath;
	/** The owner's real file. */
	FString DefaultStatePath;
};

struct STACKTOWNALPHA_API FStatePathResolution
{
	FString      Path;
	EStateSource Source = EStateSource::Default;
};

/** The session's state file, by the same four rules the Python driver uses, in
 *  the same priority order.
 *
 *  THE DEFAULT IS THE OWNER'S REAL FILE, UNCONDITIONALLY, and that direction is
 *  the whole point: a lane must opt OUT deliberately, every time, or it is on
 *  the real save. An earlier Python cut had this backwards - a flag defaulting
 *  off put the OWNER on the test path too, because a hand-started session never
 *  sets it either. Do not invert this to be safe; inverting it is the unsafe
 *  direction. */
STACKTOWNALPHA_API FStatePathResolution ResolveStatePath(const FStatePathInputs& In);

/** SAVE SLOTS (MONDAY_DECISIONS section 6, built 2026-09-07): three cities per
 *  install, chosen by the keys 1-3; a slot never written is a fresh board, and
 *  opening one never touches another. Slot 1 is the file that always existed,
 *  so every save written before slots is slot 1 and keeps its name. */
constexpr int32 SlotCount = 3;
/** "2\n" -> 2. Anything else - junk, 0, 9 - is slot 1, never a refusal. */
STACKTOWNALPHA_API int32 ParseSlot(const FString& Text);
/** Slot 1: the path itself. Slots 2 and 3: "<stem>_s<N><ext>" beside it, so the
 *  owner's citystate.json and the lanes' citystate_test.json slot the same way. */
STACKTOWNALPHA_API FString SlotStatePath(const FString& Path, int32 Slot);

/** For a log line and the ledger. */
STACKTOWNALPHA_API FString StateSourceName(EStateSource Source);

/** Everything the Python-drivers switch depends on, gathered by the caller so
 *  the RULE is testable without a plugin, an environment or an ini. */
struct STACKTOWNALPHA_API FPythonDriversInputs
{
	/** False in a packaged app: the Python plugin is UncookedOnly and simply is
	 *  not there. */
	bool    bPluginLoaded = true;
	/** STACKTOWN_PYTHON_DRIVERS, empty when unset. */
	FString EnvValue;
	bool    bFoundInNewSection = false;
	bool    bNewSectionValue = true;
	bool    bFoundInLegacySection = false;
	bool    bLegacySectionValue = true;
};

/** Whether the editor-only Python drivers own the city.
 *
 *  Priority: no plugin wins over everything (a packaged app has no Python at
 *  all, so no setting can claim otherwise), then the environment, then this
 *  build's own ini section, then the legacy section the switch already ships
 *  under, then true. The legacy fallback exists because Config/ is not this
 *  seat's to edit and the shipped key must keep working. */
STACKTOWNALPHA_API bool ResolvePythonDrivers(const FPythonDriversInputs& In);

/** Dormant pool actors are not parcels. Skipping them is not tidiness: without
 *  it every one of the thirty got registered as a real, empty, zero-width
 *  entry every session - harmless in effect but thirty wasted registrations and
 *  JSON bloat a session, which reads as a mystery a month later. */
STACKTOWNALPHA_API bool IsPoolLabel(const FString& Label);

/** What a parcel actor shows, taken from the mirrored state by its label. */
struct STACKTOWNALPHA_API FParcelFacts
{
	/** False when the label is absent from the mirror. The actor must then
	 *  change NOTHING - a lot the Python side has not registered yet is not a
	 *  lot whose facts are zero. */
	bool    bFound   = false;
	FString Rid;
	double  Width    = 0.0;
	int32   Tier     = 0;
	bool    bOwned   = false;
	bool    bFailed  = false;
	/** RECOMPUTED every sync, because it depends on Tier. Never stored. */
	double  Price    = 0.0;
	double  Accum    = 0.0;
	/** Present only on player-placed lots. */
	bool    bPlaced  = false;
};

/** The facts for one label. Pure: the same inputs always give the same answer,
 *  and nothing here touches an actor. */
STACKTOWNALPHA_API FParcelFacts FactsForLabel(const FEconRules& R, const FCityState& State,
	const FString& Label);

} // namespace Stacktown
